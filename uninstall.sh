#!/bin/bash

# Skrypt deinstalacyjny dla Linux AI Assistant

# --- Konfiguracja (musi być DOKŁADNIE taka sama jak w install.sh) ---
APP_NAME_DISPLAY="Linux AI Assistant"
INSTALL_DIR_BASE="/opt"
APP_INSTALL_DIR="$INSTALL_DIR_BASE/$APP_NAME_DISPLAY"
BIN_NAME="laia"

# Nazwa pliku ikony, jaka została zapisana w systemie przez install.sh
ICON_SYSTEM_FILENAME="laia_icon.png"

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
    rm "$DESKTOP_FILE_PATH"
    echo "Plik .desktop usunięty."
else
    echo "Plik .desktop ($DESKTOP_FILE_PATH) nie znaleziony."
fi

# --- Krok 2: Usuwanie dowiązania symbolicznego ---
SYMBLINK_PATH="/usr/local/bin/$BIN_NAME"
echo "Usuwanie dowiązania symbolicznego: $SYMBLINK_PATH..."
if [ -L "$SYMBLINK_PATH" ]; then
    rm "$SYMBLINK_PATH"
    echo "Dowiązanie symboliczne usunięte."
elif [ -f "$SYMBLINK_PATH" ]; then
     rm "$SYMBLINK_PATH"
     echo "Plik $SYMBLINK_PATH (nie dowiązanie) usunięty."
else
    echo "Dowiązanie symboliczne/plik ($SYMBLINK_PATH) nie znalezione."
fi

# --- Krok 3: Usuwanie ikony ---
# Należy sprawdzić te same potencjalne lokalizacje, do których install.sh mógł skopiować ikonę.
# Domyślnie w install.sh jest /usr/share/pixmaps
ICON_PATH_PIXMAPS="/usr/share/pixmaps/$ICON_SYSTEM_FILENAME"
# Jeśli install.sh używał struktury hicolor, np.:
ICON_PATH_HICOLOR_256="/usr/share/icons/hicolor/256x256/apps/$ICON_SYSTEM_FILENAME"

echo "Usuwanie ikony aplikacji ($ICON_SYSTEM_FILENAME)..."
ICON_REMOVED=false
if [ -f "$ICON_PATH_PIXMAPS" ]; then
    echo "Usuwanie $ICON_PATH_PIXMAPS..."
    rm "$ICON_PATH_PIXMAPS"
    echo "Ikona z pixmaps usunięta."
    ICON_REMOVED=true
fi

if [ -f "$ICON_PATH_HICOLOR_256" ]; then
    echo "Usuwanie $ICON_PATH_HICOLOR_256..."
    rm "$ICON_PATH_HICOLOR_256"
    echo "Ikona z hicolor (256x256) usunięta."
    ICON_REMOVED=true
fi

if [ "$ICON_REMOVED" = false ]; then
    echo "Ikona '$ICON_SYSTEM_FILENAME' nie została znaleziona w typowych lokalizacjach."
fi

# --- Krok 4: Usuwanie plików aplikacji i katalogu ---
echo "Usuwanie katalogu instalacyjnego: $APP_INSTALL_DIR..."
if [ -d "$APP_INSTALL_DIR" ]; then
    rm -rf "$APP_INSTALL_DIR"
    echo "Katalog instalacyjny i jego zawartość usunięte."
else
    echo "Katalog instalacyjny ($APP_INSTALL_DIR) nie znaleziony."
fi

# --- Krok 5: Aktualizacja bazy danych menu ---
echo "Aktualizowanie bazy danych menu i cache ikon..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database -q /usr/share/applications/
else
    echo "Ostrzeżenie: Polecenie 'update-desktop-database' nie znalezione."
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    if [ -d "/usr/share/icons/hicolor" ]; then
        gtk-update-icon-cache -f -t /usr/share/icons/hicolor
        echo "Cache ikon GTK (hicolor) zaktualizowany."
    fi
else
    echo "Ostrzeżenie: Polecenie 'gtk-update-icon-cache' nie znalezione."
fi

echo ""
echo "$APP_NAME_DISPLAY został pomyślnie odinstalowany."
echo "Możesz potrzebować się wylogować i zalogować ponownie, aby zmiany w menu były w pełni widoczne."

exit 0
