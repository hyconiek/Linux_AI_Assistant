import os
import sys
import argparse
import logging
import readline # type: ignore
import signal
import json
import getpass
import shlex
from typing import Dict, List, Optional, Any, Set
import locale

if not (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')):
    pass

from modules.command_executor import CommandExecutor, DistributionDetector, SecurityValidator # type: ignore
from modules.gemini_integration import GeminiIntegration, GeminiApiResponse # type: ignore

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = "/tmp/linux_ai_assistant_backend.log"
effective_log_level_backend = logging.INFO
handlers_backend: List[logging.Handler] = [logging.FileHandler(LOG_FILE, mode='a')]
if os.environ.get("LAA_VERBOSE_LOGGING_EFFECTIVE") == "1":
    effective_log_level_backend = logging.DEBUG
    if not ("--json" in sys.argv or "-j" in sys.argv):
        handlers_backend.append(logging.StreamHandler(sys.stderr))
logging.basicConfig(level=effective_log_level_backend, format=LOG_FORMAT, handlers=handlers_backend)

if not ("--json" in sys.argv or "-j" in sys.argv):
    try:
        import colorama # type: ignore
        from colorama import Fore, Style # type: ignore
        colorama.init(autoreset=True)
    except ImportError:
        class Fore: GREEN = YELLOW = CYAN = WHITE = RED = "" # type: ignore
        class Style: RESET_ALL = "" # type: ignore
else:
    class Fore: GREEN = YELLOW = CYAN = WHITE = RED = "" # type: ignore
    class Style: RESET_ALL = "" # type: ignore

class LinuxAIAssistant:
    def __init__(self, initial_working_dir: Optional[str] = None):
        self.logger = logging.getLogger("backend_assistant_instance")
        self.logger.info("LinuxAIAssistant (backend instance) logger initialized.")
        self.command_executor = CommandExecutor(timeout=120)
        if initial_working_dir and os.path.isdir(initial_working_dir):
            if self.command_executor.set_current_working_dir(initial_working_dir):
                 self.logger.info(f"Backend: Initial working directory for CommandExecutor set to: '{initial_working_dir}' by argument.")
            else:
                 self.logger.warning(f"Backend: CommandExecutor.set_current_working_dir FAILED for '{initial_working_dir}'. Executor CWD remains '{self.command_executor.get_current_working_dir()}'.")
        else:
            if initial_working_dir:
                self.logger.warning(f"Backend: Initial working_dir argument '{initial_working_dir}' is not a valid directory. Using default Executor CWD: '{self.command_executor.get_current_working_dir()}'.")
            else:
                self.logger.info(f"Backend: No initial working_dir argument provided. Using default Executor CWD: '{self.command_executor.get_current_working_dir()}'.")

        self.ai_engine = GeminiIntegration()
        self.distro_detector = DistributionDetector()
        self.distro_info = self.distro_detector.detect_distribution()
        self.chat_history_for_ai: List[Dict[str, Any]] = []
        try:
            lang_code, _ = locale.getdefaultlocale()
            if lang_code and '_' in lang_code: self.system_language = lang_code.split('_')[0]
            elif lang_code: self.system_language = lang_code
            else: self.system_language = "en"
        except Exception as e:
            self.logger.warning(f"Backend: Could not detect system language: {e}. Defaulting to 'en'.")
            self.system_language = "en"
        self.logger.info(f"Backend: Detected system language (for AI): {self.system_language}")
        self.logger.info(f"Backend: Detected distribution: {self.distro_info}")
        self.logger.info(f"Backend: Current working directory after initialization: {self.command_executor.get_current_working_dir()}")

        self.basic_command_prefixes_cli: Set[str] = {
            "ls", "cd", "pwd", "mkdir", "cp", "mv", "cat", "echo", "clear", "whoami",
            "df", "du", "free", "sensors", "man", "history", "ping", "ifconfig", "ip",
            "ssh", "scp", "top", "ps", "kill",
            "apt", "dnf", "yum", "pacman", "zypper", "sudo"
        }
        self.force_ai_for_commands_cli: Set[str] = {"rm"} # Commands that should always go through AI gen

    def _get_ai_language_instruction(self) -> str:
        if self.system_language == "pl":
            return "ODPOWIADAJ ZAWSZE W JĘZYKU POLSKIM. Wyjaśnienie polecenia, pytania doprecyzowujące, sugestie naprawcze i wszelkie inne teksty MUSZĄ być po polsku."
        return "Respond always in English. The command explanation, clarification questions, fix suggestions, and any other text MUST be in English."

    def _add_to_chat_history(self, role: str, text_content: str):
        max_text_len = 1000
        if len(text_content) > max_text_len:
            text_content = text_content[:max_text_len] + " ... (skrócono)"

        valid_role = role.lower() if role.lower() in ["user", "model"] else "user"
        self.chat_history_for_ai.append({"role": valid_role, "parts": [{"text": text_content}]})
        max_history_turns = 5
        if len(self.chat_history_for_ai) > max_history_turns * 2:
            self.chat_history_for_ai = self.chat_history_for_ai[-(max_history_turns * 2):]

    def process_query(self, query: str) -> Dict[str, Any]:
        current_dir_for_ai_context = self.command_executor.get_current_working_dir()
        self.logger.info(f"Backend process_query: Query='{query}', CWD for AI context='{current_dir_for_ai_context}'")

        cwd_entries_list: List[str] = []
        try:
            if os.path.isdir(current_dir_for_ai_context):
                all_entries = os.listdir(current_dir_for_ai_context)
                cwd_entries_list = all_entries[:100]
                if len(all_entries) > 100 :
                     self.logger.info(f"Backend process_query: Providing first 100 entries from CWD ({len(all_entries)} total).")
                else:
                    self.logger.info(f"Backend process_query: Providing {len(cwd_entries_list)} entries from CWD.")
        except Exception as e:
            self.logger.warning(f"Backend: Nie udało się odczytać wpisów z CWD ({current_dir_for_ai_context}): {e}")

        self._add_to_chat_history("user", query)

        api_response = self.ai_engine.generate_command_with_explanation(
            user_prompt=query,
            distro_info=self.distro_info,
            working_dir=current_dir_for_ai_context,
            cwd_file_list=cwd_entries_list,
            history=self.chat_history_for_ai,
            language_instruction=self._get_ai_language_instruction()
        )

        if api_response.success and api_response.needs_file_search:
            self.logger.info(f"AI zażądało przeszukania plików. Wzorzec: '{api_response.file_search_pattern}', Komunikat: '{api_response.file_search_message}'")
            search_pattern = api_response.file_search_pattern if api_response.file_search_pattern else "*"
            effective_search_cmd_pattern = f"*{search_pattern}*" if '*' not in search_pattern and '?' not in search_pattern and '[' not in search_pattern else search_pattern
            find_command = f"find . \\( -path './git/*' -o -path './.*' \\) -prune -o -maxdepth 2 -type f -iname {shlex.quote(effective_search_cmd_pattern)} -print | sed 's|^\\./||'"
            self.logger.info(f"Wykonuję polecenie wyszukiwania: {find_command} w {current_dir_for_ai_context}")
            search_result = self.command_executor.execute(find_command, working_dir_override=current_dir_for_ai_context)
            found_files_list: List[str] = []
            if search_result.success and search_result.stdout:
                found_files_list = [f.strip() for f in search_result.stdout.splitlines() if f.strip()]
                self.logger.info(f"Znaleziono plików ({len(found_files_list)}): {found_files_list[:20]}")
            else:
                self.logger.warning(f"Wyszukiwanie plików nie powiodło się lub nic nie znaleziono. Stderr: {search_result.stderr}")
            combined_files_for_ai = list(set(cwd_entries_list + found_files_list))
            search_feedback_to_ai = f"System: Wyniki wyszukiwania dla wzorca '{search_pattern}' w '{current_dir_for_ai_context}' (oraz 1 poziom niżej, ignorując ukryte i .git): "
            if found_files_list: search_feedback_to_ai += f"Znaleziono: {', '.join(found_files_list[:30])}{'...' if len(found_files_list) > 30 else ''}."
            else: search_feedback_to_ai += "Nic nie znaleziono."
            temp_history_for_search_context = self.chat_history_for_ai.copy()
            temp_history_for_search_context.append({"role": "model", "parts": [{"text": search_feedback_to_ai}]})
            self.logger.info("Ponowne wywołanie AI z zaktualizowaną listą plików i informacją o wyszukiwaniu.")
            api_response = self.ai_engine.generate_command_with_explanation(
                user_prompt=query, distro_info=self.distro_info, working_dir=current_dir_for_ai_context,
                cwd_file_list=combined_files_for_ai, history=temp_history_for_search_context,
                language_instruction=self._get_ai_language_instruction()
            )

        response_to_gui: Dict[str, Any] = {
            "success": api_response.success, "error": api_response.error,
            "working_dir": current_dir_for_ai_context, "is_text_answer": api_response.is_text_answer,
            "command": None, "explanation": None, "suggested_interaction_input": None,
            "suggested_button_label": None, "needs_file_search": False
        }

        if not api_response.success:
            error_msg = api_response.error or "Nie udało się przetworzyć zapytania"
            if api_response.error == "CLARIFY_REQUEST": self._add_to_chat_history("model", "System: AI requested clarification.")
            elif api_response.error == "DANGEROUS_REQUEST": self._add_to_chat_history("model", "System: AI identified query as dangerous.")
            elif api_response.error: self._add_to_chat_history("model", f"System: Error from AI - {api_response.error}")
            response_to_gui["error"] = error_msg
        else:
            if api_response.is_text_answer:
                response_to_gui["explanation"] = api_response.explanation
                self._add_to_chat_history("model", f"Odpowiedź tekstowa AI:\n{api_response.explanation}")
            else:
                response_to_gui["command"] = api_response.command; response_to_gui["explanation"] = api_response.explanation
                response_to_gui["suggested_interaction_input"] = api_response.suggested_interaction_input
                response_to_gui["suggested_button_label"] = api_response.suggested_button_label
                ai_model_response_text = f"Polecenie: {api_response.command}\nWYJAŚNIENIE: {api_response.explanation}"
                if api_response.suggested_interaction_input and api_response.suggested_button_label:
                    ai_model_response_text += f"\nINTERAKCJA_POLECENIE: {api_response.suggested_interaction_input};{api_response.suggested_button_label}"
                self._add_to_chat_history("model", ai_model_response_text)
        return response_to_gui

    def execute_command(self, command: str, is_interactive_sudo_prompt: bool = False) -> Dict[str, Any]:
        self.logger.info(f"Backend: Preparing to execute: '{command}' (interactive sudo: {is_interactive_sudo_prompt}) in CWD: '{self.command_executor.get_current_working_dir()}'")
        command_to_run = command; original_command_for_log = command

        if SecurityValidator.requires_confirmation(command) and \
           command.strip().startswith("sudo ") and \
           is_interactive_sudo_prompt and \
           not (command.strip().startswith("echo ") and "sudo -S" in command):
            print(f"{Fore.YELLOW}Polecenie '{command}' wymaga uprawnień sudo.{Style.RESET_ALL}")
            # No getpass here for non-interactive sudo from GUI, this path is more for CLI direct sudo.
            # GUI will send pre-filled sudo if password was obtained there.
            # If is_interactive_sudo_prompt is True, it means CLI mode.
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
        result = self.command_executor.execute(command_to_run)

        fix_suggestion_text: Optional[str] = None
        if not result.success and (result.stderr or result.return_code != 0):
            self.logger.info(f"Backend: Command '{original_command_for_log}' failed (RC: {result.return_code}). Analyzing error...")
            error_analysis_response = self.ai_engine.analyze_execution_error_and_suggest_fix(
                original_command_for_log, result.stderr, result.return_code,
                self.distro_info, result.working_dir,
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
        else: # For non-cd commands or failed cd
            output_summary = f"Wynik wykonania '{original_command_for_log}':\nRC: {result.return_code}\n"
            if result.stdout: output_summary += f"STDOUT:\n{result.stdout.strip()}\n"
            if result.stderr: output_summary += f"STDERR:\n{result.stderr.strip()}\n"
            self._add_to_chat_history("model", output_summary.strip())

        # Crucially, ensure the CommandExecutor's CWD is updated for the next CLI prompt if cd was successful.
        # This is already handled inside self.command_executor.execute()

        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr,
                "return_code": result.return_code, "execution_time": result.execution_time,
                "working_dir": result.working_dir, # This is the CWD after command execution
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

                command_prefix = query.split(' ', 1)[0].lower()
                is_basic_sudo_cli = command_prefix == "sudo" and len(query.split()) > 1 and query.split()[1].lower() in self.basic_command_prefixes_cli

                if (command_prefix in self.basic_command_prefixes_cli or is_basic_sudo_cli) and \
                   command_prefix not in self.force_ai_for_commands_cli:
                    print(f"{Fore.YELLOW}Wykonywanie podstawowego polecenia bezpośrednio...{Style.RESET_ALL}")
                    exec_result = self.execute_command(query, is_interactive_sudo_prompt=True)

                    if exec_result["success"]:
                        print(f"{Fore.GREEN}Polecenie wykonane pomyślnie.{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Błąd wykonania polecenia (kod: {exec_result['return_code']}).{Style.RESET_ALL}")

                    if exec_result.get("stdout"): print(f"\n{Fore.WHITE}{exec_result['stdout'].strip()}{Style.RESET_ALL}")
                    if exec_result.get("stderr"): print(f"\n{Fore.RED}{exec_result['stderr'].strip()}{Style.RESET_ALL}")

                    if exec_result.get("fix_suggestion"):
                         print(f"\n{Fore.CYAN}Sugestia AI (naprawa):{Style.RESET_ALL}\n{Fore.WHITE}{exec_result['fix_suggestion']}{Style.RESET_ALL}")

                    # Get AI explanation for the executed basic command
                    if self.ai_engine:
                        print(f"{Fore.YELLOW}Pobieranie wyjaśnienia AI dla '{query}'...{Style.RESET_ALL}")
                        analysis_res = self.ai_engine.analyze_text_input_type(query, language_instruction=self._get_ai_language_instruction())
                        if analysis_res.success and analysis_res.explanation:
                            print(f"\n{Fore.CYAN}Wyjaśnienie AI:{Style.RESET_ALL}\n{Fore.WHITE}{analysis_res.explanation}{Style.RESET_ALL}")
                        elif analysis_res.error:
                            print(f"{Fore.RED}Błąd pobierania wyjaśnienia AI: {analysis_res.error}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.YELLOW}AI nie dostarczyło wyjaśnienia.{Style.RESET_ALL}")
                    print() # Extra newline for clarity
                    continue # Loop for next command

                # If not a basic command or forced to AI, proceed with AI generation
                print(f"{Fore.YELLOW}Przetwarzanie zapytania przez AI...{Style.RESET_ALL}")
                result = self.process_query(query)
                if not result["success"]:
                    if result.get("error") == "CLARIFY_REQUEST": print(f"{Fore.YELLOW}AI prosi o doprecyzowanie. Spróbuj inaczej.{Style.RESET_ALL}")
                    elif result.get("error") == "DANGEROUS_REQUEST": print(f"{Fore.RED}AI zidentyfikowało zapytanie jako niebezpieczne.{Style.RESET_ALL}")
                    else: print(f"{Fore.RED}Błąd: {result.get('error', 'Nieznany błąd')}{Style.RESET_ALL}")
                    continue

                if result.get("is_text_answer"):
                    print(f"\n{Fore.CYAN}Odpowiedź AI:{Style.RESET_ALL}\n{Fore.WHITE}{result.get('explanation', 'Brak odpowiedzi.')}{Style.RESET_ALL}")
                elif result.get("command"):
                    generated_command = result.get("command")
                    print(f"\n{Fore.CYAN}Sugerowane polecenie:{Style.RESET_ALL}\n{Fore.WHITE}{generated_command}{Style.RESET_ALL}")
                    if result.get("explanation"): print(f"\n{Fore.CYAN}Wyjaśnienie:{Style.RESET_ALL}\n{Fore.WHITE}{result['explanation']}{Style.RESET_ALL}")

                    interaction_prompt_cli = f"\n{Fore.YELLOW}Wykonać? (t/n): {Style.RESET_ALL}"
                    if result.get("suggested_button_label"):
                        interaction_prompt_cli = f"\n{Fore.YELLOW}{result['suggested_button_label']}? (t/n/a-anuluj): {Style.RESET_ALL}"

                    execute_input = input(interaction_prompt_cli)
                    if execute_input.lower() in ["t", "tak", "y", "yes"]:
                        print(f"{Fore.YELLOW}Wykonywanie...{Style.RESET_ALL}")
                        exec_result = self.execute_command(generated_command, is_interactive_sudo_prompt=True) # type: ignore
                        if exec_result["success"]:
                            print(f"{Fore.GREEN}Polecenie wykonane.{Style.RESET_ALL}")
                            if exec_result.get("stdout"):
                                print(f"\n{Fore.WHITE}{exec_result['stdout'].strip()}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}Błąd wykonania (kod: {exec_result['return_code']}){Style.RESET_ALL}")
                            if exec_result.get("stderr"):
                                print(f"\n{Fore.RED}{exec_result['stderr'].strip()}{Style.RESET_ALL}")
                            if exec_result.get("fix_suggestion"):
                                print(f"\n{Fore.CYAN}Sugestia AI:{Style.RESET_ALL}\n{Fore.WHITE}{exec_result['fix_suggestion']}{Style.RESET_ALL}")
                else:
                     print(f"{Fore.RED}Błąd: AI nie zwróciło ani polecenia, ani odpowiedzi tekstowej.{Style.RESET_ALL}")
                print() # Extra newline for clarity
            except KeyboardInterrupt: print("\nPrzerwano."); break
            except Exception as e: self.logger.error(f"Nieoczekiwany błąd CLI: {e}", exc_info=True); print(f"{Fore.RED}Krytyczny błąd: {e}{Style.RESET_ALL}")

    def _show_help(self):
        print(f"\n{Fore.CYAN}=== Pomoc asystenta AI dla systemu Linux (Backend CLI) ==={Style.RESET_ALL}")
        print("Asystent przetwarza zapytania w języku naturalnym i generuje polecenia.")
        print("Podstawowe polecenia Linuksa (np. ls, cd, pwd) są wykonywane bezpośrednio, a następnie AI dostarcza wyjaśnienie.")
        print(f"\n{Fore.CYAN}Przykłady zapytań do AI:{Style.RESET_ALL}")
        print("- Pokaż wszystkie pliki w katalogu domowym")
        print("- Zainstaluj firefox")
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

    if args.query:
        assistant.logger.info(f"Backend: Zapytanie z argumentów: '{args.query}', execute: {args.execute}, json: {args.json}, CWD (arg): {args.working_dir}")
        if args.execute: # This path is mainly for GUI calling backend for direct execution
            command_to_run = args.query
            assistant.logger.info(f"Backend: Tryb --execute dla polecenia: '{command_to_run}'")
            # is_interactive_sudo_prompt=False because GUI handles password for sudo if needed
            exec_result = assistant.execute_command(command_to_run, is_interactive_sudo_prompt=False)
            final_output = exec_result
            if args.json:
                print(json.dumps(final_output))
            else: # Should not happen if GUI calls with --json
                print(f"Polecenie: {final_output.get('command')}")
                if final_output.get("success"): print(f"{Fore.GREEN}Wykonano pomyślnie.{Style.RESET_ALL}")
                else: print(f"{Fore.RED}Błąd wykonania: {final_output.get('stderr') or final_output.get('error')}{Style.RESET_ALL}")
                if final_output.get("stdout"): print(f"Stdout:\n{final_output.get('stdout')}")
        else: # This path is for GUI calling backend for AI processing
            result_process = assistant.process_query(args.query)
            if args.json:
                print(json.dumps(result_process))
            else: # Should not happen if GUI calls with --json
                if result_process.get("success"):
                    if result_process.get("is_text_answer"):
                        print(f"Odpowiedź AI: {result_process.get('explanation')}")
                    elif result_process.get("command"):
                        print(f"Sugerowane polecenie: {result_process.get('command')}")
                        if result_process.get("explanation"): print(f"Wyjaśnienie: {result_process['explanation']}")
                        if result_process.get("suggested_button_label"):
                            print(f"Sugestia interakcji (etykieta przycisku): {result_process['suggested_button_label']}")
                            print(f"Sugerowana odpowiedź tekstowa: {result_process.get('suggested_interaction_input')}")
                    else:
                        print(f"Błąd: AI zwróciło sukces, ale bez polecenia/odpowiedzi.")
                else:
                    if result_process.get("error") == "CLARIFY_REQUEST": print(f"{Fore.YELLOW}AI prosi o doprecyzowanie.{Style.RESET_ALL}")
                    elif result_process.get("error") == "DANGEROUS_REQUEST": print(f"{Fore.RED}AI zidentyfikowało zapytanie jako niebezpieczne.{Style.RESET_ALL}")
                    else: print(f"Błąd: {result_process.get('error')}")
    else: # Interactive CLI mode
        assistant.interactive_mode()

if __name__ == "__main__":
    main()
