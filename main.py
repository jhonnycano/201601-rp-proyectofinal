import sys
import os
import datetime
from datetime import timedelta
import csv
import sqlite3
import generales as g
import util as u
from timeit import default_timer as timer
import numpy as np
import scipy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import svm
from sklearn.naive_bayes import GaussianNB
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.linear_model import MultiTaskLasso
from sklearn.linear_model import ElasticNet
from sklearn.linear_model import Perceptron
from sklearn.neighbors import KNeighborsClassifier
#from sklearn.svm import SVC
import streaming as stm
#from streaming import MyStreamListener

######################################################################
# Configuracion
######################################################################

global total_clasificar

salida_tipo = 1               # 1:a pantalla, 2:tabla latex
cant_elementos = -1           # -1: todos
terminos_filtro = ['Donald Trump', 'Hillary Clinton']    
total_clasificar = 50

######################################################################
# Lectura de datos
######################################################################

def insertar_desde_archivo(cn):
    g.crear_tabla(cn)
    ciclo = g.leer_archivo("D:/AreaTrabajo/Dropbox/Universidad/2016-01/Patrones/Proyecto/Ejercicio/Datos/training.csv")
    for itm in ciclo:
        g.insertar_tweet(cn, itm)
    cn.commit()

######################################################################
# Extraccion de caracteristicas
######################################################################

def traer_columna(rs, id):
    f = lambda x: x[id]  # traer el contenido-texto de la tupla
    result = list(map(f, rs))
    return result

def generar_vector(rs):
    x = g.partir_arreglo(rs, 0.8)
    arr1 = x[0]    
    tr_corpus = traer_columna(arr1, 1)
    tr_clases = traer_columna(arr1, 2)
    #print("tr_corpus: {}".format(tr_corpus))
    #print("tr_clases: {}".format(tr_clases))
    arr2 = x[1]    
    pr_corpus = traer_columna(arr2, 1)
    pr_clases = traer_columna(arr2, 2)
    #print("tr_corpus: {}".format(tr_corpus))
    #print("tr_clases: {}".format(tr_clases))
    
    tfidf = TfidfVectorizer(min_df=2, 
                            max_df=0.7,
                            sublinear_tf=True,
                            use_idf=True)
    vectores_entrenamiento = tfidf.fit_transform(tr_corpus)
    vectores_prueba = tfidf.transform(pr_corpus)
    
    #print("vectores_prueba : {0}".format(vectores_prueba))
    #print("vocabulario : {0}".format(tfidf.vocabulary_))
    return {
        "entrenamiento": 
        {
            "vector": vectores_entrenamiento,
            "clases": tr_clases
        }, 
        "pruebas":
        {
            "vector": vectores_prueba,
            "clases": pr_clases
        },
        "tfidf": tfidf
    }

def traer_idf(matriz, termino):
    #print(matriz.idf_)#[bow_transformer.vocabulary_['u']]
    return 0

######################################################################
# Constructores de clasificadores
######################################################################

def crear_clasificador_nbm():
    return MultinomialNB(alpha=1.0, fit_prior=True, class_prior=None)

def crear_clasificador_nb():
    return GaussianNB()

def crear_clasificador_knn():
    return KNeighborsClassifier()

def crear_clasificador_passive_aggresive():
    return PassiveAggressiveClassifier()

def crear_clasificador_mtlasso():
    return MultiTaskLasso()

def crear_clasificador_elasticnet():
    return ElasticNet()

def crear_clasificador_perceptron():
    return Perceptron()

def crear_clasificador_svm():
    return svm.SVC(kernel = "rbf", C = 10)
    #return svm.SVC()

def crear_clasificador_mlp():
    return None#MLPClassifier()

######################################################################
# Ejecucion del clasificador
######################################################################

def entrenar(lista, clases, creador_clasif, arreglos_densos=False):
    clasificador = creador_clasif()
    arr = lista.todense() if arreglos_densos else lista
    predictor = clasificador.fit(arr, clases)
    return predictor

def preparar_y_probar(data, algoritmo, etiqueta, arreglos_densos=False):
    salida = {
        "etiqueta": etiqueta,
    }
    inicio = timer()
    tr = data["entrenamiento"]
    vector = tr["vector"]
    clases = tr["clases"]
    predictor = entrenar(vector, clases, algoritmo, arreglos_densos)

    pr = data["pruebas"]
    arr = pr["vector"].todense() if arreglos_densos else pr["vector"]
    res = predictor.predict(arr)
    fin = timer()
    
    arr = g.mezclar_arreglos(pr["clases"], res)
    indices, dic = g.calcular_indices(arr, [0, 4])
    salida["tiempo"] = str(timedelta(seconds=fin - inicio))
    salida["ind_general"] = indices
    salida["ind_clase"] = dic
    
    mostrar_salida(salida)
    return predictor

