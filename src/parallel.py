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
import botan
import json

events_to_process = []
event_processor_lock = threading.Lock()


#esegue il broadcast in piu fasi (evita il limite di rate delle api telegram)
#al termine manda un msg alla chat che ha eseguito il comando
def broadcast_message(bot, update, msg):
    t = threading.Thread(target = exec_broadcast_message, args = (bot, update, msg))
    t.start()

    print("Started broadcasting")


#funzione che esegue il broadcast, da avviare in unb thread separato
def exec_broadcast_message(bot, update, msg):

    print("Broadcasting: "+msg)

    bot.sendMessage(update.message.chat.id, "Broadcasting: `"+msg+"`")

    chats = dbManager.get_bcast_chats()
    for chat in chats:
        bot.sendMessage(chat["id"], msg)
        time.sleep(1)
    
    bot.sendMessage(update.message.chat.id, "Broadcast completed :3")
    print("Broadcast completed")




#aggiunge alla lista degli eventi qualcosa, appena possibile questo viene processato e inviato alle api di appmetrica
def send_stats_event(uid, message, name):
    event_processor_lock.acquire()
    events_to_process.append(
            {
                "uid": uid,
                "message": message.to_dict(),
                "name": name
            }
        )
    event_processor_lock.release()
    print("Added stats event: "+name)


#funzione che processa gli eventi per appmetrica
def event_processor():

    while True:

        if len(events_to_process) <= 0:
            continue 

        #recupera il primo elemento da processare
        event_processor_lock.acquire()
        ev = events_to_process.pop(0)
        event_processor_lock.release()

        botan.track(ev["uid"], ev["message"], ev["name"])
        print("Processed stats event: "+ev["name"])

        time.sleep(1)
        

#avvia il thread che processa gli eventi da inviare a appmetrica
def start_stats_processor():
    print("Starting stats event processor...")
    t = threading.Thread(target = event_processor)
    t.start()
    print("Done")
