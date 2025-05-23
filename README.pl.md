Asystent AI dla Systemu Linux (GUI i CLI)

Wszechstronny asystent napędzany sztuczną inteligencją, który pomaga generować, rozumieć i wykonywać polecenia Linuksa przy użyciu języka naturalnego. Projekt dostarcza zarówno Graficzny Interfejs Użytkownika (GUI), jak i Interfejs Wiersza Poleceń (CLI), oba wykorzystujące Google Gemini.

![alt text](https://img.buymeacoffee.com/button-api/?text=Kup%20mi%20kawę&emoji=☕&slug=krzyzu.83&button_colour=FF5F5F&font_colour=ffffff&font_family=Arial&outline_colour=000000&coffee_colour=FFDD00)

Projekt na GitHub: hyconiek/linux_ai_terminal_assistant
🎉 Najnowsze Wydanie: v1.0.4 - Rozszerzony Kontekst i Interakcja! 🎉

![alt text](./screenshot.png)


Najłatwiejszym sposobem na wypróbowanie Asystenta AI dla Linuksa (GUI) jest pobranie naszego najnowszego wydania w formacie AppImage lub jako samodzielny plik wykonywalny! Pliki AppImage są przenośne i powinny działać na większości nowoczesnych dystrybucji Linuksa bez potrzeby instalacji.

➡️ Pobierz Linux-AI-Assistant-x86_64.AppImage lub plik wykonywalny Linux-AI-Assistant-onefile z sekcji Wydań (v1.0.4) ⬅️
Co Nowego w v1.0.4:

    Kontekstowa Świadomość CWD: AI otrzymuje teraz listę plików i katalogów z Twojego bieżącego katalogu roboczego (CWD), aby dostarczać bardziej trafne sugestie poleceń i odpowiadać na pytania dotyczące zawartości CWD.

    Wyszukiwanie Plików na Żądanie AI: Jeśli zapytasz o pliki, które nie są od razu widoczne na początkowej liście CWD, AI może poprosić backend o wykonanie szybkiego przeszukania (find . -maxdepth 2 ...) w CWD i jego bezpośrednich podkatalogach. Wyniki są następnie przekazywane z powrotem do AI w celu uzyskania bardziej świadomej odpowiedzi lub polecenia.

    Inteligentniejsze Sugestie Interakcji: AI może teraz sugerować konkretne etykiety przycisków dla GUI, jeśli polecenie ma być interaktywne (np. "Zainstaluj (potwierdź T)"). W przypadku takiej sugestii, GUI zaoferuje uruchomienie polecenia w zewnętrznym terminalu w celu bezpośredniego wprowadzenia danych przez użytkownika.

    Tekstowe Odpowiedzi na Pytania o CWD: Zapytaj AI "Czy są tu jakieś pliki związane ze snap?" a ono może teraz odpowiedzieć tekstowo na podstawie listy plików w CWD, zamiast generować tylko polecenia.

    Ulepszone Kontekstowe Kontynuacje: Po omówieniu plików w CWD, możesz odnosić się do nich bardziej naturalnie w kolejnych poleceniach (np. "zmień nazwę tego pliku snap").

Jak Uruchomić:
AppImage:

    Pobierz plik Linux-AI-Assistant-x86_64.AppImage.

    Nadaj uprawnienia do wykonania: chmod +x Linux-AI-Assistant-x86_64.AppImage

    Uruchom: ./Linux-AI-Assistant-x86_64.AppImage
    (Niektóre środowiska graficzne mogą również pozwolić na uruchomienie poprzez dwukrotne kliknięcie.)

Samodzielny Plik Wykonywalny (PyInstaller onefile):

    Pobierz plik wykonywalny Linux-AI-Assistant-onefile (lub o podobnej nazwie).

    Nadaj uprawnienia do wykonania: chmod +x Linux-AI-Assistant-onefile

    Uruchom: ./Linux-AI-Assistant-onefile

Pierwsza Konfiguracja:

    Klucz API: Przy pierwszym uruchomieniu, jeśli klucz API Gemini nie jest skonfigurowany, zostaniesz poproszony o jego wprowadzenie. Klucz możesz uzyskać z Google AI Studio.

    Możesz zarządzać swoim kluczem API i innymi ustawieniami poprzez "Ustawienia" (Plik > Ustawienia lub ikona koła zębatego).

Uwagi dotyczące AppImage:

    Rozmiar: AppImage zawiera Pythona i niezbędne biblioteki. Rozmiar może się różnić w zależności od wydania.

    Integracja z Pulpitem: Dla ikon w menu rozważ użycie "AppImageLauncher" lub ręczne utworzenie pliku .desktop.

    Wymagania: 64-bitowa dystrybucja Linuksa (zalecane glibc 2.35+), może być wymagany pakiet fuse dla AppImage (sudo apt install fuse).

Główne Funkcje

    Intuicyjny interfejs GUI/CLI: Wybierz preferowany sposób interakcji.

    Język Naturalny na Polecenia: Proś o polecenia w języku naturalnym (obsługiwane przez Google Gemini).

    Napędzany przez AI: Wykorzystuje Google Gemini do sugestii poleceń, wyjaśnień i analizy zawartości CWD.

    Bezpośrednie Wykonywanie Poleceń: (GUI) Uruchamiaj wygenerowane polecenia bezpośrednio lub w zewnętrznym terminalu dla poleceń interaktywnych.

    Kopiowanie do Schowka: (GUI) Łatwo kopiuj polecenia lub tekstowe odpowiedzi AI.

    Zarządzanie Kluczem API: (GUI) Bezpiecznie przechowuj i zarządzaj swoim kluczem API Google Gemini.

    Personalizowane Motywy: (GUI) Wsparcie dla trybu Ciemnego (domyślny) i Jasnego.

    Przełącznik Szczegółowości Logów: (GUI) Kontroluj ilość informacji systemowych/debugowania.

    Potencjał Wieloplatformowy: Zbudowany przy użyciu Pythona i PyQt5.

Jak Zdobyć Klucz API Gemini

    Odwiedź Google AI Studio.

    Zaloguj się na swoje konto Google.

    Przejdź do "Klucze API" (API keys) w panelu bocznym.

    Kliknij "Utwórz klucz API" (Create API key) i skopiuj wygenerowany klucz.

Korzystanie z Interfejsu Wiersza Poleceń (CLI)

Główna logika jest również dostępna jako narzędzie CLI (src/backend_cli.py), używane przez GUI.
Wymagania Wstępne (CLI)

    Python 3.7+ (zalecany Python 3.11+).

    Aktywny klucz API Google Gemini.

Konfiguracja (CLI)

    Sklonuj repozytorium:

          
    git clone https://github.com/hyconiek/linux_ai_terminal_assistant.git
    cd linux_ai_terminal_assistant

        

    IGNORE_WHEN_COPYING_START

Use code with caution. Bash
IGNORE_WHEN_COPYING_END

Utwórz i aktywuj środowisko wirtualne (zalecane):

      
python3 -m venv venv
source venv/bin/activate  # W systemie Windows: venv\Scripts\activate

    

IGNORE_WHEN_COPYING_START
Use code with caution. Bash
IGNORE_WHEN_COPYING_END

Zainstaluj zależności:
(Upewnij się, że requirements.txt jest aktualny i zawiera google-generativeai oraz PyQt5 jeśli uruchamiasz GUI ze źródeł)

      
pip install -r requirements.txt

    

IGNORE_WHEN_COPYING_START
Use code with caution. Bash
IGNORE_WHEN_COPYING_END

Ustaw Klucz API (CLI):
Backend CLI oczekuje zmiennej środowiskowej GOOGLE_API_KEY.

      
export GOOGLE_API_KEY="TWÓJ_KLUCZ_API_GEMINI"

    

IGNORE_WHEN_COPYING_START

    Use code with caution. Bash
    IGNORE_WHEN_COPYING_END

    Aby ustawić na stałe, dodaj tę linię do pliku konfiguracyjnego swojej powłoki (np. .bashrc, .zshrc).

Przykłady Użycia CLI

(Uruchom z głównego katalogu sklonowanego repozytorium)

      
# Backend CLI do generowania poleceń/odpowiedzi tekstowych (tryb interaktywny)
python3 src/backend_cli.py

# Dla konkretnego zapytania (wyjście JSON używane przez GUI)
python3 src/backend_cli.py --query "czy są tu jakieś pliki tekstowe?" --json --working-dir "/ścieżka/do/twojego/katalogu"

    

IGNORE_WHEN_COPYING_START
Use code with caution. Bash
IGNORE_WHEN_COPYING_END
Budowanie Aplikacji GUI ze Źródeł

Jeśli chcesz samodzielnie zbudować aplikację GUI:
Wymagania Wstępne (Budowanie GUI)

    Wszystkie wymagania dla CLI.

    PyQt5: PyQt5>=5.15.0

    PyInstaller: pip install pyinstaller

Kroki Budowania

    Upewnij się, że projekt jest skonfigurowany, a zależności są zainstalowane w środowisku wirtualnym.

    Przejdź do głównego katalogu projektu.

    Uruchom PyInstallera. Dla pliku wykonywalnego typu one-file:

          
    pyinstaller --name "Linux-AI-Assistant-onefile" \
                --onefile \
                --windowed \
                --add-data "app_icon.png:." \
                --add-data "src:src" \
                --hidden-import="google.generativeai" \
                --hidden-import="google.ai.generativelanguage" \
                --hidden-import="google.auth" \
                --hidden-import="google.api_core" \
                --hidden-import="google.protobuf" \
                --hidden-import="google.type" \
                --hidden-import="google.rpc" \
                --hidden-import="google.longrunning" \
                --hidden-import="google.iam" \
                --hidden-import="google.oauth2" \
                --hidden-import="proto" \
                --hidden-import="grpc" \
                --hidden-import="PIL" \
                --hidden-import="pkg_resources" \
                --hidden-import="pkg_resources.py2_warn" \
                --hidden-import="argparse" \
                --hidden-import="backend_cli" \
                linux_ai_assistant_gui.py

        

    IGNORE_WHEN_COPYING_START

    Use code with caution. Bash
    IGNORE_WHEN_COPYING_END

    Plik wykonywalny znajdzie się w katalogu dist (np. dist/Linux-AI-Assistant-onefile).
    (Tworzenie AppImage jest bardziej złożonym procesem, często wykorzystującym linuxdeployqt, realizowanym np. w kontenerze Docker lub specjalnie skonfigurowanym notatniku Colab.)

Licencja

Projekt stworzony przez Krzysztofa Żuchowskiego.
Copyright © 2025 Krzysztof Żuchowski. Wszelkie prawa zastrzeżone.

Na licencji MIT License.

Stworzone z ❤️ i Pythonem.
