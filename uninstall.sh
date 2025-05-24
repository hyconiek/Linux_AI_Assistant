#!/bin/bash

# Skrypt deinstalacyjny dla Linux AI Assistant

# --- Konfiguracja (musi być DOKŁADNIE taka sama jak w install.sh) ---
APP_NAME_DISPLAY="Linux AI Assistant"
INSTALL_DIR_BASE="/opt"
APP_INSTALL_DIR="$INSTALL_DIR_BASE/$APP_NAME_DISPLAY"
BIN_NAME="laia"

# Nazwa pliku ikony, jaka została zapisana w systemie przez install.sh
ICON_SYSTEM_FILENAME="laia_icon.png"
# Ścieżka, gdzie ikona została zainstalowana (powinna pasować do install.sh)
ICON_INSTALL_TARGET_DIR="/usr/share/pixmaps" # Zgodnie z install.sh

DESKTOP_FILE_NAME="laia.desktop"

# Sprawdzenie uprawnień roota
if [ "$(id -u)" -ne 0 ]; then
  echo "Ten skrypt musi być uruchomiony z uprawnieniami roota (sudo)."
  exit 1
fi

echo "Rozpoczynanie deinstalacji $APP_NAME_DISPLAY..."

# --- Krok 1: Usuwanie pliku .desktop ---
DESKTOP_FILE_PATH="/usr/share/applications/$DESKTOP_FILE_NAME"
echo "Usuwanie pliku .desktop: $DESKTOP_FILE_PATH..."
if [ -f "$DESKTOP_FILE_PATH" ]; then
    rm "$DESKTOP_FILE_PATH" && echo "Plik .desktop usunięty." || echo "Błąd: Nie można usunąć pliku .desktop $DESKTOP_FILE_PATH."
else
    echo "Plik .desktop ($DESKTOP_FILE_PATH) nie znaleziony."
fi

# --- Krok 2: Usuwanie dowiązania symbolicznego ---
SYMBLINK_PATH="/usr/local/bin/$BIN_NAME"
echo "Usuwanie dowiązania symbolicznego: $SYMBLINK_PATH..."
if [ -L "$SYMBLINK_PATH" ]; then
    rm "$SYMBLINK_PATH" && echo "Dowiązanie symboliczne usunięte." || echo "Błąd: Nie można usunąć dowiązania symbolicznego $SYMBLINK_PATH."
elif [ -f "$SYMBLINK_PATH" ]; then
     # Na wypadek, gdyby istniał zwykły plik zamiast dowiązania
     rm "$SYMBLINK_PATH" && echo "Plik $SYMBLINK_PATH (nie dowiązanie) usunięty." || echo "Błąd: Nie można usunąć pliku $SYMBLINK_PATH."
else
    echo "Dowiązanie symboliczne/plik ($SYMBLINK_PATH) nie znalezione."
fi

# --- Krok 3: Usuwanie ikony ---
ICON_ACTUAL_PATH="$ICON_INSTALL_TARGET_DIR/$ICON_SYSTEM_FILENAME"
echo "Usuwanie ikony aplikacji: $ICON_ACTUAL_PATH..."
if [ -f "$ICON_ACTUAL_PATH" ]; then
    rm "$ICON_ACTUAL_PATH" && echo "Ikona usunięta." || echo "Błąd: Nie można usunąć ikony $ICON_ACTUAL_PATH."
else
    echo "Ikona ($ICON_ACTUAL_PATH) nie znaleziona."
fi

# --- Krok 4: Usuwanie plików aplikacji i katalogu ---
echo "Usuwanie katalogu instalacyjnego: $APP_INSTALL_DIR..."
if [ -d "$APP_INSTALL_DIR" ]; then
    rm -rf "$APP_INSTALL_DIR" && echo "Katalog instalacyjny i jego zawartość usunięte." || echo "Błąd: Nie można usunąć katalogu $APP_INSTALL_DIR i jego zawartości."
else
    echo "Katalog instalacyjny ($APP_INSTALL_DIR) nie znaleziony."
fi

# --- Krok 5: Aktualizacja bazy danych menu i cache ikon ---
echo "Aktualizowanie bazy danych menu i cache ikon..."
DB_UPDATED=false
ICON_CACHE_UPDATED=false

