import paho.mqtt.client as mqtt
import pyautogui # Library untuk mengetik otomatis di Windows
import time

# ==================== KONFIGURASI MQTT ====================
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "rfid_scan" # Harus sama dengan topik Raspberry Pi
# ==========================================================

def on_connect(client, userdata, flags, rc):
    print(f"Terhubung ke MQTT Broker dengan kode respon: {rc}")
    # Melakukan subscribe ke topik rfid
    client.subscribe(MQTT_TOPIC)
    print(f"Standby memantau data di topik: {MQTT_TOPIC}...")

def on_message(client, userdata, msg):
    # Menerima data UID dari broker
    id_inka = msg.payload.decode()
    print(f"\n[DATA MASUK] Menerima UID RFID: {id_inka}")
    
    print("Simulasi mengetik ke form web...")
    # 1. Ketikkan teks hasil konversi ke posisi kursor yang sedang aktif
    pyautogui.write(id_inka, interval=0.05) 
    
    # 2. Opsional: Otomatis tekan Enter setelah mengetik
    pyautogui.press('enter')
    print(" -> [SUKSES] ID berhasil diketikkan ke layar kios!")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    # Loop terus-menerus untuk mendengarkan data masuk di background
    client.loop_forever()
except KeyboardInterrupt:
    print("\nProgram dihentikan oleh pengguna.")
except Exception as e:
    print(f"Error: {e}")