import re
from flask.ext.wtf import Form
from wtforms.fields import TextField, PasswordField, BooleanField
from wtforms.validators import Required, Email, Regexp

#regexs for usernames and passwords and emails
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

# PASS_RE = re.compile(r"^.{3,20}$")
# def valid_password(password):
#     return password and PASS_RE.match(password)

# EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
# def valid_email(email):
#     return not email or EMAIL_RE.match(email)

class SolutionForm(Form):
    solution = TextField('solution', validators=[Required()])

class EditSolutionForm(Form):
    edited_solution = TextField('edited_solution', validators=[Required()])
    delete_solution=BooleanField('delete_solution')

class SignUpForm(Form):
    email = TextField('email', validators=[Required(), Email()])
    username = TextField('username', validators=[Required(), Regexp(USER_RE,message=u'Invalid username.')])
    confirm_password = PasswordField('confirm_password', validators=[Required()])
    password = PasswordField('password', validators=[Required()])

class SignInForm(Form):
    email = TextField('email', validators=[Required(message=u'Whats the email?'), Email()])
    password = PasswordField('password', validators=[Required(message=u'Whats the password?')])

class CommentForm(Form):
    text = TextField('text', validators=[Required()])

class FeedbackToSolutionForm(Form):
    feedback_to_solution = TextField('feedback_to_solution', validators=[Required()])

class WebsiteFeedbackForm(Form):
    feedback = TextField('feedback', validators=[Required()])
    email = TextField('email',)


class VoteForm(Form):
    vote = TextField('vote', validators=[Required()])

class ProblemSetForm(Form):
    title = TextField('title', validators=[Required()])
    slug = TextField('slug', validators=[Required()]) # validators=[Required()]

class ProblemSetDelete(Form):
    delete=BooleanField('delete', validators=[Required()])

class EntryForm(Form):
    title= TextField('title')
    text= TextField('text', validators=[Required()])
    entry_type=TextField('entry_type')
    entry_number=TextField('entry_number')

class EditEntryForm(Form):
    entry_type=TextField('entry_type')
    entry_number=TextField('entry_number')
    edit_title= TextField('edit_title')
    edit_text= TextField('edit_text', validators=[Required()])
    delete_entry=BooleanField('delete_entry')