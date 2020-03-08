# -*- coding:utf-8 -*-
"""
Dec: 该版本不再使用Arduino开发板接受蓝牙和输出脉冲
Created on: 2020.03.07
Author: Iflier
"""
import re
import os
import sys
import time
import math
import platform
import argparse
from datetime import datetime
from threading import Thread, Event

import psutil
import serial


class BLTController(object):
    def __init__(self, port, baud):
        self.port = port
        self.baud = baud
        self.event = Event()
        self.com = serial.Serial(port=self.port, baudrate=self.baud, timeout=5)
    
    def description(self):
        print("Start from {0}".format(datetime.now().strftime("%c")))
        print("Serial Version: {0}".format(serial.VERSION))
        print("Psutil Version: {0}".format(".".join(map(lambda x: str(x), psutil.version_info))))
        print("Running on platform: {0} - {1}, Python: {2} - {3}".format(platform.system(), platform.machine(), platform.python_implementation(), platform.python_version()))
    
    def initHardware(self):
        # 设置方波发生器初始频率、占空比
        if self.com.is_open:
            print("[INFO] Initialization hardware ...")
            print("[INFO] Set up frequency to 23.5 KHz ...")
            self.com.write("F23.5".encode(encoding='utf-8'))
            time.sleep(0.25)  # 如果不添加延迟，对端来不及响应
            print("[INFO] Set up duty to 55 % ...")
            self.com.write("D2:055".encode(encoding='utf-8'))
            time.sleep(0.25)
            print("[INFO] Initialization done.")
        else:
            print("[ERROR] Unable to access hardware !")
    
    def computeUtilizationRatio(self):
        # 计算cpu平均利用率
        utilizationRatio = psutil.cpu_percent()
        return math.ceil(utilizationRatio)
    
    def autoRunMode(self):
        while self.com.is_open:
            if self.event.is_set():
                cpuUtilization = self.computeUtilizationRatio()
                if 0 < cpuUtilization and cpuUtilization <= 15:
                    fanSpeed = max(math.floor(55 - 0.8 * cpuUtilization), 0)
                elif cpuUtilization > 15 and cpuUtilization <= 100:
                    fanSpeed = max(math.floor(60 - 1.2 * cpuUtilization), 0)
                else:
                    fanSpeed = 50
                self.com.write("D2:{0:>03,d}".format(fanSpeed).encode(encoding='utf-8'))
                time.sleep(1.5)
            else:
                self.event.wait()
    
    def managedMode(self):
        while True:
            try:
                command = input("Command -->:").strip(" ").lower()
                print("Received command: {0}".format(command))
                if re.search(r"^\d+$|100$", command, re.I):
                    if not self.event.is_set():
                        duty = max(0, min(int(command), 55))
                        self.com.write("D2:{0:>03,d}".format(duty).encode(encoding='utf-8'))
                        time.sleep(0.3)
                    else:
                        print("[WARNING] Unable to hanle command in auto-run mode.")
                elif command in ['auto', 'exit', 'quit', 'cancel']:
                    if command == "auto":
                        if not self.event.is_set():
                            print("[INFO] Enter into auto-run mode ...")
                            # 进入自动设置模式
                            self.event.set()
                        else:
                            print("[INFO] Alerady in auto-run mode.")
                    elif command == "cancel":
                        if self.event.is_set():
                            print("[INFO] Exit from auto-run mode ...")
                            self.event.clear()
                        else:
                            print("[INFO] Alerady in managed mode .")
                    elif command in ['exit', 'quit']:
                        self.event.clear()
                        break
                    else:
                        print("[WARNING] Unknown command: {0}".format(command))
            except Exception as err:
                print("[ERROR] {0}".format(err))
                break
        self.com.write("F23.5".encode(encoding='utf-8'))
        time.sleep(0.3)
        self.com.write("D2:{0:>03,d}".format(55).encode())
        time.sleep(0.25)
        print("Bye.")
        self.com.close()
        sys.exit(0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="应用蓝牙主从设备之间通讯，控制智能风扇的实例")
    ap.add_argument('-p', '--port', type=str, default="COM4", help="指定使用的串口设备号")
    ap.add_argument('-b', '--baud', type=int, default=9600, help="指定串口波特率")
    args = vars(ap.parse_args())
    controller = BLTController(args['port'], args['baud'])
    if controller.com.is_open:
        controller.description()
        controller.initHardware()
        managedTh = Thread(target=controller.managedMode, args=())
        autoTh = Thread(target=controller.autoRunMode, args=(), daemon=True)
        autoTh.start()
        managedTh.start()
        managedTh.join()
    else:
        print("[ERROR] Unable to open serial port.")


