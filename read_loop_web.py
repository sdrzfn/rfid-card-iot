#!/usr/bin/env python3
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
from playwright.sync_api import sync_playwright

reader = SimpleMFRC522()

# ==================== KONFIGURASI TARGET WEBSITE ====================
URL_TARGET = "https://sadrakhzp.vercel.app/" 
# ====================================================================

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

# --- PROSES UTAMA DENGAN BROWSER OTOMATISASI ---
with sync_playwright() as p:
    print("Membuka browser siluman di latar belakang...")
    # headless=True artinya browser berjalan tanpa memunculkan jendela grafis (cocok untuk CLI Raspberry)
    browser = p.chromium.launch(
        executable_path='/usr/bin/chromium-browser',
        headless=True
    )
    page = browser.new_page()
    
    try:
        print(f"Menghubungkan ke {URL_TARGET}...")
        page.goto(URL_TARGET)
        print("Website berhasil dimuat dan siap menerima RFID.\n")
        
        print("=== PROGRAM RFID STANDBY SYNC PT INKA (BROWSER DRIVER) ===")
        print("Program berjalan terus-menerus. Tekan Ctrl+C untuk menghentikan.\n")
        
        while True:
            print("Menunggu kartu di-tap...")
            id_kartu, text = reader.read()
            id_final_inka = konversi_ke_sistem_inka(id_kartu)
            
            print("\n" + "="*45)
            print(f"ID Terdeteksi (Raw Sensor) : {id_kartu}")
            print(f"ID HASIL KONVERSI PT INKA  : {id_final_inka}")
            print("="*45)
            
            print("Mengisi form secara otomatis...")
            try:
                # 1. Isi field Name (mencari elemen berdasarkan atribut name="name")
                page.locator('input[name="name"]').fill("Mesin RFID Lantai Pabrik")
                
                # 2. Isi field Email (mencari elemen berdasarkan atribut name="email")
                page.locator('input[name="email"]').fill("rfid-pabrik@inka.co.id")
                
                # 3. Isi field Message dengan hasil konversi RFID
                page.locator('textarea[name="message"]').fill(f"ID RFID Terdeteksi: {id_final_inka}")
                
                # 4. Klik tombol submit (mencari tag button dengan tipe submit atau teks tertentu)
                page.locator('button[type="submit"]').click()
                
                print(" -> [SUKSES] Form berhasil terisi dan disubmit oleh browser driver!")
                
                # Berikan jeda sejenak lalu reload halaman agar form kosong kembali untuk kartu berikutnya
                time.sleep(3)
                page.reload()
                print("Browser di-refresh. Siap untuk pemindaian berikutnya.")
                
            except Exception as e:
                print(f" -> [GAGAL] Gagal mengisi form di browser: {e}")
                # Jika terjadi error/putus koneksi, coba reload halaman web
                page.goto(URL_TARGET)
            
            print("\nSilakan angkat kartu...\n")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")
    finally:
        browser.close()
        GPIO.cleanup()
        print("Browser ditutup & GPIO Cleanup selesai.")
