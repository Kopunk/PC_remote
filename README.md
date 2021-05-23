# 3d Remote
Wireless multi-function media controller - a university project. <br>
The following documentation is written in polish as it will be taken under grading.

# Założenia Projektu
Stworzenie bezprzewodowego urządzenia wejścia dla komputera:
   - kontrola kursora za pośrednictwem sensorów ruchu, obsługa lewego i prawego przycisku myszki
   - dodatkowo - kontrola wejścia klawaitury - wpisywanie pojedyńczych znaków gestami, obsługa spacji oraz backspace

# Technologie Wymagane do Działania
### Wymagane Urządzenia
1. Wemos D1 mini v2 (ESP8266)
2. MPU6050
3. Dodatkowe elementy:
   - koszyk na 3 baterie AA
   - 2x przycisk tact
   - 2x rezystor 10k
   - dioda schottky 20V 2A lub podobna
   - płytka stykowa i przewody
### Wymagane Programy
1. Arduino IDE 1.8+ z zainstalowanymi bibliotekami:
   - ESP8266WiFi
   - Adafruit_MPU6050
   - Wire
   - Obsługa ESP8266: 
      - dodanie ścieżki http://arduino.esp8266.com/stable/package_esp8266com_index.json w IDE: Preferences > Additional boards manager URLs
      -  instalacja esp8266 by ESP8266 Community
2. Python 3.8+ z bibliotekami (patrz: requirements.txt):
   - pynput
   - socket
   - csv
   - time
3. Zawartość repozytorium
### Opis połączenia elementów
todo
### Opis instalacji
   - skonfigurować połącznie w sieci lokalnej: 
      - `cp sample_WIFI_CONFIG.h WIFI_CONFIG.h`
      - uzupełnić WIFI_CONFIG.h odpowiednimi własnymi danymi
   - zainstalować potrzebne biblioteki i menadżer płytek w Arduino IDE
   - wgrać program do mikrokontrolera przy pomocy Arduino IDE
   - zainstalować potrzebne biblioteki python3: `pip install -r requirements.txt`
   - uczynić wymagane aplikacje .py wykonywalnymi

# Omówienie Działania i Użytkowania
## Opis działania
### Opis działania .ino
todo
### Opis klasy ConnectRemote
todo
### Opis łączności przez WiFi
todo
## Opis użytkowania
todo
