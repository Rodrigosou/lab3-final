from credenciales import Consumer_Key, Consumer_Secret, Access_Token, Access_Token_Secret
import json
import os
import pika
import time
import logging
import tweepy
import requests

time.sleep(10)

logger = logging.getLogger('twitter-svc')
logger.setLevel(logging.DEBUG)
logger.propagete = False
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

def get_auth():
    auth = tweepy.OAuthHandler(Consumer_Key, Consumer_Secret)
    auth.set_access_token(Access_Token, Access_Token_Secret)
    return auth



class BreakLoopException(Exception):
    pass

class MyStreamListener(tweepy.StreamListener):

    def __init__(self,duration):
        tweepy.StreamListener.__init__(self)
        self.stream = None
        self.count = 0
        self.duration = duration
        self.start_time = None
        self.end_time = None
        return

     #def on_data(self, data):
        #logger.debug("\non_data\n")
        # Twitter returns data in JSON format - we need to decode it first
        #decoded = json.loads(data)
        # Also, we convert UTF-8 to ASCII ignoring all bad characters sent by users
        #print '@%s: %s' % (decoded['user']['screen_name'], decoded['text'].encode('ascii', 'ignore'))
        #return True

    def on_connect(self):
        logger.debug("\non_connect\n")
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration
        return

    def keep_alive(self):
        logger.debug("\nkeep_alive\n")
        now = time.time()
        if now > self.end_time:
            logger.debug("\nme tengo que ir\n")
            raise BreakLoopException('break the lop!')

    def on_error(self, status):
        print status

    def on_status(self, status):
        logger.debug("\non_status\n")
        now = time.time()
        if now < self.end_time:
            logger.debug("\ncuento el tweet\n")
            self.count = self.count + 1
            print self.count
        else:
            logger.debug('should disconnect')
            return False

# creamos la cola para el evio de datos
connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.environ['RABBITMQ_ENDPOINT']))
channel = connection.channel()
channel.queue_declare(queue='survey')


def callbacksurvey(ch, method, properties, body):
    print(" [x] Received %r" % body)
    data = json.loads(body) #string(body) to json
    logger.info('Body: %s', data)

    auth = get_auth()
    paramTime = int(data['time'])

    my_stream_listener = MyStreamListener(paramTime) # paramTime es la duracion
    my_stream = tweepy.Stream( auth=auth, listener=my_stream_listener, chunk_size=1 )

    my_stream_listener.stream = my_stream
    try:
        my_stream.filter(track=[data['hash']])
    except BreakLoopException:
        pass
    logger.debug('finalizo la cuenta')
    my_stream.disconnect()

    msg = {"usr":data['usr'], "hash":data['hash'], "time":data['time'],
                                "surveyname":data['surveyname'],"count":my_stream_listener.count}

    req = requests.put("http://tw-svc:8088/tw-svc/update", data=json.dumps(msg))
    logger.info('request: %s', req)
    # channel_basic_ack(delivery_tag=method.delivery_tag)

#########

channel.basic_consume(callbacksurvey, queue='survey', no_ack=True)
channel.start_consuming()

##########
