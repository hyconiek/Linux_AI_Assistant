#!/bin/bash
set -e

echo ">>> Rozpoczynanie budowania AppImage (Python, zależności systemowe i venv powinny być gotowe z Dockerfile)..."

# === KROK (dawny 2): Definicja ścieżki projektu ===
PROJECT_SUBDIR="linux_ai_terminal_assistant"
if [ ! -d "/app/${PROJECT_SUBDIR}" ]; then
    echo "BŁĄD: Katalog projektu /app/${PROJECT_SUBDIR} nie istnieje! Sprawdź Dockerfile."
    exit 1
fi
cd "/app/${PROJECT_SUBDIR}"
echo "Bieżący katalog: $(pwd)"

# === KROK (dawny 4): Przygotowanie narzędzi AppImage ===
echo ">>> Przygotowanie narzędzi AppImage..."
cd /app
echo "Pobieranie linuxdeployqt..."
wget -q "https://github.com/probonopd/linuxdeployqt/releases/download/continuous/linuxdeployqt-continuous-x86_64.AppImage" -O linuxdeployqt.AppImage
chmod +x linuxdeployqt.AppImage
echo "Ekstrahowanie linuxdeployqt..."
./linuxdeployqt.AppImage --appimage-extract > /dev/null
LNLPQT_EXEC_PATH_APP="/app/squashfs-root/AppRun" # Prefer AppRun if it exists
LNLPQT_EXEC_PATH_USR_BIN="/app/squashfs-root/usr/bin/linuxdeployqt"

if [ -f "${LNLPQT_EXEC_PATH_APP}" ]; then
    mv squashfs-root linuxdeployqt_extracted
    LNLPQT_EXEC="/app/linuxdeployqt_extracted/AppRun"
    echo "linuxdeployqt (AppRun) wyekstrahowane do ${LNLPQT_EXEC}"
elif [ -f "${LNLPQT_EXEC_PATH_USR_BIN}" ]; then
    mv squashfs-root linuxdeployqt_extracted
    LNLPQT_EXEC="/app/linuxdeployqt_extracted/usr/bin/linuxdeployqt"
    echo "linuxdeployqt (usr/bin) wyekstrahowane do ${LNLPQT_EXEC}"
else
    echo "BŁĄD: Nie udało się poprawnie wyekstrahować linuxdeployqt lub znaleźć pliku wykonywalnego!"
    ls -R squashfs-root || true # List extracted content for debugging
    exit 1
fi
rm linuxdeployqt.AppImage
${LNLPQT_EXEC} --version

echo "Pobieranie appimagetool..."
wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O appimagetool.AppImage
chmod +x appimagetool.AppImage
echo "Ekstrahowanie appimagetool..."
./appimagetool.AppImage --appimage-extract > /dev/null
APPIMAGETOOL_EXEC_PATH_APP="/app/squashfs-root/AppRun"
APPIMAGETOOL_EXEC_PATH_USR_BIN="/app/squashfs-root/usr/bin/appimagetool"

if [ -f "${APPIMAGETOOL_EXEC_PATH_APP}" ]; then
    mv squashfs-root appimagetool_extracted
    APPIMAGETOOL_EXEC_PATH="/app/appimagetool_extracted/AppRun"
    echo "appimagetool (AppRun) wyekstrahowane do ${APPIMAGETOOL_EXEC_PATH}"
elif [ -f "${APPIMAGETOOL_EXEC_PATH_USR_BIN}" ]; then
    mv squashfs-root appimagetool_extracted
    APPIMAGETOOL_EXEC_PATH="/app/appimagetool_extracted/usr/bin/appimagetool"
    echo "appimagetool (usr/bin) wyekstrahowane do ${APPIMAGETOOL_EXEC_PATH}"
else
    echo "BŁĄD: Nie udało się poprawnie wyekstrahować appimagetool lub znaleźć pliku wykonywalnego!"
    ls -R squashfs-root || true
    exit 1
fi
rm appimagetool.AppImage
${APPIMAGETOOL_EXEC_PATH} --version
echo "<<< Przygotowanie narzędzi AppImage zakończone."

