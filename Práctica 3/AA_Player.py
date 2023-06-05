import socket
import sys
import json

from json import dumps
from kafka import KafkaProducer
from kafka import KafkaConsumer

from sty import Style, RgbFg
from sty import fg, bg, ef, rs

from json import loads

from mapa import Mapa
import random

import threading
from threading import Thread

#----Práctica 3------ AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import Crypto
import traceback
import requests

##Esto es para deshabilitar los warning de HTTPS inseguro
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CBOLD     = '\33[1m'
CEND = '\033[0m'

args_json = json.load(open("args.json"))

puerto_escucha_AA_Registry = args_json['AA_Registry'][0]['puerto_escucha']
ip_AA_Registry = args_json['AA_Registry'][0]['ip']

puerto_escucha_AA_Engine = args_json['AA_Engine'][0]['puerto_escucha']
ip_AA_Engine = args_json['AA_Engine'][0]['ip']

topico_partida = args_json['topicos'][0]['topico_partida']
server_kafka = args_json['otros'][0]['ip_kafka'] + ":"+ args_json['otros'][0]['puerto_kafka']

consumidor_timeout = args_json['AA_Player'][0]['consumidor_timeout']

#Para detectar que un servicio para con ctrl + z ####################
import signal
def handler(signum, frame):
        print( bg.red + '\n ####### [AVISO: Ejecución de AA_Player interrumpida con CTRL+C] #######' + bg.rs)
        producer = KafkaProducer(bootstrap_servers=[server_kafka],
                value_serializer=lambda x: 
                dumps(x).encode('utf-8'))
        if len(LISTA_JUGADORES) > 0:
            #busco mi alias
            index = -1
            for i, v in enumerate(LISTA_JUGADORES):
                if v[1] == MI_ALIAS:
                    index = i
                    break
            if index >= 0:
                alias = LISTA_JUGADORES[index][0]
                producer.send(topico_partida,f"desconectar@Alias:{alias}@Player:{MI_ALIAS}")   
            
        sys.exit(0)

signal.signal(signal.SIGTSTP, handler)
########################################################

def send_To_Server(client, msg):
    message = msg.encode('utf-8')
    msg_length = len(message)
    send_length = str(msg_length).encode('utf-8')
    send_length += b' ' * (64 - len(send_length))
    client.send(send_length)
    client.send(message)


'''
 ██████╗ ██████╗ ███╗   ██╗███████╗██╗  ██╗██╗ ██████╗ ███╗   ██╗    ███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗
██╔════╝██╔═══██╗████╗  ██║██╔════╝╚██╗██╔╝██║██╔═══██╗████╗  ██║    ██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝
██║     ██║   ██║██╔██╗ ██║█████╗   ╚███╔╝ ██║██║   ██║██╔██╗ ██║    █████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗  
██║     ██║   ██║██║╚██╗██║██╔══╝   ██╔██╗ ██║██║   ██║██║╚██╗██║    ██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝  
╚██████╗╚██████╔╝██║ ╚████║███████╗██╔╝ ██╗██║╚██████╔╝██║ ╚████║    ███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗
 ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝                                                                                                                   
'''
fg.orange = Style(RgbFg(255, 150, 50))
fg.verde1 = Style(RgbFg(105, 197, 174))

#Práctica 3
aes_kafka_KEY = b""

