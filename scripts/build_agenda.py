#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
import time
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import requests

TZ = ZoneInfo("America/Santiago")
DURACION_PARTIDO_MIN = 150
NEXT_WINDOW_DAYS = 21
ROOT = Path(__file__).resolve().parents[1]
MANUAL_PATH = ROOT / "data" / "manual_sofa.json"
OUTPUT_PATH = ROOT / "agenda.json"
CACHE_DIR = ROOT / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

HEADERS = {
    "accept": "application/json,text/plain,*/*",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36",
    "referer": "https://www.sofascore.com/",
}

UNIQUE_TO_COMP = {
    11653: "primera",
    1240: "ascenso",
    1221: "copa",
    32734: "copa_liga",
    384: "libertadores",
    480: "sudamericana",
}

SOURCES = [
    {"key": "PRIMERA",      "label": "Primera",         "competencia": "primera",      "unique": 11653, "seasonYear": 2026, "mode": "round", "from": 1, "to": 4, "maxRound": 30},
    {"key": "ASCENSO",      "label": "Ascenso",         "competencia": "ascenso",      "unique": 1240,  "seasonYear": 2026, "mode": "round", "from": 1, "to": 4, "maxRound": 30},
    {"key": "COPA_CHILE",   "label": "Copa Chile",      "competencia": "copa",         "unique": 1221,  "seasonYear": 2026, "mode": "next",  "pages": 5, "lastPages": 3},
    {"key": "COPA_LIGA",    "label": "Copa Liga",       "competencia": "copa_liga",    "unique": 32734, "seasonYear": 2026, "mode": "next",  "pages": 5, "lastPages": 3},
    {"key": "LIBERTADORES", "label": "Libertadores",    "competencia": "libertadores", "unique": 384,   "seasonYear": 2026, "mode": "next",  "pages": 5, "lastPages": 3, "onlyChilean": True},
    {"key": "SUDAMERICANA", "label": "Sudamericana",    "competencia": "sudamericana", "unique": 480,   "seasonYear": 2026, "mode": "next",  "pages": 5, "lastPages": 3, "onlyChilean": True},
    {"key": "CHILE_SEL",    "label": "Selección Chile", "competencia": "seleccion",    "type": "team", "teamId": 4754, "pages": 4, "lastPages": 2},
]


def local_shield(folder: str, file_name: str) -> str:
    return f"escudos/{folder}/{file_name}"


CODE_TO_LOGO = {
    # Primera
    "AUD": local_shield("primera", "audax.png"),
    "CCO": local_shield("primera", "colocolo.png"),
    "COL": local_shield("primera", "colocolo.png"),
    "UCH": local_shield("primera", "universidaddechile.png"),
    "UDA": local_shield("primera", "universidaddechile.png"),
    "COB": local_shield("primera", "cobresal.png"),
    "CDC": local_shield("primera", "dconcepcion.png"),
    "DCO": local_shield("primera", "dconcepcion.png"),
    "COQ": local_shield("primera", "coquimbounido.png"),
    "EVT": local_shield("primera", "everton.png"),
    "EVE": local_shield("primera", "everton.png"),
    "HUA": local_shield("primera", "huachipato.png"),
    "LSR": local_shield("primera", "laserena.png"),
    "LIM": local_shield("primera", "limache.png"),
    "OHI": local_shield("primera", "ohiggins.png"),
    "PAL": local_shield("primera", "palestino.png"),
    "ULC": local_shield("primera", "unionlacalera.png"),
    "UCA": local_shield("primera", "universidadcatolica.png"),
    "UCC": local_shield("primera", "universidadcatolica.png"),
    "UCO": local_shield("primera", "udeconcepcion.png"),
    "NUB": local_shield("primera", "nublense.png"),
    # Ascenso
    "ANT": local_shield("ascenso", "antofagasta.png"),
    "COA": local_shield("ascenso", "cobreloa.png"),
    "COP": local_shield("ascenso", "copiapo.png"),
    "CUR": local_shield("ascenso", "curicounido.png"),
    "IQU": local_shield("ascenso", "iquique.png"),
    "MAG": local_shield("ascenso", "magallanes.png"),
    "PMO": local_shield("ascenso", "puertomontt.png"),
    "RAN": local_shield("ascenso", "rangers.png"),
    "REC": local_shield("ascenso", "recoleta.png"),
    "SFE": local_shield("ascenso", "sanfelipe.png"),
    "SLQ": local_shield("ascenso", "sanluis.png"),
    "SMA": local_shield("ascenso", "sanmarcos.png"),
    "SCR": local_shield("ascenso", "santacruz.png"),
    "SWA": local_shield("ascenso", "wanderers.png"),
    "TEM": local_shield("ascenso", "temuco.png"),
    "UES": local_shield("ascenso", "unionespanola.png"),
    # Selección
    "CHI": local_shield("seleccion", "chile.png"),
}

