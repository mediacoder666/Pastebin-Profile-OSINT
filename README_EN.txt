### Pastebin Profile OSINT by PanGruby ###

Pastebin Profile OSINT is an OSINT tool designed to automatically discover publicly available Pastebin user profiles using popular internet search engines. 
The project enables passive information gathering without directly searching the contents of pastes, focusing exclusively on data publicly indexed by search engines.


## Main Features

- Search for public Pastebin profiles using multiple search engines.
- Passive information gathering from publicly available search results.
- Automatic aggregation and deduplication of discovered profiles.
- Export of results to report files.
- Adjustable delays between queries.
- Support for resuming previous runs.
- No direct interaction with private or non-indexed Pastebin resources.

## Use Cases

The tool can be used for:

- OSINT (Open Source Intelligence) activities,
- data exposure research,
- security analysis,
- reconnaissance of user environments and activities,
- Red Team exercises,
- Threat Intelligence and Attack Surface Mapping activities.

## Requirements

- Python 3.10 or newer
- Requirements


## Running — Windows

Open CMD in the directory containing the file and execute:

pastebin_osint.py --max-requests 10   //  This is a short test
pastebin_osint.py   //  Full search
pastebin_osint.py --engines google bing --pages 2 --delay 4   //  Google and Bing only
pastebin_osint.py --resume   //  Resume and append results from the previous run
pastebin_osint.py --term "open source" --term "developer"   //  Additional keywords


## Output Files

- `pastebin_results/profiles.csv` - username, profile URL, first detection date, search engines, queries, and link text.
- `pastebin_results/usernames.txt` - list of discovered usernames.
- `pastebin_results/report.txt` - summary of the scanning run.
- `pastebin_results/run.json` - metadata, statistics, and error information.

## Important Limitations

- Google, Bing, DuckDuckGo, and Yandex may change their HTML structure, block automated queries, or require CAPTCHA.
- The script does not guarantee complete results.
- HTTP status codes 403, 429, and 503 usually indicate blocking, rate limiting, or an intermediary page.
- Do not attempt to bypass CAPTCHA or other security measures. If problems occur, increasing the delay or disabling the affected search engine is recommended.
- The list of supported domains has been deliberately restricted.
- A discovered entry only indicates that a result exists in a search engine's index and does not confirm that the profile still exists.

## Project Principles

The project has been designed in accordance with passive OSINT principles. 
It uses only information publicly available in internet search engine results and does not attempt to bypass security measures, log in, or access data not intended for public disclosure.

## Author

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