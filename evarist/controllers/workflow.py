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
from evarist.models import (model_problem_set, model_entry, model_post, 
                            model_solution, mongo, problem_set_filters,
                            solution_filters)
from evarist.forms import (WebsiteFeedbackForm, CommentForm, 
                            SolutionForm, FeedbackToSolutionForm, 
                            EditSolutionForm, VoteForm, 
                            trigger_flash_error)
from evarist.models.mongoengine_models import *


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
    # this is example code for sending emails
    #
    # msg = Message("Hello",
    #               recipients=["artofkot@gmail.com"])
    # g.mail.send(msg)

    website_feedback_form=WebsiteFeedbackForm()
    if website_feedback_form.validate_on_submit():
        feedback=CommentFeedback(text=website_feedback_form.feedback.data,
                                type_='feedback',
                                where_feedback='homepage')
        if g.user: feedback.author=g.user
        else: feedback.author_email=website_feedback_form.email.data
        
        feedback.save()

        flash('Thank you for your feedback!')
        return redirect(url_for('workflow.home'))

    
    # this is how we manually choose which problem_sets to display on homepage
    rus_slugset=problem_set_filters.rus_slugset
    eng_slugset=problem_set_filters.eng_slugset
    slugset=problem_set_filters.slugset

    if g.locale == 'ru': homepage_slugset=rus_slugset
    else: homepage_slugset=eng_slugset
    
    # get all problem_sets
    psets=Problem_set.objects()

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
    
    problem_set=Problem_set.objects(slug=problem_set_slug).first()
    if not problem_set: 
        flash('No such problem set.')
        return redirect(url_for('.home'))


    is_moderator=False
    if g.user: is_moderator=g.user['rights']['is_moderator']
    if (not problem_set['status']=='production') and (not is_moderator):
        flash('This problem set is not ready yet.')
        return redirect(url_for('.home'))

    
    return render_template('problem_set.html', 
                            problem_set=problem_set)

@workflow.route('/problem_sets/<problem_set_slug>/<type_>/<__id>/', methods=["GET", "POST"])
def content_block(problem_set_slug,type_,__id):

    content_block=Content_block.objects(id=ObjectId(__id)).first()

    return render_template('content_block.html',
                            content_block=content_block)

@workflow.route('/problem_sets/<problem_set_slug>/problem/<prob_id>/', methods=["GET", "POST"])
def problem(problem_set_slug,prob_id):
    
    # get the problem_set
    problem_set=Problem_set.objects(slug=problem_set_slug).first()
    if not problem_set: 
        flash('No such problem set.')
        return redirect(url_for('.home'))

    # get the problem_set
    problem=Content_block.objects(id=ObjectId(prob_id)).first()
    if not problem: 
        flash('No such problem.')
        return redirect(url_for('.home'))

    # check if user can see this problem set
    is_moderator=False
    if g.user: is_moderator=g.user.rights.is_moderator
    if (not problem_set['status']=='production') and (not is_moderator):
        flash('This problem set is not ready yet.')
        return redirect(url_for('.home'))

    # get the current_user_solution, if its written
    try: 
        current_user_solution= next(sol for sol in problem['solutions'] if sol.author.id==g.user.id)
    except StopIteration: 
        current_user_solution={}

    general_comment_form=CommentForm()
    if general_comment_form.validate_on_submit():

        comment=CommentToContent_block(text=general_comment_form.text.data,
                                        author=g.user,
                                        parent_content_block=problem)
        comment.save()
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['id']))

    vote_form=VoteForm()
    if vote_form.validate_on_submit():
        voted_solution=Solution.objects(id=ObjectId(request.args['sol_id'])).first()
        
        if not g.user['id'] in (voted_solution['users_upvoted'] + voted_solution['users_downvoted'] ):
            if g.user['rights']['is_checker']: vote_weight=2
            else: vote_weight=1

            if vote_form.vote.data == 'upvote': 
                voted_solution.users_upvoted.append(g.user)
                voted_solution.upvotes+=vote_weight

            if vote_form.vote.data == 'downvote':
                voted_solution.users_downvoted.append(g.user)
                voted_solution.downvotes+=vote_weight
            
            voted_solution.save()

            solution_filters.update_everything(voted_solution)
        else:
            flash('It turns out you already voted for this solution, sorry for the wrong data on the page.')

        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['id']))

    solution_comment_form=FeedbackToSolutionForm()
    if solution_comment_form.validate_on_submit():
        if solution_comment_form.feedback_to_solution.data:
            comment=CommentToSolution(text=solution_comment_form.feedback_to_solution.data,
                author=g.user,
                parent_solution=Solution.objects(id=ObjectId(request.args['sol_id'])).first())
            comment.save()
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem.id))

    solution_form=SolutionForm()
    if solution_form.validate_on_submit():
        file=request.files[solution_form.image.name]
        image_url=None
        if file:
            upload_result = upload(file)
            image_url=upload_result['url'] 
        solution=Solution(text=solution_form.solution.data,
                        author=g.user,
                        problem=problem,
                        problem_set=problem_set,
                        image_url=image_url)
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['id']))

    edit_solution_form=EditSolutionForm()
    if edit_solution_form.validate_on_submit():
        if edit_solution_form.delete_solution.data:
            current_user_solution.delete()
        else:
            current_user_solution.text=edit_solution_form.edited_solution.data
            current_user_solution.date=datetime.datetime.utcnow()
            current_user_solution.save()
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))
    # trigger_flash_error(edit_solution_form,'workflow.problem', 
    #                             problem_set_slug=problem_set_slug,
    #                             prob_id=problem['_id'])


    other_solutions=[]
    if g.user:
        other_solutions=solution_filters.get_other_solutions_on_problem_page(user=g.user,
                                                        problem=problem,
                                                        current_solution=current_user_solution)

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
    (not_checked_sols,checked_sols)=model_solution.get_solutions_for_check_page(g.db,g.user)

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
                            solutions=not_checked_sols+checked_sols,
                            not_checked_solutions=not_checked_sols,
                            checked_solutions=checked_sols,
                            vote_form=vote_form,
                            solution_comment_form=solution_comment_form)

