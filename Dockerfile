# Użyj Ubuntu 20.04 jako obrazu bazowego
FROM ubuntu:20.04

# Ustaw argumenty, aby uniknąć interaktywnych promptów
ENV DEBIAN_FRONTEND=noninteractive

# === WARSTWA 1: Podstawowe narzędzia i python3-apt dla systemowego Pythona ===
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        git \
        wget \
        ca-certificates \
        software-properties-common \
        python3-apt \
        gnupg \
        dirmngr && \
    python3.8 -c "import apt_pkg; print(f'apt_pkg dla Python 3.8 w: {apt_pkg.__file__}')" && \
    rm -rf /var/lib/apt/lists/*

# === WARSTWA 2: Dodanie PPA i instalacja Pythona 3.9 oraz ustawienie go jako domyślny ===
RUN echo "Dodawanie PPA deadsnakes..." && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update -qq && \
    echo "Instalowanie Pythona 3.9..." && \
    apt-get install -y --no-install-recommends \
        python3.9 \
        python3.9-venv \
        python3.9-distutils \
        python3.9-dev && \
    echo "Ustawianie Python 3.9 jako domyślny python3..." && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 10 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 20 && \
    update-alternatives --set python3 /usr/bin/python3.9 && \
    echo "Domyślny python3 to teraz: $(python3 --version)" && \
    echo "Instalowanie pip dla Python 3.9..." && \
    apt-get install -y --no-install-recommends python3-pip && \
    (python3.9 -m pip --version || (wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py && python3.9 /tmp/get-pip.py && rm /tmp/get-pip.py)) && \
    echo "Wersja pip dla python3.9: $(python3.9 -m pip --version)" && \
    rm -rf /var/lib/apt/lists/*

# === WARSTWA 3: Instalacja zależności systemowych dla budowania AppImage ===
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        qtbase5-dev qttools5-dev qttools5-dev-tools \
        libqt5svg5 libqt5svg5-dev \
        libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 \
        libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 \
        libfontconfig1 libfreetype6 libgl1-mesa-glx libglib2.0-0 libice6 libjpeg-turbo8 \
        libpng-dev libsm6 \
        libx11-6 libx11-xcb1 libxau6 libxcb1 libxdmcp6 libxext6 libxi6 libxrender1 \
        patchelf desktop-file-utils libgdk-pixbuf2.0-0 fuse \
        build-essential libdbus-1-3 libxcb-util1 chrpath libfuse2 \
        libwayland-client0 libwayland-cursor0 libwayland-egl1 \
        libxcomposite1 \
        file \
        rsync \
        appstream \
        libxml2-utils \
        lintian && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# === WARSTWA 4: Kopiowanie requirements.txt i instalacja zależności Python w venv ===
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /app/venv && \
    echo "Python w venv: $(/app/venv/bin/python --version)" && \
    /app/venv/bin/python -m pip install --upgrade pip setuptools wheel && \
    /app/venv/bin/python -m pip install --no-cache-dir -r /app/requirements.txt && \
    /app/venv/bin/python -m pip install pyinstaller

# === WARSTWA 5: Kopiowanie skryptu budującego i reszty kodu aplikacji ===
COPY build_appimage_focal.sh /app/build_appimage_focal.sh
RUN chmod +x /app/build_appimage_focal.sh

# Kopiuj appdir-lint.sh (zakładamy, że jest w tym samym katalogu co Dockerfile)
COPY appdir-lint.sh /app/appdir-lint.sh
RUN chmod +x /app/appdir-lint.sh


# Kopiuj cały kontekst (kod źródłowy aplikacji)
COPY . /app/linux_ai_terminal_assistant_project_code/

RUN mkdir -p /app/linux_ai_terminal_assistant && \
    mv /app/linux_ai_terminal_assistant_project_code/* /app/linux_ai_terminal_assistant/ || true && \
    rm -rf /app/linux_ai_terminal_assistant_project_code && \
    ln -s /app/venv /app/linux_ai_terminal_assistant/venv

WORKDIR /app

CMD ["/app/build_appimage_focal.sh"]
