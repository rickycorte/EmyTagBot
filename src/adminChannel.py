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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import dbManager
import datetime
import texts

ADMIN_ID = os.environ.get('ADMIN', 0)

CHANNEL_ID = int( os.environ.get('ADMIN_CHANNEL', 0) )


#formatta il dict del tag ricevuto da mongodb in un messaggio da mostrare ai soli admin
def format_tag_info_admin(tag_dict):

    reply = ""

    #prepara i dati lunghi da inserire
    if tag_dict["reserved"] == True:
        reply = texts.get_text("adm_info_msg_system") 
    else:
        reply = texts.get_text("adm_info_msg_usr")

    ow = tag_dict["owner"]["first_name"] + " " + tag_dict["owner"]["last_name"] + " @"+tag_dict["owner"]["username"]
    chat = tag_dict["origin_chat"]["type"] + " chat: " + tag_dict["origin_chat"]["name"]

    reports = ""
    for report in tag_dict["reports"]:
        reports +="\n - " + report["text"]

    #formatta la stringa e retituiscila
    return reply.format(
        tag = tag_dict["hashtag"],
        region = tag_dict["owner"]["region"],
        owner = ow,
        chat = chat,
        type = tag_dict["data"]["type"],
        used = str(tag_dict["use_count"]),
        exp = dbManager.calculate_delta_now(tag_dict["last_use_date"]),
        crt = tag_dict["creation_date"].strftime("%d/%m/%y"),
        rep = reports
        )



#restituisce un id per identificare l'azione associata a un preciso tag di un utente
# restituisce una strianga di massimo 64 caratteri formattata come <azione>_<user_id>_<tag id>
# l'id del tag puo essere tranciato se finiscono i 64 caratteri
def make_button_data(action, user_id, tag_id):
    id = str(action) + "_"+str(user_id) + "_"+ str(tag_id)
    return id[:64]


#manda un messaggio inerente al report nella canale admin
#aggiunge poi i bottoni con funzionalita da decidere :3
def send_report_data(bot, tag_dict):
    print("Sending report data to admin channel (" + str(CHANNEL_ID) + ")")
    msg = format_tag_info_admin(tag_dict)

    user_id = tag_dict["owner"]["id"]
    tag_id = tag_dict["_id"]

    if isinstance(tag_id, dict) and tag["$oid"] is not None:
        tag_id = tag_id["$oid"]

    keyboard = [
                    [InlineKeyboardButton(texts.get_text("admc_clear_reports"), callback_data = make_button_data("cr",user_id,tag_id) ),
                     InlineKeyboardButton(texts.get_text("admc_remove_tag"), callback_data = make_button_data("rt",user_id,tag_id) )],

                    [InlineKeyboardButton(texts.get_text("admc_show_tag"), callback_data = make_button_data("st",user_id,tag_id) )] 
                ]
    

    reply_buttons = InlineKeyboardMarkup(keyboard)

    bot.sendMessage(chat_id=CHANNEL_ID, text=msg, reply_markup=reply_buttons)
    

#handler generico delle query da usare come callback 
def query_handler(bot, update):
    query = update.callback_query

    if int(query.from_user.id) != int(ADMIN_ID): #check if admin
        return

    parts = query.data.split("_")

    if parts[0] == "st":
        send_tag_data_to_private_chat(bot,update,parts[2])

    if parts[0] == "cr":
        clear_reports(bot,update, parts[2])

    if parts[0] == "rt":
        remove_tag(bot,update, parts[2])

    if parts[0] == "nb":
        close_case(bot, update, None, texts.get_text("admc_case_delete_tag"))
    
    if parts[0] == "wu":
        r = dbManager.warn_user(int(parts[1]))

        if r == 1:
            send_private_message(bot, int(parts[1]), texts.get_text("warn_received", update.message.from_user.language_code))
            close_case(bot, update, None, texts.get_text("admc_case_delete_warn_tag"))
        else:
            send_private_message(bot, int(parts[1]), texts.get_text("ban_received", update.message.from_user.language_code))
            close_case(bot, update, None, texts.get_text("admc_case_delete_ban_tag"))


    if parts[0] == "bu":
        dbManager.ban_user(int(parts[1]))
        close_case(bot, update, None, texts.get_text("admc_case_delete_ban_tag"))

    #bot.sendMessage(chat_id=CHANNEL_ID,text = "Selected: "+query.data)


