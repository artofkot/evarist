#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
import os, time, datetime, urllib, urllib2
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.mail import Message
from evarist import models
from evarist.models import model_problem_set, model_entry, model_post, model_solution, mongo
from evarist.forms import WebsiteFeedbackForm, CommentForm, SolutionForm, FeedbackToSolutionForm, EditSolutionForm, VoteForm

workflow = Blueprint('workflow', __name__,
                        template_folder='templates')

@workflow.route('/', methods=["GET", "POST"])
def home():
    # USE THIS CAREFULLY, its DANGEROUS! This is template for updating keys in all documents.
    #
    # print mongo.add_key_value_where_none(collection=g.db.solutions, key='users_downvoted_ids', value=[])

    
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
            flash('slug ' + slug + ' was not found')

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
    if problem_set==False: 
        flash('No such problem set.')
        return redirect(url_for('.home'))

    # load problems, definition, etc
    mongo.load(obj=problem_set,
                key_id='entries_ids',
                key='entries',
                collection=g.db.entries)
    # get the numbers of problems or definitions
    model_problem_set.get_numbers(problem_set=problem_set)
    
    # this is how we did previously:
    # model_problem_set.load_entries(problem_set,g.db)

    # check if all entries loaded correctly
    if len(problem_set['entries'])!=len(problem_set['entries_ids']): 
        flash('Some entry was not found!')

    return render_template('problem_set.html', 
                            problem_set=problem_set)

@workflow.route('/problem_sets/<problem_set_slug>/<entry_type>/<__id>/', methods=["GET", "POST"])
def entry(problem_set_slug,entry_type,__id):

    # get the problem set of entry
    problem_set=g.db.problem_sets.find_one({"slug": problem_set_slug})
    if problem_set==False: 
        flash('No such problem set.')
        return redirect(url_for('.home'))   

    # get the entry
    entry=g.db.entries.find_one({"_id":ObjectId(__id)})

    return render_template('entry.html', 
                            problem_set=problem_set, 
                            entry=entry)

@workflow.route('/problem_sets/<problem_set_slug>/problem/<prob_id>/', methods=["GET", "POST"])
def problem(problem_set_slug,prob_id):

    # get the problem_set
    problem_set=g.db.problem_sets.find_one({"slug": problem_set_slug})
    if problem_set==False: 
        flash('No such problem set.')
        return redirect(url_for('.home'))

    
    #load the entries of problem_set in order to get the number of problem

    #model_problem_set.load_entries(problem_set,g.db)
    mongo.load(obj=problem_set,
                key_id='entries_ids',
                key='entries',
                collection=g.db.entries)
    # get the numbers of problems or definitions
    model_problem_set.get_numbers(problem_set=problem_set)

    # get the problem and problem's number out of problem_set
    try:
        problem, problem_number=next((entry, entry['problem_number']) for entry in problem_set['entries'] if entry.get('_id')==ObjectId(prob_id))
    except StopIteration:
        flash('No such problem in this problem_set.')
        return redirect(url_for('workflow.problem_set',problem_set_slug=problem_set_slug))
    
    
    #load general discussion
    mongo.load(obj=problem,
                key_id='general_discussion_ids',
                key='general_discussion',
                collection=g.db.posts)
    
    # load solutions
    mongo.load(obj=problem,
                key_id='solutions_ids',
                key='solutions',
                collection=g.db.solutions)

    try: 
        current_user_solution= next(sol for sol in problem['solutions'] if sol['author_id']==g.user.get('_id'))
        mongo.load(obj=current_user_solution,
                    key_id='solution_discussion_ids',
                    key='discussion',
                    collection=g.db.posts)
    except StopIteration: 
        current_user_solution=None

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
            if vote_form.vote.data == 'upvote': 
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$addToSet':{'users_upvoted_ids':g.user['_id']}})
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$inc':{'upvotes':1}})

            if vote_form.vote.data == 'downvote':
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$addToSet':{'users_downvoted_ids':g.user['_id']}})
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$inc':{'downvotes':1}})
        
            model_solution.update_everything(g.db, voted_solution['_id'])

        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))


    solution_comment_form=FeedbackToSolutionForm()
    if solution_comment_form.validate_on_submit():

        if solution_comment_form.feedback_to_solution.data:
            model_post.add(text=solution_comment_form.feedback_to_solution.data,
                           db=g.db,
                           author_id=g.user['__id'],
                           post_type='solution->comment',
                           parent_id=ObjectId(request.args['sol_id']))
        
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))

    currentuser_solution_id=None
    if not current_user_solution:
        g.solution_written=False
    else:
        g.solution_written=True
        mongo.load(obj=current_user_solution,
                key_id='solution_discussion_ids',
                key='discussion',
                collection=g.db.posts)
        currentuser_solution_id=current_user_solution['_id']

    solution_form=SolutionForm()
    if solution_form.validate_on_submit():
        model_solution.add(text=solution_form.solution.data,
                           db=g.db,
                           author_id=g.user['_id'],
                           problem_id=problem['_id'],
                           problem_set_id=problem_set['_id'])

        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))
                                # problem_number=problem_number)

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
        if problem['_id'] in g.user['problems_ids']['can_see_other_solutions'] or g.user['rights']['is_moderator'] or g.user['rights']['is_checker']:
            for sol_id in problem['solutions_ids']:
                if not currentuser_solution_id==sol_id:
                    solut=g.db.solutions.find_one({'_id':sol_id})
                    if solut:
                        mongo.load(obj=solut,
                                    key_id='solution_discussion_ids',
                                    key='discussion',
                                    collection=g.db.posts)
                        other_solutions.append(solut)




    # return redirect(url_for('.home'))
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
def check():
    if not g.user:
        flash('Please, log in first')
        return redirect(url_for('.check'))

    if g.user['rights']['is_moderator'] or g.user['rights']['is_checker']:
        solutions=g.db.solutions.find({'status': 'not_checked'})
    else:
        solutions=[]
        for idd in g.user['problems_ids']['can_see_other_solutions']:
            solutions.extend(g.db.solutions.find({'problem_id':ObjectId(idd), 'checked': False}))

    sols=[]
    for solution in solutions:
        mongo.load(obj=solution,
                key_id='solution_discussion_ids',
                key='discussion',
                collection=g.db.posts)
        if not mongo.load(obj=solution,
                        key_id='author_id',
                        key='author',
                        collection=g.db.users):
            solution['author']={}
            solution['author']['username']='deleted user'

        problem=g.db.entries.find_one({'_id':ObjectId(solution['problem_id'])})
        problem_set=g.db.problem_sets.find_one({'_id':ObjectId(solution['problem_set_id'])})
        solution['problem_text']=problem['text']
        solution['problem_set']=problem_set['title']
        sols.append(solution)

    vote_form=VoteForm()
    if vote_form.validate_on_submit():
        voted_solution=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
        if not g.user['_id'] in (voted_solution['users_upvoted_ids'] + voted_solution['users_downvoted_ids'] ):
            if vote_form.vote.data == 'upvote': 
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$addToSet':{'users_upvoted_ids':g.user['_id']}})
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$inc':{'upvotes':1}})

            if vote_form.vote.data == 'downvote':
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$addToSet':{'users_downvoted_ids':g.user['_id']}})
                g.db.solutions.update_one({'_id':voted_solution['_id']},
                                            {'$inc':{'downvotes':1}})
        
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


@workflow.route('/startertry')
def startertry():
    return render_template('examples/startertry.html')
