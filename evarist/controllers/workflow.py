#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
import os, time, datetime, urllib, urllib2
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.mail import Message
from evarist import models
from functools import wraps
from evarist.models import model_problem_set, model_entry, model_post, model_solution, mongo
from evarist.forms import WebsiteFeedbackForm, CommentForm, SolutionForm, FeedbackToSolutionForm, EditSolutionForm, VoteForm, trigger_flash_error
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url

workflow = Blueprint('workflow', __name__,
                        template_folder='templates')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if not g.user:
            flash('Please, log in first.')
            return redirect(url_for('user.login'))

        return f(*args, **kwargs)
    return decorated_function

@workflow.route('/', methods=["GET", "POST"])
def home():
    # USE THIS CAREFULLY, its DANGEROUS! This is template for updating keys in all documents.
    
    # print mongo.add_key_value_where_none(collection=g.db.entries, key='general_discussion_ids', value=[])

    
    # this is example code for sending emails
    #
    # msg = Message("Hello",
    #               recipients=["artofkot@gmail.com"])
    # g.mail.send(msg)

    website_feedback_form=WebsiteFeedbackForm()
    if website_feedback_form.validate_on_submit():
        if g.user:
            model_post.add(text=website_feedback_form.feedback.data,
                            db=g.db,
                            author_id=g.user['_id'],
                            post_type='feedback',
                            parent_id=None)
        else:
            author_email=website_feedback_form.email.data
            model_post.add(text=website_feedback_form.feedback.data,
                            db=g.db,
                            author_email=author_email,
                            post_type='feedback',
                            parent_id=None)
        flash('Thank you for your feedback!')
        return redirect(url_for('workflow.home'))

    
    # this is how we manually choose which problem_sets to display on homepage
    rus_slugset=['mnozhestva','otobrazhenia','kombinatorika','podstanovki',
            'indukcia', 'binom-newtona','teoriya-graphov-1', 
            'podstanovki-2','delimost', 'algoritm-evklida', 'otnoshenia',
             'sravneniya','integers-praktika', 'teoriya-graphov-2', 'teoriya-grup', 'gomomorphismy']
    eng_slugset=['sets','group-theory']
    if g.locale == 'ru': homepage_slugset=rus_slugset
    else: homepage_slugset=eng_slugset
    
    # get all problem_sets
    psets=mongo.get_all(g.db.problem_sets)

    # choose those problem_sets, which slug is in homepage_slugset
    # check if all chosen slugs matched to some problem_sets, and if not - write which ones are wrong
    problem_sets=[]
    for slug in homepage_slugset:
        try:
            pset= next(pset for pset in psets if pset['slug']==slug)
            problem_sets.append(pset)
        except StopIteration:
            if not app.debug: g.mail.send(Message('slug ' + slug + ' was not found on the homepage',
                                                subject='Catched error on Evarist (production)!',
                                                recipients=current_app.config['ADMINS']))
            else: flash('Error: slug ' + slug + ' was not found!')

    return render_template('home.html',
                        problem_sets=problem_sets,
                        website_feedback_form=website_feedback_form)
    

@workflow.route('/home')
def index():
    return redirect(url_for('.home'))

# @workflow.route('/roots')
# def roots():
#     return render_template('roots.html')

@workflow.route('/about')
def about():
    return render_template('about.html')

@workflow.route('/problem_sets/<problem_set_slug>/', methods=["GET", "POST"])
def problem_set(problem_set_slug):
    # get the problem set
    problem_set=g.db.problem_sets.find_one({"slug": problem_set_slug})
    if not problem_set: 
        flash('No such problem set.')
        return redirect(url_for('.home'))


    is_moder=False
    if g.user: is_moder=g.user['rights']['is_moderator']
    if (not problem_set['status']=='production') and (not is_moder):
        flash('This problem set is not ready yet.')
        return redirect(url_for('.home'))


    # load problems, definition, etc
    mongo.load(problem_set,'entries_ids','entries',g.db.entries)
    # get the numbers of problems or definitions
    model_problem_set.get_numbers(problem_set=problem_set)
    
    # check if all entries loaded correctly

    if len(problem_set['entries'])!=len(problem_set['entries_ids']):
        if not app.debug: g.mail.send(Message('Some entry in prob_set_slug=' + problem_set_slug + ' was not found on the problem_set_page',
                                                subject='Catched error on Evarist (production)!',
                                                recipients=current_app.config['ADMINS']))
        else: flash('Some entry was not found!')

    return render_template('problem_set.html', 
                            problem_set=problem_set)

