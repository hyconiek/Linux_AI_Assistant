#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# --- SPRAWDZENIE TRYBU URUCHOMIENIA ---
_IS_BACKEND_MODE = os.environ.get("LAA_BACKEND_MODE") == "1"

if _IS_BACKEND_MODE:
    try:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            backend_module_path = os.path.join(sys._MEIPASS, "src")
            if backend_module_path not in sys.path:
                sys.path.insert(0, backend_module_path)
        import backend_cli
        backend_cli.main()
        sys.exit(0)
    except ImportError as e:
        print(f"FATAL BACKEND ERROR (ImportError): Cannot import backend_cli. {e}", file=sys.stderr)
        print(f"Current sys.path: {sys.path}", file=sys.stderr)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            src_in_meipass = os.path.join(sys._MEIPASS, 'src')
            if os.path.exists(src_in_meipass) and os.path.isdir(src_in_meipass):
                print(f"MEIPASS/src content: {os.listdir(src_in_meipass)}", file=sys.stderr)
            else:
                print(f"MEIPASS/src dir not found or is not a directory: {src_in_meipass}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL BACKEND ERROR (Exception): {e}", file=sys.stderr)
        sys.exit(1)
# --- KONIEC SPRAWDZENIA TRYBU ---

import json
from typing import Dict, Optional, List
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                            QLabel, QDialog, QTabWidget, QCheckBox, QMessageBox,
                            QAction, QMenu, QStyle, QFileDialog,
                            QDialogButtonBox, QFormLayout, QGroupBox, QSizePolicy)
from PyQt5.QtGui import QFont, QIcon, QTextCursor, QColor, QPalette, QPixmap
# QColorConstants zaimportujemy w main_gui_entry_point z fallbackiem
from PyQt5.QtCore import Qt, QProcess, QSettings, QSize, pyqtSignal, QTimer, QProcessEnvironment

# Configuration paths
CONFIG_DIR = os.path.expanduser("~/.config/linux_ai_assistant")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.json")

# Default configuration
DEFAULT_CONFIG = {
    "api_keys": {"gemini": "", "openai": "", "anthropic": ""},
    "show_instructions": True,
    "theme": "dark",
    "max_history": 100,
    "verbose_logging": True
}

class ApiKeyDialog(QDialog):
    def __init__(self, parent=None, api_key=""):
        super().__init__(parent)
        self.setWindowTitle("API Key Required")
        self.setMinimumWidth(500); self.setMinimumHeight(400)
        layout = QVBoxLayout(self); header_layout = QHBoxLayout()
        logo_label = QLabel(); pixmap = self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(64, 64)
        logo_label.setPixmap(pixmap); header_layout.addWidget(logo_label)
        title_label = QLabel("Linux AI Assistant"); title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label); header_layout.addStretch(); layout.addLayout(header_layout)
        instructions = QLabel(
            "<h3>Gemini API Key Required</h3><p>To use this AI assistant, you need a Gemini API key from Google AI Studio.</p>"
            "<h4>How to get a Gemini API key:</h4><ol><li>Visit <a href='https://aistudio.google.com/'>https://aistudio.google.com/</a></li>"
            "<li>Sign in with your Google account</li><li>Navigate to 'API keys' in the left sidebar</li>"
            "<li>Click 'Create API key' and copy the generated key</li></ol>"
            "<p>Your API key will be stored locally and used only for communicating with the Gemini API.</p>"
        )
        instructions.setOpenExternalLinks(True); instructions.setWordWrap(True); layout.addWidget(instructions)
        key_layout = QHBoxLayout(); key_layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit(api_key); self.api_key_input.setPlaceholderText("Enter your Gemini API key here")
        self.api_key_input.setEchoMode(QLineEdit.Password); key_layout.addWidget(self.api_key_input); layout.addLayout(key_layout)
        show_key_layout = QHBoxLayout(); self.show_key_checkbox = QCheckBox("Show API key")
        self.show_key_checkbox.stateChanged.connect(self.toggle_key_visibility)
        show_key_layout.addWidget(self.show_key_checkbox); show_key_layout.addStretch(); layout.addLayout(show_key_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept); button_box.rejected.connect(self.reject); layout.addWidget(button_box)

    def toggle_key_visibility(self, state): self.api_key_input.setEchoMode(QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password)
    def get_api_key(self): return self.api_key_input.text().strip()