# === KROK (dawny 5): Definicja zmiennych środowiskowych ===
echo ">>> Definicja zmiennych środowiskowych..."
cd "/app/${PROJECT_SUBDIR}"
export APP_DIR_SCRIPT="/app"
export PROJECT_ROOT_IN_APP=$(pwd)
export ICON_FILENAME="laia_icon.png" # Assuming icon is in the project root
export ICON_SOURCE_PATH="${PROJECT_ROOT_IN_APP}/${ICON_FILENAME}" # Corrected path
export APPDIR_NAME="LinuxAIAssistant.AppDir"
export APPDIR_FULL_PATH="${APP_DIR_SCRIPT}/${APPDIR_NAME}"
export PYINSTALLER_APP_NAME="Linux AI Assistant"
export PYINSTALLER_DIST_DIR_FULL_PATH="${PROJECT_ROOT_IN_APP}/dist/${PYINSTALLER_APP_NAME}"
export APP_EXECUTABLE_NAME_FROM_PYINSTALLER="${PYINSTALLER_APP_NAME}"
export APP_EXECUTABLE_NAME_IN_APPDIR_ROOT="LinuxAIAssistant"
export ICON_DESKTOP_ENTRY_NAME="linux-ai-assistant" # Used for .desktop and .png in AppDir
export APPDATA_XML_FILENAME="${ICON_DESKTOP_ENTRY_NAME}.appdata.xml" # New
export ICON_APPDIR_TOPLEVEL_FILENAME="${ICON_DESKTOP_ENTRY_NAME}.png"
export VENV_PATH="/app/venv"
export PYTHON_VENV_EXEC="${VENV_PATH}/bin/python"
export PYINSTALLER_EXEC="${VENV_PATH}/bin/pyinstaller"
echo "PROJECT_ROOT_IN_APP ustawiony na: ${PROJECT_ROOT_IN_APP}"
echo "VENV_PATH ustawiony na: ${VENV_PATH}"
echo "PYINSTALLER_DIST_DIR_FULL_PATH ustawiony na: ${PYINSTALLER_DIST_DIR_FULL_PATH}"
echo "<<< Definicja zmiennych zakończona."

