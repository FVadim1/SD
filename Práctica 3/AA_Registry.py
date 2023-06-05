from email import message
import socket
import threading
import json
import sys
from db import db

#----Práctica 3------ AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import Crypto
import requests
import traceback

args_json = json.load(open("args.json")) #cargo el archivo de args.json
#Obtengo la infor del archivo args.json
SERVIDOR_IP = args_json['db'][0]['SERVIDOR_IP']
USUARIO = args_json['db'][0]['USUARIO']
CONTRASENYA = args_json['db'][0]['CONTRASENYA']
BASE_DE_DATOS = args_json['db'][0]['BASE_DE_DATOS']


puerto_escucha = args_json['AA_Registry'][0]['puerto_escucha']
ip = args_json['AA_Registry'][0]['ip']
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Metodo que se asignará a cada cliente que entre en conexión con este servidor y por donde enviará info
def handle_player(conn, addr):
    print(f"[NUEVA CONEXION] {addr} connected.")

    aes_key_temporal = b""
    while True:
        
        msg_length = conn.recv(64).decode('utf-8')
        
        if msg_length:
            
            #print()
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode('utf-8')
            
            if "|&|" in msg: #aquí entra la primera vez
                aes_key_temporal = bytes(eval(msg.split("|&|")[1]))
                msg_desencriptado = socket_desencriptar(aes_key_temporal , msg.split("|&|")[0])
            else: #aquí entra para del desconectar que le menda el player
                msg_desencriptado = socket_desencriptar(aes_key_temporal,msg)

            print(f"  He recibido del cliente [{addr}] el mensaje: {msg_desencriptado}")

             #Cliente se desconecta
            if msg_desencriptado == "Desconectar":
                break
            else:
                mensaje = msg_desencriptado.split("@")
                op = mensaje[0]
                #print(f"DEBUG_mensaje: [{mensaje}]")
                datos = json.loads(mensaje[1])
                
                if op == "crear_perfil" or op == "editar_perfil":
                        
                    #ME CONECTO A LA BASE DE DATOS
                    conexion_db = db()
                    
                    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):
                        existe = True

                        lista = conexion_db.logeo2(datos["alias"])       
                        if(len(lista) == 0):      
                            existe = False  

                        #OPERACIONES   
                        if op == "crear_perfil" and not existe:
                            if conexion_db.insertar_Jugador(datos["alias"],datos["password"],datos["nivel"],datos["ef"],datos["ec"],datos["posicion"]):                   
                                conn.send(f"{socket_encriptar(aes_key_temporal,'Jugador creado.')}".encode('utf-8'))
                            else:
                                conn.send(f"{socket_encriptar(aes_key_temporal,'ERROR: Jugador no creado.')}".encode('utf-8'))
                        
                        if op == "crear_perfil" and existe:
                            conn.send(f"{socket_encriptar(aes_key_temporal,'ERROR: Este jugador ya existe.')}".encode('utf-8'))
                                  
                        if op == "editar_perfil" and existe:
                            if conexion_db.modJugador_Password(datos["alias"],datos["password"]):    
                                conn.send(f"{socket_encriptar(aes_key_temporal,'Jugador modificado.')}".encode('utf-8'))
                            else:
                                conn.send(f"{socket_encriptar(aes_key_temporal,'Jugador no modificado.')}".encode('utf-8'))
 
                        if op == "editar_perfil" and not existe:
                            conn.send(f"{socket_encriptar(aes_key_temporal,'ERROR: jugador no existe.')}".encode('utf-8'))
                                           
                        ##CIERRO CONEXIÓN
                        conexion_db.closeCommunication()
                        
                    else:
                        print("No se ha podido conectar a la base de datos.")

            
            #Envio al cliente la confirmación de que he recibido su mensaje
            #conn.send(f"HOLA CLIENTE: He recibido tu mensaje: {msg} ".encode(FORMAT))
            
    conn.send(f"{socket_encriptar(aes_key_temporal,'Socket cerrado. Desconectado del servidor.')}".encode('utf-8'))
    conn.close()

def iniciar_ServidorRegistry():

    direccion = (ip, puerto_escucha)
    server.bind(direccion)
    server.listen()
    print(f"[AA_Registry] Servidor a la escucha en {direccion}")
    
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_player, args=(conn, addr)) #crea un thread para el cliente en cuestion (cada uno tiene el suyo)
        thread.start()


def socket_encriptar(key,mensaje) -> str:
    msg = bytes(str(mensaje).encode())

    cipher = AES.new(key,AES.MODE_CBC)
    mensaje_encriptado = cipher.encrypt(pad(msg, AES.block_size))

    return str(list(cipher.iv)) + "|@|" + str(list(mensaje_encriptado))

def socket_desencriptar(key,mensaje) -> str:
    iv = bytes(eval(mensaje.split("|@|")[0].encode()))
    mensaje_encriptado = bytes(eval(mensaje.split("|@|")[1]))

    cipher = AES.new(key,AES.MODE_CBC, iv = iv)
    return unpad(cipher.decrypt(mensaje_encriptado), AES.block_size).decode() #recibo bytes
######################### MAIN ##########################
if __name__ == "__main__":
    try:
        iniciar_ServidorRegistry()
    except KeyboardInterrupt:
        print('\n ####### [AVISO: Ejecución del servidor AA_Registry interrumpida con CTRL+C] #######')
        sys.exit(0)
