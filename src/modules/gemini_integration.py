# Plik: src/modules/gemini_integration.py

import os
import logging
import json
import google.generativeai as genai
import google.generativeai.types as genai_types
from dataclasses import dataclass
from typing import Dict, Optional, List, Any

# Logger dla tego modułu
logger = logging.getLogger("gemini_api")

@dataclass
class GeminiApiResponse:
    success: bool
    command: str
    explanation: str
    error: Optional[str] = None
    analyzed_text_type: Optional[str] = None # Dla analyze_text_input_type
    fix_suggestion: Optional[str] = None     # Dla analyze_execution_error_and_suggest_fix
    suggested_interaction_input: Optional[str] = None # np. "t", "y", "opcja1"
    suggested_button_label: Optional[str] = None     # np. "Zainstaluj (potwierdź T)"

class GeminiIntegration:
    def __init__(self, model_name: str = 'gemini-1.5-flash'): # Używamy stabilnego modelu
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        self.model_name = model_name
        self.genai_model: Optional[genai.GenerativeModel] = None

        if not self.api_key:
            logger.error("Brak klucza GOOGLE_API_KEY w zmiennych środowiskowych!")
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.genai_model = genai.GenerativeModel(self.model_name)
                logger.info(f"Skonfigurowano i zainicjalizowano model Gemini API: {self.model_name}")
            except Exception as e:
                logger.error(f"Błąd podczas konfiguracji lub inicjalizacji Gemini API: {e}", exc_info=True)
                self.api_key = None

    def _send_request_to_gemini(self,
                                prompt_parts: List[Any],
                                is_chat: bool = False,
                                chat_session: Optional[genai.ChatSession] = None) -> GeminiApiResponse:
        if not self.api_key or not self.genai_model:
            return GeminiApiResponse(
                success=False, command="", explanation="",
                error="Klucz API Google nie skonfigurowany lub model nie zainicjalizowany."
            )
        try:
            safety_settings = [
                {"category": genai_types.HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": genai_types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": genai_types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": genai_types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": genai_types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": genai_types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH},
            ]
            generation_config = genai_types.GenerationConfig(temperature=0.2, max_output_tokens=2048)

            response: genai_types.GenerateContentResponse
            if is_chat and chat_session:
                logger.debug(f"Gemini: Sending to CHAT. Last message part: {prompt_parts[-1] if prompt_parts else 'NO PROMPT PARTS'}")
                content_to_send = prompt_parts[-1] if prompt_parts else ""
                response = chat_session.send_message(content_to_send, generation_config=generation_config, safety_settings=safety_settings)
            else:
                logger.debug(f"Gemini: Sending SINGLE request. Prompt parts: {prompt_parts}")
                response = self.genai_model.generate_content(prompt_parts, generation_config=generation_config, safety_settings=safety_settings)

            logger.debug(f"Gemini: Surowa odpowiedź: {response}")

            if not response.candidates:
                reason_name = "Unknown (no candidates in response)"
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and \
                   hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason is not None:
                    block_reason_enum_type = getattr(genai_types, 'BlockReason', None)
                    if block_reason_enum_type and hasattr(block_reason_enum_type, 'Name'):
                        try: reason_name = block_reason_enum_type.Name(response.prompt_feedback.block_reason) # type: ignore
                        except ValueError: reason_name = str(response.prompt_feedback.block_reason)
                    else: reason_name = str(response.prompt_feedback.block_reason)
                logger.error(f"Odpowiedź Gemini zablokowana lub pusta. Powód: {reason_name}")
                return GeminiApiResponse(success=False, command="", explanation="", error=f"Odpowiedź zablokowana przez AI: {reason_name}")

            candidate = response.candidates[0]
            finish_reason_value = candidate.finish_reason
            finish_reason_name_str = str(finish_reason_value.name if hasattr(finish_reason_value, 'name') else finish_reason_value).upper()

            logger.debug(f"Gemini: Candidate.finish_reason: {candidate.finish_reason}, Resolved Name: {finish_reason_name_str}")

            acceptable_finish_reasons = ["STOP", "MAX_TOKENS"]
            if finish_reason_name_str not in acceptable_finish_reasons:
                logger.error(f"Generowanie zakończone z niespodziewanym powodem: {finish_reason_name_str} (raw: {candidate.finish_reason})")
                return GeminiApiResponse(success=False, command="", explanation="", error=f"Błąd generowania AI: {finish_reason_name_str}")

            if not candidate.content or not candidate.content.parts:
                logger.error("Brak części (parts) w zawartości odpowiedzi Gemini.")
                return GeminiApiResponse(success=False, command="", explanation="", error="Brak zawartości tekstowej w odpowiedzi AI.")

            raw_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text')).strip()
            return GeminiApiResponse(success=True, command=raw_text, explanation=raw_text)

        except Exception as e:
            logger.error(f"Wyjątek podczas komunikacji z Gemini API: {str(e)}", exc_info=True)
            return GeminiApiResponse(success=False, command="", explanation="", error=f"Wyjątek API: {str(e)}")

    def generate_command_with_explanation(self, user_prompt: str, distro_info: Dict[str, str],
                                           working_dir: Optional[str] = None,
                                           cwd_file_list: Optional[List[str]] = None, # Nowy argument
                                           history: Optional[List[Dict[str, Any]]] = None,
                                           language_instruction: Optional[str] = None) -> GeminiApiResponse:
        distro_context = f"Dystrybucja: {distro_info.get('ID', 'nieznana')} {distro_info.get('VERSION_ID', '')}, Menedżer pakietów: {distro_info.get('PACKAGE_MANAGER', 'nieznany')}."
        wd_context = f"Aktualny katalog roboczy: {working_dir}" if working_dir else "Katalog roboczy nieznany."
        lang_instr = language_instruction if language_instruction else "Respond in English."

        cwd_files_info = "Brak informacji o plikach w CWD."
        if cwd_file_list:
            if len(cwd_file_list) > 20: # Ograniczenie, aby nie przepełnić promptu
                cwd_files_info = f"Dostępne pliki w bieżącym katalogu roboczym ({working_dir}) (pierwsze 20): {', '.join(cwd_file_list[:20])}, ..."
            elif cwd_file_list: # Niepusta lista, ale nie za długa
                 cwd_files_info = f"Dostępne pliki w bieżącym katalogu roboczym ({working_dir}): {', '.join(cwd_file_list)}."
            else: # Pusta lista plików
                 cwd_files_info = f"Brak plików (lub tylko katalogi) w bieżącym katalogu roboczym ({working_dir})."


        system_instruction = f"""Jesteś ekspertem od terminala Linux. Twoim zadaniem jest pomoc użytkownikowi przez wygenerowanie odpowiedniego polecenia.
Kontekst systemu: {distro_context} {wd_context}
{cwd_files_info}
{lang_instr}

Jeśli użytkownik wpisze nazwę pliku z literówką lub złą wielkością liter, ale na liście plików z CWD jest pasujący plik, użyj poprawnej nazwy z listy.

Format odpowiedzi:
NAJPIERW linia z poleceniem.
W DOKŁADNIE NASTĘPNEJ linii słowo kluczowe "WYJAŚNIENIE:" (bez dodatkowych znaków).
Po "WYJAŚNIENIE:" krótkie, 1-2 zdaniowe wyjaśnienie polecenia (w języku określonym przez instrukcję językową).

JEŚLI użytkownik prosi o wykonanie akcji, która normalnie wymaga prostego potwierdzenia (np. instalacja pakietu, gdzie system zapyta 'Czy chcesz kontynuować? [T/n]'), I intencja użytkownika jest jasna, że CHCE tej akcji (np. "zainstaluj ten pakiet"), TO wygeneruj polecenie z flagą automatycznego potwierdzenia (np. sudo apt install -y nazwa-pakietu). W takim przypadku NIE generuj sekcji INTERAKCJA_POLECENIE. W WYJAŚNIENIE wspomnij o użytej fladze automatycznego potwierdzenia.

JEŚLI jednak polecenie wywoła bardziej złożoną interakcję, lub nie ma prostej flagi typu '-y', LUB jeśli chcesz dać użytkownikowi bardziej świadomy wybór przez GUI (np. użytkownik pyta ogólnie "jak zainstalować X" zamiast "zainstaluj X"), możesz zasugerować odpowiedź i etykietę dla przycisku. W DOKŁADNIE NASTĘPNEJ linii po WYJAŚNIENIE: (jeśli jest taka potrzeba) dodaj słowo kluczowe "INTERAKCJA_POLECENIE:"
Po "INTERAKCJA_POLECENIE:" podaj:
  1. Sugerowaną odpowiedź tekstową (np. "t", "y", "opcja1").
  2. ŚREDNIK (;)
  3. Etykietę dla przycisku w GUI, która odzwierciedla akcję (np. "Zainstaluj (potwierdź T)", "Wybierz opcję X"). Etykieta powinna być krótka i zrozumiała.

Nie dodawaj nic więcej, żadnych wstępów, markdown, poza wymaganym formatem.
Przykład 1 (automatyczne potwierdzenie, język polski):
sudo apt install -y firefox
WYJAŚNIENIE: Instaluje przeglądarkę Firefox używając apt, automatycznie potwierdzając (-y) wszystkie pytania.

Przykład 2 (sugestia dla GUI, gdy nie ma -y, język polski):
sudo apt install gimp
WYJAŚNIENIE: Przygotowuje polecenie do instalacji GIMP. System zapyta o potwierdzenie.
INTERAKCJA_POLECENIE: t;Zainstaluj GIMP (potwierdź T)

Jeśli zapytanie jest niejasne lub zbyt ogólne, aby wygenerować jedno polecenie, odpowiedz TYLKO słowami: CLARIFY_REQUEST
Jeśli zapytanie wydaje się niebezpieczne, odpowiedz TYLKO słowami: DANGEROUS_REQUEST
"""
        if not self.genai_model:
            return GeminiApiResponse(success=False, command="", explanation="", error="Model Gemini nie został zainicjalizowany.")

        gemini_history_formatted: List[Dict[str, Any]] = []
        if history:
            for item in history:
                role = item.get("role")
                text_content = "".join(p.get("text", "") for p in item.get("parts", [])).strip()
                if role and text_content and role.lower() in ["user", "model"]:
                    gemini_history_formatted.append({'role': role.lower(), 'parts': [{'text': text_content}]})

        logger.debug(f"Gemini: Przygotowana historia dla ChatSession: {json.dumps(gemini_history_formatted, indent=2, ensure_ascii=False)}")
        chat_session = self.genai_model.start_chat(history=gemini_history_formatted)
        prompt_for_chat = f"{system_instruction}\n\nZadanie od użytkownika: \"{user_prompt}\"\nWygeneruj polecenie i wyjaśnienie."
        api_response_wrapper = self._send_request_to_gemini([prompt_for_chat], is_chat=True, chat_session=chat_session)

        if not api_response_wrapper.success:
            return GeminiApiResponse(success=False, command="", explanation="", error=api_response_wrapper.error)

        raw_text = api_response_wrapper.command

        if raw_text.strip() == "CLARIFY_REQUEST":
            return GeminiApiResponse(success=False, command="", explanation="", error="CLARIFY_REQUEST")
        if raw_text.strip() == "DANGEROUS_REQUEST":
            return GeminiApiResponse(success=False, command="", explanation="", error="DANGEROUS_REQUEST")

        command_part, explanation_part = "", ""
        interaction_input, button_label = None, None

        lines = raw_text.split('\n')
        command_part = lines[0].strip() if lines else ""

        default_explanation_on_format_error = f"({lang_instr.split('.')[0].replace('ODPOWIADAJ ZAWSZE W JĘZYKU ', '').capitalize()}: AI nie dostarczyło wyjaśnienia w oczekiwanym formacie)"

        idx = 1
        if idx < len(lines) and lines[idx].strip().startswith("WYJAŚNIENIE:"):
            explanation_content = lines[idx].strip()[len("WYJAŚNIENIE:"):].strip()
            idx += 1

            # Zbieranie wieloliniowego wyjaśnienia, jeśli występuje przed INTERAKCJA_POLECENIE
            while idx < len(lines) and not lines[idx].strip().startswith("INTERAKCJA_POLECENIE:"):
                explanation_content += "\n" + lines[idx].strip()
                idx += 1
            explanation_part = explanation_content.strip()

            if idx < len(lines) and lines[idx].strip().startswith("INTERAKCJA_POLECENIE:"):
                interaction_line_content = lines[idx].strip()[len("INTERAKCJA_POLECENIE:"):].strip()
                if ";" in interaction_line_content:
                    interaction_input, button_label = map(str.strip, interaction_line_content.split(";", 1))
                else:
                    interaction_input = interaction_line_content
                    button_label = f"Wykonaj ({interaction_input})" if interaction_input else "Wykonaj"
                logger.info(f"AI zasugerowało interakcję: input='{interaction_input}', label='{button_label}'")
        elif command_part: # Tylko polecenie, brak poprawnego wyjaśnienia
            explanation_part = default_explanation_on_format_error
        else: # Pusta odpowiedź lub zły format
             logger.error(f"Nie udało się sparsować polecenia/wyjaśnienia z odpowiedzi AI: '{raw_text}'")
             return GeminiApiResponse(success=False, command="", explanation="", error="Nie udało się sparsować polecenia/wyjaśnienia z odpowiedzi AI.")

        if not command_part: # To nie powinno się zdarzyć, jeśli wcześniejszy warunek 'else' zadziałał
            logger.error(f"Krytyczny błąd: Brak polecenia po parsowaniu odpowiedzi AI: '{raw_text}'")
            return GeminiApiResponse(success=False, command="", explanation=explanation_part, error="Brak polecenia w odpowiedzi AI.")

        # Ostateczne czyszczenie, jeśli explanation_part jest puste, a był błąd formatu
        if not explanation_part.strip() and command_part:
            explanation_part = default_explanation_on_format_error


        return GeminiApiResponse(success=True, command=command_part, explanation=explanation_part,
                                 suggested_interaction_input=interaction_input,
                                 suggested_button_label=button_label)

    def analyze_text_input_type(self, text_input: str, language_instruction: Optional[str] = None) -> GeminiApiResponse:
        lang_instr = language_instruction if language_instruction else "Respond in English."
        prompt = f"""Przeanalizuj poniższy tekst wejściowy użytkownika i określ jego typ.
{lang_instr}
Tekst wejściowy: "{text_input}"

Odpowiedz TYLKO w formacie JSON z kluczami "type" i "explanation".
Możliwe wartości dla "type": "linux_command", "natural_language_query", "other".
Jeśli "type" to "linux_command", "explanation" powinno być krótkim opisem tego polecenia (w języku z instrukcji).
Jeśli "type" to "natural_language_query", "explanation" może być puste lub zawierać krótkie podsumowanie zapytania (w języku z instrukcji).
Jeśli "type" to "other", "explanation" powinno być puste.
"""
        api_response_wrapper = self._send_request_to_gemini([prompt])
        if not api_response_wrapper.success:
            return GeminiApiResponse(success=False, command="", explanation="", error=api_response_wrapper.error, analyzed_text_type="error")

        raw_ai_response_text = api_response_wrapper.command
        cleaned_json_text = raw_ai_response_text.replace("```json", "").replace("```", "").strip()

        try:
            analysis_result = json.loads(cleaned_json_text)
            text_type = analysis_result.get("type", "other")
            explanation = analysis_result.get("explanation", "")
            return GeminiApiResponse(success=True, command="", explanation=explanation, analyzed_text_type=text_type)
        except json.JSONDecodeError:
            logger.error(f"Błąd parsowania JSON z analizy typu tekstu. Oryginał: '{raw_ai_response_text}'. Oczyszczony: '{cleaned_json_text}'")
            return GeminiApiResponse(success=False, command="", explanation="", error="Błąd parsowania odpowiedzi AI (analiza typu).", analyzed_text_type="error")
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas analizy typu tekstu: {e}", exc_info=True)
            return GeminiApiResponse(success=False, command="", explanation="", error=f"Nieoczekiwany błąd: {e}", analyzed_text_type="error")

    def generate_clarification_questions(self, complex_query: str, distro_info: Dict[str, str],
                                         working_dir: Optional[str],
                                         language_instruction: Optional[str] = None) -> List[str]:
        distro_context = f"Dystrybucja: {distro_info.get('ID', 'nieznana')}."
        wd_context = f"Katalog roboczy: {working_dir}." if working_dir else ""
        lang_instr = language_instruction if language_instruction else "Generate questions in English."

        prompt = f"""Użytkownik zadał złożone lub niejasne zapytanie dotyczące Linuksa: "{complex_query}"
Kontekst: {distro_context} {wd_context}
{lang_instr}
Twoim zadaniem jest wygenerowanie 2-3 krótkich, precyzyjnych pytań, które pomogą użytkownikowi doprecyzować jego intencje.
Pytania powinny być sformułowane tak, aby odpowiedzi na nie pozwoliły na wygenerowanie konkretnego polecenia.
Zwróć TYLKO listę pytań, każde w nowej linii (w języku z instrukcji). Nie dodawaj numeracji ani żadnych innych komentarzy.
Jeśli uważasz, że zapytanie jest wystarczająco jasne i nie wymaga dopytywania, zwróć pustą odpowiedź lub pojedynczą linię "NO_CLARIFICATION_NEEDED".
"""
        api_response_wrapper = self._send_request_to_gemini([prompt])
        if not api_response_wrapper.success:
            logger.error(f"Błąd generowania pytań doprecyzowujących: {api_response_wrapper.error}")
            return []
        raw_text = api_response_wrapper.command.strip()
        if not raw_text or raw_text == "NO_CLARIFICATION_NEEDED": return []
        questions = [q.strip() for q in raw_text.split('\n') if q.strip()]
        logger.info(f"Gemini: Wygenerowane pytania doprecyzowujące: {questions}")
        return questions

    def analyze_execution_error_and_suggest_fix(
        self, command: str, stderr: str, return_code: int,
        distro_info: Dict[str, str], working_dir: Optional[str],
        language_instruction: Optional[str] = None
    ) -> GeminiApiResponse:
        if not stderr and return_code == 0:
            return GeminiApiResponse(success=True, command=command, explanation="", fix_suggestion="Brak błędu do analizy.")

        distro_context = f"Dystrybucja: {distro_info.get('ID', 'nieznana')} {distro_info.get('VERSION_ID', '')}, Menedżer pakietów: {distro_info.get('PACKAGE_MANAGER', 'nieznany')}."
        wd_context = f"Katalog roboczy: {working_dir}" if working_dir else "Katalog roboczy nieznany."
        lang_instr = language_instruction if language_instruction else "Provide analysis in English."

        prompt = f"""Użytkownik próbował wykonać następujące polecenie Linux:
`{command}`

Polecenie zakończyło się z kodem wyjścia: {return_code}
Standardowe wyjście błędów (stderr) było następujące (jeśli puste, oznacza brak stderr):
--- STDERR START ---
{stderr.strip() if stderr else "Brak stderr."}
--- STDERR END ---

Kontekst systemu: {distro_context} {wd_context}
{lang_instr}

Przeanalizuj ten błąd. Podaj:
1.  Prawdopodobną przyczynę błędu (krótko, 1-2 zdania, w języku z instrukcji).
2.  Proponowane kroki naprawcze lub alternatywne polecenia (jeśli to możliwe, podaj konkretne polecenia, w języku z instrukcji).

Odpowiedz TYLKO w formacie JSON z jednym kluczem "fix_suggestion", którego wartością jest string zawierający analizę i sugestie (w języku z instrukcji).
Przykład odpowiedzi JSON (jeśli język to polski):
{{"fix_suggestion": "Przyczyna: Prawdopodobnie brak uprawnień do zapisu w danym katalogu lub plik nie istnieje.\\nSugestie:\\n1. Sprawdź uprawnienia: `ls -ld /sciezka/do/katalogu`\\n2. Spróbuj wykonać polecenie z `sudo`: `sudo {command}`\\n3. Upewnij się, że plik/katalog docelowy istnieje."}}

Jeśli błąd jest zbyt ogólny, w "fix_suggestion" napisz (w języku z instrukcji): "Nie można jednoznacznie zdiagnozować problemu. Sprawdź komunikat błędu i uprawnienia."
"""
        logger.debug(f"Gemini: Prompt dla analizy błędu:\n{prompt}")
        api_response_wrapper = self._send_request_to_gemini([prompt])

        if not api_response_wrapper.success:
            return GeminiApiResponse(success=False, command=command, explanation="",
                                     error=f"Błąd generowania sugestii naprawczej: {api_response_wrapper.error}")

        raw_ai_response_text = api_response_wrapper.command
        cleaned_json_text = raw_ai_response_text.replace("```json", "").replace("```", "").strip()
        logger.debug(f"Gemini: Oczyszczony JSON (fix_suggestion): '{cleaned_json_text}'")

        try:
            analysis_result = json.loads(cleaned_json_text)
            suggestion = analysis_result.get("fix_suggestion", f"({lang_instr.split('.')[0].replace('ODPOWIADAJ ZAWSZE W JĘZYKU ', '').capitalize()}: AI nie dostarczyło sugestii w oczekiwanym formacie.)")
            return GeminiApiResponse(success=True, command=command, explanation="", fix_suggestion=suggestion)
        except json.JSONDecodeError as json_err:
            logger.error(f"Błąd parsowania JSON z sugestią. Oryginał: '{raw_ai_response_text}'. Oczyszczony: '{cleaned_json_text}'. Błąd: {json_err}")
            return GeminiApiResponse(success=True, command=command, explanation="",
                                     fix_suggestion=f"({lang_instr.split('.')[0].replace('ODPOWIADAJ ZAWSZE W JĘZYKU ', '').capitalize()}: AI zwróciło niepoprawny format JSON. Odpowiedź: {raw_ai_response_text}")
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd analizy błędu: {e}", exc_info=True)
            return GeminiApiResponse(success=False, command=command, explanation="", error=f"Nieoczekiwany błąd sugestii: {e}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
    if not os.environ.get('GOOGLE_API_KEY'):
        print("Proszę ustawić zmienną środowiskową GOOGLE_API_KEY do testów.")
    else:
        gemini_client = GeminiIntegration()
        test_distro_info = {'ID': 'ubuntu', 'VERSION_ID': '22.04', 'PACKAGE_MANAGER': 'apt'}
        test_working_dir = "/home/user/documents"
        test_cwd_files = ["plik1.txt", "Dokument.pdf", "obraz.JPG", "stary_skrypt.sh"]
        polish_lang_instruction = "ODPOWIADAJ ZAWSZE W JĘZYKU POLSKIM. Wyjaśnienie polecenia i wszelkie inne teksty MUSZĄ być po polsku."

        print("\n--- Test: Generowanie polecenia z auto-potwierdzeniem (język polski) ---")
        result_auto_pl = gemini_client.generate_command_with_explanation(
            "zainstaluj od razu htop", test_distro_info, test_working_dir, test_cwd_files, language_instruction=polish_lang_instruction
        )
        if result_auto_pl.success:
            print(f"Polecenie: {result_auto_pl.command}\nWyjaśnienie: {result_auto_pl.explanation}")
            print(f"Sugerowana interakcja: {result_auto_pl.suggested_interaction_input}, Etykieta: {result_auto_pl.suggested_button_label}")
        else:
            print(f"Błąd: {result_auto_pl.error}")

        print("\n--- Test: Generowanie polecenia z sugestią interakcji (język polski) ---")
        result_inter_pl = gemini_client.generate_command_with_explanation(
            "jak zainstalować inkscape?", test_distro_info, test_working_dir, test_cwd_files, language_instruction=polish_lang_instruction
        )
        if result_inter_pl.success:
            print(f"Polecenie: {result_inter_pl.command}\nWyjaśnienie: {result_inter_pl.explanation}")
            print(f"Sugerowana interakcja: {result_inter_pl.suggested_interaction_input}, Etykieta: {result_inter_pl.suggested_button_label}")
        else:
            print(f"Błąd: {result_inter_pl.error}")

        print("\n--- Test: Generowanie polecenia z korektą nazwy pliku (CWD) ---")
        result_file_pl = gemini_client.generate_command_with_explanation(
            "pokaż zawartość plik1.TXT", test_distro_info, test_working_dir, test_cwd_files, language_instruction=polish_lang_instruction
        )
        if result_file_pl.success:
            print(f"Polecenie: {result_file_pl.command}\nWyjaśnienie: {result_file_pl.explanation}")
        else:
            print(f"Błąd: {result_file_pl.error}")
