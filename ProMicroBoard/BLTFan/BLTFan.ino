/*
   串口连接蓝牙从机，io口连接fan控制引脚
*/
#include <FanController.h>

//与4Pin风扇相关的定义
//转速输出引脚。可用0,1,2,3,7
#define SENSOR_PIN 2

//读取转速的间隔，以毫秒为单位
#define SENSOR_THRESHOLD 1600
//PWM输入引脚。3,5,6,9,10
#define PWM_PIN 3

unsigned int rpms = 0;
int fanSpeed;

boolean stringCompleted;
String inputString = "";
String command = "";
String deviceNum = "";
String responseFlag = "";
int colonIndex, hasheIndex;
boolean stringComplete = false;  // whether the string is complete

FanController fan(SENSOR_PIN, SENSOR_THRESHOLD, PWM_PIN);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  //  蓝牙串口设备
  Serial1.begin(9600);
  fan.begin();
  fan.setDutyCycle(byte(30));
}

void loop() {
  // put your main code here, to run repeatedly:
  if (stringCompleted) {
    Serial.print(deviceNum);
    if (deviceNum.equals("2#")) {
      // 仅响应针对2#设备发送的指令
      Serial.print("Recived speed = ");Serial.println(command);
      fanSpeed = command.toInt();
      byte target = max(min(fanSpeed, 100), 0);
      fan.setDutyCycle(target);
      Serial.println(rpms);
      if (responseFlag.equals("R")) {
//      要求发送应答
        rpms = fan.getSpeed();
        delay(300);
        rpms = fan.getSpeed();
        Serial1.print(rpms);
        Serial1.println("/RPMS");
        }
    }
    responseFlag = "";
    inputString = "";
    command = "";
    stringCompleted = false;
    delay(900);
  //  Serial.println("Return to normal.");
  }
}

//接受串口USB数据
void serialEvent1() {
  while (Serial1.available()) {
//    接收字符间隔短，会出现第一个字符被漏掉的情况
    delay(20);
    char inChar = (char)Serial1.read();
    inputString += inChar;
    if (inChar == ';') {
      stringCompleted = true;
      Serial.print(inputString);
      Serial.println();
      inputString.toUpperCase();
      responseFlag = inputString.substring(0, 1);
      Serial.print(responseFlag);
      deviceNum = inputString.substring(2, 4);
      hasheIndex = inputString.indexOf("#", 0);
      colonIndex = inputString.indexOf(";", 0);
      Serial.print("Index of #(should be 3): ");Serial.println(hasheIndex);
      Serial.print("deviceNum: ");Serial.println(deviceNum);
//    从#字符后一个字符开始至分号之间为命令字符串
      command = inputString.substring(hasheIndex + 1, colonIndex);
    }
  }
}
