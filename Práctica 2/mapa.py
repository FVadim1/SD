from random import random
import random
from copy import copy,deepcopy
from sty import Style, RgbFg
from sty import fg, bg, ef, rs

CGREEN = '\033[42m'
CBLUE = '\033[104m'
CORANGE = '\033[43m'


CWHITE = '\033[107m'
CWHITE_BLACK = '\033[90m'
CBOLD     = '\33[1m'
CITALIC   = '\33[3m'

CALIMENTO = '\033[97m'
CMINA = '\033[91m'

CGREY = '\033[100m'

CVIOLETA = '\033[35m'
CRED2 = '\033[91m'

CRED = '\33[41m'
CEND = '\033[0m'

bg_verde_pdf = bg(226,239,219)

class Mapa:    
    def __init__(self):
        self.ancho=20
        self.alto=20      
        self.mapa=[]
        for i in range(self.alto):           
            self.mapa.append([])
            for j in range(self.ancho):
                self.mapa[i].append('0')
       
        
    def __str__(self):
        salida= CWHITE+ CWHITE_BLACK + CBOLD +  "\u0332".join("    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 ") + CEND + "\n"

        for f in range(self.alto):
            if f >= 10:
                salida+=CWHITE+ CWHITE_BLACK + CBOLD +  str(f) + "|" + CEND
            else:
                salida+=CWHITE+ CWHITE_BLACK + CBOLD +  str(f) + " |" +CEND
            for c in range(self.ancho):
                
                if f >= 0 and f <= 9 and c >= 0 and c <= 9:
                    salida += CGREEN
                if f >= 0 and f <= 9 and c >= 10 and c <= 19:
                    salida += CBLUE
                if f >= 10 and f <= 19 and c >= 0 and c <= 9:
                    salida += CORANGE
                if f >= 10 and f <= 19 and c >= 10 and c <= 19:
                    salida += CGREY
     
                if self.mapa[f][c] == '0': #vacio
                        salida += "\u0332".join("   ")
                elif self.mapa[f][c] == 'M': #mina
                    salida += CRED + "\u0332".join(" M ") + CEND
                elif self.mapa[f][c] == 'A': #alimento
                    salida += CALIMENTO + CBOLD + "\u0332".join(" A ") + CEND
                elif self.mapa[f][c] == 'N': #npc
                    salida += "\u0332".join(" N ")
                elif "P" in self.mapa[f][c] :
                    salida += bg.black + fg.li_red + CBOLD  + "\u0332".join(f" {self.mapa[f][c]}") + CEND + fg.rs + bg.rs
                     
                salida+=CEND
                
            salida += "\n"
        return salida
    
    #Hace lo mismo que la función __str__ pero le da un color personalizado al player
    def getMapa(self, player):
        salida= CWHITE+ CWHITE_BLACK + CBOLD +  "\u0332".join("    0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 ") + CEND + "\n"

        for f in range(self.alto):
            if f >= 10:
                salida+=CWHITE+ CWHITE_BLACK + CBOLD +  str(f) + "|" + CEND
            else:
                salida+=CWHITE+ CWHITE_BLACK + CBOLD +  str(f) + " |" +CEND
            for c in range(self.ancho):
                
                if f >= 0 and f <= 9 and c >= 0 and c <= 9:
                    salida += CGREEN
                if f >= 0 and f <= 9 and c >= 10 and c <= 19:
                    salida += CBLUE
                if f >= 10 and f <= 19 and c >= 0 and c <= 9:
                    salida += CORANGE
                if f >= 10 and f <= 19 and c >= 10 and c <= 19:
                    salida += CGREY
     
                if self.mapa[f][c] == '0': #vacio
                        salida += "\u0332".join("   ")
                elif self.mapa[f][c] == 'M': #mina
                    salida += CRED + "\u0332".join(" M ") + CEND
                elif self.mapa[f][c] == 'A': #alimento
                    salida += CALIMENTO + CBOLD + "\u0332".join(" A ") + CEND
                elif self.mapa[f][c] == 'N': #npc
                    salida += "\u0332".join(" N ")
                elif "P" in self.mapa[f][c] :
                    if self.mapa[f][c] == player:
                        salida += bg.black + fg.cyan + CBOLD  + "\u0332".join(f" {self.mapa[f][c]}") + CEND + fg.rs + bg.rs
                    else:
                        salida += bg.black + fg.li_red + CBOLD  + "\u0332".join(f" {self.mapa[f][c]}") + CEND + fg.rs + bg.rs
                else:
                    salida += bg.black + fg.li_red + CBOLD  + "\u0332".join(f" {self.mapa[f][c]} ") + CEND + fg.rs + bg.rs

                salida+=CEND
                
            salida += "\n"
        return salida

    def getArray(self):
        return self.mapa
       
    def ListCopy(self,array:list):
        self.mapa.clear()
        self.mapa = []
        for i in range(self.alto):           
            self.mapa.append([])
            for j in range(self.ancho):
                self.mapa[i].append(array[i][j])     
                
    def DeepCopy(self,lista:list):
        self.mapa = []
        self.mapa = deepcopy(lista)

    def getAncho(self):
        return self.ancho
    
    def getAlto(self):
        return self.alto
    
    def getCelda(self, fila, col):
        return self.mapa[int(fila)][int(col)]
    
    def setCelda(self, fila, col, val): #cambia el valor del mapa
        self.mapa[int(fila)][int(col)]=val  
 
    #PDF: El valor de cada celda se obtiene aleatoriamente entre Mina, Alimento y Nada  
    #Sin tener en cuenta que hay players (para testeo)
    def add_Minas_Alimentos_SinPlayers(self):
        for i in range(self.alto):           
            for j in range(self.ancho):
                self.mapa[i][j] = random.choice(['M','A','0'])
                
    #Teniendo en cuenta que hay players (al inicio de una partida)
    def add_Minas_Alimentos_ConPlayers(self):
        for i in range(self.alto):           
            for j in range(self.ancho):
                if "P" not in self.mapa[i][j]:
                    self.mapa[i][j] = random.choice(['M','A','0'])    


