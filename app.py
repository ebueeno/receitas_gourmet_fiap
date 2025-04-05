from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from flasgger import Swagger
import requests
from bs4 import BeautifulSoup
import config
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
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


@app.route("/register", methods=['POST'])
def registrer_user():
    """
    Registar um novo usuario
    ---
    parametros:
        - in: body
          name: body
          required: true
          schema:
            type: object
            properties:
                username:
                    type: string
                password:
                    type: string
    responses:
        201:
            description: Usuario criado com sucesso
        400:
            description: Usario já existe
    """

    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'User already exists'}), 400
    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'msg': 'user created'}), 201


@app.route("/login", methods=['POST'])
def login():
    """
    Fazer login do usuario e retornar um jwt
    ---
    parametros:
        - in: body
          name: body
          required: true
          schema:
            type: object
            properties:
                username:
                    type: string
                password:
                    type: string
    responses:
        201:
            description: Login bem sucedido, retorna JWT
        400:
            description: Credenciais inválidas
    """

    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and user.password == data['password']:
        # convert o ID em uma string
        token = create_access_token(identity=str(user.id))
        return jsonify({'access_token': token}), 200
    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # Retona o 'identity' usado na criação do token
    current_user_id = get_jwt_identity()
    return jsonify({'msg': f'Usuario com ID {current_user_id} acessou a rota protegida'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)
    # with app.app_context():
    #     db.create_all()
    #     print("Banco de dados criado!")
