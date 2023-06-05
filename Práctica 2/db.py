import psycopg2
from sqlobject import *
import json

args_json = json.load(open("args.json")) #cargo el archivo de args.json
#Obtengo la infor del archivo args.json
SERVIDOR_IP = args_json['db'][0]['SERVIDOR_IP']
USUARIO = args_json['db'][0]['USUARIO']
CONTRASENYA = args_json['db'][0]['CONTRASENYA']
BASE_DE_DATOS = args_json['db'][0]['BASE_DE_DATOS']

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
                                 password VARCHAR ( 50 ) NOT NULL,
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
            print("#######[Inicio excepción]#######")
            print("Excepcion ocurrida a la hora de crear tabla JUGADORES: ")
            print(error)
            print("#######[Fin excepción]#######")
            
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
            self.cur.execute(f"""insert into jugadores ("alias","password","nivel","ef","ec","posicion") values ('{alias}','{password}',{nivel},{ef},{ec},'{posicion}')""")
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
            self.cur.execute(f"""update jugadores set password='{password}' where alias='{alias}'""")
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
            self.cur.execute(f"SELECT * FROM jugadores where alias='{alias}' and password = '{password}' ")
            rows = self.cur.fetchall()
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
        
##-------OPERACIONES--------##



def crearTablas(conexion_db):
    conexion_db.creaTabla_Jugadores()
    conexion_db.creaTabla_Ciudades()
    
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