import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.autoreload
from tornado.options import define, options, parse_command_line
from tornado.ioloop import PeriodicCallback
import uuid
import redis
import pika
import os
import json

define("port", default=8888, help="run on the given port", type=int)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def initialize(self):
        self.task_uuid = None
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = connection.channel()
        self.channel.queue_declare(queue='tasks')

    def open(self, *args):
        self.callback = tornado.ioloop.PeriodicCallback(self.updateTaskStatus, 120)
        self.callback.start()
        self.task_uuid = str(uuid.uuid1());
        self.r.set(self.task_uuid, 'ENQUEUED')
        self.channel.basic_publish(exchange='', routing_key='tasks', body=self.task_uuid)

        self.write_message({'status': 'ENQUEUED', 'uuid': self.task_uuid})

    def updateTaskStatus(self):
        self.write_message({'status': self.r.get(self.task_uuid)})        

    def on_message(self, message):        
        data = json.loads(message)
        if data['request'] == 'cancel':
            self.r.set(self.task_uuid, 'CANCELED')
            self.write_message({'status': 'CANCELED', 'uuid': self.task_uuid})

    def on_close(self):
        self.callback.stop()

app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/task-start/', WebSocketHandler),
])

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    print '\tListening on port ' + str(options.port)
    tornado.autoreload.watch(os.path.abspath('./index.html'))
    tornado.autoreload.start(check_time=500)
    tornado.ioloop.IOLoop.instance().start()