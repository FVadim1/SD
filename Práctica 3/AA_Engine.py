from ipaddress import collapse_addresses
from re import I
import socket
import sys
import json
import threading
from threading import Thread
from db import db

from json import dumps
from kafka import KafkaProducer
from kafka import KafkaConsumer
from json import loads
from mapa import Mapa
from time import sleep
from sty import Style, RgbFg
from sty import fg, bg, ef, rs

from auxiliares_Engine import *
from copy import copy,deepcopy

#----Práctica 3------ AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import Crypto
import requests
import traceback

#████████████████████████████████████████████████████████████████████████     
#██Para detectar que un servicio para con ctrl + z ██████████████████████
import signal
def handler(signum, frame):
    print( bg.red + '\n ####### [AVISO: Ejecución de AA_Engine interrumpida con CTRL+Z] #######' + bg.rs)
    if len(JUGADORES_PARTIDA) > 0:
        exception_TerminarPartida()
    sys.exit(0)

signal.signal(signal.SIGTSTP, handler)
#████████████████████████████████████████████████████████████████████████

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

args_json = json.load(open("args.json"))
MAX_JUGADORES = args_json['AA_Engine'][0]['max_jugadores']
consumidor_timeout = args_json['AA_Engine'][0]['consumidor_timeout']



#████████████████████████████████████████████████████████████████████████
#████████████████████ [Servidor socket AA_Engine]  ██████████████████████
'''
███████╗███████╗██████╗ ██╗   ██╗██╗██████╗  ██████╗ ██████╗     ███████╗███╗   ██╗ ██████╗ ██╗███╗   ██╗███████╗
██╔════╝██╔════╝██╔══██╗██║   ██║██║██╔══██╗██╔═══██╗██╔══██╗    ██╔════╝████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝
███████╗█████╗  ██████╔╝██║   ██║██║██║  ██║██║   ██║██████╔╝    █████╗  ██╔██╗ ██║██║  ███╗██║██╔██╗ ██║█████╗  
╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██║██║  ██║██║   ██║██╔══██╗    ██╔══╝  ██║╚██╗██║██║   ██║██║██║╚██╗██║██╔══╝  
███████║███████╗██║  ██║ ╚████╔╝ ██║██████╔╝╚██████╔╝██║  ██║    ███████╗██║ ╚████║╚██████╔╝██║██║ ╚████║███████╗
╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝    ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝                                                                                                               '''
puerto_escucha = args_json['AA_Engine'][0]['puerto_escucha']
ip_engine = args_json['AA_Engine'][0]['ip']
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
JUGADORES_PARTIDA = []


def handle_Engine_Client(conn, addr):
    global JUGADORES_PARTIDA
    
    aes_key_temporal = b"" #esta es la key temporal para los sockets
    while True:
        
        msg_length = conn.recv(64).decode('utf-8')
        
        if msg_length:
            
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode('utf-8')
            
            #Obtengo el mensaje encriptado y la llave para desencriptarlo del player 
            #El player le envia al servidor solo 2 mensaje, el primer con el logeo y la llave aes , y el segundo para desconectarse
            if "|&|" in msg: #aquí entra la primera vez
                aes_key_temporal = bytes(eval(msg.split("|&|")[1]))
                msg = socket_desencriptar(aes_key_temporal , msg.split("|&|")[0])
            else: #aquí entra para del desconectar que le menda el player
                msg = socket_desencriptar(aes_key_temporal,msg)
            
            if "@" in str(msg): 
                mensaje = msg.split("@")
                op = mensaje[0]
                datos = json.loads(mensaje[1])
        
                if op == "login":       

                        if len(JUGADORES_PARTIDA) <= MAX_JUGADORES:
                            #ME CONECTO A LA BASE DE DATOS
                            conexion_db = db()
                            
                            if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):
                                
                                if PARTIDA_DISPONIBLE:
                                    
                                    if datos['alias'] not in JUGADORES_PARTIDA:
                                        if len(conexion_db.logeo(datos['alias'],datos['password'])) > 0: #se ha encontrado una cuenta con esos datos

                                            #PRÁCTICA 3, A parte del login correcto envio las claves RSA
                                            with open("kafka_aes_key.bin", "rb") as f:
                                                kafka_aes_key = f.read()

                                            #envio al player el mensaje encriptado con la clave aes temporal para socket, y la clave de aes que se utilizará para la comunicación con kafka
                                            conn.send(f"{socket_encriptar(aes_key_temporal,'Datos de login correctos.')}|&|{str(list(kafka_aes_key))}".encode('utf-8'))

                                            JUGADORES_PARTIDA.append(datos['alias']) #añado al jugador a la cola de espera
                                            print(f"[AA_Engine SERVER] El jugador '{datos['alias']}' se ha unido a la partida.")
     
                                        else:
                                            conn.send(f"{socket_encriptar(aes_key_temporal,'ERROR: Datos de login incorrectos o el jugador con ese alias no existe.')}".encode('utf-8'))
                                    else:
                                        print("Un jugador con el mismo alias ha intentado acceder al juego. Se le ha denegado el acceso.")
                                        conn.send(f"{socket_encriptar(aes_key_temporal,'ERROR: Ya existe un jugador con ese alias en la partida.')}".encode('utf-8'))

                                else:
                                    print(f"Jugador intentó unirse a la partida pero no hay ninguna disponible.")
                                    conn.send(f"{socket_encriptar(aes_key_temporal,'ERROR: No hay ninguna partida disponible.')}".encode('utf-8'))
                    
                                ##CIERRO CONEXIÓN
                                conexion_db.closeCommunication()
                            else:
                                conn.send(f"{socket_encriptar(aes_key_temporal,'ERROR: No se ha podido establecer conexión con la base de datos.')}".encode('utf-8'))

                        else:
                            print("Jugador intentó unirse pero se ha alcanzado el máximo de jugadores")
                            conn.send(f"{socket_encriptar(aes_key_temporal,'ERROR: se alcanzó el máximo de jugadores de la partida.')}".encode('utf-8'))


            if msg == "Desconectar":
                conn.send("".encode('utf-8'))
                conn.close()
                break
         
