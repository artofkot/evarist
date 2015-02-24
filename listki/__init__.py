# -*- coding: utf-8 -*-
# TODO:  (TALK TO LESHA BOUT THIS!)
# correct e-mail check
# requirements management
# dont delete stuff that works:
# wrong password error
# admin default
# how does auth work now?
# True/False
# validator in bootstrap
# labels

from bson.objectid import ObjectId
import os, datetime, urllib, urllib2,sys
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from controllers.login_module import login_module
from controllers.workflow import workflow

app = Flask('listki')
app.config.from_object('config')
app.register_blueprint(login_module)
app.register_blueprint(workflow)

# Usually, it is a good idea to load a configuration from a configurable file. 
# This is what from_envvar() can do, replacing the from_object() line above:
# app.config.from_envvar('FLASKR_SETTINGS', silent=True) # (these should be configuration defaults)
# export YOURAPPLICATION_SETTINGS=/path/to/settings.cfg
# That way someone can set an environment variable called FLASKR_SETTINGS to specify a config file 
# to be loaded which will then override the default values. The silent switch just tells 
# Flask to not complain if no such environment key is set.

mongo = PyMongo(app)
# print app.config['MONGO_DBNAME']

@app.before_request
def before_request():
    g.mongo = mongo
    g.db=mongo.db
# mongo.cx  is connection object



# @app.route('/')
# def index():
#     return redirect(url_for('home'))


# @app.route('/home')
# def home():
#     return render_template('home.html')

# @app.route('/show/problem_sets')
# def show_problem_sets():
#     problem_sets=g.db.problem_sets.find()
#     prlist=[]
#     for i in problem_sets:
#         prlist.append(i)
#     prlist.reverse()
#     return render_template('show/problem_sets.html',problem_sets=prlist)


# @app.route('/show/problems/<problem_set_title>')
# def show_problems(problem_set_title):
#     problem_set=g.db.problem_sets.find_one({"title":problem_set_title})
#     problems=problem_set['problems']
#     return render_template('show/problems.html',problems=problems,problem_set_title=problem_set_title)

# @app.route('/show/problem/<problem_set_title>/<int:problem_number>')
# def show_problem(problem_set_title,problem_number):
#     # problem_set={"title":"Set Theory",'problems':
#     # [   {"title":"Problem 1",
#     #      'text':'How many elements are in the set {1,2,{1,2}}?',
#     #      'posts':[{'date':datetime.datetime.utcnow(),'author':'Artem','text':'nice problem','type':'comment'}] 
#     #       #type could be later also feedback or solution
#     #     }
#     # ]}
#     # g.db.problem_sets.insert(problem_set)
    
#     # for i in g.db.problem_sets.find():
#     #     print i

#     problem_set=g.db.problem_sets.find_one({'title':problem_set_title})
#     print problem_number-1
#     posts=problem_set['problems'][problem_number-1]['posts']
#     posts.reverse()
#     # d=datetime.datetime.now()
#     # print d['month']
#     title=problem_set['problems'][problem_number-1]['title']
#     text=problem_set['problems'][problem_number-1]['text']

#     return render_template('show/problem.html', problem_number=str(problem_number), 
#                             problem_set_title=problem_set_title,title=title,text=text,posts=posts)


# @app.route('/add_problem_set', methods=['GET','POST'])
# def add_problem_set():
#     # posts=g.mongo.db.posts
#     # posts.insert({"title":request.form['title'], "text":request.form['text']})
#     if g.db.problem_sets.find_one({"title": request.form['text']}):
#         flash('Sorry, such problem set already exists')
#     elif session.get('username') != 'entreri':
#         flash('you are not authorized to do such things')
#     else:
#         g.db.problem_sets.insert({"title":request.form['text'],"problems":[]})
#         flash('Problem set added, sir')
#     return redirect(url_for('show_problem_sets'))


# @app.route('/add_problem/<problem_set_title>', methods=['GET','POST'])
# def add_problem(problem_set_title):
#     # posts=g.mongo.db.posts
#     # posts.insert({"title":request.form['title'], "text":request.form['text']})
#     psdoc=g.db.problem_sets.find_one({"title":problem_set_title})
#     a=False
#     for prob in psdoc["problems"]:
#         a= (prob['title']==request.form['title'])
#     if a:
#         flash('Sorry, such title already exists')
#         print 'GA'
#     elif session.get('username') != 'entreri':
#         flash('you are not authorized to do such things')
#     else:
#         psdoc["problems"].append({'title':request.form['title'],
#                                     "text":request.form['text'],
#                                      "posts":[]})
#         g.db.problem_sets.update({"title":problem_set_title}, {"$set": psdoc}, upsert=False)
#         psdoc=g.db.problem_sets.find_one({"title":problem_set_title})
#         flash('Problem added, sir')
#     return redirect(url_for('show_problems',problem_set_title=problem_set_title))


# @app.route('/add_post', methods=['GET', 'POST'])
# def add_post():
#     if 'username' not in session:
#         abort(401)
#     # posts=g.mongo.db.posts
#     # posts.insert({"title":request.form['title'], "text":request.form['text']})
#     else:
#         problem_set_title=request.args.get('problem_set_title')
#         problem_number=request.args.get('problem_number')


#         # problem_set={"title":"Set Theory",'problems':
#         # [   {"title":"Problem 1",
#         #      'text':'How many elements are in the set {1,2,{1,2}}?',
#         #      'posts':[{'date':datetime.datetime.utcnow(),'author':'Artem','text':'nice problem','type':'comment'}] 
#         #       #type could be later also feedback or solution
#         #     }
#         # ]}
#         psdoc=g.db.problem_sets.find_one({"title":problem_set_title})
#         psdoc["problems"][int(problem_number)-1]['posts'].append({'date':datetime.datetime.utcnow(), 
#                                                              'author':session['username'],
#                                                              "text":request.form['text'],
#                                                              'type':'comment'
#                                                             })
#         g.db.problem_sets.update({"title":problem_set_title}, {"$set": psdoc}, upsert=False)
        
#         flash('New entry was successfully posted')
#         return redirect(url_for('show_problem',problem_set_title=problem_set_title,problem_number=problem_number))







# @app.route('/comments')
# def show_entries():
#     # print g.mongo.db.collection_names()
#     # for i in g.mongo.db.posts.find():
#     #     print i
#     posts=g.mongo.db.posts.find()
#     entries = [dict(title=entry["title"], text=entry["text"]) for entry in posts]
#     entries.reverse()
#     return render_template('show_entries.html', entries=entries)

# @app.route('/comments_add', methods=['GET','POST'])
# def add_entry():
#     if not 'username' in session:
#         abort(401)
#     # posts=g.mongo.db.posts
#     # posts.insert({"title":request.form['title'], "text":request.form['text']})
#     g.db.posts.insert({"title":request.form['title'], "text":request.form['text']})
#     flash('New entry was successfully posted')
#     return redirect(url_for('show_entries'))

# @app.route('/startertry')
# def startertry():
#     return render_template('startertry.html')

# @app.route('/indexBitStarter')
# def indexBitStarter():
#     return render_template('bitstarter/indexBitStarter.html')

# if __name__ == '__main__':
#     app.run()