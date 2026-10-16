import json
import logging
import re
import threading
import time

import paho.mqtt.client as mqtt
import pyautogui

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("receiver")

# ==================== KONFIGURASI MQTT ====================
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "inka/rfid_scan_k+y8OcXqUXalaoynSJlAXReRicthOTH5OI+sxdbieuE="
MQTT_USER = None
MQTT_PASS = None
CLIENT_ID = "kios-windows-01-sub"   # dibedakan dengan sender
MAX_AGE_DETIK = 15                  # mengabaikan pesan setelah 15 detik
DEBOUNCE_DETIK = 2                  # mengabaikan UID sama yang datang beruntun
# ==========================================================

UID_RE = re.compile(r"\d{10}")
pyautogui.PAUSE = 0

_lock = threading.Lock()
_last_uid = None
_last_time = 0.0


def on_connect(client, userdata, flags, rc, *args):
    log.info("Terhubung ke broker: %s", rc)
    client.subscribe(MQTT_TOPIC, qos=1)
    log.info("Standby memantau topik: %s", MQTT_TOPIC)


def on_disconnect(client, userdata, *args):
    log.warning("Terputus dari broker, mencoba reconnect...")


def on_message(client, userdata, msg):
    global _last_uid, _last_time
    try:
        if msg.retain:
            log.warning("Pesan retained diabaikan")
            return

        data = json.loads(msg.payload.decode("utf-8"))
        uid = str(data["uid"])
        ts = data.get("ts")

        if not UID_RE.fullmatch(uid):
            log.warning("Payload tidak valid ditolak: %r", uid[:30])
            return

        if ts is not None and abs(time.time() - ts) > MAX_AGE_DETIK:
            log.warning("Pesan kedaluwarsa diabaikan (UID %s)", uid)
            return

        with _lock:
            now = time.monotonic()
            if uid == _last_uid and now - _last_time < DEBOUNCE_DETIK:
                return
            _last_uid, _last_time = uid, now

            log.info("[DATA MASUK] UID: %s", uid)
            pyautogui.write(uid, interval=0.05)
            pyautogui.press("enter")
            log.info("[SUKSES] UID diketikkan ke layar kios")
    except Exception:
        log.exception("Gagal memproses pesan")


def buat_client():
    try:
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    except AttributeError:
        c = mqtt.Client(client_id=CLIENT_ID)
    if MQTT_USER:
        c.username_pw_set(MQTT_USER, MQTT_PASS)
    c.on_connect = on_connect
    c.on_disconnect = on_disconnect
    c.on_message = on_message
    c.reconnect_delay_set(min_delay=1, max_delay=30)
    return c


client = buat_client()
try:
    client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=30)
    client.loop_forever(retry_first_connection=True)
except KeyboardInterrupt:
    log.info("Program dihentikan oleh pengguna.")
finally:
    client.disconnect()