### Pastebin Profile OSINT by PanGruby ###

 Pastebin Profile OSINT to narzędzie OSINT przeznaczone do automatycznego wykrywania publicznie dostępnych profili użytkowników Pastebin za pomocą popularnych wyszukiwarek internetowych. 
 Projekt umożliwia pasywne pozyskiwanie informacji bez bezpośredniego przeszukiwania zawartości wklejek, koncentrując się wyłącznie na danych publicznie indeksowanych przez wyszukiwarki.


## Główne funkcje

- Wyszukiwanie publicznych profili Pastebin przy użyciu wielu wyszukiwarek.
- Pasywne pozyskiwanie informacji z ogólnodostępnych wyników wyszukiwania.
- Automatyczna agregacja i deduplikacja odnalezionych profili.
- Eksport wyników do plików raportowych.
- Regulowane opóźnienia pomiędzy zapytaniami.
- Obsługa wznawiania poprzednich przebiegów.
- Brak bezpośredniej interakcji z prywatnymi lub nieindeksowanymi zasobami Pastebin.

## Zastosowanie

Narzędzie może być wykorzystywane podczas:

- działań OSINT (Open Source Intelligence),
- badań ekspozycji danych,
- analiz bezpieczeństwa,
- rozpoznania środowisk i aktywności użytkowników,
- ćwiczeń Red Team,
- działań Threat Intelligence i Attack Surface Mapping.

## Wymagania

- Python 3.10 lub nowszy
- Requirements


## Uruchomienie — Windows

Otwórz CMD w katalogu z plikiem i wykonaj:

pastebin_osint.py --max-requests 10   //  To krótki test
pastebin_osint.py   //  Pełne wyszukiwanie 
pastebin_osint.py --engines google bing --pages 2 --delay 4   //  Tylko Google i Bing
pastebin_osint.py --resume   //  Wznowienie i dopisanie wyników z poprzedniego przebiegu 
pastebin_osint.py --term "open source" --term "developer"   //  Dodatkowe słowa kluczowe


## Pliki wynikowe

- `pastebin_results/profiles.csv` - nazwa użytkownika, URL profilu, data pierwszego wykrycia, wyszukiwarki, zapytania oraz tekst linku.
- `pastebin_results/usernames.txt` - lista odnalezionych nazw użytkowników.
- `pastebin_results/report.txt` - podsumowanie przebiegu skanowania.
- `pastebin_results/run.json` - metadane, statystyki oraz informacje o błędach.

## Ważne ograniczenia

- Google, Bing, DuckDuckGo i Yandex mogą zmieniać strukturę HTML, blokować automatyczne zapytania lub wymagać CAPTCHA.
- Skrypt nie gwarantuje kompletności wyników.
- Kody HTTP 403, 429 i 503 zazwyczaj oznaczają blokadę, ograniczenie częstotliwości lub stronę pośrednią.
- Nie należy próbować omijać CAPTCHA ani innych zabezpieczeń. W przypadku problemów zaleca się zwiększenie opóźnienia lub wyłączenie danej wyszukiwarki.
- Lista obsługiwanych domen została celowo ograniczona.
- Odnaleziony wpis oznacza jedynie obecność wyniku w indeksie wyszukiwarki i nie stanowi potwierdzenia, że profil nadal istnieje.

## Założenia Projektu

Projekt został zaprojektowany zgodnie z zasadami pasywnego OSINT. 
Wykorzystuje wyłącznie informacje publicznie dostępne w wynikach wyszukiwarek internetowych i nie podejmuje prób omijania zabezpieczeń, logowania ani dostępu do danych nieprzeznaczonych do publicznej publikacji.

## Autor

**PanGruby**

*Open Source Intelligence • Security Research • OSINT Tools Development*

---

## Legal Notice

This tool is intended solely for research, educational, and defensive security purposes. 
Users are responsible for ensuring compliance with all applicable laws, regulations, and terms of service. 
The author assumes no liability for misuse of this software.

---

### Short Description

> **Pastebin Profile OSINT** is a passive reconnaissance tool designed to discover publicly indexed Pastebin