class InstructionsDialog(QDialog):
    def __init__(self, parent=None, show_again=True):
        super().__init__(parent)
        self.setWindowTitle("Linux AI Assistant - Instructions"); self.setMinimumWidth(600); self.setMinimumHeight(500)
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
        instructions.setOpenExternalLinks(True); instructions.setWordWrap(True); layout.addWidget(instructions)
        self.show_again_checkbox = QCheckBox("Do not show this again"); self.show_again_checkbox.setChecked(not show_again)
        layout.addWidget(self.show_again_checkbox)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok); button_box.accepted.connect(self.accept); layout.addWidget(button_box)
    def should_show_again(self): return not self.show_again_checkbox.isChecked()

class SettingsDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("Settings"); self.setMinimumWidth(500); self.setMinimumHeight(400)
        self.config = config if config else DEFAULT_CONFIG.copy() # Użyj .copy() dla bezpieczeństwa
        layout = QVBoxLayout(self); tabs = QTabWidget(); api_keys_tab = QWidget()
        api_keys_layout = QVBoxLayout(api_keys_tab)
        for api_name in ["Gemini", "OpenAI", "Anthropic"]:
            group = QGroupBox(f"{api_name} API"); form_layout = QFormLayout(group)
            key_input = QLineEdit(self.config["api_keys"].get(api_name.lower(), "")); key_input.setEchoMode(QLineEdit.Password)
            setattr(self, f"{api_name.lower()}_key_input", key_input)
            form_layout.addRow("API Key:", key_input)
            show_key_cb = QCheckBox("Show API key")
            show_key_cb.stateChanged.connect(lambda state, inp=key_input: self.toggle_key_visibility_static(state, inp))
            form_layout.addRow("", show_key_cb); api_keys_layout.addWidget(group)
        api_keys_layout.addStretch(); tabs.addTab(api_keys_tab, "API Keys")
        general_tab = QWidget(); general_layout = QVBoxLayout(general_tab)
        self.show_instructions_checkbox = QCheckBox("Show instructions on startup")
        self.show_instructions_checkbox.setChecked(self.config.get("show_instructions", True)); general_layout.addWidget(self.show_instructions_checkbox)
        theme_group = QGroupBox("Theme"); theme_form = QFormLayout(theme_group)
        self.theme_dark_checkbox = QCheckBox("Dark mode")
        self.theme_dark_checkbox.setChecked(self.config.get("theme", "dark") == "dark")
        theme_form.addRow(self.theme_dark_checkbox); general_layout.addWidget(theme_group)
        general_layout.addStretch(); tabs.addTab(general_tab, "General")
        layout.addWidget(tabs)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept); button_box.rejected.connect(self.reject); layout.addWidget(button_box)
    @staticmethod
    def toggle_key_visibility_static(state, input_field): input_field.setEchoMode(QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password)
    def get_config(self): # Zwraca nowy słownik config, nie modyfikuje self.config bezpośrednio
        updated_config = self.config.copy() # Pracuj na kopii
        for api_name_lower in ["gemini", "openai", "anthropic"]:
            key_input_widget = getattr(self, f"{api_name_lower}_key_input", None)
            if key_input_widget: updated_config["api_keys"][api_name_lower] = key_input_widget.text().strip()
        updated_config["show_instructions"] = self.show_instructions_checkbox.isChecked()
        updated_config["theme"] = "dark" if self.theme_dark_checkbox.isChecked() else "light"
        return updated_config

class TerminalWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True); self.setFont(QFont("Monospace", 10)); self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setObjectName("TerminalWidget")
        self.colors = { # Domyślne kolory, mogą być nadpisane przez apply_theme
            "system": QColor("#808080"), "user": QColor("#FFFFFF"), "assistant": QColor("#00FF00"),
            "command": QColor("#FFFF00"), "error": QColor("#FF0000"), "success": QColor("#00FF00")
        }
    def append_message(self, text, message_type="system"):
        self.moveCursor(QTextCursor.End); cursor = self.textCursor(); char_format = cursor.charFormat()
        text_color = self.palette().color(QPalette.Text)
        if message_type in self.colors: text_color = self.colors.get(message_type, text_color)
        char_format.setForeground(text_color); cursor.setCharFormat(char_format)
        cursor.insertText(text + "\n"); self.moveCursor(QTextCursor.End); self.ensureCursorVisible()

class LinuxAIAssistantGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self._theme_applied_once = False; self.current_command = ""; self.process = None; self.exec_process = None
        self.init_config()
        self.verbose_logging = self.config.get("verbose_logging", True)
        self.init_ui()
        self.apply_theme()
        self.check_api_key()
        if self.config.get("show_instructions", True): QTimer.singleShot(200, self.show_instructions)

    def init_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f: self.config = json.load(f)
            else: self.config = DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Error loading config: {e}", file=sys.stderr); self.config = DEFAULT_CONFIG.copy()
        self.config.setdefault("verbose_logging", DEFAULT_CONFIG["verbose_logging"]) # Użyj wartości domyślnej z DEFAULT_CONFIG

    def save_config(self):
        try:
            self.config["verbose_logging"] = self.verbose_logging
            with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=2)
        except Exception as e: print(f"Error saving config: {e}", file=sys.stderr)

    def init_ui(self):
        self.setWindowTitle("Linux AI Assistant"); self.setMinimumSize(800, 600)
        # --- SEKCJA IKONY ---
        icon_path = ""; icon_filename = "app_icon.png"
        base_path_for_icon = ""
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path_for_icon = sys._MEIPASS
            icon_path = os.path.join(base_path_for_icon, icon_filename)
            print(f"DEBUG (FROZEN): MEIPASS path: {base_path_for_icon}", file=sys.stderr)
            print(f"DEBUG (FROZEN): Trying icon path for setWindowIcon: {icon_path}", file=sys.stderr)
            try:
                if os.path.exists(base_path_for_icon): print(f"DEBUG (FROZEN): Contents of MEIPASS: {os.listdir(base_path_for_icon)}", file=sys.stderr)
                else: print(f"DEBUG (FROZEN): MEIPASS directory does not exist: {base_path_for_icon}", file=sys.stderr)
            except Exception as e: print(f"DEBUG (FROZEN): Error listing MEIPASS contents: {e}", file=sys.stderr)
        else:
            base_path_for_icon = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_path_for_icon, icon_filename)
            print(f"DEBUG (DEV): Base path for icon: {base_path_for_icon}", file=sys.stderr)
            print(f"DEBUG (DEV): Trying icon path for setWindowIcon: {icon_path}", file=sys.stderr)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            print(f"DEBUG: Window icon '{icon_filename}' SET from {icon_path}", file=sys.stderr)
        else:
            print(f"ERROR: Window icon '{icon_filename}' NOT FOUND at {icon_path}. Using default.", file=sys.stderr)
            self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        # --- KONIEC SEKCJI IKONY ---
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.terminal = TerminalWidget(); main_layout.addWidget(self.terminal)
        input_layout = QHBoxLayout(); self.prompt_label = QLabel("> "); self.prompt_label.setObjectName("PromptLabel")
        input_layout.addWidget(self.prompt_label); self.input_field = QLineEdit(); self.input_field.setObjectName("InputField")
        self.input_field.returnPressed.connect(self.process_input); input_layout.addWidget(self.input_field)
        main_layout.addLayout(input_layout)
        self.command_widget = QWidget(); command_layout = QVBoxLayout(self.command_widget)
        self.command_header_label = QLabel("Generated Command:"); self.command_header_label.setObjectName("CommandHeaderLabel")
        command_layout.addWidget(self.command_header_label); self.command_display = QTextEdit(); self.command_display.setObjectName("CommandDisplay")
        self.command_display.setReadOnly(True); self.command_display.setMaximumHeight(100); command_layout.addWidget(self.command_display)
        self.explanation_header_label = QLabel("Explanation:"); self.explanation_header_label.setObjectName("ExplanationHeaderLabel")
        command_layout.addWidget(self.explanation_header_label); self.explanation_display = QTextEdit(); self.explanation_display.setObjectName("ExplanationDisplay")
        self.explanation_display.setReadOnly(True); self.explanation_display.setMaximumHeight(100); command_layout.addWidget(self.explanation_display)
        button_layout = QHBoxLayout(); self.execute_button = QPushButton("Execute"); self.copy_button = QPushButton("Copy"); self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.execute_button); button_layout.addWidget(self.copy_button); button_layout.addWidget(self.cancel_button)
        command_layout.addLayout(button_layout); main_layout.addWidget(self.command_widget); self.command_widget.hide()
        self.execute_button.clicked.connect(self.execute_command); self.copy_button.clicked.connect(self.copy_command); self.cancel_button.clicked.connect(self.cancel_command)
        menubar = self.menuBar(); file_menu = menubar.addMenu("File")
        settings_act = QAction("Settings", self); settings_act.setShortcut("Ctrl+,"); settings_act.triggered.connect(self.show_settings); file_menu.addAction(settings_act)
        instr_act = QAction("Instructions", self); instr_act.triggered.connect(self.show_instructions); file_menu.addAction(instr_act)
        file_menu.addSeparator(); exit_act = QAction("Exit", self); exit_act.setShortcut("Ctrl+Q"); exit_act.triggered.connect(self.close); file_menu.addAction(exit_act)
        help_menu = menubar.addMenu("Help"); help_menu.addAction(QAction("About", self, triggered=self.show_about))
        toolbar = self.addToolBar("Toolbar"); toolbar.setMovable(False); toolbar.setFloatable(False)
        self.verbose_log_checkbox = QCheckBox("Verbose Log"); self.verbose_log_checkbox.setToolTip("Show detailed system messages")
        self.verbose_log_checkbox.setChecked(self.verbose_logging); self.verbose_log_checkbox.stateChanged.connect(self.toggle_verbose_logging)
        toolbar.addWidget(self.verbose_log_checkbox)
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred); toolbar.addWidget(spacer)
        self.settings_button_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Settings", self)
        self.settings_button_action.triggered.connect(self.show_settings); toolbar.addAction(self.settings_button_action)

    def apply_theme(self):
        dark_theme = self.config.get("theme", "dark") == "dark"
        base_bg = "#282A36" if dark_theme else "#F0F0F0"; base_fg = "#F8F8F2" if dark_theme else "#333333"
        alt_bg_terminal = "#1E1E1E" if dark_theme else "#FFFFFF"; alt_fg_terminal_user = "#F8F8F2" if dark_theme else "#000000"
        border_color = "#44475A" if dark_theme else "#CCCCCC"; button_bg = "#44475A" if dark_theme else "#E0E0E0"
        button_hover_bg = "#6272A4" if dark_theme else "#D0D0D0"; button_pressed_bg = "#50FA7B"; button_pressed_fg = "#282A36"
        self.terminal.colors["system"] = QColor("#B0B0B0") if dark_theme else QColor("#707070")
        self.terminal.colors["user"] = QColor(alt_fg_terminal_user); self.terminal.colors["assistant"] = QColor("#66FF66")
        self.terminal.colors["command"] = QColor("#FFC266"); self.terminal.colors["error"] = QColor("#FF6666"); self.terminal.colors["success"] = QColor("#66FF99")
        prompt_label_color = self.terminal.colors["assistant"].name(); command_header_color = self.terminal.colors["command"].name()
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
            QLineEdit {{
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
                background-color: {'#2C2F3A' if dark_theme else '#FAFAFA'};
                border: 1px solid {border_color}; border-radius: 3px;
                font-family: Monospace; font-size: 10pt; padding: 3px;
            }}
            QTextEdit#CommandDisplay {{ color: {command_header_color}; }}
            QTextEdit#ExplanationDisplay {{ color: {explanation_header_color}; }}
        """
        self.setStyleSheet(qss)
        app_font = QFont("Noto Sans", 10)
        QApplication.instance().setFont(app_font)
        if not self._theme_applied_once:
            self.log_message("=== Linux AI Assistant ===", "system", force_show=True)
            self.log_message("Type 'help' for instructions or a query.", "system", force_show=True)
            self.log_message("", "system")
            self._theme_applied_once = True
        else:
            palette = self.terminal.palette()
            palette.setColor(QPalette.Text, self.terminal.colors["user"])
            palette.setColor(QPalette.Base, QColor(alt_bg_terminal))
            self.terminal.setPalette(palette)

    def log_message(self, message: str, message_type: str = "system", force_show: bool = False):
        if message_type == "system" and not self.verbose_logging and not force_show: return
        self.terminal.append_message(message, message_type)

    def toggle_verbose_logging(self, state):
        self.verbose_logging = (state == Qt.Checked)
        self.save_config()
        self.log_message(f"Verbose logging {'enabled' if self.verbose_logging else 'disabled'}.", "system", force_show=True)

    def check_api_key(self):
        if not self.config["api_keys"].get("gemini", ""): QTimer.singleShot(100, self.prompt_for_api_key)

    def prompt_for_api_key(self):
        dialog = ApiKeyDialog(self, self.config["api_keys"].get("gemini", ""))
        if dialog.exec_():
            api_key = dialog.get_api_key()
            if api_key: self.config["api_keys"]["gemini"] = api_key; self.save_config(); self.terminal.append_message("API key configured.", "success")
            else: self.terminal.append_message("API key is required.", "error"); QTimer.singleShot(1000, self.prompt_for_api_key)

    def show_instructions(self):
        dialog = InstructionsDialog(self, self.config.get("show_instructions", True))
        if dialog.exec_(): self.config["show_instructions"] = dialog.should_show_again(); self.save_config()

    def show_settings(self):
        dialog = SettingsDialog(self, self.config.copy())
        if dialog.exec_():
            new_config = dialog.get_config()
            theme_changed = self.config.get("theme") != new_config.get("theme")
            self.verbose_logging = new_config.get("verbose_logging", self.verbose_logging) # Uaktualnij verbose_logging
            self.config = new_config
            self.save_config()
            if theme_changed: self.apply_theme()
            self.verbose_log_checkbox.setChecked(self.verbose_logging) # Uaktualnij stan checkboxa
            self.log_message("Settings updated.", "success", True)

    def show_about(self):
        QMessageBox.about(self, "About Linux AI Assistant",
            "<h3>Linux AI Assistant</h3><p>Version 1.0.1</p><p>Created by: Krzysztof Żuchowski</p>"
            "<p>© 2025 Krzysztof Żuchowski. All rights reserved.</p><p>Licensed under the MIT License.</p>"
            "<p>AI-powered command generation for Linux.</p><hr><p>Support the project:</p>"
            "<p><a href='https://www.buymeacoffee.com/krzyzu.83'>Buy me a coffee (krzyzu.83)</a></p>"
            "<p><a href='https://github.com/hyconiek/linux_ai_terminal_assistant'>Project on GitHub</a></p>")

    def process_input(self):
        user_input = self.input_field.text().strip();
        if not user_input: return
        self.input_field.clear(); self.log_message(f"> {user_input}", "user") # Zmieniono na log_message dla spójności, ale typ "user" zawsze się wyświetli
        if user_input.lower() in ["exit", "quit"]: self.close(); return
        if user_input.lower() == "help": self.show_instructions(); return
        if user_input.lower() == "settings": self.show_settings(); return
        if not self.config["api_keys"].get("gemini", ""):
            self.terminal.append_message("API key not set. Go to Settings.", "error"); self.prompt_for_api_key(); return
        self.log_message("Processing query...", "system")
        if self.process and self.process.state() == QProcess.Running:
            self.log_message("Backend busy. Please wait.", "error", True); return
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(lambda ec, es: self.process_finished(ec, es))
        env = QProcessEnvironment.systemEnvironment()
        env.insert("GOOGLE_API_KEY", self.config["api_keys"]["gemini"]); env.insert("LAA_BACKEND_MODE", "1")
        self.process.setProcessEnvironment(env)
        executable_to_run = ""; args_for_executable = []
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            executable_to_run = sys.executable
            args_for_executable = ["--query", user_input, "--json"]
            if not os.path.exists(os.path.join(sys._MEIPASS, "src", "backend_cli.py")):
                self.log_message(f"CRITICAL: Packaged backend_cli.py not found in MEIPASS/src!", "error", True); return
        else:
            executable_to_run = sys.executable
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "backend_cli.py")
            if not os.path.exists(script_path):
                self.log_message(f"CRITICAL: Dev backend_cli.py not found: {script_path}", "error", True); return
            args_for_executable = [script_path, "--query", user_input, "--json"]
        self.log_message(f"Cmd: {executable_to_run} {' '.join(args_for_executable)}", "system")
        self.process.start(executable_to_run, args_for_executable)
        if not self.process.waitForStarted(5000): self.log_message(f"Error starting backend: {self.process.errorString()}", "error", True)

    def handle_stdout(self):
        if not self.process: return
        raw_data = self.process.readAllStandardOutput().data().decode().strip()
        if not raw_data: return
        self.log_message(f"Backend STDOUT: {raw_data}", "system")
        try:
            result = json.loads(raw_data)
            if result.get("success", False):
                self.command_display.setText(result.get("command", "N/A"))
                self.explanation_display.setText(result.get("explanation", "N/A"))
                self.command_widget.show(); self.current_command = result.get("command", "")
            else:
                self.terminal.append_message(f"Backend Error (JSON): {result.get('error', 'Unknown')}", "error")
                self.command_widget.hide()
        except json.JSONDecodeError:
            self.terminal.append_message(f"Backend (non-JSON STDOUT): {raw_data}", "error")
            self.command_widget.hide()

    def handle_stderr(self):
        if not self.process: return
        raw_data = self.process.readAllStandardError().data().decode().strip()
        if raw_data: self.log_message(f"Backend STDERR: {raw_data}", "error", True)

    def process_finished(self, exit_code, exit_status):
        status = "normally" if exit_status == QProcess.NormalExit else "with a crash"
        self.log_message(f"Backend process finished {status}, exit code: {exit_code}.", "system")
        if exit_code != 0 and not self.command_widget.isVisible():
             self.log_message(f"Backend may have failed (code: {exit_code}). Check messages.", "error", True)

    def execute_command(self):
        if not self.current_command: return
        self.command_widget.hide(); self.log_message(f"Executing: {self.current_command}", "command", True)
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
        self.command_widget.hide(); self.current_command = ""
        self.log_message("Command cancelled.", "system", True)

def main_gui_entry_point():
    app = QApplication(sys.argv)
    # QColorConstants jest importowane globalnie z PyQt5.QtGui
    window = LinuxAIAssistantGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    if not _IS_BACKEND_MODE:
        main_gui_entry_point()
