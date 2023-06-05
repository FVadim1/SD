import json
from db import db
from sty import Style, RgbFg
from sty import fg, bg, ef, rs
import random


args_json = json.load(open("args.json"))
max_jugadores = args_json['AA_Engine'][0]['max_jugadores']

#Obtengo la infor del archivo args.json
SERVIDOR_IP = args_json['db'][0]['SERVIDOR_IP']
USUARIO = args_json['db'][0]['USUARIO']
CONTRASENYA = args_json['db'][0]['CONTRASENYA']
BASE_DE_DATOS = args_json['db'][0]['BASE_DE_DATOS']

puerto_escucha = args_json['AA_Engine'][0]['puerto_escucha']
ip_engine = args_json['AA_Engine'][0]['ip']
   
topico_partida = args_json['topicos'][0]['topico_partida']
server_kafka = args_json['otros'][0]['ip_kafka'] + ":"+ args_json['otros'][0]['puerto_kafka']


def terminarPartida(JUGADORES_PARTIDA_ALIAS, producer):
    
    #SI SOLO QUEDA 1 JUGADOR DESPUÉS DE QUE ESTE SALGA. AL QUE QUEDE LO DECLARO GANADOR
    if len(JUGADORES_PARTIDA_ALIAS) == 1:

        alias_ganador = JUGADORES_PARTIDA_ALIAS[0][0]
        aiias_mapa_ganador = JUGADORES_PARTIDA_ALIAS[0][1]
        print(f"Solo queda 1 jugador en el mapa. Ha salido vencedor: {alias_ganador}")
        producer.send(topico_partida, f"info@¡'{alias_ganador}'|'{aiias_mapa_ganador}' ha ganado la partida!") 
        producer.send(topico_partida, f"PARTIDA TERMINADA")

def jugador_getNivel(alias) -> int:
    conexion_db = db()
    nivel=0
    ##ABRO CONEXION CON LA BASE DE DATOS
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):

        #obtengo todos los jugadores de la base de datos
        nivel = conexion_db.getJugador_Nivel(alias) 

        #CIERRO CONEXIÓN       
        conexion_db.closeCommunication()
        
    return nivel

def jugador_addLevel(alias,JUGADORES_PARTIDA_ALIAS):
    conexion_db = db()
    ##ABRO CONEXION CON LA BASE DE DATOS
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):

        #obtengo todos los jugadores de la base de datos y luego modifico el nivel
        nivel = conexion_db.getJugador_Nivel(alias) #me devuelve un string numero
        nivel_nuevo = int(nivel) + 1
        conexion_db.modJugador_Nivel(alias,nivel_nuevo)
        
        #a la lista de jugadores le modifico el nivel nuevo
        index = -1
        for i, v in enumerate(JUGADORES_PARTIDA_ALIAS):
            if v[0] == alias:
                index = i
                break
        if index >= 0:
            alias_mapa = JUGADORES_PARTIDA_ALIAS[index][1]
            JUGADORES_PARTIDA_ALIAS[index] =  (alias,alias_mapa,f"nivel:{nivel_nuevo}")  
        
        #CIERRO CONEXIÓN       
        conexion_db.closeCommunication()  
        return nivel,nivel_nuevo
    
    return -1,-1
    
