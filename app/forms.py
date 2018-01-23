from flask_wtf import FlaskForm # Import 'what the forms'
from wtforms import StringField, BooleanField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError, Email, EqualTo
from app.models import User

# Build a class with two fields, StringField and BooleanField
class LoginForm(FlaskForm):
    login_id = StringField('login_id', validators = [DataRequired()]) # This is a validator, a function that'll check if data is in the field
    email = StringField('email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default = False)
    submit = SubmitField('Sign In')

class EditForm(FlaskForm):
    nickname = StringField('nickname', validators = [DataRequired()])
    about_me = TextAreaField('about_me', validators = [Length(min = 0, max = 140)])

    def __init__(self, original_nickname,  *arg, **kwargs):
        FlaskForm.__init__(self, *arg, **kwargs)
        self.original_nickname = original_nickname

    def validate(self): # Sees if a nickname changed or not. If not, accept it. If it did, ensure it is not already in existance.
        if not FlaskForm.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user != None: # If anything is returned, then it must already be in use
            self.nickname.errors.append('This nickname is already in use. Please choose another.')
            return False
        return 
    
# A for used to register users
class RegistrationForm(FlaskForm):
    login_id = StringField('Username', validators = [DataRequired()]) # This is a validator, a function that'll check if data is in the field
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[EqualTo('password'), DataRequired()])
    submit = SubmitField('Register')

    def validate_login_id(self, login_id):
        user = User.query.filter_by(nickname=login_id.data).first()
        if user is not None:
            raise ValidationError('That username is already in use. Please use a different username.')
    
    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email is not None:
            raise ValidationError('That email is already in use. Please use a different email.')

# Form to make a post
class PostForm(FlaskForm):
    post = StringField('post', validators=[DataRequired()], description='Say something...')
    