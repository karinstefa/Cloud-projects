# %%
from datetime import datetime
from flask import Flask, session, request, jsonify, escape
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_cors import CORS
import socket
import os
from dotenv import load_dotenv
import requests
import json
from botocore.config import Config
import base64
import uuid
import boto3
from boto3.dynamodb.conditions import Key
import redis

# %%
app = Flask(__name__)
app.secret_key = "123456abcd"
CORS(app)

# %% Variables de entorno
load_dotenv()

# variables
URL_API_SEND_FILE = os.getenv('URL_API_SEND_FILE')
# %%
ip_add = socket.gethostbyname(socket.gethostname())

# %% Variables de entorno
host = os.getenv('RDS_HOST')
port = os.getenv('RDS_PORT')
user = os.getenv('RDS_USER')
password = os.getenv('RDS_PASSWORD')
database = os.getenv('RDS_DB')
region_name = os.getenv('REGION_NAME')
bucket_name = os.getenv('BUCKET_NAME')
front_url = os.getenv('FRONT_URL')
redis_url = os.getenv('REDIS_URL')
# Inicilizacion de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:cloud1234@database-2.cnjddgnl0ynw.us-east-1.rds.amazonaws.com:5432/db_concursos"

# base de datos
db = SQLAlchemy(app)
ma = Marshmallow(app)

dynamodb = boto3.resource('dynamodb', region_name = region_name)

my_config = Config(region_name=region_name)

