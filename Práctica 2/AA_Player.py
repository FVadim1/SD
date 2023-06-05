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
import keyboard
import random

import threading
from threading import Thread
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

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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


def send_To_Server(msg):
    message = msg.encode('utf-8')
    msg_length = len(message)
    send_length = str(msg_length).encode('utf-8')
    send_length += b' ' * (64 - len(send_length))
    client.send(send_length)
    client.send(message)
   
##CONEXIÓN A SERVIDOR AA_REGISTRY 
def connnect_to_Registry(): 
    
    direccion = (ip_AA_Registry, puerto_escucha_AA_Registry)
    
    client.connect(direccion)
    print (f"Establecida conexión a AA_registry")
    
    mensaje_crear_perfil = {"alias":"testplayer", "password":"testpassword","nivel":1,"ef":1,"ec":1,"posicion":1}
    json_mensaje = json.dumps(mensaje_crear_perfil)
    
    send_To_Server("crear_perfil" + "@" + json_mensaje)
    
    server_response = client.recv(2048).decode('utf-8')
    print(server_response)
    
   
    #send_To_Registry("editar_perfil")
 
    ## MANDO MENSAJE PARA DESCONECTARME
    send_To_Server("Desconectar")
    print("Me he desconectado de AA_Registry")

    client.close()
  
fg.orange = Style(RgbFg(255, 150, 50))
fg.verde1 = Style(RgbFg(105, 197, 174))
##CONEXIÓN A SERVIDOR AA_ENGINE
def connnect_to_Engine(): 
    
    # ME CONECTO POR SOCKETS A ENGINE PARA LOGEARME
    direccion = (ip_AA_Engine, puerto_escucha_AA_Engine)
    
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
    
    send_To_Server("login" + "@" + json_mensaje)

    client.settimeout(3) #para que no se quede esperando respuesta infinitamente
    server_response = client.recv(2048).decode('utf-8')

    ## MANDO MENSAJE PARA DESCONECTARME
    send_To_Server("Desconectar")
    client.close()
    #print("Desconectado del servidor.")

    if "Datos de login correctos" in server_response: #LOGIN CORRECTO
        
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
        print(server_response)
  
################################ CONSUMIDOR ########################################


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
            enable_auto_commit=True,
            value_deserializer=lambda x: loads(x.decode('utf-8')),
            consumer_timeout_ms=consumidor_timeout
            )
        
        for message in consumer:
            
            if "PARTIDA TERMINADA" in message.value:
                print(bg.red + "La partida fué suspendida por AA_Engine o el servidor se ha caido." + bg.rs)
                ELIMINADO = True
                break #salgo del consumidor (partida)
                        
            if "inicio@" in message.value:
                
                print(bg.blue + "################################### COMIENZA LA PARTIDA ###################################" + bg.rs)
                string_players = message.value.split("@")[1] #recibo una lista de tuplas: [(alias,alias_mapa),etc]
                print(bg.black + fg.orange + f"JUGADORES PARTIDA: {string_players}" + fg.rs + bg.rs)
                LISTA_JUGADORES = eval(string_players)
                for player in LISTA_JUGADORES:
                    if player[0] == alias:
                        MI_ALIAS = player[1]
                        MI_NIVEL = player[2]
                        print(bg.black + fg.orange + f"Soy el jugador '{MI_ALIAS}', Mi nivel es: {MI_NIVEL}"  + fg.rs + bg.rs)
            
            elif "mapa@" in message.value:
                
                if i == 0: 
                    print_comoMoverJUgador()
                
                mapa.DeepCopy(eval(message.value.split("@")[1]))
                print(bg.blue + "-----------------------MAPA DE LA PARTIDA--------------------------" + bg.rs)
                print(mapa.getMapa(MI_ALIAS))
                print(bg.blue + "------------------------------------------------------------------"+ bg.rs)
                
                i = i + 1
            elif "info@" in message.value:
                msg = message.value.split("@")[1]
                
                if "mina" in message.value and f"{alias}" in message.value:
                    print(bg.red +CBOLD+ "---------------------------HAS MUERTO A CAUSA DE UNA MINA-------------------------------" +bg.rs + CEND)
                    print(bg.red +CBOLD + "---------------------------TE HAN ELIMINADO DE LA PARTIDA-------------------------------" +bg.rs + CEND)
                    ELIMINADO = True
                    break #salgo del consumidor (partida)
                if "salido" in message.value and f"{alias}" in message.value:
                    print(bg.red +CBOLD+ "-------------------------------HAS SALIDO DE LA PARTIDA-------------------------------" +bg.rs + CEND)
                    ELIMINADO = True
                    break #salgo del consumidor (partida)
                
                if "ha ganado la partida" in message.value and f"{alias}" in message.value:
                    print(bg.green +CBOLD+ "-------------------------------HAS GANADO LA PARTIDA-------------------------------" +bg.rs + CEND)
                    ELIMINADO = True
                    break #salgo del consumidor (partida)
                if "han luchado" in message.value:
                    print(msg)
                    if MI_ALIAS in message.value: #he luchado con alguien yo
                        if "EMPATE" not in message.value: #SI NO HAY EMPATE
                            if f"GANA '{MI_ALIAS}'" in message.value: #SI GANO YO
                                print("¡Gano yo el duelo!")
                            else: #SI NO GANO YO
                                print(bg.red +CBOLD+ "---------------------------HAS MUERTO A CAUSA DE UN DUELO-------------------------------" +bg.rs + CEND)
                                print(bg.red +CBOLD + "---------------------------TE HAN ELIMINADO DE LA PARTIDA-------------------------------" +bg.rs + CEND)
                                ELIMINADO = True
                                break #salgo del consumidor (partida)
                        else: # SI HEMOS EMPATADO
                            print("¡ He luchado pero hemos empatado !")

            #f"info@¡'{alias_ganador}'|'{aiias_mapa_ganador}' ha ganado la partida!")
            elif "jugadores@" in message.value:
                msg = message.value.split("@")[1]
                LISTA_JUGADORES = eval(msg)
                print(bg.blue +f"Jugadores: {msg}" + bg.rs)
                
    except Exception as error:
        
        if "NoBrokerAvailable":
            print(bg.red + "ERROR: Error en kafka. ¿Está funcionando?" + bg.rs)

        else:
            print(bg.red + "Excepción ocurrida a la hora de unirse a la partida que fué iniciada por el Engine." + bg.rs)
            print(error)
            
        
    
    #Aquí solo llega si sale del consumidor (por los mensajes o por el timeout del consumidor)
    print(bg.blue + "Te has salido del juego. O porque se ha terminado o porque tarda mucho en responder el servidor." + bg.rs)
    ELIMINADO = True 
    
