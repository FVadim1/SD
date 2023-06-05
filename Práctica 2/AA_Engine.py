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

        
#Para detectar que un servicio para con ctrl + z ####################
import signal
def handler(signum, frame):
    print( bg.red + '\n ####### [AVISO: Ejecución de AA_Engine interrumpida con CTRL+Z] #######' + bg.rs)
    if len(JUGADORES_PARTIDA) > 0:
        exception_TerminarPartida()
    sys.exit(0)

signal.signal(signal.SIGTSTP, handler)
########################################################

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

args_json = json.load(open("args.json"))
MAX_JUGADORES = args_json['AA_Engine'][0]['max_jugadores']
consumidor_timeout = args_json['AA_Engine'][0]['consumidor_timeout']


############################################################################
####################### [Servidor socket AA_Engine]  #######################

puerto_escucha = args_json['AA_Engine'][0]['puerto_escucha']
ip_engine = args_json['AA_Engine'][0]['ip']
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
JUGADORES_PARTIDA = []


def handle_Engine_Client(conn, addr):
    global JUGADORES_PARTIDA
    while True:
        
        msg_length = conn.recv(64).decode('utf-8')
        
        if msg_length:
            
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode('utf-8')
            
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
                                            conn.send(f"Datos de login correctos.".encode('utf-8'))           
                                            JUGADORES_PARTIDA.append(datos['alias']) #añado al jugador a la cola de espera
                                            print(f"[AA_Engine SERVER] El jugador '{datos['alias']}' se ha unido a la partida.")
                                            
                                            ################### PARA COMENZAR LA PARTIDA SI SE LLEGA A MAX_JUGADORES #####################
                                            if len(JUGADORES_PARTIDA) == MAX_JUGADORES:
                                                try:
                                                    comenzarPartida()
                                                except Exception as error:
                                                    if "NoBrokerAvailable":
                                                        print(bg.red + "ERROR: Error en kafka. ¿Está funcionando?" + bg.rs)
                                                    else:                                                
                                                        print("Excepción ocurrida a la hora de comenzar partida. En el handle client del servidor.")
                                                        print(error)       
                                        else:
                                            conn.send(f"ERROR: Datos de login incorrectos o el jugador con ese alias no existe.".encode('utf-8'))
                                    else:
                                        print("Un jugador con el mismo alias ha intentado acceder al juego. Se le ha denegado el acceso.")
                                        conn.send(f"ERROR: Ya existe un jugador con ese alias en la partida.".encode('utf-8'))
                                else:
                                    print(f"Jugador intentó unirse a la partida pero no hay ninguna disponible.")
                                    conn.send(f"ERROR: No hay ninguna partida disponible.".encode('utf-8'))   
                            
                                ##CIERRO CONEXIÓN
                                conexion_db.closeCommunication()
                            else:
                                conn.send(f"ERROR: No se ha podido establecer conexión con la base de datos".encode('utf-8'))
                        else:
                            print("Jugador intentó unirse pero se ha alcanzado el máximo de jugadores")
                            conn.send(f"ERROR: se alcanzó el máximo de jugadores de la partida.".encode('utf-8'))   

            if msg == "Desconectar":
                conn.send(f"[Socket cerrado]. Te has desconectado de AA_Engine.".encode('utf-8'))
                conn.close()
                break
         
def iniciar_ServidorEngine():
    
    try:
        direccion = (ip_engine, puerto_escucha)
        server.bind(direccion)
        server.listen()
        print(f"\n [AA_Engine SERVER] Servidor a la escucha en {direccion} \n")

        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_Engine_Client, args=(conn, addr)) #crea un thread para el cliente en cuestion (cada uno tiene el suyo)
            thread.start()
    except Exception as error:
        if "Errno 98" in str(error):
            print("ERROR: El puerto que usas ya está ocupado por alguien más. Servidor Engine NO inicializado.")
        else:
            print(error)


