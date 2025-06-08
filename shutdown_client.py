import socket
import json

SERVER_IP = '43.160.204.239' # Replace with your server's public IP
SERVER_PORT = 60666 # Must match the server's port

def send_shutdown_command():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    shutdown_message = json.dumps({'type': 'shutdown', 'client_id': 'shutdown_initiator'}) # client_id can be anything
    try:
        client_socket.sendto(shutdown_message.encode(), (SERVER_IP, SERVER_PORT))
        print(f"向 {SERVER_IP}:{SERVER_PORT} 发送关机命令了。")
    except Exception as e:
        print(f"发送关机命令时出现了错误： {e}")
    finally:
        client_socket.close()

if __name__ == '__main__':
    send_shutdown_command()