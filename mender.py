# Copyright 2021 Northern.tech AS
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
"""example application to control the Update flow of the Mender client
"""

import os
import sys
import threading
from datetime import datetime, timedelta
from queue import Empty, SimpleQueue
from typing import Any, Tuple

from gi.repository.GLib import Error as DBusError  # type: ignore
from pydbus import SystemBus  # type: ignore

from flask import Flask, render_template
from flask_socketio import SocketIO

import requests


UPDATE_CONTROL_MAP_PAUSE_ALL = """{
	"priority": -1,
	"states": {
		"ArtifactInstall_Enter": {
			"action": "pause"
		},
		"ArtifactReboot_Enter": {
			"action": "pause"
		},
		"ArtifactCommit_Enter": {
			"action": "pause"
		}
	},
	"id": "01234567-89ab-cdef-0123-456789abcdef"
}"""

UPDATE_CONTROL_MAP_CONTINUE_INSTALL = """{
	"priority": -1,
	"states": {
		"ArtifactInstall_Enter": {
			"action": "continue"
		},
		"ArtifactReboot_Enter": {
			"action": "continue"
		},
		"ArtifactCommit_Enter": {
			"action": "continue"
		}
	},
	"id": "01234567-89ab-cdef-0123-456789abcdef"
}"""

UPDATE_CONTROL_MAP_CONTINUE_REBOOT = """{
	"priority": -1,
	"states": {
		"ArtifactInstall_Enter": {
			"action": "pause"
		},
		"ArtifactReboot_Enter": {
			"action": "continue"
		},
		"ArtifactCommit_Enter": {
			"action": "pause"
		}
	},
	"id": "01234567-89ab-cdef-0123-456789abcdef"
}"""

UPDATE_CONTROL_MAP_CONTINUE_COMMIT = """{
	"priority": -1,
	"states": {
		"ArtifactInstall_Enter": {
			"action": "pause"
		},
		"ArtifactReboot_Enter": {
			"action": "pause"
		},
		"ArtifactCommit_Enter": {
			"action": "continue"
		}
	},
	"id": "01234567-89ab-cdef-0123-456789abcdef"
}"""


# Queue to send maps from user to D-Bus thread
set_new_map_queue = SimpleQueue()  # type: SimpleQueue

# Queue to send error messages from D-Bus to user thread
dbus_error_queue = SimpleQueue()  # type: SimpleQueue


def clear_console():
    """Clear console. Use "clear" for Linux and "cls" for Windows."""
    command = "clear"
    if os.name in ("nt", "dos"):
        command = "cls"
    os.system(command)


def ask(text: str) -> str:
    """Ask a question and return the reply."""

    sys.stdout.write(text)
    sys.stdout.flush()
    reply = sys.stdin.readline().strip()
    sys.stdout.write("\n")
    return reply


def set_update_control_map(
    io_mender_update1_object: Any, update_control_map: str
) -> Tuple[str, int]:
    """Set the given Update Control Map in Mender using D-Bus method
    io.mender.Update1.SetUpdateControlMap. Returns [error_msg,refresh_timeout]
    """
    try:
        refresh_timeout = io_mender_update1_object.SetUpdateControlMap(
            update_control_map
        )
    except DBusError as dbus_error:
        return dbus_error, 30

    if refresh_timeout == 0:
        err_msg = "io.mender.Update1.SetUpdateControlMap returned refresh_timeout=0"
        return err_msg, 30

    return "", refresh_timeout


def do_handle_update_control_map():
    """Manage D-Bus communication with the Mender client

    At start, initializes the proxy D-Bus object and sets a pause all Update
    Control Map. Then, it will wait either for an expire of the current map to
    just refresh it, or a new map coming from the queue to set that one instead.
    """

    # Get the D-Bus proxy object interface io.mender.Update1
    try:
        remote_object = SystemBus().get(
            bus_name="io.mender.UpdateManager", object_path="/io/mender/UpdateManager"
        )["io.mender.Update1"]
    except DBusError as dbus_error:
        dbus_error_queue.put(dbus_error)
        return

    # Initialize the Update Control Map for pause in all states
    err_msg, refresh_timeout = set_update_control_map(
        remote_object, UPDATE_CONTROL_MAP_PAUSE_ALL
    )
    if err_msg != "":
        dbus_error_queue.put(err_msg)
        return

    current_map = UPDATE_CONTROL_MAP_PAUSE_ALL
    next_refresh_at = datetime.now() + timedelta(0, refresh_timeout - 1)

    err_msg = ""
    while not err_msg:
        try:
            new_map = set_new_map_queue.get(timeout=0.2)
        except Empty:
            pass
        else:
            err_msg, refresh_timeout = set_update_control_map(
                remote_object, new_map)
            current_map = new_map
            next_refresh_at = datetime.now() + timedelta(0, refresh_timeout - 1)

        if next_refresh_at <= datetime.now():
            err_msg, refresh_timeout = set_update_control_map(
                remote_object, current_map
            )
            next_refresh_at = datetime.now() + timedelta(0, refresh_timeout - 1)

    # An error ocurred, report to the queue and exit
    dbus_error_queue.put(err_msg)