############################################################################
######################## [Conexión con AA_Weather] #########################

def send_To_AA_Weather(msg):
    message = msg.encode('utf-8')
    msg_length = len(message)
    send_length = str(msg_length).encode('utf-8')
    send_length += b' ' * (64 - len(send_length))
    client.send(send_length)
    client.send(message)
    
def connect_To_AA_Weather(): #Obtengo ciudad random con cada conexión
    ciudades = []
    try:
        ip_weather = args_json['AA_Weather'][0]['ip']
        puerto_a_conectar = args_json['AA_Weather'][0]['puerto_escucha']
        direccion = (ip_weather, puerto_a_conectar)
        
        client.connect(direccion)
        #print (f"Establecida conexión a AA_Weather")
        
        client.settimeout(3) #para que no se quede esperando respuesta infinitamente
        # Obtengo 4 ciudades
        for i in range(4):
            send_To_AA_Weather("Dame ciudad")
            server_response = client.recv(2048).decode('utf-8')
            #print("Recibo del Servidor: ", server_response)
            ciudades.append(server_response)

        ## MANDO MENSAJE PARA DESCONECTARME
        send_To_AA_Weather("Desconectar")
        #print("AA_Engine desconectado de AA_Weather")

        client.close()
    except Exception as error:
        if "Errno 111" in str(error):
            print("ERROR: El servidor de AA_Weather no está funcionando.")
        else:
            print(error)
    
    return ciudades
    
############################################################################
    
   
topico_partida = args_json['topicos'][0]['topico_partida']
server_kafka = args_json['otros'][0]['ip_kafka'] + ":"+ args_json['otros'][0]['puerto_kafka']

