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
import logging
from telegram.ext import Updater, CommandHandler

TOKEN = os.environ.get('TOKEN', 'token')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)

################################################################################################################################


#il comando start, sarebbe meglio mettere una frase piu decente ma vbb <3
def start(bot, update):
    update.message.reply_text('Quanto vorrei morire :3')


#comando claim
def claim(bot, update):
    update.message.reply_text('This function is not available right now')


#comando remove
def remove(bot, update):
    update.message.reply_text('This function is not available right now')


#comando info
def info(bot, update):
    update.message.reply_text('This function is not available right now')


#comando help che mostra un messaggio di aiuto
def help(bot, update):
    update.message.reply_text('Help command')


#comando top
def top(bot, update):
    update.message.reply_text('This function is not available right now')


#comando warns
def warns(bot, update):
    update.message.reply_text('This function is not available right now')


#comando report
def report(bot, update):
    update.message.reply_text('This function is not available right now')


### ADMIN ###

def admin_set(bot, update):
    update.message.reply_text('ADMIN: This function is not available right now')


def admin_remove(bot, update):
    update.message.reply_text('ADMIN: This function is not available right now')


def admin_claim(bot, update):
    update.message.reply_text('ADMIN: This function is not available right now')

################################################################################################################################

def main():

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    #registra comandi
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("claim", claim))
    dispatcher.add_handler(CommandHandler("remove", remove))
    dispatcher.add_handler(CommandHandler("info", info))

    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("top", top))

    dispatcher.add_handler(CommandHandler("warns", warns))
    dispatcher.add_handler(CommandHandler("report", report))

    #comandi admin
    dispatcher.add_handler(CommandHandler("aset", admin_set))
    dispatcher.add_handler(CommandHandler("aremove",start))
    dispatcher.add_handler(CommandHandler("areserve",start))

    # start bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()