@workflow.route('/problem_sets/<problem_set_slug>/<entry_type>/<__id>/', methods=["GET", "POST"])
def entry(problem_set_slug,entry_type,__id):

    # get the problem set of entry
    # problem_set=g.db.problem_sets.find_one({"slug": problem_set_slug})
    # if problem_set==False: 
    #     flash('No such problem set.')
    #     return redirect(url_for('.home'))   

    # get the entry
    entry=g.db.entries.find_one({"_id":ObjectId(__id)})

    return render_template('entry.html',
                            entry=entry)

@workflow.route('/problem_sets/<problem_set_slug>/problem/<prob_id>/', methods=["GET", "POST"])
def problem(problem_set_slug,prob_id):
    
    # get the problem_set
    problem_set=g.db.problem_sets.find_one({"slug": problem_set_slug})
    if problem_set==False: 
        flash('No such problem set.')
        return redirect(url_for('.home'))

    is_moder=False
    if g.user: is_moder=g.user['rights']['is_moderator']
    if (not problem_set['status']=='production') and (not is_moder):
        flash('This problem set is not ready yet.')
        return redirect(url_for('.home'))


    #next 3 queries are done so that we know the number of the problem in probem set

    #load the entries of problem_set in order to get the number of problem
    mongo.load(problem_set,'entries_ids','entries',g.db.entries)
    # get the numbers of problems or definitions
    model_problem_set.get_numbers(problem_set=problem_set)

    # get the problem and problem's number out of problem_set
    try:
        problem, problem_number=next((entry, entry['problem_number']) for entry in problem_set['entries'] if entry.get('_id')==ObjectId(prob_id))
    except StopIteration:
        flash('No such problem in this problem_set.')
        return redirect(url_for('workflow.problem_set',problem_set_slug=problem_set_slug))
    

    #load general discussion
    mongo.load(obj=problem,key_id='general_discussion_ids',key='general_discussion',collection=g.db.posts)
    # load solutions
    mongo.load(problem,'solutions_ids','solutions',g.db.solutions)

    # get the current_user_solution, if its written
    try: 
        current_user_solution= next(sol for sol in problem['solutions'] if sol.get('author_id')==g.user.get('_id'))
        mongo.load(current_user_solution,'solution_discussion_ids','discussion',g.db.posts)
    except StopIteration: 
        current_user_solution={}

    general_comment_form=CommentForm()
    if general_comment_form.validate_on_submit():
        model_post.add(text=general_comment_form.text.data,
                       db=g.db,
                       author_id=g.user['_id'],
                       post_type='entry->general_discussion',
                       parent_id=problem['_id'])
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))

    vote_form=VoteForm()
    if vote_form.validate_on_submit():
        voted_solution=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
        if not g.user['_id'] in (voted_solution['users_upvoted_ids'] + voted_solution['users_downvoted_ids'] ):
            if g.user['rights']['is_checker']: vote_weight=2
            else: vote_weight=1

            if vote_form.vote.data == 'upvote': 
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$addToSet':{'users_upvoted_ids':g.user['_id']}})
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$inc':{'upvotes':vote_weight}})

            if vote_form.vote.data == 'downvote':
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$addToSet':{'users_downvoted_ids':g.user['_id']}})
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$inc':{'downvotes':vote_weight}})
        
            model_solution.update_everything(g.db, voted_solution['_id'])

        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))


    solution_comment_form=FeedbackToSolutionForm()
    if solution_comment_form.validate_on_submit():
        if solution_comment_form.feedback_to_solution.data:
            model_post.add(text=solution_comment_form.feedback_to_solution.data,
                           db=g.db,
                           author_id=g.user['_id'],
                           post_type='solution->comment',
                           parent_id=ObjectId(request.args['sol_id']))
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))

    solution_form=SolutionForm()
    if solution_form.validate_on_submit():
        file=request.files[solution_form.image.name]
        image_url=None
        if file:
            upload_result = upload(file)
            image_url=upload_result['url'] 
        model_solution.add(text=solution_form.solution.data,
                           db=g.db,
                           author_id=g.user['_id'],
                           problem_id=problem['_id'],
                           problem_set_id=problem_set['_id'],
                           image_url=image_url)
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))

    edit_solution_form=EditSolutionForm()
    if edit_solution_form.validate_on_submit():
        if edit_solution_form.delete_solution.data:
            model_solution.delete(db=g.db,solution=current_user_solution)
        else:
            g.db.solutions.update_one({"_id":current_user_solution['_id']},
                                        {'$set':{'text':edit_solution_form.edited_solution.data} })
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))

    other_solutions=[]
    if g.user:
        other_solutions=model_solution.get_other_solutions_on_problem_page(db=g.db,
                                                        user=g.user,
                                                        problem=problem,
                                                        current_solution_id=current_user_solution.get('_id'))

    return render_template('problem.html', 
                            problem_set_slug=problem_set_slug, 
                            problem=problem,
                            general_comment_form=general_comment_form,
                            solution_comment_form=solution_comment_form,
                            solution_form=solution_form,
                            edit_solution_form=edit_solution_form,
                            vote_form=vote_form,
                            other_solutions=other_solutions,
                            current_user_solution=current_user_solution)


