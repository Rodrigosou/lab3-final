import pymysql
from  bottle import Bottle, route, run, get, template, post, request
import os
import datetime
import python_jwt as jwt
import Crypto.PublicKey.RSA as RSA
import logging

#create logger with 'auth-svc'
logger = logging.getLogger('auth-svc')
logger.setLevel(logging.DEBUG)
logger.propagate = False
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

#la clave privada, creamos el token
private_key_file = os.path.join(os.path.dirname(__file__), 'key', 'key')
with open(private_key_file, 'r') as fd:
    private_key = RSA.importKey(fd.read())

## en la veriable app guardo una instancia de bootle
app = Bottle()

mysql_config = {
    #'host' : 'localhost',
    'host' : os.environ['MYSQL_ENDPOINT'],
    #'db' : 'spt',
    'db' : os.environ['MYSQL_DATABASE'],
    #'user' : 'rodrigos',
    'user' : os.environ['MYSQL_USER'],
    #'passwd': '123'
    'passwd': os.environ['MYSQL_PASSWORD']
}
#sudo apt-get install pycharm-community
users = {}

def init_db():
    logger.info('Processing init database')

    cnx = None
    try:
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()

        create_table = "create table if not exists spt.usuarios(usuario varchar(50), password varchar(50))"
        cursor.execute(create_table)
        cursor.close()

    except pymysql.Error as err:
        msg = "Failed init database: {}".format(err)
        logger.error(msg)
    finally:
        if cnx:
            cnx.close()

    return

@app.route('/hello',method="GET")
def hello():
    return "Hello World!"
## lo mismo que route pero definis @app.get que es mas rapido y legible para especificar
## el metodo
@app.get('/auth-svc/')
@app.get('/auth-svc/hello/<name>')
## reconoce que la funcion para la ruta '/hello/<name>' y '/'es greet() porque
## es la primer funcion escrita a continuacion de las rutas
def greet(name='Stranger'):
    return template('Hello {{name2}}', name2=name)

@app.post('/auth-svc/param')
def hello_json():
    data = request.json
    param = data['param']
    ret = {"status":"OK", "param": param}
    return ret

@app.post('/auth-svc/login')
def login():
    data = request.json
    user = data['user']
    passw = data['pass']

#--------------------------------------------------
    cnx=None;
    try:
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()
        query = "SELECT `usuario`,`password` FROM `usuarios` WHERE `usuario`= %s"
        cursor.execute(query,user)
        resp = cursor.fetchone()
        #return resp

        if(not resp): #no hay resultado
            print ("El usuario no existe")
            ret = {"status": "FAIL", "msg": "usuario y/o password invalido"}

        else:
            if(resp[1] == passw):
                #si entra se pudo loguear

                payload = {'username': user, 'role': 'admin'}; #generamos el payload
                token = jwt.generate_jwt(payload, private_key, 'RS256', datetime.timedelta(minutes=5)) #generamos el token
                ret = {"status": "OK",
                       "msg": "logueado correctamente",
                       "token":token
                       }

            else:
                ret = {"status": "FAIL", "msg": "usuario o password invalido"}


        cursor.close()
    except pymysql.Error as err:
        print "Failed to insert data: {}".format(err)
        ret = {"status":"FAIL", "msg":err}
    finally:
        if cnx:
            cnx.close()

    return ret


@app.post('/auth-svc/register')
def register():

    data = request.json
    user = data['username']
    passw = data['password']

    #print("recibi:")
    print("usuario:" + user)
    print("password:" + passw + "\n\n")

    #pass2 = data['pass2']
    #p = users.has_key(param)
    cnx=None;
    try:
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()
        query = "SELECT `usuario` FROM `usuarios` WHERE `usuario`= %s"
        cursor.execute(query, user)
        resp = cursor.fetchone()
        #print(resp)
#        print("result:")
#        print(resp)

        if(not resp):#si no existe podemos registrarlo
            print ("El usuario no existe")
            #insertamos en la base de datos
            insert = "INSERT INTO usuarios (usuario, password) VALUES (%s, %s)"
            usuario = (user, passw)
            cursor.execute(insert, usuario)
            cnx.commit()
            cursor.close()

            payload = {'username': user, 'role': 'admin'};
            token = jwt.generate_jwt(payload, private_key, 'RS256', datetime.timedelta(minutes=5))
            ret = {"status": "OK",
                   "msg": "usuario creado correctamente",
                   "token": token
                   }
            return ret
        else:
            print ("usuario existe en la base de datos")
            #cnx.commit()
            cursor.close()
            ret = {"status": "FAIL", "msg": "usuario ya existe."}

        #cnx.commit()
        cursor.close()
    except pymysql.Error as err:
        print "Failed to insert data: {}".format(err)
        ret = {"status":"FAIL", "msg":err}
    finally:
        if cnx:
            cnx.close()

    return ret


init_db()
run(app, host='0.0.0.0', port=8081)
