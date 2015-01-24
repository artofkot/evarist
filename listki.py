# -*- coding: utf-8 -*-
# all the imports. For small applications it’s a possibility to drop the configuration directly 
# into the module which we will be doing here. However a cleaner solution would be 
# to create a separate .ini or .py file and load that or import the values from there.
import os
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from flaskr import flaskr 



# create our little application :)
app = Flask('listki')
app.register_blueprint(flaskr)
# configuration
app.config.update(dict(
    # MONGO_URI="mongodb://localhost:27017/",
    DEBUG=True, # !!!! Never leave debug=True in a production system
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
    #MONGO_DBNAME='flaskrrr' #The database name to make available as the db attribute. Default: app.name
))
app.config["SECRET_KEY"] = os.environ.get("LISTKI_SECRET_KEY")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

# I generated this URI using service mongolab in heroku, see https://devcenter.heroku.com/articles/mongolab
# locally on your computer when you install mongodb and then run it with command
#   $mondod
#   or even 
#   $mongod -dbpath ./databases/mongodb/
# then this the most important config variable MONGO_URI is equal to "mongodb://localhost:27017/"



# another possibility of configuration
# app.config.from_pyfile('config_listki.cfg', silent=True)

# this can be used if your app is package (used for larger apps), not object
# app.config.from_object('yourapplication.default_settings')

# Usually, it is a good idea to load a configuration from a configurable file. 
# This is what from_envvar() can do, replacing the from_object() line above:
# app.config.from_envvar('FLASKR_SETTINGS', silent=True) # (these should be configuration defaults)
# export YOURAPPLICATION_SETTINGS=/path/to/settings.cfg
# That way someone can set an environment variable called FLASKR_SETTINGS to specify a config file 
# to be loaded which will then override the default values. The silent switch just tells 
# Flask to not complain if no such environment key is set.



# def connect_mongodb():
#     """Connects to the specific database."""
#     mongo = PyMongo(app)
#     # PyMongo connects to the MongoDB server running on MONGO_URI, and assumes a default database name of app.name 
#     # (i.e. whatever name you pass to Flask). This database is exposed as the db attribute.
#     return mongo

# def get_db():
#     """Opens a new database connection if there is none yet for the
#     current application context.
#     """
#     if not hasattr(g, 'mongodb'):
#         g.mongodb = connect_mongodb()
#     return g.mongodb

# @app.teardown_appcontext
# def close_db(error):
#     """Closes the database again at the end of the request."""
#     mongo.close()

mongo = PyMongo(app)
# PyMongo connects to the MongoDB server running on MONGO_URI, and assumes a default database name of app.name 
# (i.e. whatever name you pass to Flask). This database is exposed as the db attribute.

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/startertry')
def startertry():
    return render_template('startertry.html')

@app.route('/indexBitStarter')
def indexBitStarter():
    return render_template('bitstarter/indexBitStarter.html')

@app.route('/flaskr')
def show_entries():
    # print mongo.db.collection_names()
    # for i in mongo.db.posts.find():
    #     print i
    posts=mongo.db.posts.find()
    entries = [dict(title=entry["title"], text=entry["text"]) for entry in posts]
    return render_template('flaskr/show_entries.html', entries=entries)

@app.route('/flaskr_add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    # posts=mongo.db.posts
    # posts.insert({"title":request.form['title'], "text":request.form['text']})
    mongo.db.posts.insert({"title":request.form['title'], "text":request.form['text']})
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
    return render_template('flaskr/login.html', error=error)

@app.route('/flaskr_logout')
def logout():
    session.pop('logged_in', None) 
    # We use a neat trick here:
    # if you use the pop() method of the dict and pass a second parameter to it (the default),
    # the method will delete the key from the dictionary if present or
    # do nothing when that key is not in there.
    # This is helpful because now we don’t have to check if the user was logged in.
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__ == '__main__':
    app.run()