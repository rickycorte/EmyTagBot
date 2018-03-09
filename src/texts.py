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

import json
import os 

my_path = os.path.abspath(os.path.dirname(__file__))
j_path =  os.path.join(my_path, "../data/language.json")

#carica il json dei testi
if not os.path.exists(j_path) or os.path.getsize(j_path) <= 0:
    print ("[CRITICAL ERROR]: Unable to load language file! Please check that data/language.json is present")
    exit(1)

language_fp = open(j_path)

language = json.load(language_fp)

language_fp.close()


# ottieni il testo associato al nome assegnato del json
# il code e' il codice regione di una specifica traduzione, se non trovato ritorna il testo di default
# se l'id non esiste restituisce un messaggio di errore
def get_text(id, code = "default"):
    if not id in language:
        return "Missing language key: "+id
    
    if code in language[id]:
        return language[id][code]
    else:
        return language[id]["default"]