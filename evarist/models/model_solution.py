# -*- coding: utf-8 -*-
import os, datetime, time
from bson.objectid import ObjectId
import mongo
import pymongo

def add(text,db,author_id,problem_id,problem_set_id,image_url):
    res=db.solutions.insert_one({'text':text,
                               'author_id':author_id,
                               'problem_id':problem_id,
                               'problem_set_id':problem_set_id,
                               'date':datetime.datetime.utcnow(),
                               'solution_discussion_ids':[],
                               'upvotes':0,
                               'downvotes':0,
                               'users_upvoted_ids':[],
                               'image_url':image_url,
                               'users_downvoted_ids':[],
                               'status': 'not_checked' # can be later changed to 'checked_correct' or 'checked_incorrect'
                               })
    ob_id=res.inserted_id

    # UPDATE OTHER DATABASES
    db.entries.update_one({"_id": problem_id}, 
                            {'$addToSet': {'solutions_ids': ob_id} })

    db.users.update_one({"_id": author_id}, 
                            {'$addToSet': {'problems_ids.solution_written': problem_id} })

    return True

def delete(db,solution):
    db.solutions.delete_one({'_id':solution['_id']})
    
    # UPDATE OTHER DATABASES
    db.entries.update_one({"_id": solution['problem_id']}, 
                            {'$pull': {'solutions_ids': solution['_id']} })

    db.users.update_one({"_id": solution['author_id']}, 
                            {'$pull': {'problems_ids.solution_written': solution['problem_id']} })


def get_other_solutions_on_problem_page(db,user,problem,current_solution_id):
    other_solutions=[]
    if not (problem['_id'] in user['problems_ids']['can_see_other_solutions']
            or user['rights']['is_moderator'] 
            or user['rights']['is_checker']):
        return other_solutions

    if current_solution_id in problem['solutions_ids']:
        problem['solutions_ids'].remove(current_solution_id)
    sol_ids= problem['solutions_ids']
    

    soluts=db.solutions.find({'_id':{ '$in': sol_ids }})
    for solut in soluts:
        mongo.load(solut,'solution_discussion_ids','discussion',db.posts)
        mongo.load(solut,'author_id','author',db.users)
        other_solutions.append(solut)
    other_solutions.sort(key=lambda x: x.get('date'),reverse=True)  
    return other_solutions


# функция которая выдает задачи, которые пользователь может смотреть. Сначала непроверенные, потом проверенные.
def get_solutions_for_check_page(db,user):
    # prepare for getting solutions 
    checked_solutions=[]
    not_checked_solutions=[]
    if user['rights']['is_moderator'] or user['rights']['is_checker']:
        not_checked_solutions.extend(db.solutions.find({'status': 'not_checked'}))
        not_checked_solutions.sort(key=lambda x: x.get('date'),reverse=True)
        # (sort from newest to oldest)

        checked_solutions.extend(db.solutions.find({'status':{ '$in': [ 'checked_correct',  'checked_incorrect' ] }}))
        checked_solutions.sort(key=lambda x: x.get('date'),reverse=True)  
    else:
        for idd in user['problems_ids']['can_see_other_solutions']:
            not_checked_solutions.extend(db.solutions.find({'problem_id':ObjectId(idd), 'status': 'not_checked'}))
            checked_solutions.extend(db.solutions.find({'problem_id':ObjectId(idd), 
                                                                  'status':{ '$in': 
                                                                            [ 'checked_correct',  
                                                                            'checked_incorrect' ] }}))
        checked_solutions.sort(key=lambda x: x.get('date'),reverse=True)
        not_checked_solutions.sort(key=lambda x: x.get('date'),reverse=True)    
    solutions=not_checked_solutions + checked_solutions


    # add to solutions some needed attributes
    sols=[]
    for solution in solutions:     
        mongo.load(solution,'solution_discussion_ids','discussion',db.posts)
        if not mongo.load(solution,'author_id','author',db.users):
            solution['author']={}
            solution['author']['username']='deleted user'
        mongo.load(solution,'problem_id','problem',db.entries)
        mongo.load(solution,'problem_set_id','problem_set',db.problem_sets)
        sols.append(solution)

    return sols









# criterion!
def get_status(solution):
    if solution['downvotes']>=2:
        return 'checked_incorrect'
    elif solution['upvotes']>=2:
        return 'checked_correct'
    else:
        return 'not_checked'

def did_solve(db,solution_id):
    solution=db.solutions.find_one({'_id':solution_id})
    if solution['status']=='checked_correct':
        return True
    else: 
        return False

def can_vote(db,solution_id):
    return did_solve(db,solution_id)

def can_see_other_solutions(db,solution_id):
    return did_solve(db,solution_id)

# I dont use the following function yet, but this is the right way to do this update, arguments should be user and problem
# def did_solve_by_user_and_problem_ids(db,problem_id,user_id):
#     solution=db.solutions.find_one({'author_id':solution_id,
#                                     'problem_id':problem_id})
#     if solution and solution['status']=='checked_correct':
#         return True
#     else: 
#         return False







def update_status(db,solution_id):
    solution=db.solutions.find_one({'_id':solution_id})
    new_status=get_status(solution)
    db.solutions.update_one({"_id": solution_id}, 
                            {'$set': {'status': new_status} })
    return 1

# subtle point, it is UNCLEAR how to move from one criterion to another
def update_who_solved(db,solution_id):
    solution=db.solutions.find_one({'_id':solution_id})
    if did_solve(db,solution_id):
        db.users.update_one({"_id": solution['author_id']}, 
                            {'$addToSet': {'problems_ids.solved': solution_id} })
    else:
        db.users.update_one({"_id": solution['author_id']}, 
                            {'$pull': {'problems_ids.solved': solution_id} })

    return 1

def update_who_can_see_other_solutions(db,solution_id):
    solution=db.solutions.find_one({'_id':solution_id})
    if can_see_other_solutions(db,solution_id):
        db.users.update_one({"_id": solution['author_id']}, 
                            {'$addToSet': {'problems_ids.can_see_other_solutions': solution_id} })
    else:
        db.users.update_one({"_id": solution['author_id']}, 
                            {'$pull': {'problems_ids.can_see_other_solutions': solution_id} })

    return 1

def update_who_can_vote(db,solution_id):
    solution=db.solutions.find_one({'_id':solution_id})
    if can_vote(db,solution_id):
        db.users.update_one({"_id": solution['author_id']}, 
                            {'$addToSet': {'problems_ids.can_vote': solution_id} })
    else:
        db.users.update_one({"_id": solution['author_id']}, 
                            {'$pull': {'problems_ids.can_vote': solution_id} })

    return 1

def update_everything(db,solution_id):
    update_status(db,solution_id)
    update_who_solved(db,solution_id)
    update_who_can_see_other_solutions(db,solution_id)
    update_who_can_vote(db,solution_id)