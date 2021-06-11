# PC Remote
Accelerometer / gyroscope - based PC cursor controller & gesture character input - a university project. <br>
The following documentation is written in polish as it will be taken under grading.

## Cel projektu
Stworzenie bezprzewodowego urządzenia wejścia dla komputera:
   - kontrola kursora za pośrednictwem sensorów ruchu, obsługa lewego i prawego przycisku myszki
   - dodatkowo - kontrola wejścia klawiatury - zapisywanie pojedynczych znaków gestami, obsługa spacji oraz backspace, przełączanie klawisza caps lock

## BOM (Bill of Materials) - wykorzystane elementy
### Hardware
1. Wemos D1 mini v2 (ESP8266)
2. MPU6050
3. Dodatkowe elementy:
   - koszyk na 3 baterie AA
   - 2x przycisk tact (Main oraz Sec(ondary))
   - 2x rezystor 10k
   - dioda schottky 20V 2A lub podobna
   - płytka stykowa i przewody
### Software
1. Arduino IDE 1.8+ z zainstalowanymi bibliotekami:
   - ESP8266WiFi
   - Adafruit_MPU6050
   - Wire
   - Obsługa ESP8266: 
      - dodanie ścieżki http://arduino.esp8266.com/stable/package_esp8266com_index.json w IDE: Preferences > Additional boards manager URLs
      -  instalacja esp8266 by ESP8266 Community
2. Python 3.8+ z bibliotekami:
   - patrz: requirements.txt

