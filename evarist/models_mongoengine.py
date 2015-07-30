from flask.ext.mongoengine import MongoEngine
db = MongoEngine()

import datetime
from mongoengine import *

#collection for registered users
class Rights(db.EmbeddedDocument):
    is_moderator=db.BooleanField(default=False)
    is_checker =db.BooleanField(default=False)

class User(db.Document):
    date = db.DateTimeField(default=datetime.datetime.now)
    karma= db.IntField(default=1)
    rights = db.EmbeddedDocumentField('Rights', default=Rights())

    problems_solution_written=db.ListField(db.ReferenceField('Problem'))
    problems_solved=db.ListField(db.ReferenceField('Problem'))
    problems_can_see_other_solutions=db.ListField(db.ReferenceField('Problem'))
    problems_can_vote=db.ListField(db.ReferenceField('Problem'))

    meta = {'allow_inheritance': True}

class GplusUser(User):
    provider= db.StringField(default='gplus')
    gplus_id=db.StringField()
    gplus_picture=db.StringField()
    gplus_email=db.StringField()
    gplus_name=db.StringField()

    # default=gplus_name,
    username = db.StringField(unique_with='provider', max_length=256)
    # default=gplus_email,
    email = db.StringField(unique_with='provider', max_length=256)

class EmailUser(User):
    provider= db.StringField(default='email')
    username = db.StringField(required=True,unique_with='provider', max_length=256)
    email = db.StringField(required=True, unique_with='provider', max_length=256)
    pw_hash = db.StringField()
    confirmed= db.BooleanField(default=False)


#collection for content blocks
class Content_block(db.Document):
    text = db.StringField()
    date = db.DateTimeField(default=datetime.datetime.now)
    tags= db.ListField(db.StringField(max_length=128))
    
    problem_set= db.ReferenceField('Problem_set')
    author= db.ReferenceField('User')
    general_discussion=db.ListField(db.ReferenceField('Comment'))

    meta = {'allow_inheritance': True}

class Problem(Content_block):
    type_ = db.StringField(max_length=64, default='problem', choices=('problem', 'definition', 'general_content_block'))
    solutions=db.ListField(db.ReferenceField('Solution'))
 
class Definition(Content_block):
    type_ = db.StringField(max_length=64, default='definition', choices=('problem', 'definition', 'general_content_block'))

class GeneralContent_block(Content_block):
    type_ = db.StringField(max_length=64, default='general_content_block', choices=('problem', 'general_content_block', 'general_content_block'))

#collection for problem sets
class Problem_set(db.Document):
    name = db.StringField(required=True, max_length=128)
    slug = db.StringField(max_length=128, unique=True)
    status = db.StringField(max_length=64, default='dev', choices=('dev', 'stage', 'production'))
    tags= db.ListField(db.StringField(max_length=128))
    
    content_blocks = db.ListField(db.ReferenceField('Content_block'))




#collection for solutions
class Solution(db.Document):
    text = db.StringField(required=True)
    answer = db.StringField()
    date = db.DateTimeField(default=datetime.datetime.now)
    language = db.StringField(max_length=256, default='rus')
    status = db.StringField(max_length=64, default='not_checked', choices=('checked_correct', 'checked_incorrect', 'not_checked'))

    problem = db.ReferenceField('Problem')
    author= db.ReferenceField('User')
    problem_set = db.ReferenceField('Problem_set')
    discussion=db.ListField(db.ReferenceField('Comment'))

    downvotes=db.IntField(default=0)
    upvotes=db.IntField(default=0)
    users_upvoted=db.ListField(db.ReferenceField('User'))
    users_downvoted=db.ListField(db.ReferenceField('User'))


#collection for comments
class Comment(db.Document):
    text = db.StringField(required=True)
    date = db.DateTimeField(default=datetime.datetime.now)
    author= db.ReferenceField('User')

    meta = {'allow_inheritance': True}

class CommentToSolution(Comment):    
    parent_solution = db.ReferenceField('Solution')
    type_ = db.StringField(max_length=64, default='comment_to_solution', choices=('comment_to_solution', 'comment_to_content_block', 'feedback'))

class CommentToContent_block(Comment): 
    parent_content_block = db.ReferenceField('Content_block')
    type_ = db.StringField(max_length=64, default='comment_to_content_block', choices=('comment_to_solution', 'comment_to_content_block', 'feedback'))

class CommentFeedback(Comment): 
    feedback_to_what = db.StringField()
    type_ = db.StringField(max_length=64, default='feedback', choices=('comment_to_solution', 'comment_to_content_block', 'feedback'))



# collection for subscribed users
class Subscribed_user(db.Document):
    email = db.StringField(required=True, unique=True, max_length=256)
    date = db.DateTimeField(default=datetime.datetime.now) 


# deleting rules see here:
# http://docs.mongoengine.org/guide/defining-documents.html#dealing-with-deletion-of-referred-documents
# and here (API page) http://docs.mongoengine.org/en/latest/apireference.html#mongoengine.fields.ReferenceField
Problem.register_delete_rule(User,'problems_solved', PULL)
Problem.register_delete_rule(User,'problems_can_vote', PULL)
Problem.register_delete_rule(User,'problems_solution_written',PULL)
Problem.register_delete_rule(User,'problems_can_see_other_solutions',PULL)
Problem.register_delete_rule(Solution,'problem', NULLIFY)

Problem_set.register_delete_rule(Content_block,'problem_set',NULLIFY)
Problem_set.register_delete_rule(Solution,'problem_set',NULLIFY)

User.register_delete_rule(Content_block,'author',NULLIFY)
User.register_delete_rule(Comment,'author',NULLIFY)
User.register_delete_rule(Solution,'author',NULLIFY)
User.register_delete_rule(Solution,'users_upvoted',PULL)
User.register_delete_rule(Solution,'users_downvoted',PULL)

Solution.register_delete_rule(Problem,'solutions',PULL)
Solution.register_delete_rule(CommentToSolution,'parent_solution',NULLIFY)

Content_block.register_delete_rule(Problem_set,'content_blocks',PULL)
Content_block.register_delete_rule(CommentToContent_block,'parent_content_block',NULLIFY)

Comment.register_delete_rule(Content_block,'general_discussion',PULL)
Comment.register_delete_rule(Solution,'discussion',PULL)






