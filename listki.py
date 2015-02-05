# -*- coding: utf-8 -*-
# all the imports. For small applications it’s a possibility to drop the configuration directly 
# into the module which we will be doing here. However a cleaner solution would be 
# to create a separate .ini or .py file and load that or import the values from there.
from bson.objectid import ObjectId
import os, datetime, urllib, urllib2
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from login_module import login_module


# create our little application :)
app = Flask('listki')

app.register_blueprint(login_module)
# configuration
app.config.update(dict(
    # MONGO_URI="mongodb://localhost:27017/",
    DEBUG=False, # !!!! Never leave debug=True in a production system
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
    #MONGO_DBNAME='flaskrrr' #The database name to make available as the db attribute. Default: app.name
))
app.config["SECRET_KEY"] = os.environ.get("LISTKI_SECRET_KEY") #for hashing passwords and sessions
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

# I generated this URI using service mongolab in heroku, see https://devcenter.heroku.com/articles/mongolab
# locally on your computer when you install mongodb and then run it with command
#   $mondod
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

@app.before_request
def before_request():
    g.mongo = mongo
    g.db=mongo.db
# PyMongo connects to the MongoDB server running on MONGO_URI, and assumes a default database name of app.name 
# (i.e. whatever name you pass to Flask). This database is exposed as the db attribute.


@app.route('/')
def index():
    return redirect(url_for('home'))


@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/set_theory')
def set_theory():
    return render_template('problem_sets/set_theory.html')

@app.route('/set_theory/<int:problem_number>')
def problem(problem_number):
    # problem_set={"title":"Set Theory",'problems':
    # [   {"title":"Problem 1",
    #      'text':'How many elements are in the set {1,2,{1,2}}?',
    #      'posts':[{'date':datetime.datetime.utcnow(),'author':'Artem','text':'nice problem','type':'comment'}] 
    #       #type could be later also feedback or solution
    #     }
    # ]}
    # g.db.problems_sets.insert(problem_set)
    
    # for i in g.db.problems_sets.find():
    #     print i

    problem_set=g.db.problems_sets.find_one({'title':'Set Theory'})

    posts=problem_set['problems'][problem_number-1]['posts']
    posts.reverse()
    # d=datetime.datetime.now()
    # print d['month']
    title=problem_set['problems'][problem_number-1]['title']
    text=problem_set['problems'][problem_number-1]['text']

    return render_template('problem_sets/problem.html', problem_number=str(problem_number), 
                            problem_set="Set Theory",title=title,text=text,posts=posts)

@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if 'username' not in session:
        abort(401)
    # posts=g.mongo.db.posts
    # posts.insert({"title":request.form['title'], "text":request.form['text']})
    else:
        problem_set=request.args.get('problem_set')
        problem_number=request.args.get('problem_number')


        # problem_set={"title":"Set Theory",'problems':
        # [   {"title":"Problem 1",
        #      'text':'How many elements are in the set {1,2,{1,2}}?',
        #      'posts':[{'date':datetime.datetime.utcnow(),'author':'Artem','text':'nice problem','type':'comment'}] 
        #       #type could be later also feedback or solution
        #     }
        # ]}
        psdoc=g.db.problems_sets.find_one({"title":problem_set})
        psdoc["problems"][int(problem_number)-1]['posts'].append({'date':datetime.datetime.utcnow(), 
                                                             'author':session['username'],
                                                             "text":request.form['text'],
                                                             'type':'comment'
                                                            })
        g.db.problems_sets.update({"title":problem_set}, {"$set": psdoc}, upsert=False)
        
        flash('New entry was successfully posted')
        return redirect(url_for('problem',problem_number=problem_number))



@app.route('/comments')
def show_entries():
    # print g.mongo.db.collection_names()
    # for i in g.mongo.db.posts.find():
    #     print i
    posts=g.mongo.db.posts.find()
    entries = [dict(title=entry["title"], text=entry["text"]) for entry in posts]
    entries.reverse()
    return render_template('show_entries.html', entries=entries)

@app.route('/comments_add', methods=['GET','POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    # posts=g.mongo.db.posts
    # posts.insert({"title":request.form['title'], "text":request.form['text']})
    g.mongo.db.posts.insert({"title":request.form['title'], "text":request.form['text']})
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/startertry')
def startertry():
    return render_template('startertry.html')

@app.route('/indexBitStarter')
def indexBitStarter():
    return render_template('bitstarter/indexBitStarter.html')

if __name__ == '__main__':
    app.run()