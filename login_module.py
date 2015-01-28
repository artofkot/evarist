import os, re
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from jinja2 import TemplateNotFound

login_module = Blueprint('login_module', __name__,
                    template_folder='templates')

#regexs for usernames and passwords and emails
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

@login_module.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        user=g.mongo.db.users.find_one({"username": username})
        if user:
            if g.bcrypt.check_password_hash(user["pw_hash"], password): # returns True
                session['logged_in'] = True
                session['username'] = user['username']
                flash('You were logged in')
                return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@login_module.route('/logout')
def logout():
    session.pop('logged_in', None)
    # We use a neat trick here:
    # if you use the pop() method of the dict and pass a second parameter to it (the default),
    # the method will delete the key from the dictionary if present or
    # do nothing when that key is not in there.
    flash('You were logged out')
    return redirect(url_for('show_entries'))


# pw_hash = bcrypt.generate_password_hash('hunter3')
# print bcrypt.check_password_hash(pw_hash, 'hunter3') # returns True

@login_module.route('/signup', methods=['GET', 'POST'])
def signup():

    for i in g.mongo.db.users.find():
        print i

    error=None
    if request.method == 'POST':
        if not valid_username(request.form['username']):
            error = 'Change the username please'
        elif g.mongo.db.users.find_one({"username": request.form['username']}):
            error = 'Unfortunately this username is taken'
        elif not valid_password(request.form['password']):
            error = 'Change the password please'
        elif not valid_password(request.form['email']):
            error = 'Strange email, please change'
        else:
            pw_hash = g.bcrypt.generate_password_hash(request.form['password'])
            username=request.form['username']
            email=request.form['email']
            g.mongo.db.users.insert({"username":username, "pw_hash":pw_hash, "email":email})

            return redirect(url_for('login_module.login'))


    return render_template("signup.html", error=error)






