#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
import os, datetime, urllib, urllib2
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from functools import wraps
from evarist.forms import ProblemSetForm, EntryForm, EditEntryForm, ProblemSetDelete, VoteForm, FeedbackToSolutionForm
from evarist.models import model_problem_set, model_entry, mongo, model_post, model_solution

admin = Blueprint('admin', __name__,
                        template_folder='templates')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if not session.get('is_moderator'):
            flash('You are not allowed to do that.')
            return redirect(url_for('workflow.home'))


        return f(*args, **kwargs)
    return decorated_function


@admin.route('/admin/', methods=["GET", "POST"])
@admin_required
def home():

    form = ProblemSetForm()
    if form.validate_on_submit():

        if model_problem_set.add(author=session['username'], 
                                 slug=form.slug.data, 
                                 title=form.title.data, 
                                 db=g.db ):
            flash('Probem set added, sir.')
        else: 
            flash('Need different title or slug.')
        return redirect(url_for('admin.home'))

    return render_template("admin/home.html", 
                            form=form, 
                            problem_sets=model_problem_set.get_all(g.db))

@admin.route('/admin/feedbacks', methods=["GET", "POST"])
@admin_required
def feedbacks():
    posts=g.db.posts.find({'parent_type':'evarist_feedback'})
    return render_template("admin/feedbacks.html", 
                            posts=posts)

@admin.route('/admin/problem_questions', methods=["GET", "POST"])
@admin_required
def problem_questions():
    ps=g.db.posts.find({'parent_type':'problem'})
    posts=[]
    for p in ps:
        p['problem_set']=g.db.problem_sets.find_one({'_id':p['problem_set_id']})
        p['problem']=g.db.entries.find_one({'_id':p['problem_id']})
        posts.append(p)

    print posts

    return render_template("admin/problem_questions.html", 
                            posts=posts)

@admin.route('/admin/users', methods=["GET", "POST"])
@admin_required
def users():
    users=g.db.users.find()
    return render_template("admin/users.html", 
                            users=users)

@admin.route('/admin/checked_solutions', methods=["GET", "POST"])
@admin_required
def checked_solutions():
    solutions=g.db.solutions.find({'checked': True})
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
        if not session['username'] in voted_solution['usernames_voted']:
            if vote_form.vote.data == 'upvote': 
                voted_solution['upvotes']=voted_solution['upvotes']+1
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='upvotes',
                            update_value=voted_solution['upvotes'])
                voted_solution['usernames_voted'].append(session['username'])
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='usernames_voted',
                            update_value=voted_solution['usernames_voted'])

            if vote_form.vote.data == 'downvote':
                voted_solution['downvotes']=voted_solution['downvotes']+1
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='downvotes',
                            update_value=voted_solution['downvotes'])
                voted_solution['usernames_voted'].append(session['username'])
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='usernames_voted',
                            update_value=voted_solution['usernames_voted'])

            model_solution.update_status(g.db, voted_solution)
        
        return redirect(url_for('.not_checked_solutions'))

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
        
        return redirect(url_for('.not_checked_solutions'))



    return render_template("admin/checked_solutions.html", 
                            solutions=sols,
                            vote_form=vote_form,
                            solution_comment_form=solution_comment_form)


@admin.route('/admin/not_checked_solutions', methods=["GET", "POST"])
@admin_required
def not_checked_solutions():
    solutions=g.db.solutions.find({'checked': False})
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
        if not session['username'] in voted_solution['usernames_voted']:
            if vote_form.vote.data == 'upvote': 
                voted_solution['upvotes']=voted_solution['upvotes']+1
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='upvotes',
                            update_value=voted_solution['upvotes'])
                voted_solution['usernames_voted'].append(session['username'])
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='usernames_voted',
                            update_value=voted_solution['usernames_voted'])

            if vote_form.vote.data == 'downvote':
                voted_solution['downvotes']=voted_solution['downvotes']+1
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='downvotes',
                            update_value=voted_solution['downvotes'])
                voted_solution['usernames_voted'].append(session['username'])
                mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=ObjectId(request.args['sol_id']),
                            update_key='usernames_voted',
                            update_value=voted_solution['usernames_voted'])

            model_solution.update_status(g.db, voted_solution)
        
        return redirect(url_for('.not_checked_solutions'))

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
        
        return redirect(url_for('.not_checked_solutions'))



    return render_template("admin/not_checked_solutions.html", 
                            solutions=sols,
                            vote_form=vote_form,
                            solution_comment_form=solution_comment_form)

@admin.route('/admin/<problem_set_slug>/', methods=["GET", "POST"])
@admin_required
def problem_set_edit(problem_set_slug):


    problem_set=model_problem_set.get_by_slug(problem_set_slug, g.db)
    if problem_set==False: 
        flash('No such slug.')
        return redirect(url_for('admin.home'))

    model_problem_set.load_entries(problem_set,g.db)

    edit_problem_set_form=ProblemSetForm()
    if edit_problem_set_form.validate_on_submit():
        model_problem_set.edit(ob_id=problem_set['_id'], 
                                title=edit_problem_set_form.title.data, 
                                slug=edit_problem_set_form.slug.data, 
                                db=g.db)
        return redirect(url_for('admin.problem_set_edit',
                                problem_set_slug=edit_problem_set_form.slug.data))

    delete_problem_set_form=ProblemSetDelete()
    if delete_problem_set_form.validate_on_submit():
        if delete_problem_set_form.delete.data:
            model_problem_set.delete(ob_id=problem_set['_id'],
                                     db=g.db)
        return redirect(url_for('admin.home'))

    edit_entry_form=EditEntryForm()
    if edit_entry_form.validate_on_submit():
        entry_type='problem'
        if edit_entry_form.general_entry.data: 
            entry_type='general_entry'
            
        if edit_entry_form.delete_entry.data:
            model_entry.delete_forever(entry_id=request.args['entry_id'],
                                       problem_set_id=problem_set['_id'],
                                       db=g.db)
        else:
            model_entry.edit(ob_id=ObjectId(request.args['entry_id']),
                             db=g.db, 
                             title=edit_entry_form.edit_title.data,
                             text=edit_entry_form.edit_text.data,
                             entry_type=entry_type,
                             entry_number= int(edit_entry_form.entry_number.data),
                             problem_set_id=problem_set['_id'])

        return redirect(url_for('admin.problem_set_edit',
                                problem_set_slug=problem_set['slug']))

    entryform = EntryForm()
    if entryform.validate_on_submit():
        entry_type='problem'
        if entryform.general_entry.data: 
            entry_type='general_entry'
        if model_entry.add(entry_type=entry_type, 
                            author=session['username'],
                            authors_email=session['email'], 
                            title=entryform.title.data, 
                            db=g.db, 
                            text=entryform.text.data, 
                            problem_set_id=problem_set['_id'],
                            entry_number= int(entryform.entry_number.data)):
            print flash('Entry added, sir.')

        return redirect(url_for('admin.problem_set_edit',
                                problem_set_slug=problem_set['slug']))

    return render_template('admin/problem_set_edit.html', 
                            problem_set=problem_set, 
                            entryform=entryform,
                            edit_problem_set_form=edit_problem_set_form,
                            delete_problem_set_form=delete_problem_set_form,
                            edit_entry_form=edit_entry_form)