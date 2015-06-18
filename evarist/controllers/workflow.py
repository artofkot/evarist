#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
import os, datetime, urllib, urllib2
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from evarist.models import model_problem_set, model_entry, model_post, model_solution, mongo
from evarist.forms import WebsiteFeedbackForm, CommentForm, SolutionForm, FeedbackToSolutionForm, EditSolutionForm, VoteForm

workflow = Blueprint('workflow', __name__,
                        template_folder='templates')

@workflow.route('/', methods=["GET", "POST"])
def home():
    # USE THIS CAREFULLY, its DANGEROUS! This is template for updating keys in all documents.
    # mongo.update(collection=g.db.problem_sets,doc_key='all',doc_value='notimportant',
    #             update_key='status',update_value='dev')

    website_feedback_form=WebsiteFeedbackForm()
    if website_feedback_form.validate_on_submit():
        authors_email=session.get('email')
        author=session.get('username')
        if not authors_email:
            authors_email=website_feedback_form.email.data
            author=authors_email
        model_post.add(text=website_feedback_form.feedback.data,
                        db=g.db,
                        author=author,
                        authors_email=authors_email,
                        post_type='feedback',
                        parent_type='evarist_feedback',
                        parent_id=None,
                        problem_id=None,
                        problem_set_id=None)
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
    psets=model_problem_set.get_all(g.db)

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

@workflow.route('/roots')
def roots():
    return render_template('roots.html')

@workflow.route('/about')
def about():
    return render_template('about.html')

@workflow.route('/problem_sets/<problem_set_slug>/', methods=["GET", "POST"])
def problem_set(problem_set_slug):


    problem_set=model_problem_set.get_by_slug(problem_set_slug, g.db)
    if problem_set==False: 
        flash('No such problem set.')
        return redirect(url_for('.home'))


    model_problem_set.load_entries(problem_set,g.db)

    return render_template('problem_set.html', 
                            problem_set=problem_set)

@workflow.route('/problem_sets/<problem_set_slug>/<entry_type>/<__id>/', methods=["GET", "POST"])
def entry(problem_set_slug,entry_type,__id):
    problem_set=model_problem_set.get_by_slug(problem_set_slug, g.db)
    if problem_set==False: 
        flash('No such problem set.')
        return redirect(url_for('.home'))   

    entry=g.db.entries.find_one({"_id":ObjectId(__id)})

    return render_template('entry.html', 
                            problem_set=problem_set, 
                            entry=entry)

