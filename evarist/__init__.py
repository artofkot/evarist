# -*- coding: utf-8 -*-
from bson.objectid import ObjectId
import os, sys, pymongo, re
from flask import Flask, request, session, g, redirect, url_for
from flask.ext.babel import Babel
from flask.ext.mail import Mail
from controllers.user import user
from controllers.workflow import workflow
from controllers.admin import admin
import logging

# creating an app
app = Flask('evarist')

# adding different parts of app
app.config.from_object('config')
app.register_blueprint(user)
app.register_blueprint(workflow)
app.register_blueprint(admin)

# connecting to mongodb
client = pymongo.MongoClient(app.config['MONGO_URI'])
settings=pymongo.uri_parser.parse_uri(app.config['MONGO_URI'])
db = client[settings['database']]

# for translation
babel = Babel(app)

# making mail
mail = Mail(app)

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
    

    # passing database in each request
    g.db=db

    if session.get('_id'):
        g.user=g.db.users.find_one({'_id':ObjectId(session['_id'])})
        if g.user==None: g.user={}
    else: g.user={}

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