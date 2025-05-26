import os
import sys
import argparse
import logging
import readline # type: ignore
import shutil # Dodano do sprawdzania terminali
import json
import getpass
import shlex
from typing import Dict, List, Optional, Any, Set
import locale
import traceback
import subprocess # Dodano do Popen dla external terminal

if not (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')):
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    module_path = os.path.join(current_script_path, "modules")
    if module_path not in sys.path:
        sys.path.insert(0, module_path)
else:
    # Jeśli aplikacja jest zamrożona przez PyInstallera
    module_path = os.path.join(sys._MEIPASS, "src", "modules") # Zakładając, że PyInstaller kopiuje 'src/modules' do 'src/modules' w _MEIPASS
    if module_path not in sys.path:
         sys.path.insert(0, module_path)


from command_executor import CommandExecutor, DistributionDetector, SecurityValidator
from gemini_integration import GeminiIntegration, GeminiApiResponse

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = "/tmp/linux_ai_assistant_backend.log" # Zmieniono z laa_gui.log na backend.log
effective_log_level_backend = logging.INFO # Domyślnie INFO
handlers_backend: List[logging.Handler] = []
try:
    handlers_backend.append(logging.FileHandler(LOG_FILE, mode='a')) # Tryb 'a' do dopisywania
except Exception as e:
    # To jest backend, więc nie ma sensu używać print() do GUI. Log na stderr.
    print(f"OSTRZEŻENIE: Nie można otworzyć pliku logu '{LOG_FILE}': {e}. Logowanie do pliku wyłączone.", file=sys.stderr)

# Ustawienie LAA_VERBOSE_LOGGING_EFFECTIVE powinno być przekazywane z GUI
if os.environ.get("LAA_VERBOSE_LOGGING_EFFECTIVE") == "1":
    effective_log_level_backend = logging.DEBUG
    # W trybie backendu JSON, nie chcemy dodatkowego outputu na stderr, chyba że to błąd krytyczny.
    # GUI będzie odbierać logi przez dedykowany mechanizm, jeśli zaimplementowany, lub z pliku.
    # Jeśli backend jest uruchamiany bezpośrednio w CLI (nie przez GUI), wtedy StreamHandler ma sens.
    if not ("--json" in sys.argv or "-j" in sys.argv): # Tylko jeśli nie jest w trybie JSON dla GUI
        handlers_backend.append(logging.StreamHandler(sys.stderr)) # Loguj DEBUG na stderr w trybie CLI
logging.basicConfig(level=effective_log_level_backend, format=LOG_FORMAT, handlers=handlers_backend)
logger_main_cli = logging.getLogger("backend_cli_main") # Logger dla funkcji main tego pliku

# Kolory tylko dla trybu CLI, nie JSON
if not ("--json" in sys.argv or "-j" in sys.argv):
    try:
        import colorama
        from colorama import Fore, Style
        colorama.init(autoreset=True)
    except ImportError:
        class Fore: GREEN = YELLOW = CYAN = WHITE = RED = "" # type: ignore
        class Style: RESET_ALL = "" # type: ignore
else: # W trybie JSON, wyłącz kolory
    class Fore: GREEN = YELLOW = CYAN = WHITE = RED = "" # type: ignore
    class Style: RESET_ALL = "" # type: ignore


class LinuxAIAssistant:
    def __init__(self, initial_working_dir: Optional[str] = None):
        self.logger = logging.getLogger("backend_assistant_instance") # Osobny logger dla instancji
        self.logger.info("LinuxAIAssistant (backend instance) logger initialized.")
        self.command_executor = CommandExecutor(timeout=120) # Domyślny timeout

        # Ustawianie initial_working_dir dla CommandExecutor
        if initial_working_dir:
            abs_initial_dir = os.path.abspath(initial_working_dir)
            if os.path.isdir(abs_initial_dir):
                if self.command_executor.set_current_working_dir(abs_initial_dir): # Użyj metody settera
                    self.logger.info(f"Backend: Początkowy katalog roboczy CommandExecutor ustawiony na: '{abs_initial_dir}' przez argument.")
            else:
                self.logger.warning(f"Backend: Początkowy argument working_dir '{initial_working_dir}' nie jest prawidłowym katalogiem. Używam domyślnego CWD egzekutora.")
        else:
            self.logger.info(f"Backend: Brak argumentu initial_working_dir. Używam domyślnego CWD egzekutora.")


        self.ai_engine = GeminiIntegration(model_name='gemini-2.5-flash-preview-05-20') # Użyj stabilnej nazwy
        self.distro_detector = DistributionDetector()
        self.distro_info = self.distro_detector.detect_distribution()
        self.chat_history_for_ai: List[Dict[str, Any]] = [] # Historia tylko dla AI, resetowana per sesję z GUI

        try:
            # Próba wykrycia języka systemu dla promptów AI
            if hasattr(locale, 'getlocale') and callable(locale.getlocale):
                # locale.getlocale(locale.LC_CTYPE) jest bardziej precyzyjne dla języka interfejsu
                try:
                    loc = locale.getlocale(locale.LC_CTYPE) # LC_MESSAGES lub LC_CTYPE
                    lang_code = loc[0] if loc and loc[0] else None
                except locale.Error: # Może rzucić błąd, jeśli locale nie jest ustawione
                    lang_code = None
            else: # Starsze wersje Pythona lub systemy bez pełnego wsparcia locale
                lang_code, _ = locale.getdefaultlocale()

            if lang_code and '_' in lang_code:
                self.system_language = lang_code.split('_')[0].lower()
            elif lang_code: # np. "pl" bez kodu kraju
                self.system_language = lang_code.lower()
            else:
                self.system_language = "en" # Domyślnie angielski
        except Exception as e:
            self.logger.warning(f"Backend: Nie można wykryć języka systemu: {e}. Ustawiam domyślny 'en'.")
            self.system_language = "en"

        self.logger.info(f"Backend: Wykryty język systemu (dla AI): {self.system_language}")
        self.logger.info(f"Backend: Wykryta dystrybucja: {self.distro_info}")
        self.logger.info(f"Backend: Bieżący katalog roboczy po inicjalizacji: {self.command_executor.get_current_working_dir()}")


        # Definicje poleceń dla trybu CLI (bezpośrednie wykonanie)
        self.basic_command_prefixes_cli: Set[str] = {
            "ls", "cd", "pwd", "mkdir", "cp", "mv", "cat", "echo", "clear", "whoami",
            "df", "du", "free", "sensors", "man", "history", "ping", "ifconfig", "ip",
            "ssh", "scp", "kill", # top i ps usunięte, bo są interaktywne
            # Dodaj menedżery pakietów jako podstawowe, ale pamiętaj, że sudo jest potrzebne
            "apt", "dnf", "yum", "pacman", "zypper", "sudo"
        }
        # Polecenia, które nawet w CLI powinny być kierowane do AI
        self.force_ai_for_commands_cli: Set[str] = {"rm", "top", "htop", "nano", "vim", "less", "man"} # Dodano interaktywne
        self.interactive_commands_requiring_new_terminal: Set[str] = {"top", "htop", "nano", "vim", "less", "man", "mc"}


    def _get_ai_language_instruction(self) -> str:
        if self.system_language == "pl":
            return "ODPOWIADAJ ZAWSZE W JĘZYKU POLSKIM. Wyjaśnienie polecenia, pytania doprecyzowujące, sugestie naprawcze i wszelkie inne teksty MUSZĄ być po polsku."
        elif self.system_language == "cs": # Dodano dla czeskiego
             return "ODPOVÍDEJ VŽDY ČESKY. Vysvětlení příkazu, doplňující otázky, návrhy oprav a veškeré další texty MUSÍ být v češtině."
        # Domyślnie angielski
        return "Respond always in English. The command explanation, clarification questions, fix suggestions, and any other text MUST be in English."

    def _add_to_chat_history(self, role: str, text_content: str):
        # Ogranicz długość pojedynczej wiadomości i całkowitą historię
        max_text_len = 1000 # Maksymalna długość pojedynczej części tekstu
        if len(text_content) > max_text_len:
            text_content = text_content[:max_text_len] + " ... (skrócono)"

        # Rola musi być 'user' lub 'model'
        valid_role = role.lower() if role.lower() in ["user", "model"] else "user"

        self.chat_history_for_ai.append({"role": valid_role, "parts": [{"text": text_content}]})

        # Ogranicz liczbę tur w historii (jedna tura = user + model)
        max_history_turns = 5 # Np. 5 ostatnich interakcji user-model
        if len(self.chat_history_for_ai) > max_history_turns * 2: # *2 bo user i model
            self.chat_history_for_ai = self.chat_history_for_ai[-(max_history_turns * 2):]

    def process_query(self, query: str) -> Dict[str, Any]:
        current_dir_for_ai_context = self.command_executor.get_current_working_dir()
        self.logger.info(f"Backend process_query: Zapytanie='{query}', CWD dla kontekstu AI='{current_dir_for_ai_context}'")
        self.logger.debug(f"Bieżąca historia czatu PRZED dodaniem zapytania: {json.dumps(self.chat_history_for_ai, indent=2, ensure_ascii=False)}")

        cwd_entries_list: List[str] = []
        try:
            if os.path.isdir(current_dir_for_ai_context):
                all_entries = os.listdir(current_dir_for_ai_context)
                # Sortuj dla spójności i ogranicz liczbę, aby nie przekroczyć limitu tokenów AI
                cwd_entries_list = all_entries[:100] # Pierwsze 100 wystarczy dla kontekstu
                if len(all_entries) > 100 : self.logger.info(f"Backend process_query: Dostarczam pierwsze 100 wpisów z CWD ({len(all_entries)} wszystkich).")
                else: self.logger.info(f"Backend process_query: Dostarczam {len(cwd_entries_list)} wpisów z CWD.")
        except Exception as e: self.logger.warning(f"Backend: Nie udało się odczytać wpisów z CWD ({current_dir_for_ai_context}): {e}")

        self._add_to_chat_history("user", query)
        self.logger.debug(f"Bieżąca historia czatu PO dodaniu zapytania użytkownika: {json.dumps(self.chat_history_for_ai, indent=2, ensure_ascii=False)}")

        if not self.ai_engine.is_configured:
            self.logger.error("Backend: Silnik AI nie jest skonfigurowany w process_query.")
            # Zwróć strukturę zgodną z oczekiwaniami GUI, nawet przy błędzie
            return {"success": False, "error": "Silnik AI nie jest skonfigurowany.", "working_dir": current_dir_for_ai_context, "is_text_answer": False, "needs_external_terminal": False}

        # Pierwsze wywołanie AI
        api_response = self.ai_engine.generate_command_with_explanation(
            user_prompt=query, distro_info=self.distro_info, working_dir=current_dir_for_ai_context,
            cwd_file_list=cwd_entries_list, history=self.chat_history_for_ai, # Przekaż aktualną historię
            language_instruction=self._get_ai_language_instruction()
        )

        # Jeśli AI zażądało przeszukania plików
        if api_response.success and api_response.needs_file_search:
            self.logger.info(f"AI zażądało przeszukania plików. Wzorzec: '{api_response.file_search_pattern}', Komunikat: '{api_response.file_search_message}'")
            search_pattern = api_response.file_search_pattern if api_response.file_search_pattern else "*"
            # Ulepszony wzorzec dla find, aby był bardziej użyteczny jeśli użytkownik poda tylko część nazwy
            effective_search_cmd_pattern = f"*{search_pattern}*" if '*' not in search_pattern and '?' not in search_pattern and '[' not in search_pattern else search_pattern

            # Uproszczone i bezpieczniejsze polecenie find, przeszukuje tylko bieżący katalog i jeden poziom niżej, ignoruje ukryte i .git
            find_command = f"find . \\( -path './git/*' -o -path './.*' \\) -prune -o -maxdepth 2 -type f -iname {shlex.quote(effective_search_cmd_pattern)} -print | sed 's|^\\./||'"
            self.logger.info(f"Wykonuję polecenie wyszukiwania: {find_command} w {current_dir_for_ai_context}")
            search_result = self.command_executor.execute(find_command, working_dir_override=current_dir_for_ai_context)

            found_files_list: List[str] = []
            if search_result.success and search_result.stdout:
                found_files_list = [f.strip() for f in search_result.stdout.splitlines() if f.strip()]
                self.logger.info(f"Znaleziono plików ({len(found_files_list)}): {found_files_list[:20]}") # Loguj tylko część dla zwięzłości
            else: self.logger.warning(f"Wyszukiwanie plików nie powiodło się lub nic nie znaleziono. Stderr: {search_result.stderr}")

            combined_files_for_ai = list(set(cwd_entries_list + found_files_list)) # Połącz oryginalne pliki z CWD z wynikami wyszukiwania

            # Przygotuj informację zwrotną dla AI o wynikach wyszukiwania
            search_feedback_to_ai = f"System: Wyniki wyszukiwania dla wzorca '{search_pattern}' w '{current_dir_for_ai_context}' (oraz 1 poziom niżej, ignorując ukryte i .git): "
            if found_files_list:
                search_feedback_to_ai += f"Znaleziono: {', '.join(found_files_list[:30])}{'...' if len(found_files_list) > 30 else ''}."
            else:
                search_feedback_to_ai += "Nic nie znaleziono."

            # --- POPRAWIONA LOGIKA BUDOWANIA HISTORII DLA PONOWNEGO WYWOŁANIA ---
            # Kopiujemy całą historię do tego momentu (która zawiera oryginalne zapytanie użytkownika)
            history_for_next_turn = [turn.copy() for turn in self.chat_history_for_ai]
            # Dodajemy odpowiedź systemową (rezultat wyszukiwania) jako turę modelu
            history_for_next_turn.append({"role": "model", "parts": [{"text": search_feedback_to_ai}]})
            # Nie modyfikujemy self.chat_history_for_ai tutaj bezpośrednio,
            # bo _add_to_chat_history na końcu tej funkcji zajmie się finalną odpowiedzią AI.

            self.logger.info("Ponowne wywołanie AI z oryginalnym zapytaniem i zaktualizowaną listą plików oraz informacją o wyszukiwaniu w historii.")
            api_response = self.ai_engine.generate_command_with_explanation(
                user_prompt=query, # Oryginalne zapytanie użytkownika jest nadal potrzebne
                distro_info=self.distro_info,
                working_dir=current_dir_for_ai_context,
                cwd_file_list=combined_files_for_ai, # Przekaż połączoną listę plików
                history=history_for_next_turn,      # Użyj nowo zbudowanej historii
                language_instruction=self._get_ai_language_instruction()
            )

        # Przygotowanie odpowiedzi dla GUI
        response_to_gui: Dict[str, Any] = {
            "success": api_response.success,
            "command": api_response.command,
            "explanation": api_response.explanation,
            "error": api_response.error,
            "is_text_answer": api_response.is_text_answer,
            "needs_file_search": api_response.needs_file_search, # Chociaż już obsłużone, to informacja dla GUI
            "file_search_pattern": api_response.file_search_pattern,
            "file_search_message": api_response.file_search_message,
            "suggested_interaction_input": api_response.suggested_interaction_input,
            "suggested_button_label": api_response.suggested_button_label,
            "needs_external_terminal": api_response.needs_external_terminal,
            "working_dir": current_dir_for_ai_context # Zawsze zwracaj CWD kontekstu
        }

        # Aktualizacja historii czatu na podstawie finalnej odpowiedzi AI
        if not api_response.success:
            error_msg = api_response.error or "Nie udało się przetworzyć zapytania"
            # Nie loguj do głównej historii, jeśli to tylko prośba o szukanie, bo to już obsłużone powyżej
            if api_response.error != "SZUKAJ_PLIKOW":
                if api_response.error == "CLARIFY_REQUEST": self._add_to_chat_history("model", "System: AI requested clarification.")
                elif api_response.error == "DANGEROUS_REQUEST": self._add_to_chat_history("model", "System: AI identified query as dangerous.")
                elif api_response.error: self._add_to_chat_history("model", f"System: Error from AI - {api_response.error}")
            # response_to_gui["error"] już ustawione
        else:
            if api_response.is_text_answer:
                # response_to_gui["explanation"] już ustawione
                self._add_to_chat_history("model", f"Odpowiedź tekstowa AI:\n{api_response.explanation}")
            elif api_response.command:
                # response_to_gui["command"] i ["explanation"] już ustawione
                ai_model_response_text = f"Polecenie: {api_response.command}\nWYJAŚNIENIE: {api_response.explanation}"
                if api_response.suggested_interaction_input and api_response.suggested_button_label:
                     ai_model_response_text += f"\nINTERAKCJA_POLECENIE: {api_response.suggested_interaction_input};{api_response.suggested_button_label}"
                elif api_response.needs_external_terminal and api_response.suggested_button_label:
                     ai_model_response_text += f"\nINTERAKCJA_TERMINAL: ;{api_response.suggested_button_label}"
                self._add_to_chat_history("model", ai_model_response_text)
            # Jeśli needs_file_search było true, ale drugie wywołanie AI nie dało komendy/odpowiedzi tekstowej,
            # to `api_response` może nie mieć `command` ani `is_text_answer`. Wtedy historia modelu
            # będzie zawierać tylko `search_feedback_to_ai` z poprzedniego kroku.

        self.logger.debug(f"Końcowa historia czatu po process_query: {json.dumps(self.chat_history_for_ai, indent=2, ensure_ascii=False)}")
        return response_to_gui


    def execute_command(self, command: str, is_interactive_sudo_prompt: bool = False) -> Dict[str, Any]:
        self.logger.info(f"Backend: Przygotowanie do wykonania: '{command}' (sudo interaktywne: {is_interactive_sudo_prompt}) w CWD: '{self.command_executor.get_current_working_dir()}'")
        command_to_run = command
        original_command_for_log = command # Zachowaj oryginalne polecenie do logowania i analizy błędów

        if SecurityValidator.requires_confirmation(command) and \
           command.strip().startswith("sudo ") and \
           is_interactive_sudo_prompt and \
           not (command.strip().startswith("echo ") and "sudo -S" in command): # Unikaj podwójnego promptu jeśli hasło idzie przez echo
            # Tylko dla trybu interaktywnego CLI
            print(f"{Fore.YELLOW}Polecenie '{command}' wymaga uprawnień sudo.{Style.RESET_ALL}")
            try:
                sudo_password = getpass.getpass(prompt=f"{Fore.YELLOW}Podaj hasło sudo dla [{os.environ.get('USER', os.getlogin())}]: {Style.RESET_ALL}")
                if not sudo_password: # Użytkownik nacisnął Enter bez wpisywania hasła
                    self.logger.warning("Nie podano hasła sudo. Anulowano wykonanie.")
                    return {"success": False, "stdout": "", "stderr": "Nie podano hasła sudo. Anulowano.", "return_code": -1, "execution_time": 0.0, "working_dir": self.command_executor.get_current_working_dir(), "command": command, "fix_suggestion": None}

                command_without_sudo = command.replace("sudo ", "", 1) # Usuń tylko pierwsze wystąpienie sudo
                escaped_password = shlex.quote(sudo_password)
                command_to_run = f"echo {escaped_password} | sudo -S -p '' {command_without_sudo}"
                self.logger.info(f"Przygotowano polecenie sudo z hasłem (CLI): echo '****' | sudo -S -p '' ...")
            except (EOFError, KeyboardInterrupt): # Ctrl+D lub Ctrl+C podczas wpisywania hasła
                self.logger.warning("Wprowadzanie hasła sudo przerwane.")
                print("\nWprowadzanie hasła przerwane.")
                return {"success": False, "stdout": "", "stderr": "Wprowadzanie hasła przerwane.", "return_code": -1, "execution_time": 0.0, "working_dir": self.command_executor.get_current_working_dir(), "command": command, "fix_suggestion": None}
            # Jeśli GUI wysyła polecenie sudo, to GUI powinno obsłużyć prompt o hasło i przekazać je przez `echo ... | sudo -S`

        self.logger.info(f"Backend: Ostateczne wykonanie: '{command_to_run}' w CWD: '{self.command_executor.get_current_working_dir()}'")
        result = self.command_executor.execute(command_to_run) # CommandExecutor zajmuje się aktualizacją CWD

        fix_suggestion_text: Optional[str] = None
        if not result.success and (result.stderr or result.return_code != 0): # Jeśli polecenie nie powiodło się
            self.logger.info(f"Backend: Polecenie '{original_command_for_log}' nie powiodło się (RC: {result.return_code}). Analizowanie błędu...")
            if self.ai_engine.is_configured:
                error_analysis_response = self.ai_engine.analyze_execution_error_and_suggest_fix(
                    original_command_for_log, result.stderr, result.return_code,
                    self.distro_info, result.working_dir, # Użyj working_dir z wyniku, bo tam faktycznie wykonano polecenie
                    language_instruction=self._get_ai_language_instruction()
                )
                if error_analysis_response.success and error_analysis_response.fix_suggestion:
                    fix_suggestion_text = error_analysis_response.fix_suggestion
                    self.logger.info(f"Backend: Sugestia naprawy AI: {fix_suggestion_text}")
                    # Dodaj sugestię do historii czatu, aby AI miało kontekst przy następnym zapytaniu
                    self._add_to_chat_history("model", f"System: Analiza błędu dla '{original_command_for_log}':\n{fix_suggestion_text}")
                elif error_analysis_response.error: # Jeśli samo AI zwróciło błąd podczas analizy
                    self.logger.error(f"Backend: Błąd analizy błędu przez AI: {error_analysis_response.error}")
                    self._add_to_chat_history("model", f"System: Nie udało się przeanalizować błędu '{original_command_for_log}'. Błąd AI: {error_analysis_response.error}")
            else:
                self.logger.warning("Backend: Silnik AI nie jest skonfigurowany, pomijanie analizy błędu.")
                self._add_to_chat_history("model", f"System: Polecenie '{original_command_for_log}' nie powiodło się. Silnik AI nie jest dostępny do analizy.")

        # Aktualizacja historii czatu o wynik wykonania polecenia
        # (nawet jeśli było to `cd`, bo chcemy widzieć zmianę katalogu w historii)
        if original_command_for_log.strip().startswith("cd ") and result.success:
            # CommandExecutor zaktualizował self.current_working_dir, a result.working_dir to potwierdza
            self._add_to_chat_history("model", f"System: Zmieniono katalog roboczy na {result.working_dir}")
        else:
            output_summary = f"Wynik wykonania '{original_command_for_log}':\nRC: {result.return_code}\n"
            if result.stdout: output_summary += f"STDOUT:\n{result.stdout.strip()}\n"
            if result.stderr: output_summary += f"STDERR:\n{result.stderr.strip()}\n"
            self._add_to_chat_history("model", output_summary.strip())


        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr,
                "return_code": result.return_code, "execution_time": result.execution_time,
                "working_dir": result.working_dir, # Zwróć katalog, w którym polecenie było wykonane
                "command": original_command_for_log, # Zwróć oryginalne polecenie
                "fix_suggestion": fix_suggestion_text}

    def interactive_mode(self):
        self.logger.info("Backend: Wejście w tryb interaktywny.")
        print(f"{Fore.GREEN}=== Asystent AI dla systemu Linux (Backend CLI) ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}Dystrybucja: {self.distro_info.get('PRETTY_NAME', 'Nieznana')}, Język AI: {self.system_language}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Wpisz 'help' po więcej informacji, 'exit' lub 'quit' aby zakończyć.{Style.RESET_ALL}")

        while True:
            try:
                current_dir_display = self.command_executor.get_current_working_dir() # Pobierz aktualny CWD z egzekutora
                # Skróć ścieżkę dla wyświetlania, jeśli jest długa
                home_dir = os.path.expanduser("~")
                if current_dir_display.startswith(home_dir):
                    display_dir_prompt = "~" + current_dir_display[len(home_dir):]
                else:
                    display_dir_prompt = current_dir_display
                if len(display_dir_prompt) > 30: # Arbitralny limit długości
                    parts = display_dir_prompt.split(os.sep)
                    if len(parts) > 3: display_dir_prompt = os.path.join("...", parts[-2], parts[-1])


                query = input(f"{Fore.GREEN}[{display_dir_prompt}]> {Style.RESET_ALL}").strip()

                if query.lower() in ["exit", "quit"]:
                    self.logger.info("Backend: Zakończenie trybu interaktywnego.")
                    break
                if query.lower() == "help":
                    self._show_help()
                    continue
                if not query:
                    continue

                command_prefix = query.split(' ', 1)[0].lower()
                is_basic_sudo_cli = command_prefix == "sudo" and len(query.split()) > 1 and query.split()[1].lower() in self.basic_command_prefixes_cli

                # Sprawdź, czy polecenie jest na liście interaktywnych LUB czy AI tak oznaczyło
                is_interactive_type_command = command_prefix in self.interactive_commands_requiring_new_terminal

                # Podstawowe polecenia wykonaj bezpośrednio (z wyjątkiem tych z force_ai_for_commands_cli)
                if (command_prefix in self.basic_command_prefixes_cli or is_basic_sudo_cli) and \
                   command_prefix not in self.force_ai_for_commands_cli and not is_interactive_type_command:
                    print(f"{Fore.YELLOW}Wykonywanie podstawowego polecenia bezpośrednio...{Style.RESET_ALL}")
                    # Dla podstawowych poleceń, is_interactive_sudo_prompt=True, aby CLI poprosiło o hasło
                    exec_result = self.execute_command(query, is_interactive_sudo_prompt=True)

                    if exec_result["success"]:
                        print(f"{Fore.GREEN}Polecenie wykonane pomyślnie.{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Błąd wykonania polecenia (kod: {exec_result['return_code']}).{Style.RESET_ALL}")

                    if exec_result.get("stdout"):
                        print(f"\n{Fore.WHITE}{exec_result['stdout'].strip()}{Style.RESET_ALL}")
                    if exec_result.get("stderr"): # stderr jest często używane do informacji, nawet przy sukcesie (np. `time`)
                        print(f"\n{Fore.RED}{exec_result['stderr'].strip()}{Style.RESET_ALL}")
                    if exec_result.get("fix_suggestion"): # Sugestia naprawy od AI
                        print(f"\n{Fore.CYAN}Sugestia AI (naprawa):{Style.RESET_ALL}\n{Fore.WHITE}{exec_result['fix_suggestion']}{Style.RESET_ALL}")

                    # Po wykonaniu podstawowego polecenia, poproś AI o wyjaśnienie
                    if self.ai_engine.is_configured:
                        print(f"{Fore.YELLOW}Pobieranie wyjaśnienia AI dla '{query}'...{Style.RESET_ALL}")
                        analysis_res = self.ai_engine.analyze_text_input_type(query, language_instruction=self._get_ai_language_instruction())
                        if analysis_res.success and analysis_res.explanation:
                            print(f"\n{Fore.CYAN}Wyjaśnienie AI:{Style.RESET_ALL}\n{Fore.WHITE}{analysis_res.explanation}{Style.RESET_ALL}")
                        elif analysis_res.error:
                             print(f"{Fore.RED}Błąd pobierania wyjaśnienia AI: {analysis_res.error}{Style.RESET_ALL}")
                        else: # success ale brak explanation
                             print(f"{Fore.YELLOW}AI nie dostarczyło wyjaśnienia.{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}Silnik AI nie jest skonfigurowany, pomijanie wyjaśnienia.{Style.RESET_ALL}")

                    print() # Dodatkowa linia dla czytelności
                    continue

                # Dla pozostałych zapytań (niejasne, złożone, lub z force_ai_for_commands_cli)
                print(f"{Fore.YELLOW}Przetwarzanie zapytania przez AI...{Style.RESET_ALL}")
                result = self.process_query(query) # result teraz zawiera 'needs_external_terminal'

                if not result["success"]:
                    if result.get("error") == "CLARIFY_REQUEST":
                        print(f"{Fore.YELLOW}AI prosi o doprecyzowanie. Spróbuj inaczej lub podaj więcej szczegółów.{Style.RESET_ALL}")
                    elif result.get("error") == "DANGEROUS_REQUEST":
                        print(f"{Fore.RED}AI zidentyfikowało zapytanie jako potencjalnie niebezpieczne i zablokowało je.{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Błąd: {result.get('error', 'Nieznany błąd')}{Style.RESET_ALL}")
                    continue

                if result.get("is_text_answer"):
                    print(f"\n{Fore.CYAN}Odpowiedź AI:{Style.RESET_ALL}\n{Fore.WHITE}{result.get('explanation', 'Brak odpowiedzi.')}{Style.RESET_ALL}")
                elif result.get("command"):
                    generated_command = result["command"]
                    print(f"\n{Fore.CYAN}Sugerowane polecenie:{Style.RESET_ALL}\n{Fore.WHITE}{generated_command}{Style.RESET_ALL}")
                    if result.get("explanation"):
                        print(f"\n{Fore.CYAN}Wyjaśnienie:{Style.RESET_ALL}\n{Fore.WHITE}{result['explanation']}{Style.RESET_ALL}")

                    # Zapytaj użytkownika o wykonanie
                    interaction_prompt_cli = f"\n{Fore.YELLOW}{result.get('suggested_button_label', 'Wykonać?')} (t/n/a-anuluj): {Style.RESET_ALL}"
                    execute_input = input(interaction_prompt_cli)

                    if execute_input.lower() in ["t", "tak", "y", "yes"]:
                        self.logger.info(f"Użytkownik CLI potwierdził wykonanie: '{generated_command}'")

                        # Sprawdzenie, czy polecenie wymaga nowego terminala (na podstawie flagi z AI)
                        if result.get("needs_external_terminal"):
                            self.logger.info(f"Polecenie '{generated_command}' wymaga nowego terminala. Próba uruchomienia...")
                            try:
                                terminal_emulator = None
                                # Kolejność preferencji dla emulatorów terminala
                                for term_cmd in ["gnome-terminal", "konsole", "xfce4-terminal", "lxterminal", "mate-terminal", "xterm"]:
                                    if shutil.which(term_cmd):
                                        terminal_emulator = term_cmd
                                        break

                                if not terminal_emulator: # Jeśli żaden z preferowanych nie jest dostępny
                                    terminal_emulator = "xterm" # Fallback do xterm, który jest często dostępny

                                # Zbuduj polecenie do wykonania w nowym terminalu
                                # Upewnij się, że CWD jest ustawiony poprawnie w nowym terminalu
                                # Dodaj pauzę na końcu, aby użytkownik mógł zobaczyć wynik
                                cmd_payload = f"cd {shlex.quote(self.command_executor.get_current_working_dir())} && {generated_command}; echo -e '\\n\\n--- Polecenie zakończone. Naciśnij Enter, aby zamknąć ten terminal. ---'; read"

                                if terminal_emulator == "gnome-terminal":
                                    # gnome-terminal -- bash -c "komenda"
                                    subprocess.Popen([terminal_emulator, "--", "bash", "-c", cmd_payload])
                                elif terminal_emulator == "konsole":
                                     # konsole -e bash -c "komenda"
                                     subprocess.Popen([terminal_emulator, "-e", "bash", "-c", cmd_payload])
                                elif terminal_emulator in ["xfce4-terminal", "lxterminal", "mate-terminal"]:
                                     # te często używają -e lub --command=
                                     subprocess.Popen([terminal_emulator, "-e", f"bash -c \"{cmd_payload.replace('\"', '\\\"')}\""]) # Wymaga dodatkowego escapowania dla niektórych
                                else: # xterm i inne, które mogą używać -e
                                    subprocess.Popen([terminal_emulator, "-e", f"bash -c \"{cmd_payload.replace('\"', '\\\"')}\""])


                                print(f"{Fore.GREEN}Polecenie '{generated_command}' powinno zostać uruchomione w nowym oknie terminala.{Style.RESET_ALL}")
                                print(f"{Fore.CYAN}Możesz kontynuować pracę w tym oknie asystenta.{Style.RESET_ALL}")
                                self._add_to_chat_history("model", f"System: Uruchomiono '{generated_command}' w nowym terminalu.")
                            except Exception as e_term:
                                print(f"{Fore.RED}Nie udało się automatycznie otworzyć nowego terminala dla '{generated_command}'. Błąd: {e_term}{Style.RESET_ALL}")
                                print(f"{Fore.YELLOW}Proszę ręcznie otworzyć terminal i wykonać: cd {self.command_executor.get_current_working_dir()} && {generated_command}{Style.RESET_ALL}")
                                self._add_to_chat_history("model", f"System: Nie udało się uruchomić '{generated_command}' w nowym terminalu. Błąd: {e_term}")

                        else: # Normalne wykonanie przez CommandExecutor
                            print(f"{Fore.YELLOW}Wykonywanie...{Style.RESET_ALL}")
                            # Dla poleceń AI, is_interactive_sudo_prompt=True, aby CLI poprosiło o hasło jeśli jest 'sudo'
                            exec_result = self.execute_command(generated_command, is_interactive_sudo_prompt=True)
                            if exec_result["success"]:
                                print(f"{Fore.GREEN}Polecenie wykonane.{Style.RESET_ALL}")
                            else:
                                print(f"{Fore.RED}Błąd wykonania (kod: {exec_result['return_code']}){Style.RESET_ALL}")

                            if exec_result.get("stdout"):
                                print(f"\n{Fore.WHITE}{exec_result['stdout'].strip()}{Style.RESET_ALL}")
                            if exec_result.get("stderr"):
                                print(f"\n{Fore.RED}{exec_result['stderr'].strip()}{Style.RESET_ALL}")
                            if exec_result.get("fix_suggestion"): # Sugestia naprawy od AI
                                print(f"\n{Fore.CYAN}Sugestia AI:{Style.RESET_ALL}\n{Fore.WHITE}{exec_result['fix_suggestion']}{Style.RESET_ALL}")
                else: # Sukces, ale brak polecenia i nie jest to odpowiedź tekstowa - nietypowe
                    print(f"{Fore.RED}Błąd: AI nie zwróciło ani polecenia, ani odpowiedzi tekstowej.{Style.RESET_ALL}")
                print() # Dodatkowa linia dla czytelności
            except KeyboardInterrupt:
                print("\nPrzerwano.")
                break
            except Exception as e:
                self.logger.critical(f"Nieoczekiwany błąd w pętli interaktywnej CLI: {e}", exc_info=True)
                print(f"{Fore.RED}Krytyczny błąd: {e}. Zobacz {LOG_FILE} po szczegóły.{Style.RESET_ALL}")
                traceback.print_exc() # Dodatkowy wydruk na stderr

    def _show_help(self):
        print(f"\n{Fore.CYAN}=== Pomoc asystenta AI dla systemu Linux (Backend CLI) ==={Style.RESET_ALL}")
        print("Asystent przetwarza zapytania w języku naturalnym i generuje polecenia.")
        print("Podstawowe polecenia Linuksa (np. ls, cd, pwd) są wykonywane bezpośrednio, a następnie AI dostarcza wyjaśnienie.")
        print("Bardziej złożone zapytania lub te dotyczące modyfikacji systemu są analizowane przez AI.")
        print(f"\n{Fore.CYAN}Przykłady zapytań do AI:{Style.RESET_ALL}")
        print("- Pokaż wszystkie pliki w katalogu domowym")
        print("- Zainstaluj firefox")
        print("- Jakie mam urządzenia sieciowe?")
        print("- Jak sprawdzić zużycie dysku?")
        print("- Czy są tu jakieś pliki .log?")
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

    logger_main_cli.info(f"Backend uruchomiony z argumentami: query='{args.query}', execute={args.execute}, json={args.json}, working_dir='{args.working_dir}'")

    assistant = LinuxAIAssistant(initial_working_dir=args.working_dir)

    if not assistant.ai_engine.is_configured:
        # Sprawdź, czy można bezpiecznie uruchomić polecenie offline
        # (np. podstawowe polecenie, nie niebezpieczne, nie interaktywne)
        can_run_offline_safely = False
        if args.query and args.execute: # Tylko jeśli GUI prosi o wykonanie znanego polecenia
            command_prefix = args.query.split(' ', 1)[0].lower()
            is_basic_sudo_cli = command_prefix == "sudo" and len(args.query.split()) > 1 and args.query.split()[1].lower() in assistant.basic_command_prefixes_cli
            if (command_prefix in assistant.basic_command_prefixes_cli or is_basic_sudo_cli) and \
               command_prefix not in assistant.force_ai_for_commands_cli and \
               not SecurityValidator.is_dangerous(args.query) and \
               command_prefix not in assistant.interactive_commands_requiring_new_terminal: # Dodatkowe sprawdzenie
                can_run_offline_safely = True

        if not can_run_offline_safely:
            error_msg_no_ai = "Krytyczny błąd: Silnik AI (GeminiIntegration) nie został poprawnie skonfigurowany. Sprawdź klucz API GOOGLE_API_KEY i logi."
            logger_main_cli.error(error_msg_no_ai)
            if args.json:
                print(json.dumps({"success": False, "error": error_msg_no_ai, "is_text_answer": True, "explanation": error_msg_no_ai, "needs_external_terminal": False}))
            else:
                print(f"{Fore.RED}{error_msg_no_ai}{Style.RESET_ALL}")
            # Jeśli było zapytanie z GUI, zakończ z błędem, aby GUI wiedziało
            if args.query: sys.exit(1)
            # Jeśli to tryb interaktywny, po prostu poinformuj i kontynuuj, może użytkownik chce tylko 'help' lub 'exit'
            # Jednak w tym punkcie `args.query` jest fałszywe, więc nie dojdzie do `sys.exit(1)` dla trybu interaktywnego

    if args.query: # Jeśli podano zapytanie jako argument (zwykle z GUI)
        if args.execute: # GUI prosi o wykonanie polecenia (zwykle podstawowego lub potwierdzonego)
            logger_main_cli.info(f"Backend: Tryb --execute dla polecenia: '{args.query}'")
            # Sprawdzenie, czy polecenie jest na liście interaktywnych (które backend nie powinien próbować wykonać bezpośrednio dla GUI)
            cmd_prefix_exec = args.query.split(' ',1)[0].lower()
            if cmd_prefix_exec in assistant.interactive_commands_requiring_new_terminal:
                logger_main_cli.warning(f"Backend: Polecenie '{args.query}' w trybie --execute jest interaktywne i nie może być wykonane bezpośrednio przez backend w ten sposób. Zwracam błąd.")
                # Zwróć informację do GUI, że to polecenie wymaga nowego terminala
                output = {
                    "success": False, # Niepowodzenie wykonania przez backend
                    "error": f"Polecenie '{args.query}' jest interaktywne i powinno być uruchomione w nowym terminalu przez GUI.",
                    "is_text_answer": False,
                    "needs_external_terminal": True, # Kluczowa flaga dla GUI
                    "command": args.query, # Zwróć oryginalne polecenie
                    "stdout": "", "stderr": "", "return_code": -1, "execution_time": 0.0,
                    "working_dir": assistant.command_executor.get_current_working_dir()
                }
                if args.json: print(json.dumps(output))
                else: print(f"{Fore.RED}{output['error']}{Style.RESET_ALL}") # Dla debugowania CLI
            else:
                # Dla --execute, is_interactive_sudo_prompt=False, bo GUI powinno obsłużyć hasło i wysłać je przez `echo`
                exec_result = assistant.execute_command(args.query, is_interactive_sudo_prompt=False)
                if args.json:
                    print(json.dumps(exec_result))
                else: # Logika dla CLI, jeśli nie JSON (głównie do debugowania)
                    print(f"Polecenie: {exec_result.get('command')}")
                    if exec_result.get("success"): print(f"{Fore.GREEN}Wykonano pomyślnie.{Style.RESET_ALL}")
                    else: print(f"{Fore.RED}Błąd wykonania: {exec_result.get('stderr') or exec_result.get('error')}{Style.RESET_ALL}")
                    if exec_result.get("stdout"): print(f"Stdout:\n{exec_result.get('stdout')}")
        else: # To ścieżka dla GUI do przetwarzania przez AI (--query jest, ale nie --execute)
            result_process = assistant.process_query(args.query)
            if args.json:
                print(json.dumps(result_process))
            else: # Logika dla CLI, jeśli nie JSON (głównie do debugowania)
                if result_process.get("success"):
                    if result_process.get("is_text_answer"):
                        print(f"Odpowiedź AI: {result_process.get('explanation')}")
                    elif result_process.get("command"):
                        print(f"Sugerowane polecenie: {result_process.get('command')}")
                        if result_process.get("explanation"): print(f"Wyjaśnienie: {result_process['explanation']}")
                        if result_process.get("needs_external_terminal"): print(f"{Fore.YELLOW}To polecenie powinno być uruchomione w nowym terminalu.{Style.RESET_ALL}")
                        elif result_process.get("suggested_button_label"):
                            print(f"Sugestia interakcji (etykieta przycisku): {result_process['suggested_button_label']}")
                            print(f"Sugerowana odpowiedź tekstowa: {result_process.get('suggested_interaction_input')}")
                    else: # success, ale brak polecenia/odpowiedzi
                        print(f"Błąd: AI zwróciło sukces, ale bez polecenia/odpowiedzi.")
                else: # not success
                    if result_process.get("error") == "CLARIFY_REQUEST": print(f"{Fore.YELLOW}AI prosi o doprecyzowanie.{Style.RESET_ALL}")
                    elif result_process.get("error") == "DANGEROUS_REQUEST": print(f"{Fore.RED}AI zidentyfikowało zapytanie jako niebezpieczne.{Style.RESET_ALL}")
                    else: print(f"Błąd: {result_process.get('error')}")
    else: # Tryb interaktywny CLI (jeśli nie podano --query)
        assistant.interactive_mode()

if __name__ == "__main__":
    try:
        main()
    except Exception as e_global:
        # Złap wszystkie nieobsłużone wyjątki na najwyższym poziomie
        logger_main_cli.critical(f"Nieobsłużony wyjątek na najwyższym poziomie: {e_global}", exc_info=True)
        # Wydrukuj również na stderr, jeśli to możliwe, dla trybu CLI
        print(f"{Fore.RED}Krytyczny błąd aplikacji: {e_global}. Sprawdź {LOG_FILE} po szczegóły.{Style.RESET_ALL}")
        traceback.print_exc() # Wyświetl pełny traceback na stderr
        sys.exit(1) # Zakończ z kodem błędu
