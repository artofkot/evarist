#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, re, datetime
from bson.objectid import ObjectId
# import bcrypt - fuck this shit, seriously hate this library
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from jinja2 import TemplateNotFound
from evarist.models import model_user
from evarist.models.token import generate_confirmation_token, confirm_token
from evarist.forms import SignUpForm, SignInForm
from flask.ext.mail import Message
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import AccessTokenCredentials
import httplib2, json, uuid, hashlib, string, random
from flask import make_response
import requests

from evarist.models_mongoengine import EmailUser


user = Blueprint('user', __name__,
                        template_folder='templates')

def send_confirmation_link(email):
    token = generate_confirmation_token(email)
    confirm_url = url_for('user.confirm_email', token=token, _external=True)
    html = render_template('user/activate.html', confirm_url=confirm_url)
    g.mail.send(Message(html = render_template('user/activate.html', confirm_url=confirm_url),
                        subject='Please confirm your email',
                        recipients=[email]))

    


@user.route('/user/signup', methods=['GET', 'POST'])
def signup():
    if g.user:
        flash('Please log out first')
        return redirect(url_for('workflow.home'))

    signup_form=SignUpForm()

    if request.method == 'POST' and signup_form.validate_on_submit():
        if not signup_form.password.data == signup_form.confirm_password.data:
            flash('Passwords should be the same. Try one more time, please')
            return redirect(url_for('user.signup'))
        if model_user.add(email=signup_form.email.data,
                        password=signup_form.password.data,
                        username=signup_form.username.data,
                        db=g.db,
                        secret_key=current_app.config["SECRET_KEY"]):
            flash('Hey, thanks for signing up! We sent you an email, please visit the confirmation link.')
            send_confirmation_link(signup_form.email.data)
            return redirect(url_for('workflow.home'))
        else: 
            flash('Such email already exists')
            return redirect(url_for('user.signup'))

    error=''
    if request.method == 'POST' and not signup_form.validate_on_submit():
        for err in signup_form.errors:
            error=error+signup_form.errors[err][0]+' '
        return render_template("user/signup.html", error=error, signup_form=SignUpForm())

    return render_template("user/signup.html", error=error, signup_form=signup_form)

@user.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.')
    user = g.db.users.find_one({'email':email, 'provider':'email'})
    if user:
        if user.get('confirmed'):
            flash('Account already confirmed. Please login.')
        else:
            g.db.users.update_one({"_id": user['_id']}, 
                                {'$set': {'confirmed': True} })
            session['_id']=str(user['_id'])
            flash('You have confirmed your account. Thanks!', 'success')
    else: flash('Such email does not exist in our database.')
    return redirect(url_for('workflow.home'))


@user.route('/user/login', methods=['GET', 'POST'])
def login():
    if g.user:
        flash('Please log out first')
        return redirect(url_for('workflow.home'))

    state=''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    session['state']=state

    error = ''
    signin_form=SignInForm()
    if request.method == 'POST' and signin_form.validate_on_submit():

        email=signin_form.email.data
        password=signin_form.password.data

        user=g.db.users.find_one({"email": email})
        if user:
            if model_user.check_pwd(password,user["pw_hash"],secret_key=current_app.config["SECRET_KEY"]):
                session['_id']=str(user['_id'])
                return redirect(url_for('workflow.home'))


            else:
                error = 'Invalid password'
        else:
            error = 'Invalid username'

    if request.method == 'POST' and not signin_form.validate_on_submit():
        for err in signin_form.errors:
            error=error+signin_form.errors[err][0]+' '
        return render_template("user/login.html", error=error, signin_form=SignInForm())
    return render_template('user/login.html', error=error, signin_form=signin_form, client_id_yep=current_app.config['CLIENT_ID']) 

# this POST request comes from login page if user presses gplus-sign-in button
@user.route('/user/gconnect', methods=['POST'])
def gconnect():


    # Validate state token
    if request.args.get('state') != session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object

        # CLIENT_SECRETS_JSON = json.loads(os.environ.get("CLIENT_SECRETS_JSON"))
        temp_file = open("client_secrets.json", "w")
        temp_file.write(os.environ.get("CLIENT_SECRETS_JSON"))
        temp_file.close()
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        os.remove('client_secrets.json')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response



    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'



    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result.get('user_id') != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != current_app.config['CLIENT_ID']:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    # check if user is already connected
    stored_credentials = session.get('credentials')
    stored_gplus_id = session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response


    # Store the access token in the session for later use.
    session['access_token'] = credentials.access_token
    session['gplus_id'] = gplus_id
    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    # add user if such email does not exist in database of gplus users
    added_user_id = model_user.add_gplus(gplus_id=gplus_id , 
                                gplus_picture=data['picture'],
                                db=g.db, 
                                gplus_name=data['name'], 
                                gplus_email=data['email'])

    # store user's id in session
    if added_user_id:
        session['_id']=str(added_user_id)
    else:
        user=g.db.users.find_one({"gplus_id": gplus_id})
        session['_id']=str(user['_id'])
    

    # make a response and send it back to login page
    output = ''
    output += '<h1>Welcome, '
    output += data['name']
    output += '!</h1>'
    output += '<img src="'
    output += data['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % data['name'])
    return output



@user.route('/user/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        session.pop('_id', None)
        session.pop('gplus_id', None)
        session.pop('access_token', None)

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('workflow.home'))
        # return response
    else:
        # For whatever reason, the given token was invalid.
        session.pop('_id', None)
        session.pop('gplus_id', None)
        session.pop('access_token', None)
        
        response = make_response(
            json.dumps('Failed to revoke token for a given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        # return response
        return redirect(url_for('workflow.home'))

@user.route('/user/logout')
def logout():
    if g.user.get('provider')=='gplus':
        return redirect(url_for('user.gdisconnect'))
    else:
        session.pop('_id', None)
        session.pop('gplus_id', None)
        session.pop('access_token', None)
        # We use a neat trick here:
        # if you use the pop() method of the dict and pass a second parameter to it (the default),
        # the method will delete the key from the dictionary if present or
        # do nothing when that key is not in there.
        return redirect(url_for('workflow.home'))