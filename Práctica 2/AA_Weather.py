###########-------NOTA: AA_Weather es in SERVIDOR socket que solo está para que AA_Engine(otro servidor) obtenga una ciudad random----------#########
import socket
import threading
import json
import sys
from db import db
import random

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

args_json = json.load(open("args.json")) #cargo el archivo de args.json
#Obtengo la infor del archivo args.json
SERVIDOR_IP = args_json['db'][0]['SERVIDOR_IP']
USUARIO = args_json['db'][0]['USUARIO']
CONTRASENYA = args_json['db'][0]['CONTRASENYA']
BASE_DE_DATOS = args_json['db'][0]['BASE_DE_DATOS']


args_json = json.load(open("args.json"))
puerto_escucha = args_json['AA_Weather'][0]['puerto_escucha']
ip = args_json['AA_Weather'][0]['ip']

def handle_AA_Engine(conn, addr):
    print(f"[Socket abierto] {addr} , AA_Engine se ha conectado.")

    while True:
        
        msg_length = conn.recv(64).decode('utf-8')
        
        if msg_length:
            
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode('utf-8')
            print(f" He recibido de AA_Engine [{addr}] el mensaje: {msg}")
            
            if msg == "Dame ciudad":
                
                ciudades = []
                
                #ME CONECTO A LA BASE DE DATOS
                conexion_db = db()
                if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):
        
                    #OPERACIONES
                    ciudades = conexion_db.getTabla("ciudades")
                    ##CIERRO CONEXIÓN
                    conexion_db.closeCommunication()
                
                if not len(ciudades):
                    print("ERROR: No hay ciudades en la base de datos")
                else:
                    ciudad_random = random.choice(ciudades)
                    print("Ciudad elegida de forma random: ", ciudad_random) 
                    conn.send(f"{ciudad_random}".encode('utf-8')) #envio a AA_Engine la ciudad elegido de forma random
            else:
                if msg == "Desconectar":
                    print("--------- AA_Engine se ha desconectado.----------")
                    break
                else:
                    conn.send(f"ERROR: No me has pedido una ciudad en el mensaje.".encode('utf-8'))
            
    conn.close()

def iniciar_ServidorWeather():
    
    direccion = (ip, puerto_escucha)
    server.bind(direccion)
    server.listen()
    print(f"[AA_Weather] Servidor a la escucha en {direccion}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_AA_Engine, args=(conn, addr)) #crea un thread para el cliente en cuestion (cada uno tiene el suyo)
        thread.start()


######################### MAIN ##########################
if __name__ == "__main__":
    try:
        iniciar_ServidorWeather()
    except KeyboardInterrupt:
        print('\n ####### [AVISO: Ejecución del servidor AA_Weather interrumpida con CTRL+C] #######')
        sys.exit(0)
