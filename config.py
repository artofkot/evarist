# -*- coding: utf-8 -*-
import os, json

ADMINS = ['artofkot@gmail.com','alexej.levin@gmail.com ']
MONGO_URI=os.environ.get("MONGO_URI")
SECRET_KEY = os.environ.get("LISTKI_SECRET_KEY")
DEBUG=False

# for google OAuth
CLIENT_SECRETS_JSON = json.loads(os.environ.get("CLIENT_SECRETS_JSON"))
CLIENT_ID = CLIENT_SECRETS_JSON['web']['client_id']

BABEL_DEFAULT_LOCALE='ru'
BABEL_DEFAULT_TIMEZONE='UTC+0300'


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

# FB_CLIENT_SECRETS_JSON = json.loads(os.environ.get("FB_CLIENT_SECRETS_JSON"))
# FB_APP_ID = FB_CLIENT_SECRETS_JSON['web']['app_id']


# CLIENT_ID = json.loads(
#     open('client_secrets.json', 'r').read())['web']['client_id']

# tik = json.loads(
#     open('client_secrets.json', 'r').read())

# tik= json.dumps(tik)

# print tik + '\n'

# CLIENT_ID = json.loads(tik)['web']['client_id']


APPLICATION_NAME = "Evarist"