## Schemat ideowy układu
![schemat ideowy](https://drive.google.com/uc?export=view&id=18EAJDH0eFiJiyNu5_lGT1Exfb5PC0sI4)

## Listing programu
### Opis klasy Remote
Klasa Remote zawiera metody pozwalające na łączność z urządzeniem, sterowanie ruchami kursora, naciskanie przycisków myszki oraz klawiatury, łatwe tworzenie zbiorów sygnałów akcelerometru odpowiadających znakom A-Z, spacja i backspace, uczenie maszynowe ze zbiorów sygnałów przy pomocy TensorFlow oraz metody pomocnicze. Opis możliwego użytku klasy:
   - Inicjalizowana z instancjami klas SensorConfig, ConnectionConfig, TrainingConfig (przechowujące odpowiednio konfiguracje reakcji na sygnały urządzenia; połaczenia przez WiFi; położenie danych treningowych i maksymalna długość sygnału znaku).
   - Wysłanie sygnału gotowości programu.
   - Tryb kursora:
      - poruszanie kursorem przy pomocy odczytów z akcelerometru, żyroskopu lub połączenia sygnałów obu przy przytrzymaniu przycisku Main
      - kliknięcie lewym przyciskiem myszki poprzez przycisk Sec
      - kliknięcie prawym przyciskiem myszki poprzez przytrzymanie przycisku Sec
      - wyjście poprzez podwójne kliknięcie (zwolnienie) przycisku Main
   - Tryb klawiatury:
      - wprowadzenie znaku poprzez przytrzymanie przycisku Main i wykonanie gestu urządzeniem (zależne od zbioru treningowego - można wprowadzić tylko kilka znaków)
      - wprowadzenie spacji lub usunięcie znaku przed kursorem (backspace) (podobnie jak powyżej)
      - przełączenie przycisku caps lock poprzez naciśnięcie przycisku Sec
      - wyjście poprzez podwójne kliknięcie (zwolnienie) przycisku Main
   - Tryb kursora i klawiatury:
      - przełączanie pomiędzy trybem kursora i klawiatury przy wyjściu z danego trybu
   - Tryb szkolenia:
      - ustalenie sekwencji znaków do wprowadzania i lokalizacji plików sygnałów do późniejszego szkolenia
      - odczytywanie plików .csv z zapisanymi sygnałami (format nazwy pliku: ZnakNumer.csv - A12.csv, \_3.csv, X0.csv, \-10.csv)
      - uczenie ze zbioru sygnałów treningowych

## Opis działania

## Wnioski

## Załączniki

# ---TMP---


### Opis połączenia elementów
Połączenie z opisywanego elementu ➡️ cel. Cel "+" i "-" ozn. połączenie zasilania i masy na płytce stykowej.
 - Wemos D1 mini
    - 3v3 ➡️ +
    - G ➡️ -
    - D1 ➡️ MPU6050: SCL
    - D2 ➡️ MPU6050: SDA
    - D3 ➡️ przycisk Main a
    - D4 ➡️ przycisk Sec a
 - schottky
    - \+ ➡️ baterie: +
    - \- ➡️ +
 - baterie
    - \- ➡️ -
 - przycisk Main
    - a ➡️ rezystor ➡️ +
    - b ➡️ -
 - przycisk Main
    - a ➡️ rezystor ➡️ +
    - b ➡️ -
### Opis instalacji
   - skonfigurować połączenie w sieci lokalnej: 
      - `cp sample_WIFI_CONFIG.h WIFI_CONFIG.h`
      - uzupełnić WIFI_CONFIG.h odpowiednimi własnymi danymi
   - zainstalować potrzebne biblioteki i menadżer płytek w Arduino IDE
   - wgrać program do mikrokontrolera przy pomocy Arduino IDE
   - zainstalować potrzebne biblioteki python3: `pip install -r requirements.txt`
   - uczynić wymagane aplikacje .py wykonywalnymi

# Omówienie Działania i Użytkowania
## Opis działania
### Opis działania .ino
   - Inicjalizuje połączenie wg WIFI_CONFIG.h. 
   - Oczekuje sygnału gotowości programu. 
   - W przypadku naciśnięcia / przytrzymania przycisku Main przesyła ciągi znaków odpowiadające odczytom akcelerometru i żyroskopu.
   - W przypadku zwolnienia przycisku Main przesyła sygnał zwolnienia przycisku Main.
   - W przypadku naciśnięcia / przytrzymania przycisku Sec przesyła sygnał / sygnały naciśnięcia przycisku Sec.
   - W przypadku zwolnienia przycisku Sec przesyła sygnał zwolnienia przycisku Sec.
### Opis klasy Remote
Klasa Remote zawiera metody pozwalające na łączność z urządzeniem, sterowanie ruchami kursora, naciskanie przycisków myszki oraz klawiatury, łatwe tworzenie zbiorów sygnałów akcelerometru odpowiadających znakom A-Z, spacja i backspace, uczenie maszynowe ze zbiorów sygnałów przy pomocy TensorFlow oraz metody pomocnicze. Opis możliwego użytku klasy:
   - Inicjalizowana z instancjami klas SensorConfig, ConnectionConfig, TrainingConfig (przechowujące odpowiednio konfiguracje reakcji na sygnały urządzenia; połaczenia przez WiFi; położenie danych treningowych i maksymalna długość sygnału znaku).
   - Wysłanie sygnału gotowości programu.
   - Tryb kursora:
      - poruszanie kursorem przy pomocy odczytów z akcelerometru, żyroskopu lub połączenia sygnałów obu przy przytrzymaniu przycisku Main
      - kliknięcie lewym przyciskiem myszki poprzez przycisk Sec
      - kliknięcie prawym przyciskiem myszki poprzez przytrzymanie przycisku Sec
      - wyjście poprzez podwójne kliknięcie (zwolnienie) przycisku Main
   - Tryb klawiatury:
      - wprowadzenie znaku poprzez przytrzymanie przycisku Main i wykonanie gestu urządzeniem (zależne od zbioru treningowego - można wprowadzić tylko kilka znaków)
      - wprowadzenie spacji lub usunięcie znaku przed kursorem (backspace) (podobnie jak powyżej)
      - przełączenie przycisku caps lock poprzez naciśnięcie przycisku Sec
      - wyjście poprzez podwójne kliknięcie (zwolnienie) przycisku Main
   - Tryb kursora i klawiatury:
      - przełączanie pomiędzy trybem kursora i klawiatury przy wyjściu z danego trybu
   - Tryb szkolenia:
      - ustalenie sekwencji znaków do wprowadzania i lokalizacji plików sygnałów do późniejszego szkolenia
      - odczytywanie plików .csv z zapisanymi sygnałami (format nazwy pliku: ZnakNumer.csv - A12.csv, \_3.csv, X0.csv, \-10.csv)
      - uczenie ze zbioru sygnałów treningowych
## Dodatkowe informacje
   - klasa CharSignal służy do przechowywania nazwy znaku wraz z odpowiadającym sygnałem, umożliwia zwracanie tablicy numpy sygnału, skracanie oraz wydłużanie  sygnału (uzupełnienie zerami)
   - atrybut verbose klasę Remote gdy o wartości True umożliwia wyświetlanie komunikatów dotyczących pracy programu, domyślnie ma wartość True
   - plik training_example.py zawiera przykładowe użycie metod Remote w celu uzupełniania zbioru sygnałów do późniejszego szkolenia
   - w sekwencji znaków do wprowadzania oraz w nazwach plików z sygnałami podkreślnik i myślnik oznaczają kolejno spację oraz backspace
