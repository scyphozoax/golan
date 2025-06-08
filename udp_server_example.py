import socket
import threading
import time

# 获取本机局域网IP地址
def get_local_ip():
    try:
        # 创建一个UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接一个外部地址（不发送数据，只是为了触发操作系统选择一个本地IP）
        s.connect(("8.8.8.8", 80))  # Google DNS server
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1" # Fallback to localhost if no network connection

# UDP服务器端
def udp_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"UDP Server listening on {host}:{port}")

    while True:
        data, addr = server_socket.recvfrom(1024) # buffer size is 1024 bytes
        print(f"Received message: {data.decode()} from {addr}")
        server_socket.sendto(b"Hello from server!", addr)

# UDP客户端端
def udp_client(server_ip, server_port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = b"Hello from client!"
    client_socket.sendto(message, (server_ip, server_port))
    print(f"Sent message: {message.decode()} to {server_ip}:{server_port}")

    try:
        client_socket.settimeout(5) # Set a timeout for receiving response
        data, addr = client_socket.recvfrom(1024)
        print(f"Received response: {data.decode()} from {addr}")
    except socket.timeout:
        print("No response from server within timeout.")
    finally:
        client_socket.close()

if __name__ == "__main__":
    local_ip = get_local_ip()
    print(f"你的IP地址为： {local_ip}")

    # 您可以在两台不同的电脑上运行此脚本，一台作为服务器，一台作为客户端。
    # 或者在同一台电脑上测试，但需要运行两次，一次作为服务器，一次作为客户端。

    # 示例：作为服务器运行
    server_thread = threading.Thread(target=udp_server, args=(local_ip, 12345))
    server_thread.daemon = True
    server_thread.start()
    print("服务器在单独的线程中启动，按Ctrl+C退出。")
    time.sleep(60) # Keep server running for a minute for testing

    # 示例：作为客户端运行
    # 请将 'TARGET_SERVER_IP' 替换为另一台电脑的IP地址，或者您自己的IP地址进行测试
    # udp_client('TARGET_SERVER_IP', 12345)

    print("\n--- 使用说明 ---")
    print("1. 在一台电脑上运行：python udp_example.py")
    print("2. 记下显示的 'Your local IP address is: ' (例如 192.168.1.100)")
    print("3. 如果您想作为服务器，请取消注释 `server_thread` 相关的代码，并运行脚本。")
    print("4. 如果您想作为客户端，请取消注释 `udp_client` 相关的代码，并将 `TARGET_SERVER_IP` 替换为服务器的IP地址，然后运行脚本。")
    print("5. 您可以在同一台电脑上打开两个终端，一个运行服务器，一个运行客户端进行测试。")
