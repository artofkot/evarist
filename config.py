import os, json


MONGO_URI=os.environ.get("MONGO_URI")
SECRET_KEY = os.environ.get("LISTKI_SECRET_KEY")
DEBUG=False

CLIENT_ID = os.environ.get("CLIENT_ID")

# CLIENT_ID = json.loads(
#     open('client_secrets.json', 'r').read())['web']['client_id']


APPLICATION_NAME = "Evarist"