def iniciar_ServidorEngine():
    global PUERTO_OCUPADO
    try:
        direccion = (ip_engine, puerto_escucha)
        server.bind(direccion)
        server.listen()
        print(f"\n [AA_Engine SERVER] Servidor a la escucha en {direccion} \n")

        PUERTO_OCUPADO =False
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_Engine_Client, args=(conn, addr)) #crea un thread para el cliente en cuestion (cada uno tiene el suyo)
            thread.start()
    except Exception as error:
        print(bg.red + "Excepción ocurrida." + bg.rs)
        traceback.print_exc()


#████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████
#████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████

'''
██████╗  █████╗ ██████╗ ████████╗██╗██████╗  █████╗     ███╗   ██╗██╗   ██╗███████╗██╗   ██╗ █████╗ 
██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██║██╔══██╗██╔══██╗    ████╗  ██║██║   ██║██╔════╝██║   ██║██╔══██╗
██████╔╝███████║██████╔╝   ██║   ██║██║  ██║███████║    ██╔██╗ ██║██║   ██║█████╗  ██║   ██║███████║
██╔═══╝ ██╔══██║██╔══██╗   ██║   ██║██║  ██║██╔══██║    ██║╚██╗██║██║   ██║██╔══╝  ╚██╗ ██╔╝██╔══██║
██║     ██║  ██║██║  ██║   ██║   ██║██████╔╝██║  ██║    ██║ ╚████║╚██████╔╝███████╗ ╚████╔╝ ██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═════╝ ╚═╝  ╚═╝    ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝  ╚═╝                                                                                                 
'''
topico_partida = args_json['topicos'][0]['topico_partida']
server_kafka = args_json['otros'][0]['ip_kafka'] + ":"+ args_json['otros'][0]['puerto_kafka']

