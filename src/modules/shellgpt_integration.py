#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Moduł integracji z ShellGPT API dla asystenta AI dla systemu Linux.
Odpowiada za komunikację z API, przetwarzanie odpowiedzi i zarządzanie kluczem API.
"""

import os
import json
import logging
import requests
import time
import subprocess
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
import tempfile
import configparser
import shutil

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/linux_ai_assistant.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("shellgpt_api")

@dataclass
class ApiResponse:
    """Klasa przechowująca odpowiedź z API."""
    success: bool
    command: str
    explanation: str
    error: str = ""


class ShellGptIntegration:
    """Klasa odpowiedzialna za integrację z ShellGPT."""

    def __init__(self, config_path: str = "~/.config/linux_ai_assistant/config.ini"):
        """
        Inicjalizacja integracji z ShellGPT.

        Args:
            config_path: Ścieżka do pliku konfiguracyjnego
        """
        self.config_path = os.path.expanduser(config_path)
        self.config = self._load_config()
        self.api_key = self._get_api_key()
        self.cache_dir = os.path.expanduser("~/.cache/linux_ai_assistant")

        # Utworzenie katalogów konfiguracyjnych, jeśli nie istnieją
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

    def _load_config(self) -> configparser.ConfigParser:
        """
        Wczytuje konfigurację z pliku.

        Returns:
            configparser.ConfigParser: Obiekt konfiguracji
        """
        config = configparser.ConfigParser()

        if os.path.exists(self.config_path):
            config.read(self.config_path)

        # Dodanie domyślnych sekcji, jeśli nie istnieją
        if 'ShellGPT' not in config:
            config['ShellGPT'] = {}

        if 'General' not in config:
            config['General'] = {
                'language': 'pl',
                'distribution_detection': 'true',
                'cache_enabled': 'true',
                'log_level': 'INFO'
            }

        return config

    def _save_config(self) -> None:
        """Zapisuje konfigurację do pliku."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

    def _get_api_key(self) -> Optional[str]:
        """
        Pobiera klucz API z konfiguracji lub zmiennych środowiskowych.

        Returns:
            Optional[str]: Klucz API lub None, jeśli nie znaleziono
        """
        # Sprawdzenie zmiennych środowiskowych
        api_key = os.environ.get('OPENAI_API_KEY')

        # Sprawdzenie konfiguracji
        if not api_key and 'api_key' in self.config['ShellGPT']:
            api_key = self.config['ShellGPT']['api_key']

        return api_key

    def set_api_key(self, api_key: str) -> None:
        """
        Ustawia klucz API w konfiguracji.

        Args:
            api_key: Klucz API
        """
        self.api_key = api_key
        self.config['ShellGPT']['api_key'] = api_key
        self._save_config()
        logger.info("Zapisano klucz API w konfiguracji")

    def _check_shellgpt_installation(self) -> bool:
        """
        Sprawdza, czy ShellGPT jest zainstalowany.

        Returns:
            bool: Czy ShellGPT jest zainstalowany
        """
        try:
            result = subprocess.run(
                ["which", "sgpt"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _install_shellgpt(self) -> bool:
        """
        Instaluje ShellGPT.

        Returns:
            bool: Czy instalacja się powiodła
        """
        try:
            logger.info("Instalowanie ShellGPT...")
            result = subprocess.run(
                ["pip", "install", "shell-gpt"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("ShellGPT zainstalowany pomyślnie")
                return True
            else:
                logger.error(f"Błąd podczas instalacji ShellGPT: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Wyjątek podczas instalacji ShellGPT: {str(e)}")
            return False

    def ensure_shellgpt_available(self) -> bool:
        """
        Upewnia się, że ShellGPT jest dostępny, instalując go w razie potrzeby.

        Returns:
            bool: Czy ShellGPT jest dostępny
        """
        if self._check_shellgpt_installation():
            return True

        return self._install_shellgpt()

    def _setup_shellgpt_config(self) -> bool:
        """
        Konfiguruje ShellGPT z kluczem API.

        Returns:
            bool: Czy konfiguracja się powiodła
        """
        if not self.api_key:
            logger.error("Brak klucza API")
            return False

        try:
            result = subprocess.run(
                ["sgpt", "config", "set", "OPENAI_API_KEY", self.api_key],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("Skonfigurowano ShellGPT z kluczem API")
                return True
            else:
                logger.error(f"Błąd podczas konfiguracji ShellGPT: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Wyjątek podczas konfiguracji ShellGPT: {str(e)}")
            return False

    def _get_cache_key(self, prompt: str, distro_info: Dict[str, str]) -> str:
        """
        Generuje klucz cache dla zapytania.

        Args:
            prompt: Zapytanie użytkownika
            distro_info: Informacje o dystrybucji

        Returns:
            str: Klucz cache
        """
        # Uproszczony klucz cache bazujący na zapytaniu i dystrybucji
        distro_id = distro_info.get('ID', 'unknown')
        import hashlib
        hash_obj = hashlib.md5(f"{prompt}_{distro_id}".encode())
        return hash_obj.hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[ApiResponse]:
        """
        Pobiera odpowiedź z cache.

        Args:
            cache_key: Klucz cache

        Returns:
            Optional[ApiResponse]: Odpowiedź z cache lub None, jeśli nie znaleziono
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            return ApiResponse(
                success=data['success'],
                command=data['command'],
                explanation=data['explanation'],
                error=data.get('error', '')
            )
        except Exception as e:
            logger.error(f"Błąd podczas odczytu z cache: {str(e)}")
            return None

    def _save_to_cache(self, cache_key: str, response: ApiResponse) -> None:
        """
        Zapisuje odpowiedź do cache.

        Args:
            cache_key: Klucz cache
            response: Odpowiedź do zapisania
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'success': response.success,
                    'command': response.command,
                    'explanation': response.explanation,
                    'error': response.error
                }, f)
        except Exception as e:
            logger.error(f"Błąd podczas zapisu do cache: {str(e)}")

    def generate_command(self, prompt: str, distro_info: Dict[str, str],
                        use_cache: bool = True) -> ApiResponse:
        """
        Generuje polecenie terminalowe na podstawie zapytania użytkownika.

        Args:
            prompt: Zapytanie użytkownika
            distro_info: Informacje o dystrybucji
            use_cache: Czy używać cache

        Returns:
            ApiResponse: Odpowiedź z API
        """
        # Sprawdzenie dostępności ShellGPT
        if not self.ensure_shellgpt_available():
            return ApiResponse(
                success=False,
                command="",
                explanation="",
                error="Nie można zainstalować ShellGPT"
            )

        # Konfiguracja ShellGPT
        if not self._setup_shellgpt_config():
            return ApiResponse(
                success=False,
                command="",
                explanation="",
                error="Nie można skonfigurować ShellGPT z kluczem API"
            )

        # Sprawdzenie cache
        if use_cache and self.config['General'].getboolean('cache_enabled', True):
            cache_key = self._get_cache_key(prompt, distro_info)
            cached_response = self._get_from_cache(cache_key)

            if cached_response:
                logger.info(f"Znaleziono odpowiedź w cache dla zapytania: {prompt}")
                return cached_response

        # Przygotowanie kontekstu dystrybucji
        distro_context = ""
        if self.config['General'].getboolean('distribution_detection', True):
            distro_id = distro_info.get('ID', '')
            distro_version = distro_info.get('VERSION_ID', '')
            package_manager = distro_info.get('PACKAGE_MANAGER', '')

            distro_context = f"Dystrybucja: {distro_id} {distro_version}, Menedżer pakietów: {package_manager}. "

        # Przygotowanie pełnego zapytania
        full_prompt = f"{distro_context}Wygeneruj polecenie terminalowe dla: {prompt}"

        # Wywołanie ShellGPT
        try:
            # Utworzenie pliku tymczasowego na wynik
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
                temp_path = temp_file.name

            # Wywołanie ShellGPT z opcją --code dla uzyskania tylko kodu
            code_result = subprocess.run(
                ["sgpt", "--code", full_prompt],
                capture_output=True,
                text=True
            )

            # Wywołanie ShellGPT dla uzyskania wyjaśnienia
            explanation_result = subprocess.run(
                ["sgpt", full_prompt],
                capture_output=True,
                text=True
            )

            if code_result.returncode == 0:
                command = code_result.stdout.strip()
                explanation = explanation_result.stdout.strip() if explanation_result.returncode == 0 else ""

                response = ApiResponse(
                    success=True,
                    command=command,
                    explanation=explanation,
                    error=""
                )

                # Zapisanie do cache
                if use_cache and self.config['General'].getboolean('cache_enabled', True):
                    cache_key = self._get_cache_key(prompt, distro_info)
                    self._save_to_cache(cache_key, response)

                return response
            else:
                error_msg = code_result.stderr.strip()
                logger.error(f"Błąd ShellGPT: {error_msg}")

                return ApiResponse(
                    success=False,
                    command="",
                    explanation="",
                    error=f"Błąd ShellGPT: {error_msg}"
                )

        except Exception as e:
            logger.error(f"Wyjątek podczas generowania polecenia: {str(e)}")

            return ApiResponse(
                success=False,
                command="",
                explanation="",
                error=f"Błąd: {str(e)}"
            )
        finally:
            # Usunięcie pliku tymczasowego
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)

    def clear_cache(self) -> bool:
        """
        Czyści cache.

        Returns:
            bool: Czy operacja się powiodła
        """
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
                logger.info("Wyczyszczono cache")
                return True
            return False
        except Exception as e:
            logger.error(f"Błąd podczas czyszczenia cache: {str(e)}")
            return False


# Przykład użycia
if __name__ == "__main__":
    # Przykładowe informacje o dystrybucji
    distro_info = {
        'ID': 'ubuntu',
        'VERSION_ID': '22.04',
        'PACKAGE_MANAGER': 'apt'
    }

    # Inicjalizacja integracji
    integration = ShellGptIntegration()

    # Sprawdzenie, czy klucz API jest dostępny
    if not integration.api_key:
        print("Brak klucza API. Proszę podać klucz API OpenAI:")
        api_key = input("> ")
        integration.set_api_key(api_key)

    # Generowanie polecenia
    prompt = "Pokaż wszystkie pliki w bieżącym katalogu, włącznie z ukrytymi"
    print(f"Zapytanie: {prompt}")

    response = integration.generate_command(prompt, distro_info)

    if response.success:
        print("\nWygenerowane polecenie:")
        print(response.command)
        print("\nWyjaśnienie:")
        print(response.explanation)
    else:
        print(f"\nBłąd: {response.error}")
