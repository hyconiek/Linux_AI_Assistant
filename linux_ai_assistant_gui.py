#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import re
import shlex
import shutil
import locale
import socket
import subprocess
import traceback # Upewnij się, że jest
from typing import Dict, Optional, List, Any, Set
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                            QLabel, QDialog, QTabWidget, QCheckBox, QMessageBox,
                            QAction, QMenu, QStyle, QFileDialog, QStatusBar,
                            QDialogButtonBox, QFormLayout, QGroupBox, QSizePolicy,
                            QSpacerItem)
from PyQt5.QtGui import QFont, QIcon, QTextCursor, QColor, QPalette, QPixmap
from PyQt5.QtCore import Qt, QProcess, QSettings, QSize, pyqtSignal, QTimer, QProcessEnvironment, QEvent


# --- Constants for Pre-filled Cache ---
PREFILLED_EXPLANATIONS_CACHE_EN: Dict[str, str] = {
    "ls": "List directory contents.", "ls -l": "List directory contents in long format.",
    "ls -a": "List all directory contents, including hidden files.", "ls -la": "List all directory contents in long format, including hidden files.",
    "cd <directory>": "Change the current working directory to <directory>.", "cd ..": "Change to the parent directory.",
    "cd ~": "Change to the home directory.", "cd /": "Change to the root directory.",
    "pwd": "Print the name of the current working directory.", "mkdir <directory>": "Create a new directory named <directory>.",
    "rmdir <directory>": "Remove an empty directory named <directory>.", "cp <source> <destination>": "Copy <source> file or directory to <destination>.",
    "cp -r <source_dir> <dest_dir>": "Copy directory <source_dir> recursively to <dest_dir>.", "mv <source> <destination>": "Move or rename <source> file or directory to <destination>.",
    "cat <file>": "Concatenate and display the content of <file>.", "echo \"<text>\"": "Display a line of <text>.",
    "clear": "Clear the terminal screen.", "whoami": "Print the effective user ID.",
    "df": "Report file system disk space usage.", "df -h": "Report file system disk space usage in human-readable format.",
    "du <file/directory>": "Estimate file and directory space usage.", "du -sh <file/directory>": "Estimate space usage of <file/directory> in human-readable summary.",
    "free": "Display amount of free and used memory in the system.", "free -h": "Display amount of free and used memory in human-readable format.",
    "history": "Display the command history.", "ping <host>": "Send ICMP ECHO_REQUEST packets to <host>.",
    "ifconfig": "Configure network interface parameters (legacy, use 'ip addr' on modern systems).", "ip addr": "Show/manipulate network addresses.",
    "ip link": "Show/manipulate network devices.", "ip route": "Show/manipulate routing table.",
    "ssh <user@host>": "OpenSSH SSH client (remote login program).", "scp <source> <user@host:destination>": "Secure copy (remote file copy program).",
    "top": "Display Linux processes in real-time. Requires interactive terminal.", "htop": "Interactive process viewer. Requires interactive terminal.",
    "nano <file>": "Simple text editor. Requires interactive terminal.", "vim <file>": "Vi IMproved, a programmer's text editor. Requires interactive terminal.",
    "less <file>": "File pager. Requires interactive terminal.", "man <command>": "Display the on-line manual pages. Requires interactive terminal.",
    "ps aux": "Report a snapshot of current processes (BSD syntax).", "ps -ef": "Report a snapshot of current processes (System V syntax).",
    "kill <pid>": "Send a signal to a process with ID <pid> (default SIGTERM).", "kill -9 <pid>": "Forcefully kill a process with ID <pid> (SIGKILL).",
    "sudo <command>": "Execute <command> as the superuser.", "apt update": "(Debian/Ubuntu) Update the package list.",
    "apt upgrade": "(Debian/Ubuntu) Upgrade installed packages.", "apt install <package>": "(Debian/Ubuntu) Install <package>.",
    "apt remove <package>": "(Debian/Ubuntu) Remove <package>.", "apt autoremove": "(Debian/Ubuntu) Remove automatically installed packages that are no longer needed.",
    "dnf check-update": "(Fedora/RHEL) Check for package updates.", "dnf upgrade": "(Fedora/RHEL) Upgrade installed packages.",
    "dnf install <package>": "(Fedora/RHEL) Install <package>.", "dnf remove <package>": "(Fedora/RHEL) Remove <package>.",
    "dnf autoremove": "(Fedora/RHEL) Remove packages installed as dependencies that are no longer needed.", "yum check-update": "(Older RHEL/CentOS) Check for package updates.",
    "yum update": "(Older RHEL/CentOS) Update installed packages.", "yum install <package>": "(Older RHEL/CentOS) Install <package>.",
    "yum remove <package>": "(Older RHEL/CentOS) Remove <package>.", "pacman -Syu": "(Arch) Synchronize package databases and upgrade all packages.",
    "pacman -S <package>": "(Arch) Install <package>.", "pacman -R <package>": "(Arch) Remove <package>.",
    "pacman -Rns <package>": "(Arch) Remove <package> and its dependencies not required by other packages.", "zypper refresh": "(openSUSE) Refresh repositories.",
    "zypper up": "(openSUSE) Update installed packages.", "zypper in <package>": "(openSUSE) Install <package>.",
    "zypper rm <package>": "(openSUSE) Remove <package>.", "rm <file>": "Remove (delete) <file>. Use with caution.",
    "rm -r <directory>": "Remove <directory> and its contents recursively. Use with extreme caution.", "rm -rf <directory/file>": "Forcefully remove <directory/file> recursively without prompting. EXTREMELY DANGEROUS, can lead to data loss."
}

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
            meipass_path = sys._MEIPASS
            print(f"Contents of MEIPASS ({meipass_path}): {os.listdir(meipass_path)}", file=sys.stderr)
            src_in_meipass = os.path.join(meipass_path, 'src')
            if os.path.exists(src_in_meipass) and os.path.isdir(src_in_meipass):
                print(f"MEIPASS/src content: {os.listdir(src_in_meipass)}", file=sys.stderr)
            else:
                print(f"MEIPASS/src dir not found or is not a directory: {src_in_meipass}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL BACKEND ERROR (Exception): {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

GeminiIntegration = None
GeminiApiResponse_class_ref = None
if not _IS_BACKEND_MODE:
    try:
        module_base_path = ""
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            module_base_path = os.path.join(sys._MEIPASS, "src")
        else:
            module_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")

        if module_base_path not in sys.path:
             sys.path.insert(0, module_base_path)
        from modules.gemini_integration import GeminiIntegration, GeminiApiResponse
        GeminiApiResponse_class_ref = GeminiApiResponse
    except ImportError as e:
        print(f"CRITICAL (GUI): Could not import GeminiIntegration module. Error: {e}", file=sys.stderr)
        print(f"Attempted module_base_path: {module_base_path}", file=sys.stderr)
        print(f"Current sys.path: {sys.path}", file=sys.stderr)
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            meipass_path = sys._MEIPASS
            print(f"Contents of MEIPASS ({meipass_path}): {os.listdir(meipass_path)}", file=sys.stderr)
            src_in_meipass = os.path.join(meipass_path, 'src')
            if os.path.exists(src_in_meipass) and os.path.isdir(src_in_meipass):
                 print(f"MEIPASS/src content: {os.listdir(src_in_meipass)}", file=sys.stderr)
                 modules_in_src = os.path.join(src_in_meipass, 'modules')
                 if os.path.exists(modules_in_src) and os.path.isdir(modules_in_src):
                      print(f"MEIPASS/src/modules content: {os.listdir(modules_in_src)}", file=sys.stderr)
                 else:
                      print(f"MEIPASS/src/modules dir not found: {modules_in_src}", file=sys.stderr)
            else:
                print(f"MEIPASS/src dir not found or is not a directory: {src_in_meipass}", file=sys.stderr)


CONFIG_DIR = os.path.expanduser("~/.config/linux_ai_assistant")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
EXPLANATIONS_CACHE_FILE = os.path.join(CONFIG_DIR, "explanations_cache.json")
COMMAND_HISTORY_FILE = os.path.join(CONFIG_DIR, "command_history.json")

DEFAULT_CONFIG = {
    "api_keys": {"gemini": "", "openai": "", "anthropic": ""},
    "show_instructions": True, "theme": "dark", "max_history": 100,
    "verbose_logging": True, "gui_model_name": 'gemini-1.5-flash-latest',
    "force_ai_for_commands": ["rm", "top", "htop", "nano", "vim", "less", "man"]
}

class ApiKeyDialog(QDialog):
    def __init__(self, parent=None, api_key=""):
        super().__init__(parent)
        self.setWindowTitle("API Key Required")
        self.setMinimumWidth(500); self.setMinimumHeight(400)
        layout = QVBoxLayout(self); header_layout = QHBoxLayout()
        logo_label = QLabel();
        pixmap = QApplication.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(QSize(64, 64))
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
        instructions_text = (
            "<h2>Welcome to Linux AI Assistant</h2>"
            "<p>This assistant helps you with Linux commands by understanding your natural language requests.</p>"
            "<h3>How to use:</h3>"
            "<ol>"
            "<li>Type your request in natural language (e.g., 'Show all running processes') or a direct command (e.g. 'ls -la').</li>"
            "<li>The assistant will generate a suitable Linux command or answer your question about files.</li>"
            "<li>If you type a basic command (like 'ls', 'cd', 'pwd'), it will execute directly, and an AI explanation will follow.</li>"
            "<li>Commands like 'top', 'htop', 'nano', 'vim', 'less', 'man' will be suggested to run in a new terminal.</li>"
            "<li>Review the command and its explanation, or the AI's answer.</li>"
            "<li>Click 'Execute' (or the suggested action button, e.g., 'Run in Terminal'), 'Copy', or if a command is suggested, you can also type <b>'t'</b> in the input field and press <b>Enter</b> to confirm execution.</li>"
            "<li>Use Up/Down arrows in the input field to navigate command history.</li>"
            "</ol>"
            "<h3>Offline Mode:</h3>"
            "<p>If no internet connection is detected, the assistant will switch to offline mode:</p>"
            "<ul>"
            "<li>AI command generation will be disabled.</li>"
            "<li>Explanations for commands will be served from a local cache if available.</li>"
            "<li>Basic commands will still execute directly.</li>"
            "<li>Commands listed in Settings to 'Force AI Processing' (like 'rm' or 'top') will require 'Execute'/'Run in Terminal' confirmation if found in cache; otherwise, they are blocked for safety if they require AI.</li>"
            "</ul>"
            "<h3>Example requests:</h3>"
            "<ul>"
            "<li>Show disk usage in human-readable format</li>"
            "<li>Are there any '.log' files here?</li>"
            "<li>Find all PDF files in my home directory</li>"
            "</ul>"
            "<p>You can access settings by clicking the gear icon in the top-right corner.</p>"
        )
        instructions = QLabel(instructions_text)
        instructions.setOpenExternalLinks(True); instructions.setWordWrap(True); layout.addWidget(instructions)
        self.show_again_checkbox = QCheckBox("Do not show this again"); self.show_again_checkbox.setChecked(not show_again)
        layout.addWidget(self.show_again_checkbox)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok); button_box.accepted.connect(self.accept); layout.addWidget(button_box)
    def should_show_again(self): return not self.show_again_checkbox.isChecked()

