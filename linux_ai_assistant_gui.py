#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# --- SPRAWDZENIE TRYBU URUCHOMIENIA ---
# Ta sekcja musi być PRZED importami specyficznymi dla GUI (jak PyQt5)
# aby uniknąć niepotrzebnego ładowania ciężkich bibliotek w trybie backendu.
_IS_BACKEND_MODE = os.environ.get("LAA_BACKEND_MODE") == "1"

if _IS_BACKEND_MODE:
    # Jesteśmy w trybie backendu.
    # Ten kod zostanie wykonany, gdy zamrożona aplikacja (sys.executable)
    # zostanie uruchomiona z ustawioną zmienną LAA_BACKEND_MODE.
    try:
        # Dodajemy ścieżkę do spakowanych modułów 'src', jeśli aplikacja jest zamrożona
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            backend_module_path = os.path.join(sys._MEIPASS, "src")
            if backend_module_path not in sys.path:
                sys.path.insert(0, backend_module_path)

        # Importujemy i uruchamiamy logikę backendu.
        # Zakładamy, że plik src/backend_cli.py istnieje i ma funkcję main().
        # Argumenty dla backend_cli.py (np. --query, --json) zostaną przekazane
        # przez QProcess i będą dostępne w sys.argv dla backend_cli.py.
        import backend_cli # Powinno znaleźć src/backend_cli.py
        backend_cli.main() # Wywołaj główną funkcję backendu
        sys.exit(0) # Zakończ pomyślnie
    except ImportError as e:
        # Krytyczny błąd, jeśli nie można zaimportować backendu
        print(f"FATAL BACKEND ERROR (ImportError): Cannot import backend_cli. {e}", file=sys.stderr)
        print(f"Current sys.path: {sys.path}", file=sys.stderr)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            print(f"MEIPASS/src content: {os.listdir(os.path.join(sys._MEIPASS, 'src')) if os.path.exists(os.path.join(sys._MEIPASS, 'src')) else 'src dir not found in MEIPASS'}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL BACKEND ERROR (Exception): {e}", file=sys.stderr)
        sys.exit(1)
# --- KONIEC SPRAWDZENIA TRYBU ---

# Jeśli _IS_BACKEND_MODE jest False, kontynuujemy z normalnym kodem GUI.
# Dopiero teraz importujemy ciężkie biblioteki GUI.
import json
from typing import Dict, Optional, List
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                            QLabel, QDialog, QTabWidget, QCheckBox, QMessageBox,
                            QAction, QMenu, QSystemTrayIcon, QStyle, QFileDialog,
                            QDialogButtonBox, QFormLayout, QGroupBox)
from PyQt5.QtGui import QFont, QIcon, QTextCursor, QColor, QPalette, QPixmap
from PyQt5.QtCore import Qt, QProcess, QSettings, QSize, pyqtSignal, QTimer, QProcessEnvironment

# Configuration paths
CONFIG_DIR = os.path.expanduser("~/.config/linux_ai_assistant")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")

# Default configuration
DEFAULT_CONFIG = {
    "api_keys": {
        "gemini": "",
        "openai": "",
        "anthropic": ""
    },
    "show_instructions": True,
    "theme": "dark",
    "max_history": 100
}

