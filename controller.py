# -*- coding:utf-8 -*-
"""
Dec: 连接本地串口的蓝牙主机，控制从机#1和从机#2
Created on: 2018.09.12
Author: Iflier
"""
print(__doc__)

import os
import sys
import time
import math
import signal
import argparse
from threading import Thread, Event

import psutil
import serial

ap = argparse.ArgumentParser(description="开两个线程，一个线程接受console输入，直接向各个设备发送命令；另一个是受到另一个线程控制的线程")
ap.add_argument("-p", "--port", type=str, default="COM6", help="Specify a serial port to connect, such as COM6, ...")
ap.add_argument("-b", "--baudrate", type=int, default=9600, help="Specify a baud rate, such as 9600, 115200, ...")
args = vars(ap.parse_args())

eventObj = Event()
CPUCORES = psutil.cpu_count(logical=True)
com = serial.Serial(port=args["port"], baudrate=args["baudrate"], timeout=7)


def autoRunMode(serialObj, eventObj):
    # 包装后的命令以I开头表示发送的是整数
    while serialObj.is_open:
        if eventObj.is_set():
            # 每一个逻辑处理器的使用率
            systemUtilizationPerCore = psutil.cpu_percent(percpu=True)
            # 各个逻辑处理器的利用率总和
            systemUtilization = math.ceil(sum(systemUtilizationPerCore))
            # 处理器核心的平均使用率
            avergeSystemUtilization = math.ceil(systemUtilization / CPUCORES)
            if avergeSystemUtilization <= 10:
                fanSpeed = 20
            elif 10 < avergeSystemUtilization and avergeSystemUtilization <= 20:
                fanSpeed = 25
            elif 20 < avergeSystemUtilization and avergeSystemUtilization <= 30:
                fanSpeed = 35
            elif  30 < avergeSystemUtilization and avergeSystemUtilization <= 40:
                fanSpeed = 50
            elif 40 < avergeSystemUtilization and avergeSystemUtilization <= 50:
                fanSpeed = 60
            elif avergeSystemUtilization > 50:
                fanSpeed = 75
            else:
                fanSpeed = 0
            _ = serialObj.write(('I,2#' + str(fanSpeed) + ';').encode())  # 分号作为串口结束符
            time.sleep(6.0)
        else:
            eventObj.wait()  # 阻塞
    print("[ERROR] Failed to open serial port.")
    sys.exit(0)

def acceptCommandMode(serialObj, eventObj):
    # 包装后的命令以S开头表示发送的是字符串，要求字符串命令串口最好是有返回
    if serialObj.is_open:
        while True:
            command = input("Command -->:").lower()  # 阻塞
            if command in ["quit", "exit"]:
                break
            elif command == "auto":
                eventObj.set()
            elif command == "cancel":
                eventObj.clear()
            else:
                if command in ['a', 'p', 't']:
                    _ = serialObj.write(('S,1#' + command + ';').encode())
                    result = serialObj.readline().decode()
                    print("Response -->: {0}".format(result))
                else:
                    if not eventObj.is_set():
                        # 未进入auto模式下，允许从console控制fan
                        _ = serialObj.write(('S,2#' + command + ';').encode())
                        result = serialObj.readline().decode()
                        print("Response -->: {0}".format(result))
                    else:
                        print("[WARN] Fan in auto mode, exit from it please.")
        serialObj.close()
    else:
        print("[ERROR] Failed to open serial port.")
        sys.exit(0)

print("[INFO] Starting ...")
thList = list()
thList.append(Thread(target=acceptCommandMode, args=(com, eventObj)))
thList.append(Thread(target=autoRunMode, args=(com, eventObj)))
for th in thList:
    th.start()
for th in thList:
    th.join()

print("Done.")
