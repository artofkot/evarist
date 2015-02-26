from bson.objectid import ObjectId
import os, datetime, urllib, urllib2
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from functools import wraps
from listki.forms import ProblemSetForm, EntryForm, EditEntryForm, ProblemSetDelete
from listki.models import model_problem_set, model_entry

admin = Blueprint('admin', __name__,
                        template_folder='templates')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('username')!='admin':
            flash('You are not allowed to do that.')
            return redirect(url_for('workflow.home'))
        return f(*args, **kwargs)
    return decorated_function


@admin.route('/admin/', methods=["GET", "POST"])
@admin_required
def home():

    form = ProblemSetForm()
    if form.validate_on_submit():

        if model_problem_set.add(author=session['username'], slug=form.slug.data, title=form.title.data, db=g.db ):
            flash('Probem set added, sir.')
        return redirect(url_for('admin.home'))

    return render_template("admin/home.html", form=form, problem_sets=model_problem_set.get_all(g.db))

@admin.route('/admin/<problem_set_slug>/', methods=["GET", "POST"])
@admin_required
def problem_set_edit(problem_set_slug):


    problem_set=model_problem_set.get_by_slug(problem_set_slug, g.db)
    if problem_set==False: 
        flash('No such slug.')
        return redirect(url_for('admin.home'))
    
    print problem_set.get('entries_id')

    problem_set['entries']=[]
    if problem_set.get('entries_id'):
        for ob_id in problem_set['entries_id']:
            entry=g.db.entries.find_one({'_id':ob_id})
            problem_set['entries'].append(entry)


    edit_problem_set_form=ProblemSetForm()
    if edit_problem_set_form.validate_on_submit():
        model_problem_set.edit(ob_id=problem_set['_id'], title=edit_problem_set_form.title.data, 
                                slug=edit_problem_set_form.slug.data, db=g.db)
        return redirect(url_for('admin.problem_set_edit',problem_set_slug=edit_problem_set_form.slug.data))

    delete_problem_set_form=ProblemSetDelete()
    if delete_problem_set_form.validate_on_submit():
        if delete_problem_set_form.delete.data:
            model_problem_set.delete(ob_id=problem_set['_id'],db=g.db)
        return redirect(url_for('admin.home'))

    edit_entry_form=EditEntryForm()
    if edit_entry_form.validate_on_submit():
        if edit_entry_form.delete_entry.data:
            print request.args['entry_id']+'YAYAY'
            model_entry.delete_forever(entry_id=request.args['entry_id'],problem_set_id=problem_set['_id'],db=g.db)
        else:
            model_entry.edit(ob_id=ObjectId(request.args['entry_id']),db=g.db, 
                title=edit_entry_form.edit_title.data,
                text=edit_entry_form.edit_text.data)

        return redirect(url_for('admin.problem_set_edit',problem_set_slug=problem_set['slug']))



    entryform = EntryForm()
    if entryform.validate_on_submit():
        if model_entry.add(entry_type='problem', author=session['username'], 
                            title=entryform.title.data, db=g.db, text=entryform.text.data, 
                            problem_set_id=problem_set['_id'] ):
            print flash('Entry added, sir.')
        # return redirect(url_for('admin.home'))
        return redirect(url_for('admin.problem_set_edit',problem_set_slug=problem_set['slug']))

    return render_template('admin/problem_set_edit.html', 
                            problem_set=problem_set, 
                            entryform=entryform,
                            edit_problem_set_form=edit_problem_set_form,
                            delete_problem_set_form=delete_problem_set_form,
                            edit_entry_form=edit_entry_form)

















@admin.route('/admin/problem/<problem_set_title>/<int:problem_number>')
@admin_required
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

    return render_template('admin/problem.html', problem_number=str(problem_number), 
                            problem_set_title=problem_set_title,title=title,text=text,posts=posts)

@admin.route('/admin/problem_sets')
@admin_required
def show_problem_sets():

    problem_sets=g.db.problem_sets.find()
    prlist=[]
    for i in problem_sets:
        prlist.append(i)
    prlist.reverse()
    return render_template('admin/problem_sets.html',problem_sets=prlist)

@admin.route('/admin/problems/<problem_set_title>')
@admin_required
def show_problems(problem_set_title):

    problem_set=g.db.problem_sets.find_one({"title":problem_set_title})
    problems=problem_set['problems']
    return render_template('admin/problems.html',problems=problems,problem_set_title=problem_set_title)



# @admin.route('/add_problem_set', methods=['GET','POST'])
# @admin_required
# def add_problem_set():
#     # posts=g.mongo.db.posts
#     # posts.insert({"title":request.form['title'], "text":request.form['text']})


#     if g.db.problem_sets.find_one({"title": request.form['text']}):
#         flash('Sorry, such problem set already exists')
#     elif session.get('username') != 'entreri':
#         flash('you are not authorized to do such things')
#     else:
#         g.db.problem_sets.insert({"title":request.form['text'],"problems":[]})
#         flash('Problem set added, sir')
#     return redirect(url_for('.show_problem_sets'))


@admin.route('/add_problem/<problem_set_title>', methods=['GET','POST'])
@admin_required
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