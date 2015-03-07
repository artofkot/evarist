import os, re, datetime
from bson.objectid import ObjectId
# import bcrypt - fuck this shit, seriously hate this library
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from jinja2 import TemplateNotFound
from listki.models import model_user
from listki.forms import SignUpForm, SignInForm


import uuid
import hashlib

user = Blueprint('user', __name__,
                        template_folder='templates')


@user.route('/user/login', methods=['GET', 'POST'])
def login():
    if "username" in session:
        flash('please log out first')
        return redirect(url_for('workflow.home'))

    error = ''

    signin_form=SignInForm()

    if request.method == 'POST' and signin_form.validate_on_submit():

        username=signin_form.username.data
        password=signin_form.password.data

        user=g.db.users.find_one({"username": username})
        if user:
            if model_user.check_pwd(password,user["pw_hash"],secret_key=current_app.config["SECRET_KEY"]):
                session['username'] = user['username']
                return redirect(url_for('workflow.home'))
            else:
                error = 'Invalid password'
        else:
            error = 'Invalid username'

    if request.method == 'POST' and not signin_form.validate_on_submit():
        for err in signin_form.errors:
            error=error+signin_form.errors[err][0]+' '
        return render_template("user/login.html", error=error, signin_form=SignInForm())
        
    return render_template('user/login.html', error=error, signin_form=signin_form)

@user.route('/user/logout')
def logout():
    session.pop('username', None)
    # We use a neat trick here:
    # if you use the pop() method of the dict and pass a second parameter to it (the default),
    # the method will delete the key from the dictionary if present or
    # do nothing when that key is not in there.
    return redirect(url_for('workflow.home'))


@user.route('/user/signup', methods=['GET', 'POST'])
def signup():
    # for i in g.db.users.find():
    #     print i

    if "username" in session:
        flash('please log out first')
        return redirect(url_for('workflow.home'))

    signup_form=SignUpForm()

    if request.method == 'POST' and signup_form.validate_on_submit():
        model_user.add(email=signup_form.email.data,
                        password=signup_form.password.data,
                        username=signup_form.username.data,
                        db=g.db,
                        secret_key=current_app.config["SECRET_KEY"])
        return redirect(url_for('user.login'))

    error=''
    if request.method == 'POST' and not signup_form.validate_on_submit():
        for err in signup_form.errors:
            error=error+signup_form.errors[err][0]+' '
        return render_template("user/signup.html", error=error, signup_form=SignUpForm())

    return render_template("user/signup.html", error=error, signup_form=signup_form)