def getPosNueva(pos_actual, movimiento):
    
    pos_actual_x = int(pos_actual[0])
    pos_actual_y = int(pos_actual[1])
    pos_nueva_x = -1 #valor por defecto
    pos_nueva_y = -1 #valor por defecto
        
    if movimiento == 'W' or movimiento == 'w': #arriba,  -> x disminuye o aumenta si es limitrofe en el norte) 
        pos_nueva_y = pos_actual_y #se queda como está
        if pos_actual_x == 0: #limítrofe arriba
            pos_nueva_x = 19
        else: #no limitrofe
            pos_nueva_x = pos_actual_x - 1 #subo en x    
    else:
        if movimiento == 'S' or movimiento == 's': #abajo
            pos_nueva_y = pos_actual_y #se queda como está
            if pos_actual_x == 19: #limítrofe abajo
                pos_nueva_x = 0
            else: #no limitrofe
                pos_nueva_x = pos_actual_x + 1 #bajo en x
        else:
            if movimiento == 'A' or movimiento == 'a': # izquierda
                pos_nueva_x = pos_actual_x #se queda como está
                if pos_actual_y == 0: #limítrofe izquierdo
                    pos_nueva_y = 19
                else: #no limitrofe
                    pos_nueva_y = pos_actual_y - 1 #izquierda en y
            else:
                if movimiento == 'D' or movimiento == 'd': #derecha
                    pos_nueva_x = pos_actual_x #se queda como está
                    if pos_actual_y == 19: #limítrofe derecho
                        pos_nueva_y = 0
                    else: #no limitrofe
                        pos_nueva_y = pos_actual_y + 1 #derecha en y  
        ##############################[ DIAGONALES ]#########################
                else: 
                    if movimiento == 'Q' or movimiento == 'q': #arriba-izquierda (x disminuye, y disminuye)
                        pos_nueva_x = pos_actual_x - 1
                        pos_nueva_y = pos_actual_y - 1
                        if pos_nueva_x < 0: pos_nueva_x = 19
                        if pos_nueva_y < 0: pos_nueva_y = 19  
                    else:                       
                        if movimiento == 'E' or movimiento == 'e': #arriba-derecha (x disminuye, y aumenta)
                            pos_nueva_x = pos_actual_x - 1
                            pos_nueva_y = pos_actual_y + 1
                            if pos_nueva_x < 0: pos_nueva_x = 19
                            if pos_nueva_y > 19: pos_nueva_y = 0    
                        else:                       
                            if movimiento == 'Z' or movimiento == 'z': #abajo-izquierda (x aumenta, y disminuye)
                                pos_nueva_x = pos_actual_x + 1
                                pos_nueva_y = pos_actual_y - 1
                                if pos_nueva_x > 19: pos_nueva_x = 0
                                if pos_nueva_y < 0: pos_nueva_y = 19 
                            else:
                                if movimiento == 'X' or movimiento == 'x': #abajo-izquierda (x aumenta, y aumenta)
                                    pos_nueva_x = pos_actual_x + 1
                                    pos_nueva_y = pos_actual_y + 1
                                    if pos_nueva_x > 19: pos_nueva_x = 0
                                    if pos_nueva_y > 19: pos_nueva_y = 0
                                else:
                                    pos_nueva_x = pos_actual_x
                                    pos_nueva_y = pos_actual_y
                                    print(bg.red + f"ERROR: La acción para el movimiento '{movimiento}' no está programada, por lo que el jugador no se moverá " + bg.rs)   

    return pos_nueva_x,pos_nueva_y

def jugador_setDBPosNueva(alias,pos_nueva_x,pos_nueva_y):
    
    nueva_pos = str(pos_nueva_x) + "," + str(pos_nueva_y)
    
    ##ABRO CONEXION CON LA BASE DE DATOS
    conexion_db = db()
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):
        conexion_db.modJugador_Posicion(alias,nueva_pos)
        #CIERRO CONEXIÓN       
        conexion_db.closeCommunication()   
    
def jugador_getPosActual(alias) -> str: ##devuelve: 'x,y'
    
    conexion_db = db()
    pos=""
    ##ABRO CONEXION CON LA BASE DE DATOS
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):

        #obtengo todos los jugadores de la base de datos
        pos = conexion_db.getJugador_Posicion(alias) 
        
        if "-1" in pos: print(bg.red + f"ERROR en jugador_getPosActual(), pos:{pos}" + bg.rs)
        #CIERRO CONEXIÓN       
        conexion_db.closeCommunication()
        
    return pos

def jugadoresFromDB():
    conexion_db = db()
    db_jugadores = []
    ##ABRO CONEXION
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):

        #obtengo todos los jugadores de la base de datos
        db_jugadores = conexion_db.getTabla("jugadores") #me devuelve un array 2d

        #CIERRO CONEXIÓN       
        conexion_db.closeCommunication()
        
    return db_jugadores

#le doy una pos a los jugadores
def set_Pos_Random_Jugadores(JUGADORES_PARTIDA):
    
    conexion_db = db()

    ##ABRO CONEXION
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):
        
        posiciones = []
        for player in JUGADORES_PARTIDA:
            x = random.randint(0, 19)
            y = random.randint(0, 19)
            
            #para que no se repitan posiciones en 2 jugadores
            i = 0
            while (x,y) in posiciones:
                print("Hay un jugador en esa posicion, recalculando...")
                x = random.randint(0, 19)
                y = random.randint(0, 19)
                i = i + 1
                if i == 400: 
                    print("Error, todas las casillas están ocupadas.")
                    break
                
            posiciones.append((x,y))    
            conexion_db.modJugador_Posicion(player, f"{x},{y}")

        #CIERRO CONEXIÓN       
        conexion_db.closeCommunication()
      
#le doy a los jugadores los valores de ec y ef
def set_EF_EC_Random_Jugadores(JUGADORES_PARTIDA):
    conexion_db = db()

    ##ABRO CONEXION
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):

        for player in JUGADORES_PARTIDA:
            conexion_db.modJugador_EF(player,random.randint(-10, 10)) 
            conexion_db.modJugador_EC(player,random.randint(-10, 10))  

        #CIERRO CONEXIÓN       
        conexion_db.closeCommunication()

