from  bottle import Bottle, route, run, get, template, post, request
import pymysql
import time
import logging
import json
import os
import datetime
import python_jwt as jwt
import Crypto.PublicKey.RSA as RSA
import jws
import pika
import time

time.sleep(13)

#creamos la cola para el evio de datos
connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ['RABBITMQ_ENDPOINT']))
channel = connection.channel()

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

logger = logging.getLogger('twitter-svc')
logger.setLevel(logging.DEBUG)
logger.propagete = False
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

app = Bottle()

#clave publica para verificar token
public_key_file = os.path.join(os.path.dirname(__file__), 'key', 'key.pub')
with open(public_key_file, 'r') as fd:
    public_key = RSA.importKey(fd.read())


@app.post('/tw-svc/create')
def create():
    logger.info('ENCUESTA ')####
    token_type, token = request.headers['Authorization'].split()
    print token ######## muestra el token en consola
    usr = ""
    try:
        header, claims = jwt.verify_jwt(token, public_key, ['RS256'])
    except jws.exceptions.SignatureError:
        message = "Invalid token"

    usr = claims['username']

    # auth = get_auth()

    logger.info('USER : %s', usr)
    logger.info('Processing create ')
    data = request.json

    msg = {"usr":usr, "hash":data['hash'], "time":data['time'], "surveyname":data['surveyname']}

    channel.basic_publish(exchange='', routing_key='survey', body=json.dumps(msg))
    print(' [*] Sent data')

    ret = {"status": "OK"}

    cnx = None
    try:
        process = 'In process'
        logger.info('connect : %s', mysql_config)
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()
        insert_test = "INSERT INTO jobs (username, surveyname, hash, tiempo, count) VALUES (%s, %s,%s, %s, %s)"
        query = (usr, data['surveyname'], data['hash'], data['time'], process) # tupla s, me falta usr
        cursor.execute(insert_test, query)
        cnx.commit()
        cursor.close()
        ret = {"status": "OK"}
    except pymysql.Error as err:
        logger.info('error : %s', err)
        ret = {"status": "FAIL", "msg": err}
    finally:
        if cnx:
            cnx.close()
    return ret

@app.put('/tw-svc/update')
def update():

    logger.info('Processing updating table ')
    data1 = request.body.read()
    json_data = json.loads(str(data1))
    logger.info('contain: %s', json_data)

    paramUser = json_data['usr']
    paramHash = json_data['hash']
    paramTime = json_data['time']
    paramSurvey = json_data['surveyname']
    paramCount = json_data['count']

    cnx = None
    try:
        logger.info('connect : %s', mysql_config)
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()
        insert_test = "UPDATE jobs SET count = %s WHERE username = %s AND surveyname = %s"
        query = (paramCount, paramUser, paramSurvey) # tupla s, me falta usr
        cursor.execute(insert_test, query)
        cnx.commit()
        cursor.close()
        logger.info('status OK')
    except pymysql.Error as err:
        logger.info('error : %s', err)
        logger.info('status: FAIL, msg:%s ', err)
    finally:
        if cnx:
            cnx.close()
@app.get('/tw-svc/all')
def all():
    token_type, token = request.headers['Authorization'].split()
    ret = {"status":"OK"}
    usr = ""
    try:
        header, claims = jwt.verify_jwt(token, public_key, ['RS256'])
    except jws.exceptions.SignatureError:
        message = "Invalid token"
    usr = claims['username']

    logger.info('USER : %s', usr)
    print "antes de cnx"
    # print usr
    # print "hago consulta"
    try:
        logger.info('connect : %s', mysql_config)
        cnx = pymysql.connect(**mysql_config)
        cursor = cnx.cursor()
        select_test = "SELECT * FROM `jobs` WHERE `username` = %s"
        logger.info('ahoraHaceElSELECT : %s', select_test)
        data = (usr)
        cursor.execute(select_test, data)
        results = cursor.fetchall()
        logger.info('results : %s', results)
        ret = {"status":"OK", "table":results}
        cnx.commit()
        cursor.close()
    except pymysql.Error as err:
        logger.info('error : %s', err)
        ret = {"status": "FAIL", "msg": err}
    finally:
        logger.info('FINALLY')
        if cnx:
            cnx.close()
    logger.info('RETURN RET: %s', ret)
    return ret


run(app, host='0.0.0.0', port=8088)
# @app.route('/jobs',method='GET')
# def get_jobs():
#     logger.info('Processing GET /jobs')
#     token_type, token = request.headers['Authorization'].split()
#     logger.debug('token_type: {}, token: '.format(token_type, token))
#
#     try:
#         header, claims = jwt.verify_jwt(token, public_key, ['RS256'])
#     except jws.exception.SignatureError:
#         logger.warn('invalid token signature!')
#         message = "Invalid token"
#         response.status = 400
#         ret_data = {
#             "message": message
#         }
#
#     result = db_get_jobs(claims['userId'])
#
#     if result.ok:
#         ret_data = {
#             'jobs': []
#         }
#
#     return ret_data


# if __name__ == '__main__':
#     print("===== My Application =====")
#
#     # Get an API item using tweepy
#     auth = get_auth()  # Retrieve an auth object using the function 'get_auth' above
#     api = tweepy.API(auth)  # Build an API object.
#
# # Connect to the stream
#     myStreamListener = MyStreamListener()
#     myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
#
#     print(">> Listening to tweets about #aguapesada:")
#     myStream.filter(track=['b']) #esto va a ser lo que busca
#
#     # End
#     print("c'est fini!")
