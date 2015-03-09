from bson.objectid import ObjectId
import os, datetime, urllib, urllib2
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from listki.models import model_problem_set, model_entry, model_post, model_solution, mongo
from listki.forms import CommentForm, SolutionForm, FeedbackToSolutionForm, EditSolutionForm

workflow = Blueprint('workflow', __name__,
                        template_folder='templates')

@workflow.route('/')
def home():
    # mongo.update(collection=g.db.solutions,doc_key='all',doc_value='notimportant',
    #             update_key='usernames_voted',update_value=[])
    
    return render_template('home.html',problem_sets=model_problem_set.get_all(g.db))
    

@workflow.route('/home')
def index():
    return redirect(url_for('.home'))


@workflow.route('/problem_sets/<problem_set_slug>/', methods=["GET", "POST"])
def problem_set(problem_set_slug):


    problem_set=model_problem_set.get_by_slug(problem_set_slug, g.db)
    if problem_set==False: 
        flash('No such problem set.')
        return redirect(url_for('.home'))


    model_problem_set.load_entries(problem_set,g.db)

    return render_template('problem_set.html', 
                            problem_set=problem_set)


@workflow.route('/problem_sets/<problem_set_slug>/problem/<int:problem_number>/', methods=["GET", "POST"])
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
    model_entry.load_posts(problem,g.db)
    # load solutions
    model_entry.load_solution(problem,g.db,session.get('username'))
    #TODO load comments to solutions

    problem['general_discussion'].reverse()

    general_comment_form=CommentForm()
    if general_comment_form.validate_on_submit():
        print "SDFSDFSD"
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

    solution_comment_form=FeedbackToSolutionForm()
    if solution_comment_form.validate_on_submit():
        commented_solution=g.db.solutions.find_one({'_id':ObjectId(request.args['sol_id'])})
        print solution_comment_form.upvote.data
        if solution_comment_form.upvote.data:
            mongo.update(collection=g.db.solutions,
                        doc_key='_id',
                        doc_value=ObjectId(request.args['sol_id']),
                        update_key='upvotes',
                        update_value=commented_solution['upvotes']+1)
            mongo.update(collection=g.db.solutions,
                        doc_key='_id',
                        doc_value=ObjectId(request.args['sol_id']),
                        update_key='usernames_voted',
                        update_value=commented_solution['usernames_voted'].append(session['username']) )
            
        if solution_comment_form.downvote.data:
            mongo.update(collection=g.db.solutions,
                        doc_key='_id',
                        doc_value=ObjectId(request.args['sol_id']),
                        update_key='downvotes',
                        update_value=commented_solution['downvotes']+1)
            mongo.update(collection=g.db.solutions,
                        doc_key='_id',
                        doc_value=ObjectId(request.args['sol_id']),
                        update_key='usernames_voted',
                        update_value=commented_solution['usernames_voted'].append(session['username']) )

        if solution_comment_form.feedback_to_solution.data:
            model_post.add(text=solution_comment_form.feedback_to_solution.data,
                           db=g.db,
                           author=session['username'],
                           post_type='comment',
                           parent_type='solution',
                           parent_id=ObjectId(request.args['sol_id']),
                           problem_id=problem['_id'],
                           problem_set_id=problem_set['_id'])
        
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                problem_number=problem_number))

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
                       problem_id=problem['_id'],
                       problem_set_id=problem_set['_id'])

        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                problem_number=problem_number))

    edit_solution_form=EditSolutionForm()
    if edit_solution_form.validate_on_submit():
        if edit_solution_form.delete_solution.data:
            g.db.solutions.remove({'_id':problem['solution']['_id']})
        else:
            mongo.update(collection=g.db.solutions,
                            doc_key='_id',
                            doc_value=problem['solution']['_id'],
                            update_key='text',
                            update_value=edit_solution_form.edited_solution.data)

        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                problem_number=problem_number))

    user=g.db.users.find_one({'username':session.get('username')})

    g.other_solutions=[]
    if 'username' in session:
        if problem['_id'] in user['problems_ids']['can_see_other_solutions'] or session.get("is_moderator") or session.get("is_checker"):
            for sol_id in problem['solutions_ids']:
                if not currentuser_solution_id==sol_id:
                    solut=g.db.solutions.find_one({'_id':sol_id})
                    model_solution.load_discussion(g.db,solut)
                    g.other_solutions.append(solut)




    # return redirect(url_for('.home'))
    return render_template('problem.html', 
                            problem_set_slug=problem_set_slug, 
                            problem=problem,
                            general_comment_form=general_comment_form,
                            solution_comment_form=solution_comment_form,
                            solution_form=solution_form,
                            edit_solution_form=edit_solution_form)












@workflow.route('/comments')
def show_entries():
    # print g.mongo.db.collection_names()
    # for i in g.mongo.db.posts.find():
    #     print i
    posts=g.mongo.db.posts.find()
    entries = [dict(title='title', text=entry["text"]) for entry in posts]
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