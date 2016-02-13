import time
import redis
import pika

r = redis.StrictRedis(host='localhost', port=6379, db=0)
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue='tasks')

def callback(ch, method, properties, uuid):
    percentage = 1
    
    while percentage < 100:
        time.sleep(0.15);
        percentage += 1
        if r.get(uuid) == "CANCELED":
            break
        r.set(uuid, str(percentage) + "%")
    if(percentage == 100):
        r.set(uuid, "FINISHED")

channel.basic_consume(callback, queue='tasks', no_ack=True)
print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
