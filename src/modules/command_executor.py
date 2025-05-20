#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Moduł wykonywania poleceń terminalowych dla asystenta AI dla systemu Linux.
Odpowiada za bezpieczne wykonywanie poleceń, obsługę błędów i zarządzanie uprawnieniami.
"""

import os
import subprocess
import shlex
import logging
import re
import signal
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import time

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/linux_ai_assistant.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("command_executor")

@dataclass
class CommandResult:
    """Klasa przechowująca wynik wykonania polecenia."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    command: str
    execution_time: float


class SecurityValidator:
    """Klasa odpowiedzialna za walidację bezpieczeństwa poleceń."""
    
    # Lista wzorców potencjalnie niebezpiecznych poleceń
    DANGEROUS_PATTERNS = [
        r"rm\s+(-[rf]+\s+)?(\/|\~|\.\.)",  # Usuwanie ważnych katalogów
        r">\s*(\/etc\/passwd|\/etc\/shadow)",  # Modyfikacja plików systemowych
        r"mkfs",                           # Formatowanie dysków
        r"dd\s+.*of=/dev/[sh]d[a-z]",      # Nadpisywanie dysków
        r":\(\)\s*{\s*:\s*\|\s*:\s*&\s*}\s*;",  # Fork bomb
        r"chmod\s+-[R]*\s+777\s+\/",       # Niebezpieczne uprawnienia
        r"wget\s+.*\s*\|\s*bash",          # Wykonywanie skryptów z internetu
        r"curl\s+.*\s*\|\s*bash",
    ]
    
    # Lista poleceń wymagających potwierdzenia
    CONFIRMATION_REQUIRED = [
        r"sudo",
        r"su\s",
        r"passwd",
        r"shutdown",
        r"reboot",
        r"halt",
        r"poweroff",
        r"mkfs",
        r"fdisk",
        r"parted",
        r"dd",
        r"shred",
    ]
    
    @classmethod
    def is_dangerous(cls, command: str) -> bool:
        """Sprawdza, czy polecenie jest potencjalnie niebezpieczne."""
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                return True
        return False
    
    @classmethod
    def requires_confirmation(cls, command: str) -> bool:
        """Sprawdza, czy polecenie wymaga potwierdzenia."""
        for pattern in cls.CONFIRMATION_REQUIRED:
            if re.search(pattern, command):
                return True
        return False
    
    @classmethod
    def validate(cls, command: str) -> Tuple[bool, str]:
        """
        Waliduje polecenie pod kątem bezpieczeństwa.
        
        Args:
            command: Polecenie do walidacji
            
        Returns:
            Tuple[bool, str]: (czy_bezpieczne, komunikat)
        """
        if cls.is_dangerous(command):
            return False, f"Polecenie '{command}' zostało zidentyfikowane jako potencjalnie niebezpieczne."
        
        if cls.requires_confirmation(command):
            return True, f"Polecenie '{command}' wymaga potwierdzenia przed wykonaniem."
        
        return True, ""