class ApiKeyDialog(QDialog):
    """Dialog for entering the Gemini API key"""
    def __init__(self, parent=None, api_key=""):
        super().__init__(parent)
        self.setWindowTitle("API Key Required")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        layout = QVBoxLayout(self)
        header_layout = QHBoxLayout()
        logo_label = QLabel()
        pixmap = self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(64, 64)
        logo_label.setPixmap(pixmap)
        header_layout.addWidget(logo_label)
        title_label = QLabel("Linux AI Assistant")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        instructions = QLabel(
            "<h3>Gemini API Key Required</h3>"
            "<p>To use this AI assistant, you need a Gemini API key from Google AI Studio.</p>"
            "<h4>How to get a Gemini API key:</h4>"
            "<ol>"
            "<li>Visit <a href='https://aistudio.google.com/'>https://aistudio.google.com/</a></li>"
            "<li>Sign in with your Google account</li>"
            "<li>Navigate to 'API keys' in the left sidebar</li>"
            "<li>Click 'Create API key' and copy the generated key</li>"
            "</ol>"
            "<p>Your API key will be stored locally and used only for communicating with the Gemini API.</p>"
        )
        instructions.setOpenExternalLinks(True)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit(api_key)
        self.api_key_input.setPlaceholderText("Enter your Gemini API key here")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        key_layout.addWidget(self.api_key_input)
        layout.addLayout(key_layout)
        show_key_layout = QHBoxLayout()
        self.show_key_checkbox = QCheckBox("Show API key")
        self.show_key_checkbox.stateChanged.connect(self.toggle_key_visibility)
        show_key_layout.addWidget(self.show_key_checkbox)
        show_key_layout.addStretch()
        layout.addLayout(show_key_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def toggle_key_visibility(self, state):
        self.api_key_input.setEchoMode(QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password)

    def get_api_key(self):
        return self.api_key_input.text().strip()

class InstructionsDialog(QDialog):
    def __init__(self, parent=None, show_again=True):
        super().__init__(parent)
        self.setWindowTitle("Linux AI Assistant - Instructions")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        layout = QVBoxLayout(self)
        instructions = QLabel(
            "<h2>Welcome to Linux AI Assistant</h2>"
            "<p>This assistant helps you with Linux commands by understanding your natural language requests.</p>"
            "<h3>How to use:</h3>"
            "<ol>"
            "<li>Type your request in natural language (e.g., 'Show all running processes')</li>"
            "<li>The assistant will generate a suitable Linux command</li>"
            "<li>Review the command and its explanation</li>"
            "<li>Click 'Execute' to run the command or 'Copy' to copy it to clipboard</li>"
            "</ol>"
            "<h3>Example requests:</h3>"
            "<ul>"
            "<li>Show disk usage in human-readable format</li>"
            "<li>Find all PDF files in my home directory</li>"
            "<li>Check system memory usage</li>"
            "<li>List all installed packages</li>"
            "</ul>"
            "<p>You can access settings by clicking the gear icon in the top-right corner.</p>"
        )
        instructions.setOpenExternalLinks(True)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        self.show_again_checkbox = QCheckBox("Do not show this again")
        self.show_again_checkbox.setChecked(not show_again)
        layout.addWidget(self.show_again_checkbox)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def should_show_again(self):
        return not self.show_again_checkbox.isChecked()

class SettingsDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.config = config if config else DEFAULT_CONFIG.copy()
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        api_keys_tab = QWidget()
        api_keys_layout = QVBoxLayout(api_keys_tab)
        gemini_group = QGroupBox("Gemini API")
        gemini_form_layout = QFormLayout(gemini_group) # Użyj QFormLayout dla groupboxa
        self.gemini_key_input = QLineEdit(self.config["api_keys"].get("gemini", ""))
        self.gemini_key_input.setEchoMode(QLineEdit.Password)
        gemini_form_layout.addRow("API Key:", self.gemini_key_input)
        gemini_show_key = QCheckBox("Show API key")
        gemini_show_key.stateChanged.connect(lambda state, inp=self.gemini_key_input: self.toggle_key_visibility_static(state, inp))
        gemini_form_layout.addRow("", gemini_show_key)
        api_keys_layout.addWidget(gemini_group)

        openai_group = QGroupBox("OpenAI API")
        openai_form_layout = QFormLayout(openai_group)
        self.openai_key_input = QLineEdit(self.config["api_keys"].get("openai", ""))
        self.openai_key_input.setEchoMode(QLineEdit.Password)
        openai_form_layout.addRow("API Key:", self.openai_key_input)
        openai_show_key = QCheckBox("Show API key")
        openai_show_key.stateChanged.connect(lambda state, inp=self.openai_key_input: self.toggle_key_visibility_static(state, inp))
        openai_form_layout.addRow("", openai_show_key)
        api_keys_layout.addWidget(openai_group)

        anthropic_group = QGroupBox("Anthropic API")
        anthropic_form_layout = QFormLayout(anthropic_group)
        self.anthropic_key_input = QLineEdit(self.config["api_keys"].get("anthropic", ""))
        self.anthropic_key_input.setEchoMode(QLineEdit.Password)
        anthropic_form_layout.addRow("API Key:", self.anthropic_key_input)
        anthropic_show_key = QCheckBox("Show API key")
        anthropic_show_key.stateChanged.connect(lambda state, inp=self.anthropic_key_input: self.toggle_key_visibility_static(state, inp))
        anthropic_form_layout.addRow("", anthropic_show_key)
        api_keys_layout.addWidget(anthropic_group)
        api_keys_layout.addStretch()
        tabs.addTab(api_keys_tab, "API Keys")

        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        self.show_instructions_checkbox = QCheckBox("Show instructions on startup")
        self.show_instructions_checkbox.setChecked(self.config.get("show_instructions", True))
        general_layout.addWidget(self.show_instructions_checkbox)
        theme_group = QGroupBox("Theme")
        theme_form_layout = QFormLayout(theme_group) # Użyj QFormLayout dla lepszego wyglądu
        self.theme_dark_checkbox = QCheckBox("Dark mode") # Zmień nazwę dla jasności
        self.theme_dark_checkbox.setChecked(self.config.get("theme", "dark") == "dark")
        theme_form_layout.addRow(self.theme_dark_checkbox) # Dodaj do form layout
        general_layout.addWidget(theme_group)
        general_layout.addStretch()
        tabs.addTab(general_tab, "General")
        layout.addWidget(tabs)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    @staticmethod # Metoda statyczna, bo nie używa self specyficznie dla SettingsDialog
    def toggle_key_visibility_static(state, input_field):
        input_field.setEchoMode(QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password)

    def get_config(self):
        self.config["api_keys"]["gemini"] = self.gemini_key_input.text().strip()
        self.config["api_keys"]["openai"] = self.openai_key_input.text().strip()
        self.config["api_keys"]["anthropic"] = self.anthropic_key_input.text().strip()
        self.config["show_instructions"] = self.show_instructions_checkbox.isChecked()
        self.config["theme"] = "dark" if self.theme_dark_checkbox.isChecked() else "light"
        return self.config

class TerminalWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Monospace", 10)) # Domyślna czcionka
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setObjectName("TerminalWidget")
        self.colors = {
            "system": QColorConstants.Gray, # Użyj predefiniowanych kolorów Qt
            "user": QColorConstants.White,
            "assistant": QColorConstants.Green,
            "command": QColorConstants.Yellow,
            "error": QColorConstants.Red,
            "success": QColorConstants.Green
        }

    def append_message(self, text, message_type="system"):
        self.moveCursor(QTextCursor.End)
        cursor = self.textCursor()
        char_format = cursor.charFormat()
        # Użyj palety dla koloru tekstu, jeśli motyw go nadpisuje, w przeciwnym razie użyj self.colors
        text_color = self.palette().color(QPalette.Text)
        if message_type in self.colors:
            # Sprawdź czy kolor z self.colors jest "ważniejszy" niż domyślny z palety
            # W tym przypadku, nasze zdefiniowane kolory są ważniejsze
             text_color = self.colors.get(message_type, text_color)

        char_format.setForeground(text_color)
        cursor.setCharFormat(char_format)
        cursor.insertText(text + "\n")
        self.moveCursor(QTextCursor.End)
        self.ensureCursorVisible()


class LinuxAIAssistantGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self._theme_applied_once = False # Flaga dla komunikatów powitalnych
        self.current_command = "" # Inicjalizuj atrybut
        self.process = None # Inicjalizuj QProcess
        self.exec_process = None # Inicjalizuj QProcess

        self.init_config()
        self.init_ui()
        self.apply_theme() # Musi być po init_ui

        self.check_api_key() # Po apply_theme, żeby dialogi też miały styl
        if self.config.get("show_instructions", True):
            QTimer.singleShot(200, self.show_instructions) # Krótkie opóźnienie

    def init_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading configuration: {e}", file=sys.stderr)
                self.config = DEFAULT_CONFIG.copy()
        else:
            self.config = DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving configuration: {e}", file=sys.stderr)

    def init_ui(self):
        self.setWindowTitle("Linux AI Assistant")
        self.setMinimumSize(800, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.terminal = TerminalWidget()
        main_layout.addWidget(self.terminal)

        input_layout = QHBoxLayout()
        self.prompt_label = QLabel("> ")
        self.prompt_label.setObjectName("PromptLabel")
        input_layout.addWidget(self.prompt_label)
        self.input_field = QLineEdit()
        self.input_field.setObjectName("InputField")
        self.input_field.returnPressed.connect(self.process_input)
        input_layout.addWidget(self.input_field)
        main_layout.addLayout(input_layout)

        self.command_widget = QWidget()
        command_layout = QVBoxLayout(self.command_widget)
        self.command_header_label = QLabel("Generated Command:")
        self.command_header_label.setObjectName("CommandHeaderLabel")
        command_layout.addWidget(self.command_header_label)
        self.command_display = QTextEdit()
        self.command_display.setObjectName("CommandDisplay")
        self.command_display.setReadOnly(True)
        self.command_display.setMaximumHeight(100)
        command_layout.addWidget(self.command_display)
        self.explanation_header_label = QLabel("Explanation:")
        self.explanation_header_label.setObjectName("ExplanationHeaderLabel")
        command_layout.addWidget(self.explanation_header_label)
        self.explanation_display = QTextEdit()
        self.explanation_display.setObjectName("ExplanationDisplay")
        self.explanation_display.setReadOnly(True)
        self.explanation_display.setMaximumHeight(100)
        command_layout.addWidget(self.explanation_display)
        button_layout = QHBoxLayout()
        self.execute_button = QPushButton("Execute")
        button_layout.addWidget(self.execute_button)
        self.copy_button = QPushButton("Copy")
        button_layout.addWidget(self.copy_button)
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_button)
        command_layout.addLayout(button_layout)
        main_layout.addWidget(self.command_widget)
        self.command_widget.hide()

        self.execute_button.clicked.connect(self.execute_command)
        self.copy_button.clicked.connect(self.copy_command)
        self.cancel_button.clicked.connect(self.cancel_command)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        instructions_action = QAction("Instructions", self)
        instructions_action.triggered.connect(self.show_instructions)
        file_menu.addAction(instructions_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        toolbar = self.addToolBar("Toolbar")
        toolbar.setMovable(False); toolbar.setFloatable(False)
        spacer_widget = QWidget(); spacer_widget.setSizePolicy(QApplication.style().standardIcon(QStyle.SP_TitleBarMaxButton).actualSize(QSize(16,16)).width(), QApplication.style().standardIcon(QStyle.SP_TitleBarMaxButton).actualSize(QSize(16,16)).height()) #QSizePolicy.Expanding, QSizePolicy.Preferred) #QHBoxLayout.Expanding, QHBoxLayout.Preferred) #QWidget.Expanding, QWidget.Preferred)
        toolbar.addWidget(spacer_widget)
        self.settings_button_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Settings", self)
        self.settings_button_action.triggered.connect(self.show_settings)
        toolbar.addAction(self.settings_button_action)


    def apply_theme(self):
        dark_theme = self.config.get("theme", "dark") == "dark"

        base_bg = "#282A36" if dark_theme else "#F0F0F0"
        base_fg = "#F8F8F2" if dark_theme else "#333333"
        alt_bg_terminal = "#1E1E1E" if dark_theme else "#FFFFFF" # Dla terminala i inputu
        alt_fg_terminal_user = "#F8F8F2" if dark_theme else "#000000"

        border_color = "#44475A" if dark_theme else "#CCCCCC"
        button_bg = "#44475A" if dark_theme else "#E0E0E0"
        button_hover_bg = "#6272A4" if dark_theme else "#D0D0D0"
        button_pressed_bg = "#50FA7B"; button_pressed_fg = "#282A36"

        # Aktualizacja palety kolorów dla TerminalWidget (wpłynie na append_message)
        self.terminal.colors["system"] = QColor("#B0B0B0") if dark_theme else QColor("#707070")
        self.terminal.colors["user"] = QColor(alt_fg_terminal_user)
        self.terminal.colors["assistant"] = QColor("#66FF66")
        self.terminal.colors["command"] = QColor("#FFC266") # Lepszy kontrast dla komendy
        self.terminal.colors["error"] = QColor("#FF6666")   # Lepszy kontrast dla błędu
        self.terminal.colors["success"] = QColor("#66FF99")

        prompt_label_color = self.terminal.colors["assistant"].name()
        command_header_color = self.terminal.colors["command"].name()
        explanation_header_color = QColor("#8BE9FD").name() if dark_theme else QColor("#1AA0D5")

        qss = f"""
            QMainWindow, QDialog {{ background-color: {base_bg}; color: {base_fg}; }}
            QMenuBar {{ background-color: {base_bg}; color: {base_fg}; }}
            QMenuBar::item:selected {{ background-color: {button_bg}; }}
            QMenu {{ background-color: {base_bg}; color: {base_fg}; border: 1px solid {border_color}; }}
            QMenu::item:selected {{ background-color: {button_bg}; }}
            QToolBar {{ background-color: {base_bg}; border: none; }}
            QPushButton {{
                background-color: {button_bg}; color: {base_fg};
                border: 1px solid {border_color}; padding: 5px 10px; border-radius: 3px;
            }}
            QPushButton:hover {{ background-color: {button_hover_bg}; }}
            QPushButton:pressed {{ background-color: {button_pressed_bg}; color: {button_pressed_fg}; }}

            QLabel#PromptLabel {{ color: {prompt_label_color}; font-family: Monospace; font-size: 10pt; }}
            QLabel#CommandHeaderLabel {{ color: {command_header_color}; font-weight: bold; }}
            QLabel#ExplanationHeaderLabel {{ color: {explanation_header_color}; font-weight: bold; }}
            /* Domyślny QLabel, jeśli inne nie pasują */
            QLabel {{ color: {base_fg}; }}

            QTabWidget::pane {{ border: 1px solid {border_color}; background-color: {base_bg}; }}
            QTabBar::tab {{
                background-color: {base_bg}; color: {base_fg}; padding: 5px 10px;
                border: 1px solid {border_color}; border-bottom: none;
                border-top-left-radius: 3px; border-top-right-radius: 3px;
            }}
            QTabBar::tab:selected {{ background-color: {button_bg}; }}
            QGroupBox {{
                border: 1px solid {border_color}; margin-top: 1ex; color: {base_fg};
                border-radius: 3px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }}

            QLineEdit {{ /* Ogólny QLineEdit */
                background-color: {alt_bg_terminal}; color: {alt_fg_terminal_user};
                border: 1px solid {border_color}; padding: 4px; border-radius: 3px;
            }}
            QLineEdit#InputField {{
                background-color: {alt_bg_terminal}; color: {alt_fg_terminal_user};
                border: none; font-family: Monospace; font-size: 10pt; padding: 5px;
            }}
            QCheckBox {{ color: {base_fg}; }}
            QTextEdit#TerminalWidget {{ background-color: {alt_bg_terminal}; border: none; }}
            QTextEdit#CommandDisplay, QTextEdit#ExplanationDisplay {{
                background-color: {'#2C2F3A' if dark_theme else '#FAFAFA'}; /* Lekko inne tło dla tych pól */
                border: 1px solid {border_color}; border-radius: 3px;
                font-family: Monospace; font-size: 10pt; padding: 3px;
            }}
            QTextEdit#CommandDisplay {{ color: {command_header_color}; }}
            QTextEdit#ExplanationDisplay {{ color: {explanation_header_color}; }}
        """
        self.setStyleSheet(qss)
        QApplication.instance().setFont(QFont("Noto Sans", 9)) # Ustawienie domyślnej czcionki dla całej aplikacji

        if not self._theme_applied_once:
            self.terminal.append_message("=== Linux AI Assistant ===", "system")
            self.terminal.append_message("Type your request in natural language or 'help' for instructions.", "system")
            self.terminal.append_message("", "system") # Pusta linia dla odstępu
            self._theme_applied_once = True
        else:
            # Odśwież istniejący tekst terminala (prosta implementacja)
            # To może być kosztowne dla długiej historii, ale dla celów demonstracyjnych:
            all_text = self.terminal.toPlainText()
            self.terminal.clear()
            # Ponowne dodanie linii wymagałoby zachowania typu wiadomości, upraszczamy:
            # self.terminal.setPlainText(all_text) # To straci kolory
            # Zamiast tego, pozwólmy append_message ustawiać kolory przy nowych wiadomościach.
            # Można by też zaktualizować paletę TerminalWidget.
            palette = self.terminal.palette()
            palette.setColor(QPalette.Text, QColor(alt_fg_terminal_user if dark_theme else base_fg))
            palette.setColor(QPalette.Base, QColor(alt_bg_terminal))
            self.terminal.setPalette(palette)


    def check_api_key(self):
        gemini_key = self.config["api_keys"].get("gemini", "")
        if not gemini_key:
            QTimer.singleShot(100, self.prompt_for_api_key)

    def prompt_for_api_key(self):
        dialog = ApiKeyDialog(self, self.config["api_keys"].get("gemini", ""))
        if dialog.exec_():
            api_key = dialog.get_api_key()
            if api_key:
                self.config["api_keys"]["gemini"] = api_key
                self.save_config()
                self.terminal.append_message("API key configured successfully.", "success")
            else:
                self.terminal.append_message("API key is required to use the assistant.", "error")
                QTimer.singleShot(1000, self.prompt_for_api_key)

    def show_instructions(self):
        dialog = InstructionsDialog(self, self.config.get("show_instructions", True))
        if dialog.exec_(): # Sprawdź czy dialog został zaakceptowany
            self.config["show_instructions"] = dialog.should_show_again()
            self.save_config()

    def show_settings(self):
        dialog = SettingsDialog(self, self.config.copy()) # Przekaż kopię, aby anulowanie nie zmieniało configu
        if dialog.exec_():
            self.config = dialog.get_config()
            self.save_config()
            self.apply_theme()
            self.terminal.append_message("Settings updated successfully.", "success")

    def show_about(self):
        QMessageBox.about(self, "About Linux AI Assistant",
                         "<h3>Linux AI Assistant</h3>"
                         "<p>Version 1.0</p>"
                         "<p>A terminal-style GUI for the Linux AI Assistant with API key management.</p>"
                         "<p>This application helps you generate and execute Linux commands using natural language.</p>"
                         "<p><a href='https://buymeacoffee.com/krzyzu.83'>Buy me a coffee</a></p>")

    def process_input(self):
        user_input = self.input_field.text().strip()
        if not user_input: return
        self.input_field.clear()
        self.terminal.append_message(f"> {user_input}", "user")

        if user_input.lower() in ["exit", "quit"]: self.close(); return
        if user_input.lower() == "help": self.show_instructions(); return
        if user_input.lower() == "settings": self.show_settings(); return

        if not self.config["api_keys"].get("gemini", ""):
            self.terminal.append_message("API key is not configured. Please configure it in settings.", "error")
            self.prompt_for_api_key()
            return

        self.terminal.append_message("Processing query...", "system")
        if self.process and self.process.state() == QProcess.Running:
            self.terminal.append_message("A backend process is already running. Please wait.", "error")
            return

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(lambda ec, es: self.process_finished(ec, es))

        env = QProcessEnvironment.systemEnvironment()
        env.insert("GOOGLE_API_KEY", self.config["api_keys"]["gemini"])
        env.insert("LAA_BACKEND_MODE", "1") # Kluczowe dla PyInstallera
        self.process.setProcessEnvironment(env)

        executable_to_run = ""
        args_for_executable = []

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            executable_to_run = sys.executable # Binarka GUI
            # Argumenty dla logiki backendu wewnątrz binarki GUI
            args_for_executable = ["--query", user_input, "--json"]
            # Sprawdzenie czy backend_cli.py jest spakowany
            backend_script_in_bundle = os.path.join(sys._MEIPASS, "src", "backend_cli.py")
            if not os.path.exists(backend_script_in_bundle):
                self.terminal.append_message(f"CRITICAL: Packaged backend_cli.py not found at {backend_script_in_bundle}", "error")
                return
        else: # Tryb deweloperski
            executable_to_run = sys.executable # Lub "python3"
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "backend_cli.py")
            if not os.path.exists(script_path):
                self.terminal.append_message(f"CRITICAL: Development backend_cli.py not found at {script_path}", "error")
                return
            args_for_executable = [script_path, "--query", user_input, "--json"]

        self.terminal.append_message(f"Cmd: {executable_to_run} {' '.join(args_for_executable)}", "system")
        self.process.start(executable_to_run, args_for_executable)
        if not self.process.waitForStarted(5000):
            self.terminal.append_message(f"Error starting backend: {self.process.errorString()}", "error")

    def handle_stdout(self):
        if not self.process: return
        raw_data = self.process.readAllStandardOutput().data().decode().strip()
        if not raw_data: return
        self.terminal.append_message(f"Backend STDOUT: {raw_data}", "system")
        try:
            result = json.loads(raw_data)
            if result.get("success", False):
                self.command_display.setText(result.get("command", "N/A"))
                self.explanation_display.setText(result.get("explanation", "N/A"))
                self.command_widget.show()
                self.current_command = result.get("command", "")
            else:
                self.terminal.append_message(f"Backend Error (JSON): {result.get('error', 'Unknown')}", "error")
                self.command_widget.hide()
        except json.JSONDecodeError:
            self.terminal.append_message(f"Backend (non-JSON): {raw_data}", "error")
            self.command_widget.hide()

    def handle_stderr(self):
        if not self.process: return
        raw_data = self.process.readAllStandardError().data().decode().strip()
        if raw_data:
            self.terminal.append_message(f"Backend STDERR: {raw_data}", "error")

    def process_finished(self, exit_code, exit_status):
        status = "normally" if exit_status == QProcess.NormalExit else "with a crash"
        self.terminal.append_message(f"Backend process finished {status}, exit code: {exit_code}.", "system")
        if exit_code != 0 and not self.command_widget.isVisible():
             self.terminal.append_message(f"Backend may have failed. Check messages above.", "error")


    def execute_command(self):
        if not self.current_command: return
        self.command_widget.hide()
        self.terminal.append_message(f"Executing: {self.current_command}", "command")
        self.exec_process = QProcess(self)
        self.exec_process.readyReadStandardOutput.connect(self.handle_exec_stdout)
        self.exec_process.readyReadStandardError.connect(self.handle_exec_stderr)
        self.exec_process.finished.connect(lambda ec, es: self.exec_process_finished(ec, es))
        self.exec_process.start("bash", ["-c", self.current_command])

    def handle_exec_stdout(self):
        if not self.exec_process: return
        data = self.exec_process.readAllStandardOutput().data().decode().strip()
        if data: self.terminal.append_message(data, "system")

    def handle_exec_stderr(self):
        if not self.exec_process: return
        data = self.exec_process.readAllStandardError().data().decode().strip()
        if data: self.terminal.append_message(data, "error")

    def exec_process_finished(self, exit_code, exit_status):
        status = "successfully" if exit_code == 0 and exit_status == QProcess.NormalExit else f"with code {exit_code}"
        msg_type = "success" if exit_code == 0 and exit_status == QProcess.NormalExit else "error"
        self.terminal.append_message(f"Command execution finished {status}.", msg_type)


    def copy_command(self):
        if not self.current_command: return
        QApplication.clipboard().setText(self.current_command)
        self.terminal.append_message("Command copied to clipboard.", "success")

    def cancel_command(self):
        self.command_widget.hide()
        self.current_command = ""
        self.terminal.append_message("Command cancelled.", "system")


def main_gui_entry_point(): # Zmieniono nazwę, aby była unikalna
    app = QApplication(sys.argv)
    # Ustawienie domyślnej czcionki dla aplikacji, jeśli potrzebne
    # default_font = QFont("Noto Sans", 9) # Wybierz odpowiednią czcionkę i rozmiar
    # app.setFont(default_font)
    window = LinuxAIAssistantGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Ta część kodu zostanie wykonana tylko wtedy, gdy LAA_BACKEND_MODE nie jest ustawione.
    # W przeciwnym razie, kod na samej górze pliku obsłuży tryb backendu i zakończy działanie.
    if not _IS_BACKEND_MODE:
        # Dodano QColorConstants do importów, jeśli nie ma
        try:
            from PyQt5.QtGui import QColorConstants
        except ImportError:
            # Prosty fallback, jeśli QColorConstants nie jest dostępne (starsze PyQt5?)
            class QColorConstants:
                Gray = QColor("gray")
                White = QColor("white")
                Green = QColor("green")
                Yellow = QColor("yellow")
                Red = QColor("red")
        main_gui_entry_point()
