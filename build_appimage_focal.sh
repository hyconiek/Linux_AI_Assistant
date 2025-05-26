#!/bin/bash
set -e

echo ">>> Rozpoczynanie budowania AppImage (Python, zależności systemowe i venv powinny być gotowe z Dockerfile)..."

# === KROK (dawny 2): Definicja ścieżki projektu ===
# Kod projektu jest w /app/linux_ai_terminal_assistant
# Skrypt jest uruchamiany z /app
PROJECT_SUBDIR="linux_ai_terminal_assistant"
if [ ! -d "/app/${PROJECT_SUBDIR}" ]; then
    echo "BŁĄD: Katalog projektu /app/${PROJECT_SUBDIR} nie istnieje! Sprawdź Dockerfile."
    exit 1
fi
cd "/app/${PROJECT_SUBDIR}" # Przejdź do katalogu projektu
echo "Bieżący katalog: $(pwd)"

# === KROK (dawny 4): Przygotowanie narzędzi AppImage ===
echo ">>> Przygotowanie narzędzi AppImage..."
# Narzędzia będą pobierane do /app (jeden poziom wyżej niż katalog projektu)
cd /app
# --- linuxdeployqt ---
 echo "Pobieranie linuxdeployqt..."
 wget -q "https://github.com/probonopd/linuxdeployqt/releases/download/continuous/linuxdeployqt-continuous-x86_64.AppImage" -O linuxdeployqt.AppImage
 chmod +x linuxdeployqt.AppImage
 echo "Ekstrahowanie linuxdeployqt..."
 ./linuxdeployqt.AppImage --appimage-extract > /dev/null
 if [ -f "squashfs-root/AppRun" ]; then
     mv squashfs-root linuxdeployqt_extracted
     LNLPQT_EXEC="/app/linuxdeployqt_extracted/AppRun"
     echo "linuxdeployqt wyekstrahowane do ${LNLPQT_EXEC}"
 elif [ -f "squashfs-root/usr/bin/linuxdeployqt" ]; then
     mv squashfs-root linuxdeployqt_extracted
     LNLPQT_EXEC="/app/linuxdeployqt_extracted/usr/bin/linuxdeployqt"
     echo "linuxdeployqt (z usr/bin) wyekstrahowane do ${LNLPQT_EXEC}"
 else
     echo "BŁĄD: Nie udało się poprawnie wyekstrahować linuxdeployqt lub znaleźć pliku wykonywalnego!"
     exit 1
 fi
 rm linuxdeployqt.AppImage
 ${LNLPQT_EXEC} --version

 # --- appimagetool ---
 echo "Pobieranie appimagetool..."
 wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O appimagetool.AppImage
 chmod +x appimagetool.AppImage
 echo "Ekstrahowanie appimagetool..."
 ./appimagetool.AppImage --appimage-extract > /dev/null
 if [ -f "squashfs-root/AppRun" ]; then
     mv squashfs-root appimagetool_extracted
     APPIMAGETOOL_EXEC_PATH="/app/appimagetool_extracted/AppRun"
     echo "appimagetool wyekstrahowane do ${APPIMAGETOOL_EXEC_PATH}"
 elif [ -f "squashfs-root/usr/bin/appimagetool" ]; then
     mv squashfs-root appimagetool_extracted
     APPIMAGETOOL_EXEC_PATH="/app/appimagetool_extracted/usr/bin/appimagetool"
     echo "appimagetool (z usr/bin) wyekstrahowane do ${APPIMAGETOOL_EXEC_PATH}"
 else
     echo "BŁĄD: Nie udało się poprawnie wyekstrahować appimagetool lub znaleźć pliku wykonywalnego!"
     exit 1
 fi
 rm appimagetool.AppImage
 ${APPIMAGETOOL_EXEC_PATH} --version
echo "<<< Przygotowanie narzędzi AppImage zakończone."


