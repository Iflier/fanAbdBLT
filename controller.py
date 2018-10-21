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
ap.add_argument("-p", "--port", type=str, default="COM6", required=False, help="Specify a serial port to connect, such as COM6, ...")
ap.add_argument("-s", "--sleeptime", type=int, default=6, required=False, help="Set interval time value.")
ap.add_argument("-d", "--debug", action="store_true", required=False, help="Weather enter into debug mode.")
args = vars(ap.parse_args())

eventObj = Event()
CPUCORES = psutil.cpu_count(logical=True)  # 包含逻辑CPU个数
com = serial.Serial(port=args["port"], baudrate=9600, timeout=5)


def autoRunMode(serialObj, eventObj):
    while serialObj.is_open:
        if eventObj.is_set():
            # 每一个逻辑处理器的使用率
            systemUtilizationPerCore = psutil.cpu_percent(percpu=True)
            # 各个逻辑处理器的利用率总和
            systemUtilization = math.ceil(sum(systemUtilizationPerCore))
            # 处理器核心的平均使用率
            avergeSystemUtilization = math.ceil(systemUtilization / CPUCORES)
            if 0 <= avergeSystemUtilization <= 100:
                fanSpeed = 29 + math.ceil(0.4 * avergeSystemUtilization)
            else:
                fanSpeed = 0
            _ = serialObj.write(('N,2#' + str(fanSpeed) + ';').encode())  # 不要求应答，分号作为串口结束符
            time.sleep(args["sleeptime"])
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
                if eventObj.is_set():
                    """退出之前先从自动调速模式下退出，不关机重新进入时，不用从上次的自动调速模式下退出"""
                    eventObj.clear()
                _ = serialObj.write(('N,2#0;').encode())  # 不需要应答
                break
            elif command == "auto":
                eventObj.set()
            elif command == "cancel":
                print("Exit from auot run mode.")
                eventObj.clear()
            elif command in ['a', 'p', 't']:
                _ = serialObj.write(('R,1#' + command + ';').encode())  # 要求有应答
                result = serialObj.readline().decode()
                print("Response -->: {0}".format(result))
            elif bool(re.match(r"[1-9]?\d?$|100$", command)):  # 匹配1~100之间的字符
                if not eventObj.is_set():
                    # 未进入auto模式下，允许从console控制fan
                    _ = serialObj.write(('R,2#' + command + ';').encode())  # 要求有应答
                    result = serialObj.readline().decode()
                    print("Response -->: {0}".format(result))
                else:
                    # 如果已经进入到Auto Run模式
                    print("[WARNNING] Fan in auto run mode, exit from it please.")
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
thList[0].join()

print("Done.")
