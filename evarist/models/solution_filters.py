# -*- coding: utf-8 -*-
from mongoengine_models import *

def get_other_solutions_on_problem_page(user,current_solution,problem):
    other_solutions=[]
    if not (problem['id'] in user['problems_can_see_other_solutions']
            or user['rights']['is_moderator'] 
            or user['rights']['is_checker']):
        return other_solutions

    other_solutions=problem['solutions']

    if current_solution in problem['solutions']:
        other_solutions.remove(current_solution)
    
    other_solutions.sort(key=lambda x: x.get('date'),reverse=True)  
    
    return other_solutions


# функция которая выдает задачи, которые пользователь может смотреть. Сначала непроверенные, потом проверенные.
def get_solutions_for_check_page(db,user):
    # prepare for getting solutions 
    solutions=[]
    if user['rights']['is_moderator'] or user['rights']['is_checker']:
        # (sort from newest to oldest)
        solutions=db.solutions.find({'author_id':{'$ne':user['id']}},
                                sort=[('date', pymongo.DESCENDING)])
    else:
        for idd in user['problems_ids']['can_see_other_solutions']:
            solutions.extend(db.solutions.find({'problem_id':ObjectId(idd)}))
        # (sort from newest to oldest)
        solutions.sort(key=lambda x: x.get('date'),reverse=True)   


    # add to solutions some needed attributes
    not_checked_sols=[]
    checked_sols=[]
    for solution in solutions:
        slug=db.problem_sets.find_one({'_id':solution['problem_set_id']})['slug']
        if not slug in model_problem_set.slugset:
            continue     
        mongo.load(solution,'solution_discussion_ids','discussion',db.posts)
        for post in solution['discussion']:
            mongo.load(post, 'author_id','author',db.users)
        if not mongo.load(solution,'author_id','author',db.users):
            solution['author']={}
            solution['author']['username']='deleted user'
        mongo.load(solution,'problem_id','problem',db.entries)
        mongo.load(solution,'problem_set_id','problem_set',db.problem_sets)
        
        if solution.get('status') =='not_checked':
            not_checked_sols.append(solution)
        else:
            checked_sols.append(solution)

    return (not_checked_sols,checked_sols)

def get_solutions_for_my_solutions_page(db,user):
    # prepare for getting solutions 
    solutions=db.solutions.find({'author_id': user['_id']},
                                            sort=[('date', pymongo.DESCENDING)])

    # add to solutions some needed attributes
    not_checked_sols=[]
    checked_sols=[]
    for solution in solutions:     
        mongo.load(solution,'solution_discussion_ids','discussion',db.posts)
        for post in solution['discussion']:
            mongo.load(post, 'author_id','author',db.users)
        if not mongo.load(solution,'author_id','author',db.users):
            solution['author']={}
            solution['author']['username']='deleted user'
        mongo.load(solution,'problem_id','problem',db.entries)
        mongo.load(solution,'problem_set_id','problem_set',db.problem_sets)
        
        if solution.get('status')=='not_checked':
            not_checked_sols.append(solution)
        else:
            checked_sols.append(solution)

    return (not_checked_sols,checked_sols)








# criterion!
def get_status(solution):
    if solution['downvotes']>=2:
        return 'checked_incorrect'
    elif solution['upvotes']>=2:
        return 'checked_correct'
    else:
        return 'not_checked'

def did_solve(solution):
    return solution.status=='checked_correct'

def can_vote(solution):
    return did_solve(solution)

def can_see_other_solutions(solution):
    return did_solve(solution)

# I dont use the following function yet, but this is the right way to do this update, arguments should be user and problem
# def did_solve_by_user_and_problem_ids(problem,user):
#     ....

def update_status(solution):
    solution.status=get_status(solution)
    solution.save()
    return 1

# subtle point, it is UNCLEAR how to move from one criterion to another
def update_who_solved(solution):
    if did_solve(solution):
        User.objects(id=solution.author.id).update_one(push__problems_solved=solution)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_solved=solution)
    return 1

def update_who_can_see_other_solutions(solution):
    if can_see_other_solutions(solution):
        User.objects(id=solution.author.id).update_one(push__problems_can_see_other_solutions=solution)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_can_see_other_solutions=solution)


    return 1

def update_who_can_vote(solution):
    solution=db.solutions.find_one({'_id':solution_id})
    if can_vote(solution):
        User.objects(id=solution.author.id).update_one(push__problems_can_vote=solution)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_can_vote=solution)

    return 1

def update_everything(solution):
    update_status(solution)
    update_who_solved(solution)
    update_who_can_see_other_solutions(solution)
    update_who_can_vote(solution)