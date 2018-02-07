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

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import json
import dbManager

cred = credentials.Certificate(dbManager.get_firebase_json())
firebase_admin.initialize_app(cred)

db = firestore.client()

#invia a firebase i dati passati dell'utente come parametro
def send_user_data(user_id, name, username, tags):
    doc_ref = db.collection(u'users').document(str(user_id))
    doc_ref.set({
        u'name': name,
        u'username': username,
        u'tags': tags
    })
