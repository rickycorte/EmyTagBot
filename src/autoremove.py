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

print("~~~ Removing tags ~~~")

default_hashtag_lifetime = int( os.environ.get('TAG_LIFE_TIME', 5))

client = MongoClient( os.environ.get('MONGODB_URI', 'error') )

db = client[ os.environ.get('DB_NAME', 'EmyTagBot') ] 

remove_date_sep =  datetime.datetime.utcnow() - datetime.timedelta(days=default_hashtag_lifetime)

hashs = db.hashtags.find({"reserved":False})
for tag in hashs:
    if tag["last_use_date"] < remove_date_sep:
        print ("Deleted "+tag["hashtag"])
        db.hashtags.delete_one({"_id":tag["_id"]})

print("~~~ Removing tags: DONE ~~~")