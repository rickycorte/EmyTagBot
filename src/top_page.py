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
import pymongo
import os
import firebase

print("~~~ Updating web top list ~~~")

list_size = int( os.environ.get('WEB_TOP_TAG_LIST_SIZE', 100))

client = MongoClient( os.environ.get('MONGODB_URI', 'error') )

db = client[ os.environ.get('DB_NAME', 'EmyTagBot') ] 

tags = []

res = db.hashtags.find().sort([("use_count",-1)]).limit(list_size)

for itm in res:
    tags.append(
        {
            "tag": itm["hashtag"],
            "use": itm["use_count"]
        }
        )

firebase.send_top_tags(tags)
print ("pushed "+str(res.count(True))+" tags")
print("~~~ Web top list updated ~~~")