class SettingsDialog(QDialog):
    force_ai_commands_updated = pyqtSignal(list)
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("Settings"); self.setMinimumWidth(550); self.setMinimumHeight(500)
        self.config = config if config else DEFAULT_CONFIG.copy()
        self.parent_gui = parent

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
        self.force_ai_commands_input.setToolTip("Comma-separated command prefixes (e.g., rm, mv, top) that should always be processed by AI, not executed directly as basic commands.")
        force_ai_form.addRow("Commands:", self.force_ai_commands_input)
        general_layout.addWidget(force_ai_group)

        model_group = QGroupBox("GUI AI Model")
        model_form = QFormLayout(model_group)
        self.gui_model_input = QLineEdit(self.config.get("gui_model_name", DEFAULT_CONFIG["gui_model_name"]))
        self.gui_model_input.setToolTip("Model used for real-time explanations and clarification questions in GUI (e.g., gemini-1.5-flash-latest).")
        model_form.addRow("Model Name:", self.gui_model_input)
        general_layout.addWidget(model_group)

        theme_group = QGroupBox("Theme"); theme_form = QFormLayout(theme_group)
        self.theme_dark_checkbox = QCheckBox("Dark mode")
        self.theme_dark_checkbox.setChecked(self.config.get("theme", "dark") == "dark")
        theme_form.addRow(self.theme_dark_checkbox)
        general_layout.addWidget(theme_group)

        cache_group = QGroupBox("Explanations Cache")
        cache_layout = QHBoxLayout(cache_group)
        self.export_cache_button = QPushButton("Export Cache")
        self.export_cache_button.clicked.connect(self.export_cache)
        cache_layout.addWidget(self.export_cache_button)
        self.import_cache_button = QPushButton("Import Cache")
        self.import_cache_button.clicked.connect(self.import_cache)
        cache_layout.addWidget(self.import_cache_button)
        general_layout.addWidget(cache_group)

        general_layout.addStretch(); tabs.addTab(general_tab, "General")
        layout.addWidget(tabs)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject); layout.addWidget(button_box)

    def on_accept(self):
        old_force_ai_cmds = set(self.config.get("force_ai_for_commands", []))
        new_config_values = self.get_config_values()
        new_force_ai_cmds_list = new_config_values.get("force_ai_for_commands", [])
        newly_added_force_ai = [cmd for cmd in new_force_ai_cmds_list if cmd not in old_force_ai_cmds]
        if newly_added_force_ai:
            self.force_ai_commands_updated.emit(newly_added_force_ai)
        self.accept()

    @staticmethod
    def toggle_key_visibility_static(state, input_field): input_field.setEchoMode(QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password)

    def get_config_values(self) -> Dict:
        updated_config = self.config.copy()
        for api_name_lower in ["gemini", "openai", "anthropic"]:
            key_input_widget = getattr(self, f"{api_name_lower}_key_input", None)
            if key_input_widget: updated_config["api_keys"][api_name_lower] = key_input_widget.text().strip()
        updated_config["show_instructions"] = self.show_instructions_checkbox.isChecked()
        updated_config["verbose_logging"] = self.verbose_logging_checkbox_settings.isChecked()
        try:
            max_hist_val = int(self.max_history_input.text())
            if 10 <= max_hist_val <= 999: updated_config["max_history"] = max_hist_val
            else: updated_config["max_history"] = self.config.get("max_history", DEFAULT_CONFIG["max_history"])
        except ValueError: updated_config["max_history"] = self.config.get("max_history", DEFAULT_CONFIG["max_history"])
        force_ai_text = self.force_ai_commands_input.text().strip()
        if force_ai_text: updated_config["force_ai_for_commands"] = [cmd.strip().lower() for cmd in force_ai_text.split(',') if cmd.strip()]
        else: updated_config["force_ai_for_commands"] = []
        updated_config["gui_model_name"] = self.gui_model_input.text().strip() or DEFAULT_CONFIG["gui_model_name"]
        updated_config["theme"] = "dark" if self.theme_dark_checkbox.isChecked() else "light"
        return updated_config

    def export_cache(self):
        if not self.parent_gui or not hasattr(self.parent_gui, 'explanations_cache'): return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Explanations Cache", os.path.expanduser("~/explanations_cache_export.json"), "JSON files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f: json.dump(self.parent_gui.explanations_cache, f, indent=2)
                QMessageBox.information(self, "Cache Exported", f"Cache successfully exported to {file_path}")
            except Exception as e: QMessageBox.warning(self, "Export Error", f"Could not export cache: {e}")

    def import_cache(self):
        if not self.parent_gui or not hasattr(self.parent_gui, 'explanations_cache'): return
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Explanations Cache", os.path.expanduser("~"), "JSON files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f: imported_cache = json.load(f)
                if not isinstance(imported_cache, dict): raise ValueError("Imported cache is not a valid format (not a dictionary).")
                self.parent_gui.explanations_cache.update(imported_cache)
                self.parent_gui.save_explanations_cache()
                QMessageBox.information(self, "Cache Imported", f"Cache successfully imported from {file_path} and merged.")
            except Exception as e: QMessageBox.warning(self, "Import Error", f"Could not import cache: {e}")


class SudoPasswordDialog(QDialog):
    def __init__(self, parent=None, command=""):
        super().__init__(parent)
        self.setWindowTitle("Sudo Privileges Required"); self.setMinimumWidth(500)
        layout = QVBoxLayout(self); header_layout = QHBoxLayout()
        warning_icon_label = QLabel()
        pixmap = QApplication.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(QSize(48,48))
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
            "debug_backend": QColor("#FFA500"), "ai_text_answer": QColor("#87CEFA"),
            "offline_status": QColor("#FFCC00")
        }
    def append_message(self, text, message_type="system"):
        self.moveCursor(QTextCursor.End); cursor = self.textCursor(); char_format = cursor.charFormat()
        text_color = self.palette().color(QPalette.Text)
        if message_type in self.colors:
            text_color = self.colors.get(message_type, text_color)
        char_format.setForeground(text_color); cursor.setCharFormat(char_format)
        cursor.insertText(text + "\n"); self.moveCursor(QTextCursor.End); self.ensureCursorVisible()