def comenzarPartida():
    
    global JUGADORES_PARTIDA
    
    if len(JUGADORES_PARTIDA) > 1:
        PARTIDA_DISPONIBLE = False #bloqueo que se puedan meter mas players

        borrar_mapa_en_BaseDatos() #borro los mapas que hay en la base de datos
        borrar_jugadoresPartida_en_BaseDatos()

        API_KEY_OPENWEATHER =  args_json['AA_Engine'][0]['API_KEY_OPENWEATHER']
        ciudades : list = args_json['AA_Engine'][0]['CIUDADES']

        try:
            for i, ciudad in enumerate(ciudades):
                    temperatura = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={API_KEY_OPENWEATHER}&units=metric").json()["main"]["temp"]
                    ciudades[i] = f"('{ciudad}',{round(temperatura)})"
        except Exception as error:
            print(bg.red + "Excepción orucrrida a la hora de conectarse a openweather. ¿Estás conectado a internet??" + bg.rs)
            print(error)
            ciudades = ["('Tokio', 15)", "('Sidney', 32)", "('Paris', 19)", "('Pekin', 25)"]
       
        insertar_ciudades_en_BaseDatos(ciudades)
            
        print(f"CIUDADES: {ciudades}") 
        print(f"Verde: {ciudades[0]}") #mapa[0-9][0-9]
        print(f"Azul: {ciudades[1]}") #mapa[0-9][10-19]
        print(f"Marrón: {ciudades[2]}") #mapa[10-19][0-9]
        print(f"Gris: {ciudades[3]}") #mapa[10-19][10-19]
                
        #print(f"JUGADORES_PARTIDA: {JUGADORES_PARTIDA}") 

        set_Pos_Random_Jugadores(JUGADORES_PARTIDA) 
        if PLAYER_RANDOM_EC_EF: set_EF_EC_Random_Jugadores(JUGADORES_PARTIDA)
        setLevel_Clima_JugadoresPos(ciudades,JUGADORES_PARTIDA)

        print(f"JUGADORES_PARTIDA:{JUGADORES_PARTIDA}") 
        
        db_jugadores = jugadoresFromDB() #todos los players en la base de datos
        #print(db_jugadores)

        mapa = Mapa()       
        
        #Le doy un alias a los jugadores y los meto en el mapa
        i = 1
        JUGADORES_PARTIDA_ALIAS = []
        for player in db_jugadores:
            
            if player[0] in JUGADORES_PARTIDA:
                pos = player[5].split(",")
                     
                mapa.setCelda(int(pos[0]),int(pos[1]),f'P{i}') #pongo al jugador en el mapa

                JUGADORES_PARTIDA_ALIAS.append((player[0],f"P{i}", f"nivel:{player[2]}"))  #para enviarselo a los players al inicio de la partida
                i = i + 1
        
        #AÑADO MINAS Y ALIMENTOS AL MAPA       
        mapa.add_Minas_Alimentos_ConPlayers()

        partida(mapa,JUGADORES_PARTIDA_ALIAS, ciudades)
         
    else:
        print( bg.red + "Error. No hay jugadores suficientes" + bg.rs)

