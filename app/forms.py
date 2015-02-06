from flask.ext.wtf import Form
from wtforms import StringField, DecimalField, RadioField
from wtforms.validators import DataRequired

class InputForm(Form):
    address = StringField('address', validators=[DataRequired()])
    distance = DecimalField('distance', validators=[DataRequired()])
    units = RadioField('units', choices=[('mi', 'miles'), ('km', 'km')])
