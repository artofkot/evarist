import os, json


MONGO_URI=os.environ.get("MONGO_URI")
SECRET_KEY = os.environ.get("LISTKI_SECRET_KEY")
DEBUG=False

CLIENT_SECRETS_JSON = json.loads(os.environ.get("CLIENT_SECRETS_JSON"))
CLIENT_ID = CLIENT_SECRETS_JSON['web']['client_id']


# CLIENT_ID = json.loads(
#     open('client_secrets.json', 'r').read())['web']['client_id']

# tik = json.loads(
#     open('client_secrets.json', 'r').read())

# tik= json.dumps(tik)

# print tik + '\n'

# CLIENT_ID = json.loads(tik)['web']['client_id']


APPLICATION_NAME = "Evarist"