# ICTPartnerDlaPstryk.pl Home Assistant Integration

Integracja Home Assistant z platformą pstryk.pl, umożliwiająca pobieranie i wizualizację danych o cenach energii elektrycznej.

## Instalacja przez HACS

1. Dodaj to repozytorium jako zewnętrzne repozytorium w HACS (Home Assistant Community Store).
2. Zainstaluj integrację "ICTPartnerDlaPstryk.pl" z poziomu HACS.
3. Dodaj integrację przez WebUI Home Assistant, podając klucz API do platformy pstryk.pl.

## Funkcje
- Automatyczne pobieranie danych o cenach energii raz na pełną godzinę.
- Wsparcie dla wykresów cen godzinowych za bieżący dzień oraz dzień następny (dostępny po godzinie 14:00).
- Możliwość śledzenia zmian i wizualizacji na wykresach Home Assistant.

## Konfiguracja
- Wymagany jest klucz API do platformy pstryk.pl.
- Integracja obsługuje konfigurację przez UI (config flow).

## Przykładowe encje
- `sensor.pstryk_price_today`
- `sensor.pstryk_price_tomorrow`

## Licencja
MIT