NAME_TO_LOGO = {
    # Primera
    "audax": local_shield("primera", "audax.png"),
    "audax italiano": local_shield("primera", "audax.png"),
    "colo colo": local_shield("primera", "colocolo.png"),
    "colo-colo": local_shield("primera", "colocolo.png"),
    "colocolo": local_shield("primera", "colocolo.png"),
    "cobresal": local_shield("primera", "cobresal.png"),
    "deportes concepcion": local_shield("primera", "dconcepcion.png"),
    "deportes concepción": local_shield("primera", "dconcepcion.png"),
    "concepcion": local_shield("primera", "dconcepcion.png"),
    "concepción": local_shield("primera", "dconcepcion.png"),
    "d concepcion": local_shield("primera", "dconcepcion.png"),
    "d concepción": local_shield("primera", "dconcepcion.png"),
    "coquimbo": local_shield("primera", "coquimbounido.png"),
    "coquimbo unido": local_shield("primera", "coquimbounido.png"),
    "everton": local_shield("primera", "everton.png"),
    "huachipato": local_shield("primera", "huachipato.png"),
    "la serena": local_shield("primera", "laserena.png"),
    "deportes la serena": local_shield("primera", "laserena.png"),
    "limache": local_shield("primera", "limache.png"),
    "deportes limache": local_shield("primera", "limache.png"),
    "o higgins": local_shield("primera", "ohiggins.png"),
    "ohiggins": local_shield("primera", "ohiggins.png"),
    "o'higgins": local_shield("primera", "ohiggins.png"),
    "palestino": local_shield("primera", "palestino.png"),
    "union la calera": local_shield("primera", "unionlacalera.png"),
    "unión la calera": local_shield("primera", "unionlacalera.png"),
    "la calera": local_shield("primera", "unionlacalera.png"),
    "universidad de chile": local_shield("primera", "universidaddechile.png"),
    "u de chile": local_shield("primera", "universidaddechile.png"),
    "u. de chile": local_shield("primera", "universidaddechile.png"),
    "universidad catolica": local_shield("primera", "universidadcatolica.png"),
    "universidad católica": local_shield("primera", "universidadcatolica.png"),
    "u catolica": local_shield("primera", "universidadcatolica.png"),
    "u católica": local_shield("primera", "universidadcatolica.png"),
    "u. catolica": local_shield("primera", "universidadcatolica.png"),
    "u. católica": local_shield("primera", "universidadcatolica.png"),
    "catolica": local_shield("primera", "universidadcatolica.png"),
    "católica": local_shield("primera", "universidadcatolica.png"),
    "universidad de concepcion": local_shield("primera", "udeconcepcion.png"),
    "universidad de concepción": local_shield("primera", "udeconcepcion.png"),
    "u de concepcion": local_shield("primera", "udeconcepcion.png"),
    "u de concepción": local_shield("primera", "udeconcepcion.png"),
    "udeconcepcion": local_shield("primera", "udeconcepcion.png"),
    "udeconcepción": local_shield("primera", "udeconcepcion.png"),
    "nublense": local_shield("primera", "nublense.png"),
    "ñublense": local_shield("primera", "nublense.png"),
    # Ascenso
    "antofagasta": local_shield("ascenso", "antofagasta.png"),
    "deportes antofagasta": local_shield("ascenso", "antofagasta.png"),
    "club deportes antofagasta": local_shield("ascenso", "antofagasta.png"),
    "cobreloa": local_shield("ascenso", "cobreloa.png"),
    "copiapo": local_shield("ascenso", "copiapo.png"),
    "copiapó": local_shield("ascenso", "copiapo.png"),
    "deportes copiapo": local_shield("ascenso", "copiapo.png"),
    "deportes copiapó": local_shield("ascenso", "copiapo.png"),
    "curico": local_shield("ascenso", "curicounido.png"),
    "curicó": local_shield("ascenso", "curicounido.png"),
    "curico unido": local_shield("ascenso", "curicounido.png"),
    "curicó unido": local_shield("ascenso", "curicounido.png"),
    "iquique": local_shield("ascenso", "iquique.png"),
    "deportes iquique": local_shield("ascenso", "iquique.png"),
    "magallanes": local_shield("ascenso", "magallanes.png"),
    "puerto montt": local_shield("ascenso", "puertomontt.png"),
    "deportes puerto montt": local_shield("ascenso", "puertomontt.png"),
    "rangers": local_shield("ascenso", "rangers.png"),
    "recoleta": local_shield("ascenso", "recoleta.png"),
    "deportes recoleta": local_shield("ascenso", "recoleta.png"),
    "san felipe": local_shield("ascenso", "sanfelipe.png"),
    "union san felipe": local_shield("ascenso", "sanfelipe.png"),
    "unión san felipe": local_shield("ascenso", "sanfelipe.png"),
    "san luis": local_shield("ascenso", "sanluis.png"),
    "san marcos": local_shield("ascenso", "sanmarcos.png"),
    "san marcos de arica": local_shield("ascenso", "sanmarcos.png"),
    "santa cruz": local_shield("ascenso", "santacruz.png"),
    "deportes santa cruz": local_shield("ascenso", "santacruz.png"),
    "wanderers": local_shield("ascenso", "wanderers.png"),
    "santiago wanderers": local_shield("ascenso", "wanderers.png"),
    "temuco": local_shield("ascenso", "temuco.png"),
    "deportes temuco": local_shield("ascenso", "temuco.png"),
    "union espanola": local_shield("ascenso", "unionespanola.png"),
    "union española": local_shield("ascenso", "unionespanola.png"),
    "unión española": local_shield("ascenso", "unionespanola.png"),
    "espanola": local_shield("ascenso", "unionespanola.png"),
    "española": local_shield("ascenso", "unionespanola.png"),
    # Selección
    "chile": local_shield("seleccion", "chile.png"),
    "seleccion de chile": local_shield("seleccion", "chile.png"),
    "selección de chile": local_shield("seleccion", "chile.png"),
}

