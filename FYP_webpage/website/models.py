from .import db
from flask_login import UserMixin
from sqlalchemy.sql import func



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    role = db.Column(db.String(10))
    requests = db.relationship('Request')

class Shoe_stocks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    x1 = db.Column(db.Float)
    y1 = db.Column(db.Float)
    x2 = db.Column(db.Float)
    y2 = db.Column(db.Float)
    item_number = db.Column(db.Integer)
    row = db.Column(db.Integer)
    brand = db.Column(db.String(2))
    model = db.Column(db.Integer)
    size = db.Column(db.Integer)
    shoe_number = db.Column(db.Integer)


class Brand(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    brand = db.Column(db.String(100))
    models = db.relationship('Model')
    records = db.relationship('Stock_in_Record')
    requests = db.relationship('Request')

class Model(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    model_name = db.Column(db.String(1000))
    model_number = db.Column(db.Integer)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    records = db.relationship('Stock_in_Record')
    requests = db.relationship('Request')


class Stock_in_Record(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    size = db.Column(db.Integer)
    amount = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), default=func.now())

class Request(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    model_id = db.Column(db.Integer, db.ForeignKey('model.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    gender = db.Column(db.String(10))
    size = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    image_data = db.Column(db.LargeBinary)
    status = db.Column(db.String(10))
    

