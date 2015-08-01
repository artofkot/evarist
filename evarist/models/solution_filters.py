# -*- coding: utf-8 -*-
from mongoengine_models import *
import problem_set_filters

def get_other_solutions_on_problem_page(user,current_solution,problem):
    other_solutions=[]
    if not (problem in user['problems_can_see_other_solutions']
            or user['rights']['is_moderator'] 
            or user['rights']['is_checker']):
        return other_solutions

    other_solutions=problem['solutions']

    if current_solution in problem['solutions']:
        other_solutions.remove(current_solution)
    
    other_solutions.sort(key=lambda x: x.date,reverse=True)  
    
    return other_solutions


# функция которая выдает задачи, которые пользователь может смотреть. Сначала непроверенные, потом проверенные.
def get_solutions_for_check_page(user):
    # prepare for getting solutions 
    solutions=[]
    if user['rights']['is_moderator'] or user['rights']['is_checker']:
        # (sort from newest to oldest)
        solutions=Solution.objects(author__ne=user).order_by('-date')

    else:
        for problem in user['problems_can_see_other_solutions']:
            solutions.extend(problem.solutions)
        # (sort from newest to oldest)
        solutions.sort(key=lambda x: x.date,reverse=True)   


    # add to solutions some needed attributes
    not_checked_sols=[]
    checked_sols=[]
    for solution in solutions:
        slug=solution.problem_set.slug
        if not slug in problem_set_filters.slugset:
            continue
        if solution.status =='not_checked':
            not_checked_sols.append(solution)
        else:
            checked_sols.append(solution)

    return (not_checked_sols,checked_sols)

def get_solutions_for_my_solutions_page(user):
    # prepare for getting solutions 
    solutions=Solution.objects(author=user).order_by('-date')

    # add to solutions some needed attributes
    not_checked_sols=[]
    checked_sols=[]
    for solution in solutions:
        if solution.status=='not_checked':
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
        User.objects(id=solution.author.id).update_one(push__problems_solved=solution.problem)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_solved=solution.problem)
    return 1

def update_who_can_see_other_solutions(solution):
    if can_see_other_solutions(solution):
        User.objects(id=solution.author.id).update_one(push__problems_can_see_other_solutions=solution.problem)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_can_see_other_solutions=solution.problem)


    return 1

def update_who_can_vote(solution):
    if can_vote(solution):
        User.objects(id=solution.author.id).update_one(push__problems_can_vote=solution.problem)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_can_vote=solution.problem)
    return 1

def update_everything(solution):
    update_status(solution)
    update_who_solved(solution)
    update_who_can_see_other_solutions(solution)
    update_who_can_vote(solution)