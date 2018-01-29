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

#manda un messaggio inerente al report nella canale admin
#aggiunge poi i bottoni con funzionalita da decidere :3
def send_report_data(bot, tag_dict):
    print("Sending report data to admin channel")
    msg = format_tag_info_admin(tag_dict)
    keyboard = [
                    [InlineKeyboardButton("Clear reports", callback_data='1'), InlineKeyboardButton("Remove tag", callback_data='2')],
                    [InlineKeyboardButton("Warn user", callback_data='3'), InlineKeyboardButton("Ban User", callback_data='4')],
                    [InlineKeyboardButton("Show Tag Data", callback_data='5')] 
                ]

    reply_buttons = InlineKeyboardMarkup(keyboard)

    bot.sendMessage(chat_id=CHANNEL_ID, text=msg, reply_markup=reply_buttons)
    