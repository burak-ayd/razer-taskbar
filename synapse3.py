import json
import os
import re
import signal
import threading
import time

import pystray
from PIL import Image
from pystray import MenuItem as item

config = {
    "3": r"C:\Users\Burak\AppData\Local\Razer\Synapse3\Log\Razer Synapse 3.log",
    "interval": "5s",
}

razer_version = "3"
isStop = False
menu_items = []  # Menü öğelerini burada tanımlayalım
deviceName = ""  # Boş bir dize olarak başlatıyoruz
chargingState= None
batteryPercentage = ""  # Boş bir dize olarak başlatıyoruz

def signal_close(signum, frame):
    global isStop
    isStop = True
    
signal.signal(signal.SIGINT, signal_close)

def find_last_line_with_keyword(file_name, batteryStatePattern, batteryIsChargingPattern):
    lastBatteryPercentage = lastChargingState = lastDeviceName = log_content = None
    pattern = re.compile(batteryStatePattern, re.MULTILINE)
    batteryStatusPattern = re.compile(batteryIsChargingPattern, re.MULTILINE)
    try:
        with open(file_name, 'r') as file:
            log_content = file.read()
            last_match = list(pattern.finditer(log_content))[-1]
            batteryStatusMatch = list(batteryStatusPattern.finditer(log_content))[-1]
            if last_match:
                lastDeviceName = last_match.group('name')
                lastBatteryPercentage = last_match.group('level')
            else:
                print("No match found. State")
            if batteryStatusMatch:
                lastChargingState = batteryStatusMatch.group('isCharging')
            else:
                print("No match found. Status")

    except FileNotFoundError:
        return False, False, False, f"File {file_name} not found."
    except Exception as e:
        return False, False, False, f"An error occurred: {str(e)}"
    return lastBatteryPercentage, lastChargingState, lastDeviceName, None

def main():
    global menu_items
    global deviceName
    global chargingState
    global batteryPercentage
    global hasBattery
    global isStop

    file_name = config[razer_version]
    
    batteryStatePatern = r"^(?P<dateTime>.+?) INFO.+?_OnBatteryLevelChanged[\s\S]*?Name: (?P<name>.*)[\s\S]*?Handle: (?P<handle>\d+)[\s\S]*?level (?P<level>\d+)"
    batteryIsChargingPattern = r"^(?P<dateTime>.+?) INFO.+?_OnDevicePowerStateChanged[\s\S]*?: (?P<name>.*) (?P<isCharging>.*)"
    batteryPercentage, chargingState, deviceName, err= find_last_line_with_keyword(file_name, batteryStatePatern, batteryIsChargingPattern)
    
    if not batteryPercentage and chargingState and deviceName:
        return err
        
    # print("Son şarj yüzdesi:", batteryPercentage)
    # print("Son şarj durumu:", chargingState)
    # print("Son cihaz adı:", deviceName)

    if batteryPercentage and chargingState and deviceName:
        print(f"Device Name: {deviceName}", f"Charging Status: {chargingState}", f"Level: {batteryPercentage}", sep="\n")


    # Şarj durumu ve seviyesi doğru şekilde alındıysa menü öğelerini oluştur
    menu_items = []
    if chargingState is not None:
        status = "Şarj Ediliyor" if chargingState == "True" else "Şarj Edilmiyor"
        menu_items.append(item(f"Şarj Durumu: {status}", lambda: None))  # Boş bir işlev belirtildi
    if batteryPercentage:
        menu_items.append(item(f"Şarj Seviyesi: {batteryPercentage}%", lambda: None))  # Boş bir işlev belirtildi

def update_icon():
    global icon
    global isStop

    while not isStop:
        err = main()  # Ana işlevi çağır
        if err:
            print(err, "Program sonlandırılıyor.")
            icon.stop()  # Sistem tepsisi simgesini kaldır
        

        print("İkon güncellendi:", deviceName, batteryPercentage)
        menu = tuple(menu_items + [item("Çıkış", exit_program)])  # Güncel menü öğelerini kullan
        icon.menu = menu  # Menüyü güncelle
        icon.title = str(deviceName) + f" ({batteryPercentage}% - {"Şarj Ediliyor" if chargingState == "True" else "Şarj Edilmiyor"})"
        sleepTime = int(config["interval"][:-1])
        time.sleep(sleepTime)  # 5 saniye beklet
    print("Program sonlandırıldı.")
    icon.stop()  # Sistem tepsisi simgesini kaldır

# Sistem tepsisi simgesini kapatma işlevi
def exit_program(icon):
    global isStop
    isStop = True
    icon.stop()  # Sistem tepsisi simgesini kaldır

if __name__ == "__main__":
    # Tray Icon'u oluştur
    image = Image.open(os.path.dirname(os.path.realpath(__file__))+"/icon.png")
    menu = tuple(menu_items + [item("Çıkış", exit_program)])
    icon = pystray.Icon("Razer", image, deviceName + f" ({batteryPercentage}%)", menu)

    # Tray Icon'u göstermek için bir iş parçacığı oluştur
    tray_thread = threading.Thread(target=icon.run)
    tray_thread.start()

    # Belirli aralıklarla ana programı çalıştır
    update_icon()  # Ana programı çalıştır