'''
██████╗  █████╗ ██████╗ ████████╗██╗██████╗  █████╗ 
██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██║██╔══██╗██╔══██╗
██████╔╝███████║██████╔╝   ██║   ██║██║  ██║███████║
██╔═══╝ ██╔══██║██╔══██╗   ██║   ██║██║  ██║██╔══██║
██║     ██║  ██║██║  ██║   ██║   ██║██████╔╝██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═════╝ ╚═╝  ╚═╝'''
def partida(mapa : Mapa, JUGADORES_PARTIDA_ALIAS : list, ciudades : list):

    global aes_kafka_KEY

    print(f"JUGADORES_PARTIDA_ALIAS: {JUGADORES_PARTIDA_ALIAS}")
    
    print("--------------------MAPA DE LA PARTIDA--------------------")
    print(mapa)
    print("------------------------------------------------------------------")
    
    producer = KafkaProducer(bootstrap_servers=[server_kafka],
                        value_serializer=lambda x: 
                        dumps(x).encode('utf-8'))
    
    consumer = KafkaConsumer(
        topico_partida,
        bootstrap_servers=[server_kafka],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        value_deserializer=lambda x: loads(x.decode('utf-8')),
        consumer_timeout_ms=consumidor_timeout
    )

    #Envio a los players el mapa inicial de la partida
    insertar_mapa_en_BaseDatos(mapa) #PRACTICA 3
    insertar_JugadoresPartida_en_BaseDatos(JUGADORES_PARTIDA_ALIAS)
    producer.send(topico_partida, kafka_encriptar(f"inicio@{JUGADORES_PARTIDA_ALIAS}"))
    producer.send(topico_partida, kafka_encriptar(f"mapa@{mapa.getArray()}"))

    for message in consumer:

        #Práctica 3
        mensaje = kafka_desencriptar(message.value) #quito el cifrado del mensaje con la clave 

        if "movimiento@" in mensaje: #algun player envia su movimiento
            #print(mensaje)
            #leo el mensaje y lo proceso
            mensaje_descompuesto = mensaje.split("@") #movimiento@Alias:testplayer@Player:@Movimiento:W
            alias = mensaje_descompuesto[1].split(":")[1]
            alias_mapa = mensaje_descompuesto[2].split(":")[1]
            movimiento = mensaje_descompuesto[3].split(":")[1]
            
            #obtengo la pos actual en la base de datos
            pos_actual = jugador_getPosActual(alias).split(",") #jugador_getPosActual devuelve 'x,y'

            #recalculo la nueva pos en base a donde quiera ir
            pos_nueva_x,pos_nueva_y = getPosNueva(pos_actual, movimiento)# devuelve las 2 coordenada nuevas

            #Miro si cambia de ciudad, y si es asi, modifico su nivel acorde (luego)
            ciudad_actual = aux_getCiudad(ciudades,int(pos_actual[0]), int(pos_actual[1]))
            ciudad_movimiento = aux_getCiudad(ciudades,pos_nueva_x, pos_nueva_y)
            
            #actualizo mapa en base a lo que hay en la nueva pos
            celda = mapa.getCelda(pos_nueva_x,pos_nueva_y) #lo que hay puesto en esa pos del mapa

            if celda == "M": # MINA
                if ciudad_actual != ciudad_movimiento: setLevel_Clima_Movimiento(alias,ciudad_movimiento,JUGADORES_PARTIDA_ALIAS)

                mapa.setCelda(pos_nueva_x,pos_nueva_y, "0") #pongo la mina a 0
                mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos actual a 0

                insertar_mapa_en_BaseDatos(mapa) #PRACTICA 3
                producer.send(topico_partida, kafka_encriptar(f"mapa@{mapa.getArray()}"))

                producer.send(topico_partida, kafka_encriptar(f"info@¡'{alias}'|'{alias_mapa}' ha muerto a causa de una mina!"))
                print(f"El jugador '{alias}'|'{alias_mapa}' pisó una MINA. Ha sido eliminado.")
                #JUGADORES_PARTIDA.remove(alias)
                JUGADORES_PARTIDA_ALIAS = [tup for tup in JUGADORES_PARTIDA_ALIAS if tup[0] != alias] #todas menos los que tienen ese alias
                #actualizo base de datos con su nueva posición
                jugador_setDBPosNueva(alias,pos_nueva_x,pos_nueva_y)   
                
                #SI SOLO QUEDA 1 JUGADOR DESPUÉS DE QUE ESTE SALGA. AL QUE QUEDE LO DECLARO GANADOR
                if len(JUGADORES_PARTIDA_ALIAS) == 1:
                    terminarPartida(JUGADORES_PARTIDA_ALIAS, producer)
                    break #apago el consumidor
            else:
                if celda == "A":# ALIMENTO
                    if ciudad_actual != ciudad_movimiento: setLevel_Clima_Movimiento(alias,ciudad_movimiento,JUGADORES_PARTIDA_ALIAS)

                    mapa.setCelda(pos_nueva_x,pos_nueva_y, alias_mapa) #me pongo en la nueva pos
                    mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos anterior a 0
                    nivel, nivel_nuevo = jugador_addLevel(alias,JUGADORES_PARTIDA_ALIAS ) # le subo un nivel
                    producer.send(topico_partida, kafka_encriptar(f"info@¡'{alias}'|'{alias_mapa}' gana un nivel ({nivel}->{nivel_nuevo})!"))
                    print(f"nivel:{nivel}, nivel_nuevo:{nivel_nuevo} ")
                                            
                    #actualizo base de datos con su nueva posición
                    jugador_setDBPosNueva(alias,pos_nueva_x,pos_nueva_y)   
                else:
                    mi_nivel = jugador_getNivel(alias)
                    if "P" in celda:#se encuentra un jugador, luchan
                        #Obtengo el alias del jugador en base a su alias del mapa (P1,P2,etc)
                        
                        for jugador in JUGADORES_PARTIDA_ALIAS: #[('testplayer', 'P1', 'nivel:37')]
                                if jugador[1] == celda: #('testplayer', 'P1', 'nivel:37') 
                                    enemigo_alias = jugador[0]
                                    enemigo_nivel = jugador_getNivel(enemigo_alias)
                                    if mi_nivel == enemigo_nivel: #EMPATE
                                        print(f"{alias_mapa} y {celda} han luchado, pero han EMPATADO.")
                                        producer.send(topico_partida, kafka_encriptar(f"info@¡'{alias_mapa}' y '{celda}' han luchado. EMPATE!"))
                                    else:
                                        if mi_nivel > enemigo_nivel: #GANO YO
                                            if ciudad_actual != ciudad_movimiento: setLevel_Clima_Movimiento(alias,ciudad_movimiento,JUGADORES_PARTIDA_ALIAS)

                                            mapa.setCelda(pos_nueva_x,pos_nueva_y, alias_mapa) #voy a la casilla del enemigo derrotado
                                            mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos anterior a 0
                                            producer.send(topico_partida, kafka_encriptar(f"info@¡'{alias_mapa}' y {celda} han luchado. GANA '{alias_mapa}'!"))                                           
                                            
                                            #elimino al jugadro contrario del las listas
                                            #JUGADORES_PARTIDA.remove(enemigo_alias)
                                            JUGADORES_PARTIDA_ALIAS = [tup for tup in JUGADORES_PARTIDA_ALIAS if tup[0] != enemigo_alias] #nuevas lista = todos menos los que tienen ese alias
                                            #actualizo base de datos con su nueva posición
                                            jugador_setDBPosNueva(alias,pos_nueva_x,pos_nueva_y)  
                                            
                                            #SI SOLO QUEDA 1 JUGADOR DESPUÉS DE QUE ESTE SALGA. AL QUE QUEDE LO DECLARO GANADOR
                                            if len(JUGADORES_PARTIDA_ALIAS) == 1:
                                                terminarPartida(JUGADORES_PARTIDA_ALIAS, producer)
                                                break #apago el consumidor
                                                                                            
                                        else: #mi_nivel < enemigo_nivel GANA ENEMIGO
                                            mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos actual a 0
                                            
                                            #me elimino del juego
                                            #JUGADORES_PARTIDA.remove(alias)
                                            JUGADORES_PARTIDA_ALIAS = [tup for tup in JUGADORES_PARTIDA_ALIAS if tup[0] != alias] #nuevas lista = todos menos los que tienen ese alias
                                            
                                            producer.send(topico_partida, kafka_encriptar(f"info@¡'{alias_mapa}' y {celda} han luchado. GANA '{enemigo_alias}'!"))
                                            
                                            #SI SOLO QUEDA 1 JUGADOR DESPUÉS DE QUE ESTE SALGA. AL QUE QUEDE LO DECLARO GANADOR
                                            if len(JUGADORES_PARTIDA_ALIAS) == 1:
                                                terminarPartida(JUGADORES_PARTIDA_ALIAS, producer)
                                                break #apago el consumidor
                    else:
                        if celda == "0":
                            if ciudad_actual != ciudad_movimiento: 
                                setLevel_Clima_Movimiento(alias,ciudad_movimiento,JUGADORES_PARTIDA_ALIAS)
                                                    
                            mapa.setCelda(pos_nueva_x,pos_nueva_y, alias_mapa) #voy a la nueva casilla
                            mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos anterior a 0
                            
                            #actualizo base de datos con su nueva posición
                            jugador_setDBPosNueva(alias,pos_nueva_x,pos_nueva_y)    
                        else:

                            if int(mi_nivel) == int(celda): #EMPATE
                                producer.send(topico_partida, kafka_encriptar(f"info@¡'{alias_mapa}' y un NPC han luchado. EMPATE!"))
                            else:
                                if int(mi_nivel) > int(celda): #GANO YO
                                    if ciudad_actual != ciudad_movimiento: setLevel_Clima_Movimiento(alias,ciudad_movimiento,JUGADORES_PARTIDA_ALIAS)    
                            
                                    mapa.setCelda(pos_nueva_x,pos_nueva_y, alias_mapa) #voy a la casilla del NPC derrotado
                                    mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos anterior a 0
                                    producer.send(topico_partida, kafka_encriptar(f"info@¡'{alias_mapa}' y un NPC han luchado. GANA '{alias_mapa}'!"))
                                    producer.send(topico_partida, kafka_encriptar(f"NPC_eliminado@{pos_nueva_x},{pos_nueva_y}"))            
                                    #actualizo base de datos con su nueva posición
                                    jugador_setDBPosNueva(alias,pos_nueva_x,pos_nueva_y)   
                                    
                                else: #GANA NPC
                                    mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos actual a 0
                                    producer.send(topico_partida, kafka_encriptar(f"info@¡'{alias_mapa}' y un NPC han luchado. GANA el NPC!"))
                                    
                                    #me elimino del juego
                                    #JUGADORES_PARTIDA.remove(alias)
                                    JUGADORES_PARTIDA_ALIAS = [tup for tup in JUGADORES_PARTIDA_ALIAS if tup[0] != alias] #nuevas lista = todos menos los que tienen ese alias

                                    #SI SOLO QUEDA 1 JUGADOR DESPUÉS DE QUE ESTE SALGA. AL QUE QUEDE LO DECLARO GANADOR
                                    if len(JUGADORES_PARTIDA_ALIAS) == 1:
                                        terminarPartida(JUGADORES_PARTIDA_ALIAS, producer)
                                        break #apago el consumidor
            
            #envio el mapa actualizado a todos
            insertar_mapa_en_BaseDatos(mapa) #PRACTICA 3
            insertar_JugadoresPartida_en_BaseDatos(JUGADORES_PARTIDA_ALIAS)#PRACTICA 3
            producer.send(topico_partida, kafka_encriptar(f"jugadores@{JUGADORES_PARTIDA_ALIAS}"))  
            producer.send(topico_partida, kafka_encriptar(f"mapa@{mapa.getArray()}"))
            
        elif "desconectar@" in mensaje:
            #descompongo el mensaje
            mensaje_descompuesto = mensaje.split("@") #desconectar@Alias:{alias}@Player:{MI_ALIAS}") ## salir
            alias = mensaje_descompuesto[1].split(":")[1]
            alias_mapa = mensaje_descompuesto[2].split(":")[1]
            
            #obtengo la pos actual en la base de datos
            pos_actual = jugador_getPosActual(alias).split(",") #jugador_getPosActual devuelve 'x,y'
    
            mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos actual a 0
            insertar_mapa_en_BaseDatos(mapa) #PRACTICA 3
            producer.send(topico_partida, kafka_encriptar(f"mapa@{mapa.getArray()}"))
            producer.send(topico_partida, kafka_encriptar(f"info@¡'{alias}'|'{alias_mapa}' ha salido de la partida!"))
            print(f"El jugador '{alias}'|'{alias_mapa}' ha salido de la partida!")
            JUGADORES_PARTIDA.remove(alias)
            JUGADORES_PARTIDA_ALIAS = [tup for tup in JUGADORES_PARTIDA_ALIAS if tup[0] != alias]
            
            #SI SOLO QUEDA 1 JUGADOR DESPUÉS DE QUE ESTE SALGA. AL QUE QUEDE LO DECLARO GANADOR
            if len(JUGADORES_PARTIDA_ALIAS) == 1:
                terminarPartida(JUGADORES_PARTIDA_ALIAS, producer)
                break #apago el consumidor
                    
        elif "NPC@" in mensaje:
            try:
                print("NPC hace un movimiento.")
                #producer.send(topico_partida, f"NPC@{posActual[0]},{posActual[1]}@{POS_X},{POS_Y}@{nivel}")
                msg = mensaje.split("@")
                posActual = [msg[1].split(",")[0] , msg[1].split(",")[1]]
                posMovimiento = [msg[2].split(",")[0] , msg[2].split(",")[1]]
                mi_nivel = msg[3]
                
                celda = mapa.getCelda(posMovimiento[0], posMovimiento[1])
                if "P" in celda: #he encontrado un player en mi prox movimiento
                    #Busco el nivel del player
                    for player in JUGADORES_PARTIDA_ALIAS:
                        print(f"entro en elfor {player}")
                        if player[1] == celda: #he encontrado al player
                            print("entro en jugador encontrado")
                            nivel_player = player[2].split(":")[1]

                            if int(mi_nivel) > int(nivel_player): #elimino al player
                                
                                alias_player = player[0]
                                
                                mapa.setCelda(posActual[0], posActual[1], "0") #pongo un 0 en la casilla del npc actual
                                mapa.setCelda(posMovimiento[0], posMovimiento[1], mi_nivel) #pongo al npc en la nueva pos  
                                producer.send(topico_partida, kafka_encriptar(f"info@¡'{alias_player}' y un NPC han luchado. GANA EL NPC")) #informo del jugador eliminado                                         

                                #elimino al jugadro de las listas
                                JUGADORES_PARTIDA.remove(alias_player)
                                JUGADORES_PARTIDA_ALIAS = [tup for tup in JUGADORES_PARTIDA_ALIAS if tup[0] != alias_player] #nuevas lista = todos menos los que tienen ese alias
                                
                                if len(JUGADORES_PARTIDA) == 1:
                                    producer.send(topico_partida, kafka_encriptar(f"PARTIDA TERMINADA"))
    
                            if int(mi_nivel) < int(nivel_player): #me eliminan
                                mapa.setCelda(posActual[0], posActual[1], "0") #pongo un 0 en la casilla del npc actual
                                producer.send(topico_partida, kafka_encriptar(f"NPC_eliminado@{posMovimiento[0]},{posMovimiento[1]}"))
                else:
                    mapa.setCelda(posActual[0], posActual[1], "0") #pongo un 0 en la casilla del npc actual
                    mapa.setCelda(posMovimiento[0], posMovimiento[1], mi_nivel) #pongo al npc en la nueva pos  
                    
                insertar_mapa_en_BaseDatos(mapa) #PRACTICA 3
                insertar_JugadoresPartida_en_BaseDatos(JUGADORES_PARTIDA_ALIAS)#PRACTICA 3
                producer.send(topico_partida, kafka_encriptar(f"jugadores@{JUGADORES_PARTIDA_ALIAS}"))  
                producer.send(topico_partida, kafka_encriptar(f"mapa@{mapa.getArray()}"))
                
            except Exception as error:
                print(bg.red + "Excepción ocurrida." + bg.rs)
                traceback.print_exc()

    #Aquí llega cuando se termina la partida                               
    JUGADORES_PARTIDA.clear()
    JUGADORES_PARTIDA_ALIAS.clear()
    producer.send(topico_partida, kafka_encriptar(f"PARTIDA TERMINADA"))
    print(bg.blue + "##################### PARTIDA TERMINADA #####################" + bg.rs)
    print(bg.blue + "La partida ha terminado porque ya no quedan jugadores suficientes o porque no hay ningún jugador enviando mensajes." + bg.rs)

    BorrarPartidaAnterior_en_BaseDatos()


