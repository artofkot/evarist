from bson.objectid import ObjectId
import os, datetime, urllib, urllib2
from flask import current_app, Flask, Blueprint, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing
from flask.ext.pymongo import PyMongo
from listki.models import model_problem_set, model_entry, model_post, model_solution, mongo
from listki.forms import CommentForm, SolutionForm, FeedbackToSolutionForm, EditSolutionForm, VoteForm

workflow = Blueprint('workflow', __name__,
                        template_folder='templates')

@workflow.route('/')
def home():
    # USE THIS CAREFULLY! This is template for updating some keys in all documents.
    #
    # mongo.update(collection=g.db.solutions,doc_key='all',doc_value='notimportant',
    #             update_key='GOGGO',update_value=False)
    
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
        return redirect(url_for('workflow.problem_set',problem_set_slug=problem_set_slug))

    #load general discussion
    model_entry.load_posts(problem,g.db)
    # load solutions
    model_entry.load_solution(problem,g.db,session.get('username'))
    #TODO load comments to solutions

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
                print voted_solution['upvotes']
                if voted_solution['upvotes']>=2:
                    mongo.update(collection=g.db.solutions,doc_key='_id',doc_value=ObjectId(request.args['sol_id']),
                            update_key='is_right',
                            update_value=True)
                    print 'I TRIED TO MAKE SOLUTION RIGHT!!!!!!! \n \n'
                    user=g.db.users.find_one({'username':voted_solution['author']})
                    user['problems_ids']['can_see_other_solutions'].append(voted_solution['problem_id'])
                    mongo.update(collection=g.db.users,doc_key='username',doc_value=user['username'],
                            update_key='problems_ids',
                            update_value=user['problems_ids'])

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
        return redirect(url_for('.problem', 
                                problem_set_slug=problem_set_slug,
                                problem_number=problem_number))


    solution_comment_form=FeedbackToSolutionForm()
    if solution_comment_form.validate_on_submit():

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
            model_solution.delete(db=g.db,solution=problem['solution'])
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
                    if not solut:
                        print 'HERE' + problem['text']
                        print 'SOMETHING WRONG!!!!'
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






@workflow.route('/startertry')
def startertry():
    return render_template('examples/startertry.html')

@workflow.route('/indexBitStarter')
def indexBitStarter():
    return render_template('examples/indexBitStarter.html')