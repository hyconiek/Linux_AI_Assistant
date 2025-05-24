
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
import shlex
import shutil
from typing import Dict, Optional, List, Any, Set
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                            QLabel, QDialog, QTabWidget, QCheckBox, QMessageBox,
                            QAction, QMenu, QStyle, QFileDialog,
                            QDialogButtonBox, QFormLayout, QGroupBox, QSizePolicy)
from PyQt5.QtGui import QFont, QIcon, QTextCursor, QColor, QPalette, QPixmap
from PyQt5.QtCore import Qt, QProcess, QSettings, QSize, pyqtSignal, QTimer, QProcessEnvironment, QEvent


_IS_BACKEND_MODE = os.environ.get("LAA_BACKEND_MODE") == "1"

if _IS_BACKEND_MODE:
    try:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            backend_module_path = os.path.join(sys._MEIPASS, "src") # type: ignore
            if backend_module_path not in sys.path:
                sys.path.insert(0, backend_module_path)
        import backend_cli # type: ignore
        backend_cli.main()
        sys.exit(0)
    except ImportError as e:
        print(f"FATAL BACKEND ERROR (ImportError): Cannot import backend_cli. {e}", file=sys.stderr)
        print(f"Current sys.path: {sys.path}", file=sys.stderr)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'): # type: ignore
            meipass_path = sys._MEIPASS # type: ignore
            src_in_meipass = os.path.join(meipass_path, 'src')
            if os.path.exists(src_in_meipass) and os.path.isdir(src_in_meipass):
                print(f"MEIPASS/src content: {os.listdir(src_in_meipass)}", file=sys.stderr)
            else:
                print(f"MEIPASS/src dir not found or is not a directory: {src_in_meipass}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL BACKEND ERROR (Exception): {e}", file=sys.stderr)
        sys.exit(1)

GeminiIntegration = None
if not _IS_BACKEND_MODE:
    try:
        module_base_path = ""
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            module_base_path = os.path.join(sys._MEIPASS, "src") # type: ignore
        else:
            module_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
        if module_base_path not in sys.path:
             sys.path.insert(0, module_base_path)
        from modules.gemini_integration import GeminiIntegration, GeminiApiResponse # type: ignore
    except ImportError as e:
        print(f"Warning (GUI): Could not import GeminiIntegration module directly. Error: {e}", file=sys.stderr)

CONFIG_DIR = os.path.expanduser("~/.config/linux_ai_assistant")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
EXPLANATIONS_CACHE_FILE = os.path.join(CONFIG_DIR, "explanations_cache.json")
DEFAULT_CONFIG = {
    "api_keys": {"gemini": "", "openai": "", "anthropic": ""},
    "show_instructions": True, "theme": "dark", "max_history": 100,
    "verbose_logging": True, "gui_model_name": 'gemini-2.5-flash-preview-05-20',
    "force_ai_for_commands": ["rm"]
}

# --- Klasy dialogów ---
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
            "<li>Type your request in natural language (e.g., 'Show all running processes') or a direct command (e.g. 'ls -la').</li>"
            "<li>The assistant will generate a suitable Linux command or answer your question about files.</li>"
            "<li>If you type a basic command (like 'ls', 'cd', 'pwd'), it will execute directly, and an AI explanation will follow.</li>"
            "<li>Review the command and its explanation, or the AI's answer.</li>"
            "<li>Click 'Execute' (if a command is shown) or 'Copy'.</li>"
            "<li>Use Up/Down arrows in the input field to navigate command history.</li>"
            "</ol>"
            "<h3>Example requests:</h3>"
            "<ul>"
            "<li>Show disk usage in human-readable format</li>"
            "<li>Are there any '.log' files here?</li>"
            "<li>Find all PDF files in my home directory</li>"
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
        self.setWindowTitle("Settings"); self.setMinimumWidth(500); self.setMinimumHeight(450)
        self.config = config if config else DEFAULT_CONFIG.copy()
        layout = QVBoxLayout(self); tabs = QTabWidget();
        api_keys_tab = QWidget()
        api_keys_layout = QVBoxLayout(api_keys_tab)
        for api_name in ["Gemini", "OpenAI", "Anthropic"]:
            group = QGroupBox(f"{api_name} API"); form_layout = QFormLayout(group)
            key_input = QLineEdit(self.config["api_keys"].get(api_name.lower(), "")); key_input.setEchoMode(QLineEdit.Password)
            setattr(self, f"{api_name.lower()}_key_input", key_input)
            form_layout.addRow("API Key:", key_input)
            show_key_cb = QCheckBox("Show API key")
            show_key_cb.stateChanged.connect(lambda state, inp=key_input: self.toggle_key_visibility_static(state, inp))
            form_layout.addRow("", show_key_cb)
            api_keys_layout.addWidget(group)
        api_keys_layout.addStretch(); tabs.addTab(api_keys_tab, "API Keys")

        general_tab = QWidget(); general_layout = QVBoxLayout(general_tab)
        self.show_instructions_checkbox = QCheckBox("Show instructions on startup")
        self.show_instructions_checkbox.setChecked(self.config.get("show_instructions", True))
        general_layout.addWidget(self.show_instructions_checkbox)

        self.verbose_logging_checkbox_settings = QCheckBox("Enable verbose logging (GUI display)")
        self.verbose_logging_checkbox_settings.setChecked(self.config.get("verbose_logging", True))
        self.verbose_logging_checkbox_settings.setToolTip("Show detailed backend system/debug messages in the GUI terminal window.")
        general_layout.addWidget(self.verbose_logging_checkbox_settings)

        max_history_group = QGroupBox("Command History")
        max_history_form = QFormLayout(max_history_group)
        self.max_history_input = QLineEdit(str(self.config.get("max_history", DEFAULT_CONFIG["max_history"])))
        self.max_history_input.setToolTip("Maximum number of commands to keep in input history (10-999).")
        self.max_history_input.setInputMask("999")
        max_history_form.addRow("Max History Size:", self.max_history_input)
        general_layout.addWidget(max_history_group)

        force_ai_group = QGroupBox("Force AI Processing for Commands")
        force_ai_form = QFormLayout(force_ai_group)
        current_force_ai_list = self.config.get("force_ai_for_commands", ["rm"])
        self.force_ai_commands_input = QLineEdit(", ".join(current_force_ai_list))
        self.force_ai_commands_input.setToolTip("Comma-separated command prefixes (e.g., rm, mv) that should always be processed by AI, not executed directly as basic commands.")
        force_ai_form.addRow("Commands:", self.force_ai_commands_input)
        general_layout.addWidget(force_ai_group)

        model_group = QGroupBox("GUI AI Model")
        model_form = QFormLayout(model_group)
        self.gui_model_input = QLineEdit(self.config.get("gui_model_name", DEFAULT_CONFIG["gui_model_name"]))
        self.gui_model_input.setToolTip("Model used for real-time explanations and clarification questions in GUI.")
        model_form.addRow("Model Name:", self.gui_model_input)
        general_layout.addWidget(model_group)

        theme_group = QGroupBox("Theme"); theme_form = QFormLayout(theme_group)
        self.theme_dark_checkbox = QCheckBox("Dark mode")
        self.theme_dark_checkbox.setChecked(self.config.get("theme", "dark") == "dark")
        theme_form.addRow(self.theme_dark_checkbox)
        general_layout.addWidget(theme_group); general_layout.addStretch(); tabs.addTab(general_tab, "General")
        layout.addWidget(tabs)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept); button_box.rejected.connect(self.reject); layout.addWidget(button_box)
    @staticmethod
    def toggle_key_visibility_static(state, input_field): input_field.setEchoMode(QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password)
    def get_config(self) -> Dict:
        updated_config = self.config.copy()
        for api_name_lower in ["gemini", "openai", "anthropic"]:
            key_input_widget = getattr(self, f"{api_name_lower}_key_input", None)
            if key_input_widget: updated_config["api_keys"][api_name_lower] = key_input_widget.text().strip()
        updated_config["show_instructions"] = self.show_instructions_checkbox.isChecked()
        updated_config["verbose_logging"] = self.verbose_logging_checkbox_settings.isChecked()
        try:
            updated_config["max_history"] = int(self.max_history_input.text())
            if not (10 <= updated_config["max_history"] <= 999):
                updated_config["max_history"] = DEFAULT_CONFIG["max_history"]
        except ValueError:
            updated_config["max_history"] = DEFAULT_CONFIG["max_history"]

        force_ai_text = self.force_ai_commands_input.text().strip()
        if force_ai_text:
            updated_config["force_ai_for_commands"] = [cmd.strip().lower() for cmd in force_ai_text.split(',') if cmd.strip()]
        else:
            updated_config["force_ai_for_commands"] = []


        updated_config["gui_model_name"] = self.gui_model_input.text().strip() or DEFAULT_CONFIG["gui_model_name"]
        updated_config["theme"] = "dark" if self.theme_dark_checkbox.isChecked() else "light"
        return updated_config

