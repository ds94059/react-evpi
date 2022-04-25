import threading
import subprocess

from flask import Flask, render_template
from flask_socketio import SocketIO

import requests
import rclpy

rclpy.init


def setInterval(func, sec):
    def func_wrapper():
        setInterval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


def call():
    print("hello")


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
app.debug = True


@socketio.on('message')
def handle_message(msg):
    print('received message: ' + msg)
    if(msg == 'pause'):
        pauseInstalling()
    elif(msg == 'continue'):
        continueInstalling()
    elif(msg == 'login'):
        # res = requests.post('https://hosted.mender.io/api/management/v1/useradm/auth/login',
        #                     auth=('ds94059@gmail.com', 'Mender-550837'))
        # JWT = res.cookies.get_dict()['JWT']
        JWT = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI0ZmU4Mzg4ZS04MzQ3LTRkYjEtYTkxMC1hOTk5NWIyOGJkYzAiLCJzdWIiOiJkNTJiMzAzNS04NjdmLTU5YWQtODBlOC0xMzJjYTFjZjViNGEiLCJleHAiOjE2NTEwNTIwMzUsImlhdCI6MTY1MDQ0NzIzNSwibWVuZGVyLnRlbmFudCI6IjYyNGQyMjQ4MjY2OTQ1ODUwZTMyZDhlNSIsIm1lbmRlci51c2VyIjp0cnVlLCJpc3MiOiJNZW5kZXIgVXNlcnMiLCJzY3AiOiJtZW5kZXIuKiIsIm1lbmRlci5wbGFuIjoiZW50ZXJwcmlzZSIsIm1lbmRlci50cmlhbCI6dHJ1ZSwibWVuZGVyLmFkZG9ucyI6W3sibmFtZSI6ImNvbmZpZ3VyZSIsImVuYWJsZWQiOnRydWV9LHsibmFtZSI6InRyb3VibGVzaG9vdCIsImVuYWJsZWQiOnRydWV9LHsibmFtZSI6Im1vbml0b3IiLCJlbmFibGVkIjp0cnVlfV0sIm5iZiI6MTY1MDQ0NzIzNX0.bkSxpGdUoKfyGxYjeVidK40es60whQ_AbgIB7wMowL_8h3wEduFNWXEam3pjo5oOIzD_XGER5rwlUor4NXgFAqLZU0CLp9hmdwLasxuWVWOvKGEvKlZxaaBhsGvRBaHS8vffVCOubQHgtLWWps-ZNdPzBsBxMU-vDZE911Im9XoeTYS_MRQdJnyMbVdX1C_qgDWmHRyL1EQWv6uPqSS1isUHqCVVst_DX4DFlEI5OWN-yngvZ8gwukpgRNZzyiG-A0oH3a1o8Oeyu_PUq0wDCeLN5D8BVqtB_36WEDsAlHCl2Ra7w1SE0fET0cRuLYiLS-oHrgzW2XQbZdvxLSjOlQmO4Z-dQ0BeyVEvaVgfFCz6BNHW8XovARNf2rlVnr3iNpw3nx_m9Gudp0CW2MH0aKKEr-lXm20W-oEHvaA9-sGTTUWbORApX9PXyASsDRsM1jbCSRXHd0Sm-PQO91qkIi8ilPKh4GGiVNAtXkboGzo_P3p2VFDXJvrZWtWhenCR"
        socketio.emit('JWT', JWT)
    elif(msg == 'rviz2'):
        thread_rviz = threading.Thread(target=thread_launch_rviz2)
        thread_rviz.start()
        thread_rviz.join()
    else:
        print('unknown command')


@socketio.on('checkUpdate')
def checkUpdate(JWT):
    author = 'Bearer ' + JWT
    headers = {'Authorization': author}
    res = requests.get(
        'https://hosted.mender.io/api/management/v1/deployments/deployments?status=inprogress', headers=headers)

    if(res.json()):
        print(res.json()[0]['name'])
        print('exist')
        socketio.emit('update', 'true')
    else:
        print('no update')
        socketio.emit('update', 'false')

# @app.route('/')
# def hello_world():
#     return "<p>Hello, World!</p>"


# @app.route('/continue')
def continueInstalling():
    pwd = 'user'
    cmd = 'python3 mender.py continue'

    subprocess.call('echo {} | sudo -S {}'.format(pwd, cmd),
                    shell=True, executable="/bin/bash")

#   return "<p>continue installing</p>"


# @app.route('/pause')
def pauseInstalling():
    pwd = 'user'
    cmd = 'python3 mender.py pause'

    subprocess.call('echo {} | sudo -S {}'.format(pwd, cmd),
                    shell=True, executable="/bin/bash")
    # return "<p>pause installing</p>"


def thread_launch_rviz2():
    subprocess.call('ros2 launch rviz2.py',
                    shell=True, executable="/bin/bash")


def main():
    # setInterval(call, 1)
    socketio.run(app, host='localhost')


if __name__ == "__main__":
    main()