# === KROK (dawny 5): Definicja zmiennych środowiskowych ===
echo ">>> Definicja zmiennych środowiskowych..."
cd "/app/${PROJECT_SUBDIR}" # Wróć do katalogu projektu
export APP_DIR_SCRIPT="/app" # Katalog główny aplikacji w obrazie
export PROJECT_ROOT_IN_APP=$(pwd) # Teraz to /app/linux_ai_terminal_assistant
export ICON_FILENAME="laia_icon.png"
export ICON_SOURCE_PATH="${PROJECT_ROOT_IN_APP}/${ICON_FILENAME}"
export APPDIR_NAME="LinuxAIAssistant.AppDir"
export APPDIR_FULL_PATH="${APP_DIR_SCRIPT}/${APPDIR_NAME}" # AppDir będzie w /app
export PYINSTALLER_APP_NAME="Linux AI Assistant"
export PYINSTALLER_DIST_DIR_FULL_PATH="${PROJECT_ROOT_IN_APP}/dist/${PYINSTALLER_APP_NAME}"
export APP_EXECUTABLE_NAME_FROM_PYINSTALLER="${PYINSTALLER_APP_NAME}"
export APP_EXECUTABLE_NAME_IN_APPDIR_ROOT="LinuxAIAssistant"
export ICON_DESKTOP_ENTRY_NAME="linux-ai-assistant"
export ICON_APPDIR_TOPLEVEL_FILENAME="${ICON_DESKTOP_ENTRY_NAME}.png"
# VENV_PATH teraz wskazuje na venv stworzone przez Dockerfile w /app/venv
export VENV_PATH="/app/venv" # Bezpośrednia ścieżka
export PYTHON_VENV_EXEC="${VENV_PATH}/bin/python"
export PYINSTALLER_EXEC="${VENV_PATH}/bin/pyinstaller"
echo "PROJECT_ROOT_IN_APP ustawiony na: ${PROJECT_ROOT_IN_APP}"
echo "VENV_PATH ustawiony na: ${VENV_PATH}"
echo "PYINSTALLER_DIST_DIR_FULL_PATH ustawiony na: ${PYINSTALLER_DIST_DIR_FULL_PATH}"
echo "<<< Definicja zmiennych zakończona."

# KROK 6 (Konfiguracja venv i instalacja zależności) jest teraz w Dockerfile

# === KROK 7: Budowanie aplikacji za pomocą PyInstaller ===
echo ">>> KROK 7: Budowanie aplikacji za pomocą PyInstaller..."
cd "${PROJECT_ROOT_IN_APP}" # Upewnij się, że jesteś w katalogu projektu
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
     "PyQt5.QtWebSockets" "PyQt5.QtQml" "PyQt5.QtQuick" "PyQt5.QtQuickWidgets" # DODANE QtQuickWidgets
     "PyQt5.QtMultimedia" "PyQt5.QtNetworkAuth"
     "PyQt5.QtBluetooth" "PyQt5.QtNfc" "PyQt5.QtSensors" "PyQt5.QtSerialPort" "PyQt5.QtPositioning"
     "PyQt5.QtLocation" "PyQt5.QtTextToSpeech" "PyQt5.QtWebEngineWidgets" "PyQt5.QtWebEngineCore"
     "PyQt5.QtWebView" "PyQt5.QtSql" "PyQt5.QtTest" "PyQt5.QtHelp" "PyQt5.QtDesigner"
     "PyQt5.Qt3DCore" "PyQt5.Qt3DRender" "PyQt5.Qt3DInput" "PyQt5.Qt3DLogic" "PyQt5.Qt3DAnimation"
     "PyQt5.Qt3DExtras" "PyQt5.QtQuick3D"
     "PyQt5.QtPdf" "PyQt5.QtPdfWidgets"
     "PyQt5.QtGamepad" "PyQt5.QtRemoteObjects" "PyQt5.QtScxml" "PyQt5.QtWebChannel"
 )
 for MOD in "${MODULES_TO_EXCLUDE[@]}"; do PYINSTALLER_ARGS+=( "--exclude-module" "${MOD}" ); done
 HIDDEN_IMPORTS_LIST=( "PyQt5.sip" "PyQt5.QtCore" "PyQt5.QtGui" "PyQt5.QtWidgets" "PyQt5.QtSvg" "PyQt5.QtPrintSupport" "google.generativeai" "google.ai.generativelanguage" "google.auth" "google.api_core" "google.protobuf" "google.type" "google.rpc" "proto" "grpc" "PIL" "pkg_resources" "argparse" "backend_cli" )
 for IMP in "${HIDDEN_IMPORTS_LIST[@]}"; do PYINSTALLER_ARGS+=( "--hidden-import" "${IMP}" ); done
 PYINSTALLER_ARGS+=( "linux_ai_assistant_gui.py" )
 echo "Finalna komenda PyInstaller: ${PYTHON_VENV_EXEC} -m PyInstaller ${PYINSTALLER_ARGS[*]}"
 ${PYTHON_VENV_EXEC} -m PyInstaller "${PYINSTALLER_ARGS[@]}"
 if [ $? -ne 0 ]; then echo "BŁĄD KRYTYCZNY PyInstaller!"; exit 1; fi
