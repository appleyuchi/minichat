# -*- coding: utf-8 -*-
# Micro gevent chatroom.
# ----------------------
# Make things as simple as possible, but not simpler.
from gevent import monkey; monkey.patch_all()
from flask import Flask, render_template, request, json
import os
from gevent import queue
from gevent.pywsgi import WSGIServer

app = Flask(__name__)
app.debug = True


#-----------------聊天室-------------------------------
class Room(object):

    def __init__(self):
        self.users = set()
        self.messages = []

    def backlog(self, size=25):
        return self.messages[-size:]

    def subscribe(self, user):
        self.users.add(user)

    def add(self, message):
        for user in self.users:
            print(user)
            user.queue.put_nowait(message)#信息放入队列
        self.messages.append(message)
#-----------------用户-------------------------------
class User(object):

    def __init__(self):
        self.queue = queue.Queue()
#-------------------聊天室类型------------------------
rooms = {
    'python': Room(),
    'django':  Room(),
}


#------------------输入127.0.0.1:5000/会得到下面这个--------
users = {}
@app.route('/')
def choose_name():
    return render_template('choose.html')

#--------------------输入uid后会跳转到下面这个----------------------------
@app.route('/<uid>')
def main(uid):
    return render_template('main.html',
        uid=uid,
        rooms=rooms.keys()
    )
#--------------------输入uid和聊天室名称以后会跳转到下面这个----------------------------
@app.route('/<room>/<uid>')
def join(room, uid):
    user = users.get(uid, None)

    if not user:#如果输入的uid是在不存在的,那么新建一个对象
        users[uid] = user = User()

    active_room = rooms[room]
    active_room.subscribe(user)#订阅,聊天室订阅subscribe用户,意思是用户的信息发送到这个聊天室
    print('subscribe', active_room, user)
    # 这也就是说,聊天室订阅的用户,发送的信息都会出现在聊天室中

    messages = active_room.backlog()

    return render_template('room.html',room=room, uid=uid, messages=messages)


#-------------------下面的两个函数都是在浏览器中不可访问的,而是用來在後臺返回log信息,這兩個函數都是被html中的代碼所調用的----------------------------------------

# 這個是返回給user所在的聊天室頁面的
@app.route("/put/<room>/<uid>", methods=["POST"])
def put(room, uid):
    user = users[uid]
    room = rooms[room]

    message = request.form['message']
    room.add(':'.join([uid, message]))#拼接用户id和message

    return ''


# poll:轮询请求数据的作用(每隔10秒對queue進行輪詢)
# 這個是返回給服務器的
@app.route("/poll/<uid>", methods=["POST"])
def poll(uid):
    try:
        msg = users[uid].queue.get(timeout=10)
    except queue.Empty:
        msg = []
    return json.dumps(msg)

if __name__ == "__main__":
    port=5006
    http = WSGIServer(('', port), app)
    http.serve_forever()


# 测试方法:
#可以開多個瀏覽器頁面:
#127.0.0.1:5006/python/你的網名
#然後進行互相通信