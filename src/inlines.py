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

from uuid import uuid4

from telegram import InlineQueryResultArticle, ParseMode, InputTextMessageContent
import dbManager
import telegram
import string
import os


checker = string.ascii_letters + string.digits+"_#"

MAX_HASHTAG_SIZE = int( os.environ.get('MAX_HASHTAG_SIZE', 128) )

def is_allowed_string(text):

    for ch in text:
        if not ch in checker:
            return False
    
    return True


#crea l'apposita risposta per la query inline a partire da un json preso da mongodb
def make_result_from_db_entry(db_entry):


    data = db_entry["data"]

    dbManager.inline_update_tag(db_entry)

    if data["type"] == "text":
        return InlineQueryResultArticle(
                id=uuid4(),
                title=db_entry["hashtag"]+": "+data["data"],
                input_message_content=InputTextMessageContent(data["data"])
            )


    if data["type"] == "image":
        return telegram.InlineQueryResultCachedPhoto(
                id=uuid4(),
                title=db_entry["hashtag"],
                photo_file_id=data["data"],
                caption=db_entry["hashtag"]
            )


    if data["type"] == "gif":
        return telegram.InlineQueryResultCachedDocument(
                id=uuid4(),
                title=db_entry["hashtag"],
                document_file_id=data["data"],
                caption=db_entry["hashtag"]
            )


    if data["type"] == "sticker":
        return telegram.InlineQueryResultCachedSticker(
                id=uuid4(),
                title=db_entry["hashtag"],
                sticker_file_id=data["data"]
            )


    if data["type"] == "audio":
        return telegram.InlineQueryResultCachedAudio(
                id=uuid4(),
                title=db_entry["hashtag"],
                audio_file_id=data["data"],
                caption=db_entry["hashtag"]
            )
  

    if data["type"] == "voice":
        return telegram.InlineQueryResultCachedVoice(
                id=uuid4(),
                title=db_entry["hashtag"],
                voice_file_id=data["data"],
                caption=db_entry["hashtag"]
            )


    if data["type"] == "video":
        return telegram.InlineQueryResultCachedVideo(
                id=uuid4(),
                title=db_entry["hashtag"],
                video_file_id=data["data"],
                caption=db_entry["hashtag"]
            )


#handler inline query
def inline_query(bot, update):
    query_text = update.inline_query.query

    #controlla che la query sia accettabile
    if not is_allowed_string(query_text):
        query_text = ""

    #controlla lunghezza, e taglia se si raggiunge il limite
    if len(query_text) > MAX_HASHTAG_SIZE:
        query_text = query_text[0:MAX_HASHTAG_SIZE]

    results = []

    #crea la query di default con la lista dei tag in top
    if query_text == "":
        top_tags = dbManager.get_top_list()
        for tag in top_tags:
            results.append( make_result_from_db_entry(tag) )
    else:
        tags = dbManager.search_partial_tag(query_text)
        for tag in tags:
            results.append( make_result_from_db_entry(tag) )

    if query_text == "":
        query_text="default query"
    print ("replied to inline: "+query_text)

    update.inline_query.answer(results) 