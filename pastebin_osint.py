#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from __future__ import annotations
from colorama import Fore, Style, init
init(autoreset=True)
import argparse
import csv
import html
import json
import re
import sys
import time
import os
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import (
    parse_qs, quote_plus, unquote, urljoin, urlparse, urlunparse
)
from urllib.request import Request, build_opener, HTTPRedirectHandler

APP_NAME = "Pastebin Profile OSINT by PanGruby"
VERSION = "2.0.0"
DEFAULT_OUT = Path("pastebin_results")
DEFAULT_DELAY = 2.5
DEFAULT_TIMEOUT = 15

# Exact host allowlist. Redirects are checked BEFORE they are followed.
ALLOWED_HOSTS = {
    "www.google.com", "google.com",
    "html.duckduckgo.com", "lite.duckduckgo.com",
    "www.bing.com", "bing.com",
    "yandex.com", "www.yandex.com", "yandex.ru", "www.yandex.ru",
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# Pastebin's commonly used public profile URL forms.
PROFILE_RE = re.compile(
    r"""(?ix)
    https?://(?:www\.)?pastebin\.com/
    (?:u|user)/
    ([A-Za-z0-9_-]{1,100})
    """
)
PROFILE_BARE_RE = re.compile(
    r"""(?ix)
    (?:www\.)?pastebin\.com/
    (?:u|user)/
    ([A-Za-z0-9_-]{1,100})
    """
)

class SafeRedirectHandler(HTTPRedirectHandler):
    """Reject a redirect unless its target host is explicitly allowlisted."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urljoin(req.full_url, newurl)
        host = (urlparse(target).hostname or "").lower()
        if host not in ALLOWED_HOSTS:
            raise URLError(f"redirect blocked (host not allowed): {host or target}")
        return super().redirect_request(req, fp, code, msg, headers, target)

class LinkParser(HTMLParser):
    """Collect anchor hrefs and visible text without third-party dependencies."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._parts = []

    def handle_data(self, data):
        if self._href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._parts).strip()))
            self._href = None
            self._parts = []

def normalise_candidate(value: str) -> str:
    """Decode common HTML/URL wrappers a few times, safely."""
    value = html.unescape(value or "").replace(r"\/", "/")
    for _ in range(3):
        decoded = unquote(value)
        if decoded == value:
            break
        value = decoded
    return value

def extract_profiles(document: str, page_url: str) -> list[dict]:
    """Extract profile links from result-page HTML; never fetch the profile."""
    parser = LinkParser()
    try:
        parser.feed(document)
    except Exception:
        pass

    candidates: list[tuple[str, str]] = []
    # Search link targets and visible anchor text.
    for href, anchor_text in parser.links:
        full = urljoin(page_url, html.unescape(href))
        candidates.append((normalise_candidate(full), anchor_text))
        # Search-engine redirect wrappers commonly keep the target in q/url.
        parsed = urlparse(full)
        params = parse_qs(parsed.query)
        for key in ("q", "url", "uddg", "u"):
            for target in params.get(key, []):
                candidates.append((normalise_candidate(target), anchor_text))

    # Also scan the document itself: some engines encode result links in scripts.
    candidates.append((normalise_candidate(document), ""))

    found: dict[str, dict] = {}
    for candidate, anchor_text in candidates:
        for regex in (PROFILE_RE, PROFILE_BARE_RE):
            for match in regex.finditer(candidate):
                username = match.group(1).strip()
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", username):
                    continue
                key = username.casefold()
                profile_url = f"https://pastebin.com/u/{username}"
                item = found.setdefault(key, {
                    "username": username,
                    "profile_url": profile_url,
                    "anchor_text": anchor_text[:300],
                })
                if not item["anchor_text"] and anchor_text:
                    item["anchor_text"] = anchor_text[:300]
    return list(found.values())

def build_search_url(engine: str, query: str, page: int) -> str:
    q = quote_plus(query)
    if engine == "google":
        # Google does not guarantee HTML results to automated clients.
        return f"https://www.google.com/search?q={q}&num=100&start={page * 10}"
    if engine == "ddg":
        return f"https://html.duckduckgo.com/html/?q={q}"
    if engine == "ddg-lite":
        return f"https://lite.duckduckgo.com/lite/?q={q}"
    if engine == "bing":
        return f"https://www.bing.com/search?q={q}&count=50&first={page * 50 + 1}"
    if engine == "yandex":
        return f"https://yandex.com/search/?text={q}&p={page}"
    raise ValueError(f"Unknown engine: {engine}")