echo "<<< KROK 7: Zakończono."

 # === KROK 8: Tworzenie struktury AppDir i kopiowanie plików ===
 echo ">>> KROK 8: Tworzenie struktury AppDir..."
 cd "${APP_DIR_SCRIPT}" # Powrót do /app
 if [ -d "${APPDIR_FULL_PATH}" ]; then rm -rf "${APPDIR_FULL_PATH}"; fi
 mkdir -p "${APPDIR_FULL_PATH}"

 echo "Zawartość katalogu PyInstallera PRZED kopiowaniem (${PYINSTALLER_DIST_DIR_FULL_PATH}):"
 ls -lAR "${PYINSTALLER_DIST_DIR_FULL_PATH}" || echo "Nie udało się wylistować zawartości ${PYINSTALLER_DIST_DIR_FULL_PATH}"
 echo "Sprawdzanie dowiązań symbolicznych w katalogu PyInstallera PRZED kopiowaniem:"
 find "${PYINSTALLER_DIST_DIR_FULL_PATH}" -type l -ls || echo "Nie udało się znaleźć dowiązań w ${PYINSTALLER_DIST_DIR_FULL_PATH}"

 echo "Kopiowanie z PyInstallera (${PYINSTALLER_DIST_DIR_FULL_PATH}) do AppDir (${APPDIR_FULL_PATH}) za pomocą rsync (z dereferencjacją dowiązań)..."
 if rsync -rLptD --exclude='.*' "${PYINSTALLER_DIST_DIR_FULL_PATH}/" "${APPDIR_FULL_PATH}/"; then
    echo "Kopiowanie za pomocą rsync zakończone pomyślnie."
 else
    echo "BŁĄD: Kopiowanie za pomocą rsync nie powiodło się. Kod błędu: $?"
    exit 1
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
     LIBPYTHON_EXPECTED_NAME="libpython${PYTHON_VERSION_MM_VENV_SCRIPT}.so.1.0"
     LIBPYTHON_PACKED_PATH="${INTERNAL_DIR_IN_APPDIR}/${LIBPYTHON_PACKED_NAME}"
     LIBPYTHON_EXPECTED_PATH="${INTERNAL_DIR_IN_APPDIR}/${LIBPYTHON_EXPECTED_NAME}"
     if [ -f "${LIBPYTHON_PACKED_PATH}" ] && [ ! -e "${LIBPYTHON_EXPECTED_PATH}" ]; then
         echo "Kopiowanie libpython: ${LIBPYTHON_PACKED_PATH} -> ${LIBPYTHON_EXPECTED_PATH}"
         cp "${LIBPYTHON_PACKED_PATH}" "${LIBPYTHON_EXPECTED_PATH}"
     elif [ -f "${LIBPYTHON_EXPECTED_PATH}" ]; then
         echo "Oczekiwany plik libpython ${LIBPYTHON_EXPECTED_PATH} już istnieje."
     else
         echo "OSTRZEŻENIE: Nie znaleziono libpython ${LIBPYTHON_PACKED_NAME} ani ${LIBPYTHON_EXPECTED_NAME} w _internal."
     fi
 fi
 mkdir -p "${APPDIR_FULL_PATH}/usr/bin" \
         "${APPDIR_FULL_PATH}/usr/lib" \
         "${APPDIR_FULL_PATH}/usr/share/applications" \
         "${APPDIR_FULL_PATH}/usr/share/icons/hicolor/256x256/apps"
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
Categories=Utility;
StartupWMClass=Linux AI Assistant
EOF
 cp "${DESKTOP_FILE_PATH_IN_APPDIR_ROOT}" "${DESKTOP_FILE_PATH_USR}"
 ICON_DEST_SYSTEM_PATH="${APPDIR_FULL_PATH}/usr/share/icons/hicolor/256x256/apps/${ICON_DESKTOP_ENTRY_NAME}.png"
 ICON_DEST_TOPLEVEL_PATH="${APPDIR_FULL_PATH}/${ICON_APPDIR_TOPLEVEL_FILENAME}"
 if [ -f "${ICON_SOURCE_PATH}" ]; then # ICON_SOURCE_PATH zdefiniowane w Kroku 5 skryptu
     cp "${ICON_SOURCE_PATH}" "${ICON_DEST_SYSTEM_PATH}"
     cp "${ICON_SOURCE_PATH}" "${ICON_DEST_TOPLEVEL_PATH}"
     (cd "${APPDIR_FULL_PATH}" && ln -sf "${ICON_APPDIR_TOPLEVEL_FILENAME}" ".DirIcon")
     echo "Ikony skopiowane i .DirIcon utworzone."
 else
     echo "OSTRZEŻENIE: Plik ikony ${ICON_SOURCE_PATH} nie znaleziony."
 fi
 cd "${APP_DIR_SCRIPT}" # Wróć do /app
 APP_RUN_PATH_SCRIPT="${APPDIR_FULL_PATH}/AppRun" # Unikaj konfliktu z APP_RUN_PATH z globalnego skryptu
 cat > "${APP_RUN_PATH_SCRIPT}" << EOF