class LinuxAIAssistantGUI(QMainWindow):
    def load_input_history(self):
        self.input_history = []
        self.current_history_index = 0
        if os.path.exists(COMMAND_HISTORY_FILE):
            try:
                with open(COMMAND_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.input_history = json.load(f)
                max_h = self.config.get("max_history", DEFAULT_CONFIG["max_history"])
                if len(self.input_history) > max_h:
                    self.input_history = self.input_history[-max_h:]
                self.current_history_index = len(self.input_history)
                self.log_message(f"Loaded {len(self.input_history)} commands from history.", "debug_backend")
            except Exception as e:
                self.log_message(f"Error loading command history: {e}", "error", True)
                self.input_history = []
                self.current_history_index = 0
        else:
            self.log_message("Command history file not found. Starting with empty history.", "debug_backend")

    def save_input_history(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            max_h = self.config.get("max_history", DEFAULT_CONFIG["max_history"])
            history_to_save = self.input_history[-max_h:]
            with open(COMMAND_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history_to_save, f, indent=2)
            self.log_message(f"Saved {len(history_to_save)} commands to history file.", "debug_backend")
        except Exception as e:
            self.log_message(f"Error saving command history: {e}", "error", True)



    def __init__(self):
        super().__init__()
        self._theme_applied_once = False # Ten może zostać tutaj
        self.current_command: Optional[str] = None
        self.process: Optional[QProcess] = None
        self.current_exec_process: Optional[QProcess] = None
        self.gui_current_working_dir = os.path.expanduser("~")
        if not os.path.isdir(self.gui_current_working_dir):
            self.gui_current_working_dir = os.path.abspath(os.getcwd())
        self.last_api_response: Optional[GeminiApiResponse_class_ref] = None

        self.config: Dict[str, Any] = {}
        # 1. Inicjalizacja konfiguracji (ważne dla max_history, verbose_logging itp.)
        self.init_config()
        self.verbose_logging = self.config.get("verbose_logging", True) # Ustaw zaraz po wczytaniu configu

        # 2. Inicjalizacja UI (tworzy self.terminal i inne widgety)
        # Musi być przed log_message, load_input_history, load_explanations_cache, _init_ai_engine_for_gui
        self.init_ui() # PRZENIESIONE WCZEŚNIEJ

        # Te atrybuty mogą być inicjalizowane przed init_ui, jeśli init_ui ich nie używa od razu
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

        # 3. Teraz można bezpiecznie ładować historię i cache, bo self.terminal istnieje
        self.load_input_history()
        self.load_explanations_cache() # load_explanations_cache też używa log_message

        self.basic_command_prefixes: Set[str] = {
            "ls", "cd", "pwd", "mkdir", "cp", "mv", "cat", "echo", "clear", "whoami",
            "df", "du", "free", "sensors", "kill",
            "apt", "dnf", "yum", "pacman", "zypper", "sudo"
        }
        self.interactive_commands_requiring_new_terminal: Set[str] = {"top", "htop", "nano", "vim", "less", "man", "mc", "ssh", "ping"}

        self.is_offline = False
        self.internet_check_timer = QTimer(self)
        self.internet_check_timer.timeout.connect(self.perform_internet_check)

        # 4. Pozostałe inicjalizacje
        self._init_ai_engine_for_gui() # To też używa log_message
        self.apply_theme() # apply_theme używa log_message, więc musi być po init_ui
        self.check_api_key() # To może wywołać prompt_for_api_key, które używa log_message

        if self.config.get("show_instructions", True):
            QTimer.singleShot(200, self.show_instructions) # show_instructions to dialog, nie używa log_message

        self.perform_internet_check() # To używa log_message
        self.internet_check_timer.start(60000)

    def perform_internet_check(self):
        previous_offline_state = self.is_offline
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            self.is_offline = False
            if previous_offline_state:
                self.log_message("Internet connection restored. Online mode active.", "success", True)
                self.status_bar.showMessage("Online mode", 3000)
                if not self.ai_engine_for_gui or not self.ai_engine_for_gui.is_configured:
                    self._init_ai_engine_for_gui()
        except OSError:
            self.is_offline = True
            if not previous_offline_state:
                self.log_message("No internet connection. Switching to offline mode.", "offline_status", True)
                self.status_bar.showMessage("Offline mode - AI features limited", 0)
                if self.ai_engine_for_gui:
                    self.log_message("Offline: GUI AI engine will not be used until connection is restored.", "offline_status", True)
        if not self.generated_command_panel.isVisible():
            if self.is_offline:
                self.ai_output_display.setPlaceholderText("Offline Mode: Real-time analysis disabled. Basic commands will execute directly.")
            else:
                if hasattr(self, '_original_ai_output_placeholder'):
                    self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
                else:
                     self.ai_output_display.setPlaceholderText("Type a command or query... Analysis or explanation will appear here.")
            if not self.input_field.text().strip(): self.ai_output_display.clear()

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
        if self.is_offline:
            self.log_message("Offline: GUI AI engine initialization skipped.", "offline_status", True)
            self.ai_engine_for_gui = None
            return

        if not _IS_BACKEND_MODE and GeminiIntegration is not None:
            api_key = self.config["api_keys"].get("gemini", "")
            gui_model = self.config.get("gui_model_name", DEFAULT_CONFIG["gui_model_name"])
            if api_key:
                original_env_api_key = os.environ.get('GOOGLE_API_KEY') # Zapisz przed blokiem try
                try:
                    os.environ['GOOGLE_API_KEY'] = api_key
                    self.ai_engine_for_gui = GeminiIntegration(model_name=gui_model)
                    if self.ai_engine_for_gui.is_configured:
                        self.log_message(f"AI engine for GUI (model: {gui_model}) initialized.", "system")
                    else:
                        self.log_message(f"Failed to configure AI engine for GUI. Check logs for details.", "error", True)
                        self.ai_engine_for_gui = None
                except Exception as e:
                    self.log_message(f"Error initializing AI engine for GUI: {e}", "error", True)
                    self.ai_engine_for_gui = None
                finally: # Zawsze przywracaj
                    if original_env_api_key is not None: os.environ['GOOGLE_API_KEY'] = original_env_api_key
                    elif 'GOOGLE_API_KEY' in os.environ: del os.environ['GOOGLE_API_KEY']
            else:
                self.log_message("Gemini API key not set. GUI AI features (real-time analysis) disabled.", "system")
                self.ai_engine_for_gui = None
        elif GeminiIntegration is None:
            self.log_message("GeminiIntegration module could not be imported. GUI AI features disabled.", "error", True)
            self.ai_engine_for_gui = None

    def init_ui(self):
        self.setWindowTitle("Linux AI Assistant"); self.setMinimumSize(800, 600)
        icon_path = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))), "laia_icon.png")
        if os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))
        else: self.setWindowIcon(QApplication.style().standardIcon(QStyle.SP_ComputerIcon))

        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.terminal = TerminalWidget(); main_layout.addWidget(self.terminal, 1)
        input_layout = QHBoxLayout(); self.prompt_label = QLabel("> ")
        self.prompt_label.setObjectName("PromptLabel")
        input_layout.addWidget(self.prompt_label); self.input_field = QLineEdit(); self.input_field.setObjectName("InputField")
        self.input_field.returnPressed.connect(self.process_input); self.input_field.textChanged.connect(self.update_realtime_analysis)
        self.input_field.installEventFilter(self)
        input_layout.addWidget(self.input_field);
        self.ai_output_header_label = QLabel("AI Analysis / Explanation / Answer:")
        self.ai_output_header_label.setObjectName("AIOutputHeaderLabel")
        main_layout.addWidget(self.ai_output_header_label)
        self.ai_output_display = QTextEdit()
        self.ai_output_display.setObjectName("AIOutputDisplay")
        self.ai_output_display.setReadOnly(True)
        self._original_ai_output_placeholder = "Type a command or query... Analysis or explanation will appear here."
        self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
        fm_aio = self.ai_output_display.fontMetrics(); lh_aio = fm_aio.height()
        dm_aio = int(self.ai_output_display.document().documentMargin() * 2)
        m_aio = self.ai_output_display.contentsMargins()
        p_aio = m_aio.top() + m_aio.bottom() + dm_aio
        self.ai_output_display.setMinimumHeight(int(lh_aio * 1.5) + p_aio)
        self.ai_output_display.setMaximumHeight(int(lh_aio * 4.5) + p_aio)
        self.ai_output_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.ai_output_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_layout.addWidget(self.ai_output_display)
        self.generated_command_panel = QWidget()
        generated_command_layout = QVBoxLayout(self.generated_command_panel)
        generated_command_layout.setContentsMargins(0, 5, 0, 0)
        self.generated_command_header_label = QLabel("Generated/Executed Command:")
        self.generated_command_header_label.setObjectName("GeneratedCommandHeaderLabel")
        generated_command_layout.addWidget(self.generated_command_header_label)
        self.generated_command_display = QTextEdit()
        self.generated_command_display.setObjectName("GeneratedCommandDisplay")
        self.generated_command_display.setReadOnly(True)
        self.generated_command_display.setLineWrapMode(QTextEdit.NoWrap)
        fm_cmd = self.generated_command_display.fontMetrics(); lh_cmd = fm_cmd.height()
        dm_cmd = int(self.generated_command_display.document().documentMargin() * 2)
        m_cmd = self.generated_command_display.contentsMargins()
        p_cmd = m_cmd.top() + m_cmd.bottom() + dm_cmd
        self.generated_command_display.setFixedHeight(lh_cmd + p_cmd + 5)
        self.generated_command_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.generated_command_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        generated_command_layout.addWidget(self.generated_command_display)
        button_layout = QHBoxLayout()
        self.execute_button = QPushButton("Execute"); self.copy_button = QPushButton("Copy"); self.cancel_button = QPushButton("Cancel")
        self.execute_button.setDefault(True)
        button_layout.addWidget(self.execute_button); button_layout.addWidget(self.copy_button)
        # Zmiana połączenia dla cancel_button
        self.cancel_button.clicked.connect(self.handle_cancel_or_stop_button)
        button_layout.addWidget(self.cancel_button)
        generated_command_layout.addLayout(button_layout)
        main_layout.addWidget(self.generated_command_panel)
        self.generated_command_panel.hide()
        main_layout.addLayout(input_layout)
        self.execute_button.clicked.connect(self.execute_command) # Ta linia powodowała błąd, teraz execute_command powinno istnieć
        self.copy_button.clicked.connect(self.copy_content)
        # self.cancel_button.clicked.connect(self.cancel_generated_command) # Zmienione na handle_cancel_or_stop_button
        menubar = self.menuBar(); file_menu = menubar.addMenu("File")
        new_session_action = QAction(QApplication.style().standardIcon(QStyle.SP_ToolBarHorizontalExtensionButton), "New Session", self)
        new_session_action.setShortcut("Ctrl+N"); new_session_action.triggered.connect(self.start_new_session)
        file_menu.addAction(new_session_action)
        file_menu.addAction(QAction("Save Session Log", self, shortcut="Ctrl+S", triggered=self.save_session))
        file_menu.addSeparator()
        settings_action_menu = QAction(QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Settings", self)
        settings_action_menu.setShortcut("Ctrl+,"); settings_action_menu.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action_menu)
        file_menu.addAction(QAction("Instructions", self, triggered=self.show_instructions))
        file_menu.addSeparator(); file_menu.addAction(QAction("Exit", self, shortcut="Ctrl+Q", triggered=self.close))
        help_menu = menubar.addMenu("Help"); help_menu.addAction(QAction("About", self, triggered=self.show_about))
        toolbar = self.addToolBar("Toolbar"); toolbar.setMovable(False); toolbar.setFloatable(False)
        toolbar.addAction(new_session_action)
        self.verbose_log_checkbox = QCheckBox("Verbose Backend Log")
        self.verbose_log_checkbox.setToolTip("Show detailed backend system/debug messages in this GUI terminal.")
        self.verbose_log_checkbox.setChecked(self.verbose_logging)
        self.verbose_log_checkbox.stateChanged.connect(self.toggle_verbose_logging)
        toolbar.addWidget(self.verbose_log_checkbox);
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        self.settings_button_action_toolbar = QAction(QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView), "Settings", self)
        self.settings_button_action_toolbar.triggered.connect(self.show_settings); toolbar.addAction(self.settings_button_action_toolbar)
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Initializing...", 2000)
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def apply_theme(self):
        dark = self.config.get("theme", "dark") == "dark"
        base_bg, base_fg, term_bg, term_user_fg, border, btn_bg, btn_hov, btn_press, btn_press_fg = (
            ("#282A36", "#F8F8F2", "#1E1E1E", "#F8F8F2", "#44475A", "#44475A", "#6272A4", "#50FA7B", "#282A36") if dark
            else ("#F0F0F0", "#333333", "#FFFFFF", "#000000", "#CCCCCC", "#E0E0E0", "#D0D0D0", "#50FA7B", "#282A36"))
        self.terminal.colors = {"system": QColor("#B0B0B0" if dark else "#707070"), "user": QColor(term_user_fg),
                                "assistant": QColor("#66FF66"), "command": QColor("#FFC266"), "error": QColor("#FF6666"),
                                "success": QColor("#66FF99"), "debug_backend": QColor("#FF8C00" if dark else "#FFA500"),
                                "ai_text_answer": QColor("#87CEFA" if dark else "#4682B4"),
                                "offline_status": QColor("#FFD700" if dark else "#FFBF00")}
        prompt_lbl_c = self.terminal.colors['user'].name()
        cmd_hdr_c = self.terminal.colors["command"].name()
        aio_hdr_c = (QColor("#8BE9FD") if dark else QColor("#1AA0D5")).name()
        qss = f"""
            QMainWindow, QDialog {{ background-color: {base_bg}; color: {base_fg}; }}
            QMenuBar {{ background-color: {base_bg}; color: {base_fg}; }} QMenuBar::item:selected {{ background-color: {btn_bg}; }}
            QMenu {{ background-color: {base_bg}; color: {base_fg}; border: 1px solid {border}; }} QMenu::item:selected {{ background-color: {btn_bg}; }}
            QToolBar {{ background-color: {base_bg}; border: none; }}
            QPushButton {{ background-color: {btn_bg}; color: {base_fg}; border: 1px solid {border}; padding: 5px 10px; border-radius: 3px; }}
            QPushButton:hover {{ background-color: {btn_hov}; }} QPushButton:pressed {{ background-color: {btn_press}; color: {btn_press_fg}; }}
            QPushButton:disabled {{ background-color: #3E404E; color: #707070; border-color: #30323E; }}
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
            QTextEdit#AIOutputDisplay {{ color: {aio_hdr_c}; }}
            QStatusBar {{ background-color: {base_bg}; color: {base_fg}; }}
            QStatusBar::item {{ border: none; }}
            """
        self.setStyleSheet(qss);
        current_font = QApplication.font()
        if current_font.family().lower() not in ["noto sans", "dejavu sans mono", "monospace"]:
             QApplication.instance().setFont(QFont("Noto Sans", 10 if current_font.pointSize() < 0 else current_font.pointSize()))
        if not self._theme_applied_once:
            self.log_message("=== Linux AI Assistant ===", "system", True);
            self.log_message(f"Current directory: {self.gui_current_working_dir}", "system", True)
            self.log_message(f"Type 'help' for instructions or a query.", "system", True)
            self._theme_applied_once = True
        else:
            pal = self.terminal.palette(); pal.setColor(QPalette.Text, self.terminal.colors["user"]); pal.setColor(QPalette.Base, QColor(term_bg)); self.terminal.setPalette(pal)
            aio_pal = self.ai_output_display.palette(); aio_pal.setColor(QPalette.Text, QColor(aio_hdr_c)); aio_pal.setColor(QPalette.Base, QColor({'#2C2F3A' if dark else '#FAFAFA'})); self.ai_output_display.setPalette(aio_pal)
            gcmd_pal = self.generated_command_display.palette(); gcmd_pal.setColor(QPalette.Text, QColor(cmd_hdr_c)); gcmd_pal.setColor(QPalette.Base, QColor({'#2C2F3A' if dark else '#FAFAFA'})); self.generated_command_display.setPalette(gcmd_pal)

    def update_prompt_label_text(self) -> str:
        path_parts = self.gui_current_working_dir.split(os.sep)
        home_char = "~" if self.gui_current_working_dir.startswith(os.path.expanduser("~")) else ""
        if home_char:
            rel_path = os.path.relpath(self.gui_current_working_dir, os.path.expanduser("~"))
            if rel_path == ".": display_path = "~"
            else:
                path_parts_rel = rel_path.split(os.sep)
                if len(path_parts_rel) > 2 : display_path = os.path.join("~", "...", path_parts_rel[-2], path_parts_rel[-1])
                else: display_path = os.path.join("~", rel_path)
        else:
            if len(path_parts) > 3: display_path = os.path.join(os.sep, "...", path_parts[-2], path_parts[-1])
            else: display_path = self.gui_current_working_dir
        return f"[{display_path}]> "

    def log_message(self, message: str, message_type: str = "system", force_show: bool = False):
        if message_type == "debug_backend" and not self.verbose_logging and not force_show: return
        prefix = ""
        if message_type == "user":
            prefix = self.update_prompt_label_text()
        self.terminal.append_message(f"{prefix}{message}", message_type)

    def load_explanations_cache(self):
        cache_loaded_from_file = False
        try:
            if os.path.exists(EXPLANATIONS_CACHE_FILE):
                with open(EXPLANATIONS_CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.explanations_cache = json.load(f)
                    cache_loaded_from_file = True
                    self.log_message("Explanations cache loaded from file.", "debug_backend")
            else: self.explanations_cache = {}
        except Exception as e:
            self.log_message(f"Error loading explanations cache: {e}. Initializing empty cache.", "error", True)
            self.explanations_cache = {}
        if not cache_loaded_from_file or not self.explanations_cache:
            self.log_message("Cache is empty or was not loaded. Pre-filling with basic command explanations (EN).", "system")
            self.explanations_cache.update(PREFILLED_EXPLANATIONS_CACHE_EN)
        else:
            updated_cache = False
            for cmd_key in DEFAULT_CONFIG["force_ai_for_commands"]:
                if cmd_key not in self.explanations_cache and cmd_key in PREFILLED_EXPLANATIONS_CACHE_EN:
                    self.explanations_cache[cmd_key] = PREFILLED_EXPLANATIONS_CACHE_EN[cmd_key]
                    updated_cache = True
            if updated_cache: self.log_message("Updated cache with default 'Force AI' command explanations.", "system")
        configured_force_ai = self.config.get("force_ai_for_commands", [])
        for cmd_prefix in configured_force_ai:
            if cmd_prefix not in self.explanations_cache:
                generic_key_found = False
                for k,v in PREFILLED_EXPLANATIONS_CACHE_EN.items():
                    if k.startswith(cmd_prefix + " ") or k == cmd_prefix:
                        self.explanations_cache[cmd_prefix] = v; generic_key_found = True; break
                if not generic_key_found: self.explanations_cache[cmd_prefix] = f"'{cmd_prefix}' requires AI confirmation. Explanation not cached."
                self.log_message(f"Added/updated placeholder for force-AI command '{cmd_prefix}' in cache.", "debug_backend")
        self.save_explanations_cache()

    def fetch_and_cache_force_ai_explanations(self, command_prefixes: List[str]):
        if self.is_offline or not self.ai_engine_for_gui or not self.ai_engine_for_gui.is_configured:
            self.log_message("Offline or AI not ready. Cannot fetch explanations for new Force AI commands now.", "offline_status" if self.is_offline else "error")
            for cmd_prefix in command_prefixes:
                if cmd_prefix not in self.explanations_cache: self.explanations_cache[cmd_prefix] = f"'{cmd_prefix}' is a command that requires careful execution. AI explanation not fetched yet."
            self.save_explanations_cache(); return

        self.log_message(f"Fetching explanations for newly added Force AI commands: {command_prefixes}", "system")
        lang_instr = self._get_gui_ai_language_instruction()
        for cmd_prefix in command_prefixes:
            if cmd_prefix not in self.explanations_cache or "not fetched yet" in self.explanations_cache.get(cmd_prefix, "") or "requires careful execution" in self.explanations_cache.get(cmd_prefix, "") :
                try:
                    placeholder_usage = cmd_prefix
                    if cmd_prefix == "rm": placeholder_usage = "rm example_file.txt"
                    elif cmd_prefix == "mv": placeholder_usage = "mv old_name new_name"
                    api_res = self.ai_engine_for_gui.analyze_text_input_type(placeholder_usage, language_instruction=lang_instr)
                    if api_res.success and api_res.explanation:
                        self.explanations_cache[cmd_prefix] = api_res.explanation
                        self.log_message(f"Fetched and cached explanation for '{cmd_prefix}'.", "success")
                    else:
                        error_detail = api_res.error if api_res else "No response from AI"
                        self.explanations_cache[cmd_prefix] = f"Could not fetch AI explanation for '{cmd_prefix}'. Error: {error_detail}"
                        self.log_message(f"Failed to fetch explanation for '{cmd_prefix}': {error_detail}", "error")
                except Exception as e:
                    self.explanations_cache[cmd_prefix] = f"Exception fetching AI explanation for '{cmd_prefix}'."
                    self.log_message(f"Exception fetching explanation for '{cmd_prefix}': {e}", "error")
        self.save_explanations_cache()

    def process_input(self):
        user_input = self.input_field.text().strip()

        if self.generated_command_panel.isVisible() and self.current_command:
            if user_input.lower() == 't':
                self.log_message("User confirmed 't' to execute.", "user", True)
                self.input_field.clear()
                self.execute_command()
                return

        if not user_input: return

        if not self.input_history or self.input_history[-1] != user_input:
            self.input_history.append(user_input)
            max_h = self.config.get("max_history", DEFAULT_CONFIG["max_history"])
            if len(self.input_history) > max_h:
                self.input_history = self.input_history[-max_h:]
            self.save_input_history()
        self.current_history_index = len(self.input_history); self.pending_input_text = ""
        self.input_field.clear(); self.log_message(f"{user_input}", "user", True)
        if user_input.lower() in ["exit", "quit"]: self.close(); return
        if user_input.lower() == "help": self.show_instructions(); return
        if user_input.lower() == "settings": self.show_settings(); return

        command_prefix = user_input.split(' ', 1)[0].lower()
        forced_ai_commands = set(self.config.get("force_ai_for_commands", ["rm"]))

        if self.is_offline:
            self.log_message("Offline mode: AI processing is limited.", "offline_status", True)
            if command_prefix in forced_ai_commands or command_prefix in self.interactive_commands_requiring_new_terminal:
                cached_explanation = self.explanations_cache.get(user_input) or self.explanations_cache.get(command_prefix)
                if cached_explanation:
                    self.log_message(f"'{command_prefix}' is a force-AI or interactive command. Found in cache.", "system")
                    self.generated_command_header_label.setText("Cached Command (Force AI/Interactive - Offline):")
                    self.generated_command_display.setText(user_input); self.ai_output_display.setText(cached_explanation)
                    self.generated_command_panel.show(); self.current_command = user_input
                    self.execute_button.setText("Run in Terminal" if command_prefix in self.interactive_commands_requiring_new_terminal else "Execute")
                    self.execute_button.setEnabled(True); self.current_command_suggested_interaction_input = "TERMINAL_REQUIRED" if command_prefix in self.interactive_commands_requiring_new_terminal else None
                else:
                    self.log_message(f"'{command_prefix}' requires AI/is interactive, but offline and not cached. Execution blocked.", "error", True)
                    self.ai_output_display.setText(f"Command '{user_input}' requires AI or is interactive. Offline and no cached info. Blocked for safety.")
                    self.generated_command_panel.hide()
                return

            is_basic_sudo = command_prefix == "sudo" and len(user_input.split()) > 1 and user_input.split()[1].lower() in self.basic_command_prefixes
            if (command_prefix in self.basic_command_prefixes or is_basic_sudo) and command_prefix not in self.interactive_commands_requiring_new_terminal:
                self.log_message(f"Basic command in offline mode: '{user_input}'. Executing directly.", "system")
                self.generated_command_panel.hide(); self.start_processing_animation("Executing command (Offline)..."); self.execute_basic_command(user_input)
            else:
                self.log_message("Cannot process complex query or run this interactive command with AI while offline.", "error", True)
                cached_expl = self.explanations_cache.get(user_input)
                if cached_expl: self.ai_output_display.setText(f"Offline. No AI generation. Cached explanation for '{user_input}':\n{cached_expl}")
                else: self.ai_output_display.setText("AI query processing is unavailable in offline mode. No cached explanation found.")
            return

        if command_prefix in forced_ai_commands or command_prefix in self.interactive_commands_requiring_new_terminal:
            self.log_message(f"Command '{command_prefix}' is configured to use AI or is interactive. Processing with AI...", "system")
            self.start_processing_animation("Processing AI query...")
            self.process_detailed_query(user_input); return

        is_basic_sudo = command_prefix == "sudo" and len(user_input.split()) > 1 and user_input.split()[1].lower() in self.basic_command_prefixes
        if (command_prefix in self.basic_command_prefixes or is_basic_sudo):
            self.log_message(f"Basic command detected: '{user_input}'. Executing directly.", "system")
            self.generated_command_panel.hide(); self.start_processing_animation("Executing command...")
            self.execute_basic_command(user_input); return

        if not self.config["api_keys"].get("gemini", ""):
            self.log_message("API key not set. Go to Settings.", "error", True); self.prompt_for_api_key(); return

        self.log_message("Processing query with AI backend...", "system")
        self.start_processing_animation("Processing AI query..."); self.process_detailed_query(user_input)

    def toggle_verbose_logging(self, state_int: int):
        self.verbose_logging = (state_int == Qt.Checked)
        self.config["verbose_logging"] = self.verbose_logging; self.save_config()
        self.log_message(f"Verbose backend logging (GUI display) {'enabled' if self.verbose_logging else 'disabled'}.", "system", True)

    def check_api_key(self):
        if not self.config["api_keys"].get("gemini", ""): QTimer.singleShot(100, self.prompt_for_api_key)

    def prompt_for_api_key(self):
        dialog = ApiKeyDialog(self, self.config["api_keys"].get("gemini", ""))
        if dialog.exec_():
            api_key = dialog.get_api_key()
            if api_key:
                self.config["api_keys"]["gemini"] = api_key; self.save_config()
                self.log_message("API key configured.", "success", True); self._init_ai_engine_for_gui()
            else:
                self.log_message("API key is required for AI features.", "error", True)
                QTimer.singleShot(1000, self.prompt_for_api_key)
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def show_instructions(self):
        dialog = InstructionsDialog(self, self.config.get("show_instructions", True))
        if dialog.exec_(): self.config["show_instructions"] = dialog.should_show_again(); self.save_config()
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def show_settings(self):
        prev_gemini_key = self.config["api_keys"].get("gemini",""); prev_gui_model = self.config.get("gui_model_name")
        prev_verbose_log = self.config.get("verbose_logging"); prev_max_hist = self.config.get("max_history")
        prev_force_ai_cmds = set(self.config.get("force_ai_for_commands", []))
        dialog = SettingsDialog(self, self.config.copy()); dialog.force_ai_commands_updated.connect(self.fetch_and_cache_force_ai_explanations)
        if dialog.exec_():
            new_cfg = dialog.get_config_values()
            theme_changed = self.config.get("theme") != new_cfg.get("theme"); gemini_key_changed = prev_gemini_key != new_cfg["api_keys"].get("gemini","")
            gui_model_changed = prev_gui_model != new_cfg.get("gui_model_name"); verbose_log_changed = prev_verbose_log != new_cfg.get("verbose_logging")
            max_hist_changed = prev_max_hist != new_cfg.get("max_history"); current_new_force_ai_cmds = set(new_cfg.get("force_ai_for_commands", []))
            force_ai_cmds_changed = prev_force_ai_cmds != current_new_force_ai_cmds
            self.config = new_cfg; self.verbose_logging = self.config.get("verbose_logging", True); self.save_config()
            if theme_changed: self.apply_theme()
            self.verbose_log_checkbox.setChecked(self.verbose_logging)
            if verbose_log_changed: self.log_message(f"Verbose backend logging (GUI display) {'enabled' if self.verbose_logging else 'disabled'}.", "system", True)
            if max_hist_changed:
                self.log_message(f"Max command history size set to {self.config['max_history']}.", "system", True)
                max_h = self.config.get("max_history", DEFAULT_CONFIG["max_history"])
                if len(self.input_history) > max_h: self.input_history = self.input_history[-max_h:]
                if self.current_history_index > len(self.input_history) : self.current_history_index = len(self.input_history)
                self.save_input_history()
            if force_ai_cmds_changed: self.log_message(f"Commands to always force AI processing updated: {self.config.get('force_ai_for_commands')}", "system", True)
            if gemini_key_changed or gui_model_changed: self._init_ai_engine_for_gui()
            self.log_message("Settings updated.", "success", True)
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def show_about(self):
        QMessageBox.about(self, "About Linux AI Assistant", "<h3>Linux AI Assistant</h3><p>Version 1.1</p><p>Created by: Krzysztof Żuchowski</p>"
                          "<p>© 2025 Krzysztof Żuchowski. All rights reserved.</p><p>Licensed under the MIT License.</p>"
                          "<p>AI-powered command generation for Linux.</p><hr><p>Support the project:</p>"
                          "<p><a href='https://www.buymeacoffee.com/krzyzu.83'>Buy me a coffee (krzyzu.83)</a></p>"
                          "<p><a href='https://github.com/hyconiek/linux_ai_terminal_assistant'>Project on GitHub</a></p>")
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def start_processing_animation(self, message: str = "Processing"):
        if self.is_processing_animation_active: return
        self.is_processing_animation_active = True; self.animation_index = 0
        if not hasattr(self, '_original_ai_output_placeholder'): self._original_ai_output_placeholder = self.ai_output_display.placeholderText()
        if self.animation_timer is None: self.animation_timer = QTimer(self); self.animation_timer.timeout.connect(self.update_processing_animation)
        self._current_animation_message = message; self.ai_output_display.clear(); self.update_processing_animation(); self.animation_timer.start(150)
        self.input_field.setEnabled(False)
        self.execute_button.setEnabled(False) # Deaktywuj Execute/Run in Terminal
        self.copy_button.setEnabled(False)
        self.cancel_button.setText("Stop") # Zmień Cancel na Stop
        self.cancel_button.setEnabled(True)


    def update_processing_animation(self):
        if not self.is_processing_animation_active: return
        char = self.animation_chars[self.animation_index % len(self.animation_chars)]
        self.ai_output_display.setPlaceholderText(f"{self._current_animation_message} {char}"); self.animation_index += 1

    def stop_processing_animation(self, restore_placeholder: bool = True):
        if not self.is_processing_animation_active: return
        if self.animation_timer and self.animation_timer.isActive(): self.animation_timer.stop()
        if restore_placeholder:
            self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder if hasattr(self, '_original_ai_output_placeholder') else "Type a command or query... Analysis or explanation will appear here.")
            if not self.ai_output_display.toPlainText().strip(): self.ai_output_display.clear()
        self.is_processing_animation_active = False; self.input_field.setEnabled(True)
        # Przywracanie stanu przycisków jest teraz w `process_finished` i `execution_process_finished_from_backend`
        # oraz `handle_stdout` jeśli nie ma polecenia.
        # self.execute_button.setEnabled(True) # Nie tutaj, bo może być jeszcze panel polecenia
        # self.copy_button.setEnabled(True)
        # self.cancel_button.setText("Cancel")
        # self.cancel_button.setEnabled(self.generated_command_panel.isVisible())
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def handle_stdout(self):
        self.stop_processing_animation(restore_placeholder=False)
        if not self.process: return
        raw_data = self.process.readAllStandardOutput().data().decode().strip()
        if not raw_data: return

        self.log_message(f"Backend STDOUT (AI query result): {raw_data}", "debug_backend")
        try:
            result_dict = json.loads(raw_data)
            if GeminiApiResponse_class_ref:
                self.last_api_response = GeminiApiResponse_class_ref(**result_dict)
            else:
                self.last_api_response = type('FallbackApiResponse', (), result_dict)()
                for key in ['command', 'explanation', 'error', 'is_text_answer',
                            'needs_file_search', 'file_search_pattern', 'file_search_message',
                            'suggested_interaction_input', 'suggested_button_label',
                            'needs_external_terminal', 'working_dir']:
                    if not hasattr(self.last_api_response, key):
                        setattr(self.last_api_response, key, None if "pattern" in key or "message" in key or "input" in key or "label" in key or "dir" in key else False)

            self.generated_command_panel.hide()
            self.generated_command_display.clear(); self.ai_output_display.clear()
            self.copy_button.setEnabled(True) # Zawsze włączaj kopiowanie po otrzymaniu odpowiedzi
            self.cancel_button.setText("Cancel")
            self.cancel_button.setEnabled(False) # Wyłącz Cancel, jeśli nie ma aktywnego polecenia
            self.execute_button.setText("Execute") # Zresetuj tekst przycisku execute


            if self.last_api_response.error == "CLARIFY_REQUEST":
                self.log_message("AI requires clarification for your query.", "assistant", True)
                self.ai_output_display.setText("AI requires clarification. Suggesting questions...")
                last_q = "previous query"
                current_prompt_for_log = self.update_prompt_label_text()
                for line in reversed(self.terminal.toPlainText().strip().split('\n')):
                    if line.startswith(current_prompt_for_log):
                        last_q = line[len(current_prompt_for_log):].strip(); break
                self.handle_complex_query(last_q); return
            if self.last_api_response.error == "DANGEROUS_REQUEST":
                self.log_message("AI identified query as dangerous.", "error", True)
                self.ai_output_display.setText("AI identified query as dangerous and blocked it."); return
            if self.last_api_response.error and not self.last_api_response.success:
                err_msg = self.last_api_response.error or 'Unknown backend error'
                self.log_message(f"Backend Error (JSON process_query): {err_msg}", "error", True)
                self.ai_output_display.setText(f"Error from backend: {err_msg}"); return

            if self.last_api_response.success:
                if self.last_api_response.is_text_answer:
                    answer_text = self.last_api_response.explanation or "AI provided a text answer."
                    self.log_message(f"AI Answer received.", "assistant", True)
                    self.ai_output_display.setText(answer_text)
                    self.current_command = None
                    self.cancel_button.setEnabled(True) # Włącz cancel, bo jest odpowiedź do skopiowania/anulowania (w sensie wyczyszczenia)
                elif self.last_api_response.command:
                    cmd, expl = self.last_api_response.command, self.last_api_response.explanation
                    self.current_command_suggested_interaction_input = self.last_api_response.suggested_interaction_input
                    sugg_label = self.last_api_response.suggested_button_label
                    self.generated_command_header_label.setText("Generated Command:")
                    self.generated_command_display.setText(cmd)
                    self.ai_output_display.setText(expl or "N/A")
                    self.generated_command_panel.show(); self.current_command = cmd
                    if self.last_api_response.needs_external_terminal:
                        self.execute_button.setText(sugg_label if sugg_label else "Run in Terminal")
                    else:
                        self.execute_button.setText(sugg_label if sugg_label else "Execute")
                    self.execute_button.setEnabled(True)
                    self.cancel_button.setEnabled(True) # Włącz Cancel, bo jest sugestia
                    if cmd and expl and "N/A" not in expl and "not in cache" not in expl.lower():
                        self.explanations_cache[cmd] = expl; self.save_explanations_cache()
                elif self.last_api_response.needs_file_search:
                    self.ai_output_display.setText(f"AI requests a file search: '{self.last_api_response.file_search_pattern}'. {self.last_api_response.file_search_message}")
                    self.log_message(f"AI needs file search: pattern='{self.last_api_response.file_search_pattern}', message='{self.last_api_response.file_search_message}'", "assistant", True)
                    self.current_command = None
                else:
                    self.log_message("Backend returned success but no command or text answer.", "error", True)
                    self.ai_output_display.setText("AI processed successfully but returned no actionable output.")
            new_wd_from_ai_context = self.last_api_response.working_dir
            if new_wd_from_ai_context and os.path.abspath(new_wd_from_ai_context) != self.gui_current_working_dir:
                self.gui_current_working_dir = os.path.abspath(new_wd_from_ai_context)
                self.log_message(f"GUI CWD context updated from AI to: {self.gui_current_working_dir}", "debug_backend")
                self.update_prompt_label_text()
        except json.JSONDecodeError:
            self.log_message(f"Backend (non-JSON STDOUT process_query): {raw_data}", "error", True)
            self.ai_output_display.setText("Error: Received malformed data from backend.")
        except Exception as e_parse:
            self.log_message(f"Error parsing backend response in handle_stdout: {e_parse}", "error", True)
            self.ai_output_display.setText(f"Error parsing backend response: {e_parse}")
            self.last_api_response = None
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def handle_stderr(self):
        self.stop_processing_animation(restore_placeholder=True) # Przywróć placeholder, jeśli był błąd
        if not self.process: return
        raw_data = self.process.readAllStandardError().data().decode().strip()
        if raw_data: self.log_message(f"Backend STDERR (query processing): {raw_data}", "debug_backend")
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def process_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        self.stop_processing_animation(restore_placeholder=not self.ai_output_display.toPlainText().strip())
        status_str = "normally" if exit_status == QProcess.NormalExit else "with a crash"
        self.log_message(f"Backend process (AI query) finished {status_str}, code: {exit_code}.", "debug_backend")
        if exit_code != 0 and not self.generated_command_panel.isVisible() and not self.ai_output_display.toPlainText().strip():
             self.log_message(f"Backend AI query process may have failed (code: {exit_code}).", "error", True)
             self.ai_output_display.setText(f"AI query process failed (code: {exit_code}).")

        # Przywróć stan przycisków, jeśli nie ma aktywnego polecenia
        if not self.generated_command_panel.isVisible():
            self.execute_button.setEnabled(False) # Execute jest włączane tylko gdy jest polecenie
            self.copy_button.setEnabled(True) # Kopiowanie wyjaśnienia/błędu może być nadal użyteczne
            self.cancel_button.setText("Cancel")
            self.cancel_button.setEnabled(True) # Cancel (clear) jest zawsze możliwe, jeśli jest tekst

        if self.process: self.process.deleteLater(); self.process = None
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def execute_command(self):
        if not self.current_command:
            self.log_message("No AI-generated command to execute.", "system", True); return

        needs_ext_term = False
        if self.last_api_response and hasattr(self.last_api_response, 'needs_external_terminal'):
            needs_ext_term = self.last_api_response.needs_external_terminal
        if self.current_command_suggested_interaction_input == "TERMINAL_REQUIRED":
            needs_ext_term = True

        # Zmień stan przycisków przed rozpoczęciem wykonania
        self.execute_button.setEnabled(False)
        self.copy_button.setEnabled(False) # Zdezaktywuj kopiowanie podczas wykonania
        self.cancel_button.setText("Stop")
        self.cancel_button.setEnabled(True)


        if needs_ext_term:
            self.log_message(f"Command '{self.current_command}' requires an external terminal. Launching...", "system", True)
            inner_cmd_for_bash = self.current_command.replace("'", "'\\''")
            bash_command_payload = (
                f"echo '--- Linux AI Assistant: Executing Command ---'; "
                f"echo 'Command: {inner_cmd_for_bash}'; "
                f"echo 'Working directory: {self.gui_current_working_dir}'; echo; "
                f"cd '{shlex.quote(self.gui_current_working_dir)}' && ({inner_cmd_for_bash}); "
                f"echo -e '\\n\\n--- Command finished. Press Enter to close this terminal. ---'; read"
            )
            term_to_use = None; args_term = []
            terminals = {
                "gnome-terminal": ["--working-directory", self.gui_current_working_dir, "--", "bash", "-c", bash_command_payload],
                "konsole": ["--workdir", self.gui_current_working_dir, "-e", "bash", "-c", bash_command_payload],
                "xfce4-terminal": ["--working-directory", self.gui_current_working_dir, "--command", f"bash -c \"{bash_command_payload.replace('\"', '\\\\\\"')}\""],
                "lxterminal": ["--working-directory", self.gui_current_working_dir, "-e", f"bash -c '{bash_command_payload}'"],
                "mate-terminal": ["--working-directory", self.gui_current_working_dir, "--", "bash", "-c", bash_command_payload],
                "xterm": ["-e", f"bash -c \"cd '{shlex.quote(self.gui_current_working_dir)}' && {bash_command_payload.replace('\"', '\\\"')}\""]
            }
            for term_name_iter, t_args_iter in terminals.items():
                if shutil.which(term_name_iter):
                    term_to_use = term_name_iter; args_term = t_args_iter; break
            if not term_to_use: term_to_use = "xterm"; args_term = terminals["xterm"]

            if term_to_use:
                try:
                    self.log_message(f"Attempting to launch '{self.current_command}' in '{term_to_use}'", "debug_backend")
                    final_args_for_popen = [term_to_use] + args_term[1:] if term_to_use != "xterm" else [term_to_use] + args_term # Poprawka dla xterm
                    subprocess.Popen(final_args_for_popen, cwd=(args_term[0] if term_to_use != "xterm" and len(args_term)>0 and os.path.isdir(args_term[0]) else None))
                    self.log_message(f"Command '{self.current_command}' launched in '{term_to_use}'. Please interact with the new terminal window.", "success", True)
                    # Po uruchomieniu w zewn. terminalu, czyścimy panel i resetujemy przyciski
                    self.generated_command_panel.hide()
                    self.execute_button.setText("Execute"); self.execute_button.setEnabled(False)
                    self.copy_button.setEnabled(True)
                    self.cancel_button.setText("Cancel"); self.cancel_button.setEnabled(False)
                    self.ai_output_display.clear()
                    if hasattr(self, '_original_ai_output_placeholder'): self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
                    self.current_command = None; self.current_command_suggested_interaction_input = None
                    self.stop_processing_animation() # Zatrzymaj animację, jeśli była
                except Exception as e_term_launch:
                    self.log_message(f"Error launching external terminal '{term_to_use}': {e_term_launch}", "error", True)
                    QMessageBox.warning(self, "Terminal Error", f"Could not launch command in '{term_to_use}'.\nPlease execute manually:\n\ncd \"{self.gui_current_working_dir}\"\n{self.current_command}")
                    # Przywróć stan przycisków w razie błędu uruchomienia
                    self.execute_button.setEnabled(True)
                    self.copy_button.setEnabled(True)
                    self.cancel_button.setText("Cancel")
            return # Zakończ po próbie uruchomienia w zewnętrznym terminalu

        self.start_processing_animation("Executing AI-generated command...")
        cmd_to_backend = self.current_command
        if self.current_command.strip().startswith("sudo ") and not self.current_command.strip().startswith("echo "):
            dialog = SudoPasswordDialog(self, self.current_command)
            if dialog.exec_():
                passwd = dialog.get_password()
                if passwd:
                    cmd_no_sudo = self.current_command.replace("sudo ", "", 1).strip()
                    esc_passwd = shlex.quote(passwd)
                    cmd_to_backend = f"echo {esc_passwd} | sudo -S -p '' {cmd_no_sudo}"
                    self.log_message("Sudo password provided. Preparing command for backend.", "system", True)
                else:
                    self.log_message("Sudo password not provided. Cancelled.", "error", True); self.stop_processing_animation()
                    # Przywróć przyciski
                    self.execute_button.setEnabled(True); self.copy_button.setEnabled(True); self.cancel_button.setText("Cancel")
                    return
            else:
                self.log_message("Sudo command execution cancelled by user.", "system", True); self.stop_processing_animation()
                self.execute_button.setEnabled(True); self.copy_button.setEnabled(True); self.cancel_button.setText("Cancel")
                return

        self.current_command_suggested_interaction_input = None
        self.log_message(f"Sending to backend (AI-gen, auto-confirm): {self.current_command}", "command", True)
        if cmd_to_backend != self.current_command: self.log_message(f"(Executing as: echo '****' | sudo -S ...)", "debug_backend")

        self.current_exec_process = QProcess(self)
        self.current_exec_process.readyReadStandardOutput.connect(lambda: self.handle_execution_stdout_from_backend(self.current_exec_process))
        self.current_exec_process.readyReadStandardError.connect(lambda: self.handle_execution_stderr_from_backend(self.current_exec_process))
        self.current_exec_process.finished.connect(lambda ec, es, cmd_orig=str(self.current_command): self.execution_process_finished_from_backend(ec, es, cmd_orig, self.current_exec_process))
        env = QProcessEnvironment.systemEnvironment();
        gemini_key = self.config["api_keys"].get("gemini", "")
        if gemini_key: env.insert("GOOGLE_API_KEY", gemini_key)
        env.insert("LAA_BACKEND_MODE", "1"); env.insert("LAA_VERBOSE_LOGGING_EFFECTIVE", "1" if self.verbose_logging else "0")
        self.current_exec_process.setProcessEnvironment(env)
        exec_path, exec_args_list = (sys.executable, []) if getattr(sys,'frozen',False) and hasattr(sys, '_MEIPASS') else \
                                   (sys.executable, [os.path.join(os.path.dirname(os.path.abspath(__file__)),"src","backend_cli.py")])
        if not (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')) and not os.path.exists(exec_args_list[0]):
             self.log_message(f"CRITICAL: Dev backend_cli.py not found: {exec_args_list[0]}", "error", True); self.stop_processing_animation()
             self.execute_button.setEnabled(True); self.copy_button.setEnabled(True); self.cancel_button.setText("Cancel")
             return
        exec_args_list.extend(["--query", cmd_to_backend, "--execute", "--json", "--working-dir", self.gui_current_working_dir])
        logged_args = ' '.join(shlex.quote(arg) for arg in exec_args_list)
        self.log_message(f"Backend exec cmd (AI-gen): {exec_path} {logged_args}", "debug_backend")
        self.current_exec_process.start(exec_path, exec_args_list)
        if not self.current_exec_process.waitForStarted(10000):
            self.log_message(f"Error starting backend (AI-gen exec): {self.current_exec_process.errorString()}", "error", True); self.stop_processing_animation()
            if self.current_exec_process: self.current_exec_process.deleteLater(); self.current_exec_process = None
            self.execute_button.setEnabled(True); self.copy_button.setEnabled(True); self.cancel_button.setText("Cancel")
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def execute_basic_command(self, command_str: str):
        # Zmień stan przycisków przed rozpoczęciem wykonania
        self.execute_button.setEnabled(False) # Zakładając, że panel poleceń jest ukryty dla basic_command
        self.copy_button.setEnabled(False)
        self.cancel_button.setText("Stop")
        self.cancel_button.setEnabled(True) # Aktywuj Stop

        self.current_exec_process = QProcess(self)
        self.current_exec_process.readyReadStandardOutput.connect(lambda: self.handle_execution_stdout_from_backend(self.current_exec_process))
        self.current_exec_process.readyReadStandardError.connect(lambda: self.handle_execution_stderr_from_backend(self.current_exec_process))
        self.waiting_for_basic_command_explanation_for = command_str
        self.current_exec_process.finished.connect(lambda ec, es, cmd=command_str, proc_instance=self.current_exec_process: self.execution_process_finished_from_backend(ec, es, cmd, proc_instance))
        env = QProcessEnvironment.systemEnvironment()
        gemini_key = self.config["api_keys"].get("gemini", "")
        if gemini_key: env.insert("GOOGLE_API_KEY", gemini_key)
        env.insert("LAA_BACKEND_MODE", "1"); env.insert("LAA_VERBOSE_LOGGING_EFFECTIVE", "1" if self.verbose_logging else "0")
        self.current_exec_process.setProcessEnvironment(env)
        exec_path, exec_args_list = (sys.executable, []) if getattr(sys,'frozen',False) and hasattr(sys, '_MEIPASS') else \
                                   (sys.executable, [os.path.join(os.path.dirname(os.path.abspath(__file__)),"src","backend_cli.py")])
        if not (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')) and not os.path.exists(exec_args_list[0]):
             self.log_message(f"CRITICAL: Dev backend_cli.py not found: {exec_args_list[0]}", "error", True); self.stop_processing_animation()
             self.execute_button.setEnabled(True); self.copy_button.setEnabled(True); self.cancel_button.setText("Cancel"); self.cancel_button.setEnabled(False)
             return
        exec_args_list.extend(["--query", command_str, "--execute", "--json", "--working-dir", self.gui_current_working_dir])
        logged_args = ' '.join(shlex.quote(arg) for arg in exec_args_list)
        self.log_message(f"Backend exec cmd (basic): {exec_path} {logged_args}", "debug_backend")
        self.current_exec_process.start(exec_path, exec_args_list)
        if not self.current_exec_process.waitForStarted(10000):
            self.log_message(f"Błąd startu backendu (basic exec): {self.current_exec_process.errorString()}", "error", True); self.stop_processing_animation()
            if self.current_exec_process: self.current_exec_process.deleteLater(); self.current_exec_process = None
            self.waiting_for_basic_command_explanation_for = None
            self.execute_button.setEnabled(True); self.copy_button.setEnabled(True); self.cancel_button.setText("Cancel"); self.cancel_button.setEnabled(False)
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def request_ai_explanation_for_executed_command(self, command_str: str):
        self.start_processing_animation(f"Getting AI explanation for: {command_str}") # Animacja już powinna być zatrzymana
        cached_explanation = self.explanations_cache.get(command_str)
        if not cached_explanation: cmd_prefix = command_str.split(" ", 1)[0]; cached_explanation = self.explanations_cache.get(cmd_prefix)

        # Reset przycisków po wykonaniu basic command
        self.execute_button.setText("Execute")
        self.execute_button.setEnabled(False) # Execute nieaktywne, bo polecenie już wykonane
        self.copy_button.setEnabled(True)    # Kopiowanie wyjaśnienia lub polecenia
        self.cancel_button.setText("Cancel") # Przycisk Stop wraca do Cancel
        self.cancel_button.setEnabled(True)  # Można anulować (wyczyścić) panel

        if self.is_offline:
            if cached_explanation: self.log_message(f"Fetched explanation for '{command_str}' from cache (offline).", "system"); self.ai_output_display.setText(cached_explanation)
            else: self.log_message(f"Cannot fetch AI explanation for '{command_str}' while offline and not in cache.", "offline_status", True); self.ai_output_display.setText("Explanation N/A (Offline and not cached).")
            self.generated_command_header_label.setText("Executed Command:"); self.generated_command_display.setText(command_str)
            self.generated_command_panel.show()
            self.stop_processing_animation(restore_placeholder=False); QTimer.singleShot(0, lambda: self.input_field.setFocus()); return

        if not self.ai_engine_for_gui or not self.ai_engine_for_gui.is_configured:
            self.log_message("AI engine for GUI not available to explain executed command.", "system")
            self.ai_output_display.setText(cached_explanation or "Explanation N/A (GUI AI engine disabled or not configured).")
            self.generated_command_header_label.setText("Executed Command:"); self.generated_command_display.setText(command_str)
            self.generated_command_panel.show()
            self.stop_processing_animation(restore_placeholder=False); return

        try:
            lang_instr_gui = self._get_gui_ai_language_instruction()
            api_res: Optional[GeminiApiResponse_class_ref] = self.ai_engine_for_gui.analyze_text_input_type(command_str, language_instruction=lang_instr_gui)
            explanation_text = cached_explanation or "Could not get explanation from AI."
            if api_res and api_res.success and api_res.analyzed_text_type == "linux_command" and api_res.explanation: explanation_text = api_res.explanation
            elif api_res and api_res.error: explanation_text = f"AI Analysis Error: {api_res.error}"

            self.generated_command_header_label.setText("Executed Command:"); self.generated_command_display.setText(command_str)
            self.ai_output_display.setText(explanation_text); self.generated_command_panel.show()

            if command_str and explanation_text and "Could not get" not in explanation_text and "Error" not in explanation_text and "N/A" not in explanation_text:
                 self.explanations_cache[command_str] = explanation_text; self.save_explanations_cache()
        except Exception as e:
            self.log_message(f"Exception requesting AI explanation for '{command_str}': {e}", "error", True)
            self.ai_output_display.setText(cached_explanation or f"Error getting explanation: {e}")
            self.generated_command_panel.show(); self.generated_command_display.setText(command_str)
        finally:
            self.stop_processing_animation(restore_placeholder=False); QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def handle_execution_stdout_from_backend(self, proc: Optional[QProcess]):
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
                self.update_prompt_label_text() # Zaktualizuj prompt w GUI
            fix_sugg = res.get("fix_suggestion")
            if fix_sugg: self.log_message(f"\n--- AI Fix Suggestion ---\n{fix_sugg}\n--------------------------", "assistant", True)
        except json.JSONDecodeError: self.log_message(f"Backend Exec (non-JSON STDOUT): {raw_data}", "system", True)
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def handle_execution_stderr_from_backend(self, proc: Optional[QProcess]):
        if not proc: return
        raw_data = proc.readAllStandardError().data().decode().strip()
        if raw_data: self.log_message(f"Backend Exec STDERR (raw): {raw_data}", "debug_backend")
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def execution_process_finished_from_backend(self, exit_code: int, exit_status: QProcess.ExitStatus, executed_command: str, proc: Optional[QProcess]):
        self.stop_processing_animation(restore_placeholder=False) # Zatrzymaj animację, jeśli była (np. z execute_basic_command)

        # Zawsze przywracaj stan przycisków po zakończeniu wykonania
        self.execute_button.setEnabled(True) # Domyślnie włącz, chyba że panel poleceń jest ukryty
        self.copy_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
        self.cancel_button.setEnabled(self.generated_command_panel.isVisible()) # Włącz, jeśli panel jest widoczny

        if exit_status == QProcess.CrashExit or (exit_code !=0 and self.cancel_button.text() == "Stopping..."): # Jeśli proces został zabity przez "Stop"
            self.log_message(f"Execution of '{executed_command}' was terminated by user or crashed.", "error", True)
            # Jeśli panel poleceń był widoczny (czyli to było AI-generated command)
            if self.generated_command_panel.isVisible():
                self.ai_output_display.setText(f"Execution of '{executed_command}' stopped/crashed.")
            else: # Jeśli to było basic command, panel jest ukryty
                self.ai_output_display.clear() # Wyczyść placeholder animacji
        else:
            status_str = "successfully" if exit_code == 0 else f"with code {exit_code}"
            msg_type = "success" if exit_code == 0 else "error"
            self.log_message(f"Execution of '{executed_command}' via backend finished {status_str}.", msg_type, True)

        if self.waiting_for_basic_command_explanation_for == executed_command:
            self.request_ai_explanation_for_executed_command(executed_command) # To pokaże panel i ustawi przyciski
            self.waiting_for_basic_command_explanation_for = None
        elif self.current_command and executed_command.strip().startswith(self.current_command.strip()): # Jeśli to było polecenie AI
            # Jeśli polecenie AI zakończyło się (nie przerwano), ukryj panel i wyczyść
            if not (exit_status == QProcess.CrashExit or (exit_code !=0 and self.cancel_button.text() == "Stopping...")):
                self.generated_command_panel.hide()
                self.ai_output_display.clear()
                if hasattr(self, '_original_ai_output_placeholder'): self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
                self.current_command = None
                self.current_command_suggested_interaction_input = None
                self.execute_button.setText("Execute")
                self.cancel_button.setEnabled(False) # Wyłącz Cancel, bo nie ma aktywnego polecenia

        # Reset przycisku execute, jeśli nie ma aktywnego polecenia do wykonania
        if not self.generated_command_panel.isVisible():
            self.execute_button.setEnabled(False)


        if proc and proc == self.current_exec_process:
            proc.deleteLater()
            self.current_exec_process = None
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def copy_content(self):
        clipboard = QApplication.clipboard(); text_to_copy = ""; log_msg = ""
        if self.generated_command_panel.isVisible() and self.generated_command_display.toPlainText().strip():
            text_to_copy = self.generated_command_display.toPlainText().strip(); log_msg = "Displayed command copied to clipboard."
        elif self.ai_output_display.toPlainText().strip() and not self.ai_output_display.placeholderText() == self.ai_output_display.toPlainText():
            text_to_copy = self.ai_output_display.toPlainText().strip(); log_msg = "AI output/explanation copied to clipboard."
        if text_to_copy: clipboard.setText(text_to_copy); self.log_message(log_msg, "success", True)
        else: self.log_message("Nothing to copy.", "system", True)
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def cancel_generated_command(self): # Ta metoda jest teraz tylko do anulowania *przed* wykonaniem
        self.generated_command_panel.hide(); self.generated_command_display.clear()
        if hasattr(self, '_original_ai_output_placeholder'): self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
        self.ai_output_display.clear()
        self.current_command = None; self.current_command_suggested_interaction_input = None
        self.execute_button.setText("Execute"); self.execute_button.setEnabled(False) # Execute nieaktywne po anulowaniu
        self.copy_button.setEnabled(True) # Kopiowanie może być nadal aktywne dla terminala
        self.cancel_button.setText("Cancel"); self.cancel_button.setEnabled(False) # Cancel nieaktywny po anulowaniu
        self.generated_command_header_label.setText("Generated Command:")
        self.log_message("Command cancelled.", "system", True); QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def handle_cancel_or_stop_button(self):
        if self.current_exec_process and self.current_exec_process.state() == QProcess.Running:
            # Tryb "Stop"
            self.log_message("Attempting to stop current execution...", "system", True)
            self.current_exec_process.terminate() # Wyślij SIGTERM
            # Można dodać QTimer, aby po krótkim czasie wysłać kill(), jeśli terminate() nie zadziała
            # QTimer.singleShot(1000, self.force_kill_if_still_running)
            self.cancel_button.setEnabled(False) # Zdezaktywuj, aby uniknąć wielokrotnych kliknięć
            self.cancel_button.setText("Stopping...")
            # Nie ukrywamy panelu ani nie resetujemy current_command tutaj, czekamy na sygnał `finished`
            # który wywoła `execution_process_finished_from_backend`
        elif self.generated_command_panel.isVisible():
            # Tryb "Cancel" (anulowanie przed wykonaniem)
            self.cancel_generated_command()
        else:
            # Jeśli panel nie jest widoczny, przycisk "Cancel" może służyć do wyczyszczenia AI output
            if self.ai_output_display.toPlainText().strip():
                self.ai_output_display.clear()
                if hasattr(self, '_original_ai_output_placeholder'):
                    self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
                self.log_message("AI output cleared.", "system")
            self.cancel_button.setEnabled(False) # Po wyczyszczeniu, deaktywuj


    def save_explanations_cache(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(EXPLANATIONS_CACHE_FILE, 'w', encoding='utf-8') as f: json.dump(self.explanations_cache, f, indent=2)
        except Exception as e: self.log_message(f"Error saving explanations cache: {e}", "error", True)

    def update_realtime_analysis(self):
        if self.is_offline:
            if not self.generated_command_panel.isVisible():
                 self.ai_output_display.setPlaceholderText("Offline Mode: Real-time analysis disabled.")
                 if not self.input_field.text().strip(): self.ai_output_display.clear()
            if self.explanation_timer and self.explanation_timer.isActive(): self.explanation_timer.stop()
            return
        txt = self.input_field.text().strip()
        if not self.generated_command_panel.isVisible():
            if not txt:
                self.ai_output_display.clear()
                if hasattr(self, '_original_ai_output_placeholder'): self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
                if self.explanation_timer and self.explanation_timer.isActive(): self.explanation_timer.stop()
                return
            if len(txt) < 4:
                self.ai_output_display.setText("Keep typing...")
                if self.explanation_timer and self.explanation_timer.isActive(): self.explanation_timer.stop()
                return
        if self.explanation_timer and self.explanation_timer.isActive(): self.explanation_timer.stop()
        if not self.explanation_timer:
            self.explanation_timer = QTimer(self); self.explanation_timer.setSingleShot(True)
            self.explanation_timer.timeout.connect(lambda: self.request_command_analysis_and_explanation(self.input_field.text().strip()))
        self.explanation_timer.start(1200)

    def request_command_analysis_and_explanation(self, text_input: str):
        if not text_input:
            if not self.generated_command_panel.isVisible():
                self.ai_output_display.clear()
                if hasattr(self, '_original_ai_output_placeholder'): self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
            return
        if not self.generated_command_panel.isVisible() and text_input in self.explanations_cache:
            self.ai_output_display.setText(f"Cached: {self.explanations_cache[text_input]}"); return
        if self.is_offline:
            if not self.generated_command_panel.isVisible():
                cached_expl = self.explanations_cache.get(text_input) or self.explanations_cache.get(text_input.split(" ",1)[0])
                self.ai_output_display.setText(cached_expl or "Offline: Cannot analyze new input. No cached explanation.")
            return
        if not self.ai_engine_for_gui or not self.ai_engine_for_gui.is_configured:
            if not self.generated_command_panel.isVisible(): self.ai_output_display.setText("AI for real-time analysis N/A (check API key/settings).")
            return
        if not self.generated_command_panel.isVisible(): self.ai_output_display.setText("Analyzing input with AI...")
        try:
            lang_instr_gui = self._get_gui_ai_language_instruction()
            api_res: Optional[GeminiApiResponse_class_ref] = self.ai_engine_for_gui.analyze_text_input_type(text_input, language_instruction=lang_instr_gui)
            if not self.generated_command_panel.isVisible():
                if api_res and api_res.success:
                    tt, expl = api_res.analyzed_text_type, api_res.explanation
                    if tt == "linux_command":
                        self.ai_output_display.setText(f"Cmd: {expl if expl else 'No specific explanation.'}")
                        if expl: self.explanations_cache[text_input] = expl; self.save_explanations_cache()
                    elif tt == "natural_language_query": self.ai_output_display.setText(f"Query: {expl if expl else 'Seems like a query.'}")
                    elif tt == "question_about_cwd": self.ai_output_display.setText(f"Question about files: {expl if expl else 'Understood as a question about CWD.'}")
                    elif tt == "error": self.ai_output_display.setText(f"AI Analysis Error: {expl}")
                    else: self.ai_output_display.setText("Input Type: Other/Uncertain.")
                elif api_res and api_res.error:
                    err_msg = api_res.error; quota_err_msg = "AI API quota exceeded for real-time analysis."
                    if "quota" in err_msg.lower() and ("429" in err_msg or "ResourceExhausted" in err_msg): self.ai_output_display.setText(quota_err_msg)
                    else: self.ai_output_display.setText(f"AI Analysis Network Error: {err_msg}")
                    self.log_message(f"Error during real-time text input analysis: {err_msg}", "error", True)
                else: self.ai_output_display.setText("AI Analysis did not return a response.")
        except Exception as e:
            if not self.generated_command_panel.isVisible(): self.ai_output_display.setText(f"Exception during analysis: {e}")
            self.log_message(f"Exception in real-time analysis: {e}", "error", True)
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def handle_complex_query(self, original_query: str):
        if self.is_offline:
            self.log_message("Offline: Cannot generate clarification questions.", "offline_status", True)
            self.ai_output_display.setText("Offline: Cannot ask AI for clarification. Please try a simpler query or check connection.")
            self.stop_processing_animation(); return
        self.log_message(f"AI requested clarification for: \"{original_query}\". Generating questions...", "system", True)
        self.start_processing_animation(f"AI needs clarification for: {original_query[:30]}...")
        questions: List[str] = [];
        if self.ai_engine_for_gui and self.ai_engine_for_gui.is_configured:
            try:
                lang_instr_gui = self._get_gui_ai_language_instruction(); distro_sim = {"ID": "linux", "PACKAGE_MANAGER": "unknown"}
                questions = self.ai_engine_for_gui.generate_clarification_questions(original_query, distro_sim, self.gui_current_working_dir, language_instruction=lang_instr_gui)
            except Exception as e: self.log_message(f"Error generating clarification questions: {e}", "error", True)
        else: self.log_message("GUI AI engine not available for clarification questions.", "error", True)
        self.stop_processing_animation(restore_placeholder=False)
        if not questions: questions = ["Describe your main goal?", "Specific files/dirs/params involved?", "Expected outcome?"]
        dialog = ClarificationDialog(self, original_query, questions)
        if dialog.exec_():
            answers = dialog.get_answers(); detailed_query = original_query
            clarifications_text = ""
            for q_text, ans_text in zip(questions, answers):
                if ans_text.strip(): clarifications_text += f"\n- User's answer to '{q_text}': {ans_text.strip()}"
            if clarifications_text: detailed_query += "\n\n--- User Clarifications ---" + clarifications_text
            self.log_message("Processing with user clarifications...", "system", True)
            self.start_processing_animation("Processing clarified query..."); self.process_detailed_query(detailed_query)
        else:
            self.log_message("Clarification cancelled.", "system", True)
            if hasattr(self, '_original_ai_output_placeholder'): self.ai_output_display.setPlaceholderText(self._original_ai_output_placeholder)
            self.ai_output_display.clear()
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def process_detailed_query(self, detailed_query: str):
        if self.is_offline:
            self.log_message("Offline: Cannot process detailed AI query.", "offline_status", True)
            self.ai_output_display.setText("Offline: AI query processing unavailable. Check connection or use basic commands.")
            self.stop_processing_animation(); return
        self.log_message("Processing (detailed) query with backend...", "debug_backend")
        if self.process and self.process.state() == QProcess.Running:
            self.log_message("Backend busy. Please wait for the current operation to complete.", "error", True); self.stop_processing_animation(); return
        self.process = QProcess(self); self.process.readyReadStandardOutput.connect(self.handle_stdout) # Tutaj był błąd
        self.process.readyReadStandardError.connect(self.handle_stderr); self.process.finished.connect(self.process_finished)
        env = QProcessEnvironment.systemEnvironment();
        gemini_key = self.config["api_keys"].get("gemini", "")
        if gemini_key: env.insert("GOOGLE_API_KEY", gemini_key)
        else: self.log_message("Warning: Gemini API key not found in config for backend process.", "error", True)
        env.insert("LAA_BACKEND_MODE", "1"); env.insert("LAA_VERBOSE_LOGGING_EFFECTIVE", "1" if self.verbose_logging else "0")
        self.process.setProcessEnvironment(env)
        exec_path, exec_args_list = (sys.executable, []) if getattr(sys,'frozen',False) and hasattr(sys, '_MEIPASS') else \
                                   (sys.executable, [os.path.join(os.path.dirname(os.path.abspath(__file__)),"src","backend_cli.py")])
        if not (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')) and not os.path.exists(exec_args_list[0]):
             self.log_message(f"CRITICAL: Dev backend_cli.py not found: {exec_args_list[0]}", "error", True); self.stop_processing_animation(); return
        exec_args_list.extend(["--query", detailed_query, "--json", "--working-dir", self.gui_current_working_dir])
        logged_args = ' '.join(shlex.quote(arg) for arg in exec_args_list)
        self.log_message(f"Cmd to backend (detailed_query): {exec_path} {logged_args}", "debug_backend")
        self.process.start(exec_path, exec_args_list)
        if not self.process.waitForStarted(7000):
            self.log_message(f"Error starting backend: {self.process.errorString()}", "error", True); self.stop_processing_animation()
            if self.process: self.process.deleteLater(); self.process = None
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def start_new_session(self):
        if QMessageBox.question(self,"New Session","This will close the current assistant and start a new instance. Are you sure?", QMessageBox.Yes|QMessageBox.No,QMessageBox.No) == QMessageBox.Yes:
            try:
                qapp = QApplication.instance()
                if qapp:
                    current_executable = sys.executable; args = [os.path.abspath(sys.argv[0])] if not (getattr(sys,'frozen',False) and hasattr(sys, '_MEIPASS')) else []
                    QProcess.startDetached(current_executable, args); qapp.quit()
            except Exception as e: self.log_message(f"Error starting new session: {e}", "error", True)
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def save_session(self):
        fpath, _ = QFileDialog.getSaveFileName(self,"Save Log",os.path.expanduser("~/laa_session.txt"),"Text (*.txt);;All (*)")
        if fpath:
            try:
                with open(fpath,'w',encoding='utf-8') as f: f.write(self.terminal.toPlainText())
                self.log_message(f"Log saved to {fpath}", "success", True)
            except Exception as e: self.log_message(f"Error saving log: {e}", "error", True)
        QTimer.singleShot(0, lambda: self.input_field.setFocus())

    def eventFilter(self, obj, event):
        if obj is self.input_field and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                if not self.input_history: return True
                if self.current_history_index == len(self.input_history): self.pending_input_text = self.input_field.text()
                if self.current_history_index > 0:
                    self.current_history_index -= 1; self.input_field.setText(self.input_history[self.current_history_index]); self.input_field.selectAll()
                return True
            elif key == Qt.Key_Down:
                if not self.input_history: return True
                if self.current_history_index < len(self.input_history) -1:
                    self.current_history_index += 1; self.input_field.setText(self.input_history[self.current_history_index]); self.input_field.selectAll()
                elif self.current_history_index == len(self.input_history) -1:
                    self.current_history_index +=1; self.input_field.setText(self.pending_input_text)
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event: QEvent):
        self.save_input_history(); self.save_config()
        if self.process and self.process.state() == QProcess.Running: self.process.kill(); self.process.waitForFinished(1000)
        if self.current_exec_process and self.current_exec_process.state() == QProcess.Running: self.current_exec_process.kill(); self.current_exec_process.waitForFinished(1000)
        super().closeEvent(event)


def main_gui_entry_point():
    app = QApplication(sys.argv)
    app.setApplicationName("Linux AI Assistant")
    app.setApplicationVersion("1.1")
    app.setOrganizationName("Hyconiek")
    app.setOrganizationDomain("github.com/hyconiek")

    window = LinuxAIAssistantGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    if not _IS_BACKEND_MODE:
        main_gui_entry_point()
