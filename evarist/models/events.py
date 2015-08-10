# -*- coding: utf-8 -*-
from mongoengine_models import *
import parameters

def vote(user,solution,upvote_or_downvote):
    if not user['id'] in (solution['users_upvoted'] + solution['users_downvoted'] ):
        if user['rights']['is_checker']: vote_weight=2
        else: vote_weight=1

        if upvote_or_downvote == 'upvote': 
            solution.users_upvoted.append(user)
            solution.upvotes+=vote_weight

        if upvote_or_downvote == 'downvote':
            solution.users_downvoted.append(user)
            solution.downvotes+=vote_weight
        
        solution.save()
        return True
    
    else:
        return False




# criterions, depending on solution
def solution_status_by_criterion(solution):
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




def update_status(solution):
    solution.status=solution_status_by_criterion(solution)
    solution.save()
    return 1

# subtle point, it is UNCLEAR how to move from one criterion to another
def update_who_solved(solution):
    if did_solve(solution.problem,solution.author):
        User.objects(id=solution.author.id).update_one(push__problems_solved=solution.problem)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_solved=solution.problem)
    return 1

def update_who_can_see_other_solutions(solution):
    if can_see_other_solutions(solution.problem,solution.author):
        User.objects(id=solution.author.id).update_one(push__problems_can_see_other_solutions=solution.problem)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_can_see_other_solutions=solution.problem)
    return 1

def update_who_can_vote(solution):
    if can_vote(solution.problem,solution.author):
        User.objects(id=solution.author.id).update_one(push__problems_can_vote=solution.problem)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_can_vote=solution.problem)
    return 1

def update_everything(solution):
    update_status(solution)
    update_who_solved(solution)
    update_who_can_see_other_solutions(solution)
    update_who_can_vote(solution)