@workflow.route('/check', methods=["GET", "POST"])
@login_required
def check():
    sols=model_solution.get_solutions_for_check_page(g.db,g.user)

    vote_form=VoteForm()
    if vote_form.validate_on_submit():
        voted_solution=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
        if not g.user['_id'] in (voted_solution['users_upvoted_ids'] + voted_solution['users_downvoted_ids'] ):
            if g.user['rights']['is_checker']: vote_weight=2
            else: vote_weight=1
            if vote_form.vote.data == 'upvote': 
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$addToSet':{'users_upvoted_ids':g.user['_id']}})
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$inc':{'upvotes':vote_weight}})

            if vote_form.vote.data == 'downvote':
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$addToSet':{'users_downvoted_ids':g.user['_id']}})
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$inc':{'downvotes':vote_weight}})
        
            model_solution.update_everything(g.db, voted_solution['_id'])

        return redirect(url_for('.check'))

    solution_comment_form=FeedbackToSolutionForm()
    if solution_comment_form.validate_on_submit():

        if solution_comment_form.feedback_to_solution.data:
            solut=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
            model_post.add(text=solution_comment_form.feedback_to_solution.data,
                           db=g.db,
                           author_id=g.user['_id'],
                           post_type='solution->comment',
                           parent_id=ObjectId(request.args['sol_id']))
        
        return redirect(url_for('.check'))



    return render_template("check.html", 
                            solutions=sols,
                            vote_form=vote_form,
                            solution_comment_form=solution_comment_form)

@workflow.route('/lang/en', methods=["GET", "POST"])
def lang_en():
    session['lang']='en'
    pa=request.args['pa']
    return redirect(pa)

@workflow.route('/leng/ru', methods=["GET", "POST"])
def lang_ru():
    session['lang']='ru'
    pa=request.args['pa']
    return redirect(pa)

@workflow.route('/upl', methods=['GET', 'POST'])
def upload_file():
    upload_result = None
    thumbnail_url1 = None
    thumbnail_url2 = None
    CLOUDINARY_URL='cloudinary://815324659179368:lHO42FBDftrJyCIRZ3x5OhLy_ew@artofkot'
    if request.method == 'POST':
        file = request.files['file']
        if file:
            upload_result = upload(file)
            thumbnail_url1, options = cloudinary_url(upload_result['public_id'], format = "jpg", crop = "scale", width = 100, height = 100)
            thumbnail_url2, options = cloudinary_url(upload_result['public_id'], format = "jpg", crop = "fill", width = 200, height = 100, radius = 20, effect = "sepia")
    return render_template('upload_form.html', upload_result = upload_result, thumbnail_url1 = thumbnail_url1, thumbnail_url2 = thumbnail_url2)


