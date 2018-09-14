# -*- coding:utf-8 -*-
"""
Dec: 连接本地串口的蓝牙主机，控制从机#1和从机#2
Created on: 2018.09.12
Modified on: 2018.09.14
添加正则表达式，过滤来自console的输入命令
Author: Iflier
"""
print(__doc__)

import re
import os
import sys
import time
import math
import argparse
from threading import Thread, Event

import psutil
import serial

ap = argparse.ArgumentParser(description="开两个线程，一个线程接受console输入，直接向各个设备发送命令；另一个是受到另一个线程控制的线程")
ap.add_argument("-p", "--port", type=str, default="COM6", help="Specify a serial port to connect, such as COM6, ...")
ap.add_argument("-b", "--baudrate", type=int, default=9600, help="Specify a baud rate, such as 9600, 115200, ...")
# ap.add_argument("-d", "--debug", type=bool, default=False, help="Weather enter into debug mode.")
args = vars(ap.parse_args())

eventObj = Event()
CPUCORES = psutil.cpu_count(logical=True)  # 包含逻辑CPU个数
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
                fanSpeed = 33
            elif 10 < avergeSystemUtilization and avergeSystemUtilization <= 20:
                fanSpeed = 37
            elif 20 < avergeSystemUtilization and avergeSystemUtilization <= 30:
                fanSpeed = 43
            elif  30 < avergeSystemUtilization and avergeSystemUtilization <= 40:
                fanSpeed = 46
            elif 40 < avergeSystemUtilization and avergeSystemUtilization <= 50:
                fanSpeed = 52
            elif avergeSystemUtilization > 50:
                fanSpeed = 59
            else:
                fanSpeed = 0
            _ = serialObj.write(('N,2#' + str(fanSpeed) + ';').encode())  # 不要求应答，分号作为串口结束符
            time.sleep(6.0)
        else:
            eventObj.wait()  # 阻塞
    print("[ERROR] Failed to open serial port.")
    sys.exit(0)

def acceptCommandMode(serialObj, eventObj):
    # 包装后的命令以 'R' 开头表示要求有应答，以 'N' 开头的命令不需要应答
    if serialObj.is_open:
        while True:
            command = input("Command -->:").lower()  # 阻塞
            print("Recived command: {0}".format(command))
            if command in ["quit", "exit"]:
                _ = serialObj.write(('N,2#0;').encode())  # 不需要应答
                break
            elif command == "auto":
                eventObj.set()
            elif command == "cancel":
                eventObj.clear()
            elif command in ['a', 'p', 't']:
                _ = serialObj.write(('R,1#' + command + ';').encode())  # 要求有应答
                result = serialObj.readline().decode()
                print("Response -->: {0}".format(result))
            elif bool(re.match(r"[1-9]?\d?$|100$", command)):
                if not eventObj.is_set():
                    # 未进入auto模式下，允许从console控制fan
                    _ = serialObj.write(('R,2#' + command + ';').encode())  # 要求有应答
                    result = serialObj.readline().decode()
                    print("Response -->: {0}".format(result))
                else:
                    # 如果已经进入到Auto Run模式
                    print("[WARNNING] Fan in auto mode, exit from it please.")
            else:
                print("[ERROR] Received an unknown command: {0}".format(command))
        serialObj.close()
        sys.exit(0)
    else:
        print("[ERROR] Failed to open serial port.")
        sys.exit(0)

print("[INFO] Starting ...")
thList = list()
thList.append(Thread(target=acceptCommandMode, args=(com, eventObj)))
thList.append(Thread(target=autoRunMode, args=(com, eventObj), daemon=True))
for th in thList:
    th.start()
for th in thList:
    th.join()

print("Done.")
