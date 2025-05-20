# src/modules/gemini_integration.py

import os
import logging
import google.generativeai as genai
import google.generativeai.types as genai_types # Główny import dla typów
from dataclasses import dataclass
from typing import Dict, Optional, List

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/linux_ai_assistant_gemini.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gemini_api")

@dataclass
class GeminiApiResponse:
    success: bool
    command: str
    explanation: str
    error: Optional[str] = None

class GeminiIntegration:
    def __init__(self, model_name: str = 'gemini-2.0-flash'):
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        self.model_name = model_name
        self.model = None

        if not self.api_key:
            logger.error("Brak klucza GOOGLE_API_KEY w zmiennych środowiskowych!")
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                logger.info(f"Skonfigurowano i zainicjalizowano model Gemini API: {self.model_name}")
            except Exception as e:
                logger.error(f"Błąd podczas konfiguracji lub inicjalizacji Gemini API: {e}", exc_info=True)
                self.api_key = None

    def generate_command(self, user_prompt: str, distro_info: Dict[str, str]) -> GeminiApiResponse:
        if not self.api_key or not self.model:
            return GeminiApiResponse(
                success=False,
                command="",
                explanation="",
                error="Klucz API Google nie został poprawnie skonfigurowany lub model nie został zainicjalizowany."
            )

        distro_context = ""
        if distro_info:
            distro_id = distro_info.get('ID', 'nieznana')
            distro_version = distro_info.get('VERSION_ID', '')
            package_manager = distro_info.get('PACKAGE_MANAGER', 'nieznany')
            distro_context = f"Działasz na dystrybucji Linux: {distro_id} {distro_version}, z menedżerem pakietów: {package_manager}."

        full_prompt_for_gemini = f"""Jesteś ekspertem od terminala Linux i Twoim zadaniem jest pomoc użytkownikowi poprzez wygenerowanie odpowiedniego polecenia.
{distro_context}
Zadanie od użytkownika: "{user_prompt}"

Wygeneruj tylko i wyłącznie jedno polecenie terminala Linux, które realizuje to zadanie.
Po poleceniu, w dokładnie następnej linii, napisz słowo kluczowe "WYJAŚNIENIE:" (bez dodatkowych znaków przed lub po).
Po słowie kluczowym "WYJAŚNIENIE:" podaj krótkie, jedno- lub dwuzdaniowe wyjaśnienie tego polecenia.
Nie dodawaj żadnych innych wstępów, opisów, przykładów ani formatowania markdown (np. ```bash).

PRZYKŁAD OCZEKIWANEJ ODPOWIEDZI:
free -h
WYJAŚNIENIE: Wyświetla informacje o użyciu pamięci RAM i swap w formacie czytelnym dla człowieka.

Twoja odpowiedź powinna ściśle przestrzegać tego formatu.
"""
        logger.debug(f"Pełny prompt dla Gemini:\n{full_prompt_for_gemini}")

        try:
            safety_settings = [
                {"category": genai_types.HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": genai_types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": genai_types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": genai_types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": genai_types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": genai_types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                {"category": genai_types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": genai_types.HarmBlockThreshold.BLOCK_ONLY_HIGH},
            ]

            generation_config = genai_types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=2048
            )

            response = self.model.generate_content(
                full_prompt_for_gemini,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            logger.debug(f"Surowa odpowiedź Gemini (obiekt): {response}")

            if not response.candidates:
                block_reason_str = "Nieznany (brak kandydatów w odpowiedzi)"
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    # Zakładamy, że BlockReason jest enumem w genai_types, jeśli nie, może wymagać innego dostępu
                    block_reason_name = getattr(genai_types.BlockReason, 'Name', lambda x: str(x))(response.prompt_feedback.block_reason)
                    block_reason_str = block_reason_name
                logger.error(f"Odpowiedź Gemini zablokowana lub pusta. Powód: {block_reason_str}")
                return GeminiApiResponse(success=False, command="", explanation="", error=f"Odpowiedź zablokowana przez Gemini: {block_reason_str}")

            current_candidate_obj = None
            # response.candidates jest iterowalny (RepeatedComposite zachowuje się jak lista)
            for cand_from_list in response.candidates:
                current_candidate_obj = cand_from_list
                break

            if current_candidate_obj is None:
                logger.error("Nie znaleziono żadnego kandydata w response.candidates.")
                return GeminiApiResponse(success=False, command="", explanation="", error="Brak kandydata w odpowiedzi Gemini.")

            finish_reason_enum = getattr(genai_types, 'FinishReason', None)

            if not hasattr(current_candidate_obj, 'finish_reason'):
                logger.error("Obiekt kandydata nie ma atrybutu 'finish_reason'.")
                return GeminiApiResponse(success=False, command="", explanation="", error="Brak 'finish_reason' w odpowiedzi kandydata.")

            if finish_reason_enum:
                 expected_finish_reasons = [finish_reason_enum.STOP, finish_reason_enum.MAX_TOKENS]
                 if current_candidate_obj.finish_reason not in expected_finish_reasons:
                     finish_reason_name = finish_reason_enum.Name(current_candidate_obj.finish_reason)
                     logger.error(f"Generowanie przez Gemini zakończone z niespodziewanym powodem: {finish_reason_name}")

                     if hasattr(current_candidate_obj, 'safety_ratings') and current_candidate_obj.safety_ratings:
                         for rating in current_candidate_obj.safety_ratings:
                             problematic_probabilities = [
                                 genai_types.HarmProbability.MEDIUM,
                                 genai_types.HarmProbability.HIGH
                             ]
                             if rating.probability in problematic_probabilities:
                                 category_name = genai_types.HarmCategory.Name(rating.category)
                                 probability_name = genai_types.HarmProbability.Name(rating.probability)
                                 logger.warning(f"Safety rating: {category_name} - {probability_name}")
                     return GeminiApiResponse(success=False, command="", explanation="", error=f"Błąd generowania przez Gemini: {finish_reason_name}")
            else:
                logger.warning("Nie udało się znaleźć definicji FinishReason enum. Pomijam dokładne sprawdzanie finish_reason.")


            if not hasattr(current_candidate_obj, 'content') or \
               not hasattr(current_candidate_obj.content, 'parts') or \
               not current_candidate_obj.content.parts:
                logger.error("Brak części (parts) w zawartości kandydata odpowiedzi Gemini.")
                return GeminiApiResponse(success=False, command="", explanation="", error="Brak zawartości tekstowej w odpowiedzi Gemini.")

            raw_text = "".join(part.text for part in current_candidate_obj.content.parts if hasattr(part, 'text')).strip()
            logger.debug(f"Tekst odpowiedzi Gemini (po strip i join): '{raw_text}'")

            command_part = ""
            explanation_part = ""
            separator = "WYJAŚNIENIE:"

            if separator in raw_text:
                parts_split = raw_text.split(separator, 1)
                command_part = parts_split[0].strip()
                if len(parts_split) > 1:
                    explanation_part = parts_split[1].strip()
            else:
                command_part = raw_text
                logger.warning("Separator 'WYJAŚNIENIE:' nie został znaleziony w odpowiedzi Gemini.")

            if not command_part:
                logger.error("Nie udało się sparsować polecenia z odpowiedzi Gemini (polecenie jest puste).")
                return GeminiApiResponse(success=False, command="", explanation="", error="Nie udało się sparsować polecenia z odpowiedzi Gemini.")

            return GeminiApiResponse(success=True, command=command_part, explanation=explanation_part)

        except Exception as e:
            logger.error(f"Wyjątek podczas komunikacji z Gemini API: {str(e)}", exc_info=True)
            return GeminiApiResponse(success=False, command="", explanation="", error=f"Wyjątek API: {str(e)}")

if __name__ == '__main__':
    if not os.environ.get('GOOGLE_API_KEY'):
        print("Proszę ustawić zmienną środowiskową GOOGLE_API_KEY")
    else:
        gemini_client = GeminiIntegration(model_name='gemini-2.0-flash')

        test_distro_info = {
            'ID': 'ubuntu',
            'VERSION_ID': '22.04',
            'PACKAGE_MANAGER': 'apt'
        }

        prompts_to_test = [
            "pokaż wszystkie pliki w bieżącym katalogu, włącznie z ukrytymi",
            "sprawdź użycie pamięci ram",
            "ile mam wolnego miejsca na dysku głównym",
            "zaktualizuj listę pakietów",
            "znajdź pliki z rozszerzeniem .log w katalogu /var/log zmodyfikowane w ciągu ostatnich 24 godzin",
            "jak utworzyć alias lsla dla ls -la w bashu"
        ]

        for p_idx, p in enumerate(prompts_to_test):
            print(f"\n--- Test [{p_idx+1}/{len(prompts_to_test)}] dla zapytania: \"{p}\" ---")
            result = gemini_client.generate_command(p, test_distro_info)
            if result.success:
                print(f"Polecenie: {result.command}")
                print(f"Wyjaśnienie: {result.explanation}")
            else:
                print(f"Błąd: {result.error}")
