#!/usr/bin/env python
# -*- coding: utf-8 -*-

###################################################################################
#
#    EmyTagBot
#    A Telegram bot meant to create user-based hashtags contents with text, images, audios, sticker, videos.
#    Copyright (C) 2018  RickyCorte
#    https://github.com/rickycorte
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

import environ_check  
#esegui il check di tutte le variabili e di mongodb appena viene importato
#se ci sono errori termina l'esecuzione del bot in automatico
environ_check.check()


import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, InlineQueryHandler
from telegram.ext.dispatcher import run_async
import texts
import dbManager
import string
import datetime
import firebase
import adminChannel
import parallel
import inlines


TOKEN = os.environ.get('TOKEN', 'token')
ADMIN_ID = os.environ.get('ADMIN', 0)

MAX_HASHTAG_SIZE = int( os.environ.get('MAX_HASHTAG_SIZE', 128) )
MAX_TEXT_SIZE = int( os.environ.get('MAX_TEXT_SIZE', 512) )

PORT = int(os.environ.get('PORT', '8443'))
HEROKU_APP = os.environ.get('APP_LINK', '')

HASHTAG_LIFETIME = int( os.environ.get('TAG_LIFE_TIME', 5))

checker = string.ascii_letters + string.digits


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)


# Funzioni #
################################################################################################################################



def is_hash_char(ch):
    if ch in checker + "_":
        return True
    else:
        return False

def is_digit(ch):
    if ch in string.digits:
        return True
    else:
        return False

#controlla che la parola passata come parametro abbia # come carattere 0 altrimenti lo aggiunge
#restituisce None se l'hastage' invalido altrimenti ritorna il tag completo
def check_if_hashtag(data):

    #controlla che siano stati passati dei caratteri
    if not data:
        return None

    data = data.strip().lower()

    if data[0] != "#":
        data = "#" + data
    #evita hashtag troppo lunghi
    if len(data) > MAX_HASHTAG_SIZE:
        return None
    
    if len(data) == 2 and is_digit(data[1]): #previeni hashtag come #1
        return None

    only_digit = True

    #controlla che tutti i caratteri siano ok
    count = 1 #conta da 1 per evitare l'# che renderebbe falso il primo controllo
    while count < len(data):
        if not is_hash_char(data[count]):
            return None
        if not is_digit(data[count]):
            only_digit = False
        count +=1

    if only_digit: #evita hashtag invalidi tipo 1234
        return None

    return data

#trova e restituisce il primo hashtag trovato nel testo passato
def find_first_hashtag(msg):
    if msg is None:
        return None

    beg = msg.find("#")
    end = msg.find(" ", beg)

    if beg == -1:
        return None

    if end != -1:
        return msg[beg:end]
    else:
        return msg[beg:]


#restituisce true se l'update proviene da un admin
def is_from_admin(update):
    return int(update.message.from_user.id) == int(ADMIN_ID)


#crea e restituisce la lista degli hashtag top
#restituisce la stringa da mandare alla chat
def get_hashtag_top_list_message(update):
    res = dbManager.get_top_list()
    if res is None or not res:
        return texts.get_text("top_list_error", update.message.from_user.language_code)
    
    text = texts.get_text("top_list_header", update.message.from_user.language_code)
    c = 0
    for itm in res:
        c+=1
        text = text + str(c) +". "+ itm["hashtag"]+" - " + str(itm["use_count"])+"\n"

    text+= texts.get_text("complete_list",update.message.from_user.language_code)

    return text

#convalida comandi tipo /comando #tag
#restituisce none se ci sono stati problemi altrimenti da il tag corretto come risposta
def validate_cmd(text):
    parts = text.split()

    if len(parts) != 2:
        return None
    
    return check_if_hashtag(parts[1])

#restituisce i dati contenuti nel messaggio
# none in caso di errore
def get_message_data(message):

        if message.text is not None:
            if len(message.text) > MAX_TEXT_SIZE:
                return None

            return {"type":"text", "data": message.text } 

        if message.document is not None:
            return {"type":"gif", "data": message.document.file_id}

        if message.sticker is not None:
            return {"type":"sticker", "data": message.sticker.file_id}

        if message.audio is not None:
            return {"type":"audio", "data": message.audio.file_id}     

        if message.video is not None:
            return {"type":"video", "data":message.video.file_id}

        if message.voice is not None:
            return {"type":"voice", "data":message.voice.file_id}

        if message.photo is not None:
            return {"type":"image", "data":message.photo[0].file_id}



