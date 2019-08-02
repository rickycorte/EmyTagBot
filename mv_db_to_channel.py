

from pymongo import MongoClient
from bson.objectid import ObjectId
from telegram.ext import Updater
import time

CHANNEL_ID = int(-1001255174148)

client = MongoClient('~')
db = client['~'] 


updater = Updater('~')


def send_message(item):

   result = item["data"]

   if result["type"] == "text":
      updater.bot.sendMessage(CHANNEL_ID, item["hashtag"] + ":\n" + result["data"])

   if result["type"] == "image":
      updater.bot.sendPhoto(CHANNEL_ID, result["data"], caption=item["hashtag"])

   if result["type"] == "gif":
      updater.bot.sendDocument(CHANNEL_ID, result["data"], caption=item["hashtag"])

   if result["type"] == "sticker":
      updater.bot.sendSticker(CHANNEL_ID, result["data"])

   if result["type"] == "audio":
      updater.bot.sendAudio(CHANNEL_ID, result["data"])

   if result["type"] == "voice":
      updater.bot.sendVoice(CHANNEL_ID, result["data"], caption=item["hashtag"])

   if result["type"] == "video":
      updater.bot.sendVideo(CHANNEL_ID, result["data"], caption=item["hashtag"])



for document in db.hashtags.find():
   send_message(document)
   print("Sent tag " + document["hashtag"])
   time.sleep(5) #dont hit telegram limits

updater.bot.sendMessage(CHANNEL_ID, """Purtroppo il momento di decidere se tenete o meno online il bot e' giunto,
   i numeri parlano chiaro, Emy ha un uso bassissimo e occupa molte risorse.
   Quindi dopo circa un anno e mezzo di servizio ho deciso di sospendere il suo funzionamento.
   \n\nMi spiace davvero che Emy e' stata di aiuto e di intrattenimento a poche persone,
   quando pensai per la prima volta a Emy ero davvero eccittato e felice di poter rendere 'piu vive' le chat dando una piu forte funzionalita' agli hashtag.
   \nSperavo di poter creare un modo nuovo e unico di scoprire ed esplorare i tag creati dal mondo intero stando nella propria chat di gruppo e facendosi due risate.
   \n\nMi spiace davvero che Emy non sia riuscita a creare nulla di quello che avevo sperato.
   \n\nGrazie per aver usato Emy per tutto questo tempo!\nSpero ti sia divertito ad usare Emy e che faccia tesoro dei tag presenti in questo canale e di questo anno e mezzo.""")
    