#████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████
#████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████
 
'''
███╗   ███╗███████╗███╗   ██╗██╗   ██╗
████╗ ████║██╔════╝████╗  ██║██║   ██║
██╔████╔██║█████╗  ██╔██╗ ██║██║   ██║
██║╚██╔╝██║██╔══╝  ██║╚██╗██║██║   ██║
██║ ╚═╝ ██║███████╗██║ ╚████║╚██████╔╝
╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ '''                        
PARTIDA_DISPONIBLE = False
PLAYER_RANDOM_POS = False
PLAYER_RANDOM_EC_EF = False

def menu():
    global PARTIDA_DISPONIBLE
    global PLAYER_RANDOM_POS
    global PLAYER_RANDOM_EC_EF
    ans=True
    while ans:
        print ("""
        ######### [MENU] Escoge opción ##########\n 
        1.Nueva partida. 2.Comenzar partida. 3.Parar partida.
        """)
        ans=input("Opción: ") 
        if ans=="1": 
            JUGADORES_PARTIDA.clear()
            PARTIDA_DISPONIBLE = True 
            print(bg.blue + "Partida iniciada. Esperando jugadores..." + bg.rs)
        elif ans=="2":
            PARTIDA_DISPONIBLE = False 
            try:
                comenzarPartida()
            except Exception as error:
                print(bg.red + "Excepción ocurrida." + bg.rs)
                traceback.print_exc()
        elif ans=="3":
            if len(JUGADORES_PARTIDA) > 0:
                print( bg.blue + "Parando partida...." + bg.rs)
                exception_TerminarPartida()
            else:
                print(bg.blue + "No hay ninguna partida para parar." + bg.rs)

        elif ans !="":
            print(bg.blue + " Opción no válida" + bg.rs) 

