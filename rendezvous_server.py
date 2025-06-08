import socket
import threading
import json
import time
import argparse # 导入 argparse 模块

SERVER_IP = '0.0.0.0'
SERVER_PORT = 60666 # 使用与客户端 GUI 不同的端口

clients = {}
running = True # 添加一个全局标志来控制服务器的运行状态

def handle_client(data, addr, server_socket):
    global running
    try:
        # 优先检查简单的状态检查消息
        if data == b"status_check":
            # （可选）发送一个响应以确认服务器在线
            server_socket.sendto(b"server_alive", addr) # 取消注释此行
            # print(f"收到来自 {addr} 的状态检查请求") # 移除此行
            return

        message = json.loads(data.decode())
        msg_type = message.get('type')
        client_id = message.get('client_id')

        if msg_type == 'register':
            clients[client_id] = {'address': addr, 'public_ip': addr[0], 'public_port': addr[1]}
            print(f"已注册客户端：{client_id} 来自 {addr[0]}:{addr[1]}")
            # （可选）向客户端发送确认信息
            # server_socket.sendto(json.dumps({'type': 'registered', 'client_id': client_id}).encode(), addr)

        elif msg_type == 'request_peer':
            peer_id = message.get('peer_id')
            if peer_id in clients:
                peer_info = clients[peer_id]
                # 将对端公共信息发送回请求客户端
                response_message = json.dumps({
                    'type': 'peer_info',
                    'client_id': peer_id,
                    'public_ip': peer_info['public_ip'],
                    'public_port': peer_info['public_port']
                })
                server_socket.sendto(response_message.encode(), addr)
                print(f"已发送 {peer_id} 的节点信息给 {client_id}")
            else:
                print(f"未找到客户端 {client_id} 请求的对端 {peer_id}")
                # （可选）向客户端发送错误信息
                # server_socket.sendto(json.dumps({'type': 'error', 'message': 'Peer not found'}).encode(), addr)

        elif msg_type == 'shutdown':
            print(f"收到来自 {addr} 的关机命令。正在关闭服务器...")
            running = False # 将运行标志设置为 False 以停止服务器循环

        else:
            print(f"来自 {addr} 的未知消息类型: {message}")

    except json.JSONDecodeError:
        # 只有当接收到的数据不是预期的 status_check 消息时才打印错误
        if data != b"status_check":
            print(f"收到来自 {addr} 的非 JSON 消息: {data.decode(errors='ignore')}")
    except Exception as e:
        print(f"处理客户端 {addr} 时出错: {e}")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.settimeout(1) # 设置超时以允许检查运行标志
    print(f"Rendezvous 服务器正在监听 {SERVER_IP}:{SERVER_PORT}")

    while running:
        try:
            data, addr = server_socket.recvfrom(1024) # 缓冲区大小 1024 字节
            # 在新线程中处理客户端以避免阻塞
            client_handler = threading.Thread(target=handle_client, args=(data, addr, server_socket))
            client_handler.start()
        except socket.timeout:
            pass # 超时发生，再次检查运行标志
        except Exception as e:
            print(f"服务器循环中出错: {e}")
            break
    
    server_socket.close()
    print("服务器已关闭。")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Rendezvous Server")
    parser.add_argument('--daemon', '-d', action='store_true', help='Run server in daemon mode')
    args = parser.parse_args()

    if args.daemon:
        import subprocess
        import sys
        # 重新启动脚本作为后台进程
        # 注意：在 Windows 上，这会打开一个新的控制台窗口。
        # 对于更健壮的后台运行，可能需要使用 pyinstaller 打包成 .exe 并使用 Windows 服务或类似工具。
        # 或者使用第三方库如 python-daemon (Linux/macOS) 或 pywin32 (Windows)。
        subprocess.Popen([sys.executable, __file__], creationflags=subprocess.DETACHED_PROCESS, close_fds=True)
        print("Rendezvous Server is starting in daemon mode.")
        sys.exit(0)
    else:
        start_server()