def fetch_search_page(url: str, timeout: int) -> tuple[int, str, str]:
    """Fetch only allowlisted search-engine URLs, with pre-checked redirects."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in ALLOWED_HOSTS:
        raise ValueError(f"Blocked URL: {url}")

    request = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "identity",
        "Connection": "close",
    })
    opener = build_opener(SafeRedirectHandler())
    try:
        with opener.open(request, timeout=timeout) as response:
            final_url = response.geturl()
            final_host = (urlparse(final_url).hostname or "").lower()
            if final_host not in ALLOWED_HOSTS:
                raise ValueError(f"Blocked final host: {final_host}")
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read(5_000_000).decode(charset, errors="replace")
            return response.status, body, final_url
    except HTTPError as exc:
        # Preserve status for diagnostics (e.g. 403/429); do not parse error pages.
        return exc.code, "", url
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(str(exc)) from exc

def make_queries(extra_terms: Iterable[str] = ()) -> list[str]:
    bases = [
        '"pastebin.com/u/"',
        '"pastebin.com/user/"',
        '"https://pastebin.com/u/"',
        '"https://pastebin.com/user/"',
    ]
    terms = ["github", "python", "linux", "security", "programming",
             "developer", "code", "technology"]
    terms.extend(t.strip() for t in extra_terms if t.strip())
    queries = list(bases)
    for path in ('"pastebin.com/u/"', '"pastebin.com/user/"'):
        for term in terms:
            queries.append(f"{path} {term}")
    # Keep order while removing duplicates.
    return list(dict.fromkeys(queries))

def load_existing(path: Path) -> dict[str, dict]:
    records: dict[str, dict] = {}
    if not path.exists():
        return records
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                username = (row.get("username") or "").strip()
                if username:
                    records[username.casefold()] = row
    except (OSError, csv.Error) as exc:
        print(f"[!] Nie udało się odczytać poprzedniego CSV: {exc}")
    return records

def save_outputs(out_dir: Path, records: dict[str, dict], run_meta: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ordered = sorted(records.values(), key=lambda r: r["username"].casefold())

    csv_path = out_dir / "profiles.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        fields = ["username", "profile_url", "first_seen_utc", "engines", "queries", "anchor_text"]
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ordered)

    txt_path = out_dir / "usernames.txt"
    txt_path.write_text(
        "".join(f'{r["username"]}\n' for r in ordered), encoding="utf-8"
    )

    report_path = out_dir / "report.txt"
    lines = [
        f"{APP_NAME} v{VERSION}",
        "=" * 64,
        f'Run started (UTC): {run_meta["started_utc"]}',
        f'Run finished (UTC): {datetime.now(timezone.utc).isoformat(timespec="seconds")}',
        f'Queries attempted: {run_meta["queries_attempted"]}',
        f'HTTP pages with status 200: {run_meta["http_200"]}',
        f'HTTP errors/blocked pages: {run_meta["http_errors"]}',
        f'Unique profiles saved: {len(ordered)}',
        "",
        "Engines selected: " + ", ".join(run_meta["engines"]),
        "Scope: search-engine result pages only; Pastebin profile pages are not opened.",
        "",
        "Important: absence from this report does not prove a profile does not exist.",
        "Search engines have incomplete indexes and may rate-limit automated requests.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Machine-readable run metadata, useful for debugging/reproducibility.
    (out_dir / "run.json").write_text(
        json.dumps(run_meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

def run(args) -> int:
    out_dir = Path(args.output)
    csv_path = out_dir / "profiles.csv"
    records = load_existing(csv_path) if args.resume else {}
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    engines = args.engines
    queries = make_queries(args.term)
    meta = {
        "version": VERSION,
        "started_utc": started,
        "engines": engines,
        "queries_attempted": 0,
        "http_200": 0,
        "http_errors": 0,
        "new_profiles": 0,
        "errors": [],
    }

    print(f"{Style.BRIGHT}{Fore.GREEN}{APP_NAME} v{VERSION}{Style.RESET_ALL}")
    print(f"")
    print("Tryb: publiczne wyniki wyszukiwarek; bez otwierania Pastebin.")
    print(f"Wyszukiwarki: {', '.join(engines)}")
    print(f"Zapytania: {len(queries)} | opóźnienie: {args.delay:g} s")
    print(f"Wyniki: {out_dir.resolve()}")
    print("Wskazówka: Google i inne wyszukiwarki mogą blokować automatyczne żądania.\n")
    
   

    try:
        for qi, query in enumerate(queries, 1):
            for engine in engines:
                pages = args.pages if engine in ("google", "bing", "yandex") else 1
                for page in range(pages):
                    url = build_search_url(engine, query, page)
                    meta["queries_attempted"] += 1
                    print(f"[{qi}/{len(queries)}] {engine} p{page + 1}: {query}")
                    try:
                        status, body, final_url = fetch_search_page(url, args.timeout)
                        if status == 200 and body:
                            meta["http_200"] += 1
                            hits = extract_profiles(body, final_url)
                            added = 0
                            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
                            for hit in hits:
                                key = hit["username"].casefold()
                                if key not in records:
                                    records[key] = {
                                        "username": hit["username"],
                                        "profile_url": hit["profile_url"],
                                        "first_seen_utc": now,
                                        "engines": engine,
                                        "queries": query,
                                        "anchor_text": hit["anchor_text"],
                                    }
                                    added += 1
                                else:
                                    row = records[key]
                                    old_engines = set(filter(None, row.get("engines", "").split(";")))
                                    old_engines.add(engine)
                                    row["engines"] = ";".join(sorted(old_engines))
                                    old_queries = set(filter(None, row.get("queries", "").split(" || ")))
                                    old_queries.add(query)
                                    row["queries"] = " || ".join(sorted(old_queries))
                                    if not row.get("anchor_text") and hit["anchor_text"]:
                                        row["anchor_text"] = hit["anchor_text"]
                            meta["new_profiles"] += added
                            print(f"    HTTP {status}; trafienia: {len(hits)}, nowe: {added}")
                        else:
                            meta["http_errors"] += 1
                            print(f"    HTTP {status}; wyszukiwarka nie zwróciła strony wyników.")
                            if status in (403, 429, 503):
                                print("    [!] Możliwa blokada/rate limit — zwiększ --delay lub pomiń tę wyszukiwarkę.")
                    except Exception as exc:
                        meta["http_errors"] += 1
                        message = f"{engine} | {query} | page={page + 1} | {exc}"
                        meta["errors"].append(message)
                        print(f"    [!] Błąd: {exc}")

                    # Save after each request so interruption loses little work.
                    save_outputs(out_dir, records, meta)
                    if args.max_requests and meta["queries_attempted"] >= args.max_requests:
                        print("[*] Osiągnięto limit --max-requests.")
                        raise StopIteration
                    time.sleep(args.delay)
    except KeyboardInterrupt:
        print("\n[!] Przerwano przez użytkownika. Zapisuję dotychczasowe wyniki.")
    except StopIteration:
        pass

    save_outputs(out_dir, records, meta)
    print("\nGotowe.")
    print(f"Unikalne profile: {len(records)}")
    print(f"Nowe w tej sesji: {meta['new_profiles']}")
    print(f"CSV: {(out_dir / 'profiles.csv').resolve()}")
    print(f"Lista nazw: {(out_dir / 'usernames.txt').resolve()}")
    print(f"Raport: {(out_dir / 'report.txt').resolve()}")
    return 0

def parse_args():
    parser = argparse.ArgumentParser(
        description="Wyszukuje publicznie indeksowane profile Pastebin przez strony wyników wyszukiwarek."
    )
    parser.add_argument(
        "--engines", nargs="+",
        choices=["google", "ddg", "ddg-lite", "bing", "yandex"],
        default=["google", "ddg", "ddg-lite", "bing", "yandex"],
        help="Wyszukiwarki do użycia (domyślnie wszystkie).",
    )
    parser.add_argument("--pages", type=int, default=2,
                        help="Liczba stron dla Google/Bing/Yandex (domyślnie 2).")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                        help="Przerwa po każdym żądaniu w sekundach (domyślnie 2.5).")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="Timeout żądania w sekundach (domyślnie 15).")
    parser.add_argument("--output", default=str(DEFAULT_OUT),
                        help="Katalog wynikowy (domyślnie pastebin_results).")
    parser.add_argument("--resume", action="store_true",
                        help="Wczytaj poprzednie profile.csv i kontynuuj zbieranie.")
    parser.add_argument("--term", action="append", default=[],
                        help="Dodatkowe słowo kluczowe; można podać wielokrotnie.")
    parser.add_argument("--max-requests", type=int, default=0,
                        help="Limit żądań do testów (0 = bez limitu).")
    args = parser.parse_args()
    if args.pages < 1:
        parser.error("--pages musi wynosić co najmniej 1")
    if args.delay < 0:
        parser.error("--delay nie może być ujemne")
    if args.timeout < 1:
        parser.error("--timeout musi wynosić co najmniej 1")
    if args.max_requests < 0:
        parser.error("--max-requests nie może być ujemne")
    return args

if __name__ == "__main__":
    try:
        raise SystemExit(run(parse_args()))
    except KeyboardInterrupt:
        print("\nPrzerwano.", file=sys.stderr)
        raise SystemExit(130)