#!/bin/bash
APPDIR_EXEC=\$(dirname "\$(readlink -f "\$0")") # Użyj innej nazwy zmiennej
cd "\$APPDIR_EXEC"
export LD_LIBRARY_PATH="\$APPDIR_EXEC/_internal":"\$APPDIR_EXEC/_internal/PyQt5/Qt5/lib\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
export PYTHONPATH="\$APPDIR_EXEC/_internal":"\$APPDIR_EXEC/_internal/src\${PYTHONPATH:+:\$PYTHONPATH}"
export QT_PLUGIN_PATH="\$APPDIR_EXEC/_internal/PyQt5/Qt5/plugins\${QT_PLUGIN_PATH:+:\$QT_PLUGIN_PATH}"
export QT_QPA_PLATFORM_PLUGIN_PATH="\$APPDIR_EXEC/_internal/PyQt5/Qt5/plugins/platforms\${QT_QPA_PLATFORM_PLUGIN_PATH:+:\$QT_QPA_PLATFORM_PLUGIN_PATH}"
export XDG_DATA_DIRS="\$APPDIR_EXEC/usr/share\${XDG_DATA_DIRS:+:\$XDG_DATA_DIRS}"
exec "\$APPDIR_EXEC/${APP_EXECUTABLE_NAME_IN_APPDIR_ROOT}" "\$@"
EOF
 chmod +x "${APP_RUN_PATH_SCRIPT}"
