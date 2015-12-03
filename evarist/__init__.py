# -*- coding: utf-8 -*-
from bson.objectid import ObjectId
import os, sys, pymongo, re, time
from flask import Flask, request, session, g, redirect, url_for
from flask.ext.babel import Babel
from flask.ext.bcrypt import Bcrypt
from flask.ext.mail import Mail
from controllers.user import user
from controllers.workflow import workflow
from controllers.admin import admin
import logging

from evarist.models.mongoengine_models import db, User

# creating an app
app = Flask(__name__)

# adding different parts of app
app.config.from_object('config')
app.register_blueprint(user)
app.register_blueprint(workflow)
app.register_blueprint(admin)

#connecting to database, Mongoengine
db.init_app(app)


# connecting to mongodb via pymongo
client = pymongo.MongoClient(app.config['MONGO_URI'])
settings=pymongo.uri_parser.parse_uri(app.config['MONGO_URI'])
dbpymongo = client[settings['database']]

# for translation
babel = Babel(app)

# making mail
mail = Mail(app)

# for hashing passwords
bcrypt=Bcrypt(app)

# for logging python errors in production, see them in papertrail
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

# emailing error while in production
if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(mailhost=('smtp.mandrillapp.com',587),
                            fromaddr=app.config['MANDRILL_USERNAME'],
                            toaddrs=app.config['ADMINS'],
                            subject='Error on Evarist (production)!',
                            credentials=(app.config['MANDRILL_USERNAME'],app.config['MANDRILL_APIKEY']),
                            secure=None)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)



# connecting to database before every request comes
@app.before_request
def before_request():
    # store user in proxy using mongoengine
    try: 
        g.user=User.objects.get(id=ObjectId(session.get('id')))
    except: 
        session.pop('id', None) 
        session.pop('gplus_id', None)
        session.pop('access_token', None)
        g.user={}

    # for timing of response
    g.start=time.time()

    # passing pymongo database in each request
    g.db=dbpymongo

    #connection in order to send emails
    g.mail=mail
    
    # for accessing locale in each request
    g.locale = get_locale()


    

# this function return language for babel
@babel.localeselector
def get_locale():
    if session.get('lang')=='en':
        return 'en'
    else:
        return 'ru'

    # use this after you add functionality to choose language for each user
    #
    # if a user is logged in, use the locale from the user settings
    # user = getattr(g, 'user', None)
    # if user is not None:
    #     return user['locale']

    # you can also try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    # return request.accept_languages.best_match(['ru', 'en'])


# for timezone
#
# @babel.timezoneselector
# def get_timezone():
#     user = getattr(g, 'user', None)
#     if user is not None:
#         return user.timezone