# @workflow.route('/problem_sets/<problem_set_slug>/problem/<int:problem_number>/', methods=["GET", "POST"])
@workflow.route('/problem_sets/<problem_set_slug>/problem/<prob_id>/', methods=["GET", "POST"])
def problem(problem_set_slug,prob_id):
    # problem_number=int(request.args['problem_number'])
    problem_set=model_problem_set.get_by_slug(problem_set_slug, g.db)
    if problem_set==False: 
        flash('No such problem set.')
        return redirect(url_for('.home'))


    #get the problem_set
    model_problem_set.load_entries(problem_set,g.db)

    # get the problem out of problem_set  -  OLD, when we tried to use numbers of problems in url
    try:
        problem, problem_number=next((entry, entry['problem_number']) for entry in problem_set['entries'] if entry.get('_id')==ObjectId(prob_id))
    except StopIteration:
        flash('No such problem in this problem_set.')
        return redirect(url_for('workflow.problem_set',problem_set_slug=problem_set_slug))

    
    

    #load general discussion
    model_entry.load_posts(problem,g.db)
    # load solutions
    model_entry.load_solution(problem,g.db,session.get('username'),session.get('email'))
    #TODO load comments to solutions

    general_comment_form=CommentForm()
    if general_comment_form.validate_on_submit():
        model_post.add(text=general_comment_form.text.data,
                       db=g.db,
                       author=session['username'],
                       authors_email=session['email'],
                       post_type='comment',
                       parent_type='problem',
                       parent_id=problem['_id'],
                       problem_id=problem['_id'],
                       problem_set_id=problem_set['_id'])
        
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))

    vote_form=VoteForm()
    if vote_form.validate_on_submit():
        voted_solution=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
        if not session['email'] in voted_solution['emails_voted']:
            if vote_form.vote.data == 'upvote': 
                voted_solution['upvotes']=voted_solution['upvotes']+1
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='upvotes',
                            update_value=voted_solution['upvotes'])
                voted_solution['emails_voted'].append(session['email'])
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='emails_voted',
                            update_value=voted_solution['emails_voted'])

            if vote_form.vote.data == 'downvote':
                voted_solution['downvotes']=voted_solution['downvotes']+1
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='downvotes',
                            update_value=voted_solution['downvotes'])
                voted_solution['emails_voted'].append(session['email'])
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='emails_voted',
                            update_value=voted_solution['emails_voted'])

            model_solution.update_status(g.db, voted_solution)

        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))


    solution_comment_form=FeedbackToSolutionForm()
    if solution_comment_form.validate_on_submit():

        if solution_comment_form.feedback_to_solution.data:
            model_post.add(text=solution_comment_form.feedback_to_solution.data,
                           db=g.db,
                           author=session['username'],
                           authors_email=session['email'],
                           post_type='comment',
                           parent_type='solution',
                           parent_id=ObjectId(request.args['sol_id']),
                           problem_id=problem['_id'],
                           problem_set_id=problem_set['_id'])
        
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))

    currentuser_solution_id=None
    if not problem.get('solution'):
        g.solution_written=False
    else:
        g.solution_written=True
        model_solution.load_discussion(g.db,problem['solution'])
        currentuser_solution_id=problem['solution']['_id']

    solution_form=SolutionForm()
    if solution_form.validate_on_submit():
        model_solution.add(text=solution_form.solution.data,
                           db=g.db,
                           author=session['username'],
                           authors_email=session['email'],
                           problem_id=problem['_id'],
                           problem_set_id=problem_set['_id'])

        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))
                                # problem_number=problem_number)

    edit_solution_form=EditSolutionForm()
    if edit_solution_form.validate_on_submit():
        if edit_solution_form.delete_solution.data:
            model_solution.delete(db=g.db,solution=problem['solution'])
        else:
            mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=problem['solution']['_id'],
                            update_key='text',
                            update_value=edit_solution_form.edited_solution.data)

        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                prob_id=problem['_id']))

    user=g.db.users.find_one({'email':session.get('email')})

    g.other_solutions=[]
    if 'email' in session:
        print str(session.get('is_checker')) +'!!!!'
        if problem['_id'] in user['problems_ids']['can_see_other_solutions'] or session.get("is_moderator") or session.get("is_checker"):
            for sol_id in problem['solutions_ids']:
                if not currentuser_solution_id==sol_id:
                    solut=g.db.solutions.find_one({'_id':sol_id})
                    if solut:
                        model_solution.load_discussion(g.db,solut)
                        g.other_solutions.append(solut)





    # return redirect(url_for('.home'))
    return render_template('problem.html', 
                            problem_set_slug=problem_set_slug, 
                            problem=problem,
                            general_comment_form=general_comment_form,
                            solution_comment_form=solution_comment_form,
                            solution_form=solution_form,
                            edit_solution_form=edit_solution_form,
                            vote_form=vote_form)


@workflow.route('/check', methods=["GET", "POST"])
def check():
    user=g.db.users.find_one({'email': session['email']})
    if session.get("is_moderator") or session.get("is_checker"):
        solutions=g.db.solutions.find({'checked': False})
    else:
        solutions=[]
        for idd in user['problems_ids']['can_see_other_solutions']:
            solutions.extend(g.db.solutions.find({'problem_id':ObjectId(idd), 'checked': False}))

    sols=[]
    for solution in solutions:
        model_solution.load_discussion(g.db,solution)
        problem=g.db.entries.find_one({'_id':ObjectId(solution['problem_id'])})
        problem_set=g.db.problem_sets.find_one({'_id':ObjectId(solution['problem_set_id'])})
        solution['problem_text']=problem['text']
        solution['problem_set']=problem_set['title']
        sols.append(solution)

    vote_form=VoteForm()
    if vote_form.validate_on_submit():
        voted_solution=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
        if not session['email'] in voted_solution['emails_voted']:
            if vote_form.vote.data == 'upvote': 
                voted_solution['upvotes']=voted_solution['upvotes']+1
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='upvotes',
                            update_value=voted_solution['upvotes'])
                voted_solution['emails_voted'].append(session['email'])
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='emails_voted',
                            update_value=voted_solution['emails_voted'])
                

            if vote_form.vote.data == 'downvote':
                voted_solution['downvotes']=voted_solution['downvotes']+1
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='downvotes',
                            update_value=voted_solution['downvotes'])
                voted_solution['emails_voted'].append(session['email'])
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='emails_voted',
                            update_value=voted_solution['emails_voted'])
        
            model_solution.update_status(g.db, voted_solution)

        return redirect(url_for('.check'))

    solution_comment_form=FeedbackToSolutionForm()
    if solution_comment_form.validate_on_submit():

        if solution_comment_form.feedback_to_solution.data:
            solut=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
            model_post.add(text=solution_comment_form.feedback_to_solution.data,
                           db=g.db,
                           author=session['username'],
                           authors_email=session['email'],
                           post_type='comment',
                           parent_type='solution',
                           parent_id=ObjectId(request.args['sol_id']),
                           problem_id=solut['problem_id'],
                           problem_set_id=solut['problem_set_id'])
        
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