def mostrar_salida(salida):
    if salida_tipo == 1: 
        mostrar_salida_pantalla(salida)
    elif salida_tipo == 2:
        mostrar_salida_latex(salida)

def mostrar_salida_pantalla(salida):
    print()
    print("********************************************************************************")
    print(salida["etiqueta"])
    print("********************************************************************************")
    print("tiempo: {0}".format(salida["tiempo"]))
    g.pprint_od(salida["ind_general"])
    print_list_dic(salida["ind_clase"])
    print()

def mostrar_salida_latex(salida):
    ig = salida["ind_general"]
    ic = salida["ind_clase"]
    
    print("{0:20}& {1:14} & {2:7} & {3:7} & {4:7} & {5:7} \\\\ \\hline".format(salida["etiqueta"], 
        salida["tiempo"], 
        ig["vp"], ig["vn"], 
        ig["fp"], ig["fn"]))
    print("                    & \multicolumn{{2}}{{c}}{{Espc: {0}}} & \multicolumn{{2}}{{c}}{{Sens: {1}}} \\\\ \\hline".format(
        ig["espc"], ig["sens"]
    ))
    
    # por clase
    for itm in ic:
        print("{0:3}& {1:7} & {2:7} & {3:7} & {4:7} \\\\ \\hline".format(itm["clase"], 
            itm["vp"], itm["vn"], 
            itm["fp"], itm["fn"]))
        print("   & \multicolumn{{2}}{{c}}{{Espc: {0}}} & \multicolumn{{2}}{{c}}{{Sens: {1}}} \\\\ \\hline".format(
            itm["espc"], itm["sens"]
        ))
        
    
    print()
    #print_list_dic(salida["ind_clase"])

######################################################################
# Funciones de configuracion de Streaming
######################################################################

def status_clasificar_stream(ctx_escucha, status):
    global total_clasificar
    #print("total_clasificar: {}".format(total_clasificar))
    print("********************")
    g.uprint(status.text)

    tfidf = ctx_escucha["vector"]["tfidf"]
    features = tfidf.transform([status.text])

    for k in ctx_escucha["clasificadores"]:
        itm = ctx_escucha["clasificadores"][k]
        activo = itm[0]
        creador = itm[1]
        denso = itm[2]    
        cl = itm[3]
        if activo != True:
            continue
        clase = cl.predict(features)
        print("clase segun {0}:{1}".format(k, clase))
    print()
    print()
    
    if total_clasificar == -1:
        return True
    elif total_clasificar == 0:
        exit()
    else:
        total_clasificar -= 1

######################################################################
# Otras funciones
######################################################################

def traer_clasificadores():
    return {
        "Multinomial": [True, crear_clasificador_nbm, False, None],
        "Gaussiano": [False, crear_clasificador_nb, True, None],
        "Passive-Aggresive": [True, crear_clasificador_passive_aggresive, False, None],
        "KNN": [False, crear_clasificador_knn, False, None],
        #"ElasticNet": [False, crear_clasificador_elasticnet, False, None],
        "Perceptron": [False, crear_clasificador_perceptron, False, None],
        "SVM": [False, crear_clasificador_svm, False, None],
    }
def print_list_dic(ld):
    for itm in ld:
        g.pprint_od(itm)

def mostrar_pantalla_inicial():
    print("**********     PROYECTO FINAL     **********")
    print("Materia: Reconocimiento de Patrones")
    print("Presentado por: Jhonny Dickson Cano")
    print("Docente: Laura Juliana Cortes")
    print()

######################################################################
# Funcion principal
######################################################################

def main():
    mostrar_pantalla_inicial()
    
    cn = g.crear_conexion("tweets.db")
    print("Leyendo datos de entrenamiento...")
    rs = u.traer_datos(cn, cant_elementos)
    
    print("Generando vector de caracteristicas...")
    dic_vector = generar_vector(rs)
    dic_predictores = traer_clasificadores()
    
    print("Iniciando entrenamiento...")
    for k, v in dic_predictores.items():
        activo = v[0]
        creador = v[1]
        denso = v[2]
        if activo != True:
            continue
        
        try:
            cl = preparar_y_probar(dic_vector, creador, k, denso)
        except:
            print("Error al clasificar:", sys.exc_info()[1])
            raise
            cl = None
        v[3] = cl
        
    ctx_escucha = {
        "vector": dic_vector,
        "clasificadores": dic_predictores
    }    
    sl = stm.crear_listener(ctx_escucha, status_clasificar_stream, 
           terminos_filtro)

if __name__ == "__main__": main()