# Command Handlers #
################################################################################################################################


#il comando start, sarebbe meglio mettere una frase piu decente ma vbb <3
@run_async
def start(bot, update):
    update.message.reply_text(texts.get_text("welcome_message",update.message.from_user.language_code))
    dbManager.add_chat_to_bcast_list(update.message.chat.id)



#comando claim
@run_async
def claim(bot, update):

    if dbManager.is_user_banned(update.message.from_user.id) == True:
        return

    tag = validate_cmd(update.message.text)

    if tag is None:
        update.message.reply_text(texts.get_text("claim_reply",update.message.from_user.language_code))
        return

    #controlla che sia stato quotato un messaggio
    if update.message.reply_to_message is None:
        update.message.reply_text(texts.get_text("quote_missing",update.message.from_user.language_code))
        return

    #cerca di creare il tag se possibile
    if dbManager.can_write_hashtag(tag, update.message.from_user.id) == 0:
        data = get_message_data(update.message.reply_to_message)

        #controlla validita dati
        if data is None:
            update.message.reply_text(texts.get_text("too_much_chars",update.message.from_user.language_code))
        else:
           dbManager.create_hashtag(tag, update, data, False)
           update.message.reply_text(texts.get_text("claim_ok", update.message.from_user.language_code) + tag)  

    else:
      update.message.reply_text(texts.get_text("claim_error",update.message.from_user.language_code)) 



#comando remove
@run_async
def remove(bot, update):
    
    tag = validate_cmd(update.message.text)
    if tag is None:
        update.message.reply_text(texts.get_text("cmd_rm_use",update.message.from_user.language_code))
        return
    
    #controlla se e' possibile rimuovere il tag
    res = dbManager.can_write_hashtag(tag, update.message.from_user.id, True)
    if res == 0:
        #rimuovi il tag
        dbManager.delete_hashtag(tag)
        update.message.reply_text(texts.get_text("tag_remove_ok",update.message.from_user.language_code))
    else:
        if res == 3:
            update.message.reply_text(texts.get_text("rm_tag_free",update.message.from_user.language_code))
        else:
            update.message.reply_text(texts.get_text("tag_not_owned",update.message.from_user.language_code))



#comando info
@run_async
def info(bot, update):

    tag = validate_cmd(update.message.text)
    if tag is None:
        update.message.reply_text(texts.get_text("cmd_rm_use",update.message.from_user.language_code))
        return
    
    res = dbManager.get_hashtag_info(tag)

    if res is None:
        update.message.reply_text(texts.get_text("not_found",update.message.from_user.language_code))
        return

    #recupera la stringa giusta in base al tipo di tag e formattala di conseguenza
    reply = ""
    if res["reserved"] == True:
        reply = texts.get_text("info_msg_system", update.message.from_user.language_code)
    else:
        reply = texts.get_text("info_msg_user", update.message.from_user.language_code)

    reply = reply.format(
            tag = tag,
            type = res["data"]["type"],
            used = str(res["use_count"]),
            dtc = res["creation_date"].strftime("%d/%m/%y"),
            dte = dbManager.calculate_delta_now(res["last_use_date"])
        )

    update.message.reply_text(reply)


#comando help che mostra un messaggio di aiuto
@run_async
def helpme(bot, update):
    update.message.reply_text(texts.get_text("help_reply",update.message.from_user.language_code))



#comando top list hashtag
@run_async
def top(bot, update):
    update.message.reply_text(get_hashtag_top_list_message(update))


