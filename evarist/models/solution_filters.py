# -*- coding: utf-8 -*-
from mongoengine_models import *
import problem_set_filters

def get_other_solutions_on_problem_page(user,current_solutions,problem):
    other_solutions=[]
    if not (problem in user['problems_can_see_other_solutions']
            or user['rights']['is_moderator'] 
            or user['rights']['is_checker']):
        return other_solutions

    all_other_solutions=problem['solutions']

    other_solutions=list(set(all_other_solutions) - set(current_solutions))
    
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
    checked_incorrect=[]
    checked_correct=[]
    for solution in solutions:
        if solution.status=='not_checked':
            not_checked_sols.append(solution)
        else:
            if solution.status=='checked_incorrect':
                checked_incorrect.append(solution)
            else:
                checked_correct.append(solution)
    checked_sols=checked_incorrect+checked_correct

    return (not_checked_sols,checked_sols)