#!/usr/bin/env python3
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
from playwright.sync_api import sync_playwright

reader = SimpleMFRC522()
IP_PCINKA = "192.168.17.225"
PORT_CDP = "9222"

# ==================== KONFIGURASI TARGET WEBSITE ====================
# URL_TARGET = "https://nama-website.com/" 
# ====================================================================

def konversi_ke_sistem_inka(id_sensor):
    """Fungsi khusus konversi ID menjadi format desimal PT INKA"""
    if id_sensor == 769177167877:
        return "0680007347"
    elif id_sensor == 249563743628:
        return "2233998138"
    elif id_sensor == 594774230330:
        return "2236513162"
        
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
    cdp_url = f"http://{IP_PCINKA}:{PORT_CDP}"
    # print("Membuka browser siluman di latar belakang...")
    print (f"Menghubungkan ke PC: {cdp_url}")
    # headless=True artinya browser berjalan tanpa memunculkan jendela grafis (cocok untuk CLI Raspberry)
    
    # INI BUAT CHROMIUM DI RASPBERRY
    # browser = p.chromium.launch(
    #     executable_path='/usr/bin/chromium-browser',
    #     headless=True
    # )
    # page = browser.new_page()
    
    try:
        # ---- INI BUAT KE CDP PC INKA ----
        browser = p.chromium.connect_over_cdp(cdp_url)
                
        # Mengakses context dan mengambil tab/halaman pertama yang terbuka di Kios
        default_context = browser.contexts[0]
        page = default_context.pages[0]
        
        print(" -> [SUKSES] Berhasil terhubung dan mengendalikan browser PC Kios!\n")
        
        print("=== PROGRAM RFID STANDBY SYNC PT INKA (CDP BYPASS) ===")
        print("Program berjalan terus-menerus. Tekan Ctrl+C untuk menghentikan.\n")
        
        # ---- UNCOMMENT INI JIKA BUTUH MENJALANKAN DARI RASPBERRY ----
        # print(f"Menghubungkan ke {URL_TARGET}...")
        # page.goto(URL_TARGET)
        # print("Website berhasil dimuat dan siap menerima RFID.\n")
        
        # print("=== PROGRAM RFID STANDBY SYNC PT INKA (BROWSER DRIVER) ===")
        # print("Program berjalan terus-menerus. Tekan Ctrl+C untuk menghentikan.\n")
        
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
                page.locator('input[name="name"]').fill("Mesin RFID Lantai Pabrik")
                
                page.locator('input[name="email"]').fill("rfid-pabrik@inka.co.id")
                
                page.locator('textarea[name="message"]').fill(f"ID RFID Terdeteksi: {id_final_inka}")
                
                # UNCOMMENT INI JIKA INGIN AUTO SUBMIT
                # page.locator('button[type="submit"]').click()
                
                print(" -> [SUKSES] Isian form berhasil terisi oleh browser driver!")
                
                # Berikan jeda sejenak lalu reload halaman agar form kosong kembali untuk kartu berikutnya
                time.sleep(3)
                page.reload()
                print("Browser di-refresh. Siap untuk pemindaian berikutnya.")
                
            except Exception as e:
                print(f" -> [GAGAL] Gagal mengisi form di browser: {e}")
                # Jika terjadi error/putus koneksi, coba reload halaman web
                # page.goto(URL_TARGET)
            
            print("\nSilakan angkat kartu...\n")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")
    finally:
        # browser.close()
        GPIO.cleanup()
        print("Browser ditutup & GPIO Cleanup selesai.")