#comando edit
@run_async
def edit(bot, update):

    if dbManager.is_user_banned(update.message.from_user.id) == True:
        return

    parts = update.message.text.split()

    if len(parts) != 3:
        update.message.reply_text(texts.get_text("cmd_edit_use",update.message.from_user.language_code))
        return

    #controlla i due tag
    old_tag = check_if_hashtag(parts[1])
    new_tag = check_if_hashtag(parts[2])

    if old_tag is None or new_tag is None:
        update.message.reply_text(texts.get_text("cmd_edit_use",update.message.from_user.language_code))
        return

    uid = update.message.from_user.id
    #controlla che entrambi gli hashtag siano liberi o del propietario
    if dbManager.can_write_hashtag(old_tag, uid)== 0 and dbManager.can_write_hashtag(new_tag, uid) == 0:
        res = dbManager.change_hashtag(old_tag, new_tag)

        if res == 0:
            update.message.reply_text(texts.get_text("edit_tag_error",update.message.from_user.language_code))
        else:
            update.message.reply_text( texts.get_text("edit_ok",update.message.from_user.language_code).format(old=old_tag,new=new_tag) )

    else:
        update.message.reply_text(texts.get_text("edit_perm_error",update.message.from_user.language_code))
        


#comando report
@run_async
def report(bot, update):

    if dbManager.is_user_banned(update.message.from_user.id) == True:
        return

    parts = update.message.text.split(" ",2)

    if len(parts) != 3:
        update.message.reply_text(texts.get_text("cmd_report_use",update.message.from_user.language_code))
        return
    
    tag = check_if_hashtag(parts[1])
    if tag is None:
        update.message.reply_text(texts.get_text("cmd_report_use",update.message.from_user.language_code))
        return
    
    #controlla lunghezza tag
    if len(parts[2]) < 6:
        update.message.reply_text(texts.get_text("report_short",update.message.from_user.language_code))
        return

    res = dbManager.add_report(bot, tag,update.message.from_user.id, parts[2])

    if res == 0:
        update.message.reply_text(texts.get_text("report_send_success",update.message.from_user.language_code))
        return

    if res == 1:
        update.message.reply_text(texts.get_text("report_send_error",update.message.from_user.language_code))
        return

    if res == 2:
        update.message.reply_text(texts.get_text("report_no_tag_error",update.message.from_user.language_code))
        return

    if res == 3:
        update.message.reply_text(texts.get_text("report_not_allowed",update.message.from_user.language_code))
        return


#comando mytags
@run_async
def mytags(bot,update):

    uid = update.message.from_user.id
    name = update.message.from_user.first_name
    username = update.message.from_user.username
    if username is None:
        username = ""

    print("Preparing mytags data for "+ name+" @"+username)

    firebase.send_user_data(uid,name,username,dbManager.get_user_hashtags(uid))

    print(name+" page is ready")
    update.message.reply_text(texts.get_text("mytags_message",update.message.from_user.language_code) +str(update.message.from_user.id))




### ADMIN ###
@run_async
def admin_set(bot, update):
    if is_from_admin(update) == False:
        return

    tag = validate_cmd(update.message.text)

    if tag is None:
        update.message.reply_text(texts.get_text("adm_set_use"))
        return

    #controlla che sia stato quotato un messaggio
    if update.message.reply_to_message is None:
        update.message.reply_text(texts.get_text("quote_missing"))
        return

    #crea il tag
    data = get_message_data(update.message.reply_to_message)

    #controlla validita dati
    if data is None:
            update.message.reply_text(texts.get_text("too_much_chars"))
    else:
           dbManager.create_hashtag(tag, None, data, True)
           update.message.reply_text(texts.get_text("adm_set_ok").format(tag=tag))  


@run_async
def admin_remove(bot, update):
    if is_from_admin(update) == False:
        return

    tag = validate_cmd(update.message.text)
    if tag is None:
        update.message.reply_text(texts.get_text("adm_rm_use"))
        return
    
    dbManager.delete_hashtag(tag)
    update.message.reply_text(texts.get_text("adm_rm_ok"))


@run_async
def admin_reserve(bot, update):
    if is_from_admin(update) == False:
        return

    tag = validate_cmd(update.message.text)
    if tag is None:
        update.message.reply_text(texts.get_text("adm_reserve_use"))
        return

    dbManager.create_hashtag(tag, None, {"type": "text", "data": "Sorry this tag is reserved"}, True)
    update.message.reply_text(texts.get_text("adm_reserve_ok"))


