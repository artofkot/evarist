# -*- coding: utf-8 -*-

# TODO:  (TALK TO LESHA BOUT THIS!)
# correct e-mail check
# requirements management
# validator in bootstrap
# labels

from bson.objectid import ObjectId
import os, datetime, urllib, urllib2,sys
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from controllers.user import user
from controllers.workflow import workflow
from controllers.admin import admin
from forms import SignInForm

app = Flask('listki')
app.config.from_object('config')
app.register_blueprint(user)
app.register_blueprint(workflow)
app.register_blueprint(admin)

# Usually, it is a good idea to load a configuration from a configurable file. 
# This is what from_envvar() can do, replacing the from_object() line above:
# app.config.from_envvar('FLASKR_SETTINGS', silent=True) # (these should be configuration defaults)
# export YOURAPPLICATION_SETTINGS=/path/to/settings.cfg
# That way someone can set an environment variable called FLASKR_SETTINGS to specify a config file 
# to be loaded which will the override the default values. The silent switch just tells 
# Flask to not complain if no such environment key is set.

mongo = PyMongo(app)
# print app.config['MONGO_DBNAME']

@app.before_request
def before_request():
    g.mongo = mongo
    g.db=mongo.db
    g.signin_form=SignInForm()
# mongo.cx  is connection object