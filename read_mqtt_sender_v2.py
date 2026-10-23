#!/usr/bin/env python3
import json
import logging
import time

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sender")

# ==================== KONFIGURASI MQTT ====================
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "inka/rfid_scan"
MQTT_USER = None   # hanya untuk broker privat
MQTT_PASS = None
DEVICE_ID = "rpi-kios01"
# ==========================================================

# Kartu khusus hasil konversi
OVERRIDE = {
    769177167877: "0680007347", 
    249563743628: "2233998138",
    594774230330: "2236513162",
}

reader = SimpleMFRC522()


def konversi_ke_sistem_inka(id_sensor):
    """Konversi UID angka awal langsung ke angka akhir kiosk via Little Endian.
    Mengembalikan None jika gagal.
    """
    if id_sensor in OVERRIDE:
        return OVERRIDE[id_sensor]
    try:
        # 1. Geser ke kanan 8 bit untuk membuang 1 byte terakhir
        four_bytes_int = id_sensor >> 8
        
        # 2. Ubah ke bentuk byte dengan urutan normal (Big Endian, panjang 4 byte)
        byte_data = four_bytes_int.to_bytes(4, byteorder='big')
        
        # 3. Baca kembali data byte dengan urutan terbalik (Little Endian) menjadi integer
        angka_akhir = int.from_bytes(byte_data, byteorder='little')
        
        # 4. Kembalikan dalam bentuk string berformat 10 digit desimal
        return f"{angka_akhir:010d}"
    except Exception as e:
        log.error("Konversi gagal untuk %s: %s", id_sensor, e)
        return None


def buat_client():
    try:
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{DEVICE_ID}-pub")
    except AttributeError:
        c = mqtt.Client(client_id=f"{DEVICE_ID}-pub")

    if MQTT_USER:
        c.username_pw_set(MQTT_USER, MQTT_PASS)

    def on_connect(client, userdata, flags, rc, *args):
        log.info("Terhubung ke broker: %s", rc)

    def on_disconnect(client, userdata, *args):
        log.warning("Terputus dari broker, paho akan mencoba reconnect otomatis")

    c.on_connect = on_connect
    c.on_disconnect = on_disconnect
    c.reconnect_delay_set(min_delay=1, max_delay=30)
    return c


client = buat_client()
client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=30)
client.loop_start()

try:
    log.info("=== PROGRAM RFID STANDBY MQTT PT INKA ===")
    while True:
        log.info("Menunggu kartu di-tap...")
        id_kartu, _ = reader.read()
        id_inka = konversi_ke_sistem_inka(id_kartu)
        if not id_inka:
            continue

        payload = json.dumps({"uid": id_inka, "device": DEVICE_ID, "ts": int(time.time())})
        info = client.publish(MQTT_TOPIC, payload, qos=1, retain=False)
        try:
            info.wait_for_publish(timeout=5)
        except Exception:
            pass

        if info.is_published():
            log.info("[SUKSES] UID %s terkirim", id_inka)
        else:
            log.error("[GAGAL] UID %s belum terkirim (koneksi bermasalah?)", id_inka)

        time.sleep(2)
except KeyboardInterrupt:
    log.info("Program dihentikan.")
finally:
    client.loop_stop()
    client.disconnect()
    GPIO.cleanup()