def do_main_interactive(newMap):
    """Interactively ask the user for input and apply the desired Update Control
    Map
    """

    # Wait up to 500ms for D-Bus errors from initialization
    try:
        dbus_err = dbus_error_queue.get(timeout=0.5)
    except Empty:
        pass
    else:
        print(f"ERROR: {dbus_err}")
        return

    # current_map = UPDATE_CONTROL_MAP_PAUSE_ALL

    set_new_map_queue.put(newMap)

    # Wait up to 500ms for D-Bus errors from setting the map
    try:
        dbus_err = dbus_error_queue.get(timeout=0.5)
    except Empty:
        pass
    else:
        print(f"ERROR: {dbus_err}")
        return

    # while True:
    #     # clear_console()
    #     print("Current map is:")
    #     print(current_map)
    #     print("-----------------------")
    #     print("What do you want to do?")
    #     print("  0) Pause on all states")
    #     print("  1) Continue with Installing new software")
    #     print("  2) Continue with Rebooting")
    #     print("  3) Continue with Committing new software")
    #     print("  q) Quit")

    #     reply = ask("Choice? ")
    #     if reply.lower() == "q":
    #         return

    #     if reply == "0":
    #         set_new_map_queue.put(UPDATE_CONTROL_MAP_PAUSE_ALL)
    #         current_map = UPDATE_CONTROL_MAP_PAUSE_ALL
    #     elif reply == "1":
    #         set_new_map_queue.put(UPDATE_CONTROL_MAP_CONTINUE_INSTALL)
    #         current_map = UPDATE_CONTROL_MAP_CONTINUE_INSTALL
    #     elif reply == "2":
    #         set_new_map_queue.put(UPDATE_CONTROL_MAP_CONTINUE_REBOOT)
    #         current_map = UPDATE_CONTROL_MAP_CONTINUE_REBOOT
    #     elif reply == "3":
    #         set_new_map_queue.put(UPDATE_CONTROL_MAP_CONTINUE_COMMIT)
    #         current_map = UPDATE_CONTROL_MAP_CONTINUE_COMMIT
    #     else:
    #         print(f"Unknown option: {reply}")

    #     # Wait up to 500ms for D-Bus errors from setting the map
    #     try:
    #         dbus_err = dbus_error_queue.get(timeout=0.5)
    #     except Empty:
    #         pass
    #     else:
    #         print(f"ERROR: {dbus_err}")
    #         return


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
    thread_main = threading.Thread(
        target=do_main_interactive(UPDATE_CONTROL_MAP_CONTINUE_INSTALL))
    thread_main.start()
#     return "<p>continue installing</p>"


# @app.route('/pause')
def pauseInstalling():
    # do_main_interactive(UPDATE_CONTROL_MAP_PAUSE_ALL)
    thread_main = threading.Thread(
        target=do_main_interactive(UPDATE_CONTROL_MAP_PAUSE_ALL))
    thread_main.start()
    # return "<p>pause installing</p>"


def main():
    # print(args+" installing")
    """Entry point function: start one thread to handle the D-Bus interface and
    another to handle user input.
    """
    # if(args == "continue"):
    #     thread_main = threading.Thread(
    #         target=do_main_interactive(UPDATE_CONTROL_MAP_CONTINUE_INSTALL))
    # elif(args == "pause"):
    #     thread_main = threading.Thread(
    #         target=do_main_interactive(UPDATE_CONTROL_MAP_PAUSE_ALL))
    # else:
    #     print("unknown args")
    #     return

    thread_dbus = threading.Thread(target=do_handle_update_control_map)
    thread_dbus.daemon = True

    # thread_main.start()
    thread_dbus.start()

    # thread_main.join()

    # setInterval(call, 1)
    socketio.run(app, host='localhost')


if __name__ == "__main__":
    # main(sys.argv[1])
    main()
