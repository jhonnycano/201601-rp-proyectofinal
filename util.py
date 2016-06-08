import generales as g

#------------------------------------------------------------------------------
# funciones especificas de datos para el programa
#------------------------------------------------------------------------------

def crear_tabla(cn):
    sql = """
    CREATE TABLE IF NOT EXISTS tweet (
          id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT
        , tweet_id VARCHAR(40) NOT NULL
        , fch_creacion DATETIME
        , usuario VARCHAR(50) NOT NULL
        , contenido VARCHAR(140) NOT NULL
        , clase INTEGER NOT NULL
    );
    """
    cn.execute(sql)
    
def insertar_tweet(cn, itm):
    sql = """
    INSERT INTO tweet
    (tweet_id, fch_creacion, usuario, contenido, clase)
    VALUES
    (?, ?, ?, ?, ?);
    """
    
    fch = datetime.datetime.strptime(itm[2], '%a %b %d %H:%M:%S PDT %Y')
    pars = (itm[1], fch, itm[4], itm[5], int(itm[0]))
    insertar(cn, sql, pars, traer_id=False)

def traer_datos(cn, cant=1000):
    filtro = "LIMIT {}".format(cant)
    if cant == -1:
        filtro = ""
        
    sql = """
SELECT tweet_id, contenido, clase 
FROM 
(SELECT tweet_id, contenido, clase FROM tweet WHERE clase = 0 {0}) a
UNION
SELECT tweet_id, contenido, clase 
FROM 
(SELECT tweet_id, contenido, clase FROM tweet WHERE clase = 4 {0}) b
;
    """.format(filtro)
    
    rs = g.traer_lista(cn, sql)
    return rs