def exception_TerminarPartida():
    
    try:
        producer = KafkaProducer(bootstrap_servers=[server_kafka],
                    value_serializer=lambda x: 
                    dumps(x).encode('utf-8'))
        
        print(bg.blue + "##################### PARTIDA TERMINADA #####################" + bg.rs)
        producer.send(topico_partida, f"PARTIDA TERMINADA")   
        
    except Exception as error:
        PARTIDA_DISPONIBLE = False
        print(bg.red + "Excepción ocurrida." + bg.rs)
        traceback.print_exc()


''' 
███████╗███╗   ██╗ ██████╗██████╗ ██╗██████╗ ████████╗ █████╗ ██████╗  ██████╗      █████╗ ███████╗███████╗
██╔════╝████╗  ██║██╔════╝██╔══██╗██║██╔══██╗╚══██╔══╝██╔══██╗██╔══██╗██╔═══██╗    ██╔══██╗██╔════╝██╔════╝
█████╗  ██╔██╗ ██║██║     ██████╔╝██║██████╔╝   ██║   ███████║██║  ██║██║   ██║    ███████║█████╗  ███████╗
██╔══╝  ██║╚██╗██║██║     ██╔══██╗██║██╔═══╝    ██║   ██╔══██║██║  ██║██║   ██║    ██╔══██║██╔══╝  ╚════██║
███████╗██║ ╚████║╚██████╗██║  ██║██║██║        ██║   ██║  ██║██████╔╝╚██████╔╝    ██║  ██║███████╗███████║
╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝        ╚═╝   ╚═╝  ╚═╝╚═════╝  ╚═════╝     ╚═╝  ╚═╝╚══════╝╚══════╝                                                                                                       
'''       

