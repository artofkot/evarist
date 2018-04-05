# -*- coding: utf-8 -*-
from flask_mongoengine import MongoEngine
db = MongoEngine()

import datetime
from mongoengine import *

#collection for registered users
class Rights(db.EmbeddedDocument):
    is_moderator=db.BooleanField(default=False)
    is_checker =db.BooleanField(default=False)

class User(db.Document):
    date = db.DateTimeField(default=datetime.datetime.now())
    date_last_email_sent=db.DateTimeField(default=datetime.datetime.now())

    karma= db.IntField(default=1)
    rights = db.EmbeddedDocumentField('Rights', default=Rights())

    problems_solution_written=db.ListField(db.ReferenceField('Content_block'))
    problems_solved=db.ListField(db.ReferenceField('Content_block'))
    problems_can_see_other_solutions=db.ListField(db.ReferenceField('Content_block'))
    problems_can_vote=db.ListField(db.ReferenceField('Content_block'))


    def __unicode__(self):
        return self.username + '•'.decode('utf-8') + str(self.karma)
    

    meta = {'allow_inheritance': True}

class GplusUser(User):
    provider= db.StringField(default='gplus', max_length=64)
    gplus_id=db.StringField(unique=True, sparse=True)
    gplus_picture=db.StringField()
    gplus_email=db.StringField()
    gplus_name=db.StringField()

    # default=gplus_name,
    username = db.StringField()
    # default=gplus_email,
    email = db.StringField(required=True)


class EmailUser(User):
    provider= db.StringField(default='email')
    username = db.StringField(required=True, max_length=256)
    email = db.StringField(required=True, unique_with='provider', max_length=256)
    pw_hash = db.StringField()
    old_pw_hash = db.StringField()
    confirmed= db.BooleanField(default=False)

    


#collection for content blocks
class Content_block(db.Document):
    text = db.StringField()
    date = db.DateTimeField(default=datetime.datetime.now)
    tags= db.ListField(db.StringField(max_length=128))
    
    problem_set= db.ReferenceField('Problem_set')
    author= db.ReferenceField('User')
    general_discussion=db.ListField(db.ReferenceField('Comment'))
    number_in_problem_set=db.IntField()

    type_ = db.StringField(max_length=64, default='problem', choices=('problem', 'definition', 'general_content_block'))
    solutions=db.ListField(db.ReferenceField('Solution'))

    meta = {'allow_inheritance': True}
    old_id = db.StringField()

#collection of courses
class Course(db.Document):
    name=db.StringField(required=True, unique=True, max_length=1024)
    slug = db.StringField(max_length=128, required=True, unique=True)
    problem_sets=db.ListField(db.ReferenceField('Problem_set'))

#collection for problem sets
class Problem_set(db.Document):
    title = db.StringField(required=True, unique=True, max_length=1024)
    slug = db.StringField(max_length=128, required=True, unique=True)
    status = db.StringField(max_length=64, default='dev', choices=('dev', 'stage', 'production'))
    tags= db.ListField(db.StringField(max_length=128))
    content_blocks = db.ListField(db.ReferenceField('Content_block'))

    course=db.ReferenceField('Course')

    def assign_numbers_to_content_blocks(self):
        definition_counter=0
        problem_counter=0
        for content_block in self.content_blocks:
            if not getattr(content_block,'type_',None):
                print self.title
                print self.content_blocks
                continue
            if content_block.type_=='problem': #then set the number of this problem
                problem_counter+=1
                content_block.number_in_problem_set= problem_counter
                content_block.save()
            if content_block.type_=='definition': #then set the number of this definition
                definition_counter+=1
                content_block .number_in_problem_set= definition_counter
                content_block.save()
        return self


#collection for comments
class Comment(db.Document):
    text = db.StringField(required=True)
    date = db.DateTimeField(default=datetime.datetime.now)
    author= db.ReferenceField('User')

    def save(self, *args, **kwargs):
        super(Comment, self).save(*args, **kwargs)

    meta = {'allow_inheritance': True}

class CommentToSolution(Comment):    
    parent_solution = db.ReferenceField('Solution')
    type_ = db.StringField(max_length=64, default='comment_to_solution', choices=('comment_to_solution', 'comment_to_content_block', 'feedback'))

class CommentToContent_block(Comment): 
    parent_content_block = db.ReferenceField('Content_block')
    type_ = db.StringField(max_length=64, default='comment_to_content_block', choices=('comment_to_solution', 'comment_to_content_block', 'feedback'))


# mb change this to email to sendgrid!
class CommentFeedback(Comment):
    author_email=db.StringField()
    where_feedback = db.StringField()
    type_ = db.StringField(max_length=64, default='feedback', choices=('comment_to_solution', 'comment_to_content_block', 'feedback'))


#collection for solutions
class Solution(Comment):
    text = db.StringField(required=False)
    answer = db.StringField()
    image_url = db.StringField()
    language = db.StringField(max_length=256, default='rus')
    status = db.StringField(max_length=64, default='not_checked', choices=('checked_correct', 'checked_incorrect', 'not_checked'))

    problem = db.ReferenceField('Content_block')
    problem_set = db.ReferenceField('Problem_set')
    discussion=db.ListField(db.ReferenceField('Comment'))

    downvotes=db.IntField(default=0)
    upvotes=db.IntField(default=0)
    users_upvoted=db.ListField(db.ReferenceField('User'))
    users_downvoted=db.ListField(db.ReferenceField('User'))


# collection for subscribed users
class Subscribed_user(db.Document):
    email = db.StringField(required=True, unique=True, max_length=256)
    date = db.DateTimeField(default=datetime.datetime.now) 



# "deleting rules" see here:
# http://docs.mongoengine.org/guide/defining-documents.html#dealing-with-deletion-of-referred-documents
# and here (API page) http://docs.mongoengine.org/en/latest/apireference.html#mongoengine.fields.ReferenceField

# these deleting rules dont quite work, 
# because the reference is to problems,
# and people delete usually solutions
Content_block.register_delete_rule(User,'problems_solved', PULL)
Content_block.register_delete_rule(User,'problems_can_vote', PULL)
Content_block.register_delete_rule(User,'problems_solution_written',PULL)
Content_block.register_delete_rule(User,'problems_can_see_other_solutions',PULL)

Content_block.register_delete_rule(Solution,'problem', NULLIFY)

Problem_set.register_delete_rule(Content_block,'problem_set',NULLIFY)
Problem_set.register_delete_rule(Solution,'problem_set',NULLIFY)
Problem_set.register_delete_rule(Course,'problem_sets',PULL)

Course.register_delete_rule(Problem_set,'course',NULLIFY)

User.register_delete_rule(Content_block,'author',NULLIFY)
User.register_delete_rule(Comment,'author',NULLIFY)
User.register_delete_rule(Solution,'author',NULLIFY)
User.register_delete_rule(Solution,'users_upvoted',PULL)
User.register_delete_rule(Solution,'users_downvoted',PULL)

Solution.register_delete_rule(Content_block,'solutions',PULL)
Solution.register_delete_rule(CommentToSolution,'parent_solution',NULLIFY)

Content_block.register_delete_rule(Problem_set,'content_blocks',PULL)
Content_block.register_delete_rule(CommentToContent_block,'parent_content_block',NULLIFY)

Comment.register_delete_rule(Content_block,'general_discussion',PULL)
Comment.register_delete_rule(Solution,'discussion',PULL)