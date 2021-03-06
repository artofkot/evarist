import re
from flask import flash, g, request, redirect, url_for
from flask_wtf import FlaskForm as Form
from wtforms.fields import TextField, PasswordField, BooleanField, FileField
from wtforms.validators import Required, Email, Regexp, ValidationError, EqualTo

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

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ))

def trigger_flash_error(form,endpoint,**kwargs):
    if request.method == 'POST' and not form.validate_on_submit():
        flash_errors(form)
        return redirect(url_for(endpoint,**kwargs))

class SolutionForm(Form):
    solution = TextField('solution')
    image = FileField('image')
    def validate(self):
        result=True
        if not Form.validate(self):
            return False
        if not (self.image.data or self.solution.data):
            return False
        return result

class EditSolutionForm(Form):
    use_old_image=BooleanField('use_old_image')
    edit_image = FileField('edit_image')
    edited_solution = TextField('edited_solution')
    delete_solution=BooleanField('delete_solution')
    def validate(self):
        result=True
        if not Form.validate(self):
            return False
        if not (self.edit_image.data or self.edited_solution.data):
            return False
        return result

class SignUpForm(Form):
    email = TextField('email', validators=[Required(), Email()])
    username = TextField('username', validators=[Required(), Regexp(USER_RE,message=u'Invalid username.')])
    confirm_password = PasswordField('confirm_password', validators=[Required()])
    password = PasswordField('password', validators=[Required(),EqualTo('confirm_password', message='passwords must match.')])

class SignInForm(Form):
    email = TextField('email', validators=[Required(message=u'Whats the email?'), Email()])
    password = PasswordField('password', validators=[Required(message=u'Whats the password?')])

class CommentForm(Form):
    text = TextField('text', validators=[Required()])

class EditCommentForm(Form):
    text = TextField('text', validators=[Required()])
    delete_comment=BooleanField('delete_comment')

class FeedbackToSolutionForm(Form):
    feedback_to_solution = TextField('feedback_to_solution', validators=[Required()])

class WebsiteFeedbackForm(Form):
    feedback = TextField('feedback', validators=[Required()])
    email = TextField('email',)

class VoteForm(Form):
    vote = TextField('vote', validators=[Required()])

class ProblemSetForm(Form):
    status= TextField('status')
    title = TextField('title', validators=[Required()])
    slug = TextField('slug', validators=[Required()])

class CourseForm(Form):
    name = TextField('name', validators=[Required()])
    slug = TextField('slug', validators=[Required()])


class EditCourseForm(Form):
    edit_name = TextField('edit_name', validators=[Required()])
    edit_slug = TextField('edit_slug', validators=[Required()])
    delete_course=BooleanField('delete_course')

class AddPsetForm(Form):
    pset_slug=TextField('pset_slug', validators=[Required()])
    place_of_pset=TextField('place_of_pset', validators=[Required()])

class ProblemSetDelete(Form):
    delete=BooleanField('delete', validators=[Required()])

class Content_blockForm(Form):
    text= TextField('text', validators=[Required()])
    type_=TextField('type_')
    place_of_content_block=TextField('place_of_content_block')

class EditContent_blockForm(Form):
    type_=TextField('type_')
    place_of_content_block=TextField('place_of_content_block')
    edit_text= TextField('edit_text', validators=[Required()])
    delete_content_block=BooleanField('delete_content_block')