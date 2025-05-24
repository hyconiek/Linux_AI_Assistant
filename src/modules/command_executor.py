# Plik: src/modules/command_executor.py

import os
import subprocess
import shlex
import logging
import re
# import signal # Nie jest aktywnie używany, można usunąć, jeśli nie ma planów implementacji kill_process
from typing import Dict, List, Tuple, Optional, Any # Union nie jest tu potrzebny
from dataclasses import dataclass
import time
import sys # Nie jest bezpośrednio używany w tej klasie, ale może być w bloku __main__

# Logger będzie używał konfiguracji z modułu nadrzędnego (np. backend_cli.py)
logger = logging.getLogger("command_executor")

@dataclass
class CommandResult:
    success: bool
    stdout: str
    stderr: str
    return_code: int
    command: str # Oryginalne polecenie, jakie otrzymał executor
    execution_time: float
    working_dir: str# Katalog, który JEST bieżącym katalogiem roboczym PO wykonaniu polecenia

# SecurityValidator i DistributionDetector pozostają bez zmian z poprzedniej wersji

class SecurityValidator:
    DANGEROUS_PATTERNS = [
        r"rm\s+(-[rfRPorfL]+\s+)?(\/|\~|\.\.)",
        r">\s*(\/etc\/passwd|\/etc\/shadow)",
        r"mkfs", r"dd\s+.*of=/dev/[sh]d[a-z]",
        r":\(\)\s*{\s*:\s*\|\s*:\s*&\s*}\s*;", # Fork bomb
        r"chmod\s+-[R]*\s+(777|666|444)\s+\/", # Niebezpieczne uprawnienia na roocie
        r"(wget|curl)\s+.*\s*\|\s*(bash|sh)"  # Pobieranie i wykonywanie skryptów
    ]
    CONFIRMATION_REQUIRED = [ # Polecenia często wymagające sudo lub ostrożności
        r"sudo", r"su\s", r"passwd", r"shutdown", r"reboot", r"halt", r"poweroff",
        r"mkfs", r"fdisk", r"parted", r"dd", r"shred", r"useradd", r"usermod", r"userdel",
        r"groupadd", r"groupmod", r"groupdel", r"chown", r"chgrp"
    ]

    @classmethod
    def is_dangerous(cls, command: str) -> bool:
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                logger.warning(f"Dangerous pattern '{pattern}' matched for command: '{command}'")
                return True
        return False

    @classmethod
    def requires_confirmation(cls, command: str) -> bool:
        for pattern in cls.CONFIRMATION_REQUIRED:
            if re.search(pattern, command):
                return True
        return False

    @classmethod
    def validate(cls, command: str) -> Tuple[bool, str]:
        if cls.is_dangerous(command):
            return False, f"Polecenie '{command}' zostało zidentyfikowane jako potencjalnie niebezpieczne i zablokowane."
        # Walidacja potwierdzenia jest teraz logiką interfejsu użytkownika, a nie CommandExecutor.
        return True, ""

class DistributionDetector:
    @staticmethod
    def detect_distribution() -> Dict[str, str]:
        result: Dict[str, str] = {}
        # Użyj osobnej, tymczasowej instancji CommandExecutor do wykrywania, aby nie wpływać na stan.
        # Dajemy krótki timeout, bo te polecenia powinny być szybkie.
        try:
            temp_executor_os = CommandExecutor(timeout=5)
            os_release_cmd_res = temp_executor_os.execute("cat /etc/os-release")
            if os_release_cmd_res.success:
                for line in os_release_cmd_res.stdout.splitlines():
                    if "=" in line:
                        key, value = line.split("=", 1)
                        result[key.strip()] = value.strip().strip('"')
        except Exception as e:
            logger.error(f"Błąd przy odczycie /etc/os-release w DistributionDetector: {e}")

        try:
            temp_executor_lsb = CommandExecutor(timeout=5)
            lsb_output_cmd_res = temp_executor_lsb.execute("lsb_release -a")
            if lsb_output_cmd_res.success:
                for line in lsb_output_cmd_res.stdout.splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        result[f"LSB_{key.strip().replace(' ', '_')}"] = value.strip()
        except Exception:  # lsb_release może nie być zainstalowane
            pass

        try:
            temp_executor_uname = CommandExecutor(timeout=5)
            uname_cmd_res = temp_executor_uname.execute("uname -r") # -r dla samej wersji kernela
            if uname_cmd_res.success:
                result["KERNEL"] = uname_cmd_res.stdout.strip()
        except Exception:
            pass

        package_managers = {"apt": "apt", "dnf": "dnf", "yum": "yum", "pacman": "pacman", "zypper": "zypper"}
        temp_executor_pm = CommandExecutor(timeout=5)
        for pm_name in package_managers.keys():
            check_exists_cmd = f"command -v {pm_name}" # command -v jest bardziej POSIX-owe niż which
            if temp_executor_pm.execute(check_exists_cmd).success:
                result["PACKAGE_MANAGER"] = pm_name
                break
        return result