##CONEXIÓN A SERVIDOR AA_ENGINE
def connnect_to_Engine(): 
    
    global aes_kafka_KEY

    direccion = (ip_AA_Engine, puerto_escucha_AA_Engine)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:

        client.connect(direccion)
        
        print("Introduzca su alias:")
        alias = input()
        print("Introduzca su password:")
        password = input()
        mensaje_logeo = {
            "alias":alias, 
            "password":password
        }
        json_mensaje = json.dumps(mensaje_logeo)
        
        
        #Creo una llave temporal de 1 solo uso para el socket entre player a engine (PRÁCTICA 3)
        salt = b'\x1a\xb3m\xa0\xbf!\xfc\xac6\x7f"\x9f}\xc3\xe0M\xe7\xc4\x94\xc6s\xfc\xa8\x08\xa6C\x19\x9d\x90\xb6\xec\xf3'
        password="vadim" #un password elegido (necesario para crear la key)
        aes_key_temporal = PBKDF2(password,salt,dkLen=32)
        
        ##envio a engine el mensaje encriptado y la key para desencriptar este mensaje
        send_To_Server(client, socket_encriptar(aes_key_temporal,"login" + "@" + json_mensaje) + "|&|" + str(list(aes_key_temporal)))
        #client.settimeout(3) #para que no se quede esperando respuesta infinitamente
      
        server_response = client.recv(2048).decode('utf-8')
        msg = ""

        if "|&|" in server_response:
            aes_kafka_KEY = bytes(eval(server_response.split("|&|")[1]))
            msg = socket_desencriptar(aes_key_temporal,server_response.split("|&|")[0])  
            print("Clave AES para kafka recibida.")
        else:
            msg = socket_desencriptar(aes_key_temporal,server_response)  

        ## MANDO MENSAJE PARA DESCONECTARME
        send_To_Server(client, socket_encriptar(aes_key_temporal,"Desconectar"))
        server_response = client.recv(2048).decode('utf-8')
        client.close()
        #print("Desconectado del servidor.")

        if "Datos de login correctos" in msg: #LOGIN CORRECTO
            
            global ELIMINADO
            
            ELIMINADO = False
            print(bg.blue + "Identificación correcta. Esperando a que el Engine inicie partida..." + bg.rs)

            try:
                # ACTIVO CONSUMIDOR
                Thread(target=consumidor,args=(alias,"")).start() #Para el logeo de los players
            
                # ACTIVO PRODUCTOR
                productor(alias)
            except Exception as error:
                print(bg.red + "Excepción ocurrida en la partida. Te has salido." + bg.rs)
                print(error)
            
        else:
            print(msg)
        
    except Exception as error:
        print(bg.red + "Excepción ocurrida." + bg.rs)
        traceback.print_exc()
        
  
################################ CONSUMIDOR ########################################

