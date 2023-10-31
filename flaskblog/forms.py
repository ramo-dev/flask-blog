from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, length, Email, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField("Username",
                            validators=[DataRequired(), length(min=2, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])

    password = PasswordField('password',
                              validators=[DataRequired()])

    confirm_password = password = PasswordField('confirm password',
                                validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])

    password = PasswordField('password',
                              validators=[DataRequired()])
    
    remember = BooleanField('Remember Me')

    submit = SubmitField('Login')