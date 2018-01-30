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

CHANNEL_ID = int( os.environ.get('ADMIN_CHANNEL', 0) )


#formatta il dict del tag ricevuto da mongodb in un messaggio da mostrare ai soli admin
def format_tag_info_admin(tag_dict):
    
    reply = tag_dict["hashtag"]+":\n"
    if tag_dict["reserved"] == True:
        reply += "~ Reserved by the system ~\n"

    reply += "Owner: " + tag_dict["owner"]["first_name"] + " " + tag_dict["owner"]["last_name"] + " @"+tag_dict["owner"]["username"] + "\n"
    reply += "Country: " + tag_dict["owner"]["region"] + "\n"
    reply += tag_dict["origin_chat"]["type"] + " chat: " + tag_dict["origin_chat"]["name"] + "\n"
    
    reply += "Type: " + tag_dict["data"]["type"] + "\n"
    reply += "Used: " + str(tag_dict["use_count"]) + " times\n"
         
    if tag_dict["reserved"] == True: 
        reply += "Expire: Never\n"   
    else:
        reply += "Expire: " + dbManager.calculate_delta_now(tag_dict["last_use_date"])+"\n"
        reply += "Creation: " + tag_dict["creation_date"].strftime("%d/%m/%y")+"\n"

    reply += "Reports: "
    for report in tag_dict["reports"]:
        reply +="\n - " + report["text"]

    return reply


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
                    [InlineKeyboardButton("Clear reports", callback_data = make_button_data("cr",user_id,tag_id) ),
                     InlineKeyboardButton("Remove tag", callback_data = make_button_data("rt",user_id,tag_id) )],

                    [InlineKeyboardButton("Warn user", callback_data = make_button_data("wu",user_id,tag_id) ),
                     InlineKeyboardButton("Ban User", callback_data = make_button_data("bu",user_id,tag_id) )],

                    [InlineKeyboardButton("Show Tag Data (Private Chat)", callback_data = make_button_data("st",user_id,tag_id) )] 
                ]

    reply_buttons = InlineKeyboardMarkup(keyboard)

    bot.sendMessage(chat_id=CHANNEL_ID, text=msg, reply_markup=reply_buttons)
    

#handler generico delle query da usare come callback 
def query_handler(bot, update):
    query = update.callback_query

    parts = query.data.split("_")

    if parts[0] == "st":
        send_tag_data_to_private_chat(bot,update,parts[1],parts[2])

    #bot.sendMessage(chat_id=CHANNEL_ID,text = "Selected: "+query.data)
    query.answer()

#invia in chat provivata il contenuto di un tag
def send_tag_data_to_private_chat(bot, update, user_id, tag_id):

    result = dbManager.search_tag_by_id(user_id,tag_id)
    if result is None:
       bot.sendMessage(chat_id=update.callback_query.from_user.id, text = "Error: can't find tag")
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
