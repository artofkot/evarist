# -*- coding: utf-8 -*-
import os, json

APPLICATION_NAME = "Evarist"

MONGO_URI=os.environ.get("MONGO_URI")
SECRET_KEY = os.environ.get("LISTKI_SECRET_KEY")
#next one is for email confirmation
SECURITY_PASSWORD_SALT=os.environ.get("SECURITY_PASSWORD_SALT")
DEBUG=False

# for google OAuth
CLIENT_SECRETS_JSON = json.loads(os.environ.get("CLIENT_SECRETS_JSON"))
CLIENT_ID = CLIENT_SECRETS_JSON['web']['client_id']

#config for flask-babel
BABEL_DEFAULT_LOCALE='ru'
BABEL_DEFAULT_TIMEZONE='UTC+0300'

# getting MANDRILL (email provider) username and password 
# could be the case that its better to use gmail account
MANDRILL_APIKEY=os.environ.get("MANDRILL_APIKEY")
MANDRILL_USERNAME=os.environ.get("MANDRILL_USERNAME")

# config for flask-mail
MAIL_SERVER='smtp.mandrillapp.com'#default ‘localhost’
MAIL_PORT = 587
# MAIL_USE_TLS = default False
# MAIL_USE_SSL = default False
# MAIL_DEBUG = default app.debug
MAIL_USERNAME = MANDRILL_USERNAME
MAIL_PASSWORD = MANDRILL_APIKEY
MAIL_DEFAULT_SENDER = ('Evarist',MANDRILL_USERNAME)

ADMINS = ['artofkot@gmail.com','alexej.levin@gmail.com']

# for picture upload
CLOUDINARY_URL=os.environ.get("CLOUDINARY_URL")
