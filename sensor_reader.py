import serial
import serial.tools.list_ports
import json
import time
import os
import re
from datetime import datetime

# === 기본 설정 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(BASE_DIR, "sensor_logs")
os.makedirs(output_dir, exist_ok=True)

error_log_path = os.path.join(output_dir, "parse_errors.log")

valid_devices = {"adlab01", "adlab02", "adlab03", "adlab04", "adlab05"}
sensor_data_map = {}

# === COM 포트 자동 탐지 ===
def find_serial_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if 'usbserial' in port.device.lower() or 'usb' in port.description.lower():
            return port.device
    if ports:
        print("자동 탐지 실패. 사용 가능한 포트 목록:")
        for i, port in enumerate(ports):
            print(f"[{i}] {port.device} - {port.description}")
        choice = input("번호를 선택하세요: ")
        try:
            return ports[int(choice)].device
        except:
            return None
    return None

port = find_serial_port()
if not port:
    print("❌ 시리얼 포트를 찾을 수 없습니다.")
    exit(1)

try:
    ser = serial.Serial(port, 9600, timeout=1)
    print(f"✅ 시리얼 포트 연결됨: {port}")
except Exception as port_err:
    print("❌ 포트 열기 실패:", port_err)
    exit(1)

print("✅ JSON 수신 시작")

while True:
    try:
        line = ser.readline().decode(errors='ignore').strip()
        if line:
            print(f"📡 수신 데이터: {line}")

            parts = line.split("|")
            if len(parts) == 3:
                timestamp_now = datetime.now()
                formatted_timestamp = timestamp_now.strftime("%Y-%m-%d %H:%M:%S")
                date_str = timestamp_now.strftime("%Y-%m-%d")

                device = parts[1].strip()
                if device not in valid_devices:
                    print(f"⚠️ 알 수 없는 센서 ID: {device} → 무시됨")
                    continue

                sensor_data_raw = parts[2]

                try:
                    temp = float(sensor_data_raw.split("Temp: ")[1].split("°C")[0])
                    hum = float(sensor_data_raw.split("Hum: ")[1].split("%")[0])
                    lux_match = re.search(r"Lux: ([\d.]+)lx \((\w+)\)", sensor_data_raw)
                    lux = float(lux_match.group(1))
                    direction = lux_match.group(2)
                    pH = float(sensor_data_raw.split("pH: ")[1].split("pH")[0])
                except Exception as parse_err:
                    print("🚨 파싱 오류:", parse_err)
                    with open(error_log_path, "a", encoding="utf-8") as log:
                        log.write(f"[{formatted_timestamp}] {line}\n")
                    continue

                entry = {
                    "timestamp": formatted_timestamp,
                    "device": device,
                    "temperature": temp,
                    "humidity": hum,
                    "lux": lux,
                    "direction": direction,
                    "pH": pH
                }

                if device not in sensor_data_map:
                    sensor_data_map[device] = []

                sensor_data_map[device].append(entry)

                json_filename = os.path.join(output_dir, f"{device}_{date_str}.json")
                with open(json_filename, "w", encoding="utf-8") as f:
                    json.dump(sensor_data_map[device], f, ensure_ascii=False, indent=2)

    except Exception as e:
        print("🚨 오류:", e)

    time.sleep(1)
