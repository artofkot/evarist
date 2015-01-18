# -*- coding: utf-8 -*-
# all the imports. For small applications it’s a possibility to drop the configuration directly 
# into the module which we will be doing here. However a cleaner solution would be 
# to create a separate .ini or .py file and load that or import the values from there.
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo

# configuration:
DEBUG = True
# !!!! Never leave debug=True in a production system
SECRET_KEY = 'Shatahosik'
USERNAME = 'admin'
PASSWORD = 'default'

MONGO_URI="mongodb://heroku_app33294458:ohleelvsddqissik3r7nn74ge@ds031671.mongolab.com:31671/heroku_app33294458"
# I generated this URI using service mongolab in heroku, see https://devcenter.heroku.com/articles/mongolab
# locally on your computer when you install mongodb and then run it with command
#   $mondod
#   or even 
#   $mongod -dbpath ./databases/mongodb/
# then this the most important config variable MONGO_URI is equal to "mongodb://localhost:27017/"




# create our little application :)
app = Flask(__name__)

# from_object() will look at the given object (if it’s a string it will import it) and 
# then look for all uppercase variables defined there. In our case, the configuration we 
# just wrote a few lines of code above. You can also move that into a separate file.
app.config.from_object(__name__)
# Usually, it is a good idea to load a configuration from a configurable file. 
# This is what from_envvar() can do, replacing the from_object() line above:
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
# That way someone can set an environment variable called FLASKR_SETTINGS to specify a config file 
# to be loaded which will then override the default values. The silent switch just tells 
# Flask to not complain if no such environment key is set.



mongo = PyMongo(app)
# PyMongo connects to the MongoDB server running on MONGO_URI, and assumes a default database name of app.name 
# (i.e. whatever name you pass to Flask). This database is exposed as the db attribute.

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/indexBitStarter')
def indexBitStarter():
    return render_template('indexBitStarter.html')

@app.route('/flaskr')
def show_entries():
    posts=mongo.db.posts.find()
    entries = [dict(title=entry["title"], text=entry["text"]) for entry in posts]
    return render_template('show_entries.html', entries=entries)

@app.route('/flaskr_add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    posts=mongo.db.posts
    posts.insert({"title":request.form['title'], "text":request.form['text']})
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/flaskr_login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/flaskr_logout')
def logout():
    session.pop('logged_in', None) # We use a neat trick here: if you use the pop() method of the dict and pass a second parameter to it (the default), the method will delete the key from the dictionary if present or do nothing when that key is not in there. This is helpful because now we don’t have to check if the user was logged in.
    flash('You were logged out')
    return redirect(url_for('show_entries'))



if __name__ == '__main__':
    app.run()