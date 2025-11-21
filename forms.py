from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, ValidationError
import re

class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    nickname = StringField('Nickname', validators=[
        Length(max=50, message='Nickname must be less than 50 characters')
    ])
    
    address = TextAreaField('Address', validators=[
        DataRequired(),
        Length(min=10, max=500, message='Address must be between 10 and 500 characters')
    ])
    
    mobile_number = StringField('Mobile Number', validators=[
        DataRequired(),
        Length(min=10, max=15, message='Enter a valid mobile number')
    ])
    
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPEG and PNG images are allowed!')
    ])
    
    # Player role fields
    is_all_rounder = BooleanField('All-rounder')
    is_left_arm_bowler = BooleanField('Left-arm bowler')
    is_right_arm_bowler = BooleanField('Right-arm bowler')
    is_left_hand_batter = BooleanField('Left-hand batter')
    is_right_hand_batter = BooleanField('Right-hand batter')

    def validate_mobile_number(self, field):
        # Remove any spaces or special characters
        number = re.sub(r'[^0-9]', '', field.data)
        if not re.match(r'^[0-9]{10,15}$', number):
            raise ValidationError('Please enter a valid mobile number')
        field.data = number

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])