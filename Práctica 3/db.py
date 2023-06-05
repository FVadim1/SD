import psycopg2
from sqlobject import *
import json
import traceback

from sty import Style, RgbFg
from sty import fg, bg, ef, rs

args_json = json.load(open("args.json")) #cargo el archivo de args.json
#Obtengo la infor del archivo args.json
SERVIDOR_IP = args_json['db'][0]['SERVIDOR_IP']
USUARIO = args_json['db'][0]['USUARIO']
CONTRASENYA = args_json['db'][0]['CONTRASENYA']
BASE_DE_DATOS = args_json['db'][0]['BASE_DE_DATOS']

import bcrypt #para la encriptación de contraseñas con hash

class db:
    #Constructor
    def __init__(self):
        pass
    
    #Abrir comunicación con la base de datos
    def openCommunication(self,ip,user,passwd,db):
        try:
            self.conn = psycopg2.connect(
                database=db,
                user=user,
                password=passwd,
                host=ip
            )
            #Open cursor to perform database operations
            self.cur = self.conn.cursor()
            
            #print("Conexión con la base de datos establecida. \n")
           
            return True
        except Exception as error:
            print("No es posible conectarse a la base de datos. ¿Está activa? \n" )
            return False #No hay comunicación con la base de datos
    
    #Ceerar comunicación con la base de datos
    def closeCommunication(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()
        
    def getTabla(self, tabla):
        try:
            self.cur.execute(f"SELECT * FROM {tabla} ")
            rows = self.cur.fetchall()
            return rows
        except Exception as error:
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            print("#######[Inicio excepción]#######")
            print("Excepcion ocurrida a la hora de obtener Tabla: ")
            print(error)
            print("#######[Fin excepción]#######")
            return []  

########## [CREACIÓN DE TABLAS] ##########  

    def creaTabla_Jugadores(self):
        try:
            self.cur.execute(
                """CREATE TABLE IF NOT EXISTS 
                            jugadores 
                            (
                                 alias varchar(20) PRIMARY KEY,
                                 password varchar(1000) NOT NULL,
                                 nivel int NOT NULL check (nivel >= 0),
                                 ef int NOT NULL check (ef between -10 and 10),
                                 ec int NOT NULL check (ec between -10 and 10), 
                                 posicion varchar(5) NOT NULL 
                            )"""
            )
            self.conn.commit() #guardo la info
            print("Tabla 'jugadores' creada.")
            
        except Exception as error:
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            print(bg.red + "Excepción ocurrida" + bg.rs)
            print(error)

            
    def creaTabla_Ciudades(self):
        try:
            self.cur.execute(
                """CREATE TABLE IF NOT EXISTS 
                            ciudades 
                            (
                                 ciudad varchar(50) PRIMARY KEY,
                                 temperatura int NOT NULL check (temperatura between -273 and 60)
                            )"""
            )
            self.conn.commit() #guardo la info
            print("Tabla 'ciudades' creada.")
            
        except Exception as error:
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            print("#######[Inicio excepción]#######")
            print("Excepcion ocurrida a la hora de crear tabla CIUDADES: ")
            print(error)
            print("#######[Fin excepción]#######")
            
########## [INSERTAR] ##########    
    #AA_Registry
    def insertar_Jugador(self, alias,password,nivel,ef,ec,posicion):
        try:
            hashed_password = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
            formato_hashed_password = str(list(hashed_password))
                               
            self.cur.execute(f"""insert into jugadores ("alias","password","nivel","ef","ec","posicion") values ('{alias}','{formato_hashed_password}',{nivel},{ef},{ec},'{posicion}')""")
            self.conn.commit() #guardo la info
            print(f"Jugador {alias} insertado")
            return True
        except Exception as error:
            
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            if "unique constraint" in str(error):
                print(f"ERROR: No es posible insertar jugador. El jugador con el alias '{alias}' ya existe")
            else:
                print("#######[Inicio excepción]#######")
                print(error)
                print("#######[Fin excepción]#######")
            return False
        
    #AA_Wheater
    def insertar_Ciudad(self, ciudad,temperatura):
        try:
            self.cur.execute(f"""insert into ciudades ("ciudad","temperatura") values ('{ciudad}','{temperatura}')""")
            self.conn.commit() #guardo la info
            print(f"Ciudad '{ciudad}' insertada.")
            return True
        except Exception as error:
            
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            if "unique constraint" in str(error):
                print(f"ERROR: No es posible insertar ciudad. La ciudad con el nombre '{ciudad}' ya existe.")
            else:
                print("#######[Inicio excepción]#######")
                print(error)
                print("#######[Fin excepción]#######")
            return False   
   
########## [MODIFICAR] ##########                  
    def modJugador_Password(self,alias,password):
        try:
            
            hashed_password = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
            formato_hashed_password = str(list(hashed_password))
            
            self.cur.execute(f"""update jugadores set password='{formato_hashed_password}' where alias='{alias}'""")
            self.conn.commit() #guardo la info   
            print(f"Contraseña del jugador {alias} modificado.") 
            return True
        except Exception as error:
            print(error)
            return False    
        
        
    def modJugador_Nivel(self,alias,nivel):
        try:
            if nivel < 0: nivel = 0 #############
            self.cur.execute(f"""update jugadores set nivel='{nivel}' where alias='{alias}'""")
            self.conn.commit() #guardo la info   
            print(f"Nivel del jugador {alias} modificada.")  
            return True
        except Exception as error:
            print(error)
            return False   
    def modJugador_EF(self,alias,ef):
        try:
            self.cur.execute(f"""update jugadores set ef='{ef}' where alias='{alias}'""")
            self.conn.commit() #guardo la info
            print(f"Efecto-frio del jugador {alias} modificado.")   
            return True
        except Exception as error:
            print(error)
            return False     
    def modJugador_EC(self,alias,ec):
        try:
            self.cur.execute(f"""update jugadores set ec='{ec}' where alias='{alias}'""")
            self.conn.commit() #guardo la info   
            print(f"Efecto-calor del jugador {alias} modificado.") 
            return True
        except Exception as error:
            print(error)
            return False
    def modJugador_Posicion(self,alias,pos):
        try:
            self.cur.execute(f"""update jugadores set posicion='{pos}' where alias='{alias}'""")
            self.conn.commit() #guardo la info  
            print(f"Posición del jugador {alias} modificada.")  
            return True
        except Exception as error:
            print(error)
            return False 
    
    def modJugador(self,alias,password,nivel,ef,ec,posicion):
        
        if alias != None:
            
            if password != None:
                self.modJugador_Password(alias,password)
            if nivel != None:
                self.modJugador_Nivel(alias,nivel)
            if ef != None:
                self.modJugador_EF(alias,ef)   
            if ec != None:
                self.modJugador_EC(alias,ec)     
            if posicion != None:
                self.modJugador_Posicion(alias,posicion)   
                
########## [OTROS] ########## 
    #AA_PLAYER -> AA_ENGINE 
    def logeo(self,alias,password):
        try:
            #self.cur.execute(f"SELECT * FROM jugadores where alias='{alias}' and password = '{password}' ")
            self.cur.execute(f"SELECT * FROM jugadores where alias='{alias}'")
            rows = self.cur.fetchall()
            if len(rows) > 0:
                if password_ok(rows[0][1], password): return rows
                else: return []

            return rows
        except Exception as error:
            if "does not exist" in str(error):
                print("ERROR: La tabla jugadores no existe. ¿Inicializaste la base de datos?")
            else:
                print(error)
  
            return []  

        

    def logeo2(self,alias):
        try:
            self.cur.execute(f"SELECT * FROM jugadores where alias='{alias}'")
            rows = self.cur.fetchall()
            return rows
        except Exception as error:
            if "does not exist" in str(error):
                print("ERROR: La tabla jugadores no existe. ¿Inicializaste la base de datos?")
            else:
                print(error)
  
            return []  
    
    #Para cuando se produce el movimiento del jugador y quiero saber su pos actual  
    def getJugador_Posicion(self,alias):
        try:
            self.cur.execute(f"""select posicion from jugadores where alias='{alias}'""")
            pos = self.cur.fetchall()
            return pos[0][0]
        except Exception as error:
            print(error)
            return "-1,-1"
           
    #Para cuando quiero darle un nivel al jugador cuando se come una alimento 
    def getJugador_Nivel(self,alias):
        try:
            self.cur.execute(f"""select nivel from jugadores where alias='{alias}'""")
            nivel = self.cur.fetchall()
            return nivel[0][0]
        except Exception as error:
            print(error)
            return -1  
        
        #Para cuando quiero darle un nivel al jugador cuando se come una alimento 
    def getJugador(self,alias):
        try:
            self.cur.execute(f"""select * from jugadores where alias='{alias}'""")
            nivel = self.cur.fetchall()
            return nivel[0]
        except Exception as error:
            print(error)
            return []
        

########## [PRÁCTICA 3] ########
    #-------------------------- MAPA PARTIDA --------------- #
    def crearTabla_Mapa(self):
        try:
            self.cur.execute(
                """CREATE TABLE IF NOT EXISTS 
                            mapa 
                            (
                                 mapa_array varchar[20][20] PRIMARY KEY
                            )"""
            )
            self.conn.commit() #guardo la info
            print("Tabla 'mapa' creada.")
            
        except Exception as error:
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            print("#######[Inicio excepción]#######")
            print("Excepcion ocurrida a la hora de crear tabla MAPA: ")
            print(error)
            print("#######[Fin excepción]#######")

    def insertar_mapa(self,mapa):
        try:
            self.delMapas() # PRIMERO BORRO LOS MAPAS EXISTENTES
            self.cur.execute(f"""insert into mapa ("mapa_array") values ('{mapa}')""")
            self.conn.commit() #guardo la info
            #print(f"Mapa insertado en db.py")
            return True
        except Exception as error:
            
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            if "unique constraint" in str(error):
                print(f"ERROR: No es posible insertar mapa. El mismo mapa ya existe")
            else:
                print("#######[Inicio excepción insertar mapa]#######")
                print(error)
                print("#######[Fin excepción]#######")
            return False    

    def getMapa(self) -> list:
        try:
            rows = []
            self.cur.execute(f"SELECT * FROM mapa FETCH FIRST ROW ONLY")
            rows = self.cur.fetchall()
            if len(rows) > 0: return rows[0][0]
            return rows
        except Exception as error:
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            print(bg.red + "Excepción ocurrida." + bg.rs)
            traceback.print_exc()

    #borra toda la tabla
    def delMapas(self):
        try:
            self.cur.execute(f"DELETE FROM {'mapa'}")
            self.conn.commit() #guardo la info
            return True
        except Exception as error:
            print("#######[Inicio excepción delmapas]#######")
            print(error)
            print("#######[Fin excepción]#######")
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            return False       


    ##-------------------- JUGADORES PARTIDA ------------------ ##
    def crearTabla_jugadoresPartida(self):
        try:
            self.cur.execute(
                """CREATE TABLE IF NOT EXISTS 
                            jugadores_partida 
                            (
                                 JUGADORES_PARTIDA_ALIAS varchar[20][20] PRIMARY KEY
                            )"""
            )
            self.conn.commit() #guardo la info
            print("Tabla 'jugadores_partida' creada.")
            
        except Exception as error:
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            print("#######[Inicio excepción]#######")
            print("Excepcion ocurrida a la hora de crear tabla jugadores_partida: ")
            print(error)
            print("#######[Fin excepción]#######")

    def insertar_jugadores_partida(self,JUGADORES_PARTIDA_ALIAS):
        try:
            aux = json.dumps(JUGADORES_PARTIDA_ALIAS).replace("[","{").replace("]","}")
            print(aux)
            self.delJugadoresPartida() # PRIMERO BORRO LOS jugadores partida EXISTENTES
            self.cur.execute(f"""insert into jugadores_partida ("jugadores_partida_alias") values ('{aux}')""")
            self.conn.commit() #guardo la info
            print(f"JUGADORES_PARTIDA_ALIAS insertados en db.py")
            return True
        except Exception as error:
            
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            print("#######[Inicio excepción insertar jugadores de la partida en db.py]#######")
            print(error)
            print("#######[Fin excepción]#######")
            return False  

    def get_JUGADORES_PARTIDA_ALIAS(self) -> list:
        try:
            rows = []
            self.cur.execute(f"SELECT * FROM jugadores_partida FETCH FIRST ROW ONLY")
            rows = self.cur.fetchall()
            if len(rows) > 0: return rows[0][0]
            return rows
        except Exception as error:
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            print("#######[Inicio excepción get_JUGADORES_PARTIDA_ALIAS en db.py]#######")
            print(error)
            print("#######[Fin excepción]#######")
            return []

    #borra toda la tabla
    def delJugadoresPartida(self):
        try:
            self.cur.execute(f"DELETE FROM {'jugadores_partida'}")
            self.conn.commit() #guardo la info
            return True
        except Exception as error:
            print("#######[Inicio excepción delJugadoresPartida_db]#######")
            print(error)
            print("#######[Fin excepción]#######")
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            return False   

    ##-----------------------CIUDADES PARTIDA ------------------##
    def crearTabla_CiudadesPartida(self):
        try:
            self.cur.execute(
                """CREATE TABLE IF NOT EXISTS 
                            ciudades_partida
                            (
                                 c varchar[20][20] PRIMARY KEY
                            )"""
            )
            self.conn.commit() #guardo la info
            print("Tabla 'ciudades' creada.")
            
        except Exception as error:
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            print("#######[Inicio excepción]#######")
            print("Excepcion ocurrida a la hora de crear tabla CIUDADES en db.py: ")
            print(error)
            print("#######[Fin excepción]#######")

    def insertar_ciudades_partida(self,ciudades : list):
        try:
            aux = json.dumps(ciudades).replace("[","{").replace("]","}").replace("(","{").replace(")","}").replace('"',"").replace("\'","\"")
            self.cur.execute(f"""insert into ciudades_partida ("c") values ('{aux}')""")
            self.conn.commit() #guardo la info
            print(f"Ciudades insertadas en db.py")
            return True
        except Exception as error:   
            print("#######[Inicio excepción insertar ciudades de la partida en db.py]#######")
            print(error)
            print("#######[Fin excepción]#######")
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            return False

    def getCiudades(self) -> list:
        try:
            rows = []
            self.cur.execute(f"SELECT * FROM ciudades_partida FETCH FIRST ROW ONLY")
            rows = self.cur.fetchall()
            if len(rows) > 0: return rows[0][0]
            return rows
        except Exception as error:
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            print("#######[Inicio excepción getCiudades en db.py]#######")
            print(error)
            print("#######[Fin excepción]#######")
            return []
            #borra toda la tabla
    def delCiudades(self):
        try:
            self.cur.execute(f"DELETE FROM {'ciudades_partida'}")
            self.conn.commit() #guardo la info
            return True
        except Exception as error:
            print("#######[Inicio excepción delCiudades]#######")
            print(error)
            print("#######[Fin excepción]#######")
            self.conn.rollback() #para que no dé error current transacion is aborted si intento insertar múltiples y el primero tira excepción
            return False  


##-------OPERACIONES--------##
#Compruebo la contraseña de los argumentos con la hasheada
#db_hash_lista_password = string que tiene forma de lista que en verdad es una lista de bytes
#password = la contraseña que introduce el usuario.
def password_ok(db_hash_lista_password : str , password : str) -> bool:

    if bcrypt.checkpw(str.encode(password), bytes(eval(db_hash_lista_password))): # bytes vs bytes
        return True  #Contraseña correcta
    else:
        return False #Contraseña no correcta  


def crearTablas(conexion_db):
    conexion_db.creaTabla_Jugadores()
    conexion_db.creaTabla_Ciudades()

    #NUEVO PRÁCTICA 3
    conexion_db.crearTabla_Mapa()
    conexion_db.crearTabla_jugadoresPartida()
    conexion_db.crearTabla_CiudadesPartida()
    
def insertarCiudades(conexion_db):
    
    #PDF Práctica 2
    conexion_db.insertar_Ciudad("Londres", 5)
    conexion_db.insertar_Ciudad("Alicante", 26)
    conexion_db.insertar_Ciudad("Sidney", 32)
    conexion_db.insertar_Ciudad("Wisconsin", -15)
    
    #MIAS
    conexion_db.insertar_Ciudad("Mexico", 35)
    conexion_db.insertar_Ciudad("Mumbai", 21)
    conexion_db.insertar_Ciudad("Tokio", 15)
    conexion_db.insertar_Ciudad("Shangai", 28)
    conexion_db.insertar_Ciudad("Pekin", 25)
    conexion_db.insertar_Ciudad("Paris", 19)

def iniciarDB():

    #CREO OBJETO PARA LA CONEXIÓN CON LA BASE DE DATOS
    conexion_db = db()

    ##ABRO CONEXION
    if(conexion_db.openCommunication(SERVIDOR_IP , USUARIO , CONTRASENYA, BASE_DE_DATOS) == True):
          
        #OPERACIONES
        crearTablas(conexion_db)
        insertarCiudades(conexion_db)
        conexion_db.insertar_Jugador("vadim","pass",1,2,2,"2,2")
        conexion_db.insertar_Jugador("alicia","pass",1,2,2,"5,2")
        conexion_db.insertar_Jugador("jose","pass",1,2,2,"8,2")
        conexion_db.insertar_Jugador("paco","pass",1,2,2,"10,2")
        
        #CIERRO CONEXIÓN       
        conexion_db.closeCommunication()
           
  
if __name__=="__main__":
    iniciarDB()