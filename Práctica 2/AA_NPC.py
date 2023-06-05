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

import threading
from threading import Thread

import time
import random

CBOLD     = '\33[1m'
CEND = '\033[0m'

args_json = json.load(open("args.json"))
topico_partida = args_json['topicos'][0]['topico_partida']
server_kafka = args_json['otros'][0]['ip_kafka'] + ":"+ args_json['otros'][0]['puerto_kafka']
productor_timeout = args_json['AA_Player'][0]['consumidor_timeout']
  
fg.orange = Style(RgbFg(255, 150, 50))
fg.verde1 = Style(RgbFg(105, 197, 174))

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


PARTIDA_TERMINADA = False           
def consumidor():
    
    global PARTIDA_TERMINADA
    global POS_X
    global POS_Y
    
    consumer = KafkaConsumer(
        topico_partida,
        bootstrap_servers=[server_kafka],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        value_deserializer=lambda x: loads(x.decode('utf-8')),
        consumer_timeout_ms=productor_timeout
        )
    
    #Vuelvo a escuchar el tópico para ver si hay alguna partida detectada
    for message in consumer: 
        if "PARTIDA TERMINADA" in message.value:
            PARTIDA_TERMINADA = True
            print("La partida se ha terminado")
            break
        
        if "NPC_eliminado@" in message.value: #me eliminaron de la partida
            #Obtengo la pos del eliminado
            posMovimiento = message.value.split("@")[1].split(",")     #NPC_eliminado@{posMovimiento}
            #Miro es el eliminado es mi pos
            print(f"POS_X_eliminado:{posMovimiento[0]}, POS_Y_eliminado:{posMovimiento[1]}")
            if posMovimiento[0] == str(POS_X) and posMovimiento[1] == str(POS_Y):
                PARTIDA_TERMINADA = True
                print("Te han eliminado de la partida.")
                break           
                
                
#El npc una vez abierta la consola, se convierte en consumidor directamente y esperar a recibir algún
#mensaje en el tópico donde se produce la partida. Si recibe algún mensaje entonces esta instancia del NPC
# envía un mensaje por el topico en forma de NPC@ de que se va a unir a la partida y que se le incluya.
#La idea es que se puedan abrir instancia de npc a lo largo de la partida y todos se meterán dentro del
#juego que se está jugando
PARTIDA_DETECTADA = False
POS_X = ""
POS_Y = ""
def npc():
    
    global PARTIDA_DETECTADA    
    global PARTIDA_TERMINADA
    global POS_X
    global POS_Y
    
    consumer = KafkaConsumer(
        topico_partida,
        bootstrap_servers=[server_kafka],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        value_deserializer=lambda x: loads(x.decode('utf-8')),
        consumer_timeout_ms=productor_timeout
        )
    
    print("NPC creado. Esperando partida...")
    #El npc se pone a escuchar si hay alguna partida empezada
    for message in consumer:
                    
        if "inicio@" in message.value or "mapa@" in message.value or "info@" in message.value or "jugadores@" in message.value:
            PARTIDA_DETECTADA = True
            print("Partida detectada.")
            break #dejo de escuchar al topico
        
        
    if PARTIDA_DETECTADA:
        print("Uniéndome a la partida...")
        #Pongo el consumidor en marcha
        Thread(target=consumidor).start()
        
        #creo el productor de movimientos
        producer = KafkaProducer(bootstrap_servers=[server_kafka],
                        value_serializer=lambda x: 
                        dumps(x).encode('utf-8'))

        #busco un lugar de inicio random y mi nivel
        POS_X = random.randrange(0,19)
        POS_Y = random.randrange(0,19)
        nivel = random.randrange(1,9)
        #Comiento a enviar mis movimientos al engine mientras no se haya terminada la partida
        while True:
            if(PARTIDA_TERMINADA): break
            
            movimiento = random.choice(["W", "S", "A", "D", "Q", "E", "Z", "X"]) #selecciono un movimiento random
            posActual = [POS_X,POS_Y]
            POS_X,POS_Y = getPosNueva(posActual, movimiento) #pos_Movimiento
            #NPC @ pos_Antigua @ pos_Movimiento @ Nivel
            producer.send(topico_partida, f"NPC@{posActual[0]},{posActual[1]}@{POS_X},{POS_Y}@{nivel}")
            print(f"Movimiento:{POS_X},{POS_Y}")
  
            time.sleep(5) #me quedo dormido 2 sec antes de realizar otro movimiento
            

    
if __name__=="__main__":
    try:
        npc()
    except KeyboardInterrupt:  
        sys.exit(0)