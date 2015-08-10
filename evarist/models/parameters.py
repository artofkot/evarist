# -*- coding: utf-8 -*-


upvote_correctness_threshold=2
downvote_correctness_threshold=2


#ACTIVE events = actions of user

# how much karma gains the author of solution
karma_solution_written=2

# how much karma gains the author of comment
karma_commented_solution=5

# how much karma gains voter
karma_voted_for_solution=1


####################################################

#PASSIVE events = consequences of actions of users

# how much karma gains author of solution
def karma_solution_was_voted(upvotes=0,downvotes=0):
    return upvotes - downvotes

karma_solution_was_commented=-1

karma_solution_became_right=10
karma_solution_became_wrong=-5