################################ PRODUCTOR ########################################


def productor(alias) -> None:
    global ELIMINADO 
    global MI_ALIAS
    producer = KafkaProducer(bootstrap_servers=[server_kafka],
                    value_serializer=lambda x: 
                    dumps(x).encode('utf-8'))
          
    op=""
    i : int = 0
    while op!= "X":
          
        if i > 0: 
            print_comoMoverJUgador()
            
        op= input()
        if ELIMINADO : break #cuando nos eliminan nos salimos del menú de juego
        if op in ["w","W","s","S","a","A","d","D","q","Q","e","E","z","Z","x","X","salir","SALIR"]:
            
            if op == "salir" or op == "SALIR": 
                producer.send(topico_partida,f"desconectar@Alias:{alias}@Player:{MI_ALIAS}") ## salir
                ELIMINADO = True
                LISTA_JUGADORES.clear()
                MI_ALIAS = ""
                break
            else: producer.send(topico_partida,f"movimiento@Alias:{alias}@Player:{MI_ALIAS}@Movimiento:{op}") ## mover 
        i = i + 1
    
def print_comoMoverJUgador():
    print("\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("Como mover al jugador: ")
    print("W->arriba, S->abajo, A->izquierda, D->derecha, Q->arriba-izquierda, E->arriba-derecha, Z->abajo-izquierda, X->abajo-derecha; salir-> Salir del juego")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    

#######MENUS DE REGISTRO Y EDICION
def register():
    print("REGISTRO DE USUARIO")
    posX=posY=-1
    op="N"
    
    while op=="N":
        print("Introduce tu alias:")
        alias=input()
        print("Introduce tu contraseña:")
        password=input()
        
        print("Compruebe sus datos: ")
        print("Alias: "+str(alias)+" Contraseña: "+str(password))
        op="A"
        while op!="N" and op!="S" and op!="n" and op!="s":
            print("S/N")
            op=input()
            if op=="S" or op=="s":
                #connect_to_Registry()
                direccion = (ip_AA_Registry, puerto_escucha_AA_Registry)
                client.connect(direccion)
                #print("llega a conectarse con registry")
                posX = random.randrange(0,19)
                posY = random.randrange(0,19)
                ef_ = random.randrange(-10,10)
                ec_ = random.randrange(-10,10)
                pos = str(posX) + "," + str(posY)
                mensaje_crear_perfil = {f"alias":alias, "password":password,"nivel":1,"ef":ef_,"ec":ec_,"posicion":pos}
                json_mensaje = json.dumps(mensaje_crear_perfil)
                send_To_Server("crear_perfil" + "@" + json_mensaje)
                server_response = client.recv(2048).decode('utf-8')
                print(server_response)
                
                send_To_Server("Desconectar")
                client.close()

def edit_profile():
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
            print("Es correcto?(S/N):")
            print("La nueva contraseña es: " + newPassword)
            correcto=input()
            if(correcto=="S" or correcto=="s"):
                #connect_to_Registry()
                direccion = (ip_AA_Registry, puerto_escucha_AA_Registry)
                client.connect(direccion)

                mensaje_editar_perfil = {f"alias":alias, "password":newPassword}
                json_mensaje = json.dumps(mensaje_editar_perfil)
                #print(json_mensaje)
                send_To_Server("editar_perfil" + "@" + json_mensaje)
                
                server_response = client.recv(2048).decode('utf-8')
                print(server_response)
                
                send_To_Server("Desconectar")
                client.close()

def menu():
    option = 0
    print("¡BIENVENIDO AL JUEGO!")
    while option != 1 and option != 2 and option != 3:
        print("Seleccione una opcion:")
        print("\n")
        print("1. Crear perfil")
        print("2. Editar un perfil existente")
        print("3. Unirse a la partida")
        option = int(input())
        if option == 1:
            register() #cambiar al caso de registro
        elif option == 2:
            edit_profile() #cambiar al casi de edición
        elif option == 3:
            connnect_to_Engine()
        else:
            print("ERROR. Seleccione una opción existente.")

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
        pass