session = requests.Session()
session.headers.update(HEADERS)
fetch_cache: Dict[str, Any] = {}
event_cache: Dict[str, Dict[str, Any]] = {}
season_cache: Dict[str, int] = {}


@dataclass
class MatchItem:
    competencia: str
    inicio: str
    local_nombre: str
    local_logo: str
    visita_nombre: str
    visita_logo: str
    link: str
    sofa_id: str

    def as_json(self) -> Dict[str, Any]:
        return {
            "competencia": self.competencia,
            "inicio": self.inicio,
            "local": {"nombre": self.local_nombre, "logo": self.local_logo},
            "visita": {"nombre": self.visita_nombre, "logo": self.visita_logo},
            "link": self.link,
            "sofaId": self.sofa_id,
        }


def safe_str(value: Any) -> str:
    return "" if value is None else str(value).strip()


def normalize_key(value: Any) -> str:
    text = safe_str(value).lower()
    import unicodedata

    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^\w\s'.-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_competencia(value: Any) -> str:
    t = normalize_key(value)
    if "primera" in t:
        return "primera"
    if "ascenso" in t:
        return "ascenso"
    if "copa de chile" in t or "copa chile" in t:
        return "copa"
    if "copa de la liga" in t or "copa liga" in t:
        return "copa_liga"
    if "libertadores" in t:
        return "libertadores"
    if "sudamericana" in t:
        return "sudamericana"
    if "chile" in t and ("seleccion" in t or "selection" in t):
        return "seleccion"
    return t


