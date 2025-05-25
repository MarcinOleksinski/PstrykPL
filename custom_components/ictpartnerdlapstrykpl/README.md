# ICTPartnerDlaPstryk.pl Home Assistant Integration


Integracja Home Assistant z platformą pstryk.pl, umożliwiająca automatyczne pobieranie, agregację i wizualizację danych z API Pstryk, takich jak:
- ceny energii (bieżące, prognozowane, agregaty dzienne/tygodniowe/miesięczne),
- zużycie energii,
- koszty energii,
- ślad węglowy,
- dane prosumenckie (jeśli dostępne),
- alerty cenowe i zużycia,
- status API i wersja integracji.


## Instalacja przez HACS

1. Dodaj to repozytorium jako zewnętrzne repozytorium w HACS (Home Assistant Community Store).
2. Zainstaluj integrację "ICTPartnerDlaPstryk.pl" z poziomu HACS.
3. Dodaj integrację przez interfejs Home Assistant: "Dodaj integrację" → "ICTPartnerDlaPstryk.pl".
4. Wprowadź klucz API (otrzymany z pstryk.pl) oraz opcjonalnie: identyfikator licznika/metra, strefę czasową, progi alertów cenowych i zużycia.


## Funkcje
- Automatyczne pobieranie i aktualizacja danych z API Pstryk (asynchronicznie, bez blokowania HA).
- Obsługa wielu typów danych: ceny energii (hour/day/week/month), zużycie, koszty, ślad węglowy, dane prosumenckie, agregaty.
- Alerty cenowe i zużycia (możliwość ustawienia progów w konfiguracji).
- Panel konfiguracyjny (config flow) oraz możliwość rekonfiguracji przez UI.
- Dashboard Lovelace z przykładową wizualizacją danych.
- Pełna zgodność z HACS i Home Assistant (asynchroniczność, config flow, tłumaczenia, wersjonowanie).


## Konfiguracja
- Wymagany jest klucz API do platformy pstryk.pl (pole obowiązkowe).
- Opcjonalnie: identyfikator licznika/metra, strefa czasowa, progi alertów cenowych i zużycia.
- Konfiguracja i rekonfiguracja odbywa się przez interfejs Home Assistant (config flow/options flow).


## Przykładowe encje
- `sensor.pstryk_price_today` – ceny godzinowe na dziś
- `sensor.pstryk_price_tomorrow` – ceny godzinowe na jutro (po 14:00)
- `sensor.pstryk_energy_usage` – zużycie energii (godzinowe)
- `sensor.pstryk_energy_usage_day` – zużycie energii (dziennie)
- `sensor.pstryk_energy_cost_month` – koszt energii (miesięcznie)
- `sensor.pstryk_carbon_footprint` – ślad węglowy
- `sensor.pstryk_prosumer_price_today` – cena prosumencka (jeśli dostępna)
- `sensor.pstryk_api_status` – status API
- `sensor.pstryk_integration_version` – wersja integracji


## Licencja
MIT