echo "<<< KROK 8: Zakończono."

 # === KROK 9: Agresywne oczyszczanie AppDir ===
 echo ">>> KROK 9: Agresywne oczyszczanie AppDir..."
 PATH_TO_PYQT_BASE_CLEANUP_SCRIPT="${APPDIR_FULL_PATH}/_internal/PyQt5"
 PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT="${PATH_TO_PYQT_BASE_CLEANUP_SCRIPT}/Qt5"
 PATH_TO_INTERNAL_LIBS_GENERAL_CLEANUP_SCRIPT="${APPDIR_FULL_PATH}/_internal"

 echo "Usuwanie katalogów plugins/qml/audio/mediaservice/playlistformats..."
 if [ -d "${PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT}/qml" ]; then rm -rf "${PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT}/qml"; fi
 find "${PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT}/plugins" \( -name "audio" -o -name "mediaservice" -o -name "playlistformats" \) -type d -print -exec rm -rf {} \; || true

 echo "Usuwanie bibliotek QML/Quick z lib/..."
 find "${PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT}/lib" -maxdepth 1 \( \
    -name "libQt5Qml.so.5" -o -name "libQt5QmlModels.so.5" -o -name "libQt5QmlWorkerScript.so.5" -o \
    -name "libQt5Quick.so.5" -o -name "libQt5QuickControls2.so.5" -o -name "libQt5QuickParticles.so.5" -o \
    -name "libQt5QuickShapes.so.5" -o -name "libQt5QuickTemplates2.so.5" -o -name "libQt5QuickTest.so.5" -o \
    -name "libQt5QuickWidgets.so.5" \
 \) -print -delete || true

 echo "Usuwanie modułów Qt i ich bibliotek/wtyczek (Web, 3D, Location, Sensors, SerialPort, NfcBluetooth, Sql, TestSupport, TextToSpeech, DesignerHelp, Eglfs, RemoteObjects, Pdf, WebGLPlatformPlugin)..."
 find "${PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT}/plugins" -maxdepth 2 \( \
    -name "libqpdf.so" -o -name "libqwebgl.so" -o -name "libqtwebview_webengine.so" -o \
    -name "geoservices" -o -name "position" -o -name "sensors" -o -name "sensorgestures" -o \
    -name "sqldrivers" -o -name "texttospeech" -o -name "designer" -o -name "nfc" -o \
    -name "assetimporters" -o -name "geometryloaders" -o -name "renderers" -o -name "renderplugins" -o -name "sceneparsers" \
 \) -type d -print -exec rm -rf {} \; || true
 find "${PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT}/plugins" -maxdepth 3 \( \
    -name "libqeglfs.so" -o \
    -name "libgstcamerabin.so" -o -name "libgstaudiodecoder.so" -o -name "libgstmediacapture.so" -o -name "libgstmediaplayer.so" -o \
    -name "libqtmultimedia_m3u.so" -o -name "libqtaudio_alsa.so" -o -name "libqtmedia_pulse.so" -o \
    -name "libgltfsceneimport.so" -o -name "libassimpsceneimport.so" -o -name "libgltfsceneexport.so" -o \
    -name "libopenglrenderer.so" -o -name "libdefaultgeometryloader.so" -o -name "libgltfgeometryloader.so" -o \
    -name "libscene2d.so" -o -name "libqtexttospeech_speechd.so" \
 \) -print -delete || true

 find "${PATH_TO_QT_LIBS_PLUGINS_CLEANUP_SCRIPT}/lib" -maxdepth 1 \( \
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
     "QtWebSockets.abi3.so" "QtQml.abi3.so" "QtQuick.abi3.so" "QtQuickWidgets.abi3.so" # DODANE QtQuickWidgets
     "QtMultimedia.abi3.so"
     "QtMultimediaWidgets.abi3.so" "QtNetworkAuth.abi3.so" "QtBluetooth.abi3.so" "QtNfc.abi3.so"
     "QtSensors.abi3.so" "QtSerialPort.abi3.so" "QtPositioning.abi3.so" "QtLocation.abi3.so"
     "QtTextToSpeech.abi3.so" "QtWebEngineWidgets.abi3.so" "QtWebEngineCore.abi3.so" "QtWebView.abi3.so"
     "QtSql.abi3.so" "QtTest.abi3.so" "QtHelp.abi3.so" "QtDesigner.abi3.so"
     "Qt3DCore.abi3.so" "Qt3DRender.abi3.so" "Qt3DInput.abi3.so" "Qt3DLogic.abi3.so"
     "Qt3DAnimation.abi3.so" "Qt3DExtras.abi3.so" "QtQuick3D.abi3.so"
     "QtPdf.abi3.so" "QtPdfWidgets.abi3.so"
     "QtGamepad.abi3.so" "QtRemoteObjects.abi3.so" "QtScxml.abi3.so" "QtWebChannel.abi3.so"
     "QtXmlPatterns.abi3.so" "QtScript.abi3.so" "QtScriptTools.abi3.so" "QtDesignerComponents.abi3.so"
 )
 for ABI3_FILE in "${QT_ABI3_TO_REMOVE[@]}"; do
     FILE_PATH="${PATH_TO_PYQT_BASE_CLEANUP_SCRIPT}/${ABI3_FILE}"
     if [ -f "${FILE_PATH}" ]; then
         echo "Usuwam: ${FILE_PATH}"
         rm -f "${FILE_PATH}"
     fi
     PYI_FILE="${FILE_PATH%.*}.pyi"
     if [ -f "${PYI_FILE}" ]; then
         echo "Usuwam: ${PYI_FILE}"
         rm -f "${PYI_FILE}"
     fi
 done

 echo "Usuwanie zbędnych bibliotek systemowych z _internal/ (libpulse, libsndfile, libldap, itp.)..."
 find "${PATH_TO_INTERNAL_LIBS_GENERAL_CLEANUP_SCRIPT}" -maxdepth 1 \( \
    -name "libstdc++.so.6" -o -name "libgcc_s.so.1" -o \
    -name "libglib-2.0.so.0" -o -name "libgobject-2.0.so.0" -o -name "libgmodule-2.0.so.0" -o -name "libgio-2.0.so.0" -o \
    -name "libpulse.so.0" -o -name "libsndfile.so.1" -o -name "libvorbis.so.0" -o -name "libvorbisenc.so.2" -o \
    -name "libFLAC.so.8" -o -name "libopus.so.0" -o -name "libogg.so.0" -o -name "libasound.so.2" -o \
    -name "libgstapp-1.0.so.0" -o -name "libgstaudio-1.0.so.0" -o -name "libgstbase-1.0.so.0" -o \
    -name "libgstpbutils-1.0.so.0" -o -name "libgstreamer-1.0.so.0" -o -name "libgsttag-1.0.so.0" -o \
    -name "libgstvideo-1.0.so.0" -o -name "liborc-0.4.so.0" -o -name "libpulsecommon-*.so" -o \
    -name "libpulse-mainloop-glib.so.0" -o \
    -name "libkeyutils.so.1" -o -name "libkrb5.so.3" -o -name "libk5crypto.so.3" -o -name "libkrb5support.so.0" -o \
    -name "libgssapi_krb5.so.2" -o -name "libcom_err.so.2" -o \
    -name "libldap-*.so.0" -o -name "liblber-*.so.0" -o -name "libsasl2.so.2" -o \
    -name "libcups.so.2" -o -name "libodbc.so.2" -o -name "libpq.so.5" -o \
    -name "libapparmor.so.1" -o -name "libavahi-client.so.3" -o -name "libavahi-common.so.3" -o -name "libltdl.so.7" \
 \) -print -delete || true

 echo "Usuwanie niepotrzebnych pakietów Pythona z _internal/..."
 PACKAGES_TO_CLEANUP_FROM_INTERNAL_SCRIPT=(
     "aiohttp" "attrs" "frozenlist" "markupsafe" "multidict" "propcache" "yarl"
     "shell_gpt" "distro" "instructor" "openai" "rich" "typer"
     "click" "shellingham" "markdown_it_py" "pygments" "docstring_parser"
     "jinja2" "jiter" "tenacity" "aiohappyeyeballs" "aiosignal" "anyio"
     "httpx" "httpcore" "h11" "annotated_types" "typing_inspection" "mdurl"
     "pip" "wheel" "altgraph" "pyinstaller-hooks-contrib" "importlib_metadata" "packaging" "zipp"
     "urllib3" "uritemplate" "sniffio" "tqdm" "pyasn1" "pyasn1_modules" "rsa"
     "cachetools" "httplib2" "google_auth_httplib2" "pyparsing" "proto_plus"
     "google_ai_generativelanguage" "google_api_core" "google_api_python_client" "google_auth" "googleapis_common_protos"
     "grpcio" "grpcio_status" "protobuf"
     "attrs-*.dist-info" "MarkupSafe-*.dist-info"
 )
 for PKG_NAME_SCRIPT in "${PACKAGES_TO_CLEANUP_FROM_INTERNAL_SCRIPT[@]}"; do
     find "${PATH_TO_INTERNAL_LIBS_GENERAL_CLEANUP_SCRIPT}" -maxdepth 1 -name "${PKG_NAME_SCRIPT}" -print -exec rm -rf {} \; || true
 done

 echo "Usuwanie bardzo specyficznych plików z notebooka..."
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/mediaservice/libgstcamerabin.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/mediaservice/libgstaudiodecoder.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/mediaservice/libgstmediacapture.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/mediaservice/libgstmediaplayer.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/playlistformats/libqtmultimedia_m3u.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/audio/libqtaudio_alsa.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/audio/libqtmedia_pulse.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/platforms/libqwebgl.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/webview/libqtwebview_webengine.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/qml/QtQml/RemoteObjects/libqtqmlremoteobjects.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/qml/QtQuick/Scene2D/libqtquickscene2dplugin.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/sceneparsers/libgltfsceneimport.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/sceneparsers/libassimpsceneimport.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/sceneparsers/libgltfsceneexport.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/renderers/libopenglrenderer.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/imageformats/libqpdf.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/geometryloaders/libdefaultgeometryloader.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/geometryloaders/libgltfgeometryloader.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/renderplugins/libscene2d.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/Qt5/plugins/texttospeech/libqtexttospeech_speechd.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Location.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5MultimediaWidgets.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5MultimediaGstTools.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Multimedia.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5MultimediaQuick.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Positioning.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Sensors.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Nfc.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Bluetooth.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Sql.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Test.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5PositioningQuick.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5PrintSupport.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5WebView.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5OpenGL.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DRender.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3D.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DRuntimeRender.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DAssetImport.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DUtils.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DQuick.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DInput.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DLogic.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DAnimation.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DExtras.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DQuickAnimation.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DQuickExtras.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5Quick3DQuickInput.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5TextToSpeech.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5WebSockets.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/libQt5SerialPort.so.5" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/QtXmlPatterns.abi3.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/QtScript.abi3.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/QtScriptTools.abi3.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/QtDesignerComponents.abi3.so" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/QtMultimedia.pyi" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/QtMultimediaWidgets.pyi" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/QtTextToSpeech.pyi" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/QtPositioning.pyi" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/QtLocation.pyi" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/QtBluetooth.pyi" || true
 rm -f "${APPDIR_FULL_PATH}/_internal/PyQt5/QtSerialPort.pyi" || true

 echo "Usuwanie pustych katalogów..."
 find "${APPDIR_FULL_PATH}" -depth -type d -empty -print -delete || true
