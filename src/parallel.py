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

import dbManager
import time
import threading

#esegue il broadcast in piu fasi (evita il limite di rate delle api telegram)
#al termine manda un msg alla chat che ha eseguito il comando
def broadcast_message(bot, update, msg):
    t = threading.Thread(target = exec_broadcast_message, args = (bot, update, msg))
    t.start()

    print("Broadcasting")


#funzione che esegue il broadcast, da avviare in unb thread separato
def exec_broadcast_message(bot, update, msg):

    bot.sendMessage(update.message.chat.id, "Broadcasting: `"+msg+"`")

    chats = dbManager.get_bcast_chats()
    for chat in chats:
        bot.sendMessage(chat["id"], msg)
        time.sleep(1)
    
    bot.sendMessage(update.message.chat.id, "Broadcast completed :3")