class CommandExecutor:
    """Klasa odpowiedzialna za wykonywanie poleceń terminalowych."""
    
    def __init__(self, timeout: int = 30, max_output_size: int = 1024 * 1024):
        """
        Inicjalizacja wykonawcy poleceń.
        
        Args:
            timeout: Maksymalny czas wykonania polecenia w sekundach
            max_output_size: Maksymalny rozmiar wyjścia w bajtach
        """
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.history: List[CommandResult] = []
    
    def execute(self, command: str, working_dir: str = None, 
                env: Dict[str, str] = None, capture_output: bool = True,
                require_confirmation: bool = True) -> CommandResult:
        """
        Wykonuje polecenie terminalowe.
        
        Args:
            command: Polecenie do wykonania
            working_dir: Katalog roboczy
            env: Zmienne środowiskowe
            capture_output: Czy przechwytywać wyjście
            require_confirmation: Czy wymagać potwierdzenia dla niebezpiecznych poleceń
            
        Returns:
            CommandResult: Wynik wykonania polecenia
        """
        # Walidacja bezpieczeństwa
        is_safe, message = SecurityValidator.validate(command)
        
        if not is_safe:
            logger.warning(f"Próba wykonania niebezpiecznego polecenia: {command}")
            return CommandResult(
                success=False,
                stdout="",
                stderr=message,
                return_code=-1,
                command=command,
                execution_time=0.0
            )
        
        if require_confirmation and SecurityValidator.requires_confirmation(command):
            logger.info(f"Polecenie wymaga potwierdzenia: {command}")
            # W rzeczywistej implementacji tutaj byłoby zapytanie o potwierdzenie
            # Dla celów demonstracyjnych zakładamy, że potwierdzenie zostało udzielone
        
        # Przygotowanie środowiska
        execution_env = os.environ.copy()
        if env:
            execution_env.update(env)
        
        try:
            # Pomiar czasu wykonania
            start_time = time.time()
            
            # Wykonanie polecenia
            if capture_output:
                process = subprocess.run(
                    command,
                    shell=True,
                    cwd=working_dir,
                    env=execution_env,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                stdout = process.stdout[:self.max_output_size]
                stderr = process.stderr[:self.max_output_size]
            else:
                process = subprocess.run(
                    command,
                    shell=True,
                    cwd=working_dir,
                    env=execution_env,
                    timeout=self.timeout
                )
                stdout = ""
                stderr = ""
            
            execution_time = time.time() - start_time
            
            # Tworzenie wyniku
            result = CommandResult(
                success=(process.returncode == 0),
                stdout=stdout,
                stderr=stderr,
                return_code=process.returncode,
                command=command,
                execution_time=execution_time
            )
            
            # Zapisanie do historii
            self.history.append(result)
            
            # Logowanie
            if result.success:
                logger.info(f"Polecenie wykonane pomyślnie: {command}")
            else:
                logger.warning(f"Polecenie zakończone błędem: {command}, kod: {result.return_code}")
            
            return result
            
        except subprocess.TimeoutExpired:
            logger.error(f"Przekroczono limit czasu dla polecenia: {command}")
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Przekroczono limit czasu ({self.timeout}s)",
                return_code=-1,
                command=command,
                execution_time=self.timeout
            )
        except Exception as e:
            logger.error(f"Błąd podczas wykonywania polecenia: {command}, {str(e)}")
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Błąd wykonania: {str(e)}",
                return_code=-1,
                command=command,
                execution_time=time.time() - start_time
            )
    
    def execute_interactive(self, command: str, working_dir: str = None, 
                           env: Dict[str, str] = None) -> subprocess.Popen:
        """
        Uruchamia polecenie w trybie interaktywnym.
        
        Args:
            command: Polecenie do wykonania
            working_dir: Katalog roboczy
            env: Zmienne środowiskowe
            
        Returns:
            subprocess.Popen: Obiekt procesu
        """
        # Walidacja bezpieczeństwa
        is_safe, message = SecurityValidator.validate(command)
        
        if not is_safe:
            logger.warning(f"Próba wykonania niebezpiecznego polecenia: {command}")
            raise ValueError(message)
        
        # Przygotowanie środowiska
        execution_env = os.environ.copy()
        if env:
            execution_env.update(env)
        
        try:
            # Uruchomienie procesu interaktywnego
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=working_dir,
                env=execution_env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            logger.info(f"Uruchomiono proces interaktywny: {command}")
            return process
            
        except Exception as e:
            logger.error(f"Błąd podczas uruchamiania procesu interaktywnego: {command}, {str(e)}")
            raise
    
    def kill_process(self, process: subprocess.Popen) -> bool:
        """
        Zabija proces.
        
        Args:
            process: Proces do zabicia
            
        Returns:
            bool: Czy operacja się powiodła
        """
        try:
            process.terminate()
            time.sleep(0.5)
            if process.poll() is None:  # Proces nadal działa
                process.kill()
            
            logger.info(f"Proces zakończony, PID: {process.pid}")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas zabijania procesu: {str(e)}")
            return False
    
    def get_history(self, limit: int = 10) -> List[CommandResult]:
        """
        Zwraca historię wykonanych poleceń.
        
        Args:
            limit: Maksymalna liczba wyników
            
        Returns:
            List[CommandResult]: Historia poleceń
        """
        return self.history[-limit:]


class DistributionDetector:
    """Klasa do wykrywania dystrybucji Linuxa."""
    
    @staticmethod
    def detect_distribution() -> Dict[str, str]:
        """
        Wykrywa dystrybucję Linuxa.
        
        Returns:
            Dict[str, str]: Informacje o dystrybucji
        """
        result = {}
        
        # Próba odczytu /etc/os-release
        try:
            executor = CommandExecutor()
            os_release = executor.execute("cat /etc/os-release")
            
            if os_release.success:
                for line in os_release.stdout.splitlines():
                    if "=" in line:
                        key, value = line.split("=", 1)
                        result[key] = value.strip('"')
        except Exception as e:
            logger.error(f"Błąd podczas wykrywania dystrybucji: {str(e)}")
        
        # Próba użycia lsb_release
        try:
            lsb_release = executor.execute("lsb_release -a")
            
            if lsb_release.success:
                for line in lsb_release.stdout.splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        result[f"LSB_{key.strip()}"] = value.strip()
        except Exception:
            pass
        
        # Informacje o jądrze
        try:
            uname = executor.execute("uname -a")
            
            if uname.success:
                result["KERNEL"] = uname.stdout.strip()
        except Exception:
            pass
        
        # Wykrywanie menedżera pakietów
        package_managers = {
            "apt": "apt --version",
            "dnf": "dnf --version",
            "yum": "yum --version",
            "pacman": "pacman --version",
            "zypper": "zypper --version"
        }
        
        for pm_name, pm_command in package_managers.items():
            try:
                pm_check = executor.execute(pm_command)
                if pm_check.success:
                    result["PACKAGE_MANAGER"] = pm_name
                    break
            except Exception:
                pass
        
        return result


# Przykład użycia
if __name__ == "__main__":
    # Wykrywanie dystrybucji
    detector = DistributionDetector()
    distro_info = detector.detect_distribution()
    print("Wykryta dystrybucja:")
    for key, value in distro_info.items():
        print(f"  {key}: {value}")
    
    # Wykonanie bezpiecznego polecenia
    executor = CommandExecutor()
    result = executor.execute("ls -la")
    print("\nWynik polecenia 'ls -la':")
    print(f"Sukces: {result.success}")
    print(f"Kod wyjścia: {result.return_code}")
    print(f"Czas wykonania: {result.execution_time:.2f}s")
    print(f"Wyjście standardowe:\n{result.stdout}")
    
    # Próba wykonania potencjalnie niebezpiecznego polecenia
    result = executor.execute("rm -rf /")
    print("\nWynik próby wykonania niebezpiecznego polecenia:")
    print(f"Sukces: {result.success}")
    print(f"Błąd: {result.stderr}")
