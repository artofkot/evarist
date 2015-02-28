from bson.objectid import ObjectId
import os, datetime, urllib, urllib2
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from listki.models import model_problem_set, model_entry, model_post
from listki.forms import CommentForm

workflow = Blueprint('workflow', __name__,
                        template_folder='templates')

@workflow.route('/')
def home():
    return render_template('home.html',problem_sets=model_problem_set.get_all(g.db))
    

@workflow.route('/home')
def index():
    return redirect(url_for('.home'))


@workflow.route('/<problem_set_slug>/', methods=["GET", "POST"])
def problem_set(problem_set_slug):


    problem_set=model_problem_set.get_by_slug(problem_set_slug, g.db)
    if problem_set==False: 
        flash('No such problem set.')
        return redirect(url_for('.home'))


    model_problem_set.load_entries(problem_set,g.db)

    return render_template('problem_set.html', 
                            problem_set=problem_set)


@workflow.route('/<problem_set_slug>/problem/<int:problem_number>', methods=["GET", "POST"])
def problem(problem_set_slug,problem_number):
    problem_set=model_problem_set.get_by_slug(problem_set_slug, g.db)
    if problem_set==False: 
        flash('No such problem set.')
        return redirect(url_for('.home'))

    #get the problem_set
    model_problem_set.load_entries(problem_set,g.db)

    #get the problem out of problem_set
    try:
        problem=next(entry for entry in problem_set['entries'] if entry.get('problem_number')==problem_number)
    except StopIteration:
        flash('No such problem.')
        return redirect(url_for('workflow.problem',problem_set_slug=problem_set_slug))

    #load general discussion
    model_entry.load_posts(problem,g.db) #RIGHT NOW ONLY LOADS GENERAL DISCUSSION
    #TODO load solutions
    #TODO and this should be done iteratively via tree structure of comments

    problem['general_discussion'].reverse()

    general_comment_form=CommentForm()
    if general_comment_form.validate_on_submit():
        model_post.add(text=general_comment_form.text.data,
                       db=g.db,
                       author=session['username'],
                       post_type='comment',
                       parent_type='problem',
                       parent_id=problem['_id'],
                       problem_id=problem['_id'],
                       problem_set_id=problem_set['_id'])
        
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                problem_number=problem_number))

    # return redirect(url_for('.home'))
    return render_template('problem.html', 
                            problem_set_slug=problem_set_slug, 
                            problem=problem,
                            general_comment_form=general_comment_form)









@workflow.route('/show/problem_sets')
def show_problem_sets():
    problem_sets=g.db.problem_sets.find()
    prlist=[]
    for i in problem_sets:
        prlist.append(i)
    prlist.reverse()
    return render_template('show/problem_sets.html',problem_sets=prlist)


@workflow.route('/show/problems/<problem_set_title>')
def show_problems(problem_set_title):
    problem_set=g.db.problem_sets.find_one({"title":problem_set_title})
    problems=problem_set['problems']
    return render_template('show/problems.html',problems=problems,problem_set_title=problem_set_title)

@workflow.route('/show/problem/<problem_set_title>/<int:problem_number>')
def show_problem(problem_set_title,problem_number):
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

    return render_template('show/problem.html', problem_number=str(problem_number), 
                            problem_set_title=problem_set_title,title=title,text=text,posts=posts)


@workflow.route('/add_problem_set', methods=['GET','POST'])
def add_problem_set():
    # posts=g.mongo.db.posts
    # posts.insert({"title":request.form['title'], "text":request.form['text']})
    if g.db.problem_sets.find_one({"title": request.form['text']}):
        flash('Sorry, such problem set already exists')
    elif session.get('username') != 'entreri':
        flash('you are not authorized to do such things')
    else:
        g.db.problem_sets.insert({"title":request.form['text'],"problems":[]})
        flash('Problem set added, sir')
    return redirect(url_for('.show_problem_sets'))


@workflow.route('/add_problem/<problem_set_title>', methods=['GET','POST'])
def add_problem(problem_set_title):
    # posts=g.mongo.db.posts
    # posts.insert({"title":request.form['title'], "text":request.form['text']})
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


@workflow.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if 'username' not in session:
        abort(401)
    # posts=g.mongo.db.posts
    # posts.insert({"title":request.form['title'], "text":request.form['text']})
    else:
        problem_set_title=request.args.get('problem_set_title')
        problem_number=request.args.get('problem_number')


        # problem_set={"title":"Set Theory",'problems':
        # [   {"title":"Problem 1",
        #      'text':'How many elements are in the set {1,2,{1,2}}?',
        #      'posts':[{'date':datetime.datetime.utcnow(),'author':'Artem','text':'nice problem','type':'comment'}] 
        #       #type could be later also feedback or solution
        #     }
        # ]}
        psdoc=g.db.problem_sets.find_one({"title":problem_set_title})
        psdoc["problems"][int(problem_number)-1]['posts'].append({'date':datetime.datetime.utcnow(), 
                                                             'author':session['username'],
                                                             "text":request.form['text'],
                                                             'type':'comment'
                                                            })
        g.db.problem_sets.update({"title":problem_set_title}, {"$set": psdoc}, upsert=False)
        
        flash('New entry was successfully posted')
        return redirect(url_for('.show_problem',problem_set_title=problem_set_title,problem_number=problem_number))







@workflow.route('/comments')
def show_entries():
    # print g.mongo.db.collection_names()
    # for i in g.mongo.db.posts.find():
    #     print i
    posts=g.mongo.db.posts.find()
    entries = [dict(title=entry["title"], text=entry["text"]) for entry in posts]
    entries.reverse()
    return render_template('examples/show_entries.html', entries=entries)

@workflow.route('/comments_add', methods=['GET','POST'])
def add_entry():
    if not 'username' in session:
        abort(401)
    # posts=g.mongo.db.posts
    # posts.insert({"title":request.form['title'], "text":request.form['text']})
    g.db.posts.insert({"title":request.form['title'], "text":request.form['text']})
    flash('New entry was successfully posted')
    return redirect(url_for('.show_entries'))

@workflow.route('/startertry')
def startertry():
    return render_template('examples/startertry.html')

@workflow.route('/indexBitStarter')
def indexBitStarter():
    return render_template('examples/indexBitStarter.html')