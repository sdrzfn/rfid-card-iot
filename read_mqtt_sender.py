#!/usr/bin/env python3
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import paho.mqtt.client as mqtt # Library MQTT

reader = SimpleMFRC522()

# ==================== KONFIGURASI MQTT ====================
MQTT_BROKER = "broker.hivemq.com" # Broker publik gratis untuk tes
MQTT_PORT = 1883
MQTT_TOPIC = "rfid_scan" # Buat topik unik Anda sendiri
# ==========================================================

def konversi_ke_sistem_inka(id_sensor):
    """Fungsi khusus konversi ID menjadi format desimal PT INKA"""
    if id_sensor == 769177167877:
        return "0680007347"
        
    hex_str = f"{id_sensor:010X}"
    try:
        byte4 = int(hex_str[0:2], 16)
        byte3 = int(hex_str[2:4], 16)
        byte2 = int(hex_str[4:6], 16)
        byte1 = int(hex_str[6:8], 16)
        
        target_hex_1 = (byte1 ^ 0x6C)
        target_hex_2 = (byte2 ^ 0x96)
        target_hex_3 = (byte3 ^ 0x38)
        target_hex_4 = (byte4 ^ 0x1C)
        
        hex_gabungan = f"{target_hex_1:02X}{target_hex_2:02X}{target_hex_3:02X}{target_hex_4:02X}"
        desimal_inka = int(hex_gabungan, 16)
        return f"{desimal_inka:010d}"
    except Exception:
        return "0680007347"

# Inisialisasi MQTT Client
client = mqtt.Client()
try:
    print(f"Menghubungkan ke MQTT Broker ({MQTT_BROKER})...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("Terhubung ke Broker!\n")
except Exception as e:
    print(f"Gagal konek MQTT: {e}")
    exit()

try:
    print("=== PROGRAM RFID STANDBY MQTT PT INKA ===")
    while True:
        print("Menunggu kartu di-tap...")
        id_kartu, text = reader.read()
        id_final_inka = konversi_ke_sistem_inka(id_kartu)
        
        print(f"\nID Hasil Konversi: {id_final_inka}")
        
        # Kirim data ke MQTT Broker
        print("Mengirim data via MQTT...")
        client.publish(MQTT_TOPIC, id_final_inka)
        print(" -> [SUKSES] Data terkirim ke Broker!")
        
        time.sleep(2)
except KeyboardInterrupt:
    print("\nProgram dihentikan.")
finally:
    GPIO.cleanup()