#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import logging
import readline # type: ignore
import signal
import json
import getpass
import shlex
from typing import Dict, List, Optional, Any
import locale # Dodano import locale

# Ścieżki i importy modułów
if not (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')):
    # W trybie deweloperskim, jeśli backend_cli jest w src/, a modules w src/modules/
    # sys.path powinien być już poprawnie ustawiony.
    # Można dodać to dla pewności, jeśli struktura jest inna lub są problemy z importem:
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root = os.path.dirname(current_dir) # Zakładając, że backend_cli.py jest w src/
    # if project_root not in sys.path:
    #     sys.path.insert(0, project_root)
    pass

from modules.command_executor import CommandExecutor, DistributionDetector, SecurityValidator # type: ignore
from modules.gemini_integration import GeminiIntegration # type: ignore

# --- Konfiguracja Logowania dla Backendu ---
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = "/tmp/linux_ai_assistant_backend.log"

effective_log_level_backend = logging.INFO
handlers_backend: List[logging.Handler] = [logging.FileHandler(LOG_FILE, mode='a')]

if os.environ.get("LAA_VERBOSE_LOGGING_EFFECTIVE") == "1":
    effective_log_level_backend = logging.DEBUG
    if not ("--json" in sys.argv or "-j" in sys.argv): # Loguj do stderr tylko jeśli verbose i nie JSON
        handlers_backend.append(logging.StreamHandler(sys.stderr))

logging.basicConfig(level=effective_log_level_backend, format=LOG_FORMAT, handlers=handlers_backend)
# --- Koniec Konfiguracji Logowania ---

# --- Konfiguracja Kolorów (tylko dla trybu interaktywnego CLI) ---
if not ("--json" in sys.argv or "-j" in sys.argv):
    try:
        import colorama # type: ignore
        from colorama import Fore, Style # type: ignore
        colorama.init(autoreset=True)
    except ImportError:
        class Fore: GREEN = YELLOW = CYAN = WHITE = RED = "" # type: ignore
        class Style: RESET_ALL = "" # type: ignore
else: # Tryb --json, nie potrzebujemy kolorów
    class Fore: GREEN = YELLOW = CYAN = WHITE = RED = "" # type: ignore
    class Style: RESET_ALL = "" # type: ignore
# --- Koniec Konfiguracji Kolorów ---


class LinuxAIAssistant:
    def __init__(self, initial_working_dir: Optional[str] = None):
        self.logger = logging.getLogger("backend_assistant_instance")
        self.logger.info("LinuxAIAssistant (backend instance) logger initialized.")

        self.command_executor = CommandExecutor(timeout=120)
        # POPRAWIONE WCIĘCIE TUTAJ:
        if initial_working_dir and os.path.isdir(initial_working_dir):
            if self.command_executor.set_current_working_dir(initial_working_dir):
                 self.logger.info(f"Backend: Initial working directory for CommandExecutor set to: '{initial_working_dir}' by argument.")
            else: # set_current_working_dir zwróciło False
                 self.logger.warning(f"Backend: CommandExecutor.set_current_working_dir FAILED for '{initial_working_dir}'. Executor CWD remains '{self.command_executor.get_current_working_dir()}'.")
        else:
            if initial_working_dir: # Był argument, ale nie jest poprawnym katalogiem
                self.logger.warning(f"Backend: Initial working_dir argument '{initial_working_dir}' is not a valid directory. Using default Executor CWD: '{self.command_executor.get_current_working_dir()}'.")
            else: # Nie było argumentu
                self.logger.info(f"Backend: No initial working_dir argument provided. Using default Executor CWD: '{self.command_executor.get_current_working_dir()}'.")

        self.ai_engine = GeminiIntegration()
        self.distro_detector = DistributionDetector()
        self.distro_info = self.distro_detector.detect_distribution()
        self.chat_history_for_ai: List[Dict[str, Any]] = []

        try:
            lang_code, _ = locale.getdefaultlocale()
            if lang_code and '_' in lang_code: self.system_language = lang_code.split('_')[0] # np. 'pl' z 'pl_PL'
            elif lang_code: self.system_language = lang_code
            else: self.system_language = "en"
        except Exception as e:
            self.logger.warning(f"Backend: Could not detect system language: {e}. Defaulting to 'en'.")
            self.system_language = "en"
        self.logger.info(f"Backend: Detected system language (for AI): {self.system_language}")
        self.logger.info(f"Backend: Detected distribution: {self.distro_info}")
        self.logger.info(f"Backend: Current working directory after initialization: {self.command_executor.get_current_working_dir()}")

    def _get_ai_language_instruction(self) -> str:
        if self.system_language == "pl":
            return "ODPOWIADAJ ZAWSZE W JĘZYKU POLSKIM. Wyjaśnienie polecenia, pytania doprecyzowujące, sugestie naprawcze i wszelkie inne teksty MUSZĄ być po polsku."
        # Domyślnie angielski
        return "Respond always in English. The command explanation, clarification questions, fix suggestions, and any other text MUST be in English."

    def _add_to_chat_history(self, role: str, text_content: str):
        valid_role = role.lower() if role.lower() in ["user", "model"] else "user"
        self.chat_history_for_ai.append({"role": valid_role, "parts": [{"text": text_content}]})
        max_history_turns = 7
        if len(self.chat_history_for_ai) > max_history_turns * 2:
            self.chat_history_for_ai = self.chat_history_for_ai[-(max_history_turns * 2):]

    def process_query(self, query: str) -> Dict[str, Any]:
        # current_dir POWINIEN być tym, co ustawiło GUI przez --working-dir i __init__
        current_dir_for_ai_context = self.command_executor.get_current_working_dir()
        self.logger.info(f"Backend process_query: Query='{query}', CWD for AI context='{current_dir_for_ai_context}'")

        self._add_to_chat_history("user", query)
        api_response = self.ai_engine.generate_command_with_explanation(
            user_prompt=query, distro_info=self.distro_info, working_dir=current_dir_for_ai_context, # Użyj go tutaj
            history=self.chat_history_for_ai, language_instruction=self._get_ai_language_instruction()
        )
        if not api_response.success:
            error_msg = api_response.error or "Nie udało się wygenerować polecenia"
            if api_response.error == "CLARIFY_REQUEST": self._add_to_chat_history("model", "System: AI requested clarification.")
            elif api_response.error == "DANGEROUS_REQUEST": self._add_to_chat_history("model", "System: AI identified query as dangerous.")
            elif api_response.error: self._add_to_chat_history("model", f"System: Error from AI - {api_response.error}")
            return {"success": False, "error": error_msg, "command": None, "explanation": None, "working_dir": current_dir_for_ai_context, "fix_suggestion": None}
        ai_model_response_text = f"Polecenie: {api_response.command}\nWYJAŚNIENIE: {api_response.explanation}"
        self._add_to_chat_history("model", ai_model_response_text)
        return {"success": True, "command": api_response.command, "explanation": api_response.explanation, "working_dir": current_dir_for_ai_context, "error": None, "fix_suggestion": None}

    def execute_command(self, command: str, is_interactive_sudo_prompt: bool = False) -> Dict[str, Any]:
        self.logger.info(f"Backend: Preparing to execute: '{command}' (interactive sudo: {is_interactive_sudo_prompt}) in CWD: '{self.command_executor.get_current_working_dir()}'")
        command_to_run = command; original_command_for_log = command

        # Logika pytania o hasło sudo tylko jeśli jest to interaktywny tryb CLI backendu
        # i polecenie nie zostało już przygotowane przez GUI.
        if SecurityValidator.requires_confirmation(command) and \
           command.strip().startswith("sudo ") and \
           is_interactive_sudo_prompt and \
           not (command.strip().startswith("echo ") and "sudo -S" in command):
            print(f"{Fore.YELLOW}Polecenie '{command}' wymaga uprawnień sudo.{Style.RESET_ALL}")
            print(f"{Fore.RED}OSTRZEŻENIE: Wykonywanie poleceń z sudo może być niebezpieczne.{Style.RESET_ALL}")
            try:
                sudo_password = getpass.getpass(prompt=f"{Fore.YELLOW}Podaj hasło sudo dla [{os.environ.get('USER', os.getlogin())}]: {Style.RESET_ALL}")
                if not sudo_password:
                    self.logger.warning("Nie podano hasła sudo. Anulowano wykonanie.")
                    return {"success": False, "stdout": "", "stderr": "Nie podano hasła sudo. Anulowano.", "return_code": -1, "execution_time": 0.0, "working_dir": self.command_executor.get_current_working_dir(), "command": command, "fix_suggestion": None}
                command_without_sudo = command.replace("sudo ", "", 1); escaped_password = shlex.quote(sudo_password)
                command_to_run = f"echo {escaped_password} | sudo -S -p '' {command_without_sudo}"
                self.logger.info(f"Przygotowano polecenie sudo z hasłem (CLI): echo '****' | sudo -S -p '' ...")
            except (EOFError, KeyboardInterrupt):
                self.logger.warning("Wprowadzanie hasła sudo przerwane."); print("\nWprowadzanie hasła przerwane.")
                return {"success": False, "stdout": "", "stderr": "Wprowadzanie hasła przerwane.", "return_code": -1, "execution_time": 0.0, "working_dir": self.command_executor.get_current_working_dir(), "command": command, "fix_suggestion": None}

        self.logger.info(f"Backend: Finally executing: '{command_to_run}' in CWD: '{self.command_executor.get_current_working_dir()}'")
        # CommandExecutor.execute używa swojego self.current_working_dir
        result = self.command_executor.execute(command_to_run)

        self.logger.debug(f"--- Backend: RAW CommandExecutor Result for '{original_command_for_log}' (executed as '{command_to_run}') ---")
        self.logger.debug(f"  Success: {result.success}, RC: {result.return_code}, Time: {result.execution_time:.2f}s")
        self.logger.debug(f"  Result CWD (from executor): {result.working_dir}")
        self.logger.debug(f"  Executor CWD after exec (should match Result CWD if 'cd' was pure): {self.command_executor.get_current_working_dir()}")
        self.logger.debug(f"  STDOUT: {result.stdout.strip()[:200]}{'...' if len(result.stdout.strip()) > 200 else ''}")
        self.logger.debug(f"  STDERR: {result.stderr.strip()[:200]}{'...' if len(result.stderr.strip()) > 200 else ''}")

        fix_suggestion_text: Optional[str] = None
        if not result.success and (result.stderr or result.return_code != 0):
            self.logger.info(f"Backend: Command '{original_command_for_log}' failed (RC: {result.return_code}). Analyzing error...")
            error_analysis_response = self.ai_engine.analyze_execution_error_and_suggest_fix(
                original_command_for_log, result.stderr, result.return_code,
                self.distro_info, result.working_dir, # Użyj CWD z wyniku polecenia
                language_instruction=self._get_ai_language_instruction()
            )
            if error_analysis_response.success and error_analysis_response.fix_suggestion:
                fix_suggestion_text = error_analysis_response.fix_suggestion
                self.logger.info(f"Backend: AI Fix Suggestion: {fix_suggestion_text}")
                self._add_to_chat_history("model", f"System: Analiza błędu dla '{original_command_for_log}':\n{fix_suggestion_text}")
            elif error_analysis_response.error:
                self.logger.error(f"Backend: Błąd analizy błędu przez AI: {error_analysis_response.error}")
                self._add_to_chat_history("model", f"System: Nie udało się przeanalizować błędu '{original_command_for_log}'. Błąd AI: {error_analysis_response.error}")

        if original_command_for_log.strip().startswith("cd ") and result.success:
            self._add_to_chat_history("model", f"System: Zmieniono katalog roboczy na {result.working_dir}")
        else:
            output_summary = f"Wynik wykonania '{original_command_for_log}':\nRC: {result.return_code}\n"
            if result.stdout: output_summary += f"STDOUT:\n{result.stdout.strip()}\n"
            if result.stderr: output_summary += f"STDERR:\n{result.stderr.strip()}\n"
            self._add_to_chat_history("model", output_summary.strip())

        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr,
                "return_code": result.return_code, "execution_time": result.execution_time,
                "working_dir": result.working_dir, # Zawsze zwracaj CWD z wyniku CommandExecutor
                "command": original_command_for_log, "fix_suggestion": fix_suggestion_text}


    def interactive_mode(self):
        self.logger.info("Backend: Entering interactive mode.")
        print(f"{Fore.GREEN}=== Asystent AI dla systemu Linux (Backend CLI) ==={Style.RESET_ALL}")
        print(f"Wykryta dystrybucja: {Fore.CYAN}{self.distro_info.get('ID', 'nieznana')} {self.distro_info.get('VERSION_ID', '')}{Style.RESET_ALL}")
        print(f"Menedżer pakietów: {Fore.CYAN}{self.distro_info.get('PACKAGE_MANAGER', 'nieznany')}{Style.RESET_ALL}")
        print(f"Wpisz {Fore.YELLOW}exit{Style.RESET_ALL} lub {Fore.YELLOW}quit{Style.RESET_ALL}, aby zakończyć.")
        print(f"Wpisz {Fore.YELLOW}help{Style.RESET_ALL}, aby wyświetlić pomoc.\n")
        while True:
            try:
                current_dir_display = self.command_executor.get_current_working_dir()
                query = input(f"{Fore.GREEN}[{current_dir_display}]> {Style.RESET_ALL}")
                if query.lower() in ["exit", "quit"]: break
                if query.lower() == "help": self._show_help(); continue
                if not query.strip(): continue
                print(f"{Fore.YELLOW}Przetwarzanie zapytania...{Style.RESET_ALL}")
                result = self.process_query(query)
                if not result["success"]:
                    if result.get("error") == "CLARIFY_REQUEST": print(f"{Fore.YELLOW}AI prosi o doprecyzowanie. Spróbuj inaczej.{Style.RESET_ALL}")
                    elif result.get("error") == "DANGEROUS_REQUEST": print(f"{Fore.RED}AI zidentyfikowało zapytanie jako niebezpieczne.{Style.RESET_ALL}")
                    else: print(f"{Fore.RED}Błąd: {result.get('error', 'Nieznany błąd')}{Style.RESET_ALL}")
                    continue
                generated_command = result.get("command")
                if not generated_command: print(f"{Fore.RED}Błąd: AI nie zwróciło polecenia.{Style.RESET_ALL}"); continue
                print(f"\n{Fore.CYAN}Sugerowane polecenie:{Style.RESET_ALL}\n{Fore.WHITE}{generated_command}{Style.RESET_ALL}")
                if result.get("explanation"): print(f"\n{Fore.CYAN}Wyjaśnienie:{Style.RESET_ALL}\n{Fore.WHITE}{result['explanation']}{Style.RESET_ALL}")
                execute_input = input(f"\n{Fore.YELLOW}Wykonać? (t/n): {Style.RESET_ALL}")
                if execute_input.lower() in ["t", "tak", "y", "yes"]:
                    print(f"{Fore.YELLOW}Wykonywanie...{Style.RESET_ALL}")
                    exec_result = self.execute_command(generated_command, is_interactive_sudo_prompt=True)
                    # POPRAWIONE WCIĘCIE TUTAJ:
                    if exec_result["success"]:
                        print(f"{Fore.GREEN}Polecenie wykonane.{Style.RESET_ALL}")
                        if exec_result.get("stdout"): # Użyj .get() dla bezpieczeństwa
                            print(f"\n{Fore.WHITE}{exec_result['stdout'].strip()}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Błąd wykonania (kod: {exec_result['return_code']}){Style.RESET_ALL}")
                        if exec_result.get("stderr"): # Użyj .get()
                            print(f"\n{Fore.RED}{exec_result['stderr'].strip()}{Style.RESET_ALL}")
                        if exec_result.get("fix_suggestion"):
                            print(f"\n{Fore.CYAN}Sugestia AI:{Style.RESET_ALL}\n{Fore.WHITE}{exec_result['fix_suggestion']}{Style.RESET_ALL}")
            except KeyboardInterrupt: print("\nPrzerwano."); break
            except Exception as e: self.logger.error(f"Nieoczekiwany błąd CLI: {e}", exc_info=True); print(f"{Fore.RED}Krytyczny błąd: {e}{Style.RESET_ALL}")

