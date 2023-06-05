from flask import Flask,jsonify, request
from mapa import Mapa
from db import db
import json
from sty import Style, RgbFg
from sty import fg, bg, ef, rs

from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


args_json = json.load(open("args.json"))

SERVIDOR_IP = args_json['db'][0]['SERVIDOR_IP']
USUARIO = args_json['db'][0]['USUARIO']
CONTRASENYA = args_json['db'][0]['CONTRASENYA']
BASE_DE_DATOS = args_json['db'][0]['BASE_DE_DATOS']

def getMapa_en_BaseDatos() -> list:
    ##ABRO CONEXION CON LA BASE DE DATOS
    m = []
    conexion_db = db()   
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):
        m = conexion_db.getMapa()
    else:
        print(bg.red + "ERROR: no se ha podido establecer comunicación con la DB en getMapa_en_BaseDatos()" + bg.rs)

    return m


@app.route("/mapa")
@cross_origin()
def mapaPartida():

    mapa = getMapa_en_BaseDatos()

    return jsonify(mapa)


def getJUGADORES_PARTIDA_ALIAS_en_BaseDatos() -> list:
    ##ABRO CONEXION CON LA BASE DE DATOS
    m = []
    conexion_db = db()   
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):
        m = conexion_db.get_JUGADORES_PARTIDA_ALIAS()
        m = [tuple(l) for l in m] #convierto lista de listas en lista de tuplas (requerido en algunos métodos)
    else:
        print("ERROR: no se ha podido establecer comunicación con la DB en getJUGADORES_PARTIDA_ALIAS_en_BaseDatos()")

    return m

@app.route("/jugadores")
@cross_origin()
def jugadoresPartida():
    return jsonify(getJUGADORES_PARTIDA_ALIAS_en_BaseDatos())


args_json = json.load(open("args.json"))


if __name__ == '__main__':
    app.run(debug=True, port=args_json['API_Engine'][0]['puerto'], host=args_json['API_Engine'][0]['ip'], ssl_context=('Claves_SSL/cert.pem','Claves_SSL/key.pem'))