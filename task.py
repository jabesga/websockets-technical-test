import time
import redis
import pika

r = redis.StrictRedis(host='localhost', port=6379, db=0)
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue='tasks')

def callback(ch, method, properties, uuid):
    percentage = 1
    
    while percentage < 100 and r.get(uuid) != "CANCELED":
        time.sleep(0.15);
        percentage += 1
        if r.get(uuid) != "CANCELED":
            r.set(uuid, str(percentage) + "%")
        
    if(percentage == 100):
        r.set(uuid, "FINISHED")
    else:
        r.set(uuid, "CANCELED")

print "\tWaiting tasks..."
channel.basic_consume(callback, queue='tasks', no_ack=True)
channel.start_consuming()

