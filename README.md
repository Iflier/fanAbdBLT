# 基于串口的多蓝牙设备通信
## 目的
&nbsp;&nbsp;&nbsp;&nbsp;盼望着，盼望着，夏天即将过去。使用游戏本来编写程序，好处是显而易见的，弊端是也是显而易见的。</br>
`钢铁侠`里面有句话，让我印象深刻——`一切都可以由科技达成`。作为懂得一点点硬件知识的菜鸟程序员来说，我非常认同前面那句话。</br>
想法早已有之，缺的是买材料的银子和场地呀。然而，只要`贼心不死`，就没有办不到的事。</br>

这一整套控制系统由`Arduino开发板`、`mini Arduino`、`USB转TTL`、`蓝牙`、`BMP180`、`服务器级开关电源`和`涡轮风扇`组成。</br>
由本本上开的console输入命令，通过USB转串口连接到蓝牙`（master角色）`设备，它可以连接若干个蓝牙从机，由该蓝牙设备把指令发送给蓝牙从机</br>
1#从机用于测量当前环境的物理量，如温度，气压等。2#从机，连接涡轮风扇，根据指令控制涡轮风扇的转速，强制送风，实现降温效果。</br>
好久都没有和人说话了，可能表达的意思不完整 :-)，快递的一些电子产品还没有到，但是控制涡轮风扇的功能已经调试好了，先看看吧</br>
![image](https://github.com/Iflier/fanAndBLT/blob/master/images/1.jpg)</br>
涡轮风扇，很强大</br>
![image](https://github.com/Iflier/fanAndBLT/blob/master/images/2.jpg)</br>

## Update `2018.09.16`

缺的小东西买回来了，然后发现`master`设备并不能连接两个`slaver`设备，尽管已经修改了`master`设备的`INQM`选项。

## Update `2018.09.29`

当涡轮风扇的转速与计算机`CPU`平均利用率呈线性关系的时候，风扇的噪声比较大</br>

## Update `2018.10.02`

由于单片机端的串口已经被指定了，那么在`PC`端指定串口波特率无意义，已删除该选项

## Update `2018.10.21`

## Update `2020.03.07`

使用带有串口接口的 `PWM` 发生器模块替代 `mini Arduino` 组件。使用`mini Arduino`有以下几个缺点：</br>
1、调试的时候比较麻烦，如果连接出错，可能导致该组件永久损坏；</br>
2、需要与`4 Pin`风扇的电源共地，而`mini Arduino`本身又占用计算机的一个USB端口，这样不太好。已有的现象是，鼠标出现卡顿现象。应用该方案后，该现象解除  
现在使用的是如下图所示的带有串口功能的PWM模块。通过CP2012连接，可以直接操作它：
![image](https://github.com/Iflier/fanAndBLT/blob/linearSpeed/images/PWM%E6%A8%A1%E5%9D%97.PNG)  


`Go`语言版的实现，参见[这个链接](https://github.com/Iflier/fanAndBLTGo/tree/useSwitch)