#[LA USO SI JUGADOR CAMBIA DE CIUDAD EN EL MOVIMIENTO]
def setLevel_Clima_Movimiento(alias,ciudad_movimiento,JUGADORES_PARTIDA_ALIAS):
    conexion_db = db()

    ##ABRO CONEXION
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):
        
        temperatura_ciudad = ciudad_movimiento.split(",")[1].replace(')','').replace(' ','')
        
        jugador = conexion_db.getJugador(alias)
        nivel_actual = jugador[2]
        ef = int(jugador[3])
        ec = int(jugador[4])
        
        nivel_resultante = 1
        if int(temperatura_ciudad) >= 25: #usamos Efecto Calor  
            nivel_resultante = nivel_actual + ec   
        else: #(< 0 ) usamos Efecto Frio  
            if int(temperatura_ciudad) <= 10:
                nivel_resultante = nivel_actual + ef
                
        if nivel_resultante < 0: nivel_resultante = 0

        #a la lista de jugadores le modifico el nivel nuevo
        index = -1
        for i, v in enumerate(JUGADORES_PARTIDA_ALIAS):
            if v[0] == alias:
                index = i
                break
        if index >= 0:
            alias_mapa = JUGADORES_PARTIDA_ALIAS[index][1]
            JUGADORES_PARTIDA_ALIAS[index] =  (alias,alias_mapa,f"nivel:{nivel_resultante}")          

        
        print(f"[EFECTOS CLIMA NUEVA CIUDAD] El nivel del jugador '{alias}' pasa de '{nivel_actual}' a '{nivel_resultante}' ")
        conexion_db.modJugador_Nivel(alias,nivel_resultante)

        #CIERRO CONEXIÓN       
        conexion_db.closeCommunication()
        
#[SOLO LA USO AL INICIO DE LA PARTIDA] Calculo el nivel de los jugadores dependiendo del CLIMA en su pos
def setLevel_Clima_JugadoresPos(ciudades,JUGADORES_PARTIDA):
    
    conexion_db = db()

    ##ABRO CONEXION
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):

        #obtengo todos los jugadores de la base de datos
        db_jugadores = conexion_db.getTabla("jugadores") #me devuelve un array 2d
        
        for player in JUGADORES_PARTIDA:
            for db_player in db_jugadores: #(alias, pass, nivel, ef, ec, pos) 
                if db_player[0] == player: #db_player[0] es el alias, [1] es el pass ,etc
                    
                    pos = db_player[5].split(",")
                    pos_x = pos[0]
                    pos_y = pos[1]
                    nivel_actual = db_player[2]
                    ef = int(db_player[3])
                    ec = int(db_player[4])
                    
                    ciudad_elegida = aux_getCiudad(ciudades,int(pos_x),int(pos_y))
                    temperatura_ciudad = ciudad_elegida.split(",")[1].replace(')','').replace(' ','')
                    #print(f"DEBUG:{ciudad_elegida} temperatura: {temperatura}, pos_x:{pos_x}, pos_y:{pos_y}")
                    nivel_resultante = 1
                    if int(temperatura_ciudad) >= 25: #usamos Efecto Calor  
                        nivel_resultante = nivel_actual + ec   
                    else: #(< 0 ) usamos Efecto Frio  
                        if int(temperatura_ciudad) <= 10:
                            nivel_resultante = nivel_actual + ef
                            
                    if nivel_resultante < 0: nivel_resultante = 0
                    
                    print(f"[EFECTOS CLIMA CIUDAD] El nivel del jugador '{db_player[0]}' pasa de '{nivel_actual}' a '{nivel_resultante}' ")
                    conexion_db.modJugador_Nivel(player,nivel_resultante)
                    
                    #print(f"DEBUG: nivel_actual:{nivel_actual},ec:{ec},ef:{ef}, nivel_resultante: {nivel_resultante}")
                        
        #CIERRO CONEXIÓN       
        conexion_db.closeCommunication()

#obtengo la ciudad dependiendo de la pos
def aux_getCiudad(ciudades,pos_x,pos_y):   
    if pos_x >= 0 and pos_x <= 9:
        if pos_y >= 0 and pos_y <= 9:
            return ciudades[0]
        else:
            if pos_y >= 10 and pos_y <= 19:
                return ciudades[1]
    else:

        if pos_x >= 10 and pos_x <= 19:
            if pos_y >= 0 and pos_y <= 9:
                return ciudades[2]
            else:
                if pos_y >= 10 and pos_y <= 19:
                    return ciudades[3]
        else:
            print(bg.red + f"ERROR: La pos del jugador indicada no es correcta. --posX: {pos_x}, --posY:{pos_y}" + bg.rs)
            return ""
    print(bg.red + f"ERROR: error al obtener ciudad del jugador.--Pos_x:{pos_x},--Pos_y:{pos_y}" + bg.rs)
    return ""
    