def normalize_name_code_for_link(code: Any) -> str:
    import unicodedata

    text = safe_str(code).lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def build_auto_isgd_link(home_code: Any, away_code: Any, fecha_yyyy_mm_dd: str) -> str:
    h = normalize_name_code_for_link(home_code)
    a = normalize_name_code_for_link(away_code)
    if not h or not a or not fecha_yyyy_mm_dd:
        return ""
    parts = fecha_yyyy_mm_dd.split("-")
    if len(parts) != 3:
        return ""
    return f"https://is.gd/{h}vs{a}{parts[1]}{parts[2]}"


def resolve_logo(competencia: str, display_name: str, code: str, full_name: str) -> str:
    code_key = safe_str(code).upper()
    if code_key and code_key in CODE_TO_LOGO:
        return CODE_TO_LOGO[code_key]

    name1 = normalize_key(display_name)
    if name1 and name1 in NAME_TO_LOGO:
        return NAME_TO_LOGO[name1]

    name2 = normalize_key(full_name)
    if name2 and name2 in NAME_TO_LOGO:
        return NAME_TO_LOGO[name2]

    comp = normalize_competencia(competencia)
    if comp == "seleccion" and (code_key == "CHI" or name1 == "chile" or name2 == "chile"):
        return local_shield("seleccion", "chile.png")

    return ""


def get_preferred_short_name(full_name: Any, short_name: Any) -> str:
    return safe_str(short_name) or safe_str(full_name)


def is_chilean_team(team: Dict[str, Any]) -> bool:
    country = team.get("country") or {}
    return safe_str(country.get("alpha2")).upper() == "CL" or normalize_key(country.get("name")) == "chile" or normalize_key(country.get("slug")) == "chile"


def cache_file_for_url(url: str) -> Path:
    return CACHE_DIR / f"{hashlib.md5(url.encode('utf-8')).hexdigest()}.json"


def get_fetch_ttl_seconds(url: str) -> int:
    if re.search(r"/seasons$", url):
        return 21600
    if re.search(r"/api/v1/event/\d+$", url):
        return 21600
    if "/events/round/" in url:
        return 3600
    if "/events/next/" in url or "/events/last/" in url:
        return 600
    return 300


def fetch_json(url: str) -> Any:
    if url in fetch_cache:
        return fetch_cache[url]

    cache_path = cache_file_for_url(url)
    ttl = get_fetch_ttl_seconds(url)
    if cache_path.exists() and (time.time() - cache_path.stat().st_mtime) <= ttl:
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            fetch_cache[url] = data
            return data
        except Exception:
            pass

    last_error: Optional[Exception] = None
    for attempt in range(1, 4):
        try:
            resp = session.get(url, timeout=25)
            if 200 <= resp.status_code < 300:
                data = resp.json()
                fetch_cache[url] = data
                cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                return data
            last_error = RuntimeError(f"HTTP {resp.status_code} en {url}: {resp.text[:300]}")
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(0.5 * attempt)

    raise RuntimeError(str(last_error) if last_error else f"Error desconocido en {url}")


def ts_to_chile_iso(start_ts: int) -> str:
    return datetime.fromtimestamp(start_ts, tz=timezone.utc).astimezone(TZ).isoformat(timespec="seconds")


def ts_to_date(start_ts: int) -> str:
    return datetime.fromtimestamp(start_ts, tz=timezone.utc).astimezone(TZ).strftime("%Y-%m-%d")


def now_ts() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp())


def is_event_active_or_future(start_ts: int) -> bool:
    end_ts = start_ts + DURACION_PARTIDO_MIN * 60
    return end_ts >= now_ts()


