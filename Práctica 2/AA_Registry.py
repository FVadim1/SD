from email import message
import socket
import threading
import json
import sys
from db import db

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

    while True:
        
        msg_length = conn.recv(64).decode('utf-8')
        
        if msg_length:
            
            #print()
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode('utf-8')

            print(f"  He recibido del cliente [{addr}] el mensaje: {msg}")

             #Cliente se desconecta
            if msg == "Desconectar":
                break
            else:
                mensaje = msg.split("@")
                op = mensaje[0]
                #print(f"DEBUG_mensaje: [{mensaje}]")
                datos = json.loads(mensaje[1])
                
                if op == "crear_perfil" or op == "editar_perfil":
                        
                    #ME CONECTO A LA BASE DE DATOS
                    conexion_db = db()
                    
                    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):
                        existe = True
                        print("antes de logeo")
                        lista = conexion_db.logeo2(datos["alias"])       
                        if(len(lista) == 0):      
                            existe = False  
                        print("El mensaje" + op)        
                        print(f"Existe: [{existe}]")    
                        #OPERACIONES   
                        if op == "crear_perfil" and not existe:
                            print("ha entrado en crear perfil")
                            if conexion_db.insertar_Jugador(datos["alias"],datos["password"],datos["nivel"],datos["ef"],datos["ec"],datos["posicion"]):                   
                                conn.send(f"Jugador creado.".encode('utf-8'))
                            else:
                                conn.send(f"ERROR: Jugador no creado.".encode('utf-8'))
                                                    
                        if op == "editar_perfil" and existe:
                            print("ha entrado en editar perfil")
                            if conexion_db.modJugador_Password(datos["alias"],datos["password"]):    
                                conn.send(f"Jugador modificado.".encode('utf-8'))   
                            else:
                                conn.send(f"ERROR: Jugador no modificado.".encode('utf-8'))  

                        if op == "editar_perfil" and not existe:
                            print("ha entrado en editar perfil no existe")
                            conn.send(f"ERROR: jugador no existe.".encode('utf-8'))                                             
                        ##CIERRO CONEXIÓN
                        conexion_db.closeCommunication()
                        
                    else:
                        print("No se ha podido conectar a la base de datos.")

            
            #Envio al cliente la confirmación de que he recibido su mensaje
            #conn.send(f"HOLA CLIENTE: He recibido tu mensaje: {msg} ".encode(FORMAT))
            
    conn.send(f"Socket cerrado. Desconectado del servidor.".encode('utf-8'))
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
            

######################### MAIN ##########################
if __name__ == "__main__":
    try:
        iniciar_ServidorRegistry()
    except KeyboardInterrupt:
        print('\n ####### [AVISO: Ejecución del servidor AA_Registry interrumpida con CTRL+C] #######')
        sys.exit(0)