@workflow.route('/my_solutions', methods=["GET", "POST"])
@login_required
def my_solutions():
    (not_checked_sols,checked_sols)=model_solution.get_solutions_for_my_solutions_page(g.db,g.user)
    solution_comment_form=FeedbackToSolutionForm()
    if solution_comment_form.validate_on_submit():
        if solution_comment_form.feedback_to_solution.data:
            solut=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
            model_post.add(text=solution_comment_form.feedback_to_solution.data,
                           db=g.db,
                           author_id=g.user['_id'],
                           post_type='solution->comment',
                           parent_id=ObjectId(request.args['sol_id']))
        
        return redirect(url_for('.my_solutions'))

    edit_solution_form=EditSolutionForm()
    if edit_solution_form.validate_on_submit():
        solut=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
        if edit_solution_form.delete_solution.data:
            model_solution.delete(db=g.db,solution=solut)
        else:
            g.db.solutions.update_one({"_id":solut['_id']},
                                        {'$set':{'text':edit_solution_form.edited_solution.data,
                                        'date':datetime.datetime.utcnow()} })
        return redirect(url_for('.my_solutions'))
    # trigger_flash_error(edit_solution_form,'workflow.my_solutions')


    return render_template("my_solutions.html", 
                            solutions=not_checked_sols+checked_sols,
                            not_checked_solutions=not_checked_sols,
                            checked_solutions=checked_sols,
                            solution_comment_form=solution_comment_form,
                            edit_solution_form=edit_solution_form)


@workflow.route('/lang/en', methods=["GET", "POST"])
def lang_en():
    session['lang']='en'
    pa=request.args['pa']
    # return redirect(pa)
    return redirect(url_for('.home'))

@workflow.route('/leng/ru', methods=["GET", "POST"])
def lang_ru():
    session['lang']='ru'
    pa=request.args['pa']
    # return redirect(pa)
    return redirect(url_for('.home'))

# @workflow.route('/upl', methods=['GET', 'POST'])
# def upload_file():
#     upload_result = None
#     thumbnail_url1 = None
#     thumbnail_url2 = None
#     if request.method == 'POST':
#         file = request.files['file']
#         if file:
#             upload_result = upload(file)
#             thumbnail_url1, options = cloudinary_url(upload_result['public_id'], format = "jpg", crop = "scale", width = 100, height = 100)
#             thumbnail_url2, options = cloudinary_url(upload_result['public_id'], format = "jpg", crop = "fill", width = 200, height = 100, radius = 20, effect = "sepia")
#     return render_template('upload_form.html', upload_result = upload_result, thumbnail_url1 = thumbnail_url1, thumbnail_url2 = thumbnail_url2)


