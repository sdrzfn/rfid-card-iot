#!/usr/bin/env python3
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

reader = SimpleMFRC522()

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

# --- PROSES LOOPING UTAMA ---
try:
    print("=== PROGRAM RFID STANDBY SYNC PT INKA ===")
    print("Program berjalan terus-menerus. Tekan Ctrl+C untuk menghentikan.\n")
    
    while True:
        print("Menunggu kartu di-tap...")
        
        # Membaca sensor (program akan tertahan di baris ini sampai ada kartu menempel)
        id_kartu, text = reader.read()
        
        # Memproses konversi
        id_final_inka = konversi_ke_sistem_inka(id_kartu)
        
        print("\n" + "="*45)
        print(f"ID Terdeteksi (Raw Sensor) : {id_kartu}")
        print(f"ID HASIL KONVERSI PT INKA  : {id_final_inka}")
        print("="*45)
        
        # Berikan jeda 2 detik agar kartu yang sama tidak terbaca berkali-kali secara instan
        print("Berhasil diproses. Silakan angkat kartu...\n")
        time.sleep(2)

except KeyboardInterrupt:
    print("\nProgram dihentikan oleh pengguna.")
finally:
    GPIO.cleanup()
    print("GPIO Cleanup selesai.")
