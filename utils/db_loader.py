"""
Shared database loading functions for PISA 2022 Explorer
"""

import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path


def get_db_connection():
    """
    Erstellt neue Datenbankverbindung zur vollständigen PISA 2022 Deutschland Datenbank

    WICHTIG: Kein Caching mehr, da SQLite-Connections nicht thread-safe gecacht werden können

    Returns:
        sqlite3.Connection: Datenbankverbindung
    """
    # Immer die vollständige Datenbank verwenden (6,116 Schüler)
    db_path = "pisa_2022_germany.db"

    return sqlite3.connect(db_path, check_same_thread=False)


@st.cache_data
def load_codebook(_conn, search_term=None):
    """
    Lädt Codebook mit optionalem Filter

    Args:
        _conn: Datenbankverbindung (nicht für Cache-Key verwendet)
        search_term: Optionaler Suchbegriff

    Returns:
        pd.DataFrame: Codebook-Daten
    """
    query = """
    SELECT
        variable_name,
        variable_label,
        data_type
    FROM codebook
    """

    if search_term:
        query += f"""
        WHERE LOWER(variable_label) LIKE LOWER('%{search_term}%')
        OR LOWER(variable_name) LIKE LOWER('%{search_term}%')
        """

    query += " ORDER BY variable_name;"

    return pd.read_sql_query(query, _conn)


@st.cache_data
def load_value_labels(_conn, variable_name):
    """
    Lädt Value Labels für eine Variable (mit deutschen Labels falls vorhanden)

    Args:
        _conn: Datenbankverbindung
        variable_name: Name der Variable

    Returns:
        pd.DataFrame: Value Labels
    """
    query = f"""
    SELECT
        value,
        label_en as label,
        label_de,
        count,
        percent,
        is_missing_code
    FROM value_labels
    WHERE variable_name = '{variable_name}'
    ORDER BY sort_order, value;
    """
    return pd.read_sql_query(query, _conn)


@st.cache_data
def load_question_text(_conn, variable_name):
    """
    Lädt Fragetext für eine Variable

    Args:
        _conn: Datenbankverbindung
        variable_name: Name der Variable

    Returns:
        pd.Series or None: Fragetext-Daten
    """
    query = f"""
    SELECT
        question_text_en,
        question_text_de,
        questionnaire_type,
        question_category
    FROM question_text
    WHERE variable_name = '{variable_name}';
    """
    result = pd.read_sql_query(query, _conn)
    return result.iloc[0] if len(result) > 0 else None


@st.cache_data
def load_student_data(_conn, variables, performance_vars=['PV1MATH', 'PV1READ', 'PV1SCIE']):
    """
    Lädt Schülerdaten für ausgewählte Variablen

    Args:
        _conn: Datenbankverbindung
        variables: Liste der zu ladenden Variablen
        performance_vars: Leistungsvariablen (Math, Reading, Science)

    Returns:
        pd.DataFrame: Schülerdaten
    """
    # Ensure performance variables and gender are always included
    var_list = list(set(variables + performance_vars + ['ST004D01T']))
    var_str = ", ".join(var_list)

    query = f"""
    SELECT
        {var_str}
    FROM student_data
    WHERE {variables[0]} IS NOT NULL;
    """
    return pd.read_sql_query(query, _conn)


@st.cache_data
def get_available_scales(_conn):
    """
    Lädt alle verfügbaren WLE-Skalen (nicht-NULL Werte)

    Args:
        _conn: Datenbankverbindung

    Returns:
        pd.DataFrame: Verfügbare Skalen mit Statistiken
    """
    query = """
    SELECT
        variable_name,
        variable_label,
        data_type
    FROM codebook
    WHERE variable_label LIKE '%WLE%'
    ORDER BY variable_name;
    """
    return pd.read_sql_query(query, _conn)


@st.cache_data
def count_non_null(_conn, variable_name):
    """
    Zählt nicht-NULL Werte für eine Variable

    Args:
        _conn: Datenbankverbindung
        variable_name: Name der Variable

    Returns:
        int: Anzahl nicht-NULL Werte
    """
    query = f"""
    SELECT COUNT({variable_name}) as count
    FROM student_data
    WHERE {variable_name} IS NOT NULL;
    """
    result = pd.read_sql_query(query, _conn)
    return result['count'][0] if len(result) > 0 else 0
