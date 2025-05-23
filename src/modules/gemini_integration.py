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
    command: Optional[str] = None # Może być None, jeśli to odpowiedź tekstowa
    explanation: Optional[str] = None # Może być główną odpowiedzią tekstową
    error: Optional[str] = None
    analyzed_text_type: Optional[str] = None
    fix_suggestion: Optional[str] = None
    suggested_interaction_input: Optional[str] = None
    suggested_button_label: Optional[str] = None
    is_text_answer: bool = False
    needs_file_search: bool = False # Nowe pole
    file_search_pattern: Optional[str] = None # Nowe pole
    file_search_message: Optional[str] = None # Nowe pole

class GeminiIntegration:
    def __init__(self, model_name: str = 'gemini-2.5-flash-preview-05-20'):
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
                success=False, error="Klucz API Google nie skonfigurowany lub model nie zainicjalizowany."
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
                content_to_send = prompt_parts[-1] if prompt_parts else ""
                response = chat_session.send_message(content_to_send, generation_config=generation_config, safety_settings=safety_settings)
            else:
                response = self.genai_model.generate_content(prompt_parts, generation_config=generation_config, safety_settings=safety_settings)

            logger.debug(f"Gemini: Surowa odpowiedź: {response}")

            if not response.candidates:
                reason_name = "Unknown (no candidates)"
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason: # type: ignore
                    reason_name = str(response.prompt_feedback.block_reason.name) # type: ignore
                logger.error(f"Odpowiedź Gemini zablokowana lub pusta. Powód: {reason_name}")
                return GeminiApiResponse(success=False, error=f"Odpowiedź zablokowana przez AI: {reason_name}")

            candidate = response.candidates[0]
            finish_reason_name_str = str(candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else candidate.finish_reason).upper() # type: ignore

            if finish_reason_name_str not in ["STOP", "MAX_TOKENS"]:
                logger.error(f"Generowanie zakończone z niespodziewanym powodem: {finish_reason_name_str}")
                return GeminiApiResponse(success=False, error=f"Błąd generowania AI: {finish_reason_name_str}")

            if not candidate.content or not candidate.content.parts: # type: ignore
                logger.error("Brak części (parts) w zawartości odpowiedzi Gemini.")
                return GeminiApiResponse(success=False, error="Brak zawartości tekstowej w odpowiedzi AI.")

            raw_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text')).strip() # type: ignore
            return GeminiApiResponse(success=True, explanation=raw_text) # explanation przechowuje raw_text

        except Exception as e:
            logger.error(f"Wyjątek podczas komunikacji z Gemini API: {str(e)}", exc_info=True)
            return GeminiApiResponse(success=False, error=f"Wyjątek API: {str(e)}")

    def generate_command_with_explanation(self, user_prompt: str, distro_info: Dict[str, str],
                                           working_dir: Optional[str] = None,
                                           cwd_file_list: Optional[List[str]] = None,
                                           history: Optional[List[Dict[str, Any]]] = None,
                                           language_instruction: Optional[str] = None) -> GeminiApiResponse:
        distro_context = f"Dystrybucja: {distro_info.get('ID', 'nieznana')} {distro_info.get('VERSION_ID', '')}, Menedżer pakietów: {distro_info.get('PACKAGE_MANAGER', 'nieznany')}."
        wd_context = f"Aktualny katalog roboczy: {working_dir}" if working_dir else "Katalog roboczy nieznany."
        lang_instr = language_instruction if language_instruction else "Respond in English."

        cwd_files_info = "Brak informacji o plikach/katalogach w CWD."
        if cwd_file_list:
            file_limit = 30 # Zwiększono limit dla lepszego kontekstu
            if len(cwd_file_list) > file_limit:
                cwd_files_info = f"Dostępne pliki i katalogi w bieżącym katalogu roboczym ({working_dir}) (pierwsze {file_limit}): {', '.join(cwd_file_list[:file_limit])}, ..."
            elif cwd_file_list:
                 cwd_files_info = f"Dostępne pliki i katalogi w bieżącym katalogu roboczym ({working_dir}): {', '.join(cwd_file_list)}."
            else:
                 cwd_files_info = f"Brak plików/katalogów w bieżącym katalogu roboczym ({working_dir})."

        formatted_history_for_prompt = ""
        if history:
            for entry in history:
                role = entry.get("role", "user")
                # Upewnij się, że parts jest listą i ma co najmniej jeden element (słownik)
                parts_list = entry.get("parts", [])
                text = ""
                if isinstance(parts_list, list) and parts_list:
                    first_part = parts_list[0]
                    if isinstance(first_part, dict):
                        text = first_part.get("text", "")

                if text:
                    formatted_history_for_prompt += f"{role.capitalize()}: {text}\n"


        system_instruction = f"""Jesteś ekspertem od terminala Linux. Twoim zadaniem jest pomoc użytkownikowi przez wygenerowanie odpowiedniego polecenia LUB odpowiedź na pytanie dotyczące plików w katalogu.
Kontekst systemu: {distro_context} {wd_context}
{cwd_files_info}
{lang_instr}

Historia konwersacji (jeśli istnieje):
{formatted_history_for_prompt if formatted_history_for_prompt else "Brak historii."}

ZASADY:
1. Jeśli zapytanie użytkownika jest PROŚBĄ O WYKONANIE AKCJI (np. "pokaż pliki", "zainstaluj coś", "usuń plik.txt", "rozjaśnij obraz.jpg"), wygeneruj polecenie.
   - Jeśli użytkownik wpisze nazwę pliku z literówką lub złą wielkością liter, ale na liście plików z CWD (lub z historii wyszukiwania) jest pasujący plik, użyj poprawnej nazwy z listy w poleceniu.
   - Jeśli użytkownik odnosi się do pliku wspomnianego wcześniej w historii konwersacji (np. "ten plik", "obrazek"), użyj nazwy tego pliku w poleceniu.
   - Format odpowiedzi dla polecenia:
     NAJPIERW linia z poleceniem.
     W DOKŁADNIE NASTĘPNEJ linii słowo kluczowe "WYJAŚNIENIE:"
     Po "WYJAŚNIENIE:" krótkie wyjaśnienie polecenia.
     OPCJONALNIE, jeśli polecenie może wymagać interakcji (np. pytanie T/N bez flagi -y), w NASTĘPNEJ linii "INTERAKCJA_POLECENIE: sugerowana_odpowiedź;Etykieta Przycisku"
     Przykład (instalacja z -y):
       sudo apt install -y firefox
       WYJAŚNIENIE: Instaluje Firefox, automatycznie potwierdzając.
     Przykład (instalacja bez -y, sugestia dla GUI):
       sudo apt install gimp
       WYJAŚNIENIE: Przygotowuje instalację GIMP, system zapyta o potwierdzenie.
       INTERAKCJA_POLECENIE: t;Zainstaluj GIMP (potwierdź T)

2. Jeśli zapytanie użytkownika jest PYTANIEM O PLIKI W KATALOGU (np. "czy są tu jakieś pliki snap?", "gdzie jest plik X?", "dlaczego nie widziałeś pliku X?"):
   - Jeśli MOŻESZ odpowiedzieć na podstawie dostarczonej listy plików CWD i/lub informacji z historii (np. wyników poprzedniego wyszukiwania), odpowiedz tekstowo:
     ODPOWIEDZ_TEKSTOWA:
     Twoja odpowiedź...
   - Jeśli NIE MOŻESZ odpowiedzieć (np. pliku nie ma na skróconej liście, użytkownik pyta o coś, czego nie widać, a historia nie pomaga),
     a pytanie sugeruje, że plik MOŻE istnieć lub użytkownik pyta DLACZEGO czegoś nie widać, ZAMIAST odpowiadać "nie wiem",
     poproś o przeszukanie katalogu, zwracając:
     SZUKAJ_PLIKOW: wzorzec_nazwy_pliku_do_wyszukania;komunikat_dla_uzytkownika_o_szukaniu
     Przykład (użytkownik pyta o *.log, a nie ma ich na liście):
       SZUKAJ_PLIKOW: *.log;Chwileczkę, przeszukuję katalog w poszukiwaniu plików .log...
     Przykład (użytkownik pyta o konkretny plik 'clean_snap.sh'):
       SZUKAJ_PLIKOW: clean_snap.sh;Zaraz sprawdzę, czy plik clean_snap.sh istnieje...
     Przykład (użytkownik pyta ogólnie, czy jest "coś związanego ze snap"):
       SZUKAJ_PLIKOW: *snap*;Sprawdzam pliki zawierające 'snap'...
   - 'wzorzec_nazwy_pliku_do_wyszukania' to wzorzec dla polecenia find (np. `*snap*`, `plik.txt`, `*.jpg`). Może być też bardziej ogólny.
   - 'komunikat_dla_uzytkownika_o_szukaniu' to krótki tekst, który GUI wyświetli użytkownikowi.

3. Jeśli zapytanie jest niejasne, odpowiedz TYLKO słowami: CLARIFY_REQUEST
4. Jeśli zapytanie wydaje się niebezpieczne, odpowiedz TYLKO słowami: DANGEROUS_REQUEST

Nie dodawaj nic więcej, żadnych wstępów, markdown, poza wymaganym formatem.
"""
        if not self.genai_model:
            return GeminiApiResponse(success=False, error="Model Gemini nie został zainicjalizowany.")

        # Używamy historii przekazanej do metody, a nie self.chat_history_for_ai (jeśli różnią się)
        effective_history = history if history else []
        chat_session = self.genai_model.start_chat(history=effective_history)

        prompt_for_chat = f"{system_instruction}\n\nZadanie/Pytanie od użytkownika: \"{user_prompt}\"\n"
        api_response_wrapper = self._send_request_to_gemini([prompt_for_chat], is_chat=True, chat_session=chat_session)

        if not api_response_wrapper.success or not api_response_wrapper.explanation:
            return GeminiApiResponse(success=False, error=api_response_wrapper.error or "Brak odpowiedzi od AI")

        raw_text = api_response_wrapper.explanation

        if raw_text.strip() == "CLARIFY_REQUEST": return GeminiApiResponse(success=False, error="CLARIFY_REQUEST")
        if raw_text.strip() == "DANGEROUS_REQUEST": return GeminiApiResponse(success=False, error="DANGEROUS_REQUEST")

        lines = raw_text.split('\n')

        if lines[0].strip().startswith("SZUKAJ_PLIKOW:"):
            content = lines[0].strip()[len("SZUKAJ_PLIKOW:"):].strip()
            pattern, message = "", "Rozpoczynam wyszukiwanie plików..."
            if ";" in content:
                pattern, message = map(str.strip, content.split(";", 1))
            else:
                pattern = content
            logger.info(f"AI zażądało przeszukania plików: wzorzec='{pattern}', komunikat='{message}'")
            return GeminiApiResponse(
                success=True,
                needs_file_search=True,
                file_search_pattern=pattern if pattern else "*",
                file_search_message=message
            )

        if lines[0].strip() == "ODPOWIEDZ_TEKSTOWA:":
            text_answer = "\n".join(lines[1:]).strip()
            logger.info(f"AI odpowiedziało tekstowo: {text_answer}")
            return GeminiApiResponse(success=True, explanation=text_answer, is_text_answer=True)

        command_part = lines[0].strip() if lines else ""
        explanation_part = ""
        interaction_input, button_label = None, None
        default_explanation_on_format_error = f"({lang_instr.split('.')[0].replace('ODPOWIADAJ ZAWSZE W JĘZYKU ', '').capitalize()}: AI nie dostarczyło wyjaśnienia w oczekiwanym formacie)"

        idx = 1
        if idx < len(lines) and lines[idx].strip().startswith("WYJAŚNIENIE:"):
            explanation_content = lines[idx].strip()[len("WYJAŚNIENIE:"):].strip()
            idx += 1
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
        elif command_part:
            explanation_part = default_explanation_on_format_error

        if not command_part and not explanation_part:
             logger.error(f"Nie udało się sparsować odpowiedzi AI: '{raw_text}'")
             return GeminiApiResponse(success=False, error="Nie udało się sparsować odpowiedzi AI.")

        if not explanation_part.strip() and command_part :
             explanation_part = default_explanation_on_format_error

        return GeminiApiResponse(success=True, command=command_part, explanation=explanation_part,
                                 suggested_interaction_input=interaction_input,
                                 suggested_button_label=button_label, is_text_answer=False)

    def analyze_text_input_type(self, text_input: str, language_instruction: Optional[str] = None) -> GeminiApiResponse:
        lang_instr = language_instruction if language_instruction else "Respond in English."
        prompt = f"""Przeanalizuj poniższy tekst wejściowy użytkownika i określ jego typ.
{lang_instr}
Tekst wejściowy: "{text_input}"

Odpowiedz TYLKO w formacie JSON z kluczami "type" i "explanation".
Możliwe wartości dla "type": "linux_command", "natural_language_query", "question_about_cwd", "other".
Jeśli "type" to "linux_command", "explanation" powinno być krótkim opisem tego polecenia.
Jeśli "type" to "natural_language_query", "explanation" może być puste lub zawierać krótkie podsumowanie zapytania.
Jeśli "type" to "question_about_cwd", "explanation" powinno wskazywać, że to pytanie o pliki.
Jeśli "type" to "other", "explanation" powinno być puste.
"""
        api_response_wrapper = self._send_request_to_gemini([prompt])
        if not api_response_wrapper.success or not api_response_wrapper.explanation:
            return GeminiApiResponse(success=False, error=api_response_wrapper.error or "Brak odpowiedzi od AI", analyzed_text_type="error")

        raw_ai_response_text = api_response_wrapper.explanation
        cleaned_json_text = raw_ai_response_text.replace("```json", "").replace("```", "").strip()

        try:
            analysis_result = json.loads(cleaned_json_text)
            text_type = analysis_result.get("type", "other")
            explanation = analysis_result.get("explanation", "")
            return GeminiApiResponse(success=True, explanation=explanation, analyzed_text_type=text_type)
        except json.JSONDecodeError:
            logger.error(f"Błąd parsowania JSON z analizy typu tekstu. Oryginał: '{raw_ai_response_text}'. Oczyszczony: '{cleaned_json_text}'")
            return GeminiApiResponse(success=False, error="Błąd parsowania odpowiedzi AI (analiza typu).", analyzed_text_type="error")
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas analizy typu tekstu: {e}", exc_info=True)
            return GeminiApiResponse(success=False, error=f"Nieoczekiwany błąd: {e}", analyzed_text_type="error")

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
        if not api_response_wrapper.success or not api_response_wrapper.explanation:
            logger.error(f"Błąd generowania pytań doprecyzowujących: {api_response_wrapper.error}")
            return []
        raw_text = api_response_wrapper.explanation.strip()
        if not raw_text or raw_text == "NO_CLARIFICATION_NEEDED": return []
        questions = [q.strip() for q in raw_text.split('\n') if q.strip()]
        logger.info(f"Gemini: Wygenerowane pytania doprecyzowujące: {questions}")
        return questions

    def analyze_execution_error_and_suggest_fix(
        self, command_str: str, stderr: str, return_code: int,
        distro_info: Dict[str, str], working_dir: Optional[str],
        language_instruction: Optional[str] = None
    ) -> GeminiApiResponse:
        if not stderr and return_code == 0:
            return GeminiApiResponse(success=True, command=command_str, explanation="", fix_suggestion="Brak błędu do analizy.")

        distro_context = f"Dystrybucja: {distro_info.get('ID', 'nieznana')} {distro_info.get('VERSION_ID', '')}, Menedżer pakietów: {distro_info.get('PACKAGE_MANAGER', 'nieznany')}."
        wd_context = f"Katalog roboczy: {working_dir}" if working_dir else "Katalog roboczy nieznany."
        lang_instr = language_instruction if language_instruction else "Provide analysis in English."

        prompt = f"""Użytkownik próbował wykonać następujące polecenie Linux:
`{command_str}`

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
{{"fix_suggestion": "Przyczyna: Prawdopodobnie brak uprawnień do zapisu w danym katalogu lub plik nie istnieje.\\nSugestie:\\n1. Sprawdź uprawnienia: `ls -ld /sciezka/do/katalogu`\\n2. Spróbuj wykonać polecenie z `sudo`: `sudo {command_str}`\\n3. Upewnij się, że plik/katalog docelowy istnieje."}}

Jeśli błąd jest zbyt ogólny, w "fix_suggestion" napisz (w języku z instrukcji): "Nie można jednoznacznie zdiagnozować problemu. Sprawdź komunikat błędu i uprawnienia."
"""
        logger.debug(f"Gemini: Prompt dla analizy błędu:\n{prompt}")
        api_response_wrapper = self._send_request_to_gemini([prompt])

        if not api_response_wrapper.success or not api_response_wrapper.explanation:
            return GeminiApiResponse(success=False, command=command_str,
                                     error=f"Błąd generowania sugestii naprawczej: {api_response_wrapper.error or 'Brak odpowiedzi AI'}")

        raw_ai_response_text = api_response_wrapper.explanation
        cleaned_json_text = raw_ai_response_text.replace("```json", "").replace("```", "").strip()
        logger.debug(f"Gemini: Oczyszczony JSON (fix_suggestion): '{cleaned_json_text}'")

        try:
            analysis_result = json.loads(cleaned_json_text)
            suggestion = analysis_result.get("fix_suggestion", f"({lang_instr.split('.')[0].replace('ODPOWIADAJ ZAWSZE W JĘZYKU ', '').capitalize()}: AI nie dostarczyło sugestii w oczekiwanym formacie.)")
            return GeminiApiResponse(success=True, command=command_str, fix_suggestion=suggestion)
        except json.JSONDecodeError as json_err:
            logger.error(f"Błąd parsowania JSON z sugestią. Oryginał: '{raw_ai_response_text}'. Oczyszczony: '{cleaned_json_text}'. Błąd: {json_err}")
            return GeminiApiResponse(success=True, command=command_str,
                                     fix_suggestion=f"({lang_instr.split('.')[0].replace('ODPOWIADAJ ZAWSZE W JĘZYKU ', '').capitalize()}: AI zwróciło niepoprawny format JSON. Odpowiedź: {raw_ai_response_text}")
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd analizy błędu: {e}", exc_info=True)
            return GeminiApiResponse(success=False, command=command_str, error=f"Nieoczekiwany błąd sugestii: {e}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
    if not os.environ.get('GOOGLE_API_KEY'):
        print("Proszę ustawić zmienną środowiskową GOOGLE_API_KEY do testów.")
    else:
        gemini_client = GeminiIntegration()
        test_distro_info = {'ID': 'ubuntu', 'VERSION_ID': '22.04', 'PACKAGE_MANAGER': 'apt'}
        test_working_dir = "/home/user/projects"
        test_cwd_files = ["main.py", "README.md", "obrazek.png", "snap_shot_2024.jpg", ".env", "very_long_list_of_files_that_should_be_truncated_if_above_limit_like_30_items_for_example_file_one_two_three_four_five_six_seven_eight_nine_ten_eleven_twelve_thirteen_fourteen_fifteen_sixteen_seventeen_eighteen_nineteen_twenty_twentyone_twentytwo_twentythree_twentyfour_twentyfive_twentysix_twentyseven_twentyeight_twentynine_thirty_thirtyone.txt"]
        polish_lang_instruction = "ODPOWIADAJ ZAWSZE W JĘZYKU POLSKIM."

        print("\n--- Test: Pytanie o pliki w CWD (język polski) ---")
        history_q_files = [
            {"role": "user", "parts": [{"text": "pokaż pliki w /home/user/projects"}]},
            {"role": "model", "parts": [{"text": f"Polecenie: ls -la /home/user/projects\nWYJAŚNIENIE: Listuje pliki w /home/user/projects.\nWynik polecenia (symulowany, bo nie wykonujemy naprawdę ls w teście jednostkowym):\nmain.py\nREADME.md\nobrazek.png\nsnap_shot_2024.jpg\n.env\nclean_snap.sh"}]}
        ]
        result_q_files = gemini_client.generate_command_with_explanation(
            "czy widzisz jakieś pliki związane ze snap w tym katalogu?",
            test_distro_info, test_working_dir, test_cwd_files, # test_cwd_files teraz zawiera clean_snap.sh
            history=history_q_files, language_instruction=polish_lang_instruction
        )
        if result_q_files.success:
            if result_q_files.is_text_answer:
                print(f"Odpowiedź tekstowa AI: {result_q_files.explanation}")
            elif result_q_files.needs_file_search:
                print(f"AI prosi o przeszukanie: Wzorzec='{result_q_files.file_search_pattern}', Komunikat='{result_q_files.file_search_message}'")
            else:
                print(f"Polecenie: {result_q_files.command}\nWyjaśnienie: {result_q_files.explanation}")
                print(f"Sugerowana interakcja: {result_q_files.suggested_interaction_input}, Etykieta: {result_q_files.suggested_button_label}")
        else:
            print(f"Błąd: {result_q_files.error}")

        print("\n--- Test: Pytanie o plik, którego nie ma na skróconej liście (powinno zasugerować SZUKAJ_PLIKOW) ---")
        short_cwd_files = ["main.py", "README.md"] # celowo nie zawiera 'obrazek.png'
        result_search_req = gemini_client.generate_command_with_explanation(
            "gdzie jest obrazek.png?",
            test_distro_info, test_working_dir, short_cwd_files,
            history=[], language_instruction=polish_lang_instruction
        )
        if result_search_req.success:
            if result_search_req.is_text_answer:
                print(f"Odpowiedź tekstowa AI: {result_search_req.explanation}")
            elif result_search_req.needs_file_search:
                print(f"AI prosi o przeszukanie: Wzorzec='{result_search_req.file_search_pattern}', Komunikat='{result_search_req.file_search_message}'")
            else:
                print(f"Polecenie: {result_search_req.command}\nWyjaśnienie: {result_search_req.explanation}")
        else:
            print(f"Błąd: {result_search_req.error}")


        print("\n--- Test: Generowanie polecenia na podstawie kontekstu pliku (język polski) ---")
        history_op_files = [
             {"role": "user", "parts": [{"text": "czy widzisz jakieś pliki związane ze snap w tym katalogu?"}]},
             {"role": "model", "parts": [{"text": "ODPOWIEDZ_TEKSTOWA:\nTak, widzę plik 'snap_shot_2024.jpg', który może być związany ze 'snap'."}]}
        ]
        result_op_files = gemini_client.generate_command_with_explanation(
            "zmień nazwę tego pliku snap na foto_snap.jpg",
            test_distro_info, test_working_dir, test_cwd_files,
            history=history_op_files, language_instruction=polish_lang_instruction
        )
        if result_op_files.success and not result_op_files.is_text_answer and not result_op_files.needs_file_search:
            print(f"Polecenie: {result_op_files.command}\nWyjaśnienie: {result_op_files.explanation}")
        elif result_op_files.is_text_answer:
             print(f"AI odpowiedziało tekstowo zamiast polecenia: {result_op_files.explanation}")
        elif result_op_files.needs_file_search:
             print(f"AI prosi o przeszukanie: Wzorzec='{result_op_files.file_search_pattern}', Komunikat='{result_op_files.file_search_message}'")
        else:
            print(f"Błąd: {result_op_files.error}")
