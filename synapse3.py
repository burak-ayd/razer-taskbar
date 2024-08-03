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
batteryPercentage = 0  # Boş bir dize olarak başlatıyoruz
assetsFolder = os.path.join(os.path.dirname(__file__), "assets")
isDeviceRemoved = False

def signal_close(signum, frame):
    global isStop
    isStop = True
    
signal.signal(signal.SIGINT, signal_close)

def find_last_line_with_keyword(file_name, batteryStatePattern, batteryIsChargingPattern, deviceLoadedPattern, deviceRemovedPattern):
    lastBatteryPercentage = lastChargingState = lastDeviceName = log_content =  None
    deviceRemoved = False
    pattern = re.compile(batteryStatePattern, re.MULTILINE)
    batteryStatusPattern = re.compile(batteryIsChargingPattern, re.MULTILINE)
    deviceLoadedPattern = re.compile(deviceLoadedPattern, re.MULTILINE)
    deviceRemovedPattern = re.compile(deviceRemovedPattern, re.MULTILINE)
    
    try:
        with open(file_name, 'r') as file:
            log_content = file.read()
            last_match = list(pattern.finditer(log_content))[-1]
            batteryStatusMatch = list(batteryStatusPattern.finditer(log_content))[-1]
            deviceLoadedMatches = list(deviceLoadedPattern.finditer(log_content))
            deviceRemovedMatches = list(deviceRemovedPattern.finditer(log_content))
            if last_match:
                lastDeviceName = last_match.group('name')
                lastBatteryPercentage = last_match.group('level')
            else:
                print("No match found. State")
            if batteryStatusMatch:
                lastChargingState = batteryStatusMatch.group('isCharging')
            else:
                print("No match found. Status")
            
            print("Device Loaded Matches:", len(deviceLoadedMatches))
            print("Device Removed Matches:", len(deviceRemovedMatches))
            if len(deviceLoadedMatches) > len(deviceRemovedMatches):
                deviceRemoved = False
            else:
                deviceRemoved = True

    except FileNotFoundError:
        return False, False, False, False, f"File {file_name} not found."
    except Exception as e:
        return False, False, False, False, f"An error occurred: {str(e)}"
    return lastBatteryPercentage, lastChargingState, lastDeviceName, deviceRemoved, None

def main():
    global menu_items
    global deviceName
    global chargingState
    global batteryPercentage
    global isStop
    global isDeviceRemoved

    file_name = config[razer_version]
    
    batteryStatePatern = r"^(?P<dateTime>.+?) INFO.+?_OnBatteryLevelChanged[\s\S]*?Name: (?P<name>.*)[\s\S]*?Handle: (?P<handle>\d+)[\s\S]*?level (?P<level>\d+)"
    batteryIsChargingPattern = r"^(?P<dateTime>.+?) INFO.+?_OnDevicePowerStateChanged[\s\S]*?: (?P<name>.*) (?P<isCharging>.*)"
    deviceLoadedPattern = r"^(?P<dateTime>.+?) INFO.+?_OnDeviceLoaded[\s\S]*?Name: (?P<name>.*)[\s\S]*?Handle: (?P<handle>\d+)[\s\S]"
    deviceRemovedPattern = r"^(?P<dateTime>.+?) INFO.+?_OnDeviceRemoved[\s\S]*?Name: (?P<name>.*)[\s\S]*?Handle: (?P<handle>\d+)[\s\S]"
    
    batteryPercentage, chargingState, deviceName, isDeviceRemoved, err= find_last_line_with_keyword(file_name, batteryStatePatern, batteryIsChargingPattern, deviceLoadedPattern, deviceRemovedPattern)
    
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
    global isDeviceRemoved

    while not isStop:
        err = main()  # Ana işlevi çağır
        if err:
            print(err, "Program sonlandırılıyor.")
            icon.stop()  # Sistem tepsisi simgesini kaldır
            
        if chargingState == "True":
            if 0<=int(batteryPercentage)<=20:
                image = Image.open(assetsFolder+f"/battery0_chrg_@2x.png")
            elif 21<=int(batteryPercentage)<=40:
                image = Image.open(assetsFolder+f"/battery25_chrg_@2x.png")
            elif 41<=int(batteryPercentage)<=60:
                image = Image.open(assetsFolder+f"/battery50_chrg_@2x.png")
            elif 61<=int(batteryPercentage)<=80:
                image = Image.open(assetsFolder+f"/battery75_chrg_@2x.png")
            else:
                image = Image.open(assetsFolder+f"/battery100_chrg_@2x.png")
        else:
            if 0<=int(batteryPercentage)<=20:
                image = Image.open(assetsFolder+f"/battery0_@2x.png")
            elif 21<=int(batteryPercentage)<=40:
                image = Image.open(assetsFolder+f"/battery25_@2x.png")
            elif 41<=int(batteryPercentage)<=60:
                image = Image.open(assetsFolder+f"/battery50_@2x.png")
            elif 61<=int(batteryPercentage)<=80:
                image = Image.open(assetsFolder+f"/battery75_@2x.png")
            else:
                image = Image.open(assetsFolder+f"/battery100_@2x.png")
                
        if isDeviceRemoved:
            image = Image.open(assetsFolder+f"/battery_unknown_@2x.png")
            title = "Bağlı Cihaz Yok"
        else:
            title = str(deviceName) + f" ({batteryPercentage}% - {"Şarj Ediliyor" if chargingState == "True" else "Şarj Edilmiyor"})"
        icon.icon = image  # İkonu güncelle

        print("İkon güncellendi:", deviceName, batteryPercentage)
        menu = tuple(menu_items + [item("Çıkış", exit_program)])  # Güncel menü öğelerini kullan
        icon.menu = menu  # Menüyü güncelle
        icon.title = title
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
    image = Image.open(assetsFolder+"/battery_unknown_@2x.png")
    
    menu = tuple(menu_items + [item("Çıkış", exit_program)])
    icon = pystray.Icon("Razer", image, deviceName + f" ({batteryPercentage}%)", menu)

    # Tray Icon'u göstermek için bir iş parçacığı oluştur
    tray_thread = threading.Thread(target=icon.run)
    tray_thread.start()

    # Belirli aralıklarla ana programı çalıştır
    update_icon()  # Ana programı çalıştır
