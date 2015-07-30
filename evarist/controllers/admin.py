#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
import os, datetime, urllib, urllib2, pymongo
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from functools import wraps
from evarist.forms import ProblemSetForm, EntryForm, EditEntryForm, ProblemSetDelete, VoteForm, FeedbackToSolutionForm, EditCommentForm
from evarist.models import model_problem_set, model_entry, mongo, model_post, model_solution

from evarist.models_mongoengine import User, EmailUser, GplusUser, Rights

admin = Blueprint('admin', __name__,
                        template_folder='templates')
        

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
        if g.user and (not g.user.rights.is_moderator):
            flash('You are not allowed to do that.')
            return redirect(url_for('workflow.home'))
        if not g.user:
            flash('You are not allowed to do that.')
            return redirect(url_for('workflow.home'))

        return f(*args, **kwargs)
    return decorated_function


@admin.route('/admin/db', methods=["GET", "POST"])
def db():
    if current_app.debug==False: return redirect(url_for('workflow.home'))
    #####
    count1=0
    count2=0

    old_users= g.db.users.find()
    for old_user in old_users:
        rights=Rights(is_moderator=old_user['rights']['is_moderator'],
                      is_checker=old_user['rights']['is_checker'])

        if old_user.get('gplus_email'):
            count1=count1+1
            
            new_user= GplusUser(gplus_id=old_user['gplus_id'], 
                            gplus_picture=old_user['gplus_picture'],
                            gplus_name=old_user.get('username'), 
                            gplus_email=old_user['gplus_email'],
                            rights=rights)
            new_user.email=new_user.gplus_email
            new_user.username=new_user.gplus_name
            # try:new_user.save()
            # except: pass
        else:
            count2=count2+1
            new_user= EmailUser(email=old_user.get('email'), 
                            username=old_user.get('username'),
                            pw_hash=None,
                            confirmed=old_user.get('confirmed'),
                            rights=rights,
                            old_pw_hash=old_user.get('pw_hash'))

            # try:new_user.save()
            # except: pass

    # prob=Problem.objects(author=art).first()
    # print prob.text

    return 'Ok! %d %d ' % (count1,count2)



@admin.route('/admin/', methods=["GET", "POST"])
# @admin_required
def home():

    form = ProblemSetForm()
    if form.validate_on_submit():

        if model_problem_set.add(slug=form.slug.data, 
                                 title=form.title.data, 
                                 db=g.db ):
            flash('Probem set added, sir.')
        else: 
            flash('Need different title or slug.')
        return redirect(url_for('admin.home'))

    # problem_sets=model_problem_set.get_all(g.db)
    problem_sets=mongo.get_all(g.db.problem_sets)

    problem_sets_dev=[pset for pset in problem_sets if pset['status']=='dev']
    problem_sets_stage=[pset for pset in problem_sets if pset['status']=='stage']
    problem_sets_production=[pset for pset in problem_sets if pset['status']=='production']

    return render_template("admin/home.html", 
                            form=form, 
                            problem_sets=problem_sets,
                            problem_sets_dev=problem_sets_dev,
                            problem_sets_stage=problem_sets_stage,
                            problem_sets_production=problem_sets_production)

@admin.route('/admin/feedbacks', methods=["GET", "POST"])
# @admin_required
def feedbacks():
    posts=g.db.posts.find({'parent_type':'evarist_feedback'})
    return render_template("admin/feedbacks.html", 
                            posts=posts)

@admin.route('/admin/problem_questions', methods=["GET", "POST"])
# @admin_required
def problem_questions():
    ps=g.db.posts.find({'parent_type':'problem'})
    posts=[]
    for p in ps:
        p['problem_set']=g.db.problem_sets.find_one({'_id':p['problem_set_id']})
        p['problem']=g.db.entries.find_one({'_id':p['problem_id']})
        posts.append(p)
    return render_template("admin/problem_questions.html", 
                            posts=posts)

@admin.route('/admin/users', methods=["GET", "POST"])
# @admin_required
def users():
    users=g.db.users.find()
    return render_template("admin/users.html", 
                            users=users)

@admin.route('/admin/checked_solutions', methods=["GET", "POST"])
# @admin_required
def checked_solutions():

    solutions=g.db.solutions.find({'status':{ '$in': [ 'checked_correct',  'checked_incorrect' ] }})
    solutions.sort('date',pymongo.DESCENDING)
    sols=[]
    for solution in solutions:
        mongo.load(solution,'solution_discussion_ids','discussion',g.db.posts)
        if not mongo.load(solution,'author_id','author',g.db.users):
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
        
        return redirect(url_for('.not_checked_solutions'))

    solution_comment_form=FeedbackToSolutionForm()
    if solution_comment_form.validate_on_submit():

        if solution_comment_form.feedback_to_solution.data:
            solut=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
            model_post.add(text=solution_comment_form.feedback_to_solution.data,
                           db=g.db,
                           author_id=g.user.get('_id'),
                           post_type='solution->comment',
                           parent_id=ObjectId(request.args['sol_id']))
        
        return redirect(url_for('.not_checked_solutions'))



    return render_template("admin/checked_solutions.html", 
                            solutions=sols,
                            vote_form=vote_form,
                            solution_comment_form=solution_comment_form)