# %% Definicion de conexion a s3
s3 = boto3.client('s3')
s31 = boto3.resource('s3')
# %% redis elasticache
store = redis.Redis.from_url(redis_url)
# Crear Clases y esquemas Administrador
class Administradores(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombres = db.Column(db.String(50))
    apellidos = db.Column(db.String(50))
    correo = db.Column(db.String(50))
    password = db.Column(db.String(255))


class Administrador_Schema(ma.Schema):
    class Meta:
        fields = ("id", "nombres", "apellidos", "correo", "password")


administrador_schema = Administrador_Schema()
administradores_schema = Administrador_Schema(many=True)

# Crear Clases y esquemas Concursos


class Concursos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_admin = db.Column(db.Integer)
    nombre = db.Column(db.String(50))
    path_banner = db.Column(db.String(500))
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    valor_premio = db.Column(db.String(20))
    guion = db.Column(db.String(500))   # Validar max 500 aracteres en el front
    recomendaciones = db.Column(db.String(500))  # Validar en el front
    url = db.Column(db.String(250))


class Concursos_Schema(ma.Schema):
    class Meta:
        fields = ("id", "id_admin", "nombre", "path_banner", "fecha_inicio",
                  "fecha_fin", "valor_premio", "guion", "recomendaciones", "url")


concurso_schema = Concursos_Schema()
concursos_schema = Concursos_Schema(many=True)

# Crear Clases y esquemas Voces


class Voces(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_concurso = db.Column(db.Integer)
    nombres = db.Column(db.String(50))
    apellidos = db.Column(db.String(50))
    correo = db.Column(db.String(50))
    path_original = db.Column(db.String(500))
    path_convertido = db.Column(db.String(500))
    # Validar en el front max 500 caracteres
    observaciones = db.Column(db.String(500))
    fecha_creacion = db.Column(db.Date)
    estado = db.Column(db.Integer)


class Voces_Schema(ma.Schema):
    class Meta:
        fields = ("id", "id_concurso", "nombres", "apellidos", "correo", "path_original",
                  "path_convertido", "observaciones", "fecha_creacion", "estado")


voz_schema = Voces_Schema()
voces_schema = Voces_Schema(many=True)

# API----------------------------------------------------------------------------------------------------------------------------------------
# creacion de Api Flask
api = Api(app)

# Acciones GET/POST/PUT/DELETE Administrador


class RegistrarAdministrador(Resource):
    # Insertar Administrador
    def post(self):
        nuevo_administrador = Administradores(
            nombres=request.json['nombres'],
            apellidos=request.json['apellidos'],
            correo=request.json['correo'],
            password=request.json['password']
        )
        db.session.add(nuevo_administrador)
        db.session.commit()
        admins = Administradores.query.filter_by(
            correo=request.json['correo']).all()
        for admin in admins:
            if admin.password == request.json['password']:
                return {'message': 'Administrador creado exitosamente.', 'id': admin.id}


class ValidarAdministrador(Resource):
    def post(self):
        if 'correo' in request.json:
            if 'password' in request.json:
                admins = Administradores.query.filter_by(
                    correo=request.json['correo']).all()
                for admin in admins:
                    if admin.password == request.json['password']:
                        session['correo'] = request.json['correo']
                        correo = escape(session['correo'])
                        visits = store.hincrby(correo, 'visits', 1)
                        return {'success': 'true', 'id': admin.id}
        return {'success': 'false'}

# Acciones GET/POST/PUT/DELETE Concursos


class TodosLosConcursos(Resource):
    def get(self):
        table = dynamodb.Table('concurso')
        response = table.query(
            KeyConditionExpression=Key('pk').eq('concurso#concurso')
        )
        concursos = [row['info'] for row in response['Items']]
        return concursos_schema.dump(concursos)

    def post(self):
        nom_img = request.json['nombre'].replace(" ", "-")
        [tipo, archivo] = request.json['path_banner'].split(',')
        ext= tipo.split(';')[0].split('/')[-1]

        try:
            print('try')
            msg = base64.b64decode(archivo)
            s3.put_object(Key=f"files/imagen/{nom_img}.{ext}", Bucket=bucket_name, Body=msg)
        except Exception as e:
            print(str(e))
        id = uuid.uuid1()
        id_admin = request.json['id_admin']
        row = {'pk': 'concurso#concurso',
               'sk': f'{id_admin}_{id}',
               'info': {'id': f'{id_admin}_{id}',
                        'id_admin': id_admin,
                        'nombre': request.json['nombre'],
                        'path_banner': f"files/imagen/{nom_img}.{ext}",
                        'fecha_inicio': request.json['fecha_inicio'],
                        'fecha_fin': request.json['fecha_fin'],
                        'valor_premio': str(request.json['valor_premio']),
                        'guion': request.json['guion'],
                        'recomendacion': request.json['recomendaciones'],
                        'url': request.json['url']}
               }
        dynamodb.Table('concurso').put_item(Item=row)
        return {
            'message': 'Concurso creado exitosamente.',
            'id': f'{id_admin}_{id}'
        }

class getConcursoID(Resource):
    def get(self, id_concurso):
        table = dynamodb.Table('concurso')
        response = table.query(
            KeyConditionExpression=Key('pk').eq(
                'concurso#concurso') & Key('sk').eq(id_concurso)
        )
        concurso = response['Items'][0]
        ext = concurso['info']['path_banner'].split('.')[-1]
        #Download object to the file    
        s31.Bucket(bucket_name).download_file(concurso['info']['path_banner'],f'tmp/Im_{id_concurso}.{ext}')
        img_64 = ''
        with open(f'tmp/Im_{id_concurso}.{ext}', "rb") as image_file:
            img_64 = base64.b64encode(image_file.read())
        concurso['info'].update(
            {
                'url': f"{front_url}/frontend/concursos.html?id={concurso['info']['id']}&concurso={concurso['info']['url']}"
                }
            )
        concurso['info'].update({'path_banner': f'data:image/{ext};base64,'+img_64.decode('utf-8')})
        os.remove(f'tmp/Im_{id_concurso}.{ext}')
        return concurso_schema.dump(concurso['info'])
        # return concurso_schema.dump(concurso)


class UnConcurso(Resource):
    def get(self, id_concurso):
        table = dynamodb.Table('concurso')
        response = table.query(
            KeyConditionExpression=Key('pk').eq(
                'concurso#concurso') & Key('sk').begins_with(id_concurso)
        )
        concurso = [row['info'] for row in response['Items']]
        return concursos_schema.dump(concurso)

    def put(self, id_concurso):
        # VALIDAR EL REQUEST QUE TRAE EL FRONT, ES DECIR VER SI TRAE CAMPOS VACIOS
        table = dynamodb.Table('concurso')
        response = table.query(
            KeyConditionExpression=Key('pk').eq(
                'concurso#concurso') & Key('sk').eq(id_concurso)
        )
        if response['Items']:
            concurso = response['Items'][0]['info']
            concurso.update(request.json)
            table.update_item(
                Key={'pk': 'concurso#concurso', 'sk': id_concurso},
                AttributeUpdates={
                    'info': {
                        "Action": "PUT",
                        'Value': concurso
                    }
                }
            )
            return {'message': 'El concurso se edito correctamente'}
        return {'message': 'El concurso no existe'}

    def delete(self, id_concurso):
        table = dynamodb.Table('concurso')
        table.delete_item(Key={'pk': 'concurso#concurso', 'sk': id_concurso})
        return 'Se borro exitosamente el concurso', 204
# Acciones GET/POST/PUT/DELETE Voces


class TodosLasVoces(Resource):
    def get(self):
        table = dynamodb.Table('voz')
        response = table.query(
            KeyConditionExpression=Key('pk').eq('voz#voz')
        )
        voces = [row['info'] for row in response['Items']]
        return voces_schema.dump(voces)

    def post(self):
        id = uuid.uuid1()
        [tipo, archivo] = request.json['archivo'].split(',')
        nom_voz = request.json['nombres'].replace(
            ' ', '_')+str(datetime.now().microsecond)
        ext = tipo.split(';')[0].split('/')[-1]
        id_concurso = request.json['id_concurso']
        row = {'pk': 'voz#voz',
               'sk': f'{id_concurso}_{id}',
               'info': {'id': f'{id_concurso}_{id}',
                        'id_concurso': id_concurso,
                        'nombres': request.json['nombres'],
                        'apellidos': request.json['apellidos'],
                        'correo': request.json['correo'],
                        'observaciones': request.json['observaciones'],
                        'fecha_creacion': str(datetime.now()),
                        'estado': '0',
                        'path_original': f'files/voz/{nom_voz}.{ext}',
                        'path_convertido': ''
                        }
               }
        if  ext == "mp3":
            row['info'].update({'path_convertido': f'files/voz/{nom_voz}.{ext}'})
            row['info'].update({'estado': '1'})
        
        dynamodb.Table('voz').put_item(Item=row)
        try:
            print('try')
            msg = base64.b64decode(archivo)
            s3.put_object(Key=f"files/voz/{nom_voz}.{ext}", Bucket=bucket_name, Body=msg)
            # ext = tipo.split(';')[0].split('/')[-1]
            # wav_file = open(f"/files/voz/{nom_voz}.{ext}", "wb")
            # decode_string = base64.b64decode(archivo)
            # wav_file.write(decode_string)
        except Exception as e:
            print(str(e))
        if row['info']['estado'] == '0':
            url = URL_API_SEND_FILE
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                url,
                data=json.dumps(
                    {
                        'file_name': f"{nom_voz}.{ext}",
                        'file_path': f"files/voz/{nom_voz}.{ext}",
                        'id_voz': row['info']['id'],
                        'correo': request.json['correo']
                    }),
                headers = headers)
            if response.status_code == 200:
                return {
                    'message': 'Voz creada exitosamente',
                    'id_voz': f'{id_concurso}_{id}'
                }
            else:
                return {'message': 'No se pudo crear la voz'}
        return {
            'message': 'Voz creada exitosamente.',
            'id_voz': f'{id_concurso}_{id}'
        }


class UnaVoz(Resource):
    def get(self, id_voz):
        table = dynamodb.Table('voz')
        response = table.query(
            KeyConditionExpression=Key('pk').eq(
                'voz#voz') & Key('sk').eq(id_voz)
        )
        if response['Items']:
            voz = response['Items'][0]['info']
            if (voz['estado'] == '1'):
                [name, ext] = voz['path_original'].split('.')
                # voz_64=''
                # with open(voz.path_original, "rb") as voz_file:
                #     voz_64 = base64.b64encode(voz_file.read())
                # voz.path_banner = f'data:audio/{ext};base64,'+voz_64.decode('utf-8')
            return voz_schema.dump(voz)
        return {'message': 'ID VOZ No existe'}

    def put(self, id_voz):
        # VALIDAR EL REQUEST QUE TRAE EL FRONT, ES DECIR VER SI TRAE CAMPOS VACIOS
        table = dynamodb.Table('voz')
        response = table.query(
            KeyConditionExpression=Key('pk').eq(
                'voz#voz') & Key('sk').eq(id_voz)
        )
        if response['Items']:
            voz = response['Items'][0]['info']
            voz.update(request.json)
            table.update_item(
                Key={'pk': 'voz#voz', 'sk': id_voz},
                AttributeUpdates={
                    'info': {
                        "Action": "PUT",
                        'Value': voz
                    }
                }
            )
            return {'message': 'La Voz se edito correctamente'}
        return {'message': 'La Voz no existe'}

    def delete(self, id_voz):
        table = dynamodb.Table('voz')
        table.delete_item(Key={'pk': 'voz#voz', 'sk': id_voz})
        return 'Se borro exitosamente la voz', 204


# Endpoints Administrador
api.add_resource(RegistrarAdministrador, '/administrador')
api.add_resource(ValidarAdministrador, '/validar_administrador')

# Endpoints Concursos---
api.add_resource(TodosLosConcursos, '/concursos')
api.add_resource(UnConcurso, '/concursos/<string:id_concurso>')
api.add_resource(getConcursoID, '/concurso/<string:id_concurso>')

# Endpoint Voces
api.add_resource(TodosLasVoces, '/voces')
api.add_resource(UnaVoz, '/voces/<string:id_voz>')


@app.route("/")
def test():
    return 'hello'


@app.route("/voces/original/<id_voz>")
def obtenerVozOriginal(id_voz):
    voz = Voces.query.get_or_404(id_voz)
    voz_enviar = ''
    try:
        [name, ext] = voz.path_original.split('.')
        voz_64 = ''
        with open(voz.path_original, "rb") as voz_file:
            voz_64 = base64.b64encode(voz_file.read())
        voz_enviar = f'data:audio/{ext};base64,'+voz_64.decode('utf-8')
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })
    print('Voice prepared')
    return jsonify({
        'success': True,
        'archivo': voz_enviar
    })


@app.route("/voces/convertido/<id_voz>")
def obtenerVozConvertido(id_voz):
    voz = Voces.query.get_or_404(id_voz)
    voz_enviar = ''
    try:
        if (voz.estado == 1):
            [name, ext] = voz.path_convertido.split('.')
            voz_64 = ''
            with open(voz.path_convertido, "rb") as voz_file:
                voz_64 = base64.b64encode(voz_file.read())
            voz_enviar = f'data:audio/{ext};base64,'+voz_64.decode('utf-8')
        else:
            return jsonify({
                'success': False,
                'message': 'Audio no convertido'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })
    print('Voice prepared')
    return jsonify({
        'success': True,
        'archivo': voz_enviar
    })


@app.route('/test_api_send_file', methods=['POST'])
def send_file():
    if request.method == 'POST':
        data = request.get_json()
        url = URL_API_SEND_FILE
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url,
                                 data=json.dumps(data),
                                 headers=headers)
        print(response.json())
        if response.status_code == 200:
            return response.json()

    else:
        print('POST Error 405 Method Not Allowed')
        return ({'Sucess': 'False'})


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)

# %%
