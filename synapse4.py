import json
import threading
import time

import pystray
from PIL import Image
from pystray import MenuItem as item

config = {
    "4": r"C:\Users\Burak\AppData\Local\Razer\RazerAppEngine\User Data\Logs\systray_systrayv2.log",
    "interval": "5s",
}

razer_version = "4"
isStop = False
menu_items = []  # Menü öğelerini burada tanımlayalım
deviceName = ""  # Boş bir dize olarak başlatıyoruz
chargingStatus = None
level = ""  # Boş bir dize olarak başlatıyoruz
hasBattery = None

def find_last_line_with_keyword(file_name, keyword):
    last_line = None
    try:
        with open(file_name, 'r') as file:
            for line in file:
                if keyword in line:
                    last_line = line
    except FileNotFoundError:
        return False, f"File {file_name} not found."
    except Exception as e:
        return False, f"An error occurred: {str(e)}"
    return last_line

def main():
    global menu_items
    global deviceName
    global chargingStatus
    global level
    global hasBattery
    global isStop

    file_name = config[razer_version]
    keyword = "connectingDeviceData"

    last_line_with_keyword, err= find_last_line_with_keyword(file_name, keyword)
    
    if not last_line_with_keyword:
        return err
        

    if last_line_with_keyword:
        last_line_with_keyword = json.loads(last_line_with_keyword.split("~")[-1].split("connectingDeviceData:")[1])
        deviceName = last_line_with_keyword[0]["name"]["en"]
        if last_line_with_keyword[0]["powerStatus"]:
            chargingStatus = last_line_with_keyword[0]["powerStatus"]["chargingStatus"]
            level = last_line_with_keyword[0]["powerStatus"]["level"]
        print(f"Device Name: {deviceName}", f"Charging Status: {chargingStatus}", f"Level: {level}", f"Has Battery: {hasBattery}", sep="\n")
    else:
        print("connectingDeviceData içeren bir satır bulunamadı.")

    # Şarj durumu ve seviyesi doğru şekilde alındıysa menü öğelerini oluştur
    menu_items = []
    if chargingStatus is not None:
        status = "Şarj Ediliyor" if chargingStatus == "Charging" else "Şarj Edilmiyor"
        menu_items.append(item(f"Şarj Durumu: {status}", lambda: None))  # Boş bir işlev belirtildi
    if level:
        menu_items.append(item(f"Şarj Seviyesi: {level}%", lambda: None))  # Boş bir işlev belirtildi

def update_icon():
    global icon
    global isStop

    while not isStop:
        err = main()  # Ana işlevi çağır
        if err:
            print(err, "Program sonlandırılıyor.")
            icon.stop()  # Sistem tepsisi simgesini kaldır

        print("İkon güncellendi:", deviceName, level)
        menu = tuple(menu_items + [item("Çıkış", exit_program)])  # Güncel menü öğelerini kullan
        icon.menu = menu  # Menüyü güncelle
        icon.title = deviceName + f" ({level}% - {"Şarj Ediliyor" if chargingStatus == "Charging" else "Şarj Edilmiyor"})"
        sleepTime = int(config["interval"][:-1])
        time.sleep(sleepTime)  # 5 saniye beklet

# Sistem tepsisi simgesini kapatma işlevi
def exit_program(icon):
    global isStop
    isStop = True
    icon.stop()  # Sistem tepsisi simgesini kaldır

if __name__ == "__main__":
    # Tray Icon'u oluştur
    image = Image.open("icon.png")
    menu = tuple(menu_items + [item("Çıkış", exit_program)])
    icon = pystray.Icon("Razer", image, deviceName + f" ({level}%)", menu)

    # Tray Icon'u göstermek için bir iş parçacığı oluştur
    tray_thread = threading.Thread(target=icon.run)
    tray_thread.start()

    # Belirli aralıklarla ana programı çalıştır
    update_icon()  # Ana programı çalıştır