@admin.route('/admin/not_checked_solutions', methods=["GET", "POST"])
# @admin_required
def not_checked_solutions():
    solutions=g.db.solutions.find({'status': 'not_checked'})
    sols=[]
    for solution in solutions:
        mongo.load(solution,'solution_discussion_ids','discussion',g.db.posts)
        if not mongo.load(solution,'author_id','author',g.db.users):
            solution['author']={}
            solution['author']['username']='deleted user'
        problem=g.db.entries.find_one({'_id':ObjectId(solution['problem_id'])})
        problem_set=g.db.problem_sets.find_one({'_id':ObjectId(solution['problem_set_id'])})
        solution['problem_text']=problem['text']
        solution['problem_set']=problem_set['title']
        sols.append(solution)
    sols.sort(key=lambda x: x.get('date'),reverse=True)

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
        
        return redirect(url_for('.not_checked_solutions'))

    solution_comment_form=FeedbackToSolutionForm()
    if solution_comment_form.validate_on_submit():

        if solution_comment_form.feedback_to_solution.data:
            solut=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
            model_post.add(text=solution_comment_form.feedback_to_solution.data,
                           db=g.db,
                           author_id=g.user.get('_id'),
                           post_type='solution->comment',
                           parent_id=ObjectId(request.args['sol_id']))
        
        return redirect(url_for('.not_checked_solutions'))



    return render_template("admin/not_checked_solutions.html", 
                            solutions=sols,
                            vote_form=vote_form,
                            solution_comment_form=solution_comment_form)

@admin.route('/admin/<problem_set_slug>/', methods=["GET", "POST"])
# @admin_required
def problem_set_edit(problem_set_slug):


    problem_set=g.db.problem_sets.find_one({"slug": problem_set_slug})
    if not problem_set: 
        flash('No such slug.')
        return redirect(url_for('admin.home'))

    # model_problem_set.load_entries(problem_set,g.db)
    mongo.load(problem_set,'entries_ids','entries',g.db.entries)
    # get the numbers of problems or definitions
    model_problem_set.get_numbers(problem_set=problem_set)

    

    edit_problem_set_form=ProblemSetForm()
    if edit_problem_set_form.validate_on_submit():
        if model_problem_set.edit(ob_id=problem_set['_id'],
                                old_title=problem_set['title'], 
                                title=edit_problem_set_form.title.data, 
                                slug=edit_problem_set_form.slug.data, 
                                db=g.db,
                                status=edit_problem_set_form.status.data,
                                old_slug=problem_set['slug']): 
            flash ('edited') 
        else: flash('you must change the slug to other slug, which does not exist. Sorry :)')
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
        entry_type=edit_entry_form.entry_type.data
        
        if edit_entry_form.delete_entry.data:
            model_entry.delete_forever(entry_id=ObjectId(request.args['entry_id']),
                                       problem_set_id=problem_set['_id'],
                                       db=g.db)
        else:
            rez=model_entry.edit(ob_id=ObjectId(request.args['entry_id']),
                             db=g.db, 
                             text=edit_entry_form.edit_text.data,
                             entry_type=entry_type,
                             entry_number= int(edit_entry_form.entry_number.data),
                             problem_set_id=problem_set['_id'])
            if rez:
                flash('Entry edited, sir.')
            else:
                flash('Didnt work, slug or title is wrong.')

        return redirect(url_for('admin.problem_set_edit',
                                problem_set_slug=problem_set['slug']))

    entryform = EntryForm()
    if entryform.validate_on_submit():
        entry_type=entryform.entry_type.data
        if model_entry.add(entry_type=entry_type, 
                            author_id=g.user.get('_id'),
                            db=g.db, 
                            text=entryform.text.data, 
                            problem_set_id=problem_set['_id'],
                            entry_number= int(entryform.entry_number.data)):
            flash('Entry added, sir.')

        return redirect(url_for('admin.problem_set_edit',
                                problem_set_slug=problem_set['slug']))

    return render_template('admin/problem_set_edit.html', 
                            problem_set=problem_set, 
                            entryform=entryform,
                            edit_problem_set_form=edit_problem_set_form,
                            delete_problem_set_form=delete_problem_set_form,
                            edit_entry_form=edit_entry_form)

#CRUD comments
@admin.route('/admin/posts/', methods=["GET", "POST"])
# @admin_required
def posts():
    posts_db=g.db.posts.find(sort=[('date', pymongo.DESCENDING)])
    posts=[]
    for post in posts_db:
        mongo.load(post,'author_id','author',g.db.users)
        posts.append(post)

    edit_comment_form=EditCommentForm()
    if edit_comment_form.validate_on_submit():
        
        post=g.db.posts.find_one({'_id':ObjectId(request.args['post_id'])})
        print post

        if edit_comment_form.delete_comment.data:
            model_post.delete(db=g.db,post=post)
        else:
            g.db.posts.update_one({"_id":post['_id']},
                                        {'$set':{'text':edit_comment_form.text.data,
                                        'date':datetime.datetime.utcnow()} })
        return redirect(url_for('admin.posts'))
   

    return render_template('admin/posts.html',
                            edit_comment_form=edit_comment_form, 
                            posts=posts)    







