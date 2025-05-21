# Asystent AI dla Systemu Linux (GUI i CLI)

Wszechstronny asystent napędzany sztuczną inteligencją, który pomaga generować, rozumieć i wykonywać polecenia Linuksa przy użyciu języka naturalnego. Projekt dostarcza zarówno Graficzny Interfejs Użytkownika (GUI), jak i Interfejs Wiersza Poleceń (CLI), oba wykorzystujące Google Gemini.

[![Buy Me a Coffee](https://img.buymeacoffee.com/button-api/?text=Kup%20mi%20kawę&emoji=☕&slug=krzyzu.83&button_colour=FF5F5F&font_colour=ffffff&font_family=Arial&outline_colour=000000&coffee_colour=FFDD00)](https://www.buymeacoffee.com/krzyzu.83)

Projekt na GitHub: [hyconiek/linux_ai_terminal_assistant](https://github.com/hyconiek/linux_ai_terminal_assistant)

## 🎉 Najnowsze Wydanie: v1.0.2 - AppImage 🎉

Najłatwiejszym sposobem na wypróbowanie **Asystenta AI dla Linuksa (GUI)** jest pobranie naszego najnowszego wydania w formacie AppImage! Pliki AppImage są przenośne i powinny działać na większości nowoczesnych dystrybucji Linuksa bez potrzeby instalacji.

➡️ **[Pobierz `Linux-AI-Assistant-x86_64.AppImage` (140 MB) z sekcji Wydania (Releases)](https://github.com/hyconiek/linux_ai_terminal_assistant/releases/tag/1.0.2)** ⬅️
*(Zastąp `1.0.2` aktualnym tagiem Twojego najnowszego wydania, jeśli jest inny)*

### Jak Uruchomić AppImage:

1.  **Pobierz** plik `Linux-AI-Assistant-x86_64.AppImage` z powyższego linku.
2.  **Nadaj uprawnienia do wykonania**:
    Otwórz terminal, przejdź do katalogu, do którego pobrałeś plik, i uruchom:
    ```bash
    chmod +x Linux-AI-Assistant-x86_64.AppImage
    ```
3.  **Uruchom aplikację**:
    ```bash
    ./Linux-AI-Assistant-x86_64.AppImage
    ```
    *(Niektóre środowiska graficzne mogą również pozwolić na uruchomienie poprzez dwukrotne kliknięcie.)*
4.  **Klucz API**:
    *   Przy pierwszym uruchomieniu, jeśli klucz API Gemini nie jest skonfigurowany, zostaniesz poproszony o jego wprowadzenie.
    *   Możesz zarządzać swoim kluczem API i innymi ustawieniami poprzez "Ustawienia" (Plik > Ustawienia lub ikona koła zębatego).

### Uwagi dotyczące AppImage:
*   **Rozmiar**: Około 140 MB, ponieważ zawiera interpreter Pythona i niezbędne biblioteki. Planowane są przyszłe optymalizacje rozmiaru.
*   **Integracja z Pulpitem**: Dla lepszej integracji z pulpitem (np. ikona w menu aplikacji), rozważ użycie narzędzia "AppImageLauncher" lub ręczne utworzenie pliku `.desktop` wskazującego na ten plik AppImage.
*   **Pierwsze Uruchomienie**: Może być nieco wolniejsze, gdy AppImage konfiguruje swoje środowisko.
*   **Wymagania**: 64-bitowa dystrybucja Linuksa (zalecane glibc 2.35+), może być wymagany pakiet `fuse` (`sudo apt install fuse`).

## Korzystanie ze Spakowanej Aplikacji (Zalecane dla GUI)

Aby najłatwiej skorzystać z aplikacji GUI, pobierz najnowszy gotowy plik wykonywalny z sekcji [**Wydania (Releases)**](https://github.com/hyconiek/linux_ai_terminal_assistant/releases) tego repozytorium.

1.  Pobierz samodzielny plik wykonywalny dla Linuksa (np. `Linux-AI-Assistant-vX.Y.Z-linux-x86_64` lub podobny).
2.  Nadaj uprawnienia do wykonania (na Linuksie/macOS):
    ```bash
    chmod +x <pobrana_nazwa_pliku_wykonywalnego>
    ```
3.  Uruchom aplikację:
    ```bash
    ./<pobrana_nazwa_pliku_wykonywalnego>
    ```
4.  **Klucz API**: Przy pierwszym uruchomieniu lub poprzez "Ustawienia", zostaniesz poproszony o klucz API Google Gemini.

## Funkcje (GUI i Logika Rdzenia)

- **Intuicyjny interfejs GUI/CLI**: Wybierz preferowany sposób interakcji.
- **Generowanie poleceń w języku naturalnym**: Proś o polecenia w prostym języku polskim (napędzane przez Google Gemini).
- **Napędzany przez AI**: Wykorzystuje Google Gemini do sugestii poleceń i ich wyjaśnień.
- **Bezpośrednie wykonywanie poleceń**: (GUI) Uruchamiaj wygenerowane polecenia bezpośrednio z interfejsu.
- **Kopiowanie do schowka**: (GUI) Łatwo kopiuj polecenia do użycia w innym miejscu.
- **Zarządzanie kluczem API**: (GUI) Bezpiecznie przechowuj i zarządzaj swoim kluczem API Google Gemini.
- **Personalizowane motywy**: (GUI) Wsparcie dla trybu Ciemnego (domyślny) i Jasnego.
- **Przełącznik szczegółowości logów**: (GUI) Kontroluj ilość informacji systemowych/debugowania wyświetlanych.
- **Potencjał wieloplatformowy**: Zbudowany przy użyciu Pythona i PyQt5.

## Jak Zdobyć Klucz API Gemini

1.  Odwiedź [Google AI Studio](https://aistudio.google.com/).
2.  Zaloguj się na swoje konto Google.
3.  Przejdź do "Klucze API" (API keys) w panelu bocznym.
4.  Kliknij "Utwórz klucz API" (Create API key) i skopiuj wygenerowany klucz.

## Korzystanie z Interfejsu Wiersza Poleceń (CLI)

Główna logika asystenta jest również dostępna jako narzędzie CLI, idealne do skryptów lub szybkiego użycia w terminalu. Jest to backend używany przez GUI.

### Wymagania wstępne (CLI)

- Python 3.7+ (Python 3.12 zalecany do budowania GUI).
- Aktywny klucz API Google Gemini.

### Konfiguracja (CLI)

1.  **Sklonuj repozytorium:**
    ```bash
    git clone https://github.com/hyconiek/linux_ai_terminal_assistant.git
    cd linux_ai_terminal_assistant
    ```

2.  **Utwórz i aktywuj środowisko wirtualne (zalecane):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # W systemie Windows: venv\Scripts\activate
    ```

3.  **Zainstaluj zależności:**
    Upewnij się, że masz plik `requirements.txt` w głównym katalogu. Dla backendu CLI powinien on zawierać przede wszystkim:
    ```txt
    google-generativeai>=0.5.0
    # colorama>=0.4.4 # Jeśli backend_cli.py używa go do kolorowego outputu
    # argparse # Biblioteka standardowa, ale warto wspomnieć przy intensywnym użyciu
    ```
    Następnie zainstaluj:
    ```bash
    pip install -r requirements.txt
    ```
    (Do budowania/uruchamiania GUI ze źródeł, `PyQt5>=5.15.0` również byłoby potrzebne w `requirements.txt`).

4.  **Ustaw Klucz API (CLI):**
    Backend CLI (`src/backend_cli.py`) oczekuje zmiennej środowiskowej `GOOGLE_API_KEY`.
    ```bash
    export GOOGLE_API_KEY="TWÓJ_KLUCZ_API_GEMINI"
    ```
    Aby ustawić na stałe, dodaj tę linię do pliku konfiguracyjnego swojej powłoki (np. `.bashrc`, `.zshrc`).

### Przykłady Użycia CLI

*(Te polecenia zakładają, że znajdujesz się w głównym katalogu sklonowanego repozytorium)*

```bash
# Uruchom skrypt backendu CLI bezpośrednio (upewnij się, że jest wykonywalny lub użyj python3)
# Głównie do testowania backendu lub jeśli preferujesz interakcję CLI.
python3 src/backend_cli.py --query "pokaż użycie dysku w formacie czytelnym dla człowieka" --json

python3 src/backend_cli.py --query "znajdź wszystkie pliki pdf w katalogu domowym" --json
(Uwaga: Skrypt backend_cli.py jest zaprojektowany do wywoływania przez GUI lub do generowania specyficznych poleceń. Może nie posiadać samodzielnego trybu interaktywnego, chyba że go dodałeś.)
Budowanie Aplikacji GUI ze Źródeł

Jeśli chcesz samodzielnie zbudować aplikację GUI:
Wymagania wstępne (Budowanie GUI)

    Wszystkie wymagania dla CLI.

    PyQt5: PyQt5>=5.15.0 (powinno być w Twoim requirements.txt).

    PyInstaller: pip install pyinstaller

Kroki Budowania

    Upewnij się, że projekt jest skonfigurowany jak opisano w "Konfiguracja (CLI)" i wszystkie zależności (w tym PyQt5 i pyinstaller) są zainstalowane w Twoim środowisku wirtualnym.

    Przejdź do głównego katalogu projektu (linux_ai_terminal_assistant).

    Uruchom PyInstallera (upewnij się, że skrypt GUI nazywa się linux_ai_assistant_gui.py, skrypt backendu src/backend_cli.py, a plik app_icon.png jest w głównym katalogu). Użyj następującego polecenia:

      
pyinstaller --name "Linux AI Assistant" \
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
            --hidden-import="pkg_resources.py2_warn" \
            --hidden-import="argparse" \
            --hidden-import="backend_cli" \
            linux_ai_assistant_gui.py

Plik wykonywalny znajdzie się w katalogu dist (np. dist/Linux AI Assistant).

Licencja

Projekt stworzony przez Krzysztofa Żuchowskiego.
Copyright © 2025 Krzysztof Żuchowski. Wszelkie prawa zastrzeżone.

Na licencji MIT License.

Stworzone z ❤️ i Pythonem.
