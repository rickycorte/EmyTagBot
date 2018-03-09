# EmyTagBot

Emy is a Telegram bot meant to create user-based hashtags with text, images, audios, sticker, videos.

Try her right now: https://t.me/emytagbot

## How it works
Users can assign content to an arbitrary tag that is still free (not assigned to another user). Then when Emy finds that tag in the messages of a chat immediatly sends the data atteched to it!

I know, you did not understand a bit of what I said. Just play a bit with Emy and you will know how to use her.

## Features
* Works on Heroku
* Automatic database cleanup script
* Keep track of active chats
* Environment variables, database, credentials check on boot

### Users:
* Claim unlimited tags
* Tags types: text, sticker, image, gif, audio, vocal, video
* Top tag list (in chat and web)
* Edit tag names (owned tag only)
* Remove tegs (owned tag only)
* Report tags with a custom message (1 report/user for every tag)
* Webpage with tag list (owned tag only)
* See tag data in chats
* Get tag basic infos (use count, creation date, ...)
* Command aliases (like set)

### Admin:
* Admin auth (based on Telegram user id)
* Set tag data (forced)
* Reserve tag (forced)
* Delete tag (forced)
* Admin channel where the Emy asks for actions on reported tags
* User account limitation/ban
* Get full tag infos
* Broadcast message

## Commands

### Users:
* `/claim <tag>` or `/set <tag>`: claim a tag (quote a message before you run this command)
* `/edit <old_tag> <new_tag>`: move *old_tag* to *new_tag*
* `/remove <tag>` or `/rm <tag>`: delete a tag
* `/info <tag>`: get *tag* informations
* `/help`: show help message
* `/top`: show top tags
* `/report <tag> <message>`: report a tag with the specified message
* `/mytags`: get a link to a web page that shows all of your current tags

### Admins:
* `/aset <tag>`: claim/override a tag (quote a message before you run this command)
* `/arm <tag>`: remove a tag
* `/ars <tag>`: reserve (override if needed) a tag
* `/ainfo <tag>`: show full tag infos
* `/bcast <message>`: broadcast message to all active chats

## Requirements
* Python 3.6
* Firebase account
* MongoDB instance
* Telegram Bot Token
* Cron jobs (or equivalent). 
* PipEnv

## Dependencies
* python-telegram-bot
* pymongo
* firebase-admin 

## Environment variables

[REQUIRED] `TOKEN`: telegram bot token

[REQUIRED] `PORT`: post to bind

[REQUIRED] `APP_LINK`: link to use to set webhook (/token) will be added

[REQUIRED] `ADMIN`: admin id (telegram id)

[REQUIRED] `ADMIN_CHANNEL`: telegram channel id where Emy posts reports

[REQUIRED] `MONGODB_URI`: MongoDB url

[REQUIRED] `DB_NAME`: Database to use

`MAX_HASHTAG_SIZE`:  max length of a valid hashtag

`MAX_TEXT_SIZE`: max length of a text that can be assigned to a tag

`TAG_LIFE_TIME`: tag life in days

`TOP_LIST_SIZE`: number of elements to show in /top command

`RESERVED_TAG_PLACEHOLDER`: text used as placeholder when an admin reserve a tag

`MAX_REPORTS`: max number of reports that a user can add to a tag

`WARNS_BEFORE_BAN`: max number of warnings before account ban

`WEB_TOP_TAG_LIST_SIZE`:  number of elements to show in top page

`DEBUG`: set true if you want to run the bot with polling

## Setup Firebase
Add your firebase admin json as a document called `firebase` in your database

**Note:**
your firebase admin json is something like this:
```
{
    "type": "",
    "project_id": "",
    "private_key_id": "",
    "private_key": "",
    "client_email": "",
    "client_id": "",
    "auth_uri": "",
    "token_uri": "",
    "auth_provider_x509_cert_url": "",
    "client_x509_cert_url": ""
}
```

## Web Integration
This bot is deeply integrated with a custom website powered by firebase.

You can check its repo [here](https://github.com/rickycorte/EmyTagBot-Site).


## Run the bot
To execute your bot on your local machine run:

`pipenv install`

`pipenv shell`

`python src/main.py`

Create also two daily jobs

`python autoremove.py` to remove old tags and old chats

`python top_page.py` to update the top tags page
