#!/usr/bin/env python3
"""
OpenTrack UDP数据发送器 - Python服务器
通过WebSocket接收网页数据，以固定频率广播UDP数据到OpenTrack
"""

import socket
import struct
import threading
import time
import yaml
from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'opentrack-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局数据存储
current_data = {
    'x': 1e-5,
    'y': 1e-5,
    'z': 1e-5,
    'yaw': 1e-5,
    'pitch': 1e-5,
    'roll': 1e-5
}

# 数据锁
data_lock = threading.Lock()

# UDP socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_target = (config['udp']['host'], config['udp']['port'])

# 广播线程控制
broadcast_running = True

@app.route('/')
def index():
    """提供主页面"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """提供静态文件"""
    return send_from_directory('.', path)

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    logger.info(f"客户端连接: {request.sid}")
    # 发送当前数据给新连接的客户端
    with data_lock:
        emit('data_update', current_data)

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    logger.info(f"客户端断开: {request.sid}")

@socketio.on('data_update')
def handle_data_update(data):
    """接收网页发来的数据更新"""
    global current_data
    try:
        # 验证数据
        required_keys = ['x', 'y', 'z', 'yaw', 'pitch', 'roll']
        if not all(key in data for key in required_keys):
            logger.error(f"数据格式错误: {data}")
            return

        # 更新数据
        with data_lock:
            for key in required_keys:
                current_data[key] = float(data[key])

        logger.debug(f"数据更新: {current_data}")

    except (ValueError, TypeError) as e:
        logger.error(f"数据解析错误: {e}, 数据: {data}")

def broadcast_thread():
    """UDP广播线程"""
    global broadcast_running, current_data

    broadcast_interval = 1.0 / config['udp']['broadcast_frequency']

    while broadcast_running:
        try:
            # 获取当前数据
            with data_lock:
                data_to_send = current_data.copy()

            # 打包数据（小端序64位浮点数）
            data_bytes = struct.pack('<6d',
                                   data_to_send['x'],
                                   data_to_send['y'],
                                   data_to_send['z'],
                                   data_to_send['yaw'],
                                   data_to_send['pitch'],
                                   data_to_send['roll'])

            # 发送UDP数据
            udp_socket.sendto(data_bytes, udp_target)

            # 可选：记录发送的数据
            # logger.debug(f"UDP广播: {data_to_send}")

        except Exception as e:
            logger.error(f"UDP广播错误: {e}")

        # 等待下一个广播周期
        time.sleep(broadcast_interval)

def start_broadcast():
    """启动广播线程"""
    global broadcast_thread_instance
    broadcast_thread_instance = threading.Thread(target=broadcast_thread, daemon=True)
    broadcast_thread_instance.start()
    logger.info(f"UDP广播线程已启动，频率: {config['udp']['broadcast_frequency']}Hz")

def stop_broadcast():
    """停止广播线程"""
    global broadcast_running
    broadcast_running = False
    if broadcast_thread_instance:
        broadcast_thread_instance.join(timeout=2)
    udp_socket.close()
    logger.info("UDP广播线程已停止")

if __name__ == '__main__':
    try:
        # 启动广播线程
        start_broadcast()

        # 启动Flask服务器
        logger.info(f"启动Web服务器: http://{config['web']['host']}:{config['web']['port']}")
        logger.info(f"在其他设备上使用: http://此台电脑IP地址:24242 进行远程控制")
        socketio.run(app,
                    host=config['web']['host'],
                    port=config['web']['port'],
                    debug=config['web']['debug'])

    except KeyboardInterrupt:
        logger.error("收到中断信号，正在关闭...")
    except Exception as e:
        logger.error(f"服务器错误: {e}")
    finally:
        stop_broadcast()