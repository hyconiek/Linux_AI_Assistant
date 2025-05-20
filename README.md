# linux_ai_terminal_assistant
      
# Asystent AI dla Systemu Linux

[![Licencja: MIT](https://img.shields.io/badge/Licencja-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Asystent AI dla systemu Linux to narzędzie wiersza poleceń, które pomaga użytkownikom wykonywać zadania w terminalu poprzez tłumaczenie zapytań w języku naturalnym na odpowiednie polecenia powłoki. Wykorzystuje Google Gemini API do generowania sugestii poleceń oraz ich wyjaśnień.

## Główne Funkcjonalności

*   **Interfejs w języku naturalnym:** Zadawaj pytania tak, jakbyś rozmawiał z ekspertem od Linuxa.
*   **Automatyczna generacja poleceń:** Asystent generuje polecenia terminalowe na podstawie Twojego opisu.
*   **Wykrywanie dystrybucji:** Stara się dostosować polecenia do wykrytej dystrybucji Linuxa (np. menedżera pakietów).
*   **Walidacja bezpieczeństwa:** Posiada wbudowany mechanizm identyfikujący potencjalnie niebezpieczne polecenia i wymagający potwierdzenia dla niektórych operacji.
*   **Wyjaśnienia poleceń:** Każde sugerowane polecenie jest opatrzone krótkim wyjaśnieniem jego działania.
*   **Tryb interaktywny i jednorazowy:** Używaj asystenta w sesji interaktywnej lub do szybkich, pojedynczych zapytań.
*   **Historia poleceń:** Zapamiętuje wykonane polecenia (funkcjonalność w `CommandExecutor`).
*   **Kolorowy interfejs:** Dla lepszej czytelności w terminalu.

## Technologie

*   **Język programowania:** Python 3
*   **Model AI:** Google Gemini API (specyficznie `gemini-1.5-flash` jako domyślny)
*   **Główne biblioteki:**
    *   `google-generativeai` (dla Gemini API)
    *   `colorama` (dla kolorowego outputu w konsoli)
    *   Standardowe moduły Python (`os`, `subprocess`, `logging`, `json`, `argparse`, `re`)

## Wymagania wstępne

Przed rozpoczęciem upewnij się, że masz zainstalowane następujące narzędzia:

*   Python 3.7 lub nowszy
*   `pip` (menedżer pakietów Python)
*   `git` (do sklonowania repozytorium)
*   **Klucz API Google Gemini:** Jest niezbędny do działania funkcjonalności generowania poleceń.

## Instalacja

1.  **Klonowanie repozytorium:**
    ```bash
    git clone https://github.com/hyconiek/linux_ai_terminal_assistant.git
    cd linux_ai_terminal_assistant
    ```

2.  **Tworzenie i aktywacja środowiska wirtualnego (zalecane):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *Dla systemu Windows aktywacja to: `venv\Scripts\activate`*

3.  **Instalacja zależności:**
    Upewnij się, że plik `requirements.txt` zawiera następujące linie (lub więcej, jeśli dodałeś inne zależności):
    ```
    colorama>=0.4.4
    google-generativeai>=0.5.0  # Lub najnowsza stabilna wersja
    # requests>=2.25.1         # Jeśli nadal używasz shellgpt_integration lub innych modułów tego wymagających
    # shell-gpt>=0.9.0         # Jeśli nadal używasz shellgpt_integration
    # configparser>=5.0.0      # Jeśli nadal używasz shellgpt_integration
    ```
    Następnie zainstaluj zależności:
    ```bash
    pip install -r requirements.txt
    ```
    *Jeśli `shellgpt_integration.py` nie jest  używany, możesz usunąć `requests`, `shell-gpt` i `configparser` z `requirements.txt`.*

## Konfiguracja Klucza API

Asystent wymaga klucza API Google Gemini do komunikacji z modelem generatywnym.

1.  **Uzyskaj klucz API:**
    Możesz uzyskać swój klucz API, postępując zgodnie z instrukcjami na stronie [Google AI Studio](https://aistudio.google.com/app/apikey).

2.  **Ustaw zmienną środowiskową:**
    Najbezpieczniejszym sposobem skonfigurowania klucza API jest ustawienie go jako zmiennej środowiskowej. W terminalu, w którym będziesz uruchamiał skrypt, wykonaj:
    ```bash
    export GOOGLE_API_KEY="TWOJ_RZECZYWISTY_KLUCZ_API"
    ```
    Zastąp `TWOJ_RZECZYWISTY_KLUCZ_API` swoim kluczem.

    **Ważne:** To polecenie ustawi zmienną tylko dla bieżącej sesji terminala. Aby ustawić ją na stałe:
    *   Dodaj powyższą linię `export GOOGLE_API_KEY="..."` do pliku konfiguracyjnego Twojej powłoki (np. `~/.bashrc`, `~/.zshrc`, `~/.profile`).
    *   Następnie przeładuj konfigurację powłoki (np. `source ~/.bashrc`) lub otwórz nowe okno terminala.

    **NIGDY nie umieszczaj swojego klucza API bezpośrednio w kodzie źródłowym ani nie commituj go do publicznego repozytorium!**

## Uruchomienie Asystenta

Po zainstalowaniu zależności i skonfigurowaniu klucza API, możesz uruchomić asystenta.

*   **Tryb interaktywny:**
    ```bash
    python3 src/main.py
    ```
    W tym trybie możesz prowadzić rozmowę z asystentem, zadając kolejne pytania. Wpisz `help` po instrukcje lub `exit`/`quit` aby zakończyć.

*   **Jednorazowe zapytanie:**
    ```bash
    python3 src/main.py --query "Twoje pytanie w języku naturalnym"
    ```
    Przykład:
    ```bash
    python3 src/main.py --query "pokaż wszystkie pliki w bieżącym katalogu, włącznie z ukrytymi"
    ```

*   **Jednorazowe zapytanie z automatycznym wykonaniem (UŻYWAJ OSTROŻNIE!):**
    ```bash
    python3 src/main.py --query "Twoje pytanie" --execute
    ```
    Asystent spróbuje wykonać wygenerowane polecenie bez pytania o potwierdzenie (z wyjątkiem poleceń zidentyfikowanych jako wymagające potwierdzenia przez `SecurityValidator`).

*   **Jednorazowe zapytanie z wynikiem w formacie JSON:**
    ```bash
    python3 src/main.py --query "Twoje pytanie" --json
    ```
    Zwraca odpowiedź (sugerowane polecenie i wyjaśnienie lub błąd) w formacie JSON.

*   **Wyświetlenie pomocy:**
    ```bash
    python3 src/main.py --help
    ```

## Przykłady użycia

W trybie interaktywnym lub jako jednorazowe zapytanie:

*   `> pokaż procesy zużywające najwięcej pamięci`
*   `> znajdź wszystkie pliki PDF utworzone w ciągu ostatniego tygodnia w moim katalogu domowym`
*   `> jak zaktualizować listę pakietów na Ubuntu?`
*   `> utwórz archiwum tar.gz z katalogu 'moje_dane'`

## Struktura Projektu


.
├── src/
│ ├── main.py # Główny skrypt uruchomieniowy asystenta
│ └── modules/
│ ├── command_executor.py # Moduł do wykonywania poleceń i wykrywania dystrybucji
│ ├── gemini_integration.py # Moduł do integracji z Google Gemini API
│ └── shellgpt_integration.py # (Opcjonalny/Nieużywany obecnie) Moduł do integracji z ShellGPT
├── tests/
│ └── test_assistant.py # Testy jednostkowe
├── requirements.txt # Lista zależności Python
└── README.md # Ten plik```
(Pliki takie jak final_report.md, `validation_report.md` itd. zostały pominięte w tej strukturze, zakładając, że nie są częścią głównego kodu/dokumentacji dla użytkownika końcowego w repozytorium).
Walidacja Bezpieczeństwa

Moduł SecurityValidator w command_executor.py odpowiada za:

    Identyfikację potencjalnie niebezpiecznych wzorców poleceń (np. rm -rf /).

    Oznaczanie poleceń, które zazwyczaj wymagają podwyższonych uprawnień lub ostrożności (np. sudo, mkfs, dd).
    W przypadku wykrycia polecenia jako niebezpiecznego, jego wykonanie jest blokowane. Dla poleceń wymagających potwierdzenia, użytkownik jest o tym informowany w trybie interaktywnym (obecnie w kodzie jest to zaznaczone jako miejsce na implementację faktycznego zapytania o potwierdzenie, a domyślnie zakłada się udzielenie zgody dla celów demonstracyjnych, co warto rozbudować).

Przyszłe Ulepszenia

    Rozbudowa interakcji przy potwierdzaniu poleceń (faktyczne pytanie użytkownika).

    Testowanie i pełne wsparcie dla większej liczby dystrybucji Linuxa.

    Rozbudowa bazy wiedzy dla trybu offline (jeśli będzie rozwijany).

    Możliwość wyboru silnika AI (np. Gemini vs. lokalny model lub inne API).

    Bardziej zaawansowane zarządzanie historią i preferencjami użytkownika.

    Potencjalnie prosty interfejs graficzny (GUI).

Wkład w Projekt (Contributing)

Jeśli chcesz przyczynić się do rozwoju projektu linux_ai_terminal_assistant, zapraszam do zgłaszania błędów (Issues) oraz proponowania zmian (Pull Requests) na stronie repozytorium GitHub.

Przed wprowadzeniem większych zmian, proszę o utworzenie "Issue" w celu dyskusji.
Licencja

Ten projekt jest udostępniany na licencji MIT. Rozważ dodanie pliku LICENSE do swojego repozytorium z treścią licencji MIT.
