# -*- coding: utf-8 -*-
import os, datetime, time
from bson.objectid import ObjectId
import mongo

def add(text,db,author_id,problem_id,problem_set_id):
    res=db.solutions.insert_one({'text':text,
                               'author_id':author_id,
                               'problem_id':problem_id,
                               'problem_set_id':problem_set_id,
                               'date':datetime.datetime.utcnow(),
                               'solution_discussion_ids':[],
                               'upvotes':0,
                               'downvotes':0,
                               'users_upvoted_ids':[],
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



# функция которая выдает задачи, которые пользователь может смотреть. Сначала непроверенные, потом проверенные.
def get_solution_for_check_page(db,user):
    # prepare for getting solutions 
    solutions=[]
    checked_solutions=[]
    not_checked_solutions=[]
    if user['rights']['is_moderator'] or user['rights']['is_checker']:
        not_checked_solutions.extend(db.solutions.find({'status': 'not_checked'}))
        not_checked_solutions.sort(key=lambda x: x.get('date'),reverse=True)
        # (sort from newest to oldest)

        checked_solutions.extend(db.solutions.find({'status':{ '$in': [ 'checked_correct',  'checked_incorrect' ] }}))
        checked_solutions.sort(key=lambda x: x.get('date'),reverse=True)

        solutions=not_checked_solutions + checked_solutions
    else:
        for idd in user['problems_ids']['can_see_other_solutions']:
            not_checked_solutions.solutions.extend(db.solutions.find({'problem_id':ObjectId(idd), 'status': 'not_checked'}))
            checked_solutions.solutions.extend(db.solutions.find({'problem_id':ObjectId(idd), 
                                                                  'status':{ '$in': 
                                                                            [ 'checked_correct',  
                                                                            'checked_incorrect' ] }}))
        checked_solutions.sort(key=lambda x: x.get('date'),reverse=True)
        not_checked_solutions.sort(key=lambda x: x.get('date'),reverse=True)
        solutions=not_checked_solutions + checked_solutions

    # add to solutions some needed attributes
    sols=[]
    
    for solution in solutions:
        start1=time.time()
        
        # solution['discussion']=db.posts.find({'_id':{ '$in': solution['solution_discussion_ids'] }})
        # print("-1-- %s seconds ---" % (time.time() - start1))
        mongo.load(solution,'solution_discussion_ids','discussion',db.posts)
        start2=time.time()
        # print("-1-- %s seconds ---" % (time.time() - start1))

        
        # solution['author']=db.users.find_one({'_id':solution['author_id'] })
        # if not solution['author']: 
        #     solution['author']={}
        #     solution['author']['username']='deleted user'
        # print("-2-- %s seconds ---" % (time.time() - start2))
        if not mongo.load(solution,'author_id','author',db.users):
            solution['author']={}
            solution['author']['username']='deleted user'
        
        # print("-2-- %s seconds ---" % (time.time() - start2))
        start3=time.time()


        mongo.load(solution,'problem_id','problem',db.entries)
        # print("-3-- %s seconds ---" % (time.time() - start3))

        start4=time.time()
        mongo.load(solution,'problem_set_id','problem_set',db.problem_sets)
        # problem=db.entries.find_one({'_id':ObjectId(solution['problem_id'])})
        # problem_set=db.problem_sets.find_one({'_id':ObjectId(solution['problem_set_id'])})
        # solution['problem_text']=problem['text']
        # solution['problem_set_title']=problem_set['title']
        sols.append(solution)
        # print("-4-- %s seconds --- BASTA" % (time.time() - start4))



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