@run_async
def admin_info(bot, update):

    if is_from_admin(update) == False:
        return

    tag = validate_cmd(update.message.text)
    if tag is None:
        update.message.reply_text(texts.get_text("adm_info_use"))
        return
    
    res = dbManager.get_hashtag_info(tag)

    if res is None:
        update.message.reply_text(texts.get_text("not_found"))
        return

    update.message.reply_text( adminChannel.format_tag_info_admin(res) )


@run_async
def admin_bcast(bot, update):
    if is_from_admin(update) == False:
        return

    parts = update.message.text.split(" ",1)

    if len(parts) != 2:
        update.message.reply_text(texts.get_text("adm_bcast_use"))
        return

    parallel.broadcast_message(bot, update, parts[1])

    #ci mettera un po a finire :3
    #ma qui ci arriviamo subito


# Message Handlers #
################################################################################################################################

@run_async
def hashtag_message(bot, update):
    tag = check_if_hashtag( find_first_hashtag(update.message.text) )

    if tag is None: 
        return

    dbManager.add_chat_to_bcast_list(update.message.chat.id)

    result = dbManager.search_hashtag(tag)

    #hash non trovato
    if result["code"] != 0: 
        return

    if result["type"] == "text":
        bot.sendMessage(update.message.chat.id,result["reply"])

    if result["type"] == "image":
        bot.sendPhoto(update.message.chat.id,result["reply"])

    if result["type"] == "gif":
        bot.sendDocument(update.message.chat.id,result["reply"])

    if result["type"] == "sticker":
        bot.sendSticker(update.message.chat.id,result["reply"])

    if result["type"] == "audio":
        bot.sendAudio(update.message.chat.id,result["reply"])

    if result["type"] == "voice":
        bot.sendVoice(update.message.chat.id,result["reply"])

    if result["type"] == "video":
        bot.sendVideo(update.message.chat.id,result["reply"])


def get_chat_id(bot,update):
    update.message.reply_text("Chat ID: "+str(update.message.chat.id))

################################################################################################################################


def main():

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    #registra comandi
    dispatcher.add_handler(CommandHandler("start", start))

    dispatcher.add_handler(CommandHandler("claim", claim))
    dispatcher.add_handler(CommandHandler("set", claim))

    dispatcher.add_handler(CommandHandler("edit", edit))

    dispatcher.add_handler(CommandHandler("remove", remove))
    dispatcher.add_handler(CommandHandler("rm", remove))

    dispatcher.add_handler(CommandHandler("info", info))

    dispatcher.add_handler(CommandHandler("help", helpme))
    dispatcher.add_handler(CommandHandler("top", top))

    dispatcher.add_handler(CommandHandler("report", report))

    dispatcher.add_handler(CommandHandler("mytags", mytags))
    
    #comandi admin
    dispatcher.add_handler(CommandHandler("aset", admin_set))
    dispatcher.add_handler(CommandHandler("arm", admin_remove))
    dispatcher.add_handler(CommandHandler("ars", admin_reserve))
    dispatcher.add_handler(CommandHandler("ainfo", admin_info))

    dispatcher.add_handler(CommandHandler("bcast", admin_bcast))

    #handler query admin
    dispatcher.add_handler(CallbackQueryHandler(adminChannel.query_handler))

    #hashtag chat
    dispatcher.add_handler(MessageHandler(Filters.entity("hashtag"), hashtag_message))

    #inline query
    dispatcher.add_handler(InlineQueryHandler(inlines.inline_query))

    # start bot

    DEBUG = os.environ.get('DEBUG', "false")

    up_kind = ["message", "callback_query", "inline_query"]

    if DEBUG != "false":
        dispatcher.add_handler(CommandHandler("id", get_chat_id))
        updater.start_polling(allowed_updates= up_kind)
        print("DEBUG MODE ON")
    else:
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, allowed_updates=up_kind)
        updater.bot.set_webhook(HEROKU_APP + TOKEN)
        print("PRODUCTION MODE")

    updater.idle()



if __name__ == '__main__':
    main()