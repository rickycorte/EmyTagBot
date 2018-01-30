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

import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import texts
import dbManager
import string
import datetime
import firebase
import adminChannel


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
def get_hashtag_top_list_message():
    res = dbManager.get_top_list()
    if res is None or not res:
        return texts.top_list_error
    
    text = texts.top_list_header
    c = 0
    for itm in res:
        c+=1
        text = text + str(c) +". "+ itm["hashtag"]+" - " + str(itm["uses"])+"\n"

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
def start(bot, update):
    update.message.reply_text(texts.welcome_message)



#comando claim
def claim(bot, update):
    tag = validate_cmd(update.message.text)

    if tag is None:
        update.message.reply_text(texts.claim_reply)
        return

    #controlla che sia stato quotato un messaggio
    if update.message.reply_to_message is None:
        update.message.reply_text(texts.quote_missing)
        return

    #cerca di creare il tag se possibile
    if dbManager.can_write_hashtag(tag, update.message.from_user.id) == 0:
        data = get_message_data(update.message.reply_to_message)

        #controlla validita dati
        if data is None:
            update.message.reply_text(texts.too_much_chars)
        else:
           dbManager.create_hashtag(tag, update, data, False)
           update.message.reply_text(texts.claim_ok + tag)  

    else:
      update.message.reply_text(texts.claim_error) 



#comando remove
def remove(bot, update):
    
    tag = validate_cmd(update.message.text)
    if tag is None:
        update.message.reply_text("Use /remove <tag>")
        return
    
    #controlla se e' possibile rimuovere il tag
    if dbManager.can_write_hashtag(tag, update.message.from_user.id) == 0:
        #rimuovi il tag
        dbManager.delete_hashtag(tag)
        update.message.reply_text(texts.tag_remove_ok)
    else:
        update.message.reply_text(texts.tag_not_owned)



#comando info
def info(bot, update):
    tag = validate_cmd(update.message.text)
    if tag is None:
        update.message.reply_text("Use /info <tag>")
        return
    
    res = dbManager.get_hashtag_info(tag)

    if res is None:
        update.message.reply_text(texts.not_found)
        return

    reply = tag+":\n"
    if res["reserved"] == True:
        reply += "~ Reserved by the system ~\n"
    
    reply += "Type: " + res["data"]["type"] + "\n"
    reply += "Used: " + str(res["use_count"]) + " times\n"
         
    if res["reserved"] == True: 
        reply += "Expire: Never"   
    else:
        reply += "Creation: " + res["creation_date"].strftime("%d/%m/%y")+"\n"
        reply += "Expire: " + dbManager.calculate_delta_now(res["last_use_date"])



    update.message.reply_text(reply)


#comando help che mostra un messaggio di aiuto
def helpme(bot, update):
    update.message.reply_text(texts.help_reply)



#comando top list hashtag
def top(bot, update):
    update.message.reply_text(get_hashtag_top_list_message())


#comando edit
def edit(bot, update):
    parts = update.message.text.split()

    if len(parts) != 3:
        update.message.reply_text("Use /edit <old tag> <new tag>")
        return

    #controlla i due tag
    old_tag = check_if_hashtag(parts[1])
    new_tag = check_if_hashtag(parts[2])

    if old_tag is None or new_tag is None:
        update.message.reply_text("Use /edit <old tag> <new tag>")
        return

    uid = update.message.from_user.id
    #controlla che entrambi gli hashtag siano liberi o del propietario
    if dbManager.can_write_hashtag(old_tag, uid)== 0 and dbManager.can_write_hashtag(new_tag, uid) == 0:
        res = dbManager.change_hashtag(old_tag, new_tag)

        if res == 0:
            update.message.reply_text(texts.edit_tag_error)
        else:
            update.message.reply_text(old_tag + texts.edit_ok + new_tag)

    else:
        update.message.reply_text(texts.edit_perm_error)
        


