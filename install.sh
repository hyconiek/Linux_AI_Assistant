#!/bin/bash

# Skrypt instalacyjny dla Linux AI Assistant (AppImage)
# Kopiuje app_icon.png jako laia_icon.png do systemu.

# --- Konfiguracja ---
APP_NAME_DISPLAY="Linux AI Assistant"
APPIMAGE_FILE_BASENAME="Linux-AI-Assistant-x86_64.AppImage"
INSTALL_DIR_BASE="/opt"
APP_INSTALL_DIR="$INSTALL_DIR_BASE/$APP_NAME_DISPLAY"
BIN_NAME="laia"

ICON_SOURCE_FILENAME="laia_icon.png"      # Nazwa Twojego pliku ikony źródłowej
ICON_SYSTEM_FILENAME="laia_icon.png"   # Nazwa, pod jaką ikona będzie zapisana w systemie
ICON_DESKTOP_ENTRY_NAME="laia_icon.png" # Nazwa używana w Icon= w pliku .desktop (może być z rozszerzeniem dla pixmaps)

DESKTOP_FILE_NAME="laia.desktop"

# Sprawdzenie uprawnień roota
if [ "$(id -u)" -ne 0 ]; then
  echo "Ten skrypt musi być uruchomiony z uprawnieniami roota (sudo)."
  exit 1
fi

echo "Rozpoczynanie instalacji $APP_NAME_DISPLAY..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE_SOURCE_PATH="$SCRIPT_DIR/$APPIMAGE_FILE_BASENAME"
ICON_SOURCE_PATH="$SCRIPT_DIR/$ICON_SOURCE_FILENAME"

if [ ! -f "$APPIMAGE_SOURCE_PATH" ]; then
    echo "Błąd: Plik AppImage '$APPIMAGE_FILE_BASENAME' nie został znaleziony w $SCRIPT_DIR."
    exit 1
fi

ICON_INSTALL_TARGET_DIR="/usr/share/pixmaps" # Domyślna lokalizacja dla tej konfiguracji
# Możesz zmienić na np. "/usr/share/icons/hicolor/256x256/apps"
# Jeśli zmienisz na hicolor, to ICON_DESKTOP_ENTRY_NAME powinien być "laia_icon" (bez .png)

echo "Tworzenie katalogu instalacyjnego: $APP_INSTALL_DIR"
mkdir -p "$APP_INSTALL_DIR" || { echo "Błąd: Nie można utworzyć katalogu $APP_INSTALL_DIR."; exit 1; }

echo "Kopiowanie pliku AppImage do $APP_INSTALL_DIR/$APPIMAGE_FILE_BASENAME..."
cp "$APPIMAGE_SOURCE_PATH" "$APP_INSTALL_DIR/$APPIMAGE_FILE_BASENAME" || { echo "Błąd: Nie można skopiować pliku AppImage."; exit 1; }
chmod +x "$APP_INSTALL_DIR/$APPIMAGE_FILE_BASENAME"

if [ -f "$ICON_SOURCE_PATH" ]; then
    echo "Tworzenie katalogu dla ikony (jeśli potrzebne): $ICON_INSTALL_TARGET_DIR"
    mkdir -p "$ICON_INSTALL_TARGET_DIR" || { echo "Ostrzeżenie: Nie można utworzyć katalogu dla ikony $ICON_INSTALL_TARGET_DIR."; }

    echo "Kopiowanie ikony aplikacji ($ICON_SOURCE_PATH) jako $ICON_INSTALL_TARGET_DIR/$ICON_SYSTEM_FILENAME..."
    cp "$ICON_SOURCE_PATH" "$ICON_INSTALL_TARGET_DIR/$ICON_SYSTEM_FILENAME" || { echo "Ostrzeżenie: Nie można skopiować ikony."; ICON_DESKTOP_ENTRY_NAME=""; } # Jeśli kopiowanie się nie uda, nie ustawiaj ikony w .desktop
else
    echo "Ostrzeżenie: Plik ikony '$ICON_SOURCE_PATH' nie został znaleziony. Ikona nie zostanie zainstalowana."
    ICON_DESKTOP_ENTRY_NAME="" # Nie ustawiaj ikony w .desktop
fi

echo "Tworzenie dowiązania symbolicznego w /usr/local/bin/$BIN_NAME..."
if [ -L "/usr/local/bin/$BIN_NAME" ] || [ -f "/usr/local/bin/$BIN_NAME" ]; then
    rm "/usr/local/bin/$BIN_NAME"
fi
ln -s "$APP_INSTALL_DIR/$APPIMAGE_FILE_BASENAME" "/usr/local/bin/$BIN_NAME" || echo "Ostrzeżenie: Nie można utworzyć dowiązania symbolicznego."

echo "Tworzenie pliku .desktop..."
DESKTOP_FILE_CONTENT="[Desktop Entry]
Version=1.0.5
Name=$APP_NAME_DISPLAY
GenericName=AI Command Assistant
Comment=AI Assistant for Linux Commands
Exec=\"$APP_INSTALL_DIR/$APPIMAGE_FILE_BASENAME\" %U
Icon=$ICON_DESKTOP_ENTRY_NAME
Terminal=false
Type=Application
Categories=Utility;Development;System;
Keywords=AI;Linux;Terminal;Command;Assistant;
StartupNotify=true
Name[pl_PL]=$APP_NAME_DISPLAY
Comment[pl_PL]=Asystent AI dla poleceń Linuksa"

if [ -z "$ICON_DESKTOP_ENTRY_NAME" ]; then
  DESKTOP_FILE_CONTENT=$(echo "$DESKTOP_FILE_CONTENT" | grep -v "^Icon=")
  echo "Informacja: Linia 'Icon=' zostanie pominięta w pliku .desktop, ponieważ ikona nie została znaleziona/skopiowana."
fi

echo "$DESKTOP_FILE_CONTENT" > "/usr/share/applications/$DESKTOP_FILE_NAME" || { echo "Błąd: Nie można utworzyć pliku .desktop."; }

echo "Aktualizowanie bazy danych menu i cache ikon..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database -q /usr/share/applications/
else
    echo "Ostrzeżenie: Polecenie 'update-desktop-database' nie znalezione."
fi
if command -v gtk-update-icon-cache &> /dev/null; then
    if [ -d "$ICON_INSTALL_TARGET_DIR" ] && [[ "$ICON_INSTALL_TARGET_DIR" == *"/icons/"* ]]; then # Jeśli to podkatalog .../icons/...
        gtk-update-icon-cache -f -t "$(dirname "$(dirname "$ICON_INSTALL_TARGET_DIR")")" # Aktualizuj nadrzędny katalog tematu ikon
        echo "Cache ikon GTK dla $(dirname "$(dirname "$ICON_INSTALL_TARGET_DIR")") zaktualizowany."
    elif [ -d "/usr/share/icons/hicolor" ]; then # Domyślnie hicolor, jeśli nie jest to ścieżka tematu
         gtk-update-icon-cache -f -t /usr/share/icons/hicolor
         echo "Cache ikon GTK (hicolor) zaktualizowany."
    fi
else
    echo "Ostrzeżenie: Polecenie 'gtk-update-icon-cache' nie znalezione."
fi

echo ""
echo "$APP_NAME_DISPLAY został pomyślnie zainstalowany!"
echo "Możesz potrzebować się wylogować i zalogować ponownie, aby zobaczyć ikonę w menu."
echo "Uruchom z menu lub wpisując '$BIN_NAME' w terminalu."

exit 0
