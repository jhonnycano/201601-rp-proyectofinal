import sys
import tweepy
import json
import generales as g
import creds as c

######################################################################
# Clase Listener
######################################################################

class MyStreamListener(tweepy.StreamListener):
    def __init__(self, ctx_escucha, evn_status):
        super(MyStreamListener, self).__init__()
        self.ctx_escucha = ctx_escucha
        self.evn_status = evn_status
    
    def on_status(self, status):
        #g.uprint(status.text)
        self.evn_status(self.ctx_escucha, status)
        
    def on_error(self, status_code):
        print('Error! codigo: ' + str(status_code))
        return True # Para continuar escuchando

    def on_timeout(self):
        print('Timeout...')
        return True # Para continuar escuchando

######################################################################
# Funciones de configuracion
######################################################################

def traer_api():
    llaves_consumo = c.traer_llaves_consumo()
    consumer_key = llaves_consumo[0]
    consumer_secret = llaves_consumo[1]

    llaves_acceso = c.traer_llaves_acceso()
    access_token = llaves_acceso[0]
    access_token_secret = llaves_acceso[1]

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)
    return api

def crear_listener(ctx_escucha, evn_status, arr_terminos):
    api = traer_api()
    sl = MyStreamListener(ctx_escucha, evn_status)
    sl = tweepy.Stream(auth = api.auth, listener = sl)    
    sl.filter(track=arr_terminos)
    return sl

######################################################################
# Funciones predefinidas de status
######################################################################

def status_mostrar_stream(ctx_escucha, status):
    g.uprint(status.text)

def status_guardar_stream(ctx_escucha, status):
    s = json.dumps(status._json)
    arch = "txt.json"
    
    with open(arch, "a") as f:
        f.write(s)

######################################################################
# Funciones de pruebas
######################################################################

def prueba_rest():
    api = traer_api()
    user = api.get_user('jhonnycano')
    g.uprint(user)
    public_tweets = api.home_timeline()
    for tweet in public_tweets:
        g.uprint(tweet.text)

def mostrar_stream():
    sl = crear_listener(None, status_mostrar_stream, ['amor'])

######################################################################
# Funcion principal
######################################################################

def main():
    mostrar_stream()

if __name__ == "__main__": main()