#Práctica 3
aes_kafka_KEY = b""

#Crea las claves para usar con el algoritmo de encriptación de mensajes RSA
def crear_clave_AES():
    global aes_kafka_KEY

    #el salt es una combinación de bytes random (necesaria para crear la key)
    salt = b'\x1a\xb3m\xa0\xbf!\xfc\xac6\x7f"\x9f}\xc3\xe0M\xe7\xc4\x94\xc6s\xfc\xa8\x08\xa6C\x19\x9d\x90\xb6\xec\xf3'
    password="vadim" #un password elegido (necesario para crear la key)

    #creo la key
    aes_kafka_KEY = PBKDF2(password,salt,dkLen=32)

    #meto la key dentro de un archivo
    with open("kafka_aes_key.bin", "wb") as f: 
        f.write(aes_kafka_KEY)

    print("Clave de encriptación AES para kafka creada. <kafka_aes_key.bin>")

#Práctica 3
#1-Paso el mensaje a string (porque hacerlo en bytes pide que sea string).
#2-Paso el string a bytes (porque cipher lo requiere en bytes).
#3-Cifro el mensaje.
#4-Paso el mensaje cifrado a una lista (ya que pasándolo a lista es lo único que he visto que luego en el consumidor nos dé la forma correcta)
#5-Paso esa lista a un string (porque producer.send solo envia strings)
def kafka_encriptar(mensaje) -> str:
    
    with open("kafka_aes_key.bin", "rb") as f:
        kafka_aes_key = f.read()

    msg = bytes(str(mensaje).encode())

    cipher = AES.new(kafka_aes_key,AES.MODE_CBC)
    mensaje_encriptado = cipher.encrypt(pad(msg, AES.block_size))

    return str(list(cipher.iv)) + "|@|" + str(list(mensaje_encriptado))