# ... (reszta kodu pliku backend_cli.py bez zmian)

    def _show_help(self):
        print(f"\n{Fore.CYAN}=== Pomoc asystenta AI dla systemu Linux (Backend CLI) ==={Style.RESET_ALL}")
        print("Asystent przetwarza zapytania w języku naturalnym i generuje polecenia.")
        print(f"\n{Fore.CYAN}Przykłady:{Style.RESET_ALL}")
        print("- Pokaż wszystkie pliki w katalogu domowym")
        print(f"\n{Fore.CYAN}Komendy specjalne:{Style.RESET_ALL}")
        print(f"- {Fore.YELLOW}help{Style.RESET_ALL}: Ta pomoc")
        print(f"- {Fore.YELLOW}exit/quit{Style.RESET_ALL}: Zakończ\n")

def main():
    parser = argparse.ArgumentParser(description="Asystent AI dla systemu Linux (Backend)")
    parser.add_argument("--query", "-q", help="Zapytanie do asystenta")
    parser.add_argument("--execute", "-e", action="store_true", help="Automatycznie wykonaj polecenie (używane przez GUI)")
    parser.add_argument("--json", "-j", action="store_true", help="Zwróć wynik w formacie JSON (używane przez GUI)")
    parser.add_argument("--working-dir", "-wd", help="Początkowy katalog roboczy dla sesji backendu (używane przez GUI)")
    args = parser.parse_args()

    assistant = LinuxAIAssistant(initial_working_dir=args.working_dir)
    # current_logger już nie jest potrzebny, bo self.logger jest w instancji

    if args.query:
        assistant.logger.info(f"Backend: Zapytanie z argumentów: '{args.query}', execute: {args.execute}, json: {args.json}, CWD (arg): {args.working_dir}")

        # Jeśli --execute jest podane, zakładamy, że query to polecenie do wykonania
        if args.execute:
            command_to_run = args.query # Query jest tutaj traktowane jako pełne polecenie
            assistant.logger.info(f"Backend: Tryb --execute dla polecenia: '{command_to_run}'")
            # GUI powinno było już przygotować polecenie sudo z hasłem, jeśli było potrzebne.
            # Dlatego is_interactive_sudo_prompt=False.
            # working_dir_for_execution będzie args.working_dir, który został użyty do inicjalizacji
            # LinuxAIAssistant i powinien być aktualnym katalogiem, w którym GUI oczekuje wykonania.
            exec_result = assistant.execute_command(command_to_run, is_interactive_sudo_prompt=False)
            # UWAGA: execute_command w LinuxAIAssistant samo pobiera CWD z self.command_executor.get_current_working_dir()
            # więc to nie tu jest problem. Problemem jest to, że CWD CommandExecutora
            # może nie być poprawnie ustawione na to, co przekazało GUI.
            # W trybie --execute, `explanation` nie jest generowane przez `process_query`,
            # więc nie ma sensu go tutaj łączyć, chyba że GUI przekazałoby je osobno.
            # Na razie zwracamy tylko wynik wykonania.
            final_output = exec_result # exec_result już zawiera wszystkie potrzebne pola
            if args.json:
                print(json.dumps(final_output))
            else:
                print(f"Polecenie: {final_output.get('command')}")
                if final_output.get("success"): print(f"{Fore.GREEN}Wykonano pomyślnie.{Style.RESET_ALL}")
                else: print(f"{Fore.RED}Błąd wykonania: {final_output.get('stderr') or final_output.get('error')}{Style.RESET_ALL}")
                if final_output.get("stdout"): print(f"Stdout:\n{final_output.get('stdout')}")

        else: # Jeśli nie ma --execute, to --query jest zapytaniem do przetworzenia przez AI
            result_process = assistant.process_query(args.query)
            if args.json:
                print(json.dumps(result_process))
            else:
                if result_process.get("success"):
                    print(f"Sugerowane polecenie: {result_process.get('command')}")
                    if result_process.get("explanation"): print(f"Wyjaśnienie: {result_process['explanation']}")
                else:
                    if result_process.get("error") == "CLARIFY_REQUEST": print(f"{Fore.YELLOW}AI prosi o doprecyzowanie.{Style.RESET_ALL}")
                    elif result_process.get("error") == "DANGEROUS_REQUEST": print(f"{Fore.RED}AI zidentyfikowało zapytanie jako niebezpieczne.{Style.RESET_ALL}")
                    else: print(f"Błąd: {result_process.get('error')}")
    else:
        assistant.interactive_mode()

if __name__ == "__main__":
    main()