class CommandExecutor:
    def __init__(self, timeout: int = 120, max_output_size: int = 1024 * 1024):
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.history: List[CommandResult] = []
        self.current_working_dir = os.path.abspath(os.getcwd())
        self.logger = logging.getLogger("command_executor")
        self.logger.info(f"CommandExecutor initialized. Initial CWD: {self.current_working_dir}")

    def execute(self, command: str, working_dir_override: Optional[str] = None) -> CommandResult:
        effective_initial_cwd = os.path.abspath(working_dir_override if working_dir_override else self.current_working_dir)
        # self.logger.info(f"!!! TEST EXECUTE: command='{command}', effective_initial_cwd='{effective_initial_cwd}'")
        self.logger.debug(f"Executing command='{command}' in effective_cwd='{effective_initial_cwd}'")


        is_safe, safety_message = SecurityValidator.validate(command)
        if not is_safe:
            return CommandResult(False, "", safety_message, -1, command, 0.0, effective_initial_cwd)

        start_time = time.time()

        # Sanitize command if it's a complex cd for Popen to avoid shell errors with complex paths
        # However, for subprocess.run with shell=True, direct command is usually fine.
        # For cd, the special handling below is more important.

        process = subprocess.run(
            command, shell=True, cwd=effective_initial_cwd,
            env=os.environ.copy(), capture_output=True, text=True,
            timeout=self.timeout, check=False, executable='/bin/bash'
        )
        execution_time = time.time() - start_time
        stdout = process.stdout[:self.max_output_size] if process.stdout else ""
        stderr = process.stderr[:self.max_output_size] if process.stderr else ""
        rc = process.returncode

        new_cwd_for_executor = effective_initial_cwd
        # Check if the command was 'cd' and if it succeeded
        # Use regex to be more robust about "cd" and "cd "
        if re.match(r"^\s*cd(\s+.*|$)", command.strip()) and rc == 0:
            # If 'cd' was part of a compound command like 'cd /tmp && pwd',
            # we need to determine the final CWD if the whole compound command succeeded.
            # The most reliable way for compound commands is to ask the shell.
            # For simple 'cd <dir>', our existing logic is fine.

            is_simple_cd = "&&" not in command and "|" not in command and ";" not in command

            if is_simple_cd:
                parts = shlex.split(command.strip()) # shlex.split correctly handles "cd" and "cd /some/path"
                target_dir_part = "~" # Default to home if just "cd"
                if len(parts) > 1:
                    target_dir_part = parts[1]

                expanded_target = os.path.expanduser(target_dir_part)

                # Determine absolute path: if target is absolute, use it; otherwise, join with CWD
                if os.path.isabs(expanded_target):
                    prospective_abs_path = expanded_target
                else:
                    prospective_abs_path = os.path.join(effective_initial_cwd, expanded_target)

                # Normalize the path (e.g., resolve '..')
                normalized_abs_path = os.path.normpath(prospective_abs_path)

                if os.path.isdir(normalized_abs_path):
                    new_cwd_for_executor = normalized_abs_path
                    self.current_working_dir = new_cwd_for_executor # Update executor's state
                    # For simple 'cd', stdout might be empty. Provide a confirmation.
                    if not stdout.strip(): # only if subprocess did not produce output
                         stdout = f"Changed directory to {new_cwd_for_executor}"
                else:
                    # This case should ideally be caught by rc != 0, but as a fallback:
                    self.logger.warning(f"'cd' command to '{target_dir_part}' resulted in non-directory path '{normalized_abs_path}' despite rc=0. CWD not changed by special 'cd' logic.")
            else: # Compound command potentially involving 'cd'
                # The most robust way to get the CWD after a compound command is to ask the shell
                # by appending '; pwd' to the command IF it succeeded.
                # We assume 'pwd' is available and safe.
                # This is run in a new subprocess, so it doesn't affect the current one's Popen CWD.
                if rc == 0: # Only if the compound command was successful
                    try:
                        pwd_check_process = subprocess.run(
                            f"({command}) && pwd", # Group original command to ensure pwd runs in the same subshell context
                            shell=True, cwd=effective_initial_cwd,
                            capture_output=True, text=True, timeout=2, check=True, executable='/bin/bash'
                        )
                        final_cwd_from_pwd = pwd_check_process.stdout.strip()
                        if os.path.isdir(final_cwd_from_pwd):
                            new_cwd_for_executor = final_cwd_from_pwd
                            self.current_working_dir = new_cwd_for_executor
                            self.logger.info(f"Compound command with 'cd' succeeded. New CWD from 'pwd': {new_cwd_for_executor}")
                        else:
                            self.logger.warning(f"Compound command with 'cd' succeeded, but 'pwd' check yielded non-dir: {final_cwd_from_pwd}")
                    except Exception as e_pwd:
                        self.logger.error(f"Error trying to determine CWD after compound command '{command}': {e_pwd}")
                        # Fallback to not changing CWD if pwd check fails
                        new_cwd_for_executor = effective_initial_cwd


        res = CommandResult((rc == 0), stdout, stderr, rc, command, execution_time, new_cwd_for_executor)
        self.logger.debug(f"Execution Result: Success={res.success}, RC={rc}, Result CWD: {res.working_dir}, Executor CWD after exec: {self.current_working_dir}")
        if self.current_working_dir != new_cwd_for_executor and rc == 0 and re.match(r"^\s*cd(\s+.*|$)", command.strip()):
             self.logger.warning(f"Mismatch: Executor CWD is {self.current_working_dir} but result CWD is {new_cwd_for_executor} for a 'cd' command that succeeded. This might indicate an issue in CWD update logic for compound commands if it wasn't updated by '&& pwd'.")


        return res

    def get_current_working_dir(self) -> str:
        return self.current_working_dir

    def set_current_working_dir(self, directory: str) -> bool:
        normalized_dir = os.path.normpath(os.path.abspath(directory))
        if os.path.isdir(normalized_dir):
            if self.current_working_dir != normalized_dir:
                self.logger.info(f"CommandExecutor: Working directory explicitly changing from '{self.current_working_dir}' to '{normalized_dir}'")
                self.current_working_dir = normalized_dir
            else:
                self.logger.info(f"CommandExecutor: Working directory already set to '{normalized_dir}'. No change.")
            return True
        self.logger.warning(f"CommandExecutor: Failed to set working directory to non-existent path: {normalized_dir}")
        return False

    def execute_interactive(self, command: str, working_dir_override: Optional[str] = None,
                           env: Optional[Dict[str, str]] = None) -> subprocess.Popen:
        effective_working_dir = os.path.abspath(working_dir_override if working_dir_override else self.current_working_dir)
        is_safe, message = SecurityValidator.validate(command)
        if not is_safe:
            self.logger.warning(f"Próba wykonania niebezpiecznego polecenia w trybie interaktywnym: {command}")
            raise ValueError(message)

        # Dla trybu interaktywnego, zmiana katalogu musi być częścią polecenia
        safe_cwd_for_shell_cd = shlex.quote(effective_working_dir)
        interactive_command_with_cd = f"cd {safe_cwd_for_shell_cd} && ({command})"

        execution_env = os.environ.copy()
        if env: execution_env.update(env)
        try:
            self.logger.info(f"Uruchamianie procesu interaktywnego: '{interactive_command_with_cd}' (original CWD for Popen: {os.getcwd()})")
            process = subprocess.Popen(
                interactive_command_with_cd, shell=True, cwd=None, # cwd=None, bo `cd` jest w poleceniu
                env=execution_env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, bufsize=1, executable='/bin/bash'
            )
            return process
        except Exception as e:
            self.logger.error(f"Błąd podczas uruchamiania procesu interaktywnego: {command}, {str(e)}", exc_info=True)
            raise

    def kill_process(self, process: subprocess.Popen) -> bool:
        # ... (bez zmian z poprzedniej poprawnej wersji)
        try:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    if process.poll() is None: process.kill(); self.logger.info(f"Proces (PID: {process.pid}) został zabity (kill).")
                else: self.logger.info(f"Proces (PID: {process.pid}) został zakończony (terminate).")
            else: self.logger.info(f"Proces (PID: {process.pid}) był już zakończony.")
            return True
        except Exception as e: self.logger.error(f"Błąd zabijania procesu (PID: {process.pid if process else 'N/A'}): {e}"); return False


    def get_history(self, limit: int = 10) -> List[CommandResult]:
        return self.history[-limit:]


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
    logger_main = logging.getLogger("command_executor_main_tests")
    logger_main.info("Starting CommandExecutor __main__ tests...")

    executor = CommandExecutor(timeout=10)
    initial_dir = executor.get_current_working_dir()
    logger_main.info(f"Initial PWD from executor: {initial_dir}")

    print("\n--- Test: Proste cd ---")
    res_cd_tmp = executor.execute("cd /tmp")
    print(f"CD /tmp result: Success={res_cd_tmp.success}, RC={res_cd_tmp.return_code}, Executor CWD: {executor.get_current_working_dir()}, Result CWD: {res_cd_tmp.working_dir}, Stdout: '{res_cd_tmp.stdout}'")
    assert executor.get_current_working_dir() == "/tmp", f"Executor CWD should be /tmp, is {executor.get_current_working_dir()}"
    assert res_cd_tmp.working_dir == "/tmp", f"Result CWD should be /tmp, is {res_cd_tmp.working_dir}"
    assert "Changed directory to /tmp" in res_cd_tmp.stdout

    print("\n--- Test: ls w nowym katalogu (/tmp) ---")
    res_ls_tmp = executor.execute("ls -d .")
    print(f"LS in /tmp result: Success={res_ls_tmp.success}, Stdout: '{res_ls_tmp.stdout.strip()}', Executor CWD: {executor.get_current_working_dir()}, Result CWD: {res_ls_tmp.working_dir}")
    assert executor.get_current_working_dir() == "/tmp" # Powinno pozostać /tmp
    assert res_ls_tmp.working_dir == "/tmp" # Powinno być wykonane w /tmp
    assert res_ls_tmp.stdout.strip() == "."

    print("\n--- Test: Złożone polecenie ze zmianą katalogu (cd / && pwd) ---")
    res_cd_root_pwd = executor.execute("cd / && pwd")
    print(f"cd / && pwd result: Success={res_cd_root_pwd.success}, Stdout: '{res_cd_root_pwd.stdout.strip()}', Executor CWD: {executor.get_current_working_dir()}, Result CWD: {res_cd_root_pwd.working_dir}")
    if res_cd_root_pwd.success:
        assert executor.get_current_working_dir() == "/", f"Executor CWD should be /, is {executor.get_current_working_dir()}"
        assert res_cd_root_pwd.working_dir == "/", f"Result CWD should be /, is {res_cd_root_pwd.working_dir}"
        assert res_cd_root_pwd.stdout.strip() == "/", f"Stdout should be /, is {res_cd_root_pwd.stdout.strip()}"
    else: print(f"Stderr for cd / && pwd: {res_cd_root_pwd.stderr}")

    print("\n--- Test: Złożone polecenie ze zmianą katalogu i listowaniem (cd /usr && ls -d lib) ---")
    res_cd_usr_ls = executor.execute("cd /usr && ls -d lib")
    print(f"cd /usr && ls -d lib result: Success={res_cd_usr_ls.success}, Stdout: '{res_cd_usr_ls.stdout.strip()}', Executor CWD: {executor.get_current_working_dir()}, Result CWD: {res_cd_usr_ls.working_dir}")
    if res_cd_usr_ls.success:
        assert executor.get_current_working_dir() == "/usr", f"Executor CWD should be /usr, is {executor.get_current_working_dir()}"
        assert res_cd_usr_ls.working_dir == "/usr", f"Result CWD should be /usr, is {res_cd_usr_ls.working_dir}"
        assert "lib" in res_cd_usr_ls.stdout.strip()
    else: print(f"Stderr for cd /usr && ls -d lib: {res_cd_usr_ls.stderr}")

    print(f"\n--- Test: Powrót do katalogu początkowego: {initial_dir} przez PROSTE cd ---")
    res_cd_back_simple = executor.execute(f"cd {shlex.quote(initial_dir)}")
    print(f"CD back simple to '{initial_dir}' result: Success={res_cd_back_simple.success}, Stdout: '{res_cd_back_simple.stdout.strip()}', Executor CWD: {executor.get_current_working_dir()}, Result CWD: {res_cd_back_simple.working_dir}")
    assert executor.get_current_working_dir() == initial_dir
    assert res_cd_back_simple.working_dir == initial_dir
    assert f"Changed directory to {initial_dir}" in res_cd_back_simple.stdout

    logger_main.info("CommandExecutor __main__ tests finished.")
