# Badanie dostępnych darmowych API online dla poleceń Linuxa

## Przegląd rozwiązań open-source

### 1. BuilderIO/ai-shell

**Opis:** CLI konwertujące język naturalny na polecenia powłoki.

**Zalety:**
- Lekkie i łatwe w instalacji (`npm install -g @builder.io/ai-shell`)
- Obsługuje wiele języków (w tym polski)
- Aktywnie rozwijane (4.8k gwiazdek na GitHub)
- Dobra dokumentacja
- Intuicyjny interfejs z wyjaśnieniami poleceń

**Wady:**
- Wymaga klucza API OpenAI (darmowy, ale z limitami)
- Zależność od zewnętrznego API może powodować opóźnienia
- Potencjalne koszty przy intensywnym użytkowaniu

**Integracja:** Prosta instalacja przez npm, wymaga Node.js v14+

### 2. TheR1D/shell_gpt (ShellGPT)

**Opis:** Narzędzie zwiększające produktywność w wierszu poleceń, napędzane przez modele AI.

**Zalety:**
- Rozbudowane opcje konfiguracji
- Obsługa wielu modeli (domyślnie GPT-4o)
- Możliwość zapisywania konwersacji i tworzenia ról systemowych
- Większa społeczność (10.9k gwiazdek na GitHub)
- Regularne aktualizacje i wydania

**Wady:**
- Wymaga klucza API OpenAI
- Bardziej złożona konfiguracja
- Potencjalne koszty przy intensywnym użytkowaniu

**Integracja:** Instalacja przez pip (Python)

### 3. Eden AI

**Opis:** Platforma agregująca różne API AI, w tym NLP.

**Zalety:**
- Dostęp do wielu dostawców AI przez jedno API
- Darmowe kredyty na start ($10)
- Szeroki zakres funkcji NLP

**Wady:**
- Nie jest specjalizowane pod kątem poleceń terminalowych
- Wymaga dodatkowej implementacji dla specyficznych przypadków użycia
- Potencjalne koszty po wykorzystaniu darmowych kredytów

**Integracja:** REST API z kluczem API

## Porównanie rozwiązań

| Cecha | BuilderIO/ai-shell | ShellGPT | Eden AI |
|-------|-------------------|----------|---------|
| Specjalizacja pod kątem poleceń terminalowych | ✅ Wysoka | ✅ Wysoka | ❌ Niska |
| Łatwość integracji | ✅ Prosta | ✅ Średnia | ❌ Złożona |
| Koszt | ⚠️ Wymaga klucza OpenAI | ⚠️ Wymaga klucza OpenAI | ⚠️ Darmowe kredyty, potem płatne |
| Wsparcie dla wielu języków | ✅ Tak | ✅ Tak | ✅ Tak |
| Aktywny rozwój | ✅ Tak | ✅ Tak | ✅ Tak |
| Możliwość pracy offline | ❌ Nie | ❌ Nie | ❌ Nie |

## Rekomendowane rozwiązanie

Na podstawie analizy, **ShellGPT** wydaje się najlepszym wyborem do integracji z naszym asystentem AI dla systemu Linux ze względu na:

1. Rozbudowane funkcje specyficzne dla terminala
2. Aktywny rozwój i duża społeczność
3. Możliwość dostosowania do różnych modeli AI
4. Dobra dokumentacja i regularne aktualizacje
5. Możliwość tworzenia niestandardowych ról systemowych (przydatne dla różnych dystrybucji Linuxa)

Alternatywnie, **BuilderIO/ai-shell** może być łatwiejszy w integracji dla użytkowników preferujących Node.js.

## Ograniczenia i wyzwania

1. Oba główne rozwiązania wymagają klucza API OpenAI, co może stanowić barierę dla niektórych użytkowników
2. Konieczność połączenia z internetem do działania
3. Potencjalne koszty przy intensywnym użytkowaniu
4. Konieczność dostosowania do różnych dystrybucji Linuxa

## Następne kroki

1. Zaprojektować architekturę asystenta integrującą ShellGPT
2. Opracować mechanizm wykrywania dystrybucji Linuxa
3. Stworzyć niestandardowe role systemowe dla różnych dystrybucji
4. Zaimplementować mechanizm wykonywania poleceń terminalowych
