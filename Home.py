import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="Pulse of Learning - PISA Explorer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# TITLE & DESCRIPTION
# ============================================

st.title("🎓 Pulse of Learning - PISA 2022 Explorer")
st.markdown("**Von Features zu Fragen zu Interventionen**")

st.divider()

# ============================================
# DATABASE INFO
# ============================================

st.header("📊 Datenbank-Übersicht")

# Verwende immer die vollständige Datenbank
db_path = "pisa_2022_germany.db"

try:
    conn = sqlite3.connect(db_path)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        student_count = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM student_data",
            conn
        )['count'][0]
        st.metric("👨‍🎓 Schüler", f"{student_count:,}")

    with col2:
        var_count = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM codebook",
            conn
        )['count'][0]
        st.metric("📊 Variablen", f"{var_count:,}")

    with col3:
        scale_count = pd.read_sql_query(
            "SELECT COUNT(DISTINCT variable_name) as count FROM codebook WHERE variable_label LIKE '%WLE%'",
            conn
        )['count'][0]
        st.metric("📈 WLE-Skalen", f"{scale_count}")

    with col4:
        db_size = Path(db_path).stat().st_size / (1024 * 1024)
        st.metric("💾 DB-Größe", f"{db_size:.1f} MB")

    conn.close()

except Exception as e:
    st.error(f"❌ Fehler beim Laden der Datenbank: {e}")
    st.stop()

st.divider()

# ============================================
# WORKFLOW OVERVIEW
# ============================================

st.header("🚀 Workflow")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### Phase 1: Top Features

    ✅ **Was ist wichtig?**
    - Top 15 Features aus ML-Analyse
    - Nach Einfluss sortiert
    - Schneller Überblick

    📍 **Start:** Phase 1 in Sidebar
    """)

with col2:
    st.markdown("""
    ### Phase 2-3: Verstehen

    ✅ **Wie wird es gemessen?**
    - 58 verfügbare Skalen durchsuchen
    - Einzelfragen ansehen
    - Test-Templates erstellen

    📍 **Start:** Phase 2 in Sidebar
    """)

with col3:
    st.markdown("""
    ### Phase 4-6: Analysieren & Berichten

    ✅ **Was tun?**
    - Phase 4: Korrelationen & Visualisierungen
    - Phase 5: ML Deep Dive & SHAP
    - Phase 6: Ergebnisübersicht & Handlungsempfehlungen

    📍 **Start:** Phase 4 in Sidebar
    """)

st.divider()

# ============================================
# QUICK START
# ============================================

st.header("⚡ Quick Start")

st.info("""
**Neu hier?**

1. 📊 Starte mit **Phase 1: Top 15 Features** (Sidebar links)
2. 🔍 Wähle eine interessante Skala (z.B. MATHEFF)
3. 📝 Schau dir die Einzelfragen an in **Phase 3**
4. 📥 Lade ein Test-Template herunter für deine Schüler

**Für Forscher:**

1. 📈 Gehe direkt zu **Phase 4: Tiefenanalyse** für Korrelationen & Gruppenvergleiche
2. 🔬 Nutze **Phase 5: ML Pipeline** für SHAP-Analysen
3. 📋 Erstelle professionelle Berichte in **Phase 6: Ergebnisübersicht**
4. 💡 Erhalte evidenzbasierte Handlungsempfehlungen
""")

st.divider()

# ============================================
# FOOTER
# ============================================

st.caption("📚 Basierend auf PISA 2022 Deutschland-Daten | 58 verfügbare WLE-Skalen")
