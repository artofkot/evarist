from flask.ext.wtf import Form
from wtforms.fields import TextField, PasswordField, BooleanField
from wtforms.validators import Required, Email




class ProblemSetForm(Form):
    title = TextField('title', validators=[Required()])
    slug = TextField('slug', validators=[Required()]) # validators=[Required()]



class ProblemSetDelete(Form):
    delete=BooleanField('delete', validators=[Required()])

class EntryForm(Form):
    title= TextField('title', validators=[Required()])
    text= TextField('text', validators=[Required()])

class EditEntryForm(Form):
    edit_title= TextField('edit_title', validators=[Required()])
    edit_text= TextField('edit_text', validators=[Required()])
    delete_entry=BooleanField('delete_entry')