import sys
import os
import traceback

# Add src to sys.path
current_dir = os.getcwd()
src_path = os.path.join(current_dir, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print(f"Current working directory: {current_dir}")
print(f"sys.path: {sys.path}")

try:
    from modules.gemini_integration import GeminiIntegration
    print("Successfully imported GeminiIntegration")
except ImportError as e:
    print(f"ImportError: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"An error occurred: {e}")
    traceback.print_exc()

print("\n--- Testing Translation Loading ---")
from PyQt5.QtCore import QTranslator, QCoreApplication
import sys

# Create QCoreApplication if not already exists (needed for QTranslator)
if not QCoreApplication.instance():
    app = QCoreApplication(sys.argv)

translator = QTranslator()
translations_dir = os.path.join(current_dir, "translations")
translation_file = "linux_ai_assistant_gui_pl.qm"
translation_path = os.path.join(translations_dir, translation_file)

print(f"Checking translation path: {translation_path}")
if os.path.exists(translation_path):
    print("File exists.")
    if translator.load(translation_path):
        print("Successfully loaded translation.")
    else:
        print("Failed to load translation (translator.load returned False).")
else:
    print("File does not exist.")
