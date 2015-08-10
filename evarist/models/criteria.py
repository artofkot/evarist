# -*- coding: utf-8 -*-
from mongoengine_models import *
import parameters


# subtle point, it is UNCLEAR how to move from one criterion to another
def get_solution_status_by_criterion(solution):
    if solution['downvotes']>=parameters.downvote_correctness_threshold:
        return 'checked_incorrect'
    elif solution['upvotes']>=parameters.upvote_correctness_threshold:
        return 'checked_correct'
    else:
        return 'not_checked'

def did_solve(problem, user):
    solutions=Solution.objects(problem=problem,author=user)
    for solution in solutions:
        if solution.status=='checked_correct':
            return True
    return False

def can_vote(problem, user):
    return did_solve(problem, user)

def can_see_other_solutions(problem, user):
    return did_solve(problem, user)
