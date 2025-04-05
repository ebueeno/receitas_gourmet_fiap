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


@app.route('/recipes', methods=['POST'])
@jwt_required()
def create_recipe():
    """
    Cria uma nova receita
    ---
    Security:
        - BearerAuth: []
    parametros:
        - in: body
          name: body
          required: true
          schema:
            type: object
            properties:
                title:
                    type: string
                ingredients:
                    type: string
                time_minutes:
                    type: integer
    responses:
        201:
            description: Receita criada com sucesso
        401:
            description: Token não fornecido ou inválido
    """
    data = request.get_json()  # pega o corpo da requisição Json
    new_recipe = Receipe(  # aqui está criando um novo objeto da classe receipe com os dados que vieram da requisição
        title=data['title'],
        ingredients=data['ingredients'],
        time_minutes=data['time_minutes']
    )

    db.session.add(new_recipe)
    db.session.commit()
    return jsonify({'msg': 'Recipe created'}), 201


@app.route('/recipes', methods=['GET'])
def get_recipes():
    """
    Lista receitas com filtros opcionais.
    ---
    parameters:
      - name: ingredient
        in: query
        type: string
        required: false
        description: Filtro por ingrediente
      - name: max_time
        in: query
        type: integer
        required: false
        description: Tempo máximo de preparo (em minutos)
    responses:
      200:
        description: Lista de receitas filtrada
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              title:
                type: string
              ingredients:
                type: string
              time_minutes:
                type: integer
    """
    infredient = request.args.get('ingredient')
    # pega os parâmetros da URL (chamados query parameters). http://127.0.0.1:5001/recipes?ingredient=Feijão
    max_time = request.args.get('max_time', type=int)
    # a mesma coisa do que em cima

    # consulta sem filtros. Aqui você está preparando a busca das receitas.
    query = Receipe.query

    # Se o usuário mandou o filtro ingredient, fazemos um filtro usando LIKE (busca parcial, insensível a maiúsculas/minúsculas).
    if infredient:
        query = query.filter(Receipe.ingredients.ilike(f'%{infredient}%'))
    if max_time is not None:
        query = query.filter(Receipe.time_minutes <= max_time)

    receipes = query.all()
    # Aqui estamos:
    # Percorrendo todas as receitas retornadas da consulta.
    # Transformando em dicionários para cada receita.
    # Retornando como JSON para o cliente.
    return jsonify(
        [
            {
                "id": r.id,
                "title": r.title,
                "ingredients": r.ingredients,
                "time_minutes": r.time_minutes

            }
            for r in receipes
        ]

    )


@app.route('/recipes/<int:recipe_id>', methods=['PUT'])
@jwt_required()
def update_recipe(recipe_id):
    """
    Atualiza uma recita existente.
    ---
    Security:
      -BearerAuth: []
    parameters:
      - in: path
        name: recipe_id
        required: true
        type: integer
      - in: body
        name: body
        schema:
          type: object
          properties:
            title:
              type: string
            ingredients:
              type: string
            time_minutes:
              type: integer
    responses:
      200:
       descriprion: Receita atualizada
      404:
       descriprion: Receita não encontrada
      401:
       descriprion: Token não fornecido ou invalido
    """
    data = request.get_json()
    # Busca a receita com o ID informado. Se não encontrar, retorna erro 404.
    recipe = Receipe.query.get_or_404(recipe_id)

    if 'title' in data:
        recipe.title = data['title']
    if 'ingredients' in data:
        recipe.ingredients = data['ingredients']
    if 'time_minutes' in data:
        recipe.time_minutes = data['time_minutes']

    db.session.commit()
    return jsonify({'msg': 'Recipe updated'}), 200


@app.route('/recipes/<int:receipe_id>', methods=['DELETE'])
@jwt_required()
def delete_recipe(receipe_id):
    """
    Deleta uma recita existente.
    ---
    Security:
      -BearerAuth: []
    parameters:
      - in: path
        name: recipe_id
        required: true
        type: integer
      - in: body
        name: body
        schema:
          type: object
          properties:
            title:
              type: string
            ingredients:
              type: string
            time_minutes:
              type: integer
    responses:
      200:
       descriprion: Receita deletada
      404:
       descriprion: Receita não encontrada
      401:
       descriprion: Token não fornecido ou invalido
    """
    data = request.get_json()
    # Busca a receita com o ID informado. Se não encontrar, retorna erro 404.
    recipe = Receipe.query.get_or_404(receipe_id)
    db.session.delete(recipe)
    db.session.commit()
    return jsonify({'msg': 'registro exluido com sucesso'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)
    # with app.app_context():
    #     db.create_all()
    #     print("Banco de dados criado!")
