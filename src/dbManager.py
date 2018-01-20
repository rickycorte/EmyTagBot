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

from pymongo import MongoClient
import datetime
import os

client = MongoClient( os.environ.get('MONGODB_URI', 'error') )

top_list_size = int(os.environ.get('TOP_LIST_SIZE', 10))

db = client[ os.environ.get('DB_NAME', 'EmyTagBot') ] 

reserved_tag_placeholder_name = os.environ.get('RESERVED_TAG_PLACEHOLDER', 'EmyTagBot')


#controlla se user_id puo claimare un determinato hashtag
# 0 = si
# 1 = no perche e' di un altro utente
# 2 = e' riservato
def can_write_hashtag(hashtag, user_id):
    print("checking hashtag write permission for"+ hashtag)
    hashtag = hashtag.lower()
    res = db.hashtags.find_one({"hashtag": hashtag})

    #hashtag inesistente quindi si puo scrivere
    if res is None: 
        return 0
    
    #tag riservato dal sistema
    if res["reserved"] == True:
        return 2
    
    #richiedente e' lo stesso utente che possiede il tag
    if user_id == res["owner"]["id"]:
        return 0
    else: #tag di un altro utente
        return 1

#resitituisce i 10 hashtag + usati nel formato [{"hashtag":"...", uses:..},...]    
def get_top_list():
    print("count#requests.top_list=1")
    result = []
    res = db.hashtags.find().sort([("use_count",-1)]).limit(top_list_size)
    if not res or res is None:
        return None

    for itm in res:
        result.append({"hashtag":itm["hashtag"], "uses":itm["use_count"]})

    return result


#cerca un hashtag nel database
def search_hastag(hashtag):
    hashtag = hashtag.lower()
    print("count#requests.search_hashtag=1")

    res = db.hashtags.find_one({"hashtag": hashtag})
    #hashtag non trovato - corrisponde codice 1
    if res is None:
        print("not found")
        return {"code": 1}
    else:
        #aggiorna data ultimo uso e contatore utilizzi
        db.hashtags.update_one( {"_id": res["_id"]}, 
            {"$set": 
                {
                    "use_count": res["use_count"] + 1,
                    "last_use_date": datetime.datetime.utcnow() 
                } 
            }, upsert=False)
        print("Found: Updated hashtag use count")

        return {"type": res["data"]["type"], "reply": res["data"]["data"], "code": 0}


#aggiungi un report ad un hashtag
#restituisce 0 se e' stato aggiunto
#ignora le segnalazioni di tag riservati e restituisce 3
# 1 invece se il tag e' gia stato segnalato dallo stesso utente
# 2 se il tag non esiste
def add_report(hashtag, user_id, report_text):
    hashtag = hashtag.lower()
    print("count#requests.reports=1")
    res = db.hashtags.find_one({"hashtag": hashtag})
    #controlla se tag esiste
    if res is None:
        print("tag not found")
        return 2

    if res["reserved"] == True:
        print("tag reserved: not allowed")
        return 3

    #recupera la lista dei report del tag
    reports = res["reports"]
    #controlla se l'utente non abbia gia report creati
    has_report = False
    for rep in reports:
        if rep["user_id"] == user_id:
            has_report = True
    
    if has_report:
        print(str(user_id) + " just have an active report")
        return 1

    #aggiungi il report all'array
    reports.append({"user_id":user_id,"text":report_text})
    #aggiorna il database
    db.hashtags.update_one( {"_id": res["_id"]}, 
        {"$set": 
            {
                "reports":reports
            } 
        }, upsert=False)

    print("created report")

    #TODO: aggiungere invio in canale quando i report superano un certo numero

    return 0

#inserisce un oggetto data {"type": "text/image/gif/sticker", "data":"..."} nel database
def create_hashatag(hashtag, update, data, reserved):

    hashtag = hashtag.lower()

    #i messaggi senza username non sono accettabili se non si tratta di una richiesta del sistema
    if reserved == False and not "from" in update["message"]: 
        return 

    print("creating hashtag "+hashtag)
    print("count#requests.create_hashtag")

    #inizializza i valori da inserire a quelli basi del sistema
    username = "@" + reserved_tag_placeholder_name
    user_id = 0
    first_name = reserved_tag_placeholder_name
    last_name = ""
    region = ""
    chat_id = 0
    chat_name = ""
    chat_type = ""

    #se la richiesta non e' eseguita dal sistema interno allora recupera i dati dell'utente
    if reserved == False:
        user_id = update["message"]["from"]["id"]

        if "username" in update["message"]["from"]:
            username = update["message"]["from"]["username"]
        else: 
            username = ""

        first_name = update["message"]["from"]["first_name"]

        if "last_name" in update["message"]["from"]:
            last_name = update["message"]["from"]["last_name"]

        if "language_code" in update["message"]["from"]:
            region = update["message"]["from"]["language_code"]

        chat_id = update["message"]["chat"]["id"]


        if "username" in update["message"]["chat"]:
            chat_name = update["message"]["chat"]["username"]
        elif "title" in update["message"]["chat"]:
            chat_name = update["message"]["chat"]["title"]
        
        chat_type = update["message"]["chat"]["type"]   

    print("Retrived update data")

    #prepara il dict da inserire nel db
    data_to_insert = {
        "hashtag": hashtag,
        "owner": { "id": user_id, "username": username, "first_name": first_name, "last_name": last_name,"region": region },
        "origin_chat": { "id": chat_id, "name": chat_name, "type": chat_type },
        "data": data,
        "reserved": reserved,
        "creation_date": datetime.datetime.utcnow(),
        "last_use_date": datetime.datetime.utcnow(),
        "use_count": 0,
        "reports": []
    }

    #in caso sia da riservare un hashtag controlla che non via sia gia nel db, se esiste cancellalo
    if reserved == True:
        res = db.hashtags.find_one({"hashtag": hashtag})
        if res is not None:
            #mantieni il contatore di usi
            data_to_insert["use_count"] = res["use_count"] 

    db.hashtags.update({"hashtag": hashtag}, data_to_insert, upsert=True)
    print("Created document "+ hashtag)


#cancella un documento
def adm_delete_tag(hashtag):
    print("count#requests.delete_hashtag")
    hashtag = hashtag.lower()
    db.hashtags.delete_one({"hashtag":hashtag})
    print("Deleted doc "+hashtag)