#kafka_desencriptar: Recibe un mensaje en el siguiente formato: IV|@|Mensaje
#1-Con eval paso el string (que en verdad es una lista pero en forma de string) a lista.
#2-COn bytes paso la lista a bytes (porque lo requiere el decrypt).
#3-Obtengo el mensaje y con decode le quito el "b'" que hay al principio del mensaje decodificado.
def kafka_desencriptar(mensaje) -> str:
    
    with open("kafka_aes_key.bin", "rb") as f:
        kafka_aes_key = f.read()
    
    iv = bytes(eval(mensaje.split("|@|")[0].encode()))
    mensaje_encriptado = bytes(eval(mensaje.split("|@|")[1]))

    cipher = AES.new(kafka_aes_key,AES.MODE_CBC, iv = iv)
    return unpad(cipher.decrypt(mensaje_encriptado), AES.block_size).decode() #recibo bytes


## ESTOS 2 MÉTODOS LOS UTILIZO PARA DESENCRIPTAR E INCRIPTAR EL LOGUEO CON SOCKETS
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
'''
███╗   ███╗ █████╗ ██╗███╗   ██╗
████╗ ████║██╔══██╗██║████╗  ██║
██╔████╔██║███████║██║██╔██╗ ██║
██║╚██╔╝██║██╔══██║██║██║╚██╗██║
██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝'''     
PUERTO_OCUPADO=True
def main():
    global PUERTO_OCUPADO
    Thread(target=iniciar_ServidorEngine).start() #Para el logeo de los players
    
    while PUERTO_OCUPADO:
        pass

    ##SOLO SEGUIRÁ POR AQUÍ SI SALE DEL WHILE, Y SALE DEL WHILE SI EL PUERTO NO ESTÁ EJECUTANDOSE

    #PRÁCTICA3: Genero la clave del algoritmo AES de encriptación de mensajes
    crear_clave_AES()
    
    if len(getMapa_en_BaseDatos()) > 0: #se ha encontrado un mapa de una partida sin cerrar (significa que el engine se habia caido)

        ans = ""

        while ans != "S" and ans != "s" and ans != "N" and ans != "n":
            print("¡Se ha encontrado partida sin terminar!. ¿Deseas recuperar la partida? (S/N)")
            ans=input("Opción: ")
            if ans != "S" and ans != "s" and ans != "N" and ans != "n":
                print(">>Opción incorrecta, tienes que escribir o 'S' o 'N' ")
            else:
                break
                
        if ans == "N" or ans == "n": 
            BorrarPartidaAnterior_en_BaseDatos()
            menu()
        else:
            print("PARTIDA RECUPERADA...")
            mapa = Mapa()
            mapa.DeepCopy(getMapa_en_BaseDatos())
            jug = getJUGADORES_PARTIDA_ALIAS_en_BaseDatos()
            print(type(jug))
            jugadores = deepcopy(jug)
            ciudades = deepcopy(getCiudades_en_BaseDatos())

            partida(mapa, jugadores,ciudades)

    else:
        menu()
    
if __name__ == "__main__":
    
    main()

        
