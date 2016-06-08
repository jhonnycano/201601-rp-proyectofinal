import sys
import os
import datetime
import csv
import sqlite3
from collections import OrderedDict

################################################################################
# funciones sqlite
################################################################################

def crear_conexion(ruta):
    cn = sqlite3.connect(ruta)
    return cn

def insertar(cn, sql, pars, hacer_commit=False, traer_id=True):
    #print(pars)
    cn.execute(sql, pars)
    if hacer_commit == True: cn.commit()
    
    if traer_id == True:
        id = traer_valor(cn, "select last_insert_rowid();")
        return id

def traer_lista(cn, sql, pars=None):
    cur = cn.cursor()
    if pars == None:
        cur.execute(sql)
    else:
        cur.execute(sql, pars)
    rs = cur.fetchall()
    cur.close()
    return rs

def traer_valor(cn, sql):
    lst = traer_lista(cn, sql, None)
    return lst[0][0]

################################################################################
# funciones con archivos
################################################################################

def leer_archivo(ruta, delimitador=',', skipinitialspace=False):
    with open(ruta, 'r') as csvfile:
        rdr = csv.reader(csvfile, delimiter=delimitador, quotechar='"', skipinitialspace=skipinitialspace)
        for itm in rdr:
            yield itm

################################################################################
# funciones con arreglos
################################################################################

def partir_arreglo(arr, porc):
    """
Parte un arreglo en dos arreglos, 
retorna una tupla con dos arreglos repartidos segun el porcentaje indicado
    """
    total1 = len(arr) * porc
    result1 = []
    result2 = []
    for i in range(0, len(arr)):
        if len(result1) < total1:
            result1.append(arr[i])
        else:
            result2.append(arr[i])
        
    return (result1, result2)

def mezclar_arreglos(arr1, arr2):
    res = []
    for i in range(0, len(arr1)):
        res.append((arr1[i], arr2[i]))
    return res

def extraer_componente(arr, ind):
    result = []
    for itm in arr:
        result.append(itm[ind])
    return result

################################################################################
# funciones de reconocimiento de patrones
################################################################################

def calcular_indices_clase(arr, clase):
    """
Calcula los indices positivos y negativos de un arreglo para una clase especifica
En la primer posicion de cada elemento se espera la clase real.
En la segunda posicion de cada elemento se espera la clase calculada.
    """
    vp = vn = fp = fn = 0
    for itm in arr:
        real = itm[0]
        calculado = itm[1]
        if calculado == clase:
            if real == calculado:
                vp += 1
            else:
                fp += 1
        else:
            if real == clase:
                fn += 1  # debería ser de la clase, pero calculó otra clase
            else:
                vn += 1
    result = OrderedDict()
    result["clase"] = clase
    result["vp"] = vp
    result["vn"] = vn
    result["fp"] = fp
    result["fn"] = fn
    if (result["vp"] + result["fn"] == 0):
        result["sens"] = None
    else:
        result["sens"] = round(result["vp"] / (result["vp"] + result["fn"]), 3)
    if (result["vn"] + result["fp"] == 0):
        result["espc"] = None
    else:
        result["espc"] = round(result["vn"] / (result["vn"] + result["fp"]), 3)
    return result

def calcular_indices(arr, clases_posibles):
    """
Calcula los indices positivos y negativos de un arreglo
En la primer posicion de cada elemento se espera la clase real.
En la segunda posicion de cada elemento se espera la clase calculada.
    """
    dic = []
    for clase in clases_posibles:
        ind_clase = calcular_indices_clase(arr, clase)
        #print("clase: {}, ind: {}".format(clase, ind_clase))
        dic.append(ind_clase)
    result = OrderedDict()
    result["vp"] = 0
    result["vn"] = 0
    result["fp"] = 0
    result["fn"] = 0
    #result = {"vp": 0, "vn": 0, "fp": 0, "fn": 0}
    for r in dic:
        result["vp"] += r["vp"]
        result["vn"] += r["vn"]
        result["fp"] += r["fp"]
        result["fn"] += r["fn"]
    if (result["vp"] + result["fn"] == 0):
        result["sens"] = None
    else:
        result["sens"] = round(result["vp"] / (result["vp"] + result["fn"]), 3)
    if (result["vn"] + result["fp"] == 0):
        result["espc"] = None
    else:
        result["espc"] = round(result["vn"] / (result["vn"] + result["fp"]), 3)
    return result, dic

def realizar_conteo(arr):
    """
        Cuenta las combinaciones entre clases calculadas y reales
    """
    res = {}
    for itm in arr:
        if not itm[0] in res:
            res[itm[0]] = {}
        if not itm[1] in res[itm[0]]:
            res[itm[0]][itm[1]] = 1
        else:
            res[itm[0]][itm[1]] += 1
    return res
    
################################################################################
# funciones de consola
################################################################################

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

def elegir_de_arreglo(arr, etiqueta):
    i = 0
    for r in arr:
        print("{0}:{1}".format(str(i), r))
        i += 1
    while True:
        try:
            ind = input(etiqueta)
            ind = int(ind)
            if not (0 <= ind < len(arr)): 
                print("Ingrese un indice de la lista ({0}-{1})".format(0, len(arr) - 1))
                continue
            break
        except:
            continue
       
    return arr[ind]

def pprint_od(od):
    for key in od:
        sys.stdout.write("%s:%s, " % (key, od[key]))
    print()