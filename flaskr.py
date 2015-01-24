import os
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from jinja2 import TemplateNotFound

flaskr = Blueprint('flaskr', __name__,
                    template_folder='templates')

# @flaskr.route('/', defaults={'page': 'index'})
# @flaskr.route('/<page>')
# def show(page):
#     try:
#         return render_template('pages/%s.html' % page)
#     except TemplateNotFound:
#         abort(404)

@flaskr.route('/flaskr')
def show_entries():
    # print mongo.db.collection_names()
    # for i in mongo.db.posts.find():
    #     print i
    posts=mongo.db.posts.find()
    entries = [dict(title=entry["title"], text=entry["text"]) for entry in posts]
    return render_template('flaskr/show_entries.html', entries=entries)

@flaskr.route('/flaskr_add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    # posts=mongo.db.posts
    # posts.insert({"title":request.form['title'], "text":request.form['text']})
    mongo.db.posts.insert({"title":request.form['title'], "text":request.form['text']})
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@flaskr.route('/flaskr_login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != current_app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != current_app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('flaskr/login.html', error=error)

@flaskr.route('/flaskr_logout')
def logout():
    session.pop('logged_in', None) 
    # We use a neat trick here:
    # if you use the pop() method of the dict and pass a second parameter to it (the default),
    # the method will delete the key from the dictionary if present or
    # do nothing when that key is not in there.
    flash('You were logged out')
    return redirect(url_for('show_entries'))