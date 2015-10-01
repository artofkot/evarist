# -*- coding: utf-8 -*-
from mongoengine import *
import datetime


#collection for registered users
class Rights(EmbeddedDocument):
    is_moderator=BooleanField(default=False)
    is_checker =BooleanField(default=False)

class User(Document):
    date = DateTimeField(default=datetime.datetime.now)
    karma= IntField(default=1)
    rights = EmbeddedDocumentField('Rights', default=Rights())

    problems_solution_written=ListField(ReferenceField('Content_block'))
    problems_solved=ListField(ReferenceField('Content_block'))
    problems_can_see_other_solutions=ListField(ReferenceField('Content_block'))
    problems_can_vote=ListField(ReferenceField('Content_block'))

    def __unicode__(self):
        return self.username + '•'.decode('utf-8') + str(self.karma)
    

    meta = {'allow_inheritance': True}

class GplusUser(User):
    provider= StringField(default='gplus', max_length=64)
    gplus_id=StringField(unique=True, sparse=True)
    gplus_picture=StringField()
    gplus_email=StringField()
    gplus_name=StringField()

    # default=gplus_name,
    username = StringField()
    # default=gplus_email,
    email = StringField(required=True)


class EmailUser(User):
    provider= StringField(default='email')
    username = StringField(required=True, max_length=256)
    email = StringField(required=True, unique_with='provider', max_length=256)
    pw_hash = StringField()
    old_pw_hash = StringField()
    confirmed= BooleanField(default=False)

    


#collection for content blocks
class Content_block(Document):
    text = StringField()
    date = DateTimeField(default=datetime.datetime.now)
    tags= ListField(StringField(max_length=128))
    
    problem_set= ReferenceField('Problem_set')
    author= ReferenceField('User')
    general_discussion=ListField(ReferenceField('Comment'))
    number_in_problem_set=IntField()

    type_ = StringField(max_length=64, default='problem', choices=('problem', 'definition', 'general_content_block'))
    solutions=ListField(ReferenceField('Solution'))

    meta = {'allow_inheritance': True}
    old_id = StringField()

#collection of courses
class Course(Document):
    name=StringField(required=True, unique=True, max_length=1024)
    slug = StringField(max_length=128, required=True, unique=True)
    problem_sets=ListField(ReferenceField('Problem_set'))

#collection for problem sets
class Problem_set(Document):
    title = StringField(required=True, unique=True, max_length=1024)
    slug = StringField(max_length=128, required=True, unique=True)
    status = StringField(max_length=64, default='dev', choices=('dev', 'stage', 'production'))
    tags= ListField(StringField(max_length=128))
    content_blocks = ListField(ReferenceField('Content_block'))

    course=ReferenceField('Course')

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
class Comment(Document):
    text = StringField(required=True)
    date = DateTimeField(default=datetime.datetime.now)
    author= ReferenceField('User')

    def save(self, *args, **kwargs):
        super(Comment, self).save(*args, **kwargs)

    meta = {'allow_inheritance': True}

class CommentToSolution(Comment):    
    parent_solution = ReferenceField('Solution')
    type_ = StringField(max_length=64, default='comment_to_solution', choices=('comment_to_solution', 'comment_to_content_block', 'feedback'))

class CommentToContent_block(Comment): 
    parent_content_block = ReferenceField('Content_block')
    type_ = StringField(max_length=64, default='comment_to_content_block', choices=('comment_to_solution', 'comment_to_content_block', 'feedback'))


# mb change this to email to mandrill!
class CommentFeedback(Comment):
    author_email=StringField()
    where_feedback = StringField()
    type_ = StringField(max_length=64, default='feedback', choices=('comment_to_solution', 'comment_to_content_block', 'feedback'))


#collection for solutions
class Solution(Comment):
    text = StringField(required=False)
    answer = StringField()
    image_url = StringField()
    language = StringField(max_length=256, default='rus')
    status = StringField(max_length=64, default='not_checked', choices=('checked_correct', 'checked_incorrect', 'not_checked'))

    problem = ReferenceField('Content_block')
    problem_set = ReferenceField('Problem_set')
    discussion=ListField(ReferenceField('Comment'))

    downvotes=IntField(default=0)
    upvotes=IntField(default=0)
    users_upvoted=ListField(ReferenceField('User'))
    users_downvoted=ListField(ReferenceField('User'))


# collection for subscribed users
class Subscribed_user(Document):
    email = StringField(required=True, unique=True, max_length=256)
    date = DateTimeField(default=datetime.datetime.now) 



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









