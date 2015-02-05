from flask.ext.wtf import Form
from wtforms import StringField, DecimalField
from wtforms.validators import DataRequired

class InputForm(Form):
    address = StringField('openid', validators=[DataRequired()])
