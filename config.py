import os, json

ADMINS = ['artofkot@gmail.com']
MONGO_URI=os.environ.get("MONGO_URI")
SECRET_KEY = os.environ.get("LISTKI_SECRET_KEY")
DEBUG=False

CLIENT_SECRETS_JSON = json.loads(os.environ.get("CLIENT_SECRETS_JSON"))
CLIENT_ID = CLIENT_SECRETS_JSON['web']['client_id']

BABEL_DEFAULT_LOCALE='ru'
BABEL_DEFAULT_TIMEZONE='UTC+0300'


MANDRILL_APIKEY=os.environ.get("MANDRILL_APIKEY")
MANDRILL_USERNAME=os.environ.get("MANDRILL_USERNAME")

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