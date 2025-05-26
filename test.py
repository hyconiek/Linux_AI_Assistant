import os
from google import genai
from google.genai import types

API_KEY = "AIzaSyDxPrM3dGKsVJ0D69JLS0fT5Y91TnqeHMM" # WSTAW TUTAJ
PROJECT_ID = "twoj-projekt-id" # Jeśli używasz Vertex AI, inaczej niepotrzebne dla Gemini Developer API

def test_gemini_chat():
    print(f"Google GenAI SDK Version: {genai.__version__}")
    try:
        # Dla Gemini Developer API
        client = genai.Client(api_key=API_KEY)

        # Dla Vertex AI API (odkomentuj i skonfiguruj, jeśli potrzebujesz)
        # client = genai.Client(vertexai=True, project=PROJECT_ID, location='us-central1')

        print(f"Klient utworzony. Model: gemini-2.5-flash-preview-05-20")

        # Przygotowanie historii
        legacy_history = [
            {"role": "user", "parts": [{"text": "What is the capital of France?"}]},
            {"role": "model", "parts": [{"text": "The capital of France is Paris."}]}
        ]

        new_sdk_history = []
        for entry in legacy_history:
            role = entry.get("role", "user")
            parts_data = entry.get("parts", [])
            current_parts_for_content = []
            if isinstance(parts_data, list) and parts_data:
                for part_entry in parts_data:
                    text_content = ""
                    if isinstance(part_entry, dict):
                        text_content = part_entry.get("text", "")
                    elif isinstance(part_entry, str):
                        text_content = part_entry
                    if text_content:
                        current_parts_for_content.append(types.Part.from_text(text=text_content)) # Jawne text=
            if current_parts_for_content:
                valid_role = "model" if role.lower() == "model" else "user"
                new_sdk_history.append(types.Content(parts=current_parts_for_content, role=valid_role))

        print(f"Skonwertowana historia: {new_sdk_history}")

        chat_session = client.chats.create(model='gemini-2.5-flash-preview-05-20', history=new_sdk_history or [])
        print("Sesja czatu utworzona.")

        user_message_str = "And what is its population?"
        print(f"Wysyłanie wiadomości: '{user_message_str}'")

        # Opakowanie stringa w listę Part
        content_to_send = [types.Part.from_text(text=user_message_str)]

        response = chat_session.send_message(content_to_send) # Przekazanie List[Part]
        print(f"Odpowiedź AI: {response.text}")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_gemini_chat()
