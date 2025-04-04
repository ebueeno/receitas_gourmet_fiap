from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from flasgger import Swagger
import requests
from bs4 import BeautifulSoup
import config
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_acess_token,
    jwt_required, get_jwt_identity
)

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


class Receipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    time_minutes = db.Column(db.Integer, nullable=False)


swagger = Swagger(app)
auth = HTTPBasicAuth()


@app.route('/')
def home():
    return "Hello, flask"


if __name__ == '__main__':
    app.run(debug=True, port=5001)
    # with app.app_context():
    #     db.create_all()
    #     print("Banco de dados criado!")
