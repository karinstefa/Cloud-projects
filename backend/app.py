from datetime import datetime
from flask import Flask
from flask import request
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow  
from flask_restful import Api, Resource
from flask_cors import CORS
from sqlalchemy import false, true

app = Flask(__name__)
CORS(app)

# Inicilizacion de base de datos

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://admin:123456@172.24.41.222:5432/project01"
# base de datos
db = SQLAlchemy(app)
ma = Marshmallow(app)


# Crear Clases y esquemas Administrador
class Administradores(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nombres = db.Column(db.String(50) )
    apellidos = db.Column(db.String(50) )
    correo = db.Column(db.String(50) )
    password = db.Column(db.String(255) )

class Administrador_Schema(ma.Schema):
    class Meta:
        fields = ("id", "nombres", "apellidos", "correo", "password")

administrador_schema = Administrador_Schema()
administradores_schema = Administrador_Schema(many = True)

# Crear Clases y esquemas Concursos
class Concursos(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    id_admin = db.Column(db.Integer)
    nombre = db.Column(db.String(50) )
    path_banner = db.Column(db.String(500) )
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    valor_premio = db.Column(db.String(20))
    guion = db.Column(db.String(500))   # Validar max 500 aracteres en el front
    recomendaciones = db.Column(db.String(500)) # Validar en el front
    url = db.Column(db.String(250))
class Concursos_Schema(ma.Schema):
    class Meta:
        fields = ("id","id_admin","nombre","path_banner","fecha_inicio","fecha_fin","valor_premio","guion","recomendaciones","url")

concurso_schema = Concursos_Schema()
concursos_schema = Concursos_Schema(many = True)

# Crear Clases y esquemas Voces
class Voces(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    id_concurso = db.Column(db.Integer)
    nombres = db.Column(db.String(50) )
    apellidos = db.Column(db.String(50) )
    correo = db.Column(db.String(50) )
    path_original = db.Column(db.String(500) )
    path_convertido = db.Column(db.String(500) )
    observaciones = db.Column(db.String(500)) # Validar en el front max 500 caracteres
    fecha_creacion = db.Column(db.Date)
    estado = db.Column(db.Integer)

class Voces_Schema(ma.Schema):
    class Meta:
        fields = ("id","id_concurso","nombres","apellidos","correo","path_original","path_convertido","observaciones","fecha_creacion","estado")

voz_schema = Voces_Schema()
voces_schema = Voces_Schema(many = True)

# API----------------------------------------------------------------------------------------------------------------------------------------
# creacion de Api Flask
api = Api(app)

# Acciones GET/POST/PUT/DELETE Administrador
class RegistrarAdministrador(Resource):
    # Insertar Administrador
    def post(self):
        nuevo_administrador = Administradores(
            nombres = request.json['nombres'],
            apellidos = request.json['apellidos'],
            correo = request.json['correo'],
            password = request.json['password']
        )
        db.session.add(nuevo_administrador)
        db.session.commit()
        admins = Administradores.query.filter_by(correo=request.json['correo']).all()
        for admin in admins:
            if admin.password == request.json['password']:
                return {'message':'Administrador creado exitosamente.','id':admin.id}



class ValidarAdministrador(Resource):
    def post(self):
        if 'correo' in request.json:
            if 'password' in request.json:
                admins = Administradores.query.filter_by(correo=request.json['correo']).all()
                for admin in admins:
                    if admin.password == request.json['password']:
                        return {'success':'true','id':admin.id}
        return {'success':'false'}

# Acciones GET/POST/PUT/DELETE Concursos

class TodosLosConcursos(Resource):
    def get(self):
        concursos = Concursos.query.all()        
        return concursos_schema.dump(concursos)
    def post(self):
        [tipo, archivo] = request.json['path_banner'].split(',')
        nom_img = request.json['nombre'].replace(" ","-")
        try:
            ext= tipo.split(';')[0].split('/')[-1]
            wav_file = open(f"/files/imagen/{nom_img}.{ext}", "wb")
            decode_string = base64.b64decode(archivo)
            wav_file.write(decode_string)
        except Exception as e:
            print(str(e))
        nuevo_concurso = Concursos(
                id_admin = request.json['id_admin'],
                nombre = request.json['nombre'],
                path_banner = f"/files/imagen/{nom_img}.{ext}",
                fecha_inicio = datetime.strptime(request.json['fecha_inicio'],"%d/%m/%Y"),
                fecha_fin = datetime.strptime(request.json['fecha_fin'],"%d/%m/%Y"),
                valor_premio = request.json['valor_premio'],
                guion = request.json['guion'],
                recomendaciones = request.json['recomendaciones'],
                url = request.json['url']
        )
        db.session.add(nuevo_concurso)
        db.session.commit()
        return {'message':'Concurso creado exitosamente.'}

class getConcursoID(Resource):
    def get(self,id_concurso):
        concurso = Concursos.query.get_or_404(id_concurso)
        [name, ext] = concurso.path_banner.split('.')
        img_64=''
        with open(concurso.path_banner, "rb") as image_file:
            img_64 = base64.b64encode(image_file.read())
        url = concurso.url
        concurso.url = f'http://172.24.41.218/frontend/concursos.html?id={concurso.id}&concurso={url}'

        concurso.path_banner = f'data:image/{ext};base64,'+img_64.decode('utf-8')
        return concurso_schema.dump(concurso)

class UnConcurso(Resource):
    def get(self,id_concurso):
        concurso = Concursos.query.filter_by(id_admin = id_concurso).all()
        return concursos_schema.dump(concurso)
    def put(self,id_concurso):
        concurso = Concursos.query.get_or_404(id_concurso)
        if 'id_admin' in request.json:
            concurso.id_admin = request.json['id_admin']
        if 'nombre' in request.json:
            concurso.nombre = request.json['nombre']
        if 'path_banner' in request.json:
            concurso.path_banner = request.json['path_banner']
        if 'fecha_inicio' in request.json:
            concurso.fecha_inicio = datetime.strptime(request.json['fecha_inicio'],"%d/%m/%Y"),
        if 'fecha_fin' in request.json:
            concurso.fecha_fin = datetime.strptime(request.json['fecha_fin'],"%d/%m/%Y"),
        if 'valor_premio' in request.json:
            concurso.valor_premio = request.json['valor_premio']
        if 'guion' in request.json:
            concurso.guion = request.json['guion']
        if 'recomendaciones' in request.json:
            concurso.recomendaciones = request.json['recomendaciones']
        if 'url' in request.json:
            concurso.url = request.json['url']
        db.session.commit()
        return {'message':'El concurso se edito correctamente'}
    def delete(self, id_concurso):
        concurso = Concursos.query.get_or_404(id_concurso)
        db.session.delete(concurso)
        db.session.commit()
        return 'Se borro exitosamente el concurso', 204

import base64


# Acciones GET/POST/PUT/DELETE Voces 
class TodosLasVoces(Resource):
    def get(self):
        voces = Voces.query.all()        
        return voces_schema.dump(voces)
    
    def post(self):
        nueva_voz = Voces(
            id_concurso = request.json['id_concurso'],
            nombres = request.json['nombres'],
            apellidos = request.json['apellidos'],
            correo = request.json['correo'],
            observaciones = request.json['observaciones'],
            fecha_creacion = datetime.now(),
            estado = 0 #se asegura que la voz no este procesada
        )

        [tipo, archivo] = request.json['archivo'].split(',')
        nom_voz = nueva_voz.nombres.replace(' ','_')+str(datetime.now().microsecond)
        try:
            ext = tipo.split(';')[0].split('/')[-1]
            wav_file = open(f"/files/voz/{nom_voz}.{ext}", "wb")
            decode_string = base64.b64decode(archivo)
            wav_file.write(decode_string)
        except Exception as e:
            print(str(e))
        nueva_voz.path_original = f"/files/voz/{nom_voz}.{ext}"
        db.session.add(nueva_voz)
        db.session.commit()
        return {'message':'Voz creada exitosamente.'}



class UnaVoz(Resource):
    def get(self,id_voz):
        voz = Voces.query.get_or_404(id_voz)
        if (voz.estado==1):
            [name, ext] = voz.path_original.split('.')
            voz_64=''
            with open(voz.path_original, "rb") as voz_file:
                voz_64 = base64.b64encode(voz_file.read())
            voz.path_banner = f'data:audio/{ext};base64,'+voz_64.decode('utf-8')
        return voz_schema.dump(voz)
    
    def put(self,id_voz):
        voz = Voces.query.get_or_404(id_voz)
        if 'id_concurso' in request.json:
            voz.id_concurso = request.json['id_concurso']
        if 'nombres' in request.json:
            voz.nombres = request.json['nombres']
        if 'apellidos' in request.json:
            voz.apellidos = request.json['apellidos']
        if 'correo' in request.json:
            voz.correo = request['correo']
        if 'path_original' in request.json:
            voz.path_original = request.json['path_original']
        if 'path_convertido' in request.json:
            voz.path_convertido = request.json['path_convertido']
        if 'observaciones' in request.json:
            voz.observaciones = request.json['observaciones']
        if 'fecha_creacion' in request.json:
            voz.fecha_creacion = request.json['fecha_creacion']
        if 'estado' in request.json:
            voz.estado = request.json['estado']
        db.session.commit()
        return {'message':'La voz se edito correctamente'}
    
    def delete(self, id_voz):
        voz = Concursos.query.get_or_404(id_voz)
        db.session.delete(voz)
        db.session.commit()
        return 'La voz se borro exitosamente', 204



# Endpoints Administrador
api.add_resource(RegistrarAdministrador, '/administrador')
api.add_resource(ValidarAdministrador, '/validar_administrador')

# Endpoints Concursos---
api.add_resource(TodosLosConcursos, '/concursos')
api.add_resource(UnConcurso,'/concursos/<int:id_concurso>')
api.add_resource(getConcursoID,'/concurso/<int:id_concurso>')

# Endpoint Voces
api.add_resource(TodosLasVoces, '/voces')
api.add_resource(UnaVoz,'/voces/<int:id_voz>')

@app.route("/voces/original/<id_voz>")
def obtenerVozOriginal(id_voz):
    voz = Voces.query.get_or_404(id_voz)
    voz_enviar = ''
    try:
        [name, ext] = voz.path_original.split('.')
        voz_64=''
        with open(voz.path_original, "rb") as voz_file:
            voz_64 = base64.b64encode(voz_file.read())
        voz_enviar = f'data:audio/{ext};base64,'+voz_64.decode('utf-8')
    except Exception as e:
        return jsonify({
            'success' : False,
            'message' : str(e)
            })        
    print('Voice prepared')    
    return jsonify({
        'success' : True,
        'archivo' : voz_enviar
        })

@app.route("/voces/convertido/<id_voz>")
def obtenerVozConvertido(id_voz):
    voz = Voces.query.get_or_404(id_voz)
    voz_enviar = ''
    try:
        if (voz.estado==1):
            [name, ext] = voz.path_convertido.split('.')
            voz_64=''
            with open(voz.path_convertido, "rb") as voz_file:
                voz_64 = base64.b64encode(voz_file.read())
            voz_enviar = f'data:audio/{ext};base64,'+voz_64.decode('utf-8')
        else:
            return jsonify({
                'success' : False,
                'message' : 'Audio no convertido'
            })
    except Exception as e:
        return jsonify({
            'success' : False,
            'message' : str(e)
            })        
    print('Voice prepared')    
    return jsonify({
        'success' : True,
        'archivo' : voz_enviar
        })


if __name__ == '__main__':
    app.run(debug=False,host="0.0.0.0", port=8080)