#invia in chat provivata il contenuto di un tag
def send_tag_data_to_private_chat(bot, update, tag_id):

    result = dbManager.get_tag_by_id(tag_id)
    if result is None:
       bot.sendMessage(chat_id=update.callback_query.from_user.id, text = texts.get_text("admc_missing_tag_data"))
       return

    uid = update.callback_query.from_user.id

    if result["data"]["type"] == "text":
        bot.sendMessage(uid, result["data"]["data"])

    if result["data"]["type"] == "image":
        bot.sendPhoto(uid, result["data"]["data"])

    if result["data"]["type"] == "gif":
        bot.sendDocument(uid, result["data"]["data"])

    if result["data"]["type"] == "sticker":
        bot.sendSticker(uid, result["data"]["data"])

    if result["data"]["type"] == "audio":
        bot.sendAudio(uid, result["data"]["data"])

    if result["data"]["type"] == "voice":
        bot.sendVoice(uid, result["data"]["data"])

    if result["data"]["type"] == "video":
        bot.sendVideo(uid, result["data"]["data"])


#genera il messaggio che infroma gli admin che sono stati presi provvedimenti sul tag
def close_case(bot, update, db_data, message):
    qr = update.callback_query

    reply = texts.get_text("admc_case_closed")
    head = ""

    if db_data is not None:
        head = "Tag "+ db_data["hashtag"]+":"
    else:
        head = texts.get_text("admc_case_delete_tag")

    reply = reply.format(
        head = head,
        act = message,
        aut = qr.from_user.first_name +" ("+qr.from_user.username+")",
        dt = datetime.datetime.utcnow().strftime("%d/%m/%y")

    )

    bot.edit_message_text(text = reply, chat_id=qr.message.chat_id, message_id=qr.message.message_id)


#elimina tutti i report di un tag e modifica il messaggio per avvisare del completamento dell'operazione
def clear_reports(bot, update, tag_id):
    res = dbManager.remove_reports(tag_id)
    close_case(bot,update,res,texts.get_text("admc_report_clear"))



#elimina un tag e chiedi cosa fare con l'utente: nulla/warn/ban
def remove_tag(bot, update, tag_id):

    res = dbManager.get_tag_by_id(tag_id)

    send_private_message( bot, res["origin_chat"]["id"] , texts.get_text("admc_bad_tag_warn").format(tag=res["hashtag"]) )

    dbManager.delete_tag_by_id(tag_id)

    user_id = res["owner"]["id"] 
    
    qr = update.callback_query

    keyboard = [
                    [
                        InlineKeyboardButton(texts.get_text("admc_warn_usr"), callback_data = make_button_data("wu",user_id,tag_id) ),
                        InlineKeyboardButton(texts.get_text("admc_ban_usr"), callback_data = make_button_data("bu",user_id,tag_id) )
                    ],
                    [
                        InlineKeyboardButton(texts.get_text("admc_close_case"), callback_data = make_button_data("nb",user_id,tag_id) ),
                    ]


                ]
    
    bot.edit_message_text(text = texts.get_text("admc_pending_adm_action"), chat_id=qr.message.chat_id, message_id=qr.message.message_id, 
        reply_markup=InlineKeyboardMarkup(keyboard) )


#invia un messaggipo privata a un utente
def send_private_message(bot, user_id, text):
    bot.sendMessage(chat_id = user_id, text = text)
