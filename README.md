# PC Remote
Accelerometer / gyroscope - based PC cursor controller & gesture character input - a university project. <br>
The following documentation is written in polish as it will be taken under grading.

## Cel projektu
Stworzenie bezprzewodowego urządzenia wejścia dla komputera:
   - Kontrola kursora za pośrednictwem sensorów ruchu, obsługa lewego i prawego przycisku myszki.
   - Dodatkowo: kontrola wejścia klawiatury - zapisywanie pojedynczych znaków gestami, obsługa spacji oraz backspace, przełączanie klawisza CapsLock.

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
      - instalacja esp8266 by ESP8266 Community
2. Python 3.8+ z bibliotekami ([zgodnie z requirements.txt](https://github.com/Kopunk/PC_remote/blob/requirements.txt)):
   - numpy 1.19.2
   - pynput 1.7.3
   - tensorflow 2.5.0
   - dataclasses 0.8

## Schemat ideowy układu - "urządzenia"
![schemat ideowy](https://drive.google.com/uc?export=view&id=18EAJDH0eFiJiyNu5_lGT1Exfb5PC0sI4)
### Opis połączeń, "+" i "-" ozn. połączenie zasilania i masy na płytce stykowej.
Od | Do
-- | --
Wemos D1 mini: 3v3 | +
Wemos D1 mini: G | -
Wemos D1 mini: D1 | MPU6050: SCL
Wemos D1 mini: D2 | MPU6050: SDA
Wemos D1 mini: D3 | przycisk Main: a
Wemos D1 mini: D4 | przycisk Sec: a
dioda schottky: + | baterie: +
dioda schottky: - | +
baterie: - | -
przycisk Main: b | rezystor 1
przycisk Main: b | -
przycisk Sec: b | rezystor 2
przycisk Sec: b | -
rezystor 1 | +
rezystor 2 | +

## Listing programu
### [3d_remote.ino](https://github.com/Kopunk/PC_remote/blob/v2.0/3d_remote.ino)
Program działający na urządzeniu. Wymaga pliku nagłówkowego WIFI_CONFIG.h.
 - Stałe:
   - `int buttonPinMain` - numer pinu połączenia przycisku Main;
   - `int buttonPinSec` - numer pinu połączenia przycisku Sec;
   - `char endMsg[]` - wiadomość zwolnienia przycisku Main;
   - `char pressSecMsg[]` - wiadomość naciśnięcia przycisku Sec;
   - `char releaseSecMsg[]` - wiadomość zwolnienia przycisku Sec;
- Zmienne globalne:
   - `WiFiUDP UDP` - obiekt klasy komunikacji przez UDP;
   - `Adafruit_MPU6050 MPU` - obiekt klasy obsługującej sensor MPU6050;
   - `sensors_event_t acc, gyro, temp` - obiekty reprezentujące odczyty akcelerometru, żyroskopu, czujnika temperatury;
   - `float sensors[7]` - tablica odczytów kolejno akcelerometru (3), żyroksopu (3), temperatury (1);
   - `bool buttonPressedMain = false` - zmienna przechowująca obecny stan przycisku Main;
   - `bool buttonPressedSec = false` - zmienna przechowująca obecny stan przycisku Sec;
- Funkcje:
   - `buttonHold(buttonPinMain)` - zwraca `true` jeśli przycisk `buttonPinMain` (argument) jest wciśnięty, w przeciwnym wypadku `false`;
   - `setup()`:
      - inicjalizuje połączenie szeregowe USB dla możliwości podglądu komunikatów w monitorze szeregowym Arduino IDE;
      - inicjalizuje buttonPinMain oraz buttonPinSec jako wejścia cyfrowe;
      - inicjalizuje obiekt urządzenia MPU6050;
      - inicjalizuje połączenie z WiFi;
      - wypisuje (w przypadku połączenia monitora szeregowego) przypisany adres IP urządzenia;
      - inicjalizuje komunikację UDP na zadanym porcie;
      - oczekuje "sygnału gotowości" ze strony PC (patrz: remote.py send_ready_signal());
      - po otrzymaniu sygnału kontynuuje do funkcji `loop()`;
   - `loop()`:
      - zbiera odczyty sensorów MPU do tablicy `sensors`;
      - tworzy obiekt `msg` typu String, konwertuje na ciągi znaków pierwsze 6 pól `sensors` (bez temperatury) i dodaje do `msg` oddzielając wartości dwukropkami;
      - w przypadku naciśnięcia przycisku Main wysyła przez UDP przygotowany String `msg`, ustawia wartość `buttonPressedMain` na `true`;
      - w przeciwnym wypadku jeśli `buttonPressedMain` ma wartość `true`, ustawia ją na `false` i wysyła wiadomość zwolnienia przycisku Main przez UDP;
      - w przypadku naciśnięcia przycisku Sec wysyła wiadomość naciśnięcia przycisku Sec przez UDP i ustawia wartość `buttonPressedSec` na `true`;
      -  w przeciwnym wypadku jeśli `buttonPressedSec` ma wartość `true`, ustawia ją na `false` i wysyła wiadomość zwolnienia przycisku Sec przez UDP;

### [sample_WIFI_CONFIG.h](https://github.com/Kopunk/PC_remote/blob/v2.0/sample_WIFI_CONFIG.h)
Plik nagłówkowy dla 3d_remote.ino, zawiera konfigurację połączenia bezprzewodowej sieci lokalnej: SSID, hasło, adres IP PC, port sieciowy urządzenia, port sieciowy PC. By wykonać konfigurację należy:
 - skopiować go pod nową nazwą WIFI_CONFIG.h: `cp sample_WIFI_CONFIG.h WIFI_CONFIG.h`;
 - uzupełnić WIFI_CONFIG.h odpowiednimi własnymi danymi;

### [remote.py](https://github.com/Kopunk/PC_remote/blob/v2.0/remote.py)
#### Klasa CharSignal
Reprezentuje odczyt sygnału znaku w postaci zapisu odczytów akcelerometru wykonanego gestu znaku i pola znaku.
 - Pola:
    - `char: str` - znak A-Z, "-" (ozn. backspace), "\_" (ozn. spację) lub "?" (znak nieznany - do oszacowania);
    - `signal` - lista pythonowska dwuwymiarowa float odczytów akcelerometru;
 - Metody:
    - `set_length(new_length)` - ustawia ilość wierszy pola sygnałów na new_length, 'przycina' lub uzupełnia wartościami zerowymi;
    - `get_array()` - zwraca pole sygnałów typu tablicy numpy zamiast użycia list pythonowskich;
#### Klasa SensorConfig
Przechowuje zmienne konfiguracji sensorów z poziomu aplikacji.
 - Pola:
    - `mode: str` - determinuje czy tryb kursora działa przy użyciu akcelerometru ("acc"), żyroskopu ("gyro") czy połączenia obu ("hybrid");
    - `accel_multiplier: float` - mnożnik odczytów akcelerometru w trybie kursora;
    - `accel_treshold: float` - próg odczytów akcelerometru w trybie kursora, zapobiega ruchom kursora gdy urządzenie jest nieruchome;
    - `gyro_multiplier: float` - mnożnik odczytów żyroskopu w trybie kursora;
    - `gyro_treshold: float` - próg odczytów żyroskopu w trybie kursora;
    - `double_click_time: float` - maksymalny czas rejestracji akcji podwójnego kliknięcia;
    - `button_hold_time: float` - minimalny czas rejestracji akcji przytrzymania przycisku;
    - `hybrid_switch_treshold: float` - próg zmiany wejścia żyroskopu na akcelerometr w trybie kursora w trybie hybrydowym;
#### Klasa ConnectionConfig
Przechowuje zmienne konfiguracji połączenia z urządzeniem w bezprzewodowej sieci lokalnej.
 - Pola:
    - `remote_ip: str` - adres IP urządzenia;
    - `remote_port: int` - port sieciowy urządzenia;
    - `server_ip: str` - adres IP PC;
    - `server_port: int` - port sieciowy PC;
    - `server_addr` - krotka `(server_ip, server_port)`;
    - `remote_addr` - krotka `(remote_ip, remote_port)`;
#### Klasa TrainingConfig
Przechowuje zmienne konfiguracji dla trybu uczenia maszynowego.
 - Pola:
   - `max_input_len: int` - maksymalna długość sygnału (ilość wierszy pola `signal` klasy CharSignal);
   - `training_data_path: str` - nazwa podkatalogu zawierającego pliki sygnałów znaków do uczenia, w przypadku braku "/" po nazwie dodaje automatycznie;
#### Klasa Remote
Główna klasa pliku, zawiera wszystkie funkcje projektu ze strony PC.
 - Stałe: 
   - `COMM_MSG` - dwustronny słownik zastępujący wcześniej wykorzystywane `MAIN_RELEASE_MSG`, `SEC_PRESS_MSG`, `SEC_RELEASE_MSG`, tłumaczy krótkie ciągi znaków oznaczające akcje przycisków przesyłane przez urządzenie na bardziej czytelne, łatwiejsze do interpretacji;
- Pola:
   - `sesensor_config: SensorConfig` - instancja klasy SensorConfig z konfiguracją (patrz: SensorConfig);
   - `conn_config: ConnectionConfig` - instancja klasy ConnectionConfig z konfiguracją (patrz: ConnectionConfig);
   - `training_config: TrainingConfig` - instancja klasy TrainingConfig z konfiguracją (patrz: TrainingConfig);
   - `verbose: bool` - determinuje czy program będzie drukował komunikaty podczas działania;
   - `train_labels` - przechowuje tablicę liczb "labels" odpowiadające indeksom pola `available_chars`, wykorzystywane przy uczeniu;
   - `train_values` - przechowuje tablicę sygnałów gestów znaków, wykorzystywane przy uczeniu;
   - `training_sequence` - przechowuje listę znaków których sygnały mają być wprowadzone przez użytkownika (gesty znaków) i zapisane w plikach;
   - `model` - przechowuje wytrenowany z zebranych danych model uczenia maszynowego;
   - `available_chars: tuple` - przechowuje zbiór dostępnych do trenowania znaków, bez powtórzeń;
 - Metody:
   - konstruktor - tworzy wszystkie opisane pola, tworzy obiekt socket, tworzy podkatalog `TrainingConfig.training_data_path` jeśli nie istnieje;
   - `verbose(s)` - drukuje na ekran ciąg znaków `s` jeśli pole `verbose` ma wartość `True`;
   - `send_ready_signal()` - wysyła wartość 1 do urządzenia, które po włączeniu oczekuje na ten sygnał i nie nada żadnych danych do tego momentu;
   - `receive_data()` - odbiera przesłany przez urządzenie sygnał (ciąg znaków), dekoduje i zwraca odpowiednio: ciąg znaków w przypadku sygnału akcji przycisku, krotka dwóch list pythonowskich z odczytami akcelerometru i żyroskopu (pojedynczy wiersz);
   - `receive_char(char)` - korzystając z `receive_data()` odbiera sygnał całego gestu znaku i zwraca instancję CharSignal o zadanym przez argument `char` polu `char`;
   - `cursor_mode()` - wykorzystując konfigurację w polu `sensor_config` odbiera w pętli i przetwarza sygnały urządzenia, reaguje na podwójne kliknięcie przycisku Main wyjściem z pętli, przycisk Sec powoduje wywołanie kliknięcia lewego przycisku myszki, przytrzymanie - prawego przycisku myszki, ruchy kursora odbywają się przy przytrzymaniu przycisku Main w zależności od wybranego trybu sterowania: akceleratora, żyroskopu, hybrydowego;
   - `prepare_keyboard()` - wywołuje metody `prepare_training_data()`, `train()`, drukuje na ekran wielkość zbioru uczącego;
   - `keyboard_mode()` - wykorzystując metodę `receive_char()` w pętli odbiera sygnały znaków i przewiduje znak którego gest został wykonany urządzeniem, wprowadza znak w miejscu kursora, przycisk Sec przełącza klawisz CapsLock, podwójne kliknięcie przycisku Main wychodzi z pętli wprowadzania;
   - `cursor_keyboard_mode()` - wywołuje metodę `prepare_keyboard()`, w nieskończonej pętli wywołuje metody `cursor_mode()`, `keyboard_mode()`, pozwala to na przełączanie się między trybem kursora i klawiatury;
   - `prepare_char(data)` - zwraca tablicę numpy sygnału gestu `data` o długości zadanej przez `TrainingConfig.max_input_len`;
   - `predict_char(data)` - zwraca znak oszacowany przez model uczenia maszynowego na podstawie sygnału gestu `data`;
   - `set_training_char_sequence(chars, repeats, shuffle_chars, include_extra_chars)` - na podstawie listy znaków `chars` tworzy listę `training_sequence`, dodaje znak spacji i backspace w zależności od `include_extra_chars`, ilość powtórzeń każdego znaku w zależności od `repeats`, ustawia losową kolejność `training_sequence` w zależności od `shuffle_chars`, zwraca łączną długość `training_sequence`;
   - `next_file_no(char)` - zwraca numer następnego pliku dla danego znaku `char` w podkatalogu zadanym przez `TrainingConfig.training_data_path`;
   - `write_to_dataset(char_signal)` - zapisuje obiekt CharSignal `char_signal` do nowego pliku .csv w podkatalogu zadanym przez `TrainingConfig.training_data_path`, konwencja nazewnicza: `<znak><numer pliku znaku>.csv`, przykład: C15.csv, -0.csv, \_50.csv;
   - `prepare_training_data()` - czyta sygnały z plików .csv z podkatalogu zadanego przez `TrainingConfig.training_data_path` i zapisuje do pól `train_labels` (z nazwy pliku), `train_values` (zwartość - sygnał);
   - `train()` - wykorzystując przygotowane przez `prepare_training_data()` `train_labels` i `train_values` wykorzystuje TensorFlow do utworzenia modelu zapisanego do pola `model`;
   - `train_mode(char_sequence, repeats, shuffle_chars, include_extra_chars)` - wykorzystuje `set_training_char_sequence()`, iterując po wypełnionym polu `training_sequence` wypisuje kolejne znaki na ekran i przy pomocy `write_to_dataset()` zapisuje sygnał wykonanego przez użytkownika gestu znaku do pliku;
#### funkcja `main()`
W przypadku uruchomienia pliku `remote.py` program tworzy obiekt Remote ze standardową konfiguracją, wywołuje `send_ready_signal()` a następnie `cursor_keyboard_mode()`.

### [training_example.py](https://github.com/Kopunk/PC_remote/blob/v2.0/training_example.py)
Program mający na celu wykorzystanie komponentów remote.py w celu zebrania sygnałów gestów użytkownika znaków "L", "M", "N" w 7 powtórzeniach, z wprowadzaniem w losowej kolejności. Po zakończeniu uczenia przechodzi w tryb wprowadzania klawiatury gdzie użytkownik może sprawdzić efekt  wprowadzonych wcześniej danych. Zapis odbywa się w niestandarodwym podfolderze by brane pod uwagę były tylko nowe dane.

### [requirements.txt](https://github.com/Kopunk/PC_remote/blob/v2.0/requirements.txt)
Plik zawierający wymagające instalacji nazwy bibliotek python3 wraz z wersjami. Instalacja: `pip install -r requirements.txt`.

### [Ta dokumentacja](https://github.com/Kopunk/PC_remote/blob/v2.1/README.md)

## Opis działania
### Instalacja
`git clone git@github.com:Kopunk/PC_remote.git`

#### Konfiguracja sieciowa
 - skopiować sample_WIFI_CONFIG.h pod nową nazwą WIFI_CONFIG.h: `cp sample_WIFI_CONFIG.h WIFI_CONFIG.h`
 - ustawić stały lokalny adres IP komputera, wprowadzić go w konfiguracji WIFI_CONFIG.h oraz remote.py
 - adres IP urządzenia można sprawdzić przy pomocy podglądu monitora szeregowego Arduino IDE, wprowadzić go w konfiguracji remote.py przy inicjalizacji klasy (jak pokazano poniżej)
 ```python3
 def main():
    r = Remote(SensorConfig(), ConnectionConfig(remote_ip='<ip urządzenia>', server_ip='<ip komputera>'), TrainingConfig())
 ```
 #### Instalacja wymaganych bibliotek
 - instalacja bibliotek python3: `pip install -r requirements.txt`
 - instalacja bibliotek dla mikrokontrolera (z poziomu Arduino IDE):
   - dodanie ścieżki http://arduino.esp8266.com/stable/package_esp8266com_index.json w IDE: Preferences > Additional boards manager URLs
   - instalacja esp8266 by ESP8266 Community
   - instalacja Adafruit MPU6050 by Adafruit

### Omówienie działania projektu ze strony użytkownika
Aby uruchomić i połączyć urządzenie należy w pierwszej kolejności podłączyć urządzenie do zasilania (przez USB lub podłączając baterie) a następnie uruchomić program remote.py. W trakcie działania urządzenia można bez problemów podłączać i odłączać kabel USB jeśli podłączone jest zasilanie z baterii. W terminalu uruchomionego programu domyślnie wyświetlają się komunikaty ułatwiające orientację.

Domyślnie po włączeniu aktywny jest tryb kursora. Aby przesunąć kursor należy przytrzymać przycisk Main a następnie wykonać ruch urządzeniem obserwując kursor na ekranie. Aby wykonać kliknięcie lewym przyciskiem myszy należy nacisnąć przycisk Sec, operacja jest rejestrowana wraz ze zwolnieniem przycisku. Należy naciskać tylko jeden przycisk na raz. Aby wykonać kliknięcie prawym przyciskiem myszy należy przytrzymać przycisk Sec. Aby przełączyć się w tryb klawiatury należy dwukrotnie nacisnąć przycisk Main.

W trybie klawiatury przytrzymanie przycisku Main i wykonanie urządzeniem gestu wprowadzanego znaku spowoduje wprowadzenie znaku w miejscu kursora na komputerze. Gest - przesunięcie poziomo w lewo spowoduje usunięcie znaku przed kursorem (backspace), natomiast przesunięcie poziomo w prawo spowoduje wprowadzenie spacji. Aby przełączyć klawisz CapsLock należy nacisnąć przycisk Sec. Obecnie zakładane jest używanie znaków z zakresu A-Z (oraz a-z po przełączeniu CapsLock, gesty pozostają takie same), spacji oraz backspace. Aby przełączyć się z powrotem w tryb kursora należy dwukrotnie nacisnąć przycisk Main.

W przypadku korzystania z trybu uczenia w oknie terminala wyświetlają się znaki do wprowadzenia, użytkownik powinien postępować tak jakby chciał wprowadzić wyświetlony znak w trybie klawiatury.

## Wnioski
Cel projektu został w pełni osiągnięty. Udało się stworzyć nie tylko narzędzie zdalnej kontroli kursora, ale również "wirtualnej klawiatury". Kontrola kursora oraz wprowadzania znaków są wystarczająco dokładne by dało się praktycznie wykorzystywać projekt. Ze strony technicznej najwięcej trudności sprawiło zastosowanie bublioteki TensorFlow ze względu na stosunkowo małe doświadczenie z uczeniem maszynowym. Klasa Remote wraz z klasami pomocniczymi jest prosta do wykorzystania w osobnych programach (jak pokazano w [training_example.py](https://github.com/Kopunk/PC_remote/blob/v2.0/training_example.py)) i pozwala wykorzystywać urządzenie na kilka sposobów.

## Załączniki