'''
 ██████╗ ██████╗ ███╗   ██╗███████╗██╗   ██╗███╗   ███╗██╗██████╗  ██████╗ ██████╗ 
██╔════╝██╔═══██╗████╗  ██║██╔════╝██║   ██║████╗ ████║██║██╔══██╗██╔═══██╗██╔══██╗
██║     ██║   ██║██╔██╗ ██║███████╗██║   ██║██╔████╔██║██║██║  ██║██║   ██║██████╔╝
██║     ██║   ██║██║╚██╗██║╚════██║██║   ██║██║╚██╔╝██║██║██║  ██║██║   ██║██╔══██╗
╚██████╗╚██████╔╝██║ ╚████║███████║╚██████╔╝██║ ╚═╝ ██║██║██████╔╝╚██████╔╝██║  ██║
 ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝                                                                                  
'''
MI_ALIAS = ""
MI_NIVEL = ""
LISTA_JUGADORES = []  
ELIMINADO = False
def consumidor(alias,aux) -> None:
    mapa = Mapa()
    global MI_ALIAS
    global MI_NIVEL
    global LISTA_JUGADORES
    global ELIMINADO
    
    i : int = 0

    try:
        consumer = KafkaConsumer(
            topico_partida,
            bootstrap_servers=[server_kafka],
            auto_offset_reset='latest',
            #group_id= None,
            enable_auto_commit=True,
            value_deserializer=lambda x: loads(x.decode('utf-8')),
            consumer_timeout_ms=consumidor_timeout
            )
        for message in consumer:

            #Práctica 3
            mensaje = kafka_desencriptar(message.value) #quito el cifrado del mensaje con la clave 

                

            if "PARTIDA TERMINADA" in mensaje:
                print(bg.red + "La partida fué suspendida por AA_Engine o el servidor se ha caido." + bg.rs)
                ELIMINADO = True
                break #salgo del consumidor (partida)
                        
            if "inicio@" in mensaje:
                
                print(bg.blue + "################################### COMIENZA LA PARTIDA ###################################" + bg.rs)
                string_players = mensaje.split("@")[1] #recibo una lista de tuplas: [(alias,alias_mapa),etc]
                print(bg.black + fg.orange + f"JUGADORES PARTIDA: {string_players}" + fg.rs + bg.rs)
                LISTA_JUGADORES = eval(string_players)
                for player in LISTA_JUGADORES:
                    if player[0] == alias:
                        MI_ALIAS = player[1]
                        MI_NIVEL = player[2]
                        print(bg.black + fg.orange + f"Soy el jugador '{MI_ALIAS}', Mi nivel es: {MI_NIVEL}"  + fg.rs + bg.rs)
            
            elif "mapa@" in mensaje:
                if i == 0: 
                    print_comoMoverJUgador()
                
                mapa.DeepCopy(eval(mensaje.split("@")[1]))
                print(bg.blue + "-----------------------MAPA DE LA PARTIDA--------------------------" + bg.rs)
                print(mapa.getMapa(MI_ALIAS))
                print(bg.blue + "------------------------------------------------------------------"+ bg.rs)
                
                i = i + 1
            elif "info@" in mensaje:
                msg = mensaje.split("@")[1]
                
                if "mina" in mensaje and f"{alias}" in mensaje:
                    print(bg.red +CBOLD+ "---------------------------HAS MUERTO A CAUSA DE UNA MINA-------------------------------" +bg.rs + CEND)
                    print(bg.red +CBOLD + "---------------------------TE HAN ELIMINADO DE LA PARTIDA-------------------------------" +bg.rs + CEND)
                    ELIMINADO = True
                    break #salgo del consumidor (partida)
                if "salido" in mensaje and f"{alias}" in mensaje:
                    print(bg.red +CBOLD+ "-------------------------------HAS SALIDO DE LA PARTIDA-------------------------------" +bg.rs + CEND)
                    ELIMINADO = True
                    break #salgo del consumidor (partida)
                
                if "ha ganado la partida" in mensaje and f"{alias}" in mensaje:
                    print(bg.green +CBOLD+ "-------------------------------HAS GANADO LA PARTIDA-------------------------------" +bg.rs + CEND)
                    ELIMINADO = True
                    break #salgo del consumidor (partida)
                if "han luchado" in mensaje:
                    print(msg)
                    if MI_ALIAS in mensaje: #he luchado con alguien yo
                        if "EMPATE" not in mensaje: #SI NO HAY EMPATE
                            if f"GANA '{MI_ALIAS}'" in mensaje: #SI GANO YO
                                print("¡Gano yo el duelo!")
                            else: #SI NO GANO YO
                                print(bg.red +CBOLD+ "---------------------------HAS MUERTO A CAUSA DE UN DUELO-------------------------------" +bg.rs + CEND)
                                print(bg.red +CBOLD + "---------------------------TE HAN ELIMINADO DE LA PARTIDA-------------------------------" +bg.rs + CEND)
                                ELIMINADO = True
                                break #salgo del consumidor (partida)
                        else: # SI HEMOS EMPATADO
                            print("¡ He luchado pero hemos empatado !")

            #f"info@¡'{alias_ganador}'|'{aiias_mapa_ganador}' ha ganado la partida!")
            elif "jugadores@" in mensaje:
                msg = mensaje.split("@")[1]
                LISTA_JUGADORES = eval(msg)
                print(bg.blue +f"Jugadores: {msg}" + bg.rs)

    except Exception as error:
        print(bg.red + "Excepción ocurrida en el consumidor de AA_Player" + bg.rs)
        traceback.print_exc()
            
    #Aquí solo llega si sale del consumidor (por los mensajes o por el timeout del consumidor)
    print(bg.blue + "Te has salido del juego. O porque se ha terminado o porque tarda mucho en responder el servidor." + bg.rs)
    ELIMINADO = True 
    
################################ PRODUCTOR ########################################

'''
██████╗ ██████╗  ██████╗ ██████╗ ██╗   ██╗ ██████╗████████╗ ██████╗ ██████╗ 
██╔══██╗██╔══██╗██╔═══██╗██╔══██╗██║   ██║██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
██████╔╝██████╔╝██║   ██║██║  ██║██║   ██║██║        ██║   ██║   ██║██████╔╝
██╔═══╝ ██╔══██╗██║   ██║██║  ██║██║   ██║██║        ██║   ██║   ██║██╔══██╗
██║     ██║  ██║╚██████╔╝██████╔╝╚██████╔╝╚██████╗   ██║   ╚██████╔╝██║  ██║
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝  ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝                                                                        
'''

import readchar

