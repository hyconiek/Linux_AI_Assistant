# test_errors.py
import google.genai.errors as google_genai_errors
import google.api_core.exceptions # Często tu są bardziej generyczne błędy API

print("--- Zawartość google.genai.errors: ---")
found_exceptions_in_genai_errors = []
for attr_name in dir(google_genai_errors):
    if not attr_name.startswith('_') and "Error" in attr_name: # Szukamy klas błędów
        found_exceptions_in_genai_errors.append(attr_name)
        print(attr_name)
if not found_exceptions_in_genai_errors:
    print("(brak publicznych atrybutów zawierających 'Error')")


print("\n--- Zawartość google.api_core.exceptions (dla porównania): ---")
found_exceptions_in_api_core = []
for attr_name in dir(google.api_core.exceptions):
    if not attr_name.startswith('_') and "Error" in attr_name:
        found_exceptions_in_api_core.append(attr_name)
        print(attr_name)
if not found_exceptions_in_api_core:
    print("(brak publicznych atrybutów zawierających 'Error')")


# Sprawdzenie, czy GoogleAPIError jest tam, gdzie się spodziewamy
print("\n--- Sprawdzanie konkretnych wyjątków ---")
try:
    _ = google_genai_errors.GoogleAPIError
    print("google.genai.errors.GoogleAPIError ISTNIEJE")
except AttributeError:
    print("google.genai.errors.GoogleAPIError NIE ISTNIEJE")
    # Spróbuj z google.api_core.exceptions
    try:
        _ = google.api_core.exceptions.GoogleAPIError
        print("google.api_core.exceptions.GoogleAPIError ISTNIEJE")
    except AttributeError:
        print("google.api_core.exceptions.GoogleAPIError NIE ISTNIEJE")

try:
    _ = google_genai_errors.APIError # Zgodnie z dokumentacją genai.txt dla Error Handling
    print("google.genai.errors.APIError ISTNIEJE")
except AttributeError:
    print("google.genai.errors.APIError NIE ISTNIEJE")
