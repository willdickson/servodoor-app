import sys
import json
import time
import signal
import pathlib
import functools
import subprocess
import importlib.resources
import serial.tools.list_ports

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QTimer
from PySide6.QtCore import Slot 
from PySide6.QtCore import QObject 
from PySide6.QtWidgets import QFileDialog

from servodoor import ServoDoor


class AppBackend(QObject):
    """
    Backend for servodoor app
    """

    TIMER_PERIOD_MS = 5000

    def __init__(self, win):

        super().__init__()

        self.win = win
        self.win.doorSwitchClicked.connect(self.on_door_switch_clicked)
        self.win.openCloseButtonClicked.connect(self.on_open_close_button)
        self.win.readConfigFile.connect(self.on_read_config_file)
        self.win.setProperty("openCloseButtonText", "Open")
        self.win.setProperty("loadButtonEnabled", False)

        self.device = None
        self.port_info = None
        self.index_to_door = {}
        self.update_ports()

        self.timer = QTimer()
        self.timer.setInterval(self.TIMER_PERIOD_MS)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start()



    @Slot(str)
    def on_open_close_button(self, port):
        print('open/close button clicked')
        if self.device is None:
            self.timer.stop()
            self.open_device(port)
        else:
            self.close_device()
            self.timer.start()


    def open_device(self, port): 
        self.set_port_info(port)
        self.device = ServoDoor(port=port)
        self.win.setProperty("openCloseButtonText", "Close")
        self.win.setProperty("loadButtonEnabled", True)
        self.read_device_config()
        self.set_config_info()
        self.set_config_doors()


    def close_device(self): 
        self.device.close()
        self.device = None
        self.clear_port_info()
        self.clear_config_info()
        self.clear_config_doors()
        self.win.setProperty("openCloseButtonText", "Open")
        self.win.setProperty("loadButtonEnabled", False)


    @Slot(str)
    def on_door_switch_clicked(self, index, name, checked):
        print(f'door: {index}, {name}, {checked}')
        if self.device is None:
            return
        cmd = {name: 'open' if checked else 'close'}
        self.device.set_doors(cmd)


    @Slot(str)
    def on_read_config_file(self, filename):
        filename = filename.replace('file://', '')
        print(f'config file: {filename}')
        if self.device is None:
            return
        if not is_valid_json(filename):
            error_msg = f'file: {filename} does not contain valid json'
            self.win.setProperty('errorMessageText', error_msg)
            self.win.setProperty('errorMessageVisible', True)
            return 

        self.win.setProperty('configInfoText', f'\nuploading config and resetting device - please wait :) ')
        QTimer.singleShot(200, functools.partial(self.upload_config, filename))

    def on_timer(self):
        self.update_ports()


    def update_ports(self):
        print('update_ports')
        port_list = serial.tools.list_ports.comports()
        port_names = [item.device for item in port_list]
        if sys.platform.startswith('linux'):
            port_names = [item for item in port_names if 'ttyACM' in item]
        self.win.setProperty("serialPortNames", port_names)
        self.port_info = {item.device: item for item in port_list if item.device in port_names}


    def set_port_info(self, port): 
        port_info = self.port_info[port]
        lines = []
        lines.append(f'{port_info.device}')
        lines.append(f'{port_info.manufacturer}') 
        lines.append(f'{port_info.description}')
        for item in port_info.hwid.split(' ')[1:]:
            lines.append(item)
        info_str = '\n'.join(lines)
        self.win.setProperty('portInfoText', info_str)


    def clear_port_info(self):
        self.win.setProperty('portInfoText', '')


    def read_device_config(self):
        if self.device is None:
            return
        # Check for configuration errors
        rsp = self.device.get_config_errors()
        if not rsp['ok']: 
            self.win.setProperty('configInfoText', 'get_config_errors: ok=False')
            return
        if rsp['config_errors']:
            self.win.setProperty('configInfoText', f'errors: {rsp["config_errors"]}')
            return

        # Get device configuration
        rsp = self.device.get_config()
        if not rsp['ok']: 
            self.win.setProperty('configInfoText', 'get_config: ok=False')
            return
        self.config = rsp['config']


    def set_config_info(self):
        info_str = json.dumps(self.config, indent=4, sort_keys=True) 
        self.win.setProperty('configInfoText', info_str)


    def clear_config_info(self):
        self.win.setProperty('configInfoText', '')


    def set_config_doors(self):
        # Set door names
        door_names = [k for k in self.config]
        door_names.sort()
        self.index_to_door = {i:k for (i,k) in enumerate(door_names)}

        rsp = self.device.get_doors()
        door_checks = [False for item in door_names]
        if rsp['ok']:
            for i, name in self.index_to_door.items():
                door_checks[i] = False if rsp['doors'][name]=='close' else True 
        self.win.setProperty('doorChecks', door_checks)
        self.win.setProperty('doorNames', door_names)
        self.win.setProperty('numDoors', len(door_names))


    def clear_config_doors(self):
        self.index_to_door = {}
        self.win.setProperty('numDoors', 0)
        self.win.setProperty('doorChecks', [])
        self.win.setProperty('doorNames', [])


    def upload_config(self, filename):
        if self.device is None:
            return

        # Close connection to device and save port name
        port = self.device.port
        self.close_device()

        # Upload configuration file
        print(f'uploading {filename}')
        cmd_list = ['ampy', '-p', port, 'put', filename]
        subprocess.run(cmd_list)

        print('resetting device')
        cmd_list = ['ampy', '-p', port, 'reset', '--hard']
        subprocess.run(cmd_list)

        time.sleep(5.0)

        # Re-open connection to device
        self.open_device(port)



# -----------------------------------------------------------------------------------------------

def is_valid_json(filename):
    """
    Check if file contains valid json
    """
    rval = True
    with open(filename,'r') as f:
        try:
            json.load(f)
        except ValueError:
            rval = False
    return rval


def main():
    """
    App main entry point
    """
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QGuiApplication()
    engine = QQmlApplicationEngine()
    engine.quit.connect(app.quit)
    pkg_path = pathlib.Path(importlib.resources.files(__package__))
    qml_path = pathlib.Path(pkg_path, "main.qml")
    engine.load(str(qml_path))
    if not engine.rootObjects():
        print("app failed to load QML file")
        sys.exit(1)
    win = engine.rootObjects()[0]
    backend = AppBackend(win)
    engine.rootContext().setContextProperty("backend", backend)
    sys.exit(app.exec_())







