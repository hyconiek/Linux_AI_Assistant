# Linux AI Assistant (GUI & CLI)

A versatile AI-powered assistant to help you generate, understand, and execute Linux commands using natural language. This project provides both a Graphical User Interface (GUI) and a Command-Line Interface (CLI), both utilizing Google Gemini.

[![Buy Me a Coffee](https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=☕&slug=krzyzu.83&button_colour=FF5F5F&font_colour=ffffff&font_family=Arial&outline_colour=000000&coffee_colour=FFDD00)](https://www.buymeacoffee.com/krzyzu.83)

Find the project on GitHub: [hyconiek/linux_ai_terminal_assistant](https://github.com/hyconiek/linux_ai_terminal_assistant)

## 🎉 Latest Release: v1.0.3 - AppImage 🎉

The easiest way to try the **Linux AI Assistant GUI** is by downloading our latest AppImage release! AppImages are portable and should run on most modern Linux distributions without installation.

➡️ **[Download `Linux-AI-Assistant-x86_64.AppImage` (140 MB) from Releases](https://github.com/hyconiek/linux_ai_terminal_assistant/releases/tag/1.0.2)** ⬅️


### How to Run the AppImage:

1.  **Download** the `Linux-AI-Assistant-x86_64.AppImage` file from the link above.
2.  **Make it executable**:
    Open your terminal, navigate to the directory where you downloaded the file, and run:
    ```bash
    chmod +x Linux-AI-Assistant-x86_64.AppImage
    ```
3.  **Run the application**:
    ```bash
    ./Linux-AI-Assistant-x86_64.AppImage
    ```
    *(Some desktop environments might also allow you to run it by double-clicking.)*
4.  **API Key**:
    *   On the first launch, if a Gemini API key is not configured, you will be prompted to enter one.
    *   You can manage your API key and other settings via "Settings" (File > Settings or the gear icon).

### AppImage Notes:
*   **Size**: Approx. 140 MB, bundling Python and necessary libraries. Future optimizations planned.
*   **Desktop Integration**: For menu icons, consider "AppImageLauncher" or manually creating a `.desktop` file.
*   **First Run**: May be slightly slower as the AppImage sets up.
*   **Requirements**: 64-bit Linux (glibc 2.35+ recommended), `fuse` package might be needed (`sudo apt install fuse`).


## Using the Packaged Application (Recommended for GUI)

For the easiest way to use the GUI application, download the latest pre-built executable from the [**Releases Section**](https://github.com/hyconiek/linux_ai_terminal_assistant/releases) of this repository.

1.  Download the standalone executable for Linux (e.g., `Linux-AI-Assistant-vX.Y.Z-linux-x86_64` or similar).
2.  Make it executable (on Linux/macOS):
    ```bash
    chmod +x <downloaded_executable_name>
    ```
3.  Run the application:
    ```bash
    ./<downloaded_executable_name>
    ```
4.  **API Key**: On the first launch, or via "Settings", you will be prompted for your Google Gemini API key.

## Features (GUI & Core Logic)

- **Intuitive GUI/CLI**: Choose your preferred way to interact.
- **Natural Language Command Generation**: Ask for commands in plain English (powered by Google Gemini).
- **AI-Powered**: Utilizes Google Gemini for command suggestions and explanations.
- **Direct Command Execution**: (GUI) Run generated commands directly from the interface.
- **Copy to Clipboard**: (GUI) Easily copy commands for use elsewhere.
- **API Key Management**: (GUI) Securely store and manage your Google Gemini API key.
- **Customizable Themes**: (GUI) Supports both Dark (default) and Light modes.
- **Verbose Logging Toggle**: (GUI) Control the amount of system/debug information displayed.
- **Cross-Platform Potential**: Built with Python and PyQt5.

## How to Get a Gemini API Key

1.  Visit [Google AI Studio](https://aistudio.google.com/).
2.  Sign in with your Google account.
3.  Navigate to "API keys" in the left sidebar.
4.  Click "Create API key" and copy the generated key.

## Using the Command-Line Interface (CLI)

The core logic of the assistant is also available as a CLI tool, perfect for scripting or quick terminal use. This is the backend used by the GUI.

### Prerequisites (CLI)

- Python 3.7+ (Python 3.12 recommended for building the GUI).
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
    Ensure you have a `requirements.txt` file in the root directory. For the CLI backend, it should primarily contain:
    ```txt
    google-generativeai>=0.5.0
    # colorama>=0.4.4 # If your backend_cli.py uses it for colored output
    # argparse # Standard library, but good to note if extensively used
    ```
    Then install:
    ```bash
    pip install -r requirements.txt
    ```
    (For building/running the GUI from source, `PyQt5>=5.15.0` would also be needed in `requirements.txt`).

4.  **Set API Key (CLI):**
    The CLI backend (`src/backend_cli.py`) expects the `GOOGLE_API_KEY` environment variable.
    ```bash
    export GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
    ```
    For permanent setting, add this to your shell's configuration file (e.g., `.bashrc`, `.zshrc`).

### CLI Usage Examples

*(These commands assume you are in the root directory of the cloned repository)*

```bash
# Run the backend CLI script directly (ensure it's executable or use python3)
# This is primarily for testing the backend or if you prefer CLI interaction.
python3 src/backend_cli.py --query "show disk usage in human readable format" --json

python3 src/backend_cli.py --query "list all pdf files in home directory" --json```
*(Note: The `backend_cli.py` script is designed to be called by the GUI or for specific command generation. It might not have an interactive mode by itself unless you've added one.)*

## Building the GUI Application from Source

If you want to build the GUI application yourself:

### Prerequisites (Building GUI)

- All prerequisites for CLI.
- PyQt5: `PyQt5>=5.15.0` (should be in your `requirements.txt`).
- PyInstaller: `pip install pyinstaller`

### Build Steps

1.  Ensure your project is set up as described in "Setup (CLI)" and all dependencies (including `PyQt5` and `pyinstaller`) are installed in your virtual environment.
2.  Navigate to the project's root directory (`linux_ai_terminal_assistant`).
3.  Run PyInstaller (ensure your GUI script is named `linux_ai_assistant_gui.py` and your backend script `src/backend_cli.py`. The `app_icon.png` should also be in the root directory):
    ```bash
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
    ```
4.  The executable will be in the `dist` folder (e.g., `dist/Linux AI Assistant`).

## License

This project is created by Krzysztof Żuchowski.
Copyright © 2025 Krzysztof Żuchowski. All rights reserved.

Licensed under the [MIT License](LICENSE.md).

---

Made with ❤️ and Python.
