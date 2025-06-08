# Game On LAN
Game On LAN（GOLAN）是用于游戏的局域网联机的软件。
该软件分为客户端和服务器端两个部分。



## 前置
### 服务器端
**您需要自备一个已安装Linux系统的服务器。**

需要Python 3.x（一般应该是自带的）

服务器开放60666端口

将`rendezvous_server.py`上传至服务器并输入
```
cd /your_self_set/
python3 rendezvous_server.py
```
来启动服务器端文件。

启动成功之后会收到
```
Rendezvous 服务器正在监听 0.0.0.0:60666
```

### 客户端
**.exe文件不需要准备环境。**

**如果您要使用`.py`文件，请先安装`python 3.x`。**

Python 2.7.9 + 或 Python 3.4+ 以上版本都自带 pip 工具。3.x版本可以通过`pip3 --version`来判断是否有 pip 。

若您没有 pip 工具，请到 **[pip官网](https://pypi.org/project/pip/ "pip官网")** 下载。

除此之外，在客户端需要需要安装：
pytuntap
pywin32

安装方式：
```
    pip install python-pytuntap
    pip install pywin32
```

## 客户端使用方式
**该软件需要获取管理员权限**，以便于使用 TUN/TAP ，在打开GUI后，您需要输入：
- 目标IP（IP为局域网分配的IP）
- 中继服务器地址（需要填入IP:端口，本软件使用60666端口，需要在服务器端的防火墙开放该端口）
- 您的客户端ID（客户端ID不能和其他人相同，否则会出现意外的问题）
- 请求对等客户端ID（对方所使用的客户端ID）
- 本地游戏UDP端口（请在此填入游戏内局域网联机开放的端口）

1. 按要求输入好之后，请先点击`发送测试消息（局域网）`，在服务器终端查看是否可以收到信息；
您会收到：
```
已发送消息: 来自GUI客户端的消息! 到 IP.IP.IP.IP:PORT
```
2. 之后点击`连接服务器并注册`以注册您的ID，对方也需要注册一次，此时服务器终端可以收到
```
已注册客户端：client_1 来自 IP.IP.IP.IP:PORT
已注册客户端：client_2 来自 IP.IP.IP.IP:PORT
```
此时连接成功，服务器状态会显示“在线”
***P.S.目前不清楚监测功能为何会一会在线一会离线，该功能仅供参考。***
3. 点击`请求对顶客户端信息`以进行UDP打洞，此时日志会显示
```
已向服务器请求客户端ID 'client_1' 的对等客户端信息。
收到消息: {"type": "peer_info", "client_id": "client_1", "public_ip": "IP.IP.IP.IP", "public_port": PORT} 来自 YOUR_SERVER_IP:60666
收到客户端ID 'client_1' 的对等客户端信息: IP1.IP1.IP1.IP1:PORT
尝试向 IP2:IP2:IP2:IP2:PORT 打洞
已发送消息: UDP打洞尝试! 到 IP2:IP2:IP2:IP2:PORT
已发送打洞数据包。
```
4. 点击`开始游戏数据转发`即可，
若您想关闭联机，点击`停止游戏数据转发`，并关闭客户端即可。