def comenzarPartida():
    
    global JUGADORES_PARTIDA
    
    if len(JUGADORES_PARTIDA) > 1:
        PARTIDA_DISPONIBLE = False #bloqueo que se puedan meter mas players
        
        ##### FALTA DECLARAR UNA LISTA CON CIUDADES POR DEFECTO POR SI EL WHEATER NO FUNCIONA ###
        ciudades = []
        
        try:
            ciudades = connect_To_AA_Weather()
        except Exception as error:
            print("Error al conectares a AA_Weather.")
        
        if len(ciudades) < 4:
            ciudades = ["('Tokio', 15)", "('Sidney', 32)", "('Paris', 19)", "('Pekin', 25)"]
            
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
        
        db_jugadores = jugadoresFromDB() #muestro a los jugadores ya con el nivel modificado
        print(db_jugadores)

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
            
        print(f"JUGADORES_PARTIDA_ALIAS: {JUGADORES_PARTIDA_ALIAS}")
        
        print("--------------------MAPA INICIAL DE LA PARTIDA--------------------")
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
        producer.send(topico_partida, f"inicio@{JUGADORES_PARTIDA_ALIAS}")
        ##enviar a cada jugador el alias del mapa suyo
        producer.send(topico_partida, f"mapa@{mapa.getArray()}")  
        
        for message in consumer:

            if "movimiento@" in message.value: #algun player envia su movimiento
                #print(message.value)
                #leo el mensaje y lo proceso
                mensaje_descompuesto = message.value.split("@") #movimiento@Alias:testplayer@Player:@Movimiento:W
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
                    producer.send(topico_partida, f"mapa@{mapa.getArray()}")  
                    producer.send(topico_partida, f"info@¡'{alias}'|'{alias_mapa}' ha muerto a causa de una mina!")
                    print(f"El jugador '{alias}'|'{alias_mapa}' pisó una MINA. Ha sido eliminado.")
                    JUGADORES_PARTIDA.remove(alias)
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
                        producer.send(topico_partida, f"info@¡'{alias}'|'{alias_mapa}' gana un nivel ({nivel}->{nivel_nuevo})!")
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
                                            producer.send(topico_partida, f"info@¡'{alias_mapa}' y '{celda}' han luchado. EMPATE!")
                                        else:
                                            if mi_nivel > enemigo_nivel: #GANO YO
                                                if ciudad_actual != ciudad_movimiento: setLevel_Clima_Movimiento(alias,ciudad_movimiento,JUGADORES_PARTIDA_ALIAS)

                                                mapa.setCelda(pos_nueva_x,pos_nueva_y, alias_mapa) #voy a la casilla del enemigo derrotado
                                                mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos anterior a 0
                                                producer.send(topico_partida, f"info@¡'{alias_mapa}' y {celda} han luchado. GANA '{alias_mapa}'!")                                           
                                                
                                                #elimino al jugadro contrario del las listas
                                                JUGADORES_PARTIDA.remove(enemigo_alias)
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
                                                JUGADORES_PARTIDA.remove(alias)
                                                JUGADORES_PARTIDA_ALIAS = [tup for tup in JUGADORES_PARTIDA_ALIAS if tup[0] != alias] #nuevas lista = todos menos los que tienen ese alias
                                                
                                                producer.send(topico_partida, f"info@¡'{alias_mapa}' y {celda} han luchado. GANA '{enemigo_alias}'!")
                                                
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
                                    producer.send(topico_partida, f"info@¡'{alias_mapa}' y un NPC han luchado. EMPATE!")
                                else:
                                    if int(mi_nivel) > int(celda): #GANO YO
                                        if ciudad_actual != ciudad_movimiento: setLevel_Clima_Movimiento(alias,ciudad_movimiento,JUGADORES_PARTIDA_ALIAS)    
                                
                                        mapa.setCelda(pos_nueva_x,pos_nueva_y, alias_mapa) #voy a la casilla del NPC derrotado
                                        mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos anterior a 0
                                        producer.send(topico_partida, f"info@¡'{alias_mapa}' y un NPC han luchado. GANA '{alias_mapa}'!")
                                        producer.send(topico_partida, f"NPC_eliminado@{pos_nueva_x},{pos_nueva_y}")               
                                        #actualizo base de datos con su nueva posición
                                        jugador_setDBPosNueva(alias,pos_nueva_x,pos_nueva_y)   
                                        
                                    else: #GANA NPC
                                        mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos actual a 0
                                        producer.send(topico_partida, f"info@¡'{alias_mapa}' y un NPC han luchado. GANA el NPC!")
                                        
                                        #me elimino del juego
                                        JUGADORES_PARTIDA.remove(alias)
                                        JUGADORES_PARTIDA_ALIAS = [tup for tup in JUGADORES_PARTIDA_ALIAS if tup[0] != alias] #nuevas lista = todos menos los que tienen ese alias

                                        #SI SOLO QUEDA 1 JUGADOR DESPUÉS DE QUE ESTE SALGA. AL QUE QUEDE LO DECLARO GANADOR
                                        if len(JUGADORES_PARTIDA_ALIAS) == 1:
                                            terminarPartida(JUGADORES_PARTIDA_ALIAS, producer)
                                            break #apago el consumidor
                
                #envio el mapa actualizado a todos
                producer.send(topico_partida, f"mapa@{mapa.getArray()}")
                producer.send(topico_partida, f"jugadores@{JUGADORES_PARTIDA_ALIAS}")  
                
            elif "desconectar@" in message.value:
                #descompongo el mensaje
                mensaje_descompuesto = message.value.split("@") #desconectar@Alias:{alias}@Player:{MI_ALIAS}") ## salir
                alias = mensaje_descompuesto[1].split(":")[1]
                alias_mapa = mensaje_descompuesto[2].split(":")[1]
                
                #obtengo la pos actual en la base de datos
                pos_actual = jugador_getPosActual(alias).split(",") #jugador_getPosActual devuelve 'x,y'
     
                mapa.setCelda(int(pos_actual[0]),int(pos_actual[1]), "0") #pongo mi pos actual a 0
                producer.send(topico_partida, f"mapa@{mapa.getArray()}")  
                producer.send(topico_partida, f"info@¡'{alias}'|'{alias_mapa}' ha salido de la partida!")
                print(f"El jugador '{alias}'|'{alias_mapa}' ha salido de la partida!")
                JUGADORES_PARTIDA.remove(alias)
                JUGADORES_PARTIDA_ALIAS = [tup for tup in JUGADORES_PARTIDA_ALIAS if tup[0] != alias]
                
                #SI SOLO QUEDA 1 JUGADOR DESPUÉS DE QUE ESTE SALGA. AL QUE QUEDE LO DECLARO GANADOR
                if len(JUGADORES_PARTIDA_ALIAS) == 1:
                    terminarPartida(JUGADORES_PARTIDA_ALIAS, producer)
                    break #apago el consumidor
                      
            elif "NPC@" in message.value:
                try:
                    print("NPC hace un movimiento.")
                    #producer.send(topico_partida, f"NPC@{posActual[0]},{posActual[1]}@{POS_X},{POS_Y}@{nivel}")
                    msg = message.value.split("@")
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
                                    producer.send(topico_partida, f"info@¡'{alias_player}' y un NPC han luchado. GANA EL NPC") #informo del jugador eliminado                                         

                                    #elimino al jugadro de las listas
                                    JUGADORES_PARTIDA.remove(alias_player)
                                    JUGADORES_PARTIDA_ALIAS = [tup for tup in JUGADORES_PARTIDA_ALIAS if tup[0] != alias_player] #nuevas lista = todos menos los que tienen ese alias
                                    
                                    if len(JUGADORES_PARTIDA) == 1:
                                        producer.send(topico_partida, f"PARTIDA TERMINADA")
        
                                if int(mi_nivel) < int(nivel_player): #me eliminan
                                    mapa.setCelda(posActual[0], posActual[1], "0") #pongo un 0 en la casilla del npc actual
                                    producer.send(topico_partida, f"NPC_eliminado@{posMovimiento[0]},{posMovimiento[1]}")
                    else:
                        mapa.setCelda(posActual[0], posActual[1], "0") #pongo un 0 en la casilla del npc actual
                        mapa.setCelda(posMovimiento[0], posMovimiento[1], mi_nivel) #pongo al npc en la nueva pos  
                        
                        
                    producer.send(topico_partida, f"mapa@{mapa.getArray()}")
                    
                except Exception as error:
                    print(">>>>>>>>>>>>>>>>>>>>>>Excepción ocurrida en el movimiento del npc.")
                    print(error)
                           
        JUGADORES_PARTIDA.clear()
        JUGADORES_PARTIDA_ALIAS.clear()
        producer.send(topico_partida, f"PARTIDA TERMINADA")
        print(bg.blue + "##################### PARTIDA TERMINADA #####################" + bg.rs)
        print(bg.blue + "La partida ha terminado porque ya no quedan jugadores suficientes o porque no hay ningún jugador enviando mensajes." + bg.rs)
          
    else:
        print( bg.red + "Error. No hay jugadores suficientes" + bg.rs)
    
######################### MAIN ##########################
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
                print(bg.red + "Excepción ocurrida a la hora de comenzar partida. En el menú" + bg.rs)
                print(error)
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
        if "NoBrokerAvailable":
            print(bg.red + "ERROR: Error en kafka. ¿Está funcionando?" + bg.rs)
        else:
            print(error)

def main():

    Thread(target=iniciar_ServidorEngine).start() #Para el logeo de los players

    menu()
    #connect_To_AA_Weather()
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        
        if len(JUGADORES_PARTIDA) > 0:
            exception_TerminarPartida()

        print( bg.red + '\n ####### [AVISO: Ejecución de AA_Engine interrumpida con CTRL+C] #######' + bg.rs)
        sys.exit(0)
    except Exception as error:
        pass
        
