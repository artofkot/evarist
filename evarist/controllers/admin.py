#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from bson.objectid import ObjectId
import os, datetime, urllib, urllib2, pymongo
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from functools import wraps
from evarist.forms import ProblemSetForm, Content_blockForm, EditContent_blockForm, ProblemSetDelete, VoteForm, FeedbackToSolutionForm, EditCommentForm
from evarist.models.mongoengine_models import *


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
@admin_required
def db():
    if current_app.debug==False: return redirect(url_for('workflow.home'))
    #####
    count1=0
    count2=0
    count3=0

    old_posts=g.db.posts.find()
    for old_post in old_posts:
        old_author=g.db.users.find_one({'_id':old_post['author_id']})
        old_solution=g.db.solutions.find_one({'_id':old_post['parent_id']})
        if old_author and old_solution: author=User.objects(email=old_author.get('email')).first()
        else:
            print 'AAAAAA %s' % old_post['text']
            continue
        parent_solution=Solution.objects(text=old_solution['text']).first()    
        count1+=1
        # try:
        #     comment=CommentToSolution(text=old_post['text'],
        #                     author=author,
        #                     parent_solution=parent_solution)
        #     comment.save()
        #     parent_solution.discussion.append(comment)
        #     parent_solution.save()
        #     count3+=1
        # except: count2+=1
            

    return '%d %d %d' % (count1,count2,count3)



@admin.route('/admin/', methods=["GET", "POST"])
@admin_required
def home():

    form = ProblemSetForm()
    if form.validate_on_submit():

        try:
            problem_set=Problem_set(slug=form.slug.data, 
                                 title=form.title.data)
            problem_set.save()
            flash('Probem set added, sir.')
        except: 
            flash('Need a different title and slug.')
        return redirect(url_for('admin.home'))

    problem_sets=Problem_set.objects()

    problem_sets_dev=[pset for pset in problem_sets if pset['status']=='dev']
    problem_sets_stage=[pset for pset in problem_sets if pset['status']=='stage']
    problem_sets_production=[pset for pset in problem_sets if pset['status']=='production']

    return render_template("admin/home.html", 
                            form=form, 
                            problem_sets=problem_sets,
                            problem_sets_dev=problem_sets_dev,
                            problem_sets_stage=problem_sets_stage,
                            problem_sets_production=problem_sets_production)

@admin.route('/admin/<problem_set_slug>/', methods=["GET", "POST"])
@admin_required
def problem_set_edit(problem_set_slug):

    problem_set=Problem_set.objects(slug=problem_set_slug).first()
    if not problem_set: 
        flash('No such slug.')
        return redirect(url_for('admin.home'))

    problem_set.assign_numbers_to_content_blocks()

    edit_problem_set_form=ProblemSetForm()
    if edit_problem_set_form.validate_on_submit():
        problem_set.title=edit_problem_set_form.title.data
        problem_set.slug=edit_problem_set_form.slug.data
        if edit_problem_set_form.status.data:
            problem_set.status=edit_problem_set_form.status.data
        try: 
            problem_set.save()
            flash('Problem_set was edited')
        except: 
            flash('you must change the slug or title to other values, which do not exist in our database.')
            return redirect(url_for('admin.problem_set_edit',
                                problem_set_slug=problem_set_slug))

        return redirect(url_for('admin.problem_set_edit',
                                problem_set_slug=problem_set.slug))

    delete_problem_set_form=ProblemSetDelete()
    if delete_problem_set_form.validate_on_submit():
        if delete_problem_set_form.delete.data:
            problem_set.delete()
        return redirect(url_for('admin.home'))

    edit_content_block_form=EditContent_blockForm()
    if edit_content_block_form.validate_on_submit():
        content_block=Content_block.objects(id=ObjectId(request.args['content_block_id'])).first()
        place_of_content_block= int(edit_content_block_form.place_of_content_block.data)
        if edit_content_block_form.delete_content_block.data:
            content_block.delete()
        else:
            content_block.text=edit_content_block_form.edit_text.data
            content_block.type_=edit_content_block_form.type_.data
            try:
                problem_set.content_blocks.remove(content_block)
                problem_set.content_blocks.insert(place_of_content_block,content_block)
                content_block.save()
                problem_set.save()
                flash('content_block edited, sir.')
            except:
                flash('Didnt work, slug or title is wrong.')

        return redirect(url_for('admin.problem_set_edit',
                                problem_set_slug=problem_set['slug']))

    content_blockform = Content_blockForm()
    if content_blockform.validate_on_submit():
        content_block=Content_block()
        content_block.type_=content_blockform.type_.data
        # if type_=='definition': content_block=Definition()
        # if type_=='problem': content_block=Problem()
        # if type_=='general_content_block': content_block=GeneralContent_block()
        content_block.author=g.user
        content_block.problem_set=problem_set
        content_block.text=content_blockform.text.data
        place_of_content_block= int(content_blockform.place_of_content_block.data)
            
        try:
            content_block.save()
            problem_set.content_blocks.insert(place_of_content_block,content_block)
            problem_set.save()
            flash('content_block added, sir.')
        except: 
            flash('Something went wrong')

        return redirect(url_for('admin.problem_set_edit',
                                problem_set_slug=problem_set['slug']))

    return render_template('admin/problem_set_edit.html', 
                            problem_set=problem_set, 
                            content_blockform=content_blockform,
                            edit_problem_set_form=edit_problem_set_form,
                            delete_problem_set_form=delete_problem_set_form,
                            edit_content_block_form=edit_content_block_form)





@admin.route('/admin/users', methods=["GET", "POST"])
@admin_required
def users():
    users=User.objects()
    return render_template("admin/users.html", 
                            users=users)

#CRUD comments
@admin.route('/admin/comments/', methods=["GET", "POST"])
@admin_required
def comments():
    comments=Comment.objects()

    edit_comment_form=EditCommentForm()
    if edit_comment_form.validate_on_submit():
        comment=Comment.objects(id=ObjectId(request.args['comment_id'])).first()
        if edit_comment_form.delete_comment.data:
            comment.delete()
        else:
            comment.text=edit_comment_form.text.data
            comment.date=datetime.datetime.utcnow()
            comment.save()
        return redirect(url_for('admin.comments'))
   
    solutions=Solution.objects()
    comments=Comment.objects(_cls__ne='Comment.Solution')

    return render_template('admin/comments.html',
                            edit_comment_form=edit_comment_form, 
                            comments=comments,
                            solutions=solutions)    