def productor(alias) -> None:
    global ELIMINADO 
    global MI_ALIAS
    producer = KafkaProducer(bootstrap_servers=[server_kafka],
                    value_serializer=lambda x: 
                    dumps(x).encode('utf-8'))
          
    op=""

    while op!= "X":  

        op= readchar.readkey()
        #op = sys.stdin.read()
        if ELIMINADO : break #cuando nos eliminan nos salimos del menú de juego
        if op in ["w","W","s","S","a","A","d","D","q","Q","e","E","z","Z","x","X","0","0"]:
            
            if op == "0" or op == "0": 

                #Práctica 3 encriptado
                producer.send(topico_partida, kafka_encriptar(f"desconectar@Alias:{alias}@Player:{MI_ALIAS}")) ## salir

                ELIMINADO = True
                LISTA_JUGADORES.clear()
                MI_ALIAS = ""
                break
            else: 
                #Práctica 3 encriptado
                producer.send(topico_partida, kafka_encriptar(f"movimiento@Alias:{alias}@Player:{MI_ALIAS}@Movimiento:{op}")) ## mover 
    
def print_comoMoverJUgador():
    print("\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("Como mover al jugador: ")
    print("W->arriba, S->abajo, A->izquierda, D->derecha, Q->arriba-izquierda, E->arriba-derecha, Z->abajo-izquierda, X->abajo-derecha; salir-> Salir del juego")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    
'''
██████╗ ███████╗ ██████╗ ██╗███████╗████████╗██████╗  ██████╗     ██████╗ ███████╗    ██╗   ██╗███████╗██╗   ██╗ █████╗ ██████╗ ██╗ ██████╗ 
██╔══██╗██╔════╝██╔════╝ ██║██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗    ██╔══██╗██╔════╝    ██║   ██║██╔════╝██║   ██║██╔══██╗██╔══██╗██║██╔═══██╗
██████╔╝█████╗  ██║  ███╗██║███████╗   ██║   ██████╔╝██║   ██║    ██║  ██║█████╗      ██║   ██║███████╗██║   ██║███████║██████╔╝██║██║   ██║
██╔══██╗██╔══╝  ██║   ██║██║╚════██║   ██║   ██╔══██╗██║   ██║    ██║  ██║██╔══╝      ██║   ██║╚════██║██║   ██║██╔══██║██╔══██╗██║██║   ██║
██║  ██║███████╗╚██████╔╝██║███████║   ██║   ██║  ██║╚██████╔╝    ██████╔╝███████╗    ╚██████╔╝███████║╚██████╔╝██║  ██║██║  ██║██║╚██████╔╝
╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝     ╚═════╝ ╚══════╝     ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝                                                                                                                                         
'''

#######MENUS DE REGISTRO Y EDICION
def registrarUsuario(tipo):
    print("REGISTRO DE USUARIO")
    op="N"
    alias = password = ""
    
    while op=="N":

        while True:
            print("Introduce tu alias:")
            alias=input()
            if(alias == ""):
                print("Tiene que introducir un alias.")
            else:
                break

        while True:
            print("Introduce tu contraseña :")
            password=input()
            if(password == ""):
                print("La contraseña no puede estar vacía. Si desea salirse, introduzca una letra y ponga 'n' en la confirmación")
            else:
                break
        
        print("Compruebe sus datos: ")
        print("Alias: "+str(alias)+" Contraseña: "+str(password))
        op="A"
        while op!="N" and op!="S" and op!="n" and op!="s":
            print("S/N")
            op=input()
            if op=="S" or op=="s":

                posX = random.randrange(0,19)
                posY = random.randrange(0,19)
                ef_ = random.randrange(-10,10)
                ec_ = random.randrange(-10,10)
                pos = str(posX) + "," + str(posY)
                mensaje_crear_perfil = {f"alias":alias, "password":password,"nivel":1,"ef":ef_,"ec":ec_,"posicion":pos}
                json_mensaje = json.dumps(mensaje_crear_perfil)
                
                #Creo una llave temporal de 1 solo uso para el socket entre player a registry (PRÁCTICA 3)
                salt = b'\x1a\xb3m\xa0\xbf!\xfc\xac6\x7f"\x9f}\xc3\xe0M\xe7\xc4\x94\xc6s\xfc\xa8\x08\xa6C\x19\x9d\x90\xb6\xec\xf3'
                password="vadim" #un password elegido (necesario para crear la key)
                aes_key_temporal = PBKDF2(password,salt,dkLen=32)
             
                if tipo == "SOCKETS": print(registrarUsuario_sockets(json_mensaje, aes_key_temporal))
                else: 
                    if tipo == "API": print(registrarUsuario_API(json_mensaje, aes_key_temporal))    

def registrarUsuario_sockets(json_mensaje , aes_key_temporal):
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    direccion = (ip_AA_Registry, puerto_escucha_AA_Registry)
    client.connect(direccion)
                
    msg = socket_encriptar(aes_key_temporal,"crear_perfil" + "@" + json_mensaje) + "|&|" + str(list(aes_key_temporal))
            
    send_To_Server(client, msg)

    respuesta = client.recv(2048).decode('utf-8')
    respuesta_desencriptada = socket_desencriptar(aes_key_temporal,respuesta)
    
    send_To_Server(client, socket_encriptar(aes_key_temporal,"Desconectar"))
    client.close()
    
    return respuesta_desencriptada


def registrarUsuario_API(json_mensaje , aes_key_temporal):
    
    ip = args_json['API_Registry'][0]['ip']
    puerto = args_json['API_Registry'][0]['puerto']

    url = f'https://{ip}:{puerto}/jugador'
    
    msg = api_encriptar(aes_key_temporal,json_mensaje) + "|&|" + str(list(aes_key_temporal))
    
    respuesta = requests.post(url, verify=False, json = msg)  
    respuesta_desencriptada = api_desencriptar(aes_key_temporal , respuesta.text)  
    
    return respuesta_desencriptada
    
    
    
'''
███████╗██████╗ ██╗████████╗ █████╗ ██████╗     ██████╗ ███████╗██████╗ ███████╗██╗██╗     
██╔════╝██╔══██╗██║╚══██╔══╝██╔══██╗██╔══██╗    ██╔══██╗██╔════╝██╔══██╗██╔════╝██║██║     
█████╗  ██║  ██║██║   ██║   ███████║██████╔╝    ██████╔╝█████╗  ██████╔╝█████╗  ██║██║     
██╔══╝  ██║  ██║██║   ██║   ██╔══██║██╔══██╗    ██╔═══╝ ██╔══╝  ██╔══██╗██╔══╝  ██║██║     
███████╗██████╔╝██║   ██║   ██║  ██║██║  ██║    ██║     ███████╗██║  ██║██║     ██║███████╗
╚══════╝╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝                                                                                      
'''

def editarPerfil(tipo):
    print("EDITAR PERFIL")
    correcto="N"
    cadena=""
    while(correcto=="N"):

        while True:
            print("Introduce tu nombre alias:")
            alias=input()
            if(alias == ""):
                print("Tiene que introducir un alias.")
            else:
                break

        while True:
            print("Introduce tu contraseña nueva:")
            newPassword=input()
            if(newPassword == ""):
                print("La contraseña no puede estar vacía. Si desea salirse, introduzca una letra y ponga 'n' en la confirmación")
            else:
                break
        
        correcto="T"
        while correcto!="S" and correcto !="N" and correcto!="s" and correcto !="n":
            print("La nueva contraseña es: " + newPassword)
            print("Es correcto?(S/N):")
            correcto=input()
            if(correcto=="S" or correcto=="s"):  
                
                #Creo una llave temporal de 1 solo uso para el socket entre player a registry (PRÁCTICA 3)
                salt = b'\x1a\xb3m\xa0\xbf!\xfc\xac6\x7f"\x9f}\xc3\xe0M\xe7\xc4\x94\xc6s\xfc\xa8\x08\xa6C\x19\x9d\x90\xb6\xec\xf3'
                password="vadim" #un password elegido (necesario para crear la key)
                aes_key_temporal = PBKDF2(password,salt,dkLen=32)
                
                mensaje_editar_perfil = {"alias":alias, "password":newPassword}
                json_mensaje = json.dumps(mensaje_editar_perfil)
     
                if tipo == "SOCKETS": print(editarPerfil_sockets(json_mensaje, aes_key_temporal))
                else: 
                    if tipo == "API": print(editarPerfil_API(json_mensaje, aes_key_temporal))            
                          
#Enviar mensaje por sockets
def editarPerfil_sockets(json_mensaje, aes_key_temporal) -> str:

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    direccion = (ip_AA_Registry, puerto_escucha_AA_Registry)
    client.connect(direccion)
    
    msg = socket_encriptar(aes_key_temporal,"editar_perfil" + "@" + json_mensaje) + "|&|" + str(list(aes_key_temporal))

    send_To_Server(client, msg)

    respuesta = client.recv(2048).decode('utf-8')
    respuesta_desencriptada = socket_desencriptar(aes_key_temporal,respuesta)

    send_To_Server(client, socket_encriptar(aes_key_temporal,"Desconectar"))
    client.close()
    
    return respuesta_desencriptada

#Enviar mensaje por API
def editarPerfil_API(json_mensaje, aes_key_temporal) -> str:
    
    ip = args_json['API_Registry'][0]['ip']
    puerto = args_json['API_Registry'][0]['puerto']

    url = f'https://{ip}:{puerto}/jugador'

    msg = api_encriptar(aes_key_temporal,json_mensaje) + "|&|" + str(list(aes_key_temporal))
    
    respuesta = requests.put(url, verify=False, json = msg) #hago un put y recibo respuesta
    respuesta_desencriptada = api_desencriptar(aes_key_temporal , respuesta.text)  

    return respuesta_desencriptada


'''
███╗   ███╗███████╗███╗   ██╗██╗   ██╗
████╗ ████║██╔════╝████╗  ██║██║   ██║
██╔████╔██║█████╗  ██╔██╗ ██║██║   ██║
██║╚██╔╝██║██╔══╝  ██║╚██╗██║██║   ██║
██║ ╚═╝ ██║███████╗██║ ╚████║╚██████╔╝
╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝                                    
'''
def menu():
    option = 0
    print(bg.blue + "¡BIENVENIDO AL JUEGO!" + bg.rs)
    while True: 
        print(bg.blue + "Seleccione una opcion:" + bg.rs)
        print("1. Crear perfil (SOCKETS)")
        print("2. Crear perfil (API)")
        print("3. Editar un perfil existente (SOCKETS)")
        print("4. Editar un perfil existente (API)")
        print("5. Unirse a la partida")
        print("6. Salir")
        option = input()
        if option == '1':
            registrarUsuario("SOCKETS") 
        elif option == '2':
            registrarUsuario("API") 
        elif option == '3':
            editarPerfil("SOCKETS")
        elif option == '4':
            editarPerfil("API")
        elif option == '5':
            connnect_to_Engine()
        elif option == '6':
            break
        else:
            print("ERROR. Seleccione una opción existente.")


#Práctica 3
#1-Paso el mensaje a string (porque hacerlo en bytes pide que sea string).
#2-Paso el string a bytes (porque cipher lo requiere en bytes).
#3-Cifro el mensaje.
#4-Paso el mensaje cifrado a una lista (ya que pasándolo a lista es lo único que he visto que luego en el consumidor nos dé la forma correcta)
#5-Paso esa lista a un string (porque producer.send solo envia strings)
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

def kafka_encriptar(mensaje) -> str:
    global aes_kafka_KEY

    msg = bytes(str(mensaje).encode())

    cipher = AES.new(aes_kafka_KEY,AES.MODE_CBC)
    mensaje_encriptado = cipher.encrypt(pad(msg, AES.block_size))

    return str(list(cipher.iv)) + "|@|" + str(list(mensaje_encriptado))

#kafka_desencriptar: Recibe un mensaje en el siguiente formato: IV|@|Mensaje
#1-Con eval paso el string (que en verdad es una lista pero en forma de string) a lista.
#2-COn bytes paso la lista a bytes (porque lo requiere el decrypt).
#3-Obtengo el mensaje y con decode le quito el "b'" que hay al principio del mensaje decodificado.
def kafka_desencriptar(mensaje) -> str:
    global aes_kafka_KEY

    iv = bytes(eval(mensaje.split("|@|")[0].encode()))
    mensaje_encriptado = bytes(eval(mensaje.split("|@|")[1]))

    cipher = AES.new(aes_kafka_KEY,AES.MODE_CBC, iv = iv)
    return unpad(cipher.decrypt(mensaje_encriptado), AES.block_size).decode() #recibo bytes

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

if __name__=="__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print( bg.red + '\n ####### [AVISO: Ejecución de AA_Player interrumpida con CTRL+C] #######' + bg.rs)
        producer = KafkaProducer(bootstrap_servers=[server_kafka],
                value_serializer=lambda x: 
                dumps(x).encode('utf-8'))
        if len(LISTA_JUGADORES) > 0:
            #busco mi alias
            index = -1
            for i, v in enumerate(LISTA_JUGADORES):
                if v[1] == MI_ALIAS:
                    index = i
                    break
            if index >= 0:
                alias = LISTA_JUGADORES[index][0]
                producer.send(topico_partida,f"desconectar@Alias:{alias}@Player:{MI_ALIAS}")   
            
        sys.exit(0)
    except Exception as error:
        print(bg.red + "Excepción ocurrida." + bg.rs)
        traceback.print_exc()
