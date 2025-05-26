# Plik: src/modules/gemini_integration.py

import os
import logging
import json
import re

from google import genai
from google.genai import types as genai_types
from google.genai import errors as google_genai_errors

from dataclasses import dataclass
from typing import Dict, Optional, List, Any

logger = logging.getLogger("gemini_api")

@dataclass
class GeminiApiResponse:
    success: bool
    command: Optional[str] = None
    explanation: Optional[str] = None
    error: Optional[str] = None
    analyzed_text_type: Optional[str] = None
    fix_suggestion: Optional[str] = None
    suggested_interaction_input: Optional[str] = None
    suggested_button_label: Optional[str] = None
    is_text_answer: bool = False
    needs_file_search: bool = False
    file_search_pattern: Optional[str] = None
    file_search_message: Optional[str] = None
    needs_external_terminal: bool = False
    working_dir: Optional[str] = None

class GeminiIntegration:
    def __init__(self, model_name: str = 'gemini-1.5-flash-latest'): # Użyj stabilnej nazwy modelu
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        self.model_name_str = model_name
        self.client: Optional[genai.Client] = None
        self.is_configured = False

        # Parametry dla obiektu types.GenerateContentConfig
        self.default_generation_config_params = {
            "temperature": 0.2,
            "max_output_tokens": 2048,
            "candidate_count": 1
        }
        # Safety settings jako osobny atrybut listy
        self.default_safety_settings_list = [
            genai_types.SafetySetting(category=cat, threshold=thresh)
            for cat, thresh in [
                (genai_types.HarmCategory.HARM_CATEGORY_HARASSMENT, genai_types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
                (genai_types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, genai_types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
                (genai_types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, genai_types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
                (genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH),
            ]
        ]

        if not self.api_key:
            logger.error("Brak klucza GOOGLE_API_KEY w zmiennych środowiskowych!")
        else:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.is_configured = True
                logger.info(f"Klient Gemini API zainicjalizowany. Model domyślny ustawiony na: {self.model_name_str}")
            except Exception as e:
                logger.error(f"Błąd podczas inicjalizacji klienta Gemini API (genai.Client): {e}", exc_info=True)
                self.client = None
                self.is_configured = False

    def _convert_legacy_history_to_new_format(self, history: Optional[List[Dict[str, Any]]]) -> List[genai_types.Content]:
        if not history: return []
        new_history: List[genai_types.Content] = []
        for entry in history:
            role = entry.get("role", "user")
            parts_data = entry.get("parts", [])
            current_parts_for_content: List[genai_types.Part] = []
            if isinstance(parts_data, list) and parts_data:
                for part_entry in parts_data:
                    text_content = ""
                    if isinstance(part_entry, dict): text_content = part_entry.get("text", "")
                    elif isinstance(part_entry, str): text_content = part_entry
                    if text_content: current_parts_for_content.append(genai_types.Part.from_text(text=text_content))
            if current_parts_for_content:
                valid_role = "model" if role.lower() == "model" else "user"
                new_history.append(genai_types.Content(parts=current_parts_for_content, role=valid_role))
        return new_history

    def _send_request_to_gemini(self,
                                contents_arg: Any,
                                is_chat: bool = False,
                                chat_session: Optional[Any] = None, # google.genai.ChatSession
                                system_instruction_for_non_chat: Optional[str] = None
                                ) -> GeminiApiResponse:
        if not self.is_configured or not self.client:
            return GeminiApiResponse(success=False, error="Klient API Google nie skonfigurowany.")
        try:
            response: genai_types.GenerateContentResponse
            if is_chat and chat_session:
                content_to_send_in_chat: Any
                if isinstance(contents_arg, str): content_to_send_in_chat = contents_arg
                elif isinstance(contents_arg, genai_types.Content): content_to_send_in_chat = contents_arg.parts
                elif isinstance(contents_arg, list) and all(isinstance(p, genai_types.Part) for p in contents_arg): content_to_send_in_chat = contents_arg
                else: content_to_send_in_chat = str(contents_arg)

                # Dla czatu, konfiguracja i safety settings są zwykle ustawiane podczas tworzenia sesji
                # lub dziedziczone z modelu. send_message ich nie przyjmuje.
                # Jednak jeśli chcemy je dynamicznie zmieniać dla każdej wiadomości w czacie (co nie jest typowe dla tego SDK),
                # musielibyśmy prawdopodobnie tworzyć nową sesję czatu z nową konfiguracją, co jest nieefektywne.
                # Na razie zakładamy, że konfiguracja sesji czatu jest wystarczająca.
                # Jeśli `chat_session.send_message` w Twojej wersji SDK *przyjmuje* `generation_config` i `safety_settings`,
                # możesz je tutaj dodać, ale dokumentacja, którą widziałem, tego nie sugeruje.
                # Sprawdźmy dokumentację dla `chat_session.send_message` dla google-genai 1.16.1.
                # Jeśli nie, to te ustawienia są brane z `self.client.chats.create` (czyli z modelu).
                # Dla pewności można by jawnie tworzyć `GenerationConfig` i `SafetySettings` dla czatu,
                # ale tylko jeśli `send_message` je akceptuje.
                # Zostawmy na razie tak, jak było - jeśli będą problemy z bezpieczeństwem/konfiguracją czatu,
                # będziemy musieli to zbadać głębiej.

                response = chat_session.send_message(content_to_send_in_chat)
            else: # non-chat
                # Przygotuj config_dict
                config_dict = self.default_generation_config_params.copy()
                if system_instruction_for_non_chat:
                    config_dict["system_instruction"] = system_instruction_for_non_chat

                # --- POPRAWKA TUTAJ ---
                # Safety settings powinny być częścią obiektu GenerateContentConfig
                # przekazywanego do argumentu `config` w `client.models.generate_content`.
                config_dict["safety_settings"] = self.default_safety_settings_list

                current_content_config = genai_types.GenerateContentConfig(**config_dict)

                response = self.client.models.generate_content(
                    model=self.model_name_str,
                    contents=contents_arg,
                    config=current_content_config, # Przekaż JEDEN obiekt config
                    # safety_settings=self.default_safety_settings_list # USUNIĘTE STĄD
                )

            logger.debug(f"Gemini: Surowa odpowiedź: {response}")

            if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                reason_name = response.prompt_feedback.block_reason.name
                logger.error(f"Odpowiedź Gemini zablokowana (prompt_feedback). Powód: {reason_name}")
                return GeminiApiResponse(success=False, error=f"Odpowiedź zablokowana przez AI (prompt): {reason_name}")
            if not response.candidates:
                logger.error("Odpowiedź Gemini pusta (brak kandydatów).")
                return GeminiApiResponse(success=False, error="Odpowiedź AI pusta (brak kandydatów).")

            candidate = response.candidates[0]

            if hasattr(candidate, 'finish_reason') and candidate.finish_reason not in [genai_types.FinishReason.STOP, genai_types.FinishReason.MAX_TOKENS, genai_types.FinishReason.FINISH_REASON_UNSPECIFIED, genai_types.FinishReason.OTHER, None]:
                finish_reason_name = candidate.finish_reason.name
                logger.error(f"Generowanie kandydata zatrzymane z powodu: {finish_reason_name}.")
                safety_block_info = f" Kandydat zablokowany: {finish_reason_name}."
                if candidate.safety_ratings:
                    blocked_categories = [str(sr.category.name) for sr in candidate.safety_ratings if hasattr(sr, 'probability') and sr.probability.name in ["HIGH", "MEDIUM"]]
                    if blocked_categories: safety_block_info += f" Kategorie bezpieczeństwa: {', '.join(blocked_categories)}."
                return GeminiApiResponse(success=False, error=f"Błąd generowania AI: {finish_reason_name}.{safety_block_info}")

            raw_text = response.text
            if raw_text is None:
                 if candidate.content and candidate.content.parts:
                     raw_text = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text')).strip()
                 else:
                    logger.error("Brak części (parts) lub tekstu w zawartości odpowiedzi Gemini.")
                    return GeminiApiResponse(success=False, error="Brak zawartości tekstowej w odpowiedzi AI.")
            return GeminiApiResponse(success=True, explanation=raw_text)

        except google_genai_errors.APIError as api_err:
            error_message = str(api_err)
            if hasattr(api_err, 'message') and api_err.message: error_message = api_err.message
            block_indicators = ["blocked due to safety", "prompt was blocked", "candidate was blocked", "finish_reason: SAFETY"]
            is_blocked_by_message = any(indicator in error_message.lower() for indicator in block_indicators)
            if is_blocked_by_message:
                logger.error(f"Zapytanie zablokowane przez AI (wykryte z APIError): {error_message}", exc_info=True)
                return GeminiApiResponse(success=False, error=f"Zapytanie zablokowane przez AI: {error_message[:150]}")
            logger.error(f"Wyjątek APIError (google.genai.errors) podczas komunikacji z Gemini: {error_message}", exc_info=True)
            return GeminiApiResponse(success=False, error=f"Błąd API Gemini (genai): {error_message[:150]}")
        except Exception as e:
            logger.error(f"Nieznany wyjątek podczas komunikacji z Gemini API: {str(e)}", exc_info=True)
            if "DeadlineExceeded" in str(e) or "unavailable" in str(e).lower():
                return GeminiApiResponse(success=False, error=f"Błąd sieci lub usługa Gemini niedostępna: {str(e)}")
            if isinstance(e, TypeError) and "got an unexpected keyword argument" in str(e): # Błąd konfiguracji
                return GeminiApiResponse(success=False, error=f"Błąd konfiguracji wywołania API Gemini (TypeError): {e}")
            return GeminiApiResponse(success=False, error=f"Wyjątek API: {str(e)}")

    def generate_command_with_explanation(self, user_prompt: str, distro_info: Dict[str, str],
                                           working_dir: Optional[str] = None,
                                           cwd_file_list: Optional[List[str]] = None,
                                           history: Optional[List[Dict[str, Any]]] = None,
                                           language_instruction: Optional[str] = None) -> GeminiApiResponse:
        if not self.is_configured or not self.client:
            return GeminiApiResponse(success=False, error="Model Gemini nie został poprawnie zainicjalizowany.")

        distro_context = f"Dystrybucja: {distro_info.get('ID', 'nieznana')} {distro_info.get('VERSION_ID', '')}, Menedżer pakietów: {distro_info.get('PACKAGE_MANAGER', 'nieznany')}."
        wd_context = f"Aktualny katalog roboczy: {working_dir}" if working_dir else "Katalog roboczy nieznany."
        lang_instr = language_instruction if language_instruction else "Respond in English."
        cwd_files_info = "Brak informacji o plikach/katalogach w CWD."
        if cwd_file_list:
            file_limit = 30; temp_list = [f for f in cwd_file_list if f]
            if len(temp_list) > file_limit:
                cwd_files_info = f"Dostępne pliki i katalogi w bieżącym katalogu roboczym ({working_dir}) (pierwsze {file_limit}): {', '.join(temp_list[:file_limit])}, ..."
            elif temp_list:
                 cwd_files_info = f"Dostępne pliki i katalogi w bieżącym katalogu roboczym ({working_dir}): {', '.join(temp_list)}."
            else:
                 cwd_files_info = f"Brak plików/katalogów w bieżącym katalogu roboczym ({working_dir})."

        formatted_history_for_prompt = ""
        if history:
            for entry in history:
                role = entry.get("role", "user")
                parts_list = entry.get("parts", [])
                text_content_hist_entry = ""
                if isinstance(parts_list, list) and parts_list:
                    first_part = parts_list[0]
                    if isinstance(first_part, dict): text_content_hist_entry = first_part.get("text", "")
                if text_content_hist_entry: formatted_history_for_prompt += f"{role.capitalize()}: {text_content_hist_entry}\n"
        if not formatted_history_for_prompt: formatted_history_for_prompt = "Brak historii."

        system_instruction_template = """Jesteś ekspertem od terminala Linux. Twoim zadaniem jest pomoc użytkownikowi przez wygenerowanie odpowiedniego polecenia LUB odpowiedź na pytanie dotyczące plików w katalogu.
Kontekst systemu: {distro_context} {wd_context}
{cwd_files_info}
{lang_instr}

Historia konwersacji (jeśli istnieje):
{formatted_history_for_prompt}

ZASADY:
1. Jeśli zapytanie użytkownika jest PROŚBĄ O WYKONANIE AKCJI (np. "pokaż pliki", "zainstaluj coś", "usuń plik.txt", "rozjaśnij obraz.jpg"), wygeneruj polecenie.
   - Jeśli użytkownik wpisze nazwę pliku z literówką lub złą wielkością liter, ale na liście plików z CWD (lub z historii wyszukiwania) jest pasujący plik, użyj poprawnej nazwy z listy w poleceniu.
   - Jeśli użytkownik odnosi się do pliku wspomnianego wcześniej w historii konwersacji (np. "ten plik", "obrazek"), użyj nazwy tego pliku w poleceniu.
   - Format odpowiedzi dla polecenia:
     NAJPIERW linia z poleceniem.
     W DOKŁADNIE NASTĘPNEJ linii słowo kluczowe "WYJAŚNIENIE:"
     Po "WYJAŚNIENIE:" krótkie wyjaśnienie polecenia.
     OPCJONALNIE, jeśli polecenie może wymagać interakcji (np. pytanie T/N bez flagi -y), w NASTĘPNEJ linii "INTERAKCJA_POLECENIE: sugerowana_odpowiedź;Etykieta Przycisku"
     LUB jeśli polecenie jest programem pełnoekranowym/interaktywnym (np. top, htop, nano, vim, less, man), w NASTĘPNEJ linii "INTERAKCJA_TERMINAL: ;Uruchom w nowym terminalu"
     Przykład (instalacja z -y):
       sudo apt install -y firefox
       WYJAŚNIENIE: Instaluje Firefox, automatycznie potwierdzając.
     Przykład (instalacja bez -y, sugestia dla GUI):
       sudo apt install gimp
       WYJAŚNIENIE: Przygotowuje instalację GIMP, system zapyta o potwierdzenie.
       INTERAKCJA_POLECENIE: t;Zainstaluj GIMP (potwierdź T)
     Przykład (top):
       top
       WYJAŚNIENIE: Wyświetla dynamiczny, rzeczywisty widok działających procesów.
       INTERAKCJA_TERMINAL: ;Uruchom 'top' w terminalu

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

Nie dodawaj nic więcej, żadnych wstępów, markdown, poza wymaganym formatem."""
        system_instruction_formatted = system_instruction_template.format(
            distro_context=distro_context, wd_context=wd_context,
            cwd_files_info=cwd_files_info, lang_instr=lang_instr,
            formatted_history_for_prompt=formatted_history_for_prompt
        )

        new_sdk_history = self._convert_legacy_history_to_new_format(history)

        # Tworzenie sesji czatu. Konfiguracja safety/generation jest dziedziczona z klienta/modelu.
        # Dla czatu, system_instruction jest często częścią pierwszej tury użytkownika lub specjalnej tury 'system'.
        # Tutaj dołączamy ją do pierwszej tury użytkownika.
        # Historia `new_sdk_history` powinna być przekazana tutaj, jeśli ma być użyta.
        chat_session = self.client.chats.create(
            model=self.model_name_str,
            history=new_sdk_history,
            # Safety settings i generation config są stosowane na poziomie klienta lub modelu,
            # ale dla sesji czatu można je też (w niektórych wersjach/sposobach SDK) przekazać tu.
            # Jednak najnowsze SDK zdaje się preferować, by były one częścią `client.chat(...)` lub dziedziczone.
            # Sprawdzimy, czy przekazanie ich tutaj jest konieczne lub poprawne dla `client.chats.create`.
            # Według dokumentacji `google-genai==0.5.4` (na którą patrzę), `chats.create` nie przyjmuje
            # `safety_settings` ani `generation_config` bezpośrednio. Są one częścią `send_message` dla ChatSession,
            # lub `generate_content` dla `GenerativeModel`.
            # Dla client.chats.create, dziedziczy z modelu.
        )
        # Jeśli chcemy użyć system_instruction w czacie, musi być jako pierwsza tura w historii
        # lub połączona z pierwszym zapytaniem użytkownika.
        # Tutaj łączymy ją z zapytaniem użytkownika.

        current_turn_content_str = f"{system_instruction_formatted}\n\nZadanie/Pytanie od użytkownika: \"{user_prompt}\"\n"
        logger.debug(f"Pełny prompt dla Gemini (generate_command_with_explanation - chat turn):\n{current_turn_content_str[:1000]}...")

        api_response_wrapper = self._send_request_to_gemini(
            contents_arg=current_turn_content_str, # String jest automatycznie konwertowany na Part przez SDK
            is_chat=True,
            chat_session=chat_session
            # Nie przekazujemy system_instruction_for_non_chat, bo to jest czat
        )

        if not api_response_wrapper.success or not api_response_wrapper.explanation:
            return GeminiApiResponse(success=False, error=api_response_wrapper.error or "Brak odpowiedzi od AI", working_dir=working_dir)
        raw_text = api_response_wrapper.explanation; logger.debug(f"Surowy tekst odpowiedzi Gemini (po _send_request): {raw_text}")
        if raw_text.strip() == "CLARIFY_REQUEST": return GeminiApiResponse(success=False, error="CLARIFY_REQUEST", working_dir=working_dir)
        if raw_text.strip() == "DANGEROUS_REQUEST": return GeminiApiResponse(success=False, error="DANGEROUS_REQUEST", working_dir=working_dir)
        lines = raw_text.split('\n')
        if lines and lines[0].strip().startswith("SZUKAJ_PLIKOW:"):
            content = lines[0].strip()[len("SZUKAJ_PLIKOW:"):].strip(); pattern, message = "", "Rozpoczynam wyszukiwanie plików..."
            if ";" in content: pattern, message = map(str.strip, content.split(";", 1))
            else: pattern = content
            logger.info(f"AI zażądało przeszukania plików: wzorzec='{pattern}', komunikat='{message}'")
            return GeminiApiResponse(success=True, needs_file_search=True, file_search_pattern=pattern if pattern else "*", file_search_message=message, needs_external_terminal=False, working_dir=working_dir)
        if lines and lines[0].strip() == "ODPOWIEDZ_TEKSTOWA:":
            text_answer = "\n".join(lines[1:]).strip(); logger.info(f"AI odpowiedziało tekstowo: {text_answer}")
            return GeminiApiResponse(success=True, explanation=text_answer, is_text_answer=True, needs_external_terminal=False, working_dir=working_dir)

        command_part = lines[0].strip() if lines else ""
        explanation_part = ""
        interaction_input, button_label = None, None
        needs_ext_term = False

        if command_part.lower().startswith("polecenie:"):
            command_part = command_part[len("polecenie:") :].strip()
        elif command_part.lower().startswith("command:"):
            command_part = command_part[len("command:") :].strip()

        default_lang_name = "English"
        if "polski" in lang_instr.lower(): default_lang_name = "Polski"
        elif "česky" in lang_instr.lower() or "češtině" in lang_instr.lower(): default_lang_name = "Česky"
        default_explanation_on_format_error = f"({default_lang_name}: AI nie dostarczyło wyjaśnienia w oczekiwanym formacie)"

        idx = 1
        if idx < len(lines) and lines[idx].strip().startswith("WYJAŚNIENIE:"):
            explanation_content = lines[idx].strip()[len("WYJAŚNIENIE:"):].strip(); idx += 1
            while idx < len(lines) and not lines[idx].strip().startswith("INTERAKCJA_POLECENIE:") and not lines[idx].strip().startswith("INTERAKCJA_TERMINAL:"):
                explanation_content += "\n" + lines[idx].strip(); idx += 1
            explanation_part = explanation_content.strip()

            if idx < len(lines):
                if lines[idx].strip().startswith("INTERAKCJA_POLECENIE:"):
                    interaction_line_content = lines[idx].strip()[len("INTERAKCJA_POLECENIE:"):].strip()
                    if ";" in interaction_line_content: interaction_input, button_label = map(str.strip, interaction_line_content.split(";", 1))
                    else: interaction_input = interaction_line_content; button_label = f"Wykonaj ({interaction_input})" if interaction_input else "Wykonaj"
                elif lines[idx].strip().startswith("INTERAKCJA_TERMINAL:"):
                    needs_ext_term = True
                    interaction_line_content = lines[idx].strip()[len("INTERAKCJA_TERMINAL:"):].strip()
                    interaction_input = "TERMINAL_REQUIRED"
                    if ";" in interaction_line_content: _, button_label = map(str.strip, interaction_line_content.split(";", 1))
                    else: button_label = interaction_line_content if interaction_line_content else "Uruchom w terminalu"

        elif command_part: explanation_part = default_explanation_on_format_error
        elif not command_part and not explanation_part and raw_text:
            logger.warning(f"AI zwróciło tekst bez standardowego formatowania polecenia/odpowiedzi. Traktuję jako odpowiedź tekstową: '{raw_text}'")
            return GeminiApiResponse(success=True, explanation=raw_text, is_text_answer=True, needs_external_terminal=False, working_dir=working_dir)

        if not command_part and not explanation_part and not raw_text.strip():
             logger.error(f"Nie udało się sparsować odpowiedzi AI, była pusta: '{raw_text}'")
             return GeminiApiResponse(success=False, error="Nie udało się sparsować odpowiedzi AI (pusta).", working_dir=working_dir)
        if not explanation_part.strip() and command_part: explanation_part = default_explanation_on_format_error

        return GeminiApiResponse(success=True, command=command_part, explanation=explanation_part,
                                 suggested_interaction_input=interaction_input,
                                 suggested_button_label=button_label,
                                 is_text_answer=False if command_part else True,
                                 needs_external_terminal=needs_ext_term, working_dir=working_dir)


    def analyze_text_input_type(self, text_input: str, language_instruction: Optional[str] = None) -> GeminiApiResponse:
        if not self.is_configured or not self.client:
            return GeminiApiResponse(success=False, error="Model Gemini nie zainicjalizowany.", analyzed_text_type="error")
        lang_instr = language_instruction if language_instruction else "Respond in English."
        system_prompt_for_analysis = f"""Przeanalizuj poniższy tekst wejściowy użytkownika i określ jego typ.
{lang_instr}
Odpowiedz TYLKO w formacie JSON z kluczami "type" i "explanation".
Możliwe wartości dla "type": "linux_command", "natural_language_query", "question_about_cwd", "other".
Jeśli "type" to "linux_command", "explanation" powinno być krótkim opisem tego polecenia.
Jeśli "type" to "natural_language_query", "explanation" może być puste lub zawierać krótkie podsumowanie zapytania.
Jeśli "type" to "question_about_cwd", "explanation" powinno wskazywać, że to pytanie o pliki.
Jeśli "type" to "other", "explanation" powinno być puste.
"""
        # contents_arg dla generate_content może być stringiem, SDK opakuje go
        contents_for_analysis = f"Tekst wejściowy: \"{text_input}\""

        api_response_wrapper = self._send_request_to_gemini(
            contents_arg=contents_for_analysis,
            is_chat=False,
            system_instruction_for_non_chat=system_prompt_for_analysis # Przekaż instrukcję systemową tutaj
        )
        if not api_response_wrapper.success or not api_response_wrapper.explanation:
            return GeminiApiResponse(success=False, error=api_response_wrapper.error or "Brak odpowiedzi od AI (analiza typu)", analyzed_text_type="error")

        raw_ai_response_text = api_response_wrapper.explanation
        match = re.search(r"```json\s*(\{.*?\})\s*```", raw_ai_response_text, re.DOTALL)
        if match: cleaned_json_text = match.group(1).strip()
        else: cleaned_json_text = raw_ai_response_text.replace("```json", "").replace("```", "").strip()

        try:
            analysis_result = json.loads(cleaned_json_text)
            text_type = analysis_result.get("type", "other"); explanation = analysis_result.get("explanation", "")
            return GeminiApiResponse(success=True, explanation=explanation, analyzed_text_type=text_type, needs_external_terminal=False)
        except json.JSONDecodeError:
            logger.error(f"Błąd parsowania JSON z analizy typu tekstu. Oryginał: '{raw_ai_response_text}'. Oczyszczony: '{cleaned_json_text}'")
            return GeminiApiResponse(success=False, error="Błąd parsowania odpowiedzi AI (analiza typu nie jest JSON).", analyzed_text_type="error", needs_external_terminal=False)
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas analizy typu tekstu: {e}", exc_info=True)
            return GeminiApiResponse(success=False, error=f"Nieoczekiwany błąd: {e}", analyzed_text_type="error", needs_external_terminal=False)

    def generate_clarification_questions(self, complex_query: str, distro_info: Dict[str, str],
                                         working_dir: Optional[str],
                                         language_instruction: Optional[str] = None) -> List[str]:
        if not self.is_configured or not self.client:
            logger.error("Model Gemini nie zainicjalizowany (pytania doprecyzowujące).")
            return []
        distro_context = f"Dystrybucja: {distro_info.get('ID', 'nieznana')}."; wd_context = f"Katalog roboczy: {working_dir}." if working_dir else ""
        lang_instr = language_instruction if language_instruction else "Generate questions in English."

        system_prompt_for_clarification = f"""Użytkownik zadał złożone lub niejasne zapytanie dotyczące Linuksa.
Kontekst: {distro_context} {wd_context}
{lang_instr}
Twoim zadaniem jest wygenerowanie 2-3 krótkich, precyzyjnych pytań, które pomogą użytkownikowi doprecyzować jego intencje.
Pytania powinny być sformułowane tak, aby odpowiedzi na nie pozwoliły na wygenerowanie konkretnego polecenia.
Zwróć TYLKO listę pytań, każde w nowej linii (w języku z instrukcji). Nie dodawaj numeracji ani żadnych innych komentarzy.
Jeśli uważasz, że zapytanie jest wystarczająco jasne i nie wymaga dopytywania, zwróć pustą odpowiedź lub pojedynczą linię "NO_CLARIFICATION_NEEDED".
"""
        contents_for_clarification = f"Zapytanie użytkownika: \"{complex_query}\""

        api_response_wrapper = self._send_request_to_gemini(
            contents_arg=contents_for_clarification,
            is_chat=False,
            system_instruction_for_non_chat=system_prompt_for_clarification
        )
        if not api_response_wrapper.success or not api_response_wrapper.explanation:
            logger.error(f"Błąd generowania pytań doprecyzowujących: {api_response_wrapper.error}"); return []
        raw_text = api_response_wrapper.explanation.strip()
        if not raw_text or raw_text == "NO_CLARIFICATION_NEEDED": return []
        questions = [q.strip() for q in raw_text.split('\n') if q.strip()]
        logger.info(f"Gemini: Wygenerowane pytania doprecyzowujące: {questions}"); return questions

    def analyze_execution_error_and_suggest_fix(
        self, command_str: str, stderr: str, return_code: int,
        distro_info: Dict[str, str], working_dir: Optional[str],
        language_instruction: Optional[str] = None
    ) -> GeminiApiResponse:
        if not self.is_configured or not self.client:
            return GeminiApiResponse(success=False, command=command_str, error="Model Gemini nie zainicjalizowany (analiza błędu).")
        if not stderr and return_code == 0:
            return GeminiApiResponse(success=True, command=command_str, explanation="", fix_suggestion="Brak błędu do analizy.", needs_external_terminal=False)

        distro_context = f"Dystrybucja: {distro_info.get('ID', 'nieznana')} {distro_info.get('VERSION_ID', '')}, Menedżer pakietów: {distro_info.get('PACKAGE_MANAGER', 'nieznany')}."
        wd_context = f"Katalog roboczy: {working_dir}" if working_dir else "Katalog roboczy nieznany."
        lang_instr = language_instruction if language_instruction else "Provide analysis in English."
        default_lang_name = "English"
        if "polski" in lang_instr.lower(): default_lang_name = "Polski"
        elif "česky" in lang_instr.lower() or "češtině" in lang_instr.lower(): default_lang_name = "Česky"

        system_prompt_for_error_analysis = f"""Przeanalizuj ten błąd. Podaj:
1.  Prawdopodobną przyczynę błędu (krótko, 1-2 zdania, w języku z instrukcji).
2.  Proponowane kroki naprawcze lub alternatywne polecenia (jeśli to możliwe, podaj konkretne polecenia, w języku z instrukcji).

Odpowiedz TYLKO w formacie JSON z jednym kluczem "fix_suggestion", którego wartością jest string zawierający analizę i sugestie (w języku z instrukcji).
Przykład odpowiedzi JSON (jeśli język to polski):
{{"fix_suggestion": "Przyczyna: Prawdopodobnie brak uprawnień do zapisu w danym katalogu lub plik nie istnieje.\\nSugestie:\\n1. Sprawdź uprawnienia: `ls -ld /sciezka/do/katalogu`\\n2. Spróbuj wykonać polecenie z `sudo`: `sudo {command_str}`\\n3. Upewnij się, że plik/katalog docelowy istnieje."}}

Jeśli błąd jest zbyt ogólny, w "fix_suggestion" napisz (w języku z instrukcji): "Nie można jednoznacznie zdiagnozować problemu. Sprawdź komunikat błędu i uprawnienia."
"""
        contents_for_error_analysis = f"""Użytkownik próbował wykonać następujące polecenie Linux:
`{command_str}`

Polecenie zakończyło się z kodem wyjścia: {return_code}
Standardowe wyjście błędów (stderr) było następujące (jeśli puste, oznacza brak stderr):
--- STDERR START ---
{stderr.strip() if stderr else "Brak stderr."}
--- STDERR END ---

Kontekst systemu: {distro_context} {wd_context}
{lang_instr}
"""
        logger.debug(f"Gemini: Prompt dla analizy błędu (bez instrukcji systemowej):\n{contents_for_error_analysis}")

        api_response_wrapper = self._send_request_to_gemini(
            contents_arg=contents_for_error_analysis,
            is_chat=False,
            system_instruction_for_non_chat=system_prompt_for_error_analysis
        )
        if not api_response_wrapper.success or not api_response_wrapper.explanation:
            return GeminiApiResponse(success=False, command=command_str, error=f"Błąd generowania sugestii naprawczej: {api_response_wrapper.error or 'Brak odpowiedzi AI'}", needs_external_terminal=False)

        raw_ai_response_text = api_response_wrapper.explanation
        match = re.search(r"```json\s*(\{.*?\})\s*```", raw_ai_response_text, re.DOTALL)
        if match: cleaned_json_text = match.group(1).strip()
        else: cleaned_json_text = raw_ai_response_text.replace("```json", "").replace("```", "").strip()
        logger.debug(f"Gemini: Oczyszczony JSON (fix_suggestion): '{cleaned_json_text}'")

        try:
            analysis_result = json.loads(cleaned_json_text)
            suggestion = analysis_result.get("fix_suggestion", f"({default_lang_name}: AI nie dostarczyło sugestii w oczekiwanym formacie.)")
            return GeminiApiResponse(success=True, command=command_str, fix_suggestion=suggestion, needs_external_terminal=False)
        except json.JSONDecodeError as json_err:
            logger.error(f"Błąd parsowania JSON z sugestią. Oryginał: '{raw_ai_response_text}'. Oczyszczony: '{cleaned_json_text}'. Błąd: {json_err}")
            return GeminiApiResponse(success=True, command=command_str, fix_suggestion=f"({default_lang_name}: AI zwróciło niepoprawny format JSON. Odpowiedź: {raw_ai_response_text}", needs_external_terminal=False)
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd analizy błędu: {e}", exc_info=True)
            return GeminiApiResponse(success=False, command=command_str, error=f"Nieoczekiwany błąd sugestii: {e}", needs_external_terminal=False)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
    if not os.environ.get('GOOGLE_API_KEY'):
        print("Proszę ustawić zmienną środowiskową GOOGLE_API_KEY do testów.")
    else:
        gemini_client = GeminiIntegration(model_name='gemini-1.5-flash-latest')
        if not gemini_client.is_configured:
            print(f"Nie udało się skonfigurować klienta Gemini dla modelu '{gemini_client.model_name_str}'. Sprawdź logi i klucz API oraz dostępność modelu.")
        else:
            test_distro_info = {'ID': 'ubuntu', 'VERSION_ID': '22.04', 'PACKAGE_MANAGER': 'apt'}
            test_working_dir = "/home/user/projects"
            polish_lang_instruction = "ODPOWIADAJ ZAWSZE W JĘZYKU POLSKIM."

            print("\n--- Test: 'pokaż obciążenie procesora' (język polski) ---")
            result_top_test = gemini_client.generate_command_with_explanation(
                "pokaż obciążenie procesora",
                test_distro_info, test_working_dir, ["plik1.txt", "dokument.pdf"],
                history=[], language_instruction=polish_lang_instruction
            )
            if result_top_test.success:
                if result_top_test.is_text_answer: print(f"Odpowiedź tekstowa AI: {result_top_test.explanation}")
                elif result_top_test.needs_file_search: print(f"AI prosi o przeszukanie: Wzorzec='{result_top_test.file_search_pattern}', Komunikat='{result_top_test.file_search_message}'")
                elif result_top_test.command:
                    print(f"Polecenie: {result_top_test.command}\nWyjaśnienie: {result_top_test.explanation}")
                    if result_top_test.needs_external_terminal:
                        print(f"Wymaga zewnętrznego terminala. Sugerowana etykieta: {result_top_test.suggested_button_label}")
                    elif result_top_test.suggested_interaction_input:
                        print(f"Sugerowana interakcja: {result_top_test.suggested_interaction_input}, Etykieta: {result_top_test.suggested_button_label}")
                else: print(f"Sukces, ale brak polecenia lub odpowiedzi tekstowej. Wyjaśnienie: {result_top_test.explanation}")
            else: print(f"Błąd dla 'pokaż obciążenie procesora': {result_top_test.error}")