#comando report
def report(bot, update):
    parts = update.message.text.split(" ",2)

    if len(parts) != 3:
        update.message.reply_text("Use /report <tag> <message>")
        return
    
    tag = check_if_hashtag(parts[1])
    if tag is None:
        update.message.reply_text("Use /report <tag> <message>")
        return
    
    #controlla lunghezza tag
    if len(parts[2]) < 6:
        update.message.reply_text(texts.report_short)
        return

    res = dbManager.add_report(bot, tag,update.message.from_user.id, parts[2])

    if res == 0:
        update.message.reply_text(texts.report_send_success)
        return

    if res == 1:
        update.message.reply_text(texts.report_send_error)
        return

    if res == 2:
        update.message.reply_text(texts.report_no_tag_error)
        return

    if res == 3:
        update.message.reply_text(texts.report_not_allowed)
        return


#comando mytags
def mytags(bot,update):
    uid = update.message.from_user.id
    name = update.message.from_user.first_name
    username = update.message.from_user.username
    if username is None:
        username = ""

    print("Preparing mytags data for "+ name+" @"+username)

    firebase.send_data(uid,name,username,dbManager.get_user_hashtags(uid))

    print(name+" page is ready")
    update.message.reply_text(texts.mytags_message+str(update.message.from_user.id))




### ADMIN ###

def admin_set(bot, update):
    if is_from_admin(update) == False:
        return

    tag = validate_cmd(update.message.text)

    if tag is None:
        update.message.reply_text("Use /aset <tag> ")
        return

    #controlla che sia stato quotato un messaggio
    if update.message.reply_to_message is None:
        update.message.reply_text(texts.quote_missing)
        return

    #crea il tag
    data = get_message_data(update.message.reply_to_message)

    #controlla validita dati
    if data is None:
            update.message.reply_text(texts.too_much_chars)
    else:
           dbManager.create_hashtag(tag, None, data, True)
           update.message.reply_text("[A] "+texts.claim_ok + tag)  



def admin_remove(bot, update):
    if is_from_admin(update) == False:
        return

    tag = validate_cmd(update.message.text)
    if tag is None:
        update.message.reply_text("Use /arm <tag>")
        return
    
    dbManager.delete_hashtag(tag)
    update.message.reply_text("[A] Tag removed")


def admin_reserve(bot, update):
    if is_from_admin(update) == False:
        return

    tag = validate_cmd(update.message.text)
    if tag is None:
        update.message.reply_text("Use /ars <tag>")
        return

    dbManager.create_hashtag(tag, None, {"type": "text", "data": "Sorry this tag is reserved"}, True)
    update.message.reply_text("[A] Tag reserved")


def admin_info(bot, update):

    if is_from_admin(update) == False:
        return

    tag = validate_cmd(update.message.text)
    if tag is None:
        update.message.reply_text("Use /info <tag>")
        return
    
    res = dbManager.get_hashtag_info(tag)

    if res is None:
        update.message.reply_text(texts.not_found)
        return

    update.message.reply_text( adminChannel.format_tag_info_admin(res) )

# Message Handlers #
################################################################################################################################


def hashtag_message(bot, update):
    tag = check_if_hashtag( find_first_hashtag(update.message.text) )

    if tag is None: 
        return

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

    #handler query admin
    dispatcher.add_handler(CallbackQueryHandler(adminChannel.query_handler))

    #hashtag chat
    dispatcher.add_handler(MessageHandler(Filters.entity("hashtag"), hashtag_message))


    # start bot

    DEBUG = os.environ.get('DEBUG', "false")

    if DEBUG != "false":
        dispatcher.add_handler(CommandHandler("id", get_chat_id))
        updater.start_polling(allowed_updates=["message", "callback_query"])
        print("DEBUG MODE ON")
    else:
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, allowed_updates=["message", "callback_query"])
        updater.bot.set_webhook(HEROKU_APP + TOKEN)
        print("PRODUCTION MODE")

    updater.idle()



if __name__ == '__main__':
    main()