if command -v update-desktop-database &> /dev/null; then
    if [ -d "/usr/share/applications" ]; then
        update-desktop-database -q /usr/share/applications/
        echo "Baza danych pulpitu zaktualizowana."
        DB_UPDATED=true
    else
        echo "Ostrzeżenie: Katalog /usr/share/applications nie istnieje. Pomijanie update-desktop-database."
    fi
else
    echo "Ostrzeżenie: Polecenie 'update-desktop-database' nie znalezione."
fi

# Logika aktualizacji cache ikon, bardziej spójna z install.sh
if command -v gtk-update-icon-cache &> /dev/null; then
    TARGET_ICON_CACHE_DIR_FOR_UPDATE=""
    # Sprawdź, czy ICON_INSTALL_TARGET_DIR wskazuje na katalog wewnątrz struktury motywów ikon
    if [[ "$ICON_INSTALL_TARGET_DIR" == *"/icons/"* ]]; then
        # Spróbuj znaleźć katalog główny motywu ikon
        # (to jest uproszczenie, install.sh używa dirname "$(dirname "$ICON_INSTALL_TARGET_DIR")")
        POTENTIAL_THEME_BASE=$(dirname "$ICON_INSTALL_TARGET_DIR")
        while [[ "$POTENTIAL_THEME_BASE" != "/" && "$POTENTIAL_THEME_BASE" != "." && ! -f "$POTENTIAL_THEME_BASE/index.theme" ]]; do
            # Zabezpieczenie przed pętlą, jeśli ścieżka jest "dziwna"
            if [ "$POTENTIAL_THEME_BASE" == "$(dirname "$POTENTIAL_THEME_BASE")" ]; then break; fi
            POTENTIAL_THEME_BASE=$(dirname "$POTENTIAL_THEME_BASE")
        done
        if [ -f "$POTENTIAL_THEME_BASE/index.theme" ]; then
            TARGET_ICON_CACHE_DIR_FOR_UPDATE="$POTENTIAL_THEME_BASE"
        fi
    fi

    # Jeśli nie znaleziono specyficznego motywu LUB ikona była np. w pixmaps (co jest naszym przypadkiem),
    # użyj hicolor jako fallback, jeśli istnieje.
    if [ -z "$TARGET_ICON_CACHE_DIR_FOR_UPDATE" ] && [ -d "/usr/share/icons/hicolor" ]; then
        TARGET_ICON_CACHE_DIR_FOR_UPDATE="/usr/share/icons/hicolor"
    fi

    if [ -n "$TARGET_ICON_CACHE_DIR_FOR_UPDATE" ] && [ -d "$TARGET_ICON_CACHE_DIR_FOR_UPDATE" ]; then
        echo "Aktualizowanie cache ikon GTK dla $TARGET_ICON_CACHE_DIR_FOR_UPDATE..."
        gtk-update-icon-cache -f -t "$TARGET_ICON_CACHE_DIR_FOR_UPDATE"
        ICON_CACHE_UPDATED=true
    elif [ -d "/usr/share/icons" ]; then # Ogólny fallback, jeśli hicolor też nie ma lub TARGET_ICON_CACHE_DIR_FOR_UPDATE jest pusty
        echo "Aktualizowanie cache ikon GTK dla /usr/share/icons/ (ogólny fallback)..."
        gtk-update-icon-cache -f -t /usr/share/icons
        ICON_CACHE_UPDATED=true
    else
        echo "Ostrzeżenie: Nie można określić katalogu dla gtk-update-icon-cache lub katalog nie istnieje."
    fi
else
    echo "Ostrzeżenie: Polecenie 'gtk-update-icon-cache' nie znalezione."
fi

echo ""
echo "$APP_NAME_DISPLAY został pomyślnie odinstalowany."
if [ "$DB_UPDATED" = true ] || [ "$ICON_CACHE_UPDATED" = true ]; then
    echo "Zmiany w menu i ikonach powinny być widoczne. W razie potrzeby wyloguj się i zaloguj ponownie."
else
    echo "Możesz potrzebować się wylogować i zalogować ponownie, aby upewnić się, że wszystkie zmiany są widoczne."
fi

exit 0
