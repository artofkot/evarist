# -*- coding: utf-8 -*-
from mongoengine_models import *
import parameters
import criteria


# ACTIVE EVENTS
# these events is triggered by vote forms on website
def vote(user,solution,upvote_or_downvote):
    if not user['id'] in (solution['users_upvoted'] + solution['users_downvoted'] ):
        vote_weight=parameters.vote_weight(user)

        if upvote_or_downvote == 'upvote': 
            solution.users_upvoted.append(user)
            solution.upvotes+=vote_weight

        if upvote_or_downvote == 'downvote':
            solution.users_downvoted.append(user)
            solution.downvotes+=vote_weight
        
        solution.author.karma+=parameters.karma_solution_was_voted(
                                                upvote_or_downvote,vote_weight)
        solution.author.save()
        solution.save()

        user.karma+=parameters.karma_voted_for_solution
        user.save()

        return True
    
    else:
        return False

def solution_written(solution):
    solution.problem.solutions.append(solution)
    solution.problem.save()
    
    solution.author.problems_solution_written.append(problem)
    solution.author.karma+=parameters.karma_solution_written
    solution.author.save()

def commented_solution(comment):
    comment.parent_solution.discussion.append(comment)
    comment.parent_solution.save()

    if comment.author is not comment.parent_solution.author:
        comment.author.karma+=parameters.karma_commented_solution



# PASSIVE EVENTS
def do_events_after_voting(solution):
    (old_status,solution)=update_status(solution)

    if old_status!=solution.status:
        change_solution_status(old_status,solution)

    update_who_solved(solution)

    update_who_can_see_other_solutions(solution)

    update_who_can_vote(solution)

def update_status(solution):
    old_status=solution.status
    solution.status=criteria.get_solution_status_by_criterion(solution)
    solution.save()

    return (old_status,solution)


# this event is triggered in update_status
def change_solution_status(old_status,solution):
    if old_status=='not_checked' and solution.status=='checked_correct':
        solution.author.karma+=parameters.karma_solution_became_right

    if old_status=='checked_correct' and solution.status=='not_checked':
        solution.author.karma-=parameters.karma_solution_became_right



    if old_status=='not_checked' and solution.status=='checked_incorrect':
        solution.author.karma+=parameters.karma_solution_became_wrong

    if old_status=='checked_incorrect' and solution.status=='not_checked':
        solution.author.karma-=parameters.karma_solution_became_wrong



    if old_status=='checked_incorrect' and solution.status=='checked_correct':
        solution.author.karma+=parameters.karma_solution_became_right
        solution.author.karma-=parameters.karma_solution_became_wrong

    if old_status=='checked_correct' and solution.status=='checked_incorrect':
        solution.author.karma-=parameters.karma_solution_became_right
        solution.author.karma+=parameters.karma_solution_became_wrong

    solution.save()



def update_who_solved(solution):
    if criteria.did_solve(solution.problem,solution.author):
        User.objects(id=solution.author.id).update_one(push__problems_solved=solution.problem)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_solved=solution.problem)
    return 1

def update_who_can_see_other_solutions(solution):
    if criteria.can_see_other_solutions(solution.problem,solution.author):
        User.objects(id=solution.author.id).update_one(push__problems_can_see_other_solutions=solution.problem)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_can_see_other_solutions=solution.problem)
    return 1

def update_who_can_vote(solution):
    if criteria.can_vote(solution.problem,solution.author):
        User.objects(id=solution.author.id).update_one(push__problems_can_vote=solution.problem)
    else:
        User.objects(id=solution.author.id).update_one(pull__problems_can_vote=solution.problem)
    return 1




