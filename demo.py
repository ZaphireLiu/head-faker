import socket
import struct

# OpenTracker配置
UDP_IP = "127.0.0.1"
UDP_PORT = 4242

# 创建UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 初始值
x, y, z = 0.0, 0.0, 0.0
yaw, pitch, roll = 0.0, 0.0, 0.0

print("OpenTracker数据发送器")
print("格式: X,Y,Z,Yaw,Pitch,Roll")
print("跳过某个值请留空，例如: 1,2,3,,5,6")
print("输入 'q' 退出\n")

while True:
    try:
        user_input = input("输入数据: ").strip()
        
        if user_input.lower() == 'q':
            break
        
        # 解析输入
        values = user_input.split(',')
        
        if len(values) != 6:
            print("错误: 需要6个值（用逗号分隔）")
            continue
        
        # 更新非空值
        if values[0].strip():
            x = float(values[0])
        if values[1].strip():
            y = float(values[1])
        if values[2].strip():
            z = float(values[2])
        if values[3].strip():
            yaw = float(values[3])
        if values[4].strip():
            pitch = float(values[4])
        if values[5].strip():
            roll = float(values[5])
        
        # OpenTracker格式: 小端序64位浮点数，顺序为 X,Y,Z,Yaw,Pitch,Roll
        data = struct.pack('<6d', x, y, z, yaw, pitch, roll)
        # print(data)
        
        # 发送UDP数据
        sock.sendto(data, (UDP_IP, UDP_PORT))
        
        print(f"已发送: X={x:.2f}, Y={y:.2f}, Z={z:.2f}, Yaw={yaw:.2f}, Pitch={pitch:.2f}, Roll={roll:.2f}")
        
    except ValueError:
        print("错误: 请输入有效的数字")
    except KeyboardInterrupt:
        print("\n程序中断")
        break
    except Exception as e:
        print(f"错误: {e}")

sock.close()
print("已关闭连接")
