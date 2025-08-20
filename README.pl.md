# Asystent AI dla Systemu Linux (GUI i CLI)

Wszechstronny asystent napędzany sztuczną inteligencją, który pomaga generować, rozumieć i wykonywać polecenia Linuksa przy użyciu języka naturalnego. Projekt dostarcza zarówno Graficzny Interfejs Użytkownika (GUI), jak i Interfejs Wiersza Poleceń (CLI), oba wykorzystujące Google Gemini.

[![Kup mi kawę](https://img.buymeacoffee.com/button-api/?text=Kup%20mi%20kawę&emoji=☕&slug=krzyzu.83&button_colour=FF5F5F&font_colour=ffffff&font_family=Arial&outline_colour=000000&coffee_colour=FFDD00)](https://www.buymeacoffee.com/krzyzu.83)

Projekt na GitHub: [hyconiek/linux_ai_terminal_assistant](https://github.com/hyconiek/linux_ai_terminal_assistant)

## 🎉 Najnowsze Wydanie: v1.1 - Tryb Offline, Umiędzynarodowienie i Więcej! 🎉

![alt text](./screenshot.png)

Najłatwiejszym sposobem na wypróbowanie Asystenta AI dla Linuksa (GUI) jest pobranie naszego najnowszego wydania w formacie AppImage lub jako samodzielny plik wykonywalny! Pliki AppImage są przenośne i powinny działać na większości nowoczesnych dystrybucji Linuksa bez potrzeby instalacji.

➡️ **[Pobierz najnowsze wydanie v1.1 z GitHub](https://github.com/hyconiek/linux_ai_terminal_assistant/releases/latest)** ⬅️

### Co Nowego w v1.1:

 *   **Pełny Tryb Offline:** Asystent wykrywa problemy z internetem i przełącza się w funkcjonalny tryb offline, wykorzystując obszerną, wbudowaną pamięć podręczną do wyjaśniania poleceń.
 *   **Automatyczne Dostosowanie Języka:** AI jest automatycznie instruowane, aby odpowiadać w języku ojczystym Twojego systemu (obsługuje m.in. polski, czeski, niemiecki, hiszpański), co czyni interakcje bardziej naturalnymi.
 *   **Bezpieczna Obsługa Hasła Sudo:** GUI udostępnia teraz bezpieczne okno dialogowe do wprowadzania hasła `sudo` dla poleceń wymagających uprawnień administratora.
 *   **Interaktywne Doprecyzowanie przez AI:** Jeśli zapytanie jest niejednoznaczne, aplikacja wyświetli okno z pytaniami doprecyzowującymi od AI, aby pomóc Ci udoskonalić prośbę.
 *   **Zaawansowane Ustawienia Optymalizacji AI:** Nowe menu pozwala włączać/wyłączać analizę w czasie rzeczywistym i buforowanie AI w celu zarządzania kosztami API, a nawet importować/eksportować pamięć podręczną.
 *   **Poprawka Integracji z Wayland:** Usunięto błąd uniemożliwiający prawidłowe grupowanie ikony aplikacji na nowoczesnych pulpitach Wayland.

### Jak Uruchomić:
#### AppImage:

1.  **Pobierz** plik `Linux-AI-Assistant-x86_64.AppImage`.
2.  **Nadaj uprawnienia do wykonania**: `chmod +x Linux-AI-Assistant-x86_64.AppImage`
3.  **Uruchom**: `./Linux-AI-Assistant-x86_64.AppImage`

#### Samodzielny Plik Wykonywalny (PyInstaller onefile):

1.  **Pobierz** plik wykonywalny `Linux-AI-Assistant-onefile`.
2.  **Nadaj uprawnienia do wykonania**: `chmod +x Linux-AI-Assistant-onefile`
3.  **Uruchom**: `./Linux-AI-Assistant-onefile`

### Pierwsza Konfiguracja:

*   **Klucz API**: Przy pierwszym uruchomieniu zostaniesz poproszony o wprowadzenie klucza API Gemini. Klucz możesz uzyskać z [Google AI Studio](https://aistudio.google.com/).
*   Możesz zarządzać kluczem API i innymi ustawieniami w "Ustawieniach" (Plik > Ustawienia lub ikona koła zębatego).

### Uwagi dotyczące AppImage:

*   **Integracja z Pulpitem**: Dla ikon w menu i łatwego dostępu z wiersza poleceń, zaleca się użycie dołączonego skryptu `install.sh` (wymaga sudo).
*   **Wymagania**: 64-bitowa dystrybucja Linuksa (zalecane glibc 2.35+), może być wymagany pakiet `fuse` (`sudo apt install fuse`).

## Główne Funkcje

*   **Intuicyjny interfejs GUI/CLI**: Wybierz preferowany sposób interakcji.
*   **Język Naturalny na Polecenia**: Proś o polecenia w języku naturalnym (obsługiwane przez Google Gemini).
*   **Wielojęzyczne Odpowiedzi AI**: AI dostosowuje się do języka Twojego systemu.
*   **Tryb Offline z Wypełnioną Pamięcią Podręczną**: Główne funkcje pozostają dostępne bez internetu.
*   **Bezpieczna Obsługa Hasła Sudo**: (GUI) Bezpieczne okno dialogowe dla haseł administratora.
*   **Dialogi Doprecyzowujące AI**: (GUI) Aplikacja dopytuje o szczegóły, gdy Twoje żądanie jest niejasne.
*   **Bezpośrednie Wykonywanie Poleceń**: (GUI) Uruchamiaj polecenia bezpośrednio lub w zewnętrznym terminalu.
*   **Zaawansowane Ustawienia Optymalizacji AI**: (GUI) Kontroluj użycie API za pomocą przełączników analizy i buforowania.
*   **Zarządzanie Kluczem API**: (GUI) Bezpiecznie przechowuj swój klucz API Google Gemini.
*   **Personalizowane Motywy**: (GUI) Wsparcie dla trybu Ciemnego (domyślny) i Jasnego.
*   **Historia Poleceń**: (GUI) Nawiguj po historii wprowadzania za pomocą strzałek.

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
    source venv/bin/activate
    ```

3.  **Zainstaluj zależności:**
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
# Tryb interaktywny do generowania poleceń
python3 src/backend_cli.py

# Dla konkretnego zapytania (wyjście JSON używane przez GUI)
python3 src/backend_cli.py --query "czy są tu jakieś pliki tekstowe?" --json --working-dir "/ścieżka/do/twojego/katalogu"

  

Budowanie Aplikacji GUI ze Źródeł

Jeśli chcesz samodzielnie zbudować aplikację GUI:
Wymagania Wstępne (Budowanie GUI)

    Wszystkie wymagania dla CLI.

    PyQt5: PyQt5>=5.15.0

    PyInstaller: pip install pyinstaller

Kroki Budowania

    Upewnij się, że projekt jest skonfigurowany, a zależności są zainstalowane.

    Przejdź do głównego katalogu projektu.

    Uruchom PyInstallera dla pliku wykonywalnego typu one-file:
    code Bash

    IGNORE_WHEN_COPYING_START
    IGNORE_WHEN_COPYING_END

        
    pyinstaller --name "Linux-AI-Assistant-onefile" \
                --onefile \
                --windowed \
                --add-data "laia_icon.png:." \
                --add-data "src:src" \
                # ... dodaj inne ukryte importy w razie potrzeby
                linux_ai_assistant_gui.py

      

    Plik wykonywalny znajdzie się w katalogu dist.

Licencja

Projekt stworzony przez Krzysztofa Żuchowskiego.
Copyright © 2025 Krzysztof Żuchowski. Wszelkie prawa zastrzeżone.

Na licencji MIT License.

Stworzone z ❤️ i Pythonem.
