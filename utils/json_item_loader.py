"""
Item-Informationen aus JSON-Dokumentation laden

Dieses Modul lädt die Einzelfragen (Items) für PISA-Skalen aus der
JSON-Dokumentation, die aus dem PISA 2022 Skalenhandbuch erstellt wurde.

Quelle: PISA 2022 Skalenhandbuch - Dokumentation der Erhebungsinstrumente
"""

import json
import streamlit as st
from pathlib import Path
from typing import Dict, List, Optional

# Pfade zu JSON-Dateien (relativ zum Projektverzeichnis)
JSON_PATH = "data/skalen_infos/pisa_skalen.json"
JSON_INDIZES_PATH = "data/skalen_infos/pisa_indizes_erweitert.json"


@st.cache_data
def load_json_scales() -> Dict:
    """
    Lädt die komplette JSON-Datei mit allen Skalen-Informationen.

    Returns:
        Dict: Dictionary mit allen Skalen und ihren Items

    Raises:
        FileNotFoundError: Wenn JSON-Datei nicht gefunden wird
        json.JSONDecodeError: Wenn JSON ungültig ist
    """
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"⚠️ JSON-Datei nicht gefunden: {JSON_PATH}")
        return {}
    except json.JSONDecodeError as e:
        st.error(f"⚠️ JSON-Datei konnte nicht gelesen werden: {e}")
        return {}


@st.cache_data
def load_json_indizes() -> Dict:
    """
    Lädt die JSON-Datei mit erweiterten Informationen zu berechneten Indizes.

    Returns:
        Dict: Dictionary mit Indizes und ihren Berechnungshinweisen
    """
    try:
        with open(JSON_INDIZES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Kein Fehler - Indizes-Datei ist optional
        return {}
    except json.JSONDecodeError as e:
        st.warning(f"⚠️ Indizes-JSON konnte nicht gelesen werden: {e}")
        return {}


def has_json_items(scale_name: str) -> bool:
    """
    Prüft, ob für eine Skala Items in der JSON vorhanden sind.

    Args:
        scale_name: Der Skalencode (z.B. "ANXMAT", "MATHEFF")

    Returns:
        bool: True wenn Items vorhanden, sonst False
    """
    scales = load_json_scales()

    if scale_name not in scales:
        return False

    items = scales[scale_name].get('items', [])
    return len(items) > 0


def get_scale_items(scale_name: str) -> List[Dict]:
    """
    Gibt die Items für eine Skala zurück.

    Args:
        scale_name: Der Skalencode (z.B. "ANXMAT", "MATHEFF")

    Returns:
        List[Dict]: Liste von Items mit 'code' und 'text'
                   Format: [{"code": "ST292Q01JA", "text": "..."}, ...]
                   Leere Liste wenn keine Items vorhanden
    """
    scales = load_json_scales()

    if scale_name not in scales:
        return []

    scale_data = scales[scale_name]
    items = scale_data.get('items', [])

    # Füge zusätzliche Metadaten hinzu (für Kompatibilität mit App)
    enriched_items = []
    for item in items:
        enriched_items.append({
            'variable_name': item['code'],
            'question_text_de': item['text'],
            'question_text_en': item['text'],  # Fallback
            'source': 'JSON'
        })

    return enriched_items


def get_scale_metadata(scale_name: str) -> Optional[Dict]:
    """
    Gibt die Metadaten einer Skala zurück.

    Args:
        scale_name: Der Skalencode

    Returns:
        Dict: Metadaten mit 'titel', 'beschreibung', 'fragestamm', etc.
        None wenn Skala nicht vorhanden
    """
    scales = load_json_scales()
    return scales.get(scale_name, None)


def get_all_scales_with_items() -> List[str]:
    """
    Gibt eine Liste aller Skalen zurück, die Items haben.

    Returns:
        List[str]: Liste von Skalencodes
    """
    scales = load_json_scales()
    return [
        scale_name
        for scale_name, scale_data in scales.items()
        if len(scale_data.get('items', [])) > 0
    ]


def get_items_availability_summary() -> Dict:
    """
    Erstellt eine Übersicht über alle Skalen und ihre Item-Verfügbarkeit.

    Returns:
        Dict: Zusammenfassung mit Statistiken
    """
    scales = load_json_scales()

    summary = {
        'total_scales': len(scales),
        'scales_with_items': 0,
        'scales_without_items': 0,
        'total_items': 0,
        'scales': []
    }

    for scale_name, scale_data in scales.items():
        items = scale_data.get('items', [])
        num_items = len(items)

        if num_items > 0:
            summary['scales_with_items'] += 1
            summary['total_items'] += num_items
        else:
            summary['scales_without_items'] += 1

        summary['scales'].append({
            'code': scale_name,
            'titel': scale_data.get('titel', 'N/A'),
            'anzahl_items': num_items,
            'hat_items': num_items > 0
        })

    # Sortiere nach Anzahl Items (absteigend)
    summary['scales'] = sorted(
        summary['scales'],
        key=lambda x: x['anzahl_items'],
        reverse=True
    )

    return summary


def get_fragestamm(scale_name: str) -> Optional[str]:
    """
    Gibt den Fragestamm (gemeinsamen Einleitungstext) einer Skala zurück.

    Args:
        scale_name: Der Skalencode

    Returns:
        str: Fragestamm oder None wenn nicht vorhanden
    """
    metadata = get_scale_metadata(scale_name)
    if metadata:
        return metadata.get('fragestamm', None)
    return None


def is_calculated_index(scale_name: str) -> bool:
    """
    Prüft, ob eine Skala ein berechneter Index ist.

    Args:
        scale_name: Der Skalencode

    Returns:
        bool: True wenn berechneter Index, sonst False
    """
    indizes = load_json_indizes()
    if scale_name in indizes:
        return indizes[scale_name].get('typ') == 'zusammengesetzter_index'
    return False


def get_index_info(scale_name: str) -> Optional[Dict]:
    """
    Gibt erweiterte Informationen zu einem berechneten Index zurück.

    Args:
        scale_name: Der Skalencode

    Returns:
        Dict: Informationen mit 'anmerkung', 'typ', etc.
        None wenn nicht vorhanden
    """
    indizes = load_json_indizes()
    return indizes.get(scale_name, None)


def get_calculation_note(scale_name: str) -> Optional[str]:
    """
    Gibt die Berechnungsanmerkung für einen Index zurück.

    Args:
        scale_name: Der Skalencode

    Returns:
        str: Anmerkung zur Berechnung oder None
    """
    index_info = get_index_info(scale_name)
    if index_info:
        return index_info.get('anmerkung', None)
    return None
