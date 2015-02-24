from bson.objectid import ObjectId
import os, datetime, urllib, urllib2
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from login_module import login_module

admin = Blueprint('admin', __name__,
                        template_folder='templates')

@admin.route('/admin')
def admin_home():
    if session.get('username')!='admin':
        flash('You need to log in as "admin" to do that.')
        return redirect(url_for('workflow.home'))

    return render_template("admin/admin_home.html")


@admin.route('/admin/problem/<problem_set_title>/<int:problem_number>')
def show_problem(problem_set_title,problem_number):
    if session.get('username')!='admin':
        flash('You need to log in as "admin" to do that.')
        return redirect(url_for('workflow.home'))


    # problem_set={"title":"Set Theory",'problems':
    # [   {"title":"Problem 1",
    #      'text':'How many elements are in the set {1,2,{1,2}}?',
    #      'posts':[{'date':datetime.datetime.utcnow(),'author':'Artem','text':'nice problem','type':'comment'}] 
    #       #type could be later also feedback or solution
    #     }
    # ]}
    # g.db.problem_sets.insert(problem_set)
    
    # for i in g.db.problem_sets.find():
    #     print i

    problem_set=g.db.problem_sets.find_one({'title':problem_set_title})
    print problem_number-1
    posts=problem_set['problems'][problem_number-1]['posts']
    posts.reverse()
    # d=datetime.datetime.now()
    # print d['month']
    title=problem_set['problems'][problem_number-1]['title']
    text=problem_set['problems'][problem_number-1]['text']

    return render_template('admin/problem.html', problem_number=str(problem_number), 
                            problem_set_title=problem_set_title,title=title,text=text,posts=posts)

@admin.route('/admin/problem_sets')
def show_problem_sets():
    if session.get('username')!='admin':
        flash('You need to log in as "admin" to do that.')
        return redirect(url_for('workflow.home'))

    problem_sets=g.db.problem_sets.find()
    prlist=[]
    for i in problem_sets:
        prlist.append(i)
    prlist.reverse()
    return render_template('admin/problem_sets.html',problem_sets=prlist)

@admin.route('/admin/problems/<problem_set_title>')
def show_problems(problem_set_title):
    if session.get('username')!='admin':
        flash('You need to log in as "admin" to do that.')
        return redirect(url_for('workflow.home'))

    problem_set=g.db.problem_sets.find_one({"title":problem_set_title})
    problems=problem_set['problems']
    return render_template('admin/problems.html',problems=problems,problem_set_title=problem_set_title)



@admin.route('/add_problem_set', methods=['GET','POST'])
def add_problem_set():
    # posts=g.mongo.db.posts
    # posts.insert({"title":request.form['title'], "text":request.form['text']})
    if session.get('username')!='admin':
        flash('You need to log in as "admin" to do that.')
        return redirect(url_for('workflow.home'))


    if g.db.problem_sets.find_one({"title": request.form['text']}):
        flash('Sorry, such problem set already exists')
    elif session.get('username') != 'entreri':
        flash('you are not authorized to do such things')
    else:
        g.db.problem_sets.insert({"title":request.form['text'],"problems":[]})
        flash('Problem set added, sir')
    return redirect(url_for('.show_problem_sets'))


@admin.route('/add_problem/<problem_set_title>', methods=['GET','POST'])
def add_problem(problem_set_title):
    # posts=g.mongo.db.posts
    # posts.insert({"title":request.form['title'], "text":request.form['text']})
    if session.get('username')!='admin':
        flash('You need to log in as "admin" to do that.')
        return redirect(url_for('workflow.home'))

    psdoc=g.db.problem_sets.find_one({"title":problem_set_title})
    a=False
    for prob in psdoc["problems"]:
        a= (prob['title']==request.form['title'])
    if a:
        flash('Sorry, such title already exists')
        print 'GA'
    elif session.get('username') != 'entreri':
        flash('you are not authorized to do such things')
    else:
        psdoc["problems"].append({'title':request.form['title'],
                                    "text":request.form['text'],
                                     "posts":[]})
        g.db.problem_sets.update({"title":problem_set_title}, {"$set": psdoc}, upsert=False)
        psdoc=g.db.problem_sets.find_one({"title":problem_set_title})
        flash('Problem added, sir')
    return redirect(url_for('.show_problems',problem_set_title=problem_set_title))