def event_meta_by_sofa_id(sofa_id: str) -> Dict[str, Any]:
    sofa_id = safe_str(sofa_id)
    if not sofa_id:
        return {}
    if sofa_id in event_cache:
        return event_cache[sofa_id]

    url = f"https://www.sofascore.com/api/v1/event/{sofa_id}"
    data = fetch_json(url)
    ev = (data or {}).get("event") or {}

    home_team = ev.get("homeTeam") or {}
    away_team = ev.get("awayTeam") or {}
    tournament = ev.get("tournament") or {}
    unique_tournament = tournament.get("uniqueTournament") or {}
    unique_id = int(unique_tournament.get("id") or 0)
    comp = UNIQUE_TO_COMP.get(unique_id) or normalize_competencia(unique_tournament.get("name") or tournament.get("name") or "")
    start_ts = int(ev.get("startTimestamp") or 0)

    result = {
        "competencia": comp,
        "inicio": ts_to_chile_iso(start_ts) if start_ts else "",
        "startTs": start_ts,
        "homeName": safe_str(home_team.get("name")),
        "awayName": safe_str(away_team.get("name")),
        "homeShortName": get_preferred_short_name(home_team.get("name"), home_team.get("shortName")),
        "awayShortName": get_preferred_short_name(away_team.get("name"), away_team.get("shortName")),
        "homeCode": safe_str(home_team.get("nameCode")).upper(),
        "awayCode": safe_str(away_team.get("nameCode")).upper(),
    }
    result["homeLogo"] = resolve_logo(result["competencia"], result["homeShortName"], result["homeCode"], result["homeName"])
    result["awayLogo"] = resolve_logo(result["competencia"], result["awayShortName"], result["awayCode"], result["awayName"])

    event_cache[sofa_id] = result
    return result


def resolve_season_id(source: Dict[str, Any]) -> int:
    year = int(source.get("seasonYear") or datetime.now(tz=TZ).year)
    key = f"{source['unique']}:{year}"
    if key in season_cache:
        return season_cache[key]

    url = f"https://www.sofascore.com/api/v1/unique-tournament/{source['unique']}/seasons"
    data = fetch_json(url)
    seasons = (data or {}).get("seasons") or []
    if not seasons:
        raise RuntimeError(f"No encontré seasons para {source['label']}")

    chosen = None
    for season in seasons:
        if int(season.get("year") or 0) == year:
            chosen = season
            break
    if not chosen:
        for season in seasons:
            if str(year) in safe_str(season.get("name")):
                chosen = season
                break
    if not chosen:
        seasons_sorted = sorted(seasons, key=lambda s: int(s.get("year") or 0), reverse=True)
        chosen = seasons_sorted[0]

    season_id = int(chosen.get("id") or 0)
    if not season_id:
        raise RuntimeError(f"No pude resolver seasonId para {source['label']}")

    season_cache[key] = season_id
    return season_id


def event_to_match(ev: Dict[str, Any], competencia_override: Optional[str] = None) -> Optional[MatchItem]:
    start_ts = int(ev.get("startTimestamp") or 0)
    if not start_ts:
        return None

    tournament = ev.get("tournament") or {}
    unique_tournament = tournament.get("uniqueTournament") or {}
    comp_from_event = UNIQUE_TO_COMP.get(int(unique_tournament.get("id") or 0)) or normalize_competencia(unique_tournament.get("name") or tournament.get("name") or "")
    comp = safe_str(competencia_override or comp_from_event)

    home_team = ev.get("homeTeam") or {}
    away_team = ev.get("awayTeam") or {}

    home_name = safe_str(home_team.get("name"))
    away_name = safe_str(away_team.get("name"))
    home_short = get_preferred_short_name(home_name, home_team.get("shortName"))
    away_short = get_preferred_short_name(away_name, away_team.get("shortName"))
    home_code = safe_str(home_team.get("nameCode")).upper()
    away_code = safe_str(away_team.get("nameCode")).upper()
    fecha = ts_to_date(start_ts)

    return MatchItem(
        competencia=comp,
        inicio=ts_to_chile_iso(start_ts),
        local_nombre=home_short or home_name,
        local_logo=resolve_logo(comp, home_short or home_name, home_code, home_name),
        visita_nombre=away_short or away_name,
        visita_logo=resolve_logo(comp, away_short or away_name, away_code, away_name),
        link=build_auto_isgd_link(home_code, away_code, fecha),
        sofa_id=safe_str(ev.get("id")),
    )