# === KROK 7: Budowanie aplikacji za pomocą PyInstaller ===
# (Content from your script, ensure paths are correct, ICON_FILENAME is correct)
echo ">>> KROK 7: Budowanie aplikacji za pomocą PyInstaller..."
cd "${PROJECT_ROOT_IN_APP}"
 PYQT5_DIR_PATH=$(${PYTHON_VENV_EXEC} -c "import PyQt5, os; print(os.path.dirname(PyQt5.__file__))")
 if [ ! -d "${PYQT5_DIR_PATH}" ]; then PYQT5_DIR_PATH=""; fi
 PYTHON_VERSION_SHORT_FOR_VENV=$(${PYTHON_VENV_EXEC} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
 LOREM_IPSUM_BASE_PATH_JARCO="${VENV_PATH}/lib/python${PYTHON_VERSION_SHORT_FOR_VENV}/site-packages/jaraco/text"
 LOREM_IPSUM_SOURCE_PATH_JARACO="${LOREM_IPSUM_BASE_PATH_JARCO}/Lorem ipsum.txt"
 LOREM_IPSUM_ACTUAL_SOURCE_PATH=""
 LOREM_IPSUM_TARGET_DIR_IN_INTERNAL=""
 if [ -f "${LOREM_IPSUM_SOURCE_PATH_JARACO}" ]; then
     LOREM_IPSUM_ACTUAL_SOURCE_PATH="${LOREM_IPSUM_SOURCE_PATH_JARACO}"
     LOREM_IPSUM_TARGET_DIR_IN_INTERNAL="jaraco/text"
 else
     LOREM_IPSUM_SOURCE_PATH_SETUPTOOLS="${VENV_PATH}/lib/python${PYTHON_VERSION_SHORT_FOR_VENV}/site-packages/setuptools/_vendor/jaraco/text/Lorem ipsum.txt"
     if [ -f "${LOREM_IPSUM_SOURCE_PATH_SETUPTOOLS}" ]; then
         LOREM_IPSUM_ACTUAL_SOURCE_PATH="${LOREM_IPSUM_SOURCE_PATH_SETUPTOOLS}"
         LOREM_IPSUM_TARGET_DIR_IN_INTERNAL="setuptools/_vendor/jaraco/text"
     fi
 fi
 if [ -z "${LOREM_IPSUM_ACTUAL_SOURCE_PATH}" ]; then echo "OSTRZEŻENIE: Lorem ipsum.txt nie znaleziony."; fi

 PYINSTALLER_ARGS=( "--name" "${PYINSTALLER_APP_NAME}" "--noconfirm" "--onedir" "--windowed" "--strip" "--add-data" "${ICON_FILENAME}:." "--add-data" "src:src" )
 if [ -n "${PYQT5_DIR_PATH}" ]; then PYINSTALLER_ARGS+=( "--add-data" "${PYQT5_DIR_PATH}:PyQt5" ); fi
 if [ -n "${LOREM_IPSUM_ACTUAL_SOURCE_PATH}" ]; then PYINSTALLER_ARGS+=( "--add-data" "${LOREM_IPSUM_ACTUAL_SOURCE_PATH}:_internal/${LOREM_IPSUM_TARGET_DIR_IN_INTERNAL}" ); fi

 MODULES_TO_EXCLUDE=(
     "PyQt5.QtWebSockets" "PyQt5.QtQml" "PyQt5.QtQuick" "PyQt5.QtQuickWidgets"
     "PyQt5.QtMultimedia" "PyQt5.QtNetworkAuth"
     "PyQt5.QtBluetooth" "PyQt5.QtNfc" "PyQt5.QtSensors" "PyQt5.QtSerialPort" "PyQt5.QtPositioning"
     "PyQt5.QtLocation" "PyQt5.QtTextToSpeech" "PyQt5.QtWebEngineWidgets" "PyQt5.QtWebEngineCore"
     "PyQt5.QtWebView" "PyQt5.QtSql" "PyQt5.QtTest" "PyQt5.QtHelp" "PyQt5.QtDesigner"
     "PyQt5.Qt3DCore" "PyQt5.Qt3DRender" "PyQt5.Qt3DInput" "PyQt5.Qt3DLogic" "PyQt5.Qt3DAnimation"
     "PyQt5.Qt3DExtras" "PyQt5.QtQuick3D"
     "PyQt5.QtPdf" "PyQt5.QtPdfWidgets" # Explicitly exclude PDF if not used
     "PyQt5.QtGamepad" "PyQt5.QtRemoteObjects" "PyQt5.QtScxml" "PyQt5.QtWebChannel" # More exclusions
 )
 for MOD in "${MODULES_TO_EXCLUDE[@]}"; do PYINSTALLER_ARGS+=( "--exclude-module" "${MOD}" ); done
 HIDDEN_IMPORTS_LIST=( "PyQt5.sip" "PyQt5.QtCore" "PyQt5.QtGui" "PyQt5.QtWidgets" "PyQt5.QtSvg" "PyQt5.QtPrintSupport" "google.generativeai" "google.ai.generativelanguage" "google.auth" "google.api_core" "google.protobuf" "google.type" "google.rpc" "proto" "grpc" "PIL" "pkg_resources" "argparse" "backend_cli" "socket" ) # Added socket
 for IMP in "${HIDDEN_IMPORTS_LIST[@]}"; do PYINSTALLER_ARGS+=( "--hidden-import" "${IMP}" ); done
 PYINSTALLER_ARGS+=( "linux_ai_assistant_gui.py" )
 echo "Finalna komenda PyInstaller: ${PYTHON_VENV_EXEC} -m PyInstaller ${PYINSTALLER_ARGS[*]}"
 ${PYTHON_VENV_EXEC} -m PyInstaller "${PYINSTALLER_ARGS[@]}"
 if [ $? -ne 0 ]; then echo "BŁĄD KRYTYCZNY PyInstaller!"; exit 1; fi
echo "<<< KROK 7: Zakończono."

# === KROK 8: Tworzenie struktury AppDir i kopiowanie plików ===
echo ">>> KROK 8: Tworzenie struktury AppDir..."
cd "${APP_DIR_SCRIPT}"
if [ -d "${APPDIR_FULL_PATH}" ]; then rm -rf "${APPDIR_FULL_PATH}"; fi
mkdir -p "${APPDIR_FULL_PATH}"

echo "Kopiowanie z PyInstallera (${PYINSTALLER_DIST_DIR_FULL_PATH}) do AppDir (${APPDIR_FULL_PATH}) za pomocą rsync..."
if rsync -rLptD --exclude='.*' "${PYINSTALLER_DIST_DIR_FULL_PATH}/" "${APPDIR_FULL_PATH}/"; then
    echo "Kopiowanie rsync zakończone."
else
    echo "BŁĄD: rsync nie powiódł się. Kod: $?"; exit 1;
fi

SOURCE_EXE_IN_APPDIR="${APPDIR_FULL_PATH}/${APP_EXECUTABLE_NAME_FROM_PYINSTALLER}"
TARGET_EXE_IN_APPDIR="${APPDIR_FULL_PATH}/${APP_EXECUTABLE_NAME_IN_APPDIR_ROOT}"
if [ "${APP_EXECUTABLE_NAME_FROM_PYINSTALLER}" != "${APP_EXECUTABLE_NAME_IN_APPDIR_ROOT}" ]; then
    if [ -f "${SOURCE_EXE_IN_APPDIR}" ]; then mv "${SOURCE_EXE_IN_APPDIR}" "${TARGET_EXE_IN_APPDIR}"; fi
fi
if [ ! -f "${TARGET_EXE_IN_APPDIR}" ]; then echo "BŁĄD: Brak pliku wykonywalnego w AppDir! (${TARGET_EXE_IN_APPDIR})"; exit 1; fi

INTERNAL_DIR_IN_APPDIR="${APPDIR_FULL_PATH}/_internal"
if [ -d "${INTERNAL_DIR_IN_APPDIR}" ]; then
    PYTHON_VERSION_MM_VENV_SCRIPT=$(${PYTHON_VENV_EXEC} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    LIBPYTHON_PACKED_NAME="libpython${PYTHON_VERSION_MM_VENV_SCRIPT}.so"
    LIBPYTHON_EXPECTED_NAME="libpython${PYTHON_VERSION_MM_VENV_SCRIPT}.so.1.0" # Expected by some tools
    LIBPYTHON_PACKED_PATH="${INTERNAL_DIR_IN_APPDIR}/${LIBPYTHON_PACKED_NAME}"
    LIBPYTHON_EXPECTED_PATH="${INTERNAL_DIR_IN_APPDIR}/${LIBPYTHON_EXPECTED_NAME}"

    if [ -f "${LIBPYTHON_PACKED_PATH}" ] && [ ! -e "${LIBPYTHON_EXPECTED_PATH}" ]; then
        echo "Tworzenie dowiązania symbolicznego dla libpython: ${LIBPYTHON_EXPECTED_NAME} -> ${LIBPYTHON_PACKED_NAME}"
        ln -s "${LIBPYTHON_PACKED_NAME}" "${LIBPYTHON_EXPECTED_PATH}"
    elif [ -f "${LIBPYTHON_EXPECTED_PATH}" ] && [ -L "${LIBPYTHON_EXPECTED_PATH}" ]; then
        echo "Dowiązanie libpython ${LIBPYTHON_EXPECTED_PATH} już istnieje."
    elif [ -f "${LIBPYTHON_EXPECTED_PATH}" ] && [ ! -L "${LIBPYTHON_EXPECTED_PATH}" ]; then
         echo "Plik ${LIBPYTHON_EXPECTED_PATH} istnieje, ale nie jest dowiązaniem. Zostawiam bez zmian."
    elif [ -f "${LIBPYTHON_PACKED_PATH}" ] && [ -e "${LIBPYTHON_EXPECTED_PATH}" ] && [ ! -L "${LIBPYTHON_EXPECTED_PATH}" ]; then
        echo "Plik ${LIBPYTHON_PACKED_PATH} istnieje, oraz ${LIBPYTHON_EXPECTED_PATH} istnieje, ale nie jest dowiązaniem. Sprawdź ręcznie."
    else
        echo "OSTRZEŻENIE: Nie znaleziono libpython ${LIBPYTHON_PACKED_NAME} w _internal lub ${LIBPYTHON_EXPECTED_PATH} już istnieje jako plik."
    fi
fi

mkdir -p "${APPDIR_FULL_PATH}/usr/bin" \
         "${APPDIR_FULL_PATH}/usr/lib" \
         "${APPDIR_FULL_PATH}/usr/share/applications" \
         "${APPDIR_FULL_PATH}/usr/share/icons/hicolor/256x256/apps" \
         "${APPDIR_FULL_PATH}/usr/share/metainfo" # New directory for appdata

# Desktop file (ensure Categories has a trailing semicolon if multiple)
DESKTOP_FILE_PATH_IN_APPDIR_ROOT="${APPDIR_FULL_PATH}/${ICON_DESKTOP_ENTRY_NAME}.desktop"
DESKTOP_FILE_PATH_USR="${APPDIR_FULL_PATH}/usr/share/applications/${ICON_DESKTOP_ENTRY_NAME}.desktop"
cat > "${DESKTOP_FILE_PATH_IN_APPDIR_ROOT}" << EOF
[Desktop Entry]
Version=1.1
Name=Linux AI Assistant
GenericName=AI Command Assistant
Comment=AI Assistant for Linux Commands
Exec=${APP_EXECUTABLE_NAME_IN_APPDIR_ROOT}
Icon=${ICON_DESKTOP_ENTRY_NAME}
Terminal=false
Type=Application
Categories=Utility;Development;System;
StartupWMClass=Linux AI Assistant
Keywords=AI;Linux;Terminal;Command;Assistant;Shell;Gemini;
EOF
cp "${DESKTOP_FILE_PATH_IN_APPDIR_ROOT}" "${DESKTOP_FILE_PATH_USR}"

# Copy AppStream metadata file (assuming it's in the project root with other build files)
APPDATA_SOURCE_PATH="${PROJECT_ROOT_IN_APP}/${APPDATA_XML_FILENAME}"
APPDATA_DEST_PATH="${APPDIR_FULL_PATH}/usr/share/metainfo/${APPDATA_XML_FILENAME}"
if [ -f "${APPDATA_SOURCE_PATH}" ]; then
    cp "${APPDATA_SOURCE_PATH}" "${APPDATA_DEST_PATH}"
    echo "Plik AppStream metadata skopiowany do ${APPDATA_DEST_PATH}"
else
    echo "OSTRZEŻENIE: Plik AppStream metadata ${APPDATA_SOURCE_PATH} nie znaleziony."
fi


ICON_DEST_SYSTEM_PATH="${APPDIR_FULL_PATH}/usr/share/icons/hicolor/256x256/apps/${ICON_DESKTOP_ENTRY_NAME}.png"
ICON_DEST_TOPLEVEL_PATH="${APPDIR_FULL_PATH}/${ICON_APPDIR_TOPLEVEL_FILENAME}"
if [ -f "${ICON_SOURCE_PATH}" ]; then
    cp "${ICON_SOURCE_PATH}" "${ICON_DEST_SYSTEM_PATH}"
    cp "${ICON_SOURCE_PATH}" "${ICON_DEST_TOPLEVEL_PATH}"
    (cd "${APPDIR_FULL_PATH}" && ln -sf "${ICON_APPDIR_TOPLEVEL_FILENAME}" ".DirIcon")
    echo "Ikony skopiowane i .DirIcon utworzone."
else
    echo "OSTRZEŻENIE: Plik ikony ${ICON_SOURCE_PATH} nie znaleziony."
fi
cd "${APP_DIR_SCRIPT}"
APP_RUN_PATH_SCRIPT="${APPDIR_FULL_PATH}/AppRun"
cat > "${APP_RUN_PATH_SCRIPT}" << EOF
#!/bin/bash
APPDIR_EXEC=\$(dirname "\$(readlink -f "\$0")")
cd "\$APPDIR_EXEC"
export LD_LIBRARY_PATH="\$APPDIR_EXEC/_internal":"\$APPDIR_EXEC/_internal/PyQt5/Qt5/lib\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
export PYTHONPATH="\$APPDIR_EXEC/_internal":"\$APPDIR_EXEC/_internal/src\${PYTHONPATH:+:\$PYTHONPATH}"
export QT_PLUGIN_PATH="\$APPDIR_EXEC/_internal/PyQt5/Qt5/plugins\${QT_PLUGIN_PATH:+:\$QT_PLUGIN_PATH}"
export QT_QPA_PLATFORM_PLUGIN_PATH="\$APPDIR_EXEC/_internal/PyQt5/Qt5/plugins/platforms\${QT_QPA_PLATFORM_PLUGIN_PATH:+:\$QT_QPA_PLATFORM_PLUGIN_PATH}"
export XDG_DATA_DIRS="\$APPDIR_EXEC/usr/share\${XDG_DATA_DIRS:+:\$XDG_DATA_DIRS}"
# Fallback CWD to user's home if APPIMAGE_ ehemaliger_CWD is not set or invalid
if [ -z "\$APPIMAGE_ORIGINAL_CWD" ] || [ ! -d "\$APPIMAGE_ORIGINAL_CWD" ]; then
    export APPIMAGE_ORIGINAL_CWD="\$HOME"
fi
cd "\$APPIMAGE_ORIGINAL_CWD" || cd "\$HOME" # Try to cd to original or home
exec "\$APPDIR_EXEC/${APP_EXECUTABLE_NAME_IN_APPDIR_ROOT}" "\$@"
EOF
chmod +x "${APP_RUN_PATH_SCRIPT}"
echo "<<< KROK 8: Zakończono."

# === KROK 9: Agresywne oczyszczanie AppDir ===
# (Content from your script, ensure paths are correct)
echo ">>> KROK 9: Agresywne oczyszczanie AppDir..."
 # ... (your existing aggressive cleanup commands, make sure paths are still valid after rsync -L)
 # Ensure that cleanup does not remove essential _internal files or PyQt5 core files needed.
 # The list from your script is very extensive. For AppImageHub, sometimes less aggressive is better if it doesn't break.
 PATH_TO_PYQT_BASE_CLEANUP_SCRIPT="${APPDIR_FULL_PATH}/_internal/PyQt5"
 PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT="${PATH_TO_PYQT_BASE_CLEANUP_SCRIPT}/Qt5"
 PATH_TO_INTERNAL_LIBS_GENERAL_CLEANUP_SCRIPT="${APPDIR_FULL_PATH}/_internal"

 echo "Usuwanie katalogów plugins/qml/audio/mediaservice/playlistformats..."
 if [ -d "${PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT}/qml" ]; then rm -rf "${PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT}/qml"; fi
 # More targeted removal to avoid removing 'platforms' or 'imageformats' entirely if needed by core
 find "${PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT}/plugins" -mindepth 1 -maxdepth 1 \( -name "audio" -o -name "mediaservice" -o -name "playlistformats" \
    -o -name "webview" -o -name "assetimporters" -o -name "geometryloaders" -o -name "renderers" \
    -o -name "renderplugins" -o -name "sceneparsers" -o -name "geoservices" -o -name "position" \
    -o -name "sensors" -o -name "sensorgestures" -o -name "sqldrivers" -o -name "texttospeech" \
    -o -name "designer" -o -name "nfc" \
 \) -type d -print -exec rm -rf {} \; || true

 echo "Usuwanie wybranych bibliotek z lib/..."
 find "${PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT}/lib" -maxdepth 1 \( \
    -name "libQt5Qml.so.5" -o -name "libQt5QmlModels.so.5" -o -name "libQt5QmlWorkerScript.so.5" -o \
    -name "libQt5Quick.so.5" -o -name "libQt5QuickControls2.so.5" -o -name "libQt5QuickParticles.so.5" -o \
    -name "libQt5QuickShapes.so.5" -o -name "libQt5QuickTemplates2.so.5" -o -name "libQt5QuickTest.so.5" -o \
    -name "libQt5QuickWidgets.so.5" -o \
    -name "libQt5Multimedia*.so*" -o -name "libQt5Pdf*.so*" -o -name "libQt5WebView*.so*" -o \
    -name "libQt5WebSockets*.so*" -o -name "libQt5Location*.so*" -o -name "libQt5Positioning*.so*" -o \
    -name "libQt5Sensors*.so*" -o -name "libQt5SerialPort*.so*" -o -name "libQt5Nfc*.so*" -o \
    -name "libQt5Bluetooth*.so*" -o -name "libQt5Sql*.so*" -o -name "libQt5Test*.so*" -o \
    -name "libQt5TextToSpeech*.so*" -o -name "libQt5Designer*.so*" -o -name "libQt5Help*.so*" -o \
    -name "libQt5RemoteObjects*.so*" -o -name "libQt5Gamepad*.so*" -o -name "libQt5Scxml*.so*" -o \
    -name "libQt5WebChannel*.so*" -o \
    -name "libQt53DCore*.so*" -o -name "libQt53DRender*.so*" -o -name "libQt53DInput*.so*" -o \
    -name "libQt53DLogic*.so*" -o -name "libQt53DAnimation*.so*" -o -name "libQt53DExtras*.so*" -o \
    -name "libQt5Quick3D*.so*" -o -name "libQt5EglFSDeviceIntegration.so.5" \
 \) -print -delete || true

 echo "Usuwanie modułów .abi3.so i .pyi z _internal/PyQt5/..."
 QT_ABI3_TO_REMOVE=(
     "QtWebSockets" "QtQml" "QtQuick" "QtQuickWidgets"
     "QtMultimedia" "QtMultimediaWidgets" "QtNetworkAuth" "QtBluetooth" "QtNfc"
     "QtSensors" "QtSerialPort" "QtPositioning" "QtLocation"
     "QtTextToSpeech" "QtWebEngineWidgets" "QtWebEngineCore" "QtWebView"
     "QtSql" "QtTest" "QtHelp" "QtDesigner"
     "Qt3DCore" "Qt3DRender" "Qt3DInput" "Qt3DLogic" "Qt3DAnimation"
     "Qt3DExtras" "QtQuick3D"
     "QtPdf" "QtPdfWidgets"
     "QtGamepad" "QtRemoteObjects" "QtScxml" "QtWebChannel"
     "QtXmlPatterns" "QtScript" "QtScriptTools" "QtDesignerComponents"
 )
 for ABI3_NAME in "${QT_ABI3_TO_REMOVE[@]}"; do
     ABI3_FILE="${PATH_TO_PYQT_BASE_CLEANUP_SCRIPT}/${ABI3_NAME}.abi3.so"
     PYI_FILE="${PATH_TO_PYQT_BASE_CLEANUP_SCRIPT}/${ABI3_NAME}.pyi"
     if [ -f "${ABI3_FILE}" ]; then echo "Usuwam: ${ABI3_FILE}"; rm -f "${ABI3_FILE}"; fi
     if [ -f "${PYI_FILE}" ]; then echo "Usuwam: ${PYI_FILE}"; rm -f "${PYI_FILE}"; fi
 done

 echo "Usuwanie zbędnych bibliotek systemowych i pakietów Python z _internal/ ..."
 # Simplified: remove only obviously multimedia/network-related system libs not covered by Qt paths
 find "${PATH_TO_INTERNAL_LIBS_GENERAL_CLEANUP_SCRIPT}" -maxdepth 1 \( \
    -name "libpulse.so.0" -o -name "libsndfile.so.1" -o -name "libFLAC.so.8" -o -name "libopus.so.0" -o \
    -name "libogg.so.0" -o -name "libasound.so.2" -o -name "libgst*.so*" -o -name "liborc-*.so*" -o \
    -name "libpulsecommon-*.so" -o -name "libpulse-mainloop-glib.so.0" \
 \) -print -delete || true
 # Remove bulky Python packages if they are not truly needed by core functionality that PyInstaller missed
 PACKAGES_TO_CLEANUP_FROM_INTERNAL_SCRIPT=( "aiohttp" "grpc" "httpx" "shell_gpt" "openai" "rich" "typer" "click" "jinja2" "anyio" "PIL" ) # Example
 for PKG_NAME_SCRIPT in "${PACKAGES_TO_CLEANUP_FROM_INTERNAL_SCRIPT[@]}"; do
     find "${PATH_TO_INTERNAL_LIBS_GENERAL_CLEANUP_SCRIPT}" -maxdepth 1 -name "${PKG_NAME_SCRIPT}" -type d -print -exec rm -rf {} \; || true
     find "${PATH_TO_INTERNAL_LIBS_GENERAL_CLEANUP_SCRIPT}" -maxdepth 1 -name "${PKG_NAME_SCRIPT}-*.dist-info" -type d -print -exec rm -rf {} \; || true
 done

 echo "Usuwanie pustych katalogów..."
 find "${APPDIR_FULL_PATH}" -depth -type d -empty -print -delete || true
echo "<<< KROK 9: Zakończono."


# === KROK 10: Walidacja i Budowanie finalnego AppImage ===
echo ">>> KROK 10: Walidacja i Budowanie finalnego AppImage..."
cd "${APP_DIR_SCRIPT}" # Ensure CWD is /app for appimagetool

echo "Walidacja pliku .desktop..."
if desktop-file-validate "${DESKTOP_FILE_PATH_IN_APPDIR_ROOT}"; then
    echo "Plik .desktop jest poprawny."
else
    echo "OSTRZEŻENIE: Plik .desktop ma problemy."
    # desktop-file-validate "${DESKTOP_FILE_PATH_IN_APPDIR_ROOT}" # Show errors again
fi

echo "Walidacja drzewa AppStream..."
if appstreamcli validate --nonet "${APPDIR_FULL_PATH}/usr/share/metainfo/${APPDATA_XML_FILENAME}"; then
    echo "Metadane AppStream są poprawne."
else
    echo "OSTRZEŻENIE: Metadane AppStream mają problemy."
    # appstreamcli validate --nonet "${APPDIR_FULL_PATH}/usr/share/metainfo/${APPDATA_XML_FILENAME}" # Show errors again
fi

echo "Uruchamianie appdir-lint.sh..."
# Assuming appdir-lint.sh was copied to /app by Dockerfile
if /app/appdir-lint.sh "${APPDIR_FULL_PATH}"; then
    echo "appdir-lint.sh nie znalazł krytycznych problemów."
else
    echo "OSTRZEŻENIE: appdir-lint.sh znalazł problemy."
fi


FINAL_APPIMAGE_NAME_SCRIPT="Linux_AI_Assistant-$(uname -m).AppImage"
FINAL_APPIMAGE_PATH_IN_APP_DIR_SCRIPT="${APP_DIR_SCRIPT}/${FINAL_APPIMAGE_NAME_SCRIPT}"
if [ -f "${FINAL_APPIMAGE_PATH_IN_APP_DIR_SCRIPT}" ]; then rm -f "${FINAL_APPIMAGE_PATH_IN_APP_DIR_SCRIPT}"; fi

echo "Przygotowywanie AppDir za pomocą linuxdeployqt (bez opcji -appimage)..."
# Use the .desktop file inside the AppDir for linuxdeployqt
${LNLPQT_EXEC} "${DESKTOP_FILE_PATH_IN_APPDIR_ROOT}" -no-translations -no-copy-copyright-files -always-overwrite -verbose=1
if [ $? -ne 0 ]; then
    echo "BŁĄD: linuxdeployqt (przygotowanie) nie powiodło się. Przerywam."
    exit 1
fi
echo "linuxdeployqt (przygotowanie) zakończone."

echo "Usuwanie libstdc++.so.6 i libgcc_s.so.1 z _internal PO linuxdeployqt, jeśli zostały dodane..."
find "${PATH_TO_INTERNAL_LIBS_GENERAL_CLEANUP_SCRIPT}" -maxdepth 1 \( -name "libstdc++.so.6" -o -name "libgcc_s.so.1" \) -print -delete || true

echo "Budowanie finalnego AppImage za pomocą appimagetool..."
# Ensure ARCH is set for appimagetool if it needs it, or let it auto-detect
export ARCH=$(uname -m)
${APPIMAGETOOL_EXEC_PATH} "${APPDIR_FULL_PATH}" "${FINAL_APPIMAGE_PATH_IN_APP_DIR_SCRIPT}"

if [ $? -eq 0 ] && [ -f "${FINAL_APPIMAGE_PATH_IN_APP_DIR_SCRIPT}" ]; then
    ls -lh "${FINAL_APPIMAGE_PATH_IN_APP_DIR_SCRIPT}"
    DESTINATION_IN_PROJECT_SCRIPT="${PROJECT_ROOT_IN_APP}/${FINAL_APPIMAGE_NAME_SCRIPT}"
    if [ -f "${DESTINATION_IN_PROJECT_SCRIPT}" ]; then rm -f "${DESTINATION_IN_PROJECT_SCRIPT}"; fi
    mv "${FINAL_APPIMAGE_PATH_IN_APP_DIR_SCRIPT}" "${DESTINATION_IN_PROJECT_SCRIPT}"
    echo "AppImage przeniesione do: ${DESTINATION_IN_PROJECT_SCRIPT}"
else
    echo "BŁĄD: appimagetool nie powiódł się lub plik AppImage nie został utworzony."
    exit 1
fi
echo "<<< KROK 10: Zakończono."

echo "================================================================================"
echo "Budowanie AppImage zakończone!"
echo "Plik AppImage powinien znajdować się w: ${PROJECT_ROOT_IN_APP}/${FINAL_APPIMAGE_NAME_SCRIPT}"
echo "Aby skopiować go z kontenera Docker na swój system hosta, użyj nazwy kontenera, którą nadałeś."
echo "Jeśli uruchomiłeś kontener z '--name MOJA_NAZWA_KONTENERA', wykonaj na hoście:"
echo "sudo docker cp MOJA_NAZWA_KONTENERA:${PROJECT_ROOT_IN_APP}/${FINAL_APPIMAGE_NAME_SCRIPT} ./"
echo "Na przykład, jeśli użyłeś '--name laia_build_attempt':"
echo "sudo docker cp laia_build_attempt:${PROJECT_ROOT_IN_APP}/${FINAL_APPIMAGE_NAME_SCRIPT} ./"
echo "================================================================================"
