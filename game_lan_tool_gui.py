import tkinter as tk
import socket
import threading
import time
import json # Import json for message serialization
import os # Import os for path operations
import tuntap # Import tuntap for virtual network interface
import os
import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    if not is_admin():
        # Re-run the program with admin rights
        script = os.path.abspath(sys.argv[0])
        params = ' '.join(sys.argv)
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        except Exception as e:
            print(f"Error elevating privileges: {e}")
        sys.exit(0)

class GameLanToolGUI:
    CONFIG_FILE = "config.json"

    def __init__(self, master):
        self.master = master
        master.title("Game On LAN - 客户端")

        # Log area - MUST be initialized before any log calls
        self.log_text = tk.Text(master, height=10, width=50)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) # 将日志区域放置在左侧，并填充和扩展
        self.log_text.config(state=tk.DISABLED) # 设置为只读

        # Add a scrollbar to the log area
        self.log_scrollbar = tk.Scrollbar(master, command=self.log_text.yview)
        self.log_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.log_text.config(yscrollcommand=self.log_scrollbar.set)

        self.local_ip = self.get_local_ip()
        self.log(f"本地IP: {self.local_ip}")

        # Label for local IP
        self.ip_label = tk.Label(master, text=f"本地IP: {self.local_ip}")
        self.ip_label.pack()

        # Input field for target IP (for direct LAN communication)
        self.target_ip_label = tk.Label(master, text="目标IP (局域网):")
        self.target_ip_label.pack()
        self.target_ip_entry = tk.Entry(master)
        self.target_ip_entry.pack()

        # Button to send message (for direct LAN communication)
        self.send_button = tk.Button(master, text="发送测试消息 (局域网)", command=self.send_test_message)
        self.send_button.pack()

        # --- Rendezvous Server Interaction ---
        self.server_address_label = tk.Label(master, text="中继服务器地址 (IP:端口):")
        self.server_address_label.pack()
        self.server_address_entry = tk.Entry(master)
        self.server_address_entry.pack()

        self.client_id_label = tk.Label(master, text="您的客户端ID:")
        self.client_id_label.pack()
        self.client_id_entry = tk.Entry(master)
        self.client_id_entry.pack()

        self.connect_button = tk.Button(master, text="连接服务器并注册", command=self.connect_and_register)
        self.connect_button.pack()

        self.request_peer_id_label = tk.Label(master, text="请求对等客户端ID:")
        self.request_peer_id_label.pack()
        self.request_peer_id_entry = tk.Entry(master)
        self.request_peer_id_entry.pack()

        self.request_peer_button = tk.Button(master, text="请求对等客户端信息", command=self.request_peer_info)
        self.request_peer_button.pack()

        # Server Status Label
        self.server_status_label = tk.Label(master, text="服务器状态: 未知", fg="gray")
        self.server_status_label.pack()

        # --- Game Data Forwarding ---
        self.game_port_label = tk.Label(master, text="本地游戏UDP端口:")
        self.game_port_label.pack()
        self.game_port_entry = tk.Entry(master)
        self.game_port_entry.pack()

        self.start_forwarding_button = tk.Button(master, text="开始游戏数据转发", command=self.start_game_forwarding)
        self.start_forwarding_button.pack()

        self.stop_forwarding_button = tk.Button(master, text="停止游戏数据转发", command=self.stop_game_forwarding, state=tk.DISABLED)
        self.stop_forwarding_button.pack()
        # --- End Game Data Forwarding ---

        # UDP Socket
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_port = 12345 # Use a fixed port for consistency
        try:
            # Bind the socket to the local IP and port for receiving
            self.udp_socket.bind((self.local_ip, self.udp_port))
            self.log(f"UDP socket bound to {self.local_ip}:{self.udp_port}")
        except socket.error as e:
            self.log(f"Error binding UDP socket: {e}")
            # Handle error, maybe exit or disable functionality

        # Start UDP receiving thread
        self.receive_thread = threading.Thread(target=self.receive_udp_messages, daemon=True)
        self.receive_thread.start()
        self.log("UDP receiving thread started.")

        self.server_address = None
        self.client_id = None
        self.peer_address = None # Store peer's address for forwarding
        self.game_forwarding_socket = None
        self.game_forwarding_thread = None
        self.forwarding_running = False

        self.tun = None # Initialize TUN device
        self.tun_read_thread = None

        # Load configuration on startup
        self.load_config()

        # Add a flag to track registration status
        self.is_registered = False

        # Start periodic server status check
        self.check_server_status()

        # Bind the window closing event to save configuration
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Removed Help Button
        # self.help_button = tk.Button(master, text="帮助", command=self.show_help)
        # self.help_button.grid(row=10, column=0, columnspan=2, pady=5)

    def get_local_ip(self):
        try:
            # Create a temporary socket to get the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80)) # Connect to a public server (doesn't send data)
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "无法获取本地IP"

    def log(self, message):
        self.log_text.config(state=tk.NORMAL) # 临时设置为可写
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END) # Auto-scroll to the bottom
        self.log_text.config(state=tk.DISABLED) # 重新设置为只读

        self.log_text.see(tk.END) # Auto-scroll to the bottom

    def send_test_message(self):
        target_ip = self.target_ip_entry.get()
        if not target_ip:
            self.log("请输入目标IP。")
            return

        message = "来自GUI客户端的消息!"
        # Send message in a separate thread to avoid blocking GUI
        send_thread = threading.Thread(target=self.send_udp_message, args=(target_ip, self.udp_port, message))
        send_thread.start()

    def send_udp_message(self, ip, port, message):
        try:
            self.udp_socket.sendto(message.encode(), (ip, port))
            self.log(f"已发送消息: {message} 到 {ip}:{port}")
        except socket.error as e:
            self.log(f"发送消息到 {ip}:{port} 时出错: {e}")

    def receive_udp_messages(self):
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(1024) # Buffer size 1024 bytes
                message = data.decode()
                self.log(f"收到消息: {message} 来自 {addr[0]}:{addr[1]}")

                # Basic message handling (can be expanded)
                try:
                    msg_obj = json.loads(message)
                    if msg_obj.get("type") == "peer_info":
                        peer_id = msg_obj.get("client_id")
                        peer_public_ip = msg_obj.get("public_ip")
                        peer_public_port = msg_obj.get("public_port")
                        self.log(f"收到客户端ID '{peer_id}' 的对等客户端信息: {peer_public_ip}:{peer_public_port}")
                        self.peer_address = (peer_public_ip, peer_public_port) # Store peer address
                        # Now attempt UDP hole punching
                        self.attempt_hole_punching(peer_public_ip, peer_public_port)
                except json.JSONDecodeError:
                    # Not a JSON message, treat as simple text message
                    pass # Already logged as received message

            except socket.timeout:
                pass # Ignore timeout errors
            except socket.error as e:
                self.log(f"接收消息时出错: {e}")
                break # Exit thread on error
            except Exception as e:
                self.log(f"接收过程中发生意外错误: {e}")
                break

    def init_tun_device(self):
        try:
            # Create a TUN device named 'tun0'
            self.tun = tuntap.TunTap(nic_type="Tun", nic_name="tun0")
            # Configure a virtual IP address for the TUN device
            # This IP should be in a different subnet than your physical network
            # And should be unique for each client in the virtual network
            self.tun.config(ip="10.0.0.1", mask="255.255.255.0") # Example IP, adjust as needed
            self.log(f"TUN设备 'tun0' 已创建并配置IP: 10.0.0.1")

            # Start a thread to read data from the TUN device
            self.tun_read_thread = threading.Thread(target=self.read_tun_data, daemon=True)
            self.tun_read_thread.start()
            self.log("TUN设备读取线程已启动。")

        except Exception as e:
            self.log(f"初始化TUN设备时出错: {e}\n请确保您以管理员权限运行程序，并且在Windows上已安装OpenVPN的TAP驱动。")

    def read_tun_data(self):
        while True:
            try:
                # Read data from the TUN device
                # The size (e.g., 1500) should be sufficient for an MTU
                packet = self.tun.read(1500)
                if packet:
                    self.log(f"从TUN设备读取到数据包，大小: {len(packet)} 字节")
                    # Here, you would typically encapsulate the packet and send it
                    # through your existing UDP hole punching mechanism to the peer.
                    # For now, we just log it.
                    # self.send_tun_packet_to_peer(packet)
            except Exception as e:
                self.log(f"读取TUN设备数据时出错: {e}")
                break

    def connect_and_register(self):
        if self.is_registered:
            self.log("您已注册到服务器，无需重复注册。")
            return

        server_address_str = self.server_address_entry.get()
        client_id = self.client_id_entry.get()

        if not server_address_str or not client_id:
            self.log("请输入服务器地址和客户端ID。")
            return

        try:
            server_ip, server_port = server_address_str.split(':')
            server_port = int(server_port)
            self.server_address = (server_ip, server_port)
            self.client_id = client_id

            # Send registration message
            message = {"type": "register", "client_id": self.client_id}
            self.send_udp_message(self.server_address[0], self.server_address[1], json.dumps(message))
            self.log(f"已向中继服务器 {self.server_address[0]}:{self.server_address[1]} 注册客户端ID: {self.client_id}")
            self.server_status_label.config(text="服务器状态: 在线", fg="green") # Update status to online
            self.is_registered = True # Set registered flag to True
            self.connect_button.config(state=tk.DISABLED) # Disable the register button
        except ValueError:
            self.log("服务器地址格式不正确，请使用 IP:端口 格式。")
        except Exception as e:
            self.log(f"连接服务器时出错: {e}")
            self.server_status_label.config(text="服务器状态: 离线", fg="red") # Update status to offline

    def request_peer_info(self):
        if not self.server_address or not self.client_id:
            self.log("请先连接服务器并注册。")
            return

        peer_id_to_request = self.request_peer_id_entry.get()
        if not peer_id_to_request:
            self.log("请输入要请求的对等客户端ID。")
            return

        # Send request for peer info to the server
        request_message = json.dumps({"type": "request_peer", "client_id": self.client_id, "peer_id": peer_id_to_request})
        self.send_udp_message(self.server_address[0], self.server_address[1], request_message)
        self.log(f"已向服务器请求客户端ID '{peer_id_to_request}' 的对等客户端信息。")

    def attempt_hole_punching(self, peer_public_ip, peer_public_port):
        # This is a simplified attempt. In a real scenario, you'd send multiple packets
        # and potentially to both public and local addresses.
        self.log(f"尝试向 {peer_public_ip}:{peer_public_port} 打洞")
        punch_message = "UDP打洞尝试!"
        # Send a message to the peer's public address
        self.send_udp_message(peer_public_ip, peer_public_port, punch_message)
        self.log("已发送打洞数据包。")

    def start_game_forwarding(self):
        game_port_str = self.game_port_entry.get()
        if not game_port_str:
            self.log("请输入本地游戏UDP端口。")
            return

        if not self.peer_address:
            self.log("请先请求对等客户端信息并完成打洞。")
            return

        try:
            game_port = int(game_port_str)
            self.game_forwarding_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.game_forwarding_socket.bind((self.local_ip, game_port))
            self.log(f"游戏转发UDP socket已绑定到 {self.local_ip}:{game_port}")

            self.forwarding_running = True
            self.game_forwarding_thread = threading.Thread(target=self.forward_game_data, args=(game_port,))
            self.game_forwarding_thread.daemon = True
            self.game_forwarding_thread.start()
            self.log("游戏数据转发线程已启动。")

            self.start_forwarding_button.config(state=tk.DISABLED)
            self.stop_forwarding_button.config(state=tk.NORMAL)

        except ValueError:
            self.log("游戏端口格式无效。请输入一个数字。")
        except socket.error as e:
            self.log(f"绑定游戏转发UDP socket时出错: {e}")
        except Exception as e:
            self.log(f"启动游戏转发时发生意外错误: {e}")

    def forward_game_data(self, game_port):
        while self.forwarding_running:
            try:
                # Set a timeout to allow the thread to check self.forwarding_running periodically
                self.game_forwarding_socket.settimeout(0.1) # Set a small timeout
                data, addr = self.game_forwarding_socket.recvfrom(2048) # Larger buffer for game data
                # Only forward if the data is from the local game (not from the peer)
                # This is a simplification; a more robust solution might involve checking source IP/port
                # or having a dedicated port for incoming forwarded data.
                if addr[0] == self.local_ip and addr[1] == game_port: # Assuming game sends from this port
                    self.log(f"捕获到本地游戏数据 ({len(data)} 字节) from {addr[0]}:{addr[1]}")
                    # Forward to the peer's public address
                    self.game_forwarding_socket.sendto(data, self.peer_address)
                    self.log(f"已转发游戏数据到对等端 {self.peer_address[0]}:{self.peer_address[1]}")
                else:
                    # This is likely incoming forwarded data from the peer
                    self.log(f"收到对等端转发的游戏数据 ({len(data)} 字节) from {addr[0]}:{addr[1]}")
                    # Here you would typically inject this data back into the local game
                    # For now, we just log it.
                    pass

            except socket.timeout:
                # Timeout occurred, check if forwarding should stop
                continue
            except Exception as e:
                self.log(f"游戏数据转发时出错: {e}")
                self.forwarding_running = False
                break

    def stop_game_forwarding(self):
        self.forwarding_running = False
        if self.game_forwarding_socket:
            # Attempt to break the blocking recvfrom call by sending a dummy packet
            # or by setting a timeout on the socket before closing.
            # Setting a timeout is generally cleaner.
            try:
                self.game_forwarding_socket.shutdown(socket.SHUT_RDWR)
                self.game_forwarding_socket.close()
                self.log("游戏转发UDP socket已关闭。")
            except OSError as e:
                self.log(f"关闭游戏转发UDP socket时出错: {e}")
            finally:
                self.game_forwarding_socket = None # Ensure the socket reference is cleared

        if self.game_forwarding_thread and self.game_forwarding_thread.is_alive():
            # Give the thread a moment to finish, or use a more robust shutdown mechanism
            # For simplicity, we just log and rely on the loop condition.
            self.game_forwarding_thread.join(timeout=1) # Wait for the thread to finish
            if self.game_forwarding_thread.is_alive():
                self.log("警告: 游戏数据转发线程未能及时停止。")

        self.log("游戏数据转发已停止。")
        self.start_forwarding_button.config(state=tk.NORMAL)
        self.stop_forwarding_button.config(state=tk.DISABLED)


    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.target_ip_entry.insert(0, config.get("target_ip", ""))
                    self.server_address_entry.insert(0, config.get("server_address", ""))
                    self.client_id_entry.insert(0, config.get("client_id", ""))
                    self.request_peer_id_entry.insert(0, config.get("request_peer_id", ""))
                    self.game_port_entry.insert(0, config.get("game_port", ""))
                self.log("配置已加载。")
            except Exception as e:
                self.log(f"加载配置时出错: {e}")

    def save_config(self):
        config = {
            "target_ip": self.target_ip_entry.get(),
            "server_address": self.server_address_entry.get(),
            "client_id": self.client_id_entry.get(),
            "request_peer_id": self.request_peer_id_entry.get(),
            "game_port": self.game_port_entry.get()
        }
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            self.log("配置已保存。")
        except Exception as e:
            self.log(f"保存配置时出错: {e}")

    def check_server_status(self):
        if self.server_address:
            try:
                # Attempt to connect to the server to check its status
                # Use a small timeout to avoid blocking
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                temp_socket.settimeout(1) # 1 second timeout
                # Send a dummy message or a specific status request
                temp_socket.sendto(b"status_check", self.server_address)
                # Try to receive a response (optional, but good for confirmation)
                temp_socket.recvfrom(1024) # Expect a response, but don't care about content
                self.server_status_label.config(text="服务器状态: 在线", fg="green")
            except (socket.timeout, ConnectionRefusedError, OSError):
                self.server_status_label.config(text="服务器状态: 离线", fg="red")
            except Exception as e:
                self.server_status_label.config(text="服务器状态: 错误", fg="orange")
                self.log(f"检查服务器状态时发生错误: {e}")
            finally:
                temp_socket.close()
        else:
            self.server_status_label.config(text="服务器状态: 未配置", fg="gray")
        
        # Schedule the next check after 5 seconds
        self.master.after(5000, self.check_server_status)

    def on_closing(self):
        self.log("正在关闭程序...")
        # Stop the periodic server status check
        self.master.after_cancel(self.check_server_status) # This might not work directly if not stored as an ID
        # A more robust way to stop is to use a flag and check it in check_server_status
        
        self.save_config()
        # Clean up sockets and threads before closing
        if self.udp_socket:
            self.udp_socket.close()
        self.stop_game_forwarding() # Ensure game forwarding is stopped
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = GameLanToolGUI(root)
    root.mainloop()