def update_torneo_rango(source: Dict[str, Any]) -> List[MatchItem]:
    rows: List[MatchItem] = []
    season_id = resolve_season_id(source)
    round_from = max(1, int(source.get("from") or 1))
    round_to = min(int(source.get("to") or round_from), int(source.get("maxRound") or round_from))

    for round_num in range(round_from, round_to + 1):
        try:
            url = f"https://www.sofascore.com/api/v1/unique-tournament/{source['unique']}/season/{season_id}/events/round/{round_num}"
            data = fetch_json(url)
            events = (data or {}).get("events") or []
            for ev in events:
                start_ts = int(ev.get("startTimestamp") or 0)
                if not start_ts or not is_event_active_or_future(start_ts):
                    continue
                match = event_to_match(ev, source.get("competencia"))
                if match:
                    rows.append(match)
        except Exception as exc:  # noqa: BLE001
            print(f"Round inválido o vacío en {source['label']} {round_num}: {exc}", file=sys.stderr)

    return rows


def update_torneo_next(source: Dict[str, Any]) -> List[MatchItem]:
    rows: List[MatchItem] = []
    season_id = resolve_season_id(source)
    now = datetime.now(tz=timezone.utc)
    until = now + timedelta(days=NEXT_WINDOW_DAYS)
    pages = max(1, int(source.get("pages") or 5))
    last_pages = max(1, int(source.get("lastPages") or pages))

    def process_event(ev: Dict[str, Any]) -> None:
        start_ts = int(ev.get("startTimestamp") or 0)
        if not start_ts:
            return
        start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
        end_dt = start_dt + timedelta(minutes=DURACION_PARTIDO_MIN)
        if end_dt < now or start_dt > until:
            return
        if source.get("onlyChilean"):
            if not is_chilean_team(ev.get("homeTeam") or {}) and not is_chilean_team(ev.get("awayTeam") or {}):
                return
        match = event_to_match(ev, source.get("competencia"))
        if match:
            rows.append(match)

    for page in range(pages):
        try:
            url = f"https://www.sofascore.com/api/v1/unique-tournament/{source['unique']}/season/{season_id}/events/next/{page}"
            data = fetch_json(url)
            events = (data or {}).get("events") or []
            if not events:
                break
            for ev in events:
                process_event(ev)
        except Exception:
            break

    for page in range(last_pages):
        try:
            url = f"https://www.sofascore.com/api/v1/unique-tournament/{source['unique']}/season/{season_id}/events/last/{page}"
            data = fetch_json(url)
            events = (data or {}).get("events") or []
            if not events:
                break
            for ev in events:
                process_event(ev)
        except Exception:
            break

    return rows


def update_equipo(team_id: int, source: Dict[str, Any]) -> List[MatchItem]:
    rows: List[MatchItem] = []
    now = datetime.now(tz=timezone.utc)
    until = now + timedelta(days=NEXT_WINDOW_DAYS)
    pages = max(1, int(source.get("pages") or 4))
    last_pages = max(1, int(source.get("lastPages") or 2))

    def process_event(ev: Dict[str, Any]) -> None:
        start_ts = int(ev.get("startTimestamp") or 0)
        if not start_ts:
            return
        start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
        end_dt = start_dt + timedelta(minutes=DURACION_PARTIDO_MIN)
        if end_dt < now or start_dt > until:
            return
        match = event_to_match(ev, "seleccion")
        if match:
            rows.append(match)

    for page in range(pages):
        try:
            url = f"https://www.sofascore.com/api/v1/team/{team_id}/events/next/{page}"
            data = fetch_json(url)
            events = (data or {}).get("events") or []
            if not events:
                break
            for ev in events:
                process_event(ev)
        except Exception:
            break

    for page in range(last_pages):
        try:
            url = f"https://www.sofascore.com/api/v1/team/{team_id}/events/last/{page}"
            data = fetch_json(url)
            events = (data or {}).get("events") or []
            if not events:
                break
            for ev in events:
                process_event(ev)
        except Exception:
            break

    return rows


def extract_sofa_id_from_url(url: str) -> str:
    text = safe_str(url)
    if not text:
        return ""
    m1 = re.search(r"#id:(\d+)", text, flags=re.I)
    if m1:
        return m1.group(1)
    m2 = re.search(r"/event/(\d+)", text, flags=re.I)
    if m2:
        return m2.group(1)
    return ""


def read_manual_sofa() -> List[Dict[str, Any]]:
    if not MANUAL_PATH.exists():
        return []
    try:
        raw = json.loads(MANUAL_PATH.read_text(encoding="utf-8"))
        items = raw.get("manual_sofa") or []
        return items if isinstance(items, list) else []
    except Exception:
        return []


def build_match_from_manual(item: Dict[str, Any]) -> Optional[MatchItem]:
    active = bool(item.get("activo", True))
    if not active:
        return None

    sofa_id = safe_str(item.get("sofaId")) or extract_sofa_id_from_url(item.get("sourceUrl") or item.get("sofascoreUrl") or item.get("url"))
    if not sofa_id:
        return None

    meta = event_meta_by_sofa_id(sofa_id)
    start_ts = int(meta.get("startTs") or 0)
    if not start_ts or not is_event_active_or_future(start_ts):
        return None

    inicio = meta.get("inicio") or ts_to_chile_iso(start_ts)
    comp = "seleccion" if safe_str(item.get("competencia")) == "seleccion" or safe_str(meta.get("competencia")) == "seleccion" else safe_str(item.get("competencia")) or safe_str(meta.get("competencia"))

    home_name = safe_str(meta.get("homeShortName") or meta.get("homeName"))
    away_name = safe_str(meta.get("awayShortName") or meta.get("awayName"))
    home_logo = safe_str(item.get("logoLocal")) or resolve_logo(comp, home_name, safe_str(meta.get("homeCode")), safe_str(meta.get("homeName")))
    away_logo = safe_str(item.get("logoVisita")) or resolve_logo(comp, away_name, safe_str(meta.get("awayCode")), safe_str(meta.get("awayName")))
    link = safe_str(item.get("link")) or build_auto_isgd_link(meta.get("homeCode"), meta.get("awayCode"), ts_to_date(start_ts))

    return MatchItem(
        competencia=comp,
        inicio=inicio,
        local_nombre=home_name,
        local_logo=home_logo,
        visita_nombre=away_name,
        visita_logo=away_logo,
        link=link,
        sofa_id=sofa_id,
    )


def dedupe_matches(matches: List[MatchItem]) -> List[MatchItem]:
    seen = set()
    out: List[MatchItem] = []
    for m in matches:
        key = m.sofa_id or f"{m.inicio}|{m.local_nombre}|{m.visita_nombre}"
        if key in seen:
            continue
        seen.add(key)
        out.append(m)
    out.sort(key=lambda m: m.inicio)
    return out


def build_all_matches() -> List[MatchItem]:
    matches: List[MatchItem] = []
    for source in SOURCES:
        try:
            if source.get("type") == "team":
                matches.extend(update_equipo(int(source["teamId"]), source))
            elif source.get("mode") == "next":
                matches.extend(update_torneo_next(source))
            else:
                matches.extend(update_torneo_rango(source))
        except Exception as exc:  # noqa: BLE001
            print(f"Error procesando {source['label']}: {exc}", file=sys.stderr)

    for item in read_manual_sofa():
        try:
            manual_match = build_match_from_manual(item)
            if manual_match:
                matches.append(manual_match)
        except Exception as exc:  # noqa: BLE001
            print(f"Error en manual_sofa {item}: {exc}", file=sys.stderr)

    return dedupe_matches(matches)


def main() -> int:
    matches = build_all_matches()
    output = {
        "timezone": "America/Santiago",
        "duracion_partido_min": DURACION_PARTIDO_MIN,
        "partidos": [m.as_json() for m in matches],
    }
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generados {len(matches)} partidos en {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
