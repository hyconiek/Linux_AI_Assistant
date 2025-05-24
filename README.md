# Linux AI Assistant (GUI & CLI)

A versatile AI-powered assistant to help you generate, understand, and execute Linux commands using natural language. This project provides both a Graphical User Interface (GUI) and a Command-Line Interface (CLI), both utilizing Google Gemini.

[![Buy Me a Coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=☕&slug=krzyzu.83&button_colour=FF5F5F&font_colour=ffffff&font_family=Arial&outline_colour=000000&coffee_colour=FFDD00)](https://www.buymeacoffee.com/krzyzu.83)

Find the project on GitHub: [hyconiek/linux_ai_terminal_assistant](https://github.com/hyconiek/linux_ai_terminal_assistant)

## 🎉 Latest Release: v1.0.5 - Enhanced Context and Interaction! 🎉
![screenshot](./screenshot.png)
The easiest way to try the **Linux AI Assistant GUI** is by downloading our latest AppImage or standalone executable release! AppImages are portable and should run on most modern Linux distributions without installation.

➡️ **[Download `Linux-AI-Assistant-x86_64.AppImage` or the `Linux-AI-Assistant-onefile` executable from Releases (v1.0.4)](https://github.com/hyconiek/linux_ai_terminal_assistant/releases/latest)** ⬅️

### What's New in v1.0.5:
 *   **Improved Contextual Follow-up:** After discussing files in your CWD, you can refer to them more naturally in subsequent commands (e.g., "rename that snap file").
 *   **Direct Execution of Basic Commands:** Common Linux commands (e.g., `ls`, `cd`, `pwd`) typed into the GUI are executed directly. The GUI then requests an AI-generated explanation for the executed command.
 *   **Command History in GUI:** The input field in the GUI now supports command history navigation using the Up and Down arrow keys.
-*   **Dynamic Prompt in Terminal Widget:** The terminal widget in the GUI now displays the current working directory in its prompt, similar to a standard terminal (e.g., `[/home/user/docs]> `). The input field prompt remains a static `> `.
+*   **Dynamic Prompt in Terminal Widget:** The main terminal output area in the GUI now displays the current working directory in its prompt for user inputs, similar to a standard terminal (e.g., `[/home/user/docs]> your_command`). The actual input field prompt remains a static `> `.
+*   **Stable GUI Layout:** The layout of command/explanation areas has been reordered for better stability, with the input field always at the bottom, followed by the AI output/explanation area, and then the (conditionally visible) panel for generated/executed commands and their action buttons. The command display itself is now single-line.
 *   **Customizable "Force AI" Commands:** Added a setting to specify commands (e.g., `rm`) that should always be sent to the AI for generation/confirmation, even if they match basic command patterns.

### How to Run:

#### AppImage:
1.  **Download** the `Linux-AI-Assistant-x86_64.AppImage` file.
2.  **Make it executable**: `chmod +x Linux-AI-Assistant-x86_64.AppImage`
3.  **Run**: `./Linux-AI-Assistant-x86_64.AppImage`
    *(Some desktop environments might also allow you to run it by double-clicking.)*

#### Standalone Executable (PyInstaller onefile):
1.  **Download** the `Linux-AI-Assistant-onefile` (or similar named) executable.
2.  **Make it executable**: `chmod +x Linux-AI-Assistant-onefile`
3.  **Run**: `./Linux-AI-Assistant-onefile`

### First Time Setup:
*   **API Key**: On the first launch, if a Gemini API key is not configured, you will be prompted to enter one. You can get a key from [Google AI Studio](https://aistudio.google.com/).
*   Manage your API key and other settings via "Settings" (File > Settings or the gear icon).

### AppImage Notes:
*   **Size**: AppImage bundles Python and necessary libraries. Size may vary per release.
*   **Desktop Integration**: For menu icons and easy command-line access, it's recommended to use the provided `install.sh` script (requires sudo). Alternatively, consider "AppImageLauncher" or manually creating a `.desktop` file.
*   **Requirements**: 64-bit Linux (glibc 2.35+ recommended), `fuse` package might be needed for AppImage (`sudo apt install fuse`).


## Core Features

- **Intuitive GUI/CLI**: Choose your preferred way to interact.
- **Natural Language to Command**: Ask for commands in plain English (powered by Google Gemini).
- **AI-Powered**: Utilizes Google Gemini for command suggestions, explanations, and CWD content analysis.
- **Direct Command Execution**: (GUI) Run generated commands directly or in an external terminal for interactive ones. Basic commands are executed immediately with post-execution AI explanation.
- **Copy to Clipboard**: (GUI) Easily copy commands or AI's textual answers.
- **API Key Management**: (GUI) Securely store and manage your Google Gemini API key.
- **Customizable Themes**: (GUI) Supports Dark (default) and Light modes.
- **Verbose Logging Toggle**: (GUI) Control the amount of system/debug information displayed.
- **Command History**: (GUI) Navigate input history with arrow keys.
- **Dynamic Prompt in Terminal Widget**: (GUI) Terminal widget prompt shows current working directory.
- **Customizable "Force AI" Commands**: (GUI) Define commands that always require AI processing.
- **Cross-Platform Potential**: Built with Python and PyQt5.

## How to Get a Gemini API Key

1.  Visit [Google AI Studio](https://aistudio.google.com/).
2.  Sign in with your Google account.
3.  Navigate to "API keys" in the left sidebar.
4.  Click "Create API key" and copy the generated key.

## Using the Command-Line Interface (CLI)

The core logic is also available as a CLI tool (`src/backend_cli.py`), used by the GUI.

### Prerequisites (CLI)

- Python 3.7+ (Python 3.11+ recommended).
- An active Google Gemini API Key.

### Setup (CLI)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/hyconiek/linux_ai_terminal_assistant.git
    cd linux_ai_terminal_assistant
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    (Ensure `requirements.txt` is up-to-date with `google-generativeai` and `PyQt5` if running GUI from source)
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set API Key (CLI):**
    The CLI backend expects the `GOOGLE_API_KEY` environment variable.
    ```bash
    export GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
    ```
    For permanent setting, add this to your shell's configuration file (e.g., `.bashrc`, `.zshrc`).

### CLI Usage Examples

*(Run from the root directory of the cloned repository)*

```bash
# Backend CLI for command generation/textual answers (interactive mode)
python3 src/backend_cli.py

# For specific query (JSON output used by GUI)
python3 src/backend_cli.py --query "are there any text files here?" --json --working-dir "/path/to/your/directory"

    

IGNORE_WHEN_COPYING_START
Use code with caution. Markdown
IGNORE_WHEN_COPYING_END
Building the GUI Application from Source

If you want to build the GUI application yourself:
Prerequisites (Building GUI)

    All prerequisites for CLI.

    PyQt5: PyQt5>=5.15.0

    PyInstaller: pip install pyinstaller

Build Steps

    Ensure your project is set up and dependencies are installed in your virtual environment.

    Navigate to the project's root directory.

    Run PyInstaller. For a one-file executable:

          
    pyinstaller --name "Linux-AI-Assistant-onefile" \
                --onefile \
                --windowed \
                --add-data "laia_icon.png:." \
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

    The executable will be in the dist folder (e.g., dist/Linux-AI-Assistant-onefile).
    (For AppImage creation, a more complex process involving linuxdeployqt is typically used, often within a Docker container or a Colab notebook configured for AppImage building.)

License

This project is created by Krzysztof Żuchowski.
Copyright © 2025 Krzysztof Żuchowski. All rights reserved.

Licensed under the MIT License.

Made with ❤️ and Python.

# Asystent AI dla Systemu Linux (GUI i CLI)

Wszechstronny asystent napędzany sztuczną inteligencją, który pomaga generować, rozumieć i wykonywać polecenia Linuksa przy użyciu języka naturalnego. Projekt dostarcza zarówno Graficzny Interfejs Użytkownika (GUI), jak i Interfejs Wiersza Poleceń (CLI), oba wykorzystujące Google Gemini.

[![Kup mi kawę](https://img.buymeacoffee.com/button-api/?text=Kup%20mi%20kawę&emoji=☕&slug=krzyzu.83&button_colour=FF5F5F&font_colour=ffffff&font_family=Arial&outline_colour=000000&coffee_colour=FFDD00)](https://www.buymeacoffee.com/krzyzu.83)

Projekt na GitHub: [hyconiek/linux_ai_terminal_assistant](https://github.com/hyconiek/linux_ai_terminal_assistant)
## 🎉 Najnowsze Wydanie: v1.0.5 - Rozszerzony Kontekst i Interakcja! 🎉

![alt text](./screenshot.png)


Najłatwiejszym sposobem na wypróbowanie Asystenta AI dla Linuksa (GUI) jest pobranie naszego najnowszego wydania w formacie AppImage lub jako samodzielny plik wykonywalny! Pliki AppImage są przenośne i powinny działać na większości nowoczesnych dystrybucji Linuksa bez potrzeby instalacji.

➡️ **[Pobierz `Linux-AI-Assistant-x86_64.AppImage` lub plik wykonywalny `Linux-AI-Assistant-onefile` z sekcji Wydań (v1.0.4)](https://github.com/hyconiek/linux_ai_terminal_assistant/releases/latest)** ⬅️
### Co Nowego w v1.0.5:

 *   **Ulepszone Kontekstowe Kontynuacje:** Po omówieniu plików w CWD, możesz odnosić się do nich bardziej naturalnie w kolejnych poleceniach (np. "zmień nazwę tego pliku snap").
 *   **Bezpośrednie Wykonywanie Podstawowych Poleceń:** Powszechne polecenia Linuksa (np. `ls`, `cd`, `pwd`) wpisane w GUI są wykonywane bezpośrednio. Następnie GUI żąda od AI wyjaśnienia wykonanego polecenia.
 *   **Historia Poleceń w GUI:** Pole wprowadzania w GUI obsługuje teraz nawigację po historii poleceń za pomocą strzałek Góra/Dół.
-*   **Dynamiczny Znak Zachęty w Widżecie Terminala:** Widżet terminala w GUI wyświetla teraz bieżący katalog roboczy w swoim znaku zachęty, podobnie jak standardowy terminal (np. `[/home/user/docs]> `). Znak zachęty pola wprowadzania pozostaje statyczny `> `.
+*   **Dynamiczny Znak Zachęty w Widżecie Terminala:** Główny obszar wyjściowy terminala w GUI wyświetla teraz bieżący katalog roboczy w swoim znaku zachęty dla wprowadzanych przez użytkownika poleceń, podobnie jak standardowy terminal (np. `[/home/user/docs]> twoje_polecenie`). Rzeczywisty znak zachęty pola wprowadzania pozostaje statyczny `> `.
+*   **Stabilny Układ GUI:** Układ obszarów poleceń/wyjaśnień został przeorganizowany dla lepszej stabilności, z polem wprowadzania zawsze na dole, następnie obszarem wyjścia/wyjaśnień AI, a potem (warunkowo widocznym) panelem dla wygenerowanych/wykonanych poleceń i ich przycisków akcji. Sam wyświetlacz polecenia jest teraz jednowierszowy.
 *   **Konfigurowalne Polecenia "Wymuś AI":** Dodano ustawienie pozwalające określić polecenia (np. `rm`), które zawsze powinny być wysyłane do AI w celu wygenerowania/potwierdzenia, nawet jeśli pasują do wzorców poleceń podstawowych.

### Jak Uruchomić:
#### AppImage:

1.  **Pobierz** plik `Linux-AI-Assistant-x86_64.AppImage`.
2.  **Nadaj uprawnienia do wykonania**: `chmod +x Linux-AI-Assistant-x86_64.AppImage`
3.  **Uruchom**: `./Linux-AI-Assistant-x86_64.AppImage`
    *(Niektóre środowiska graficzne mogą również pozwolić na uruchomienie poprzez dwukrotne kliknięcie.)*

#### Samodzielny Plik Wykonywalny (PyInstaller onefile):

1.  **Pobierz** plik wykonywalny `Linux-AI-Assistant-onefile` (lub o podobnej nazwie).
2.  **Nadaj uprawnienia do wykonania**: `chmod +x Linux-AI-Assistant-onefile`
3.  **Uruchom**: `./Linux-AI-Assistant-onefile`

### Pierwsza Konfiguracja:

*   **Klucz API**: Przy pierwszym uruchomieniu, jeśli klucz API Gemini nie jest skonfigurowany, zostaniesz poproszony o jego wprowadzenie. Klucz możesz uzyskać z [Google AI Studio](https://aistudio.google.com/).
*   Możesz zarządzać swoim kluczem API i innymi ustawieniami poprzez "Ustawienia" (Plik > Ustawienia lub ikona koła zębatego).

### Uwagi dotyczące AppImage:
*   **Rozmiar**: AppImage zawiera Pythona i niezbędne biblioteki. Rozmiar może się różnić w zależności od wydania.
*   **Integracja z Pulpitem**: Dla ikon w menu i łatwego dostępu z wiersza poleceń, zaleca się użycie dołączonego skryptu `install.sh` (wymaga sudo). Alternatywnie, rozważ użycie "AppImageLauncher" lub ręczne utworzenie pliku `.desktop`.
*   **Wymagania**: 64-bitowa dystrybucja Linuksa (zalecane glibc 2.35+), może być wymagany pakiet `fuse` dla AppImage (`sudo apt install fuse`).

## Główne Funkcje

*   **Intuicyjny interfejs GUI/CLI**: Wybierz preferowany sposób interakcji.
*   **Język Naturalny na Polecenia**: Proś o polecenia w języku naturalnym (obsługiwane przez Google Gemini).
*   **Napędzany przez AI**: Wykorzystuje Google Gemini do sugestii poleceń, wyjaśnień i analizy zawartości CWD.
*   **Bezpośrednie Wykonywanie Poleceń**: (GUI) Uruchamiaj wygenerowane polecenia bezpośrednio lub w zewnętrznym terminalu dla poleceń interaktywnych. Podstawowe polecenia są wykonywane natychmiast z wyjaśnieniem AI po wykonaniu.
*   **Kopiowanie do Schowka**: (GUI) Łatwo kopiuj polecenia lub tekstowe odpowiedzi AI.
*   **Zarządzanie Kluczem API**: (GUI) Bezpiecznie przechowuj i zarządzaj swoim kluczem API Google Gemini.
*   **Personalizowane Motywy**: (GUI) Wsparcie dla trybu Ciemnego (domyślny) i Jasnego.
*   **Przełącznik Szczegółowości Logów**: (GUI) Kontroluj ilość informacji systemowych/debugowania.
*   **Historia Poleceń**: (GUI) Nawiguj po historii wprowadzania za pomocą strzałek.
*   **Dynamiczny Znak Zachęty w Widżecie Terminala**: (GUI) Znak zachęty widżetu terminala pokazuje bieżący katalog roboczy.
*   **Konfigurowalne Polecenia "Wymuś AI"**: (GUI) Zdefiniuj polecenia, które zawsze wymagają przetwarzania przez AI.
*   **Potencjał Wieloplatformowy**: Zbudowany przy użyciu Pythona i PyQt5.


## Jak Zdobyć Klucz API Gemini

1.  Odwiedź [Google AI Studio](https://aistudio.google.com/).
2.  Zaloguj się na swoje konto Google.
3.  Przejdź do "Klucze API" (API keys) w panelu bocznym.
4.  Kliknij "Utwórz klucz API" (Create API key) i skopiuj wygenerowany klucz.

## Korzystanie z Interfejsu Wiersza Poleceń (CLI)

Główna logika jest również dostępna jako narzędzie CLI (`src/backend_cli.py`), używane przez GUI.
### Wymagania Wstępne (CLI)

- Python 3.7+ (zalecany Python 3.11+).
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
    (Upewnij się, że `requirements.txt` jest aktualny i zawiera `google-generativeai` oraz `PyQt5` jeśli uruchamiasz GUI ze źródeł)
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ustaw Klucz API (CLI):**
    Backend CLI oczekuje zmiennej środowiskowej `GOOGLE_API_KEY`.
    ```bash
    export GOOGLE_API_KEY="TWÓJ_KLUCZ_API_GEMINI"
    ```
    Aby ustawić na stałe, dodaj tę linię do pliku konfiguracyjnego swojej powłoki (np. `.bashrc`, `.zshrc`).

### Przykłady Użycia CLI

*(Uruchom z głównego katalogu sklonowanego repozytorium)*

```bash
# Backend CLI do generowania poleceń/odpowiedzi tekstowych (tryb interaktywny)
python3 src/backend_cli.py

# Dla konkretnego zapytania (wyjście JSON używane przez GUI)
python3 src/backend_cli.py --query "czy są tu jakieś pliki tekstowe?" --json --working-dir "/ścieżka/do/twojego/katalogu"

    

IGNORE_WHEN_COPYING_START
Use code with caution. Markdown
IGNORE_WHEN_COPYING_END
## Budowanie Aplikacji GUI ze Źródeł

Jeśli chcesz samodzielnie zbudować aplikację GUI:
### Wymagania Wstępne (Budowanie GUI)

- Wszystkie wymagania dla CLI.
- PyQt5: `PyQt5>=5.15.0`
- PyInstaller: `pip install pyinstaller`

### Kroki Budowania

1.  Upewnij się, że projekt jest skonfigurowany, a zależności są zainstalowane w środowisku wirtualnym.
2.  Przejdź do głównego katalogu projektu.
3.  Uruchom PyInstallera. Dla pliku wykonywalnego typu one-file:

    ```bash
    pyinstaller --name "Linux-AI-Assistant-onefile" \
                --onefile \
                --windowed \
                --add-data "laia_icon.png:." \
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
    ```

    Plik wykonywalny znajdzie się w katalogu `dist` (np. `dist/Linux-AI-Assistant-onefile`).
    (Tworzenie AppImage jest bardziej złożonym procesem, często wykorzystującym `linuxdeployqt`, realizowanym np. w kontenerze Docker lub specjalnie skonfigurowanym notatniku Colab.)

## Licencja

Projekt stworzony przez Krzysztofa Żuchowskiego.
Copyright © 2025 Krzysztof Żuchowski. Wszelkie prawa zastrzeżone.

Na licencji MIT License.

Stworzone z ❤️ i Pythonem.