class SudoPasswordDialog(QDialog):
    def __init__(self, parent=None, command=""):
        super().__init__(parent)
        self.setWindowTitle("Sudo Privileges Required"); self.setMinimumWidth(500)
        layout = QVBoxLayout(self); header_layout = QHBoxLayout()
        warning_icon_label = QLabel(); pixmap = self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(48, 48)
        warning_icon_label.setPixmap(pixmap); header_layout.addWidget(warning_icon_label)
        title_label = QLabel("Sudo Privileges Required"); title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label); header_layout.addStretch(); layout.addLayout(header_layout)
        warning_text_label = QLabel(
            f"<p>The command <b><code>{command}</code></b> requires sudo (administrator) privileges.</p>"
            f"<p><b>Warning:</b> Executing commands with sudo can make critical changes to your system. "
            f"Only proceed if you understand the command and trust its source.</p>"
            f"<p>Please enter your sudo password to continue, or cancel to abort.</p>"
        ); warning_text_label.setWordWrap(True); layout.addWidget(warning_text_label)
        form_layout = QFormLayout(); self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Sudo Password:", self.password_input); layout.addLayout(form_layout)
        self.show_password_checkbox = QCheckBox("Show password")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility); layout.addWidget(self.show_password_checkbox)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept); button_box.rejected.connect(self.reject); layout.addWidget(button_box)
    def toggle_password_visibility(self, state): self.password_input.setEchoMode(QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password)
    def get_password(self) -> str: return self.password_input.text()

class ClarificationDialog(QDialog):
    def __init__(self, parent=None, query: str = "", questions_list: Optional[List[str]] = None):
        super().__init__(parent)
        self.setWindowTitle("Clarification Needed"); self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        intro_label = QLabel(f"Your query \"<b>{query}</b>\" may require more details. Please answer the questions below if applicable:")
        intro_label.setWordWrap(True); layout.addWidget(intro_label)
        self.answer_inputs: List[QLineEdit] = []
        if questions_list:
            for question_text in questions_list:
                q_label = QLabel(question_text); q_label.setWordWrap(True); layout.addWidget(q_label)
                answer_edit = QLineEdit(); self.answer_inputs.append(answer_edit); layout.addWidget(answer_edit)
        else:
            layout.addWidget(QLabel("Provide additional details or press OK to proceed with the original query:"))
            generic_input = QLineEdit(); self.answer_inputs.append(generic_input); layout.addWidget(generic_input)
        layout.addSpacing(10)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept); button_box.rejected.connect(self.reject); layout.addWidget(button_box)
    def get_answers(self) -> List[str]: return [editor.text() for editor in self.answer_inputs]

class TerminalWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True); self.setFont(QFont("Monospace", 10)); self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setObjectName("TerminalWidget")
        self.colors = {
            "system": QColor("#808080"), "user": QColor("#FFFFFF"), "assistant": QColor("#00FF00"),
            "command": QColor("#FFFF00"), "error": QColor("#FF0000"), "success": QColor("#00FF00"),
            "debug_backend": QColor("#FFA500"), "ai_text_answer": QColor("#87CEFA")
        }
    def append_message(self, text, message_type="system"):
        self.moveCursor(QTextCursor.End); cursor = self.textCursor(); char_format = cursor.charFormat()
        text_color = self.palette().color(QPalette.Text)
        if message_type in self.colors: text_color = self.colors.get(message_type, text_color) # type: ignore
        char_format.setForeground(text_color); cursor.setCharFormat(char_format)
        cursor.insertText(text + "\n"); self.moveCursor(QTextCursor.End); self.ensureCursorVisible()
# --- Koniec klas dialogów ---

class LinuxAIAssistantGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self._theme_applied_once = False
        self.current_command: Optional[str] = None
        self.process: Optional[QProcess] = None
        self.current_exec_process: Optional[QProcess] = None
        self.gui_current_working_dir = os.path.abspath(os.getcwd())
        self.config: Dict[str, Any] = {}
        self.init_config()
        self.verbose_logging = self.config.get("verbose_logging", True)
        self.explanations_cache: Dict[str, str] = {}
        self.explanation_timer: Optional[QTimer] = None
        self.ai_engine_for_gui: Optional[GeminiIntegration] = None
        self.current_command_suggested_interaction_input: Optional[str] = None
        self.waiting_for_basic_command_explanation_for: Optional[str] = None

        self.animation_timer: Optional[QTimer] = None
        self.animation_chars = ["|", "/", "-", "\\"]
        self.animation_index = 0
        self.is_processing_animation_active = False
        self._current_animation_message = "Processing"


        self.input_history: List[str] = []
        self.current_history_index: int = 0
        self.pending_input_text: str = ""

        self.basic_command_prefixes: Set[str] = {
            "ls", "cd", "pwd", "mkdir", "cp", "mv", "cat", "echo", "clear", "whoami",
            "df", "du", "free", "sensors", "man", "history", "ping", "ifconfig", "ip",
            "ssh", "scp", "top", "ps", "kill",
            "apt", "dnf", "yum", "pacman", "zypper", "sudo"
        }
        self.init_ui()
        self.load_explanations_cache()
        self._init_ai_engine_for_gui()
        self.apply_theme()
        self.check_api_key()
        if self.config.get("show_instructions", True):
            QTimer.singleShot(200, self.show_instructions)

    def init_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    self.config = DEFAULT_CONFIG.copy()
                    self.config.update(loaded_config)
            else:
                self.config = DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Error loading config: {e}. Using default config.", file=sys.stderr)
            self.config = DEFAULT_CONFIG.copy()
        for key, value in DEFAULT_CONFIG.items():
            self.config.setdefault(key, value)
        try:
            self.config["max_history"] = int(self.config.get("max_history", DEFAULT_CONFIG["max_history"]))
            if not (10 <= self.config["max_history"] <= 999):
                self.config["max_history"] = DEFAULT_CONFIG["max_history"]
        except ValueError:
            self.config["max_history"] = DEFAULT_CONFIG["max_history"]
        if not isinstance(self.config.get("force_ai_for_commands"), list):
            self.config["force_ai_for_commands"] = DEFAULT_CONFIG["force_ai_for_commands"]

    def save_config(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}", file=sys.stderr)

    def _get_gui_ai_language_instruction(self) -> str:
        try:
            lang_code, _ = locale.getdefaultlocale()
            system_language = "en"
            if lang_code and '_' in lang_code: system_language = lang_code.split('_')[0]
            elif lang_code: system_language = lang_code

            if system_language == "pl":
                return "ODPOWIADAJ ZAWSZE W JĘZYKU POLSKIM. Wyjaśnienie polecenia, pytania doprecyzowujące, sugestie naprawcze i wszelkie inne teksty MUSZĄ być po polsku."
            elif system_language == "cs":
                return "ODPOVÍDEJ VŽDY ČESKY. Vysvětlení příkazu, doplňující otázky, návrhy oprav a veškeré další texty MUSÍ být v češtině."
            return "Respond always in English. The command explanation, clarification questions, fix suggestions, and any other text MUST be in English."
        except Exception:
            return "Respond always in English. The command explanation, clarification questions, fix suggestions, and any other text MUST be in English."

    def _init_ai_engine_for_gui(self):
        if not _IS_BACKEND_MODE and GeminiIntegration is not None:
            api_key = self.config["api_keys"].get("gemini", "")
            gui_model = self.config.get("gui_model_name", DEFAULT_CONFIG["gui_model_name"])
            if api_key:
                try:
                    original_env_api_key = os.environ.get('GOOGLE_API_KEY')
                    os.environ['GOOGLE_API_KEY'] = api_key
                    self.ai_engine_for_gui = GeminiIntegration(model_name=gui_model)
                    if original_env_api_key is not None: os.environ['GOOGLE_API_KEY'] = original_env_api_key
                    else: del os.environ['GOOGLE_API_KEY']
                    self.log_message(f"AI engine for GUI (model: {gui_model}) initialized.", "system")
                except Exception as e:
                    self.log_message(f"Error initializing AI engine for GUI: {e}", "error", True); self.ai_engine_for_gui = None
            else:
                self.log_message("Gemini API key not set. GUI AI features (real-time analysis) disabled.", "system"); self.ai_engine_for_gui = None
        elif GeminiIntegration is None:
            self.log_message("GeminiIntegration module could not be imported. GUI AI features disabled.", "error", True)

    def init_ui(self):
        self.setWindowTitle("Linux AI Assistant"); self.setMinimumSize(800, 600)
        icon_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "laia_icon.png")
        if os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))
        else: self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.terminal = TerminalWidget(); main_layout.addWidget(self.terminal, 1)

        self.generated_command_panel = QWidget()
        generated_command_layout = QVBoxLayout(self.generated_command_panel)
        generated_command_layout.setContentsMargins(0, 5, 0, 0)
        self.generated_command_header_label = QLabel("Generated Command:")
        self.generated_command_header_label.setObjectName("GeneratedCommandHeaderLabel")
        generated_command_layout.addWidget(self.generated_command_header_label)
        self.generated_command_display = QTextEdit()
        self.generated_command_display.setObjectName("GeneratedCommandDisplay")
        self.generated_command_display.setReadOnly(True)
        fm_cmd = self.generated_command_display.fontMetrics(); lh_cmd = fm_cmd.height(); dm_cmd = int(self.generated_command_display.document().documentMargin())
        m_cmd = self.generated_command_display.contentsMargins(); p_cmd = m_cmd.top() + m_cmd.bottom() + (dm_cmd * 2)
        self.generated_command_display.setMinimumHeight(lh_cmd + p_cmd + 5)
        self.generated_command_display.setMaximumHeight(lh_cmd + p_cmd + 5) # One line height
        self.generated_command_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.generated_command_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.generated_command_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        generated_command_layout.addWidget(self.generated_command_display)

        button_layout = QHBoxLayout()
        self.execute_button = QPushButton("Execute"); self.copy_button = QPushButton("Copy"); self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.execute_button); button_layout.addWidget(self.copy_button); button_layout.addWidget(self.cancel_button)
        generated_command_layout.addLayout(button_layout)
        main_layout.addWidget(self.generated_command_panel)
        self.generated_command_panel.hide()

        self.ai_output_header_label = QLabel("AI Analysis / Explanation / Answer:")
        self.ai_output_header_label.setObjectName("AIOutputHeaderLabel")
        main_layout.addWidget(self.ai_output_header_label)
        self.ai_output_display = QTextEdit()
        self.ai_output_display.setObjectName("AIOutputDisplay")
        self.ai_output_display.setReadOnly(True)
        self._original_ai_output_placeholder = "Type a command or query... Analysis or explanation will appear here." # Store original
        self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
        fm_aio = self.ai_output_display.fontMetrics(); lh_aio = fm_aio.height(); dm_aio = int(self.ai_output_display.document().documentMargin())
        m_aio = self.ai_output_display.contentsMargins(); p_aio = m_aio.top() + m_aio.bottom() + (dm_aio * 2)
        self.ai_output_display.setMinimumHeight(lh_aio + p_aio + 5); self.ai_output_display.setMaximumHeight(int(lh_aio * 3.5) + p_aio + 5)
        self.ai_output_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred); self.ai_output_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_layout.addWidget(self.ai_output_display)

        input_layout = QHBoxLayout(); self.prompt_label = QLabel("> ")
        self.prompt_label.setObjectName("PromptLabel")
        input_layout.addWidget(self.prompt_label); self.input_field = QLineEdit(); self.input_field.setObjectName("InputField")
        self.input_field.returnPressed.connect(self.process_input); self.input_field.textChanged.connect(self.update_realtime_analysis)
        self.input_field.installEventFilter(self)
        input_layout.addWidget(self.input_field); main_layout.addLayout(input_layout)

        self.execute_button.clicked.connect(self.execute_command); self.copy_button.clicked.connect(self.copy_content); self.cancel_button.clicked.connect(self.cancel_generated_command)

        menubar = self.menuBar(); file_menu = menubar.addMenu("File")
        file_menu.addAction(QAction("New Session", self, shortcut="Ctrl+N", triggered=self.start_new_session))
        file_menu.addAction(QAction("Save Session Log", self, shortcut="Ctrl+S", triggered=self.save_session))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Settings", self, shortcut="Ctrl+,", triggered=self.show_settings))
        file_menu.addAction(QAction("Instructions", self, triggered=self.show_instructions))
        file_menu.addSeparator(); file_menu.addAction(QAction("Exit", self, shortcut="Ctrl+Q", triggered=self.close))
        help_menu = menubar.addMenu("Help"); help_menu.addAction(QAction("About", self, triggered=self.show_about))
        toolbar = self.addToolBar("Toolbar"); toolbar.setMovable(False); toolbar.setFloatable(False)
        toolbar.addAction(QAction(self.style().standardIcon(QStyle.SP_FileIcon), "New Session", self, triggered=self.start_new_session))
        self.verbose_log_checkbox = QCheckBox("Verbose Backend Log")
        self.verbose_log_checkbox.setToolTip("Show detailed backend system/debug messages in this GUI terminal.")
        self.verbose_log_checkbox.setChecked(self.verbose_logging)
        self.verbose_log_checkbox.stateChanged.connect(self.toggle_verbose_logging)
        toolbar.addWidget(self.verbose_log_checkbox); spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        self.settings_button_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Settings", self)
        self.settings_button_action.triggered.connect(self.show_settings); toolbar.addAction(self.settings_button_action)

    def update_prompt_label_text(self) -> str:
        path_parts = self.gui_current_working_dir.split(os.sep)
        if len(path_parts) > 3:
            display_path = os.path.join("...", path_parts[-2], path_parts[-1])
        else:
            display_path = self.gui_current_working_dir
        return f"[{display_path}]> "

    def apply_theme(self):
        dark = self.config.get("theme", "dark") == "dark"
        base_bg, base_fg, term_bg, term_user_fg, border, btn_bg, btn_hov, btn_press, btn_press_fg = (
            ("#282A36", "#F8F8F2", "#1E1E1E", "#F8F8F2", "#44475A", "#44475A", "#6272A4", "#50FA7B", "#282A36") if dark
            else ("#F0F0F0", "#333333", "#FFFFFF", "#000000", "#CCCCCC", "#E0E0E0", "#D0D0D0", "#50FA7B", "#282A36"))
        self.terminal.colors = {"system": QColor("#B0B0B0" if dark else "#707070"), "user": QColor(term_user_fg),
                                "assistant": QColor("#66FF66"), "command": QColor("#FFC266"), "error": QColor("#FF6666"),
                                "success": QColor("#66FF99"), "debug_backend": QColor("#FF8C00" if dark else "#FFA500"),
                                "ai_text_answer": QColor("#87CEFA" if dark else "#4682B4")}

        prompt_lbl_c = self.terminal.colors['assistant'].name()
        cmd_hdr_c = self.terminal.colors["command"].name()
        aio_hdr_c = (QColor("#8BE9FD") if dark else QColor("#1AA0D5")).name()

        qss = f"""
            QMainWindow, QDialog {{ background-color: {base_bg}; color: {base_fg}; }}
            QMenuBar {{ background-color: {base_bg}; color: {base_fg}; }} QMenuBar::item:selected {{ background-color: {btn_bg}; }}
            QMenu {{ background-color: {base_bg}; color: {base_fg}; border: 1px solid {border}; }} QMenu::item:selected {{ background-color: {btn_bg}; }}
            QToolBar {{ background-color: {base_bg}; border: none; }}
            QPushButton {{ background-color: {btn_bg}; color: {base_fg}; border: 1px solid {border}; padding: 5px 10px; border-radius: 3px; }}
            QPushButton:hover {{ background-color: {btn_hov}; }} QPushButton:pressed {{ background-color: {btn_press}; color: {btn_press_fg}; }}
            QLabel#PromptLabel {{ color: {prompt_lbl_c}; font-family: Monospace; font-size: 10pt; }}
            QLabel#GeneratedCommandHeaderLabel {{ color: {cmd_hdr_c}; font-weight: bold; }}
            QLabel#AIOutputHeaderLabel {{ color: {aio_hdr_c}; font-weight: bold; }}
            QLabel {{ color: {base_fg}; }} QTabWidget::pane {{ border: 1px solid {border}; background-color: {base_bg}; }}
            QTabBar::tab {{ background-color: {base_bg}; color: {base_fg}; padding: 5px 10px; border: 1px solid {border}; border-bottom: none; border-top-left-radius: 3px; border-top-right-radius: 3px; }}
            QTabBar::tab:selected {{ background-color: {btn_bg}; }}
            QGroupBox {{ border: 1px solid {border}; margin-top: 1ex; color: {base_fg}; border-radius: 3px; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }}
            QLineEdit {{ background-color: {term_bg}; color: {term_user_fg}; border: 1px solid {border}; padding: 4px; border-radius: 3px; }}
            QLineEdit#InputField {{ background-color: {term_bg}; color: {term_user_fg}; border: none; font-family: Monospace; font-size: 10pt; padding: 5px; }}
            QCheckBox {{ color: {base_fg}; }} QTextEdit#TerminalWidget {{ background-color: {term_bg}; border: none; }}
            QTextEdit#GeneratedCommandDisplay, QTextEdit#AIOutputDisplay {{
                background-color: {'#2C2F3A' if dark else '#FAFAFA'};
                border: 1px solid {border}; border-radius: 3px;
                font-family: Monospace; font-size: 10pt; padding: 3px;
            }}
            QTextEdit#GeneratedCommandDisplay {{ color: {cmd_hdr_c}; }}
            QTextEdit#AIOutputDisplay {{ color: {aio_hdr_c}; }}"""
        self.setStyleSheet(qss); QApplication.instance().setFont(QFont("Noto Sans", 10))
        if not self._theme_applied_once:
            self.log_message("=== Linux AI Assistant ===", "system", True);
            self.log_message(f"Type 'help' for instructions or a query.", "user", True)
            self.log_message("", "system"); self._theme_applied_once = True
        else:
            pal = self.terminal.palette(); pal.setColor(QPalette.Text, self.terminal.colors["user"]); pal.setColor(QPalette.Base, QColor(term_bg)); self.terminal.setPalette(pal)
            aio_pal = self.ai_output_display.palette(); aio_pal.setColor(QPalette.Text, QColor(aio_hdr_c)); aio_pal.setColor(QPalette.Base, QColor({'#2C2F3A' if dark else '#FAFAFA'})); self.ai_output_display.setPalette(aio_pal)
            gcmd_pal = self.generated_command_display.palette(); gcmd_pal.setColor(QPalette.Text, QColor(cmd_hdr_c)); gcmd_pal.setColor(QPalette.Base, QColor({'#2C2F3A' if dark else '#FAFAFA'})); self.generated_command_display.setPalette(gcmd_pal)

    def log_message(self, message: str, message_type: str = "system", force_show: bool = False):
        if message_type == "debug_backend" and not self.verbose_logging and not force_show: return
        prefix = ""
        if message_type == "user":
            prefix = self.update_prompt_label_text()
        self.terminal.append_message(f"{prefix}{message}", message_type)

    def toggle_verbose_logging(self, state_int: int):
        self.verbose_logging = (state_int == Qt.Checked); self.config["verbose_logging"] = self.verbose_logging; self.save_config()
        self.log_message(f"Verbose backend logging (GUI display) {'enabled' if self.verbose_logging else 'disabled'}.", "system", True)

    def check_api_key(self):
        if not self.config["api_keys"].get("gemini", ""): QTimer.singleShot(100, self.prompt_for_api_key)

    def prompt_for_api_key(self):
        dialog = ApiKeyDialog(self, self.config["api_keys"].get("gemini", ""))
        if dialog.exec_():
            api_key = dialog.get_api_key()
            if api_key: self.config["api_keys"]["gemini"] = api_key; self.save_config(); self.log_message("API key configured.", "success", True); self._init_ai_engine_for_gui()
            else: self.log_message("API key is required for AI features.", "error", True); QTimer.singleShot(1000, self.prompt_for_api_key)

    def show_instructions(self):
        dialog = InstructionsDialog(self, self.config.get("show_instructions", True))
        if dialog.exec_(): self.config["show_instructions"] = dialog.should_show_again(); self.save_config()

    def show_settings(self):
        prev_gemini_key = self.config["api_keys"].get("gemini","")
        prev_gui_model = self.config.get("gui_model_name")
        prev_verbose_log = self.config.get("verbose_logging")
        prev_max_hist = self.config.get("max_history")
        prev_force_ai_cmds = self.config.get("force_ai_for_commands", [])
        dialog = SettingsDialog(self, self.config.copy())
        if dialog.exec_():
            new_cfg = dialog.get_config()
            theme_changed = self.config.get("theme") != new_cfg.get("theme")
            gemini_key_changed = prev_gemini_key != new_cfg["api_keys"].get("gemini","")
            gui_model_changed = prev_gui_model != new_cfg.get("gui_model_name")
            verbose_log_changed = prev_verbose_log != new_cfg.get("verbose_logging")
            max_hist_changed = prev_max_hist != new_cfg.get("max_history")
            force_ai_cmds_changed = set(prev_force_ai_cmds) != set(new_cfg.get("force_ai_for_commands", []))
            self.config = new_cfg
            self.verbose_logging = self.config.get("verbose_logging", True)
            self.save_config()
            if theme_changed: self.apply_theme()
            self.verbose_log_checkbox.setChecked(self.verbose_logging)
            if verbose_log_changed: self.log_message(f"Verbose backend logging (GUI display) {'enabled' if self.verbose_logging else 'disabled'}.", "system", True)
            if max_hist_changed:
                self.log_message(f"Max command history size set to {self.config['max_history']}.", "system", True)
                max_h = self.config.get("max_history", DEFAULT_CONFIG["max_history"])
                if len(self.input_history) > max_h:
                    self.input_history = self.input_history[-max_h:]
                    if self.current_history_index > len(self.input_history) :
                        self.current_history_index = len(self.input_history)
            if force_ai_cmds_changed:
                self.log_message(f"Commands to always force AI processing updated: {self.config.get('force_ai_for_commands')}", "system", True)
            if gemini_key_changed or gui_model_changed: self._init_ai_engine_for_gui()
            self.log_message("Settings updated.", "success", True)

    def show_about(self):
        QMessageBox.about(self, "About Linux AI Assistant", "<h3>Linux AI Assistant</h3><p>Version 1.0.5</p><p>Created by: Krzysztof Żuchowski</p>"
                          "<p>© 2025 Krzysztof Żuchowski. All rights reserved.</p><p>Licensed under the MIT License.</p>"
                          "<p>AI-powered command generation for Linux.</p><hr><p>Support the project:</p>"
                          "<p><a href='https://www.buymeacoffee.com/krzyzu.83'>Buy me a coffee (krzyzu.83)</a></p>"
                          "<p><a href='https://github.com/hyconiek/linux_ai_terminal_assistant'>Project on GitHub</a></p>")

    def start_processing_animation(self, message: str = "Processing"):
        if self.is_processing_animation_active: return
        self.is_processing_animation_active = True
        self.animation_index = 0
        if not hasattr(self, '_original_ai_output_placeholder'):
            self._original_ai_output_placeholder = self.ai_output_display.placeholderText()
        if self.animation_timer is None:
            self.animation_timer = QTimer(self)
            self.animation_timer.timeout.connect(self.update_processing_animation)
        self._current_animation_message = message
        self.ai_output_display.clear() # Clear previous content before showing animation/placeholder
        self.update_processing_animation()
        self.animation_timer.start(150)
        self.input_field.setEnabled(False)

    def update_processing_animation(self):
        if not self.is_processing_animation_active: return
        char = self.animation_chars[self.animation_index % len(self.animation_chars)]
        self.ai_output_display.setPlaceholderText(f"{self._current_animation_message} {char}")
        self.animation_index += 1

    def stop_processing_animation(self, restore_placeholder: bool = True):
        if not self.is_processing_animation_active: return
        if self.animation_timer and self.animation_timer.isActive(): self.animation_timer.stop()
        if restore_placeholder:
            self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder if hasattr(self, '_original_ai_output_placeholder') else "Type a command or query... Analysis or explanation will appear here.")
            if not self.ai_output_display.toPlainText().strip(): # If it's truly empty, clear to show placeholder
                self.ai_output_display.clear()
        self.is_processing_animation_active = False
        self.input_field.setEnabled(True)


    def process_input(self):
        user_input = self.input_field.text().strip()
        if not user_input: return
        if not self.input_history or self.input_history[-1] != user_input:
            self.input_history.append(user_input)
            max_h = self.config.get("max_history", DEFAULT_CONFIG["max_history"])
            if len(self.input_history) > max_h: self.input_history = self.input_history[-max_h:]
        self.current_history_index = len(self.input_history); self.pending_input_text = ""
        self.input_field.clear(); self.log_message(f"{user_input}", "user", True)
        if user_input.lower() in ["exit", "quit"]: self.close(); return
        if user_input.lower() == "help": self.show_instructions(); return
        if user_input.lower() == "settings": self.show_settings(); return

        command_prefix = user_input.split(' ', 1)[0].lower()
        forced_ai_commands = set(self.config.get("force_ai_for_commands", ["rm"]))

        if command_prefix in forced_ai_commands:
            self.log_message(f"Command '{command_prefix}' is configured to always use AI. Processing query...", "system")
            self.start_processing_animation("Processing AI query...")
            self.process_detailed_query(user_input); return

        is_basic_sudo = command_prefix == "sudo" and len(user_input.split()) > 1 and user_input.split()[1].lower() in self.basic_command_prefixes
        if (command_prefix in self.basic_command_prefixes or is_basic_sudo):
            self.log_message(f"Basic command detected: '{user_input}'. Executing directly.", "system")
            self.generated_command_panel.hide();
            self.start_processing_animation("Executing command...")
            self.execute_basic_command(user_input); return

        if not self.config["api_keys"].get("gemini", ""):
            self.log_message("API key not set. Go to Settings.", "error", True); self.prompt_for_api_key(); return
        self.log_message("Processing query with AI backend...", "system")
        self.start_processing_animation("Processing AI query...")
        self.process_detailed_query(user_input)

    def handle_stdout(self):
        self.stop_processing_animation(restore_placeholder=False)
        if not self.process: return
        raw_data = self.process.readAllStandardOutput().data().decode().strip()
        if not raw_data: return
        self.log_message(f"Backend STDOUT (AI query result): {raw_data}", "debug_backend")
        try:
            result = json.loads(raw_data)
            self.generated_command_panel.hide()
            self.generated_command_display.clear(); self.ai_output_display.clear()

            if result.get("error") == "CLARIFY_REQUEST":
                self.log_message("AI requires clarification for your query.", "assistant", True)
                self.ai_output_display.setText("AI requires clarification. Suggesting questions...")
                last_q = "previous query"
                for line in reversed(self.terminal.toPlainText().strip().split('\n')):
                    prompt_text = self.update_prompt_label_text()
                    if line.startswith(prompt_text): last_q = line[len(prompt_text):].strip(); break
                self.handle_complex_query(last_q); return
            if result.get("error") == "DANGEROUS_REQUEST":
                self.log_message("AI identified query as dangerous.", "error", True)
                self.ai_output_display.setText("AI identified query as dangerous and blocked it."); return

            if result.get("success", False):
                if result.get("is_text_answer"):
                    answer_text = result.get("explanation", "AI provided a text answer.")
                    self.log_message(f"AI Answer received.", "assistant", True)
                    self.ai_output_display.setText(answer_text)
                    self.current_command = None
                elif result.get("command"):
                    cmd, expl = result.get("command", "N/A"), result.get("explanation", "N/A")
                    self.current_command_suggested_interaction_input = result.get("suggested_interaction_input")
                    sugg_label = result.get("suggested_button_label")
                    self.generated_command_header_label.setText("Generated Command:")
                    self.generated_command_display.setText(cmd)
                    self.ai_output_display.setText(expl)
                    self.generated_command_panel.show(); self.current_command = cmd
                    self.execute_button.setText(sugg_label if sugg_label else "Execute"); self.execute_button.setEnabled(True)
                    if cmd and expl: self.explanations_cache[cmd] = expl; self.save_explanations_cache()
                else: self.log_message("Backend returned success but no command or text answer.", "error", True)
            else:
                err_msg = result.get('error', 'Unknown backend error')
                self.log_message(f"Backend Error (JSON process_query): {err_msg}", "error", True)
                self.ai_output_display.setText(f"Error from backend: {err_msg}")

            new_wd_from_ai_context = result.get("working_dir")
            if new_wd_from_ai_context and os.path.abspath(new_wd_from_ai_context) != self.gui_current_working_dir:
                self.gui_current_working_dir = os.path.abspath(new_wd_from_ai_context)
                self.log_message(f"GUI CWD context updated from AI to: {self.gui_current_working_dir}", "debug_backend")
        except json.JSONDecodeError:
            self.log_message(f"Backend (non-JSON STDOUT process_query): {raw_data}", "error", True)
            self.ai_output_display.setText("Error: Received malformed data from backend.")

    def handle_stderr(self):
        self.stop_processing_animation(restore_placeholder=True) # Stop anim if stderr comes first
        if not self.process: return
        raw_data = self.process.readAllStandardError().data().decode().strip()
        if raw_data: self.log_message(f"Backend STDERR (query processing): {raw_data}", "debug_backend")

    def process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        self.stop_processing_animation(restore_placeholder=not self.ai_output_display.toPlainText().strip())
        status = "normally" if exit_status == QProcess.NormalExit else "with a crash"
        self.log_message(f"Backend process (AI query) finished {status}, code: {exit_code}.", "debug_backend")
        if exit_code != 0 and not self.generated_command_panel.isVisible() and not self.ai_output_display.toPlainText().strip():
             self.log_message(f"Backend AI query process may have failed (code: {exit_code}).", "error", True)
             self.ai_output_display.setText(f"AI query process failed (code: {exit_code}).")
        if self.process: self.process.deleteLater(); self.process = None

    def execute_basic_command(self, command_str: str):
        self.current_exec_process = QProcess(self)
        self.current_exec_process.readyReadStandardOutput.connect(lambda: self.handle_execution_stdout_from_backend(self.current_exec_process))
        self.current_exec_process.readyReadStandardError.connect(lambda: self.handle_execution_stderr_from_backend(self.current_exec_process))
        self.waiting_for_basic_command_explanation_for = command_str
        self.current_exec_process.finished.connect(lambda ec, es, cmd=command_str: self.execution_process_finished_from_backend(ec, es, cmd, self.current_exec_process))

        env = QProcessEnvironment.systemEnvironment()
        env.insert("GOOGLE_API_KEY", self.config["api_keys"]["gemini"])
        env.insert("LAA_BACKEND_MODE", "1"); env.insert("LAA_VERBOSE_LOGGING_EFFECTIVE", "1" if self.verbose_logging else "0")
        self.current_exec_process.setProcessEnvironment(env)
        exec_path, exec_args = (sys.executable, []) if getattr(sys,'frozen',False) else (sys.executable, [os.path.join(os.path.dirname(os.path.abspath(__file__)),"src","backend_cli.py")])
        if not getattr(sys, 'frozen', False) and not os.path.exists(exec_args[0]):
             self.log_message(f"CRITICAL: Dev backend_cli.py not found: {exec_args[0]}", "error", True)
             self.stop_processing_animation()
             return
        exec_args.extend(["--query", command_str, "--execute", "--json", "--working-dir", self.gui_current_working_dir])
        self.log_message(f"Backend exec cmd (basic): {exec_path} {' '.join(exec_args)}", "debug_backend")
        self.current_exec_process.start(exec_path, exec_args)
        if not self.current_exec_process.waitForStarted(10000):
            self.log_message(f"Błąd startu backendu (basic exec): {self.current_exec_process.errorString()}", "error", True)
            self.stop_processing_animation()
            if self.current_exec_process: self.current_exec_process.deleteLater(); self.current_exec_process = None
            self.waiting_for_basic_command_explanation_for = None

    def request_ai_explanation_for_executed_command(self, command_str: str):
        self.start_processing_animation(f"Getting AI explanation for: {command_str}")
        if not self.ai_engine_for_gui:
            self.log_message("AI engine for GUI not available to explain executed command.", "system")
            self.generated_command_header_label.setText("Executed Command:")
            self.generated_command_display.setText(command_str)
            self.ai_output_display.setText("Explanation N/A (GUI AI engine disabled).")
            self.generated_command_panel.show()
            self.execute_button.setEnabled(False); self.execute_button.setText("Executed")
            self.stop_processing_animation(restore_placeholder=False)
            return
        try:
            lang_instr_gui = self._get_gui_ai_language_instruction()
            api_res: Optional[GeminiApiResponse] = self.ai_engine_for_gui.analyze_text_input_type(command_str, language_instruction=lang_instr_gui)
            explanation_text = "Could not get explanation from AI."
            if api_res and api_res.success and api_res.analyzed_text_type == "linux_command":
                explanation_text = api_res.explanation or "AI confirmed it's a command but provided no specific explanation."
            elif api_res and api_res.error:
                explanation_text = f"AI Analysis Error: {api_res.error}"

            self.generated_command_header_label.setText("Executed Command:")
            self.generated_command_display.setText(command_str)
            self.ai_output_display.setText(explanation_text)
            self.generated_command_panel.show()
            self.execute_button.setEnabled(False); self.execute_button.setText("Executed")
            if command_str and explanation_text and "Could not get" not in explanation_text and "Error" not in explanation_text:
                 self.explanations_cache[command_str] = explanation_text
                 self.save_explanations_cache()
        except Exception as e:
            self.log_message(f"Exception requesting AI explanation for '{command_str}': {e}", "error", True)
            self.ai_output_display.setText(f"Error getting explanation: {e}")
            self.generated_command_panel.show()
            self.generated_command_display.setText(command_str)
            self.execute_button.setEnabled(False); self.execute_button.setText("Executed")
        finally:
            self.stop_processing_animation(restore_placeholder=False)


    def execute_command(self):
        if not self.current_command:
            self.log_message("No AI-generated command to execute.", "system", True); return

        self.start_processing_animation("Executing AI-generated command...")

        if self.current_command_suggested_interaction_input:
            self.log_message(f"Command '{self.current_command}' may require interaction. AI suggests response: '{self.current_command_suggested_interaction_input}'.\nRunning in external terminal...", "system", True)
            inner_cmd_for_bash = self.current_command.replace("'", "'\\''")
            bash_command_payload = f"{inner_cmd_for_bash}; echo -e '\\n\\n--- Command finished. Press Enter to close. ---'; read"
            term_to_use, args_term = None, []
            terminals = {"gnome-terminal": ["--", "bash", "-c", bash_command_payload], "konsole": ["-e", "bash", "-c", bash_command_payload], "xterm": ["-e", "bash", "-c", bash_command_payload]}
            for term, t_args in terminals.items():
                if shutil.which(term): term_to_use, args_term = term, t_args; break
            if term_to_use:
                try: QProcess.startDetached(term_to_use, args_term, self.gui_current_working_dir); self.log_message(f"Command '{self.current_command}' launched in '{term_to_use}'. Interact there.", "success", True)
                except Exception as e: self.log_message(f"Error launching external terminal: {e}", "error", True)
            else: self.log_message("No suitable terminal emulator found (gnome-terminal, konsole, xterm).", "error", True)
            self.generated_command_panel.hide(); self.execute_button.setText("Execute"); self.ai_output_display.clear()
            self.current_command_suggested_interaction_input = None; self.current_command = None
            self.stop_processing_animation()
        else:
            cmd_to_backend = self.current_command
            if self.current_command.strip().startswith("sudo "):
                dialog = SudoPasswordDialog(self, self.current_command)
                if dialog.exec_():
                    passwd = dialog.get_password()
                    if passwd:
                        cmd_no_sudo = self.current_command.replace("sudo ", "", 1).strip()
                        esc_passwd = shlex.quote(passwd)
                        cmd_to_backend = f"echo {esc_passwd} | sudo -S -p '' {cmd_no_sudo}"
                        self.log_message("Sudo password provided. Preparing command.", "system", True)
                    else:
                        self.log_message("Sudo password not provided. Execution cancelled.", "error", True)
                        self.stop_processing_animation(); return
                else:
                    self.log_message("Sudo command execution cancelled by user.", "system", True)
                    self.stop_processing_animation(); return

            self.current_command_suggested_interaction_input = None # Will be hidden after this
            self.log_message(f"Sending to backend (AI-gen, auto-confirm): {self.current_command}", "command", True)
            if cmd_to_backend != self.current_command: self.log_message(f"(Executing as: echo '****' | sudo -S ...)", "debug_backend")

            self.current_exec_process = QProcess(self)
            self.current_exec_process.readyReadStandardOutput.connect(lambda: self.handle_execution_stdout_from_backend(self.current_exec_process))
            self.current_exec_process.readyReadStandardError.connect(lambda: self.handle_execution_stderr_from_backend(self.current_exec_process))
            self.current_exec_process.finished.connect(lambda ec, es, cmd=str(self.current_command): self.execution_process_finished_from_backend(ec, es, cmd, self.current_exec_process))
            env = QProcessEnvironment.systemEnvironment()
            env.insert("GOOGLE_API_KEY", self.config["api_keys"]["gemini"])
            env.insert("LAA_BACKEND_MODE", "1"); env.insert("LAA_VERBOSE_LOGGING_EFFECTIVE", "1" if self.verbose_logging else "0")
            self.current_exec_process.setProcessEnvironment(env)
            exec_path, exec_args = (sys.executable, []) if getattr(sys,'frozen',False) else (sys.executable, [os.path.join(os.path.dirname(os.path.abspath(__file__)),"src","backend_cli.py")])
            if not getattr(sys, 'frozen', False) and not os.path.exists(exec_args[0]):
                 self.log_message(f"CRITICAL: Dev backend_cli.py not found: {exec_args[0]}", "error", True)
                 self.stop_processing_animation(); return
            exec_args.extend(["--query", cmd_to_backend, "--execute", "--json", "--working-dir", self.gui_current_working_dir])
            self.log_message(f"Backend exec cmd (AI-gen): {exec_path} {' '.join(exec_args)}", "debug_backend")
            self.current_exec_process.start(exec_path, exec_args)
            if not self.current_exec_process.waitForStarted(10000):
                self.log_message(f"Error starting backend (AI-gen exec): {self.current_exec_process.errorString()}", "error", True)
                self.stop_processing_animation()
                if self.current_exec_process: self.current_exec_process.deleteLater(); self.current_exec_process = None

    def handle_execution_stdout_from_backend(self, proc: Optional[QProcess]):
        # No stop_processing_animation here, wait for finished signal or explanation request
        if not proc: return
        raw_data = proc.readAllStandardOutput().data().decode().strip()
        if not raw_data: return
        self.log_message(f"Backend Exec STDOUT (JSON expected): {raw_data}", "debug_backend")
        try:
            res = json.loads(raw_data)
            if res.get("stdout"): self.log_message(res.get("stdout").strip(), "system", True)
            if not res.get("success", False) and res.get("stderr"): self.log_message(res.get("stderr").strip(), "error", True)
            new_wd = res.get("working_dir")
            if new_wd and os.path.abspath(new_wd) != self.gui_current_working_dir:
                self.gui_current_working_dir = os.path.abspath(new_wd)
                self.log_message(f"GUI: Working directory updated to: {self.gui_current_working_dir}", "debug_backend")
            fix_sugg = res.get("fix_suggestion")
            if fix_sugg: self.log_message(f"\n--- AI Fix Suggestion ---\n{fix_sugg}\n--------------------------", "assistant", True)
        except json.JSONDecodeError: self.log_message(f"Backend Exec (non-JSON STDOUT): {raw_data}", "system", True)

    def handle_execution_stderr_from_backend(self, proc: Optional[QProcess]):
        # No stop_processing_animation here
        if not proc: return
        raw_data = proc.readAllStandardError().data().decode().strip()
        if raw_data: self.log_message(f"Backend Exec STDERR (raw): {raw_data}", "debug_backend")

    def execution_process_finished_from_backend(self, exit_code: int, exit_status: QProcess.ExitStatus, executed_command: str, proc: Optional[QProcess]):
        # Stop general "Executing command..." animation if it was active for this process
        if self.is_processing_animation_active and self._current_animation_message.startswith("Executing"):
            self.stop_processing_animation(restore_placeholder=False) # Will be filled by explanation or error

        status = "successfully" if exit_code == 0 and exit_status == QProcess.NormalExit else f"with code {exit_code}"
        msg_type = "success" if exit_code == 0 and exit_status == QProcess.NormalExit else "error"
        self.log_message(f"Execution of '{executed_command}' via backend finished {status}.", msg_type, True)

        if self.waiting_for_basic_command_explanation_for == executed_command:
            self.request_ai_explanation_for_executed_command(executed_command) # This will manage its own animation
            self.waiting_for_basic_command_explanation_for = None
        elif self.current_command and executed_command.strip() == self.current_command.strip(): # AI-gen cmd finished
            self.generated_command_panel.hide() # Hide panel after execution
            self.ai_output_display.clear()      # Clear explanation area too
            self.current_command = None; self.current_command_suggested_interaction_input = None
            self.execute_button.setText("Execute")

        if proc and proc == self.current_exec_process:
             proc.deleteLater(); self.current_exec_process = None

    def copy_content(self):
        clipboard = QApplication.clipboard()
        text_to_copy = ""
        log_msg = ""
        if self.generated_command_panel.isVisible() and self.generated_command_display.toPlainText().strip():
            text_to_copy = self.generated_command_display.toPlainText().strip()
            log_msg = "Displayed command copied to clipboard."
        elif self.ai_output_display.toPlainText().strip() and not self.ai_output_display.placeholderText() == self.ai_output_display.toPlainText():
            text_to_copy = self.ai_output_display.toPlainText().strip()
            log_msg = "AI output/explanation copied to clipboard."

        if text_to_copy: clipboard.setText(text_to_copy); self.log_message(log_msg, "success", True)
        else: self.log_message("Nothing to copy.", "system", True)

    def cancel_generated_command(self):
        self.generated_command_panel.hide()
        self.generated_command_display.clear()
        self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
        self.ai_output_display.clear()
        self.current_command = None; self.current_command_suggested_interaction_input = None
        self.execute_button.setText("Execute"); self.execute_button.setEnabled(True)
        self.generated_command_header_label.setText("Generated Command:")
        self.log_message("Command cancelled.", "system", True)

    def load_explanations_cache(self):
        try:
            if os.path.exists(EXPLANATIONS_CACHE_FILE):
                with open(EXPLANATIONS_CACHE_FILE, 'r', encoding='utf-8') as f: self.explanations_cache = json.load(f)
            else: self.explanations_cache = {}
        except Exception as e: self.log_message(f"Error loading explanations cache: {e}", "error", True); self.explanations_cache = {}

    def save_explanations_cache(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(EXPLANATIONS_CACHE_FILE, 'w', encoding='utf-8') as f: json.dump(self.explanations_cache, f, indent=2)
        except Exception as e: self.log_message(f"Error saving explanations cache: {e}", "error", True)

    def update_realtime_analysis(self):
        txt = self.input_field.text().strip()
        # Don't clear ai_output_display if it's showing a result from a previous command
        if not self.generated_command_panel.isVisible():
            if not txt:
                self.ai_output_display.clear()
                self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
                return
            if len(txt) < 4:
                self.ai_output_display.setText("Keep typing...")
                _ = self.explanation_timer and self.explanation_timer.stop()
                return

        if self.explanation_timer and self.explanation_timer.isActive(): self.explanation_timer.stop()
        if not self.explanation_timer:
            self.explanation_timer = QTimer(self); self.explanation_timer.setSingleShot(True)
            self.explanation_timer.timeout.connect(lambda: self.request_command_analysis_and_explanation(self.input_field.text().strip()))
        self.explanation_timer.start(1200)

    def request_command_analysis_and_explanation(self, text_input: str):
        if not text_input:
            if not self.generated_command_panel.isVisible(): # Only clear if no command panel is shown
                self.ai_output_display.clear()
                self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
            return
        if not self.ai_engine_for_gui:
            if not self.generated_command_panel.isVisible(): self.ai_output_display.setText("AI for real-time analysis N/A.")
            return
        if text_input in self.explanations_cache:
            if not self.generated_command_panel.isVisible(): self.ai_output_display.setText(f"Cached: {self.explanations_cache[text_input]}")
            return

        # Only show "Analyzing..." if no command panel is active
        if not self.generated_command_panel.isVisible():
            self.ai_output_display.setText("Analyzing input with AI...")

        try:
            lang_instr_gui = self._get_gui_ai_language_instruction()
            api_res: Optional[GeminiApiResponse] = self.ai_engine_for_gui.analyze_text_input_type(text_input, language_instruction=lang_instr_gui)

            # Only update ai_output_display if no command panel is active
            if not self.generated_command_panel.isVisible():
                if api_res and api_res.success:
                    tt, expl = api_res.analyzed_text_type, api_res.explanation
                    if tt == "linux_command": self.ai_output_display.setText(f"Cmd: {expl if expl else 'No specific explanation.'}");_ = expl and setattr(self.explanations_cache, text_input, expl) and self.save_explanations_cache()
                    elif tt == "natural_language_query": self.ai_output_display.setText(f"Query: {expl if expl else 'Seems like a query.'}")
                    elif tt == "question_about_cwd": self.ai_output_display.setText(f"Question about files: {expl if expl else 'Understood as a question about CWD.'}")
                    elif tt == "error": self.ai_output_display.setText(f"AI Analysis Error: {expl}")
                    else: self.ai_output_display.setText("Input Type: Other/Uncertain.")
                elif api_res:
                    err_msg = api_res.error or "Unknown AI error."
                    quota_err_msg = "AI API quota exceeded for real-time analysis."
                    if "quota" in err_msg.lower() and ("429" in err_msg or "ResourceExhausted" in err_msg): self.ai_output_display.setText(quota_err_msg)
                    else: self.ai_output_display.setText(f"AI Analysis Network Error: {err_msg}")
                    self.log_message(f"Error during real-time text input analysis: {err_msg}", "error", True)
                else: self.ai_output_display.setText("AI Analysis did not return a response.")
        except Exception as e:
            if not self.generated_command_panel.isVisible(): self.ai_output_display.setText(f"Exception: {e}")
            self.log_message(f"Exception in real-time analysis: {e}", "error", True)

    def handle_complex_query(self, original_query: str):
        self.log_message(f"AI requested clarification for: \"{original_query}\". Generating questions...", "system", True)
        self.start_processing_animation(f"AI needs clarification for: {original_query[:30]}...")
        questions: List[str] = [];
        if self.ai_engine_for_gui:
            try:
                lang_instr_gui = self._get_gui_ai_language_instruction()
                questions = self.ai_engine_for_gui.generate_clarification_questions(original_query, {"ID": "linux"}, self.gui_current_working_dir, language_instruction=lang_instr_gui)
            except Exception as e: self.log_message(f"Error generating clarification questions: {e}", "error", True)

        self.stop_processing_animation(restore_placeholder=False) # Dialog will take over
        if not questions: questions = ["Describe your main goal?", "Specific files/dirs/params involved?", "Expected outcome?"]

        dialog = ClarificationDialog(self, original_query, questions)
        if dialog.exec_():
            answers = dialog.get_answers(); detailed_query = original_query
            clarifs = [f"User: '{q}' -> '{a.strip()}'" for q,a in zip(questions, answers) if a.strip()]
            if clarifs: detailed_query += "\n\n--- User Clarifications ---\n" + "\n".join(clarifs)
            self.log_message("Processing with user clarifications...", "system", True)
            self.start_processing_animation("Processing clarified query...")
            self.process_detailed_query(detailed_query)
        else:
            self.log_message("Clarification cancelled.", "system", True)
            self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
            self.ai_output_display.clear()


    def process_detailed_query(self, detailed_query: str):
        self.log_message("Processing (detailed) query with backend...", "debug_backend")
        if self.process and self.process.state() == QProcess.Running:
            self.log_message("Backend busy.", "error", True)
            self.stop_processing_animation() # Stop if we can't start a new one
            return
        self.process = QProcess(self); self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr); self.process.finished.connect(self.process_finished)
        env = QProcessEnvironment.systemEnvironment(); env.insert("GOOGLE_API_KEY", self.config["api_keys"]["gemini"])
        env.insert("LAA_BACKEND_MODE", "1"); env.insert("LAA_VERBOSE_LOGGING_EFFECTIVE", "1" if self.verbose_logging else "0")
        self.process.setProcessEnvironment(env)
        exec_path, exec_args = (sys.executable, []) if getattr(sys,'frozen',False) else (sys.executable, [os.path.join(os.path.dirname(os.path.abspath(__file__)),"src","backend_cli.py")])
        if not getattr(sys, 'frozen', False) and not os.path.exists(exec_args[0]):
            self.log_message(f"CRITICAL: Dev backend_cli.py not found: {exec_args[0]}", "error", True)
            self.stop_processing_animation(); return
        exec_args.extend(["--query", detailed_query, "--json", "--working-dir", self.gui_current_working_dir])
        self.log_message(f"Cmd to backend (detailed_query): {exec_path} {' '.join(exec_args)}", "debug_backend")
        self.process.start(exec_path, exec_args)
        if not self.process.waitForStarted(7000):
            self.log_message(f"Error starting backend: {self.process.errorString()}", "error", True)
            self.stop_processing_animation()
            _ = self.process and self.process.deleteLater(); self.process = None

    def start_new_session(self):
        if QMessageBox.question(self,"New Session","This will close current assistant. Sure?", QMessageBox.Yes|QMessageBox.No,QMessageBox.No) == QMessageBox.Yes:
            try:
                qapp = QApplication.instance()
                if qapp:
                    exec_path, exec_args = (sys.executable, []) if getattr(sys,'frozen',False) else (sys.executable, [os.path.abspath(sys.argv[0])])
                    QProcess.startDetached(exec_path, exec_args); qapp.quit()
            except Exception as e: self.log_message(f"Error starting new session: {e}", "error", True)

    def save_session(self):
        fpath, _ = QFileDialog.getSaveFileName(self,"Save Log",os.path.expanduser("~/laa_session.txt"),"Text (*.txt);;All (*)")
        if fpath:
            try:
                with open(fpath,'w',encoding='utf-8') as f: f.write(self.terminal.toPlainText())
                self.log_message(f"Log saved to {fpath}", "success", True)
            except Exception as e: self.log_message(f"Error saving log: {e}", "error", True)

    def eventFilter(self, obj, event):
        if obj is self.input_field and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                if not self.input_history: return True
                if self.current_history_index == len(self.input_history):
                    self.pending_input_text = self.input_field.text()
                if self.current_history_index > 0:
                    self.current_history_index -= 1
                    self.input_field.setText(self.input_history[self.current_history_index])
                    self.input_field.selectAll()
                return True
            elif key == Qt.Key_Down:
                if not self.input_history: return True
                if self.current_history_index < len(self.input_history) -1:
                    self.current_history_index += 1
                    self.input_field.setText(self.input_history[self.current_history_index])
                    self.input_field.selectAll()
                elif self.current_history_index == len(self.input_history) -1:
                    self.current_history_index +=1
                    self.input_field.setText(self.pending_input_text)
                return True
        return super().eventFilter(obj, event)


def main_gui_entry_point():
    app = QApplication(sys.argv)
    window = LinuxAIAssistantGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    if not _IS_BACKEND_MODE:
        main_gui_entry_point()
