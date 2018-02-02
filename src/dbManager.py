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
from bson.objectid import ObjectId
import datetime
import os
import adminChannel

HASHTAG_LIFETIME = int( os.environ.get('TAG_LIFE_TIME', 5))

client = MongoClient( os.environ.get('MONGODB_URI', 'error') )

top_list_size = int( os.environ.get('TOP_LIST_SIZE', 10) )

db = client[ os.environ.get('DB_NAME', 'EmyTagBot') ] 

reserved_tag_placeholder_name = os.environ.get('RESERVED_TAG_PLACEHOLDER', 'EmyTagBot')

MAX_REPORTS = int( os.environ.get('MAX_REPORTS', 1))

WARNS_BEFORE_BAN = int( os.environ.get('WARNS_BEFORE_BAN', 3))

#controlla se user_id puo claimare un determinato hashtag
# 0 = si
# 1 = no perche e' di un altro utente
# 2 = e' riservato
def can_write_hashtag(hashtag, user_id):
    print("checking hashtag write permission for "+ hashtag)
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
    print("Getting top list")
    result = []
    res = db.hashtags.find().sort([("use_count",-1)]).limit(top_list_size)
    if not res or res is None:
        return None

    for itm in res:
        result.append({"hashtag":itm["hashtag"], "uses":itm["use_count"]})

    return result


#cerca un hashtag nel database
def search_hashtag(hashtag):
    hashtag = hashtag.lower()
    print("Searching tag "+ hashtag)

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
def add_report(bot, hashtag, user_id, report_text):
    hashtag = hashtag.lower()
    print("Adding report to "+hashtag)
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

    #aggiorna il json locale da passare al canale admin se necessario
    res["resports"] = reports

    #aggiorna il database
    db.hashtags.update_one( {"_id": res["_id"]}, 
        {"$set": 
            {
                "reports":reports
            } 
        }, upsert=False)

    print("created report")

    if len(reports) >= MAX_REPORTS:
        adminChannel.send_report_data(bot, res)

    return 0

#inserisce un oggetto data {"type": "text/image/gif/sticker", "data":"..."} nel database
def create_hashtag(hashtag, update, data, reserved):

    hashtag = hashtag.lower()

    #i messaggi senza username non sono accettabili se non si tratta di una richiesta del sistema
    if reserved == False and update.message.from_user is None: 
        return 

    print("Creating hashtag "+hashtag)

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
        user_id = update.message.from_user.id

        if update.message.from_user.username is not None:
            username = update.message.from_user.username
        else: 
            username = ""

        first_name = update.message.from_user.first_name

        if update.message.from_user.last_name is not None:
            last_name = update.message.from_user.last_name

        if update.message.from_user.language_code is not None:
            region = update.message.from_user.language_code

        chat_id = update.message.chat.id


        if update.message.chat.username is not None:
            chat_name = update.message.chat.username
        elif update.message.chat.title is not None:
            chat_name = update.message.chat.title
        
        chat_type = update.message.chat.type

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
def delete_hashtag(hashtag):
    print("Deleting "+hashtag)
    hashtag = hashtag.lower()
    db.hashtags.delete_one({"hashtag":hashtag})
    print("Deleted doc "+hashtag)


#restituisce le info di un hashtag in un dict
# none se non ha trovato nulla
def get_hashtag_info(hashtag):
    hashtag = hashtag.lower()

    print("getting info of "+ hashtag)

    res = db.hashtags.find_one({"hashtag": hashtag})
    if res is None:
        return None
    else:
        return res


#cambia un hashtag in un altro
#restituisce 1 se l'operazione e' andata a buon fine 
#0 se non e' stato possibile trovare il tag vecchio o esite gia un tag con il nome nuovo
def change_hashtag(old_tag, new_tag):
    old_tag = old_tag.lower()
    new_tag = new_tag.lower()

    print("trying to move "+old_tag +" to "+new_tag)

    res = db.hashtags.find_one({"hashtag": old_tag})

    #controlla che non ci sia gia anche l'altro tag
    check = db.hashtags.find_one({"hashtag": new_tag})

    if res is None or check is not None:
        print ("Failed move")
        return 0 

    db.hashtags.update_one( {"_id": res["_id"]}, 
        {"$set": 
            {
                "hashtag": new_tag
            } 
        }, upsert=False)
    return 1
    print ("move done")
    

#calcola la differenza in giorni od ore dalla data passata come parametro a oggi
def calculate_delta_now(old_dt):
    dt = datetime.datetime.utcnow() - old_dt 
    hours_left = int( HASHTAG_LIFETIME * 24 - dt.total_seconds()/3600)
    reply = ""
    if hours_left >= 24:
        reply = str( int(hours_left/24) )+" days"
    else:
        if hours_left <= 3:
            reply = "a few moments"
        else:
            reply = str(hours_left)+" hours"

    return reply


#restituisce l'array di tag che ha l'utente
#array vuoto se non ne possiede
def get_user_hashtags(user_id):
    res = db.hashtags.find({ "owner.id": user_id })

    hashs = []
    for tag in res:
        hashs.append(
                {
                "tag": tag["hashtag"],
                "use": tag["use_count"],
                "type": tag["data"]["type"],
                "creation": tag["creation_date"].strftime("%d/%m/%y"),
                "expire": calculate_delta_now(tag["last_use_date"]),
                }
            )
    return hashs


#restituisce il json 
def get_firebase_json():
    res = db.firebase.find_one()
    del res["_id"]
    return res


#cerca un tag in base all'id di mongodb passato
def get_tag_by_id(tag_id):
    return db.hashtags.find_one({"_id": ObjectId(tag_id)})


#cancella tutti i report del tag passato per id
#restituisce il nuovo documento
def remove_reports(tag_id):
    res = get_tag_by_id(tag_id)

    #aggiorna il json locale da passare al canale admin se necessario
    res["resports"] = []

    #aggiorna il database
    db.hashtags.update_one( {"_id": res["_id"]}, 
        {"$set": 
            {
                "reports": []
            } 
        }, upsert=False)

    print("cleared reports")
    return res


#cancella un tag per id
def delete_tag_by_id(tag_id):
    print("Deleted tag by id")
    db.hashtags.delete_one({"_id":ObjectId(tag_id)})


#warna un utente, se l'utente supera il limite di warning viene bannato in automatico
# restituisce 1 se warnato
# restituisce 2 se bannatp
def warn_user(user_id):

    res = db.users.find_one({"id": user_id})

    warns = 0

    if res is not None:
        warns = res["warnings"]
    
    warns += 1


    if warns < WARNS_BEFORE_BAN:
        db.users.update_one( {"id": user_id}, 
            {"$set": 
                {
                    "warnings": warns,
                    "banned": False
                } 
            },  upsert=True)

        print("warned user "+str(user_id)+" ("+str(warns)+" warns)")
        return 1

    else:
        ban_user(user_id)
        return 2


#banna l'utente in modo permanente
def ban_user(user_id):
    db.users.update_one( {"id": user_id}, 
        {"$set": 
            {
                "warnings": WARNS_BEFORE_BAN,
                "banned": True
            } 
        }, upsert=True)
    print("banned user "+str(user_id))


#restituisce true se l'utente e' stato bannato
def is_user_banned(user_id):

    res = db.users.find_one({"id": user_id})
    if res is None or res["banned"] == False:
        return False

    return True