echo "<<< KROK 9: Zakończono."

 # === KROK 10: Budowanie finalnego AppImage ===
 echo ">>> KROK 10: Budowanie finalnego AppImage..."
 cd "${APP_DIR_SCRIPT}" # Powrót do /app
 FINAL_APPIMAGE_NAME_SCRIPT="Linux_AI_Assistant-$(uname -m).AppImage"
 FINAL_APPIMAGE_PATH_IN_APP_DIR_SCRIPT="${APP_DIR_SCRIPT}/${FINAL_APPIMAGE_NAME_SCRIPT}"
 if [ -f "${FINAL_APPIMAGE_PATH_IN_APP_DIR_SCRIPT}" ]; then rm -f "${FINAL_APPIMAGE_PATH_IN_APP_DIR_SCRIPT}"; fi

 DESKTOP_FILE_FOR_LDQT_SCRIPT="${APPDIR_FULL_PATH}/${ICON_DESKTOP_ENTRY_NAME}.desktop"

 echo "Przygotowywanie AppDir za pomocą linuxdeployqt (bez opcji -appimage)..."
 ${LNLPQT_EXEC} "${DESKTOP_FILE_FOR_LDQT_SCRIPT}" -no-translations -no-copy-copyright-files -always-overwrite -verbose=1
 if [ $? -ne 0 ]; then
    echo "BŁĄD: linuxdeployqt (przygotowanie) nie powiodło się. Przerywam."
    exit 1
 fi
 echo "linuxdeployqt (przygotowanie) zakończone."

 echo "Usuwanie libstdc++.so.6 i libgcc_s.so.1 z _internal, jeśli zostały dodane przez linuxdeployqt..."
 find "${PATH_TO_INTERNAL_LIBS_GENERAL_CLEANUP_SCRIPT}" -maxdepth 1 \( -name "libstdc++.so.6" -o -name "libgcc_s.so.1" \) -print -delete || true

 echo "Budowanie finalnego AppImage za pomocą appimagetool..."
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

# ... (reszta skryptu) ...
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
