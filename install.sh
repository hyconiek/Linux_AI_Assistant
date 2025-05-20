#!/bin/bash

# Prosty skrypt instalacyjny dla Linux AI Assistant

# --- Konfiguracja ---
APP_NAME="LinuxAIAssistant"
INSTALL_DIR="/opt/$APP_NAME"
BIN_NAME="linux-ai-assistant" # Nazwa dowiązania symbolicznego w /usr/local/bin
ICON_NAME="linux-ai-assistant.png" # Nazwa ikony w katalogu ikon systemowych
DESKTOP_FILE_NAME="linux-ai-assistant.desktop"

# Sprawdzenie uprawnień roota
if [ "$(id -u)" -ne 0 ]; then
  echo "Ten skrypt musi być uruchomiony z uprawnieniami roota (sudo)."
  exit 1
fi

echo "Rozpoczynanie instalacji $APP_NAME..."

# --- Krok 1: Kopiowanie plików aplikacji ---
echo "Tworzenie katalogu instalacyjnego: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
if [ $? -ne 0 ]; then
  echo "Błąd: Nie można utworzyć katalogu $INSTALL_DIR."
  exit 1
fi

echo "Kopiowanie pliku wykonywalnego aplikacji..."
# Zakładamy, że skrypt jest uruchamiany z głównego katalogu projektu,
# a binarka jest w ./dist/LinuxAIAssistant
if [ ! -f "./dist/$APP_NAME" ]; then
    echo "Błąd: Plik wykonywalny ./dist/$APP_NAME nie został znaleziony."
    echo "Upewnij się, że zbudowałeś aplikację za pomocą PyInstallera i ten skrypt jest w głównym katalogu projektu."
    exit 1
fi
cp "./dist/$APP_NAME" "$INSTALL_DIR/$APP_NAME"
chmod +x "$INSTALL_DIR/$APP_NAME"

echo "Kopiowanie ikony aplikacji..."
# Zakładamy, że ikona jest w głównym katalogu projektu jako app_icon.png
if [ ! -f "./app_icon.png" ]; then
    echo "Ostrzeżenie: Plik ikony ./app_icon.png nie został znaleziony. Ikona nie zostanie zainstalowana."
else
    mkdir -p "/usr/share/pixmaps/" # Standardowy katalog dla ikon
    cp "./app_icon.png" "/usr/share/pixmaps/$ICON_NAME"
fi

# --- Krok 2: Tworzenie dowiązania symbolicznego (opcjonalne, dla łatwego uruchamiania z terminala) ---
echo "Tworzenie dowiązania symbolicznego w /usr/local/bin/$BIN_NAME..."
# Usunięcie istniejącego dowiązania, jeśli istnieje
if [ -L "/usr/local/bin/$BIN_NAME" ]; then
    rm "/usr/local/bin/$BIN_NAME"
elif [ -f "/usr/local/bin/$BIN_NAME" ]; then
    echo "Ostrzeżenie: Istnieje plik (nie dowiązanie) o nazwie $BIN_NAME w /usr/local/bin. Pomijam tworzenie dowiązania."
fi

if [ ! -f "/usr/local/bin/$BIN_NAME" ]; then # Sprawdź ponownie, na wypadek gdyby ostrzeżenie powyżej nie było trafne
 ln -s "$INSTALL_DIR/$APP_NAME" "/usr/local/bin/$BIN_NAME"
fi


# --- Krok 3: Tworzenie pliku .desktop ---
echo "Tworzenie pliku .desktop..."
DESKTOP_FILE_CONTENT="[Desktop Entry]
Version=1.0
Name=Linux AI Assistant
GenericName=AI Command Assistant
Comment=AI Assistant for Linux Commands
Exec=$INSTALL_DIR/$APP_NAME %U
Icon=$ICON_NAME
Terminal=false
Type=Application
Categories=Utility;Development;System;
Keywords=AI;Linux;Terminal;Command;Assistant;
StartupNotify=true
Name[pl_PL]=Asystent AI dla Linuksa
Comment[pl_PL]=Asystent AI dla poleceń Linuksa"

echo "$DESKTOP_FILE_CONTENT" > "/usr/share/applications/$DESKTOP_FILE_NAME"

# --- Krok 4: Aktualizacja bazy danych menu (ważne!) ---
echo "Aktualizowanie bazy danych menu..."
update-desktop-database -q /usr/share/applications/

echo ""
echo "$APP_NAME został pomyślnie zainstalowany!"
echo "Możesz go uruchomić z menu aplikacji lub wpisując '$BIN_NAME' w terminalu (jeśli dowiązanie zostało utworzone)."

exit 0
