# -*- coding: utf-8 -*-


# THRESHOLDS
upvote_correctness_threshold=2
downvote_correctness_threshold=2

#ACTIVE EVENTS parameters
karma_solution_written=2
karma_commented_solution=3 #(each comment matters!)
karma_voted_for_solution=1
def vote_weight(user):
    if user['rights']['is_checker']: vote_weight=2
    else: vote_weight=1

    return vote_weight

#PASSIVE EVENTS parameters
def karma_solution_was_voted(upvote_or_downvote,vote_weight):
    if upvote_or_downvote='upvote':
        return vote_weight
    else:
        return -vote_weight
karma_solution_was_commented=-1
karma_solution_became_right=10
karma_solution_became_wrong=-5



def recount_all_users_karma():
    for solution in Solution.objects()
        #ACTIVE events
        solution.author.karma+=karma_solution_written
        for comment in solution.discussion:
            if comment.author is not solution.author
                comment.author.karma+=karma_commented_solution
                comment.author.save()

                solution.author.karma+=karma_solution_was_commented
        for user in users_upvoted+users_downvoted:
            user.karma+=karma_voted_for_solution
            user.save()

        #PASSIVE events
        solution.author.karma=solution.author.karma+solution.upvotes-solution.downvotes

        if solution.status=='checked_correct':
            solution.author.karma+=karma_solution_became_right

        if solution.status=='checked_incorrect':
            solution.author.karma+=karma_solution_became_wrong

        solution.author.save()



        