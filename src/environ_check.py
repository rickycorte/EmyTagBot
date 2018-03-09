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
from pymongo import MongoClient


def check():
    #controlla che tutte le variabili necessarie siano state settate altrimenti chiudi il bot
    print("Checking required variables...")

    crit_vars = ['TOKEN','PORT','APP_LINK','ADMIN','ADMIN_CHANNEL','MONGODB_URI','DB_NAME']
    for itm in crit_vars:
        CURR_VAR = os.environ.get(itm, None)
        if CURR_VAR is None:
            print("[Critical] Missing " + itm + " var value. Closing bot.")
            exit(1)

    #controlla che le variabili accessorie siano state settate altrimenti printa un avviso
    print("Checking other variables...")

    misc_vars = ['MAX_HASHTAG_SIZE','MAX_TEXT_SIZE','TAG_LIFE_TIME','TOP_LIST_SIZE','RESERVED_TAG_PLACEHOLDER','MAX_REPORTS','WARNS_BEFORE_BAN','WEB_TOP_TAG_LIST_SIZE']
    for itm in misc_vars:
        CURR_VAR = os.environ.get(itm, None)
        if CURR_VAR is None:
            print("[Settings] Missing " + itm + " var value.")

    print("Checking database...")
    #controlla che sia possibile connetersi a mongodb
    client = None

    try:
        #controlla che mongodb vada
        client = MongoClient( os.environ.get('MONGODB_URI', 'error'), serverSelectionTimeoutMS=100 )
        res = client.server_info()
    except:
        print("[Critical] Can't connect to mongodb. Check it is up and running. Closing bot.")
        exit(2)
    
    print("Checking firebase credentials...")
    #controlla che ci siano le credenziali di firebase
    db = client[ os.environ.get('DB_NAME', 'EmyTagBot') ]
    res = db.firebase.find_one()
    if res is None:
        print("[Critical] Can't find firebase credentials. Closing bot.")
        exit(3)
    
    print("Check complete, starting bot")