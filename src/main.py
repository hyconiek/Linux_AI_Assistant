#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Główny moduł asystenta AI dla systemu Linux.
Integruje wszystkie komponenty i zapewnia interfejs użytkownika.
"""

import os
import sys
import argparse
import logging
import readline
import signal
import json
from typing import Dict, List, Optional
import colorama
from colorama import Fore, Style

# Importowanie modułów asystenta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.command_executor import CommandExecutor, DistributionDetector
from modules.gemini_integration import GeminiIntegration, GeminiApiResponse

# Inicjalizacja kolorów
colorama.init()

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/linux_ai_assistant.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("linux_ai_assistant")

class LinuxAIAssistant:
    """Główna klasa asystenta AI dla systemu Linux."""
    
    def __init__(self):
        """Inicjalizacja asystenta."""
        self.command_executor = CommandExecutor()
        self.ai_engine = GeminiIntegration()
        self.distro_detector = DistributionDetector()
        self.distro_info = self.distro_detector.detect_distribution()
        
        # Wyświetlenie informacji o wykrytej dystrybucji
        logger.info(f"Wykryta dystrybucja: {self.distro_info}")
    
    def process_query(self, query: str) -> Dict:
        """
        Przetwarza zapytanie użytkownika.
        
        Args:
            query: Zapytanie użytkownika
            
        Returns:
            Dict: Wynik przetwarzania
        """
        logger.info(f"Przetwarzanie zapytania: {query}")
        
        # Generowanie polecenia
        api_response = self.ai_engine.generate_command(query, self.distro_info)
        
        if not api_response.success:
            return {
                "success": False,
                "error": api_response.error or "Nie udało się wygenerować polecenia"
            }
        
        return {
            "success": True,
            "command": api_response.command,
            "explanation": api_response.explanation
        }
    
    def execute_command(self, command: str) -> Dict:
        """
        Wykonuje polecenie terminalowe.
        
        Args:
            command: Polecenie do wykonania
            
        Returns:
            Dict: Wynik wykonania
        """
        logger.info(f"Wykonywanie polecenia: {command}")
        
        # Wykonanie polecenia
        result = self.command_executor.execute(command)
        
        return {
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.return_code,
            "execution_time": result.execution_time
        }
    
    def interactive_mode(self):
        """Uruchamia asystenta w trybie interaktywnym."""
        print(f"{Fore.GREEN}=== Asystent AI dla systemu Linux ==={Style.RESET_ALL}")
        print(f"Wykryta dystrybucja: {Fore.CYAN}{self.distro_info.get('ID', 'nieznana')} {self.distro_info.get('VERSION_ID', '')}{Style.RESET_ALL}")
        print(f"Menedżer pakietów: {Fore.CYAN}{self.distro_info.get('PACKAGE_MANAGER', 'nieznany')}{Style.RESET_ALL}")
        print(f"Wpisz {Fore.YELLOW}exit{Style.RESET_ALL} lub {Fore.YELLOW}quit{Style.RESET_ALL}, aby zakończyć.")
        print(f"Wpisz {Fore.YELLOW}help{Style.RESET_ALL}, aby wyświetlić pomoc.")
        print()
        
        while True:
            try:
                query = input(f"{Fore.GREEN}> {Style.RESET_ALL}")
                
                if query.lower() in ["exit", "quit"]:
                    break
                
                if query.lower() == "help":
                    self._show_help()
                    continue
                
                if not query.strip():
                    continue
                
                # Przetwarzanie zapytania
                print(f"{Fore.YELLOW}Przetwarzanie zapytania...{Style.RESET_ALL}")
                result = self.process_query(query)
                
                if not result["success"]:
                    print(f"{Fore.RED}Błąd: {result['error']}{Style.RESET_ALL}")
                    continue
                
                # Wyświetlenie wygenerowanego polecenia
                print(f"\n{Fore.CYAN}Sugerowane polecenie:{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{result['command']}{Style.RESET_ALL}")
                
                # Wyświetlenie wyjaśnienia
                if result["explanation"]:
                    print(f"\n{Fore.CYAN}Wyjaśnienie:{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}{result['explanation']}{Style.RESET_ALL}")
                
                # Zapytanie o wykonanie
                execute = input(f"\n{Fore.YELLOW}Wykonać to polecenie? (t/n): {Style.RESET_ALL}")
                
                if execute.lower() in ["t", "tak", "y", "yes"]:
                    # Wykonanie polecenia
                    print(f"{Fore.YELLOW}Wykonywanie polecenia...{Style.RESET_ALL}")
                    exec_result = self.execute_command(result["command"])
                    
                    if exec_result["success"]:
                        print(f"{Fore.GREEN}Polecenie wykonane pomyślnie{Style.RESET_ALL}")
                        if exec_result["stdout"]:
                            print(f"\n{Fore.WHITE}{exec_result['stdout']}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Błąd wykonania polecenia (kod: {exec_result['return_code']}){Style.RESET_ALL}")
                        if exec_result["stderr"]:
                            print(f"\n{Fore.RED}{exec_result['stderr']}{Style.RESET_ALL}")
                
            except KeyboardInterrupt:
                print("\nPrzerwano przez użytkownika.")
                break
            except Exception as e:
                logger.error(f"Błąd: {str(e)}")
                print(f"{Fore.RED}Wystąpił błąd: {str(e)}{Style.RESET_ALL}")
    
    def _show_help(self):
        """Wyświetla pomoc."""
        print(f"\n{Fore.CYAN}=== Pomoc asystenta AI dla systemu Linux ==={Style.RESET_ALL}")
        print(f"Asystent przetwarza zapytania w języku naturalnym i generuje odpowiednie polecenia terminalowe.")
        print(f"\n{Fore.CYAN}Przykłady zapytań:{Style.RESET_ALL}")
        print(f"- Pokaż wszystkie pliki w bieżącym katalogu, włącznie z ukrytymi")
        print(f"- Znajdź wszystkie pliki PDF w katalogu /home")
        print(f"- Sprawdź zużycie pamięci RAM")
        print(f"- Włącz zramswap dla zwiększenia dostępnej pamięci")
        print(f"- Zaktualizuj system")
        print(f"\n{Fore.CYAN}Dostępne komendy:{Style.RESET_ALL}")
        print(f"- {Fore.YELLOW}help{Style.RESET_ALL}: Wyświetla tę pomoc")
        print(f"- {Fore.YELLOW}exit{Style.RESET_ALL} lub {Fore.YELLOW}quit{Style.RESET_ALL}: Kończy działanie asystenta")
        print()


def main():
    """Funkcja główna."""
    parser = argparse.ArgumentParser(description="Asystent AI dla systemu Linux")
    parser.add_argument("--query", "-q", help="Zapytanie do asystenta")
    parser.add_argument("--execute", "-e", action="store_true", help="Automatycznie wykonaj wygenerowane polecenie")
    parser.add_argument("--json", "-j", action="store_true", help="Zwróć wynik w formacie JSON")
    args = parser.parse_args()
    
    # Inicjalizacja asystenta
    assistant = LinuxAIAssistant()
    
    if args.query:
        # Tryb jednorazowego zapytania
        result = assistant.process_query(args.query)
        
        if args.json:
            # Zwróć wynik w formacie JSON
            print(json.dumps(result))
        else:
            # Wyświetl wynik w czytelnej formie
            if result["success"]:
                print(f"Polecenie: {result['command']}")
                if result["explanation"]:
                    print(f"\nWyjaśnienie: {result['explanation']}")
                
                if args.execute:
                    # Wykonaj polecenie
                    exec_result = assistant.execute_command(result["command"])
                    
                    if exec_result["success"]:
                        print(f"\nPolecenie wykonane pomyślnie")
                        if exec_result["stdout"]:
                            print(f"\n{exec_result['stdout']}")
                    else:
                        print(f"\nBłąd wykonania polecenia (kod: {exec_result['return_code']})")
                        if exec_result["stderr"]:
                            print(f"\n{exec_result['stderr']}")
            else:
                print(f"Błąd: {result['error']}")
    else:
        # Tryb interaktywny
        assistant.interactive_mode()


if __name__ == "__main__":
    main()
