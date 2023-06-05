from flask import Flask,jsonify, request
from db import db
import json
from flask_cors import CORS, cross_origin

#----Práctica 3------ AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import Crypto
###para los logs
from datetime import datetime

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

args_json = json.load(open("args.json"))
#Obtengo la infor del archivo args.json
SERVIDOR_IP = args_json['db'][0]['SERVIDOR_IP']
USUARIO = args_json['db'][0]['USUARIO']
CONTRASENYA = args_json['db'][0]['CONTRASENYA']
BASE_DE_DATOS = args_json['db'][0]['BASE_DE_DATOS']

# EL POST ES PARA AÑADIR
@app.route('/jugador', methods= ['POST'])
@cross_origin()
def addJugador():
    ##AUDITORIA
    fichero = open("LOGS.txt", "a")
    date = datetime.now()
    ip = request.remote_addr
    ###########

    aes_key_temporal = bytes(eval(request.json.split("|&|")[1]))
    datos = eval(api_desencriptar(aes_key_temporal , request.json.split("|&|")[0]))

    conexion_db = db()
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):
        if len(conexion_db.getJugador(datos['alias'])) > 0: # si el jugador con ese alias existe
            ##AUDITORIA
            fichero.write(str(date) + " | " + str(ip) + " | ERROR | JUGADOR YA EXISTE "+'\n')
            fichero.close()
            ###########
            return f"{api_encriptar(aes_key_temporal,'ERROR: Este jugador ya existe.')}"
        else:
            if conexion_db.insertar_Jugador(datos['alias'], datos['password'], datos['nivel'], datos['ef'], datos['ec'], datos['posicion']):
                ##AUDITORIA
                fichero.write(str(date) + " | " + str(ip) + " | JUGADOR CREADO "+'\n')
                fichero.close()
                ###########
                return f"{api_encriptar(aes_key_temporal,'Jugador creado.')}"
            else:
                ##AUDITORIA
                fichero.write(str(date) + " | " + str(ip) + " | ERROR | JUGADOR NO CREADO "+'\n')
                fichero.close()
                ###########
                return f"{api_encriptar(aes_key_temporal,'ERROR: Jugador no creado.')}"
    else:
        print("No se ha podido establecer comunicación con la base de datos en insertar jugador.")
        return f"{api_encriptar(aes_key_temporal,'Error no hay conexión con la DB.')}"

# EL PUT ES PARA MODIFICAR
@app.route('/jugador', methods = ['PUT'])
@cross_origin()
def editJugadorPassword():
        ##AUDITORIA
        fichero = open("LOGS.txt", "a")
        date = datetime.now()
        ip = request.remote_addr
        ###########

        aes_key_temporal = bytes(eval(request.json.split("|&|")[1]))
        datos = eval(api_desencriptar(aes_key_temporal , request.json.split("|&|")[0]))
    
        conexion_db = db() 
        if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):

            if len(conexion_db.getJugador(datos['alias'])) > 0: # si el jugador con ese alias existe
                
                if conexion_db.modJugador_Password(datos["alias"],datos["password"]):
                    ##AUDITORIA
                    fichero.write(str(date) + " | " + str(ip) + " | JUGADOR MODIFICADO "+'\n')
                    fichero.close()
                    ###########
                    return f"{api_encriptar(aes_key_temporal,'Jugador modificado.')}"

                else:
                    ##AUDITORIA
                    fichero.write(str(date) + " | " + str(ip) + " | ERROR | JUGADOR NO MODIFICADO "+'\n')
                    fichero.close()
                    ###########
                    return f"{api_encriptar(aes_key_temporal,'Jugador no modificado.')}"
            else:
                ##AUDITORIA
                fichero.write(str(date) + " | " + str(ip) + " | ERROR | JUGADOR NO EXISTE "+'\n')
                fichero.close()
                ###########
                return f"{api_encriptar(aes_key_temporal,'ERROR: jugador no existe.')}"
        else:
            print("No se ha podido establecer comunicación con la base de datos en modificar jugador.")
            return f"{api_encriptar(aes_key_temporal,'Error no hay conexión con la DB.')}"


def api_encriptar(key,mensaje) -> str:
    msg = bytes(str(mensaje).encode())

    cipher = AES.new(key,AES.MODE_CBC)
    mensaje_encriptado = cipher.encrypt(pad(msg, AES.block_size))

    return str(list(cipher.iv)) + "|@|" + str(list(mensaje_encriptado))

def api_desencriptar(key,mensaje) -> str:
    iv = bytes(eval(mensaje.split("|@|")[0].encode()))
    mensaje_encriptado = bytes(eval(mensaje.split("|@|")[1]))

    cipher = AES.new(key,AES.MODE_CBC, iv = iv)
    return unpad(cipher.decrypt(mensaje_encriptado), AES.block_size).decode() #recibo bytes

if __name__ == '__main__':
    app.run(debug=True, port=args_json['API_Registry'][0]['puerto'], host=args_json['API_Registry'][0]['ip'], ssl_context=('Claves_SSL/cert.pem','Claves_SSL/key.pem'))