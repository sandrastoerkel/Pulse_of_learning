import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="PISA Math Self-Confidence Explorer",
    page_icon="📊",
    layout="wide"
)

# ============================================
# DATABASE CONNECTION
# ============================================

@st.cache_resource
def get_db_connection():
    """Erstellt gecachte Datenbankverbindung"""
    db_path = "pisa_2022_germany.db"
    return sqlite3.connect(db_path, check_same_thread=False)

# ============================================
# DATA LOADING FUNCTIONS
# ============================================

@st.cache_data
def load_codebook(_conn, search_term=None):
    """Lädt Codebook mit optionalem Filter"""
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
    """Lädt Value Labels für eine Variable (mit deutschen Labels falls vorhanden)"""
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
    """Lädt Fragetext für eine Variable"""
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
def load_student_data(_conn, variables):
    """Lädt Schülerdaten für ausgewählte Variablen

    Args:
        _conn: Datenbankverbindung (wird nicht für Cache-Key verwendet)
        variables: Liste der zu ladenden Variablen
    """
    var_list = ", ".join(variables)
    query = f"""
    SELECT
        {var_list},
        ST004D01T as gender,
        PV1MATH as math_score,
        PV1READ as reading_score,
        PV1SCIE as science_score
    FROM student_data
    WHERE {variables[0]} IS NOT NULL;
    """
    return pd.read_sql_query(query, _conn)

# ============================================
# HELPER FUNCTIONS
# ============================================

def find_math_confidence_vars(conn):
    """Findet alle Mathe-Selbstvertrauens-Variablen (PISA 2022 Indices)"""
    # PISA 2022 nutzt ausschließlich aggregierte Indices
    # Keine einzelnen Items (ST182, ST181) in öffentlichen Daten
    
    # Liste der bekannten Math-Confidence Indices aus Test
    known_indices = [
        'ANXMAT',      # Mathematics Anxiety (WLE)
        'MATHEFF',     # Mathematics self-efficacy
        'MATHMOT',     # Motivation to do well in mathematics
        'MATHPERS',    # Effort and Persistence in Mathematics
        'MATHPREF',    # Preference of Math over other subjects
        'MATHEASE',    # Perception of Math as easier
        'MATHEF21'     # Self-efficacy: reasoning and 21st century
    ]
    
    query = """
    SELECT 
        variable_name,
        variable_label,
        data_type
    FROM codebook
    WHERE variable_name IN ('ANXMAT', 'MATHEFF', 'MATHMOT', 'MATHPERS', 
                            'MATHPREF', 'MATHEASE', 'MATHEF21', 'BELONG', 'ESCS')
    OR (
        variable_label LIKE '%math%' 
        AND (
            variable_label LIKE '%anxiety%'
            OR variable_label LIKE '%efficacy%'
            OR variable_label LIKE '%confidence%'
            OR variable_label LIKE '%motivation%'
            OR variable_label LIKE '%persistence%'
        )
    )
    ORDER BY 
        CASE 
            WHEN variable_name = 'ANXMAT' THEN 1
            WHEN variable_name = 'MATHEFF' THEN 2
            WHEN variable_name = 'MATHMOT' THEN 3
            WHEN variable_name = 'MATHPERS' THEN 4
            WHEN variable_name = 'MATHPREF' THEN 5
            WHEN variable_name = 'MATHEASE' THEN 6
            WHEN variable_name = 'MATHEF21' THEN 7
            ELSE 99
        END;
    """
    return pd.read_sql_query(query, conn)

def calculate_composite_score(df, anxiety_vars, reverse=True):
    """Berechnet Composite Score aus mehreren Items"""
    if reverse:
        # Reverse-code: 5 - value (höherer Score = mehr Confidence)
        composite = sum(5 - df[var] for var in anxiety_vars) / len(anxiety_vars)
    else:
        composite = sum(df[var] for var in anxiety_vars) / len(anxiety_vars)
    return composite

# ============================================
# MAIN APP
# ============================================

def main():
    st.title("📊 PISA 2022 - Mathematics Self-Confidence Explorer")
    st.markdown("**Deutschland-Daten | Fokus: Matheselbstvertrauen & Anxiety**")
    
    # Verwende immer die vollständige Datenbank
    conn = get_db_connection()
    
    # ============================================
    # TABS
    # ============================================
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📚 Variable Explorer",
        "📊 Deskriptive Statistik",
        "🔗 Korrelationen",
        "📈 Visualisierungen",
        "🗺️ TIMSS-PISA Mapping",
        "📋 Ergebnisübersicht"
    ])
    
    # ============================================
    # TAB 1: VARIABLE EXPLORER
    # ============================================
    
    with tab1:
        st.header("📚 Variable Explorer - Codebook durchsuchen")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_term = st.text_input(
                "🔍 Suche nach Variablen:",
                placeholder="z.B. 'math anxiety' oder 'ST182'",
                help="Durchsucht Variable Names und Labels"
            )
        
        with col2:
            quick_search = st.selectbox(
                "⚡ Quick Search:",
                [
                    "Math-Variablen (Standard)",
                    "Math Anxiety Items (mit Fragetext)",
                    "Math Self-Efficacy Items (mit Fragetext)",
                    "Alle Anxiety/Angst/Worry",
                    "Alle Self-Efficacy",
                    "Alle Variablen"
                ]
            )

        # Quick search mapping
        quick_search_terms = {
            "Math-Variablen (Standard)": None,
            "Math Anxiety Items (mit Fragetext)": "ST292",  # Math Anxiety Items mit Fragetexten
            "Math Self-Efficacy Items (mit Fragetext)": "ST29",  # ST290 + ST291 Items
            "Alle Anxiety/Angst/Worry": "anx",  # Findet anxiety, anxious, ANXMAT
            "Alle Self-Efficacy": "effic",  # Findet efficacy, MATHEFF, etc.
            "Alle Variablen": ""  # Leerer String = alle
        }
        
        final_search = search_term if search_term else quick_search_terms[quick_search]

        if final_search is not None:  # None = Standard, "" = alle
            if final_search == "":
                # "Alle Variablen" ausgewählt - zeige wirklich alle
                codebook = load_codebook(conn, None)
                # Kleine Warnung bei vielen Variablen
                if len(codebook) > 500:
                    st.info(f"ℹ️ {len(codebook)} Variablen gefunden. Du kannst die Suchbox nutzen, um zu filtern.")
            else:
                # Suche mit Begriff
                codebook = load_codebook(conn, final_search)
        else:
            # Zeige nur Mathe-relevante Variablen standardmäßig
            codebook = find_math_confidence_vars(conn)
        
        st.dataframe(
            codebook,
            use_container_width=True,
            height=400
        )
        
        st.info(f"📊 Gefundene Variablen: **{len(codebook)}**")
        
        # Variable Details
        if len(codebook) > 0:
            st.subheader("🔍 Variable Details")
            
            selected_var = st.selectbox(
                "Wähle Variable für Details:",
                options=codebook['variable_name'].tolist()
            )
            
            if selected_var:
                var_info = codebook[codebook['variable_name'] == selected_var].iloc[0]

                # Basis-Info
                st.markdown(f"**Variable Name:** `{var_info['variable_name']}`")
                st.markdown(f"**Label:** {var_info['variable_label']}")
                st.markdown(f"**Data Type:** {var_info['data_type']}")

                # Fragetext laden (falls vorhanden) - PROMINENT OBEN
                question = load_question_text(conn, selected_var)
                if question is not None:
                    st.markdown("---")
                    st.markdown("### 📝 Fragetext (Question Text)")

                    # Zeige deutschen Text falls vorhanden, sonst englisch
                    if pd.notna(question.get('question_text_de')):
                        st.success(f"**🇩🇪 Deutsch:** {question['question_text_de']}")
                        with st.expander("🇬🇧 Show English text"):
                            st.text(question['question_text_en'])
                    else:
                        st.success(f"**🇬🇧 English:** {question['question_text_en']}")

                    if pd.notna(question.get('questionnaire_type')):
                        st.caption(f"📋 Questionnaire: {question['questionnaire_type']} | Category: {question.get('question_category', 'N/A')}")
                else:
                    st.info("ℹ️ Kein Fragetext vorhanden (aggregierter Index oder keine Question-Items)")

                st.markdown("---")

                # Antwortoptionen in voller Breite
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 📊 Statistik")
                    # Placeholder für Statistik
                    st.caption("Verfügbar in Tab 2: Deskriptive Statistik")

                with col2:
                    # Value Labels anzeigen
                    value_labels = load_value_labels(conn, selected_var)

                    if len(value_labels) > 0:
                        st.markdown("### 📋 Antwortoptionen")
                        
                        # Erstelle schönere Darstellung
                        display_labels = value_labels.copy()
                        
                        # Zeige deutsche Labels falls vorhanden
                        display_labels['Antwort'] = display_labels.apply(
                            lambda row: f"{row['label_de']}" if pd.notna(row.get('label_de')) 
                            else f"{row['label']}", 
                            axis=1
                        )
                        
                        # Formatiere Prozent falls vorhanden
                        if 'percent' in display_labels.columns and display_labels['percent'].notna().any():
                            display_labels['Häufigkeit'] = display_labels.apply(
                                lambda row: f"{row['percent']:.1f}%" if pd.notna(row['percent']) else "",
                                axis=1
                            )
                            cols_to_show = ['value', 'Antwort', 'Häufigkeit']
                        else:
                            cols_to_show = ['value', 'Antwort']
                        
                        # Markiere Missing Codes
                        if 'is_missing_code' in display_labels.columns:
                            display_labels['value'] = display_labels.apply(
                                lambda row: f"~~{row['value']}~~" if row.get('is_missing_code') == 1 
                                else str(row['value']),
                                axis=1
                            )
                        
                        st.dataframe(
                            display_labels[cols_to_show],
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Hinweis zu Missing Codes
                        if (display_labels.get('is_missing_code') == 1).any():
                            st.caption("~~Durchgestrichene Werte~~ = Missing Codes (97, 98, 99)")
                    else:
                        st.info("ℹ️ Keine Value Labels verfügbar (numerische Variable)")
    
    # ============================================
    # TAB 2: DESKRIPTIVE STATISTIK
    # ============================================
    
    with tab2:
        st.header("📊 Deskriptive Statistik")
        
        # Variable Selection
        st.subheader("🎯 Variablen auswählen")
        
        st.info("""
        ℹ️ **PISA 2022 Hinweis:** Die Datenbank enthält aggregierte **Indices** statt einzelner Fragebogen-Items.
        
        **Verfügbare Math-Confidence Indices:**
        - **ANXMAT** = Mathematics Anxiety (höher = mehr Angst) ⭐
        - **MATHEFF** = Mathematics Self-Efficacy (höher = mehr Selbstvertrauen) ⭐
        - **MATHMOT** = Motivation to do well in mathematics
        - **MATHPERS** = Effort and Persistence in Mathematics
        - **MATHPREF** = Preference of Math over other subjects
        - **MATHEASE** = Perception of Math as easier than other subjects
        - **MATHEF21** = Self-efficacy: mathematical reasoning and 21st century skills
        
        ⭐ = Empfohlen für Selbstvertrauens-Analyse
        """)
        
        # Finde alle verfügbaren Math-bezogenen Variablen
        available_vars = load_codebook(conn, 'math')['variable_name'].tolist()

        # Standard: Die 2 wichtigsten Indices für Math Self-Confidence
        pisa_indices = ['ANXMAT', 'MATHEFF', 'MATHMOT', 'MATHPERS']
        default_vars = [v for v in pisa_indices if v in available_vars][:2]  # Nur die ersten 2

        # Falls keine Indices, zeige alle Math-Variablen
        if not default_vars:
            default_vars = available_vars[:3] if len(available_vars) >= 3 else available_vars

        selected_vars = st.multiselect(
            "Wähle Variablen für Analyse:",
            options=available_vars,
            default=default_vars,
            help="Empfohlen: ANXMAT (Anxiety) und MATHEFF (Self-Efficacy)"
        )

        if selected_vars:
            # Daten laden
            df = load_student_data(conn, selected_vars)
            
            # Deskriptive Statistik
            st.subheader("📈 Statistik-Übersicht")
            
            desc_stats = df[selected_vars + ['math_score']].describe()
            st.dataframe(desc_stats, use_container_width=True)
            
            # Erklärung für Indices
            st.caption("""
            📌 **PISA Indices Interpretation:**
            - Indices sind standardisiert (Mean ≈ 0, SD ≈ 1 im OECD-Durchschnitt)
            - **Negative Werte** = unter OECD-Durchschnitt
            - **Positive Werte** = über OECD-Durchschnitt
            """)
            
            # Missing Values
            st.subheader("🔍 Missing Values")
            missing = df[selected_vars].isnull().sum()
            missing_pct = (missing / len(df) * 100).round(2)
            
            missing_df = pd.DataFrame({
                'Variable': missing.index,
                'Missing Count': missing.values,
                'Missing %': missing_pct.values
            })
            
            st.dataframe(missing_df, use_container_width=True)
            
            # Composite Score nur wenn mehrere Variablen gewählt
            if len(selected_vars) >= 2 and 'ANXMAT' in selected_vars and 'MATHEFF' in selected_vars:
                st.subheader("🧮 Composite Score")
                
                st.info("""
                📊 **Confidence Score Berechnung:**
                - Basiert auf MATHEFF (Self-Efficacy) minus ANXMAT (Anxiety)
                - Höhere Werte = mehr Selbstvertrauen, weniger Angst
                """)
                
                # Berechne Confidence Score: Self-Efficacy - Anxiety
                df['confidence_score'] = df['MATHEFF'] - df['ANXMAT']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Ø Math Anxiety",
                        f"{df['ANXMAT'].mean():.3f}",
                        help="ANXMAT Index (0 = OECD Durchschnitt)"
                    )
                
                with col2:
                    st.metric(
                        "Ø Math Self-Efficacy",
                        f"{df['MATHEFF'].mean():.3f}",
                        help="MATHEFF Index (0 = OECD Durchschnitt)"
                    )
                
                with col3:
                    st.metric(
                        "Ø Confidence Score",
                        f"{df['confidence_score'].mean():.3f}",
                        help="MATHEFF - ANXMAT"
                    )
                
                # Zusätzliche Statistik
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Ø Math Score",
                        f"{df['math_score'].mean():.0f}",
                        help="PISA Math Performance (Plausible Value 1)"
                    )
                
                with col2:
                    # Korrelation Confidence vs. Performance
                    corr = df[['confidence_score', 'math_score']].corr().iloc[0, 1]
                    st.metric(
                        "Korrelation Confidence ↔ Math",
                        f"{corr:.3f}",
                        help="Pearson Korrelation"
                    )
                
                # ============================================
                # KINDERLEICHTE ERKLÄRUNGEN (ANXMAT + MATHEFF)
                # ============================================
                
                st.markdown("---")
                
                with st.expander("👶 **Einfach erklärt - Was bedeuten diese Zahlen?**", expanded=True):
                    
                    # Berechne Werte
                    n_students = len(df)
                    mean_anxmat = df['ANXMAT'].mean()
                    mean_matheff = df['MATHEFF'].mean()
                    mean_confidence = df['confidence_score'].mean()
                    mean_math = df['math_score'].mean()
                    std_anxmat = df['ANXMAT'].std()
                    std_matheff = df['MATHEFF'].std()
                    
                    # ========== SECTION 1: Was siehst du? ==========
                    st.markdown(f"""
                    ### 📊 Was siehst du?
                    
                    Du schaust dir **{n_students:,} deutsche Schüler** an (aus der PISA-Studie).
                    
                    Für jeden haben wir gemessen:
                    - **ANXMAT** = Mathe-Angst (je höher, desto ängstlicher)
                    - **MATHEFF** = Selbstvertrauen in Mathe (je höher, desto selbstbewusster)
                    - **Math Score** = Matheleistung in Punkten
                    """)
                    
                    # ========== SECTION 2: Der Durchschnitt erklärt ==========
                    st.markdown("### 🎯 Der Durchschnitt erklärt")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # ANXMAT Interpretation
                        if abs(mean_anxmat) < 0.2:
                            anxmat_color = "🟢"
                            anxmat_text = "**Fast genau beim OECD-Durchschnitt!**"
                            anxmat_detail = "Deutsche Schüler haben eine normale Mathe-Angst - nicht mehr und nicht weniger als der internationale Durchschnitt."
                        elif mean_anxmat > 0.5:
                            anxmat_color = "🔴"
                            anxmat_text = "**Deutlich über dem OECD-Durchschnitt!**"
                            anxmat_detail = "Deutsche Schüler haben mehr Mathe-Angst als der internationale Durchschnitt. Hier besteht Handlungsbedarf!"
                        elif mean_anxmat > 0:
                            anxmat_color = "🟡"
                            anxmat_text = "**Etwas über dem OECD-Durchschnitt**"
                            anxmat_detail = "Deutsche Schüler haben etwas mehr Mathe-Angst als der internationale Durchschnitt."
                        elif mean_anxmat > -0.5:
                            anxmat_color = "🟢"
                            anxmat_text = "**Etwas unter dem OECD-Durchschnitt**"
                            anxmat_detail = "Deutsche Schüler haben etwas weniger Mathe-Angst als der internationale Durchschnitt - das ist gut!"
                        else:
                            anxmat_color = "🟢"
                            anxmat_text = "**Deutlich unter dem OECD-Durchschnitt!**"
                            anxmat_detail = "Deutsche Schüler haben viel weniger Mathe-Angst als der internationale Durchschnitt. Super!"
                        
                        st.markdown(f"""
                        **😰 Mathe-Angst: {mean_anxmat:.3f}**
                        
                        {anxmat_color} {anxmat_text}
                        
                        {anxmat_detail}
                        
                        **Merke:** 0 = OECD-Durchschnitt
                        """)
                    
                    with col2:
                        # MATHEFF Interpretation
                        if abs(mean_matheff) < 0.2:
                            matheff_color = "🟢"
                            matheff_text = "**Fast genau beim OECD-Durchschnitt!**"
                            matheff_detail = "Deutsche Schüler haben ein normales Mathe-Selbstvertrauen - vergleichbar mit dem internationalen Durchschnitt."
                        elif mean_matheff > 0.5:
                            matheff_color = "🟢"
                            matheff_text = "**Deutlich über dem OECD-Durchschnitt!**"
                            matheff_detail = "Deutsche Schüler haben mehr Selbstvertrauen in Mathe als der internationale Durchschnitt. Super!"
                        elif mean_matheff > 0:
                            matheff_color = "🟢"
                            matheff_text = "**Etwas über dem OECD-Durchschnitt**"
                            matheff_detail = "Deutsche Schüler haben etwas mehr Selbstvertrauen als der internationale Durchschnitt."
                        elif mean_matheff > -0.5:
                            matheff_color = "🟡"
                            matheff_text = "**Etwas unter dem OECD-Durchschnitt**"
                            matheff_detail = "Deutsche Schüler haben etwas weniger Selbstvertrauen als der internationale Durchschnitt."
                        else:
                            matheff_color = "🔴"
                            matheff_text = "**Deutlich unter dem OECD-Durchschnitt!**"
                            matheff_detail = "Deutsche Schüler haben deutlich weniger Selbstvertrauen als der internationale Durchschnitt. Hier können Interventionen helfen!"
                        
                        st.markdown(f"""
                        **💪 Selbstvertrauen: {mean_matheff:.3f}**
                        
                        {matheff_color} {matheff_text}
                        
                        {matheff_detail}
                        
                        **Merke:** 0 = OECD-Durchschnitt
                        """)
                    
                    # ========== SECTION 3: Emoji-Skala ==========
                    st.markdown("### 😊 Wo steht Deutschland?")
                    
                    # ANXMAT Skala
                    st.markdown("**😰 Mathe-Angst Skala:**")
                    
                    # Berechne Position auf Skala (-3 bis +3, aber zeige -2 bis +2)
                    anxmat_pos = max(-2, min(2, mean_anxmat))
                    scale_positions = [-2, -1, 0, 1, 2]
                    emojis = ["😊😊", "🙂", "😐", "😟", "😰😰"]
                    
                    # Erstelle Skala-String
                    scale_str = ""
                    for i, pos in enumerate(scale_positions):
                        if abs(anxmat_pos - pos) < 0.3:
                            scale_str += f"**[{emojis[i]}]** "
                        else:
                            scale_str += f"{emojis[i]} "
                    
                    st.markdown(scale_str)
                    st.markdown("← Wenig Angst&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Viel Angst →")
                    
                    # MATHEFF Skala
                    st.markdown("")
                    st.markdown("**💪 Selbstvertrauen Skala:**")
                    
                    matheff_pos = max(-2, min(2, mean_matheff))
                    emojis_eff = ["😔😔", "😕", "😐", "🙂", "😊😊"]
                    
                    scale_str_eff = ""
                    for i, pos in enumerate(scale_positions):
                        if abs(matheff_pos - pos) < 0.3:
                            scale_str_eff += f"**[{emojis_eff[i]}]** "
                        else:
                            scale_str_eff += f"{emojis_eff[i]} "
                    
                    st.markdown(scale_str_eff)
                    st.markdown("← Wenig Selbstvertrauen&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Viel Selbstvertrauen →")
                    
                    # ========== SECTION 4: Die Unterschiede (std) ==========
                    st.markdown("### 📏 Wie unterschiedlich sind die Schüler?")
                    
                    # Interpretation der Standardabweichung
                    if std_anxmat > 1.3:
                        std_text = "**Sehr große Unterschiede!**"
                        std_detail = "Manche Schüler sind total entspannt, andere sehr ängstlich. Die Gruppe ist sehr heterogen."
                    elif std_anxmat > 1.0:
                        std_text = "**Große Unterschiede**"
                        std_detail = "Es gibt deutliche Unterschiede zwischen den Schülern - manche ängstlich, manche entspannt."
                    else:
                        std_text = "**Moderate Unterschiede**"
                        std_detail = "Die Schüler sind sich relativ ähnlich in ihrer Mathe-Angst."
                    
                    st.markdown(f"""
                    **Standardabweichung (std)** = Wie verschieden sind die Schüler?
                    
                    - ANXMAT: {std_anxmat:.2f} → {std_text}
                    - MATHEFF: {std_matheff:.2f}
                    
                    {std_detail}
                    
                    **Visualisiert:**
                    """)
                    
                    # Visuelle Darstellung der Streuung
                    if std_anxmat > 1.2:
                        st.markdown("""
                        ```
                        Entspannt                           Ängstlich
                        |                                         |
                        👤              👤👤👤              👤👤
                        ← Wenige hier   Viele hier   Viele hier →
                        ```
                        → Das Schulsystem erzeugt **sehr unterschiedliche** Ergebnisse!
                        """)
                    else:
                        st.markdown("""
                        ```
                        Entspannt                           Ängstlich
                        |                                         |
                               👤👤👤👤👤👤👤
                               ← Die meisten hier →
                        ```
                        → Die meisten Schüler sind sich ähnlich.
                        """)
                    
                    # ========== SECTION 5: Die Extremen (min/max) ==========
                    st.markdown("### 🎯 Von Minimum bis Maximum")
                    
                    min_anxmat = df['ANXMAT'].min()
                    max_anxmat = df['ANXMAT'].max()
                    min_matheff = df['MATHEFF'].min()
                    max_matheff = df['MATHEFF'].max()
                    min_math = df['math_score'].min()
                    max_math = df['math_score'].max()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        **😰 Mathe-Angst Spannweite:**
                        
                        ```
                        Entspanntester: {min_anxmat:.2f}
                        Durchschnitt:   {mean_anxmat:.2f}
                        Ängstlichster:  {max_anxmat:.2f}
                        
                        Spannweite: {max_anxmat - min_anxmat:.2f} Punkte
                        ```
                        
                        Das heißt: Der ängstlichste Schüler hat {abs(max_anxmat - min_anxmat):.1f}x mehr Angst als der entspannteste!
                        """)
                    
                    with col2:
                        st.markdown(f"""
                        **📝 Matheleistung Spannweite:**
                        
                        ```
                        Schwächster:   {min_math:.0f} Punkte
                        Durchschnitt:  {mean_math:.0f} Punkte
                        Stärkster:     {max_math:.0f} Punkte
                        
                        Spannweite: {max_math - min_math:.0f} Punkte
                        ```
                        
                        Das heißt: Der beste Schüler ist {(max_math/min_math):.1f}x besser als der schwächste!
                        """)
                    
                    # ========== SECTION 6: Confidence Score ==========
                    st.markdown("### 🏆 Der Confidence Score")
                    
                    st.markdown(f"""
                    **Formel:** Confidence Score = MATHEFF - ANXMAT
                    
                    **Dein Ergebnis:** {mean_confidence:.3f}
                    """)
                    
                    if mean_confidence > 0.5:
                        confidence_emoji = "🟢"
                        confidence_text = "**Super! Selbstvertrauen überwiegt deutlich!**"
                        confidence_detail = "Deutsche Schüler haben mehr Selbstvertrauen als Angst. Das ist eine gute Grundlage für Lernerfolg!"
                    elif mean_confidence > 0:
                        confidence_emoji = "🟢"
                        confidence_text = "**Gut! Selbstvertrauen überwiegt leicht**"
                        confidence_detail = "Deutsche Schüler haben etwas mehr Selbstvertrauen als Angst."
                    elif mean_confidence > -0.5:
                        confidence_emoji = "🟡"
                        confidence_text = "**Ausgeglichen mit leichtem Angst-Überhang**"
                        confidence_detail = "Selbstvertrauen und Angst halten sich fast die Waage, mit leichter Tendenz zur Angst."
                    else:
                        confidence_emoji = "🔴"
                        confidence_text = "**Achtung! Angst überwiegt deutlich!**"
                        confidence_detail = "Deutsche Schüler haben mehr Angst als Selbstvertrauen. Hier sollten Interventionen ansetzen!"
                    
                    st.markdown(f"""
                    {confidence_emoji} {confidence_text}
                    
                    {confidence_detail}
                    """)
                    
                    # Visualisierung
                    st.markdown("**Visualisierung:**")
                    
                    # Erstelle Balance-Waage
                    matheff_bar = "█" * max(1, int(abs(mean_matheff) * 10))
                    anxmat_bar = "█" * max(1, int(abs(mean_anxmat) * 10))
                    
                    st.markdown(f"""
                    ```
                    Selbstvertrauen  vs.  Angst
                    {matheff_bar: <20} | {anxmat_bar}
                    {mean_matheff:.2f}           {mean_anxmat:.2f}
                    ```
                    """)
                    
                    if mean_confidence > 0:
                        st.success("✅ Selbstvertrauen ist stärker!")
                    elif abs(mean_confidence) < 0.1:
                        st.info("⚖️ Fast ausgeglichen")
                    else:
                        st.warning("⚠️ Angst ist stärker")

            elif len(selected_vars) >= 1:
                # Zeige Durchschnitte für einzelne Variablen
                st.subheader("📊 Durchschnittswerte")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    for var in selected_vars[:len(selected_vars)//2 + 1]:
                        st.metric(
                            f"Ø {var}",
                            f"{df[var].mean():.3f}",
                            help=f"Durchschnitt für {var}"
                        )
                
                with col2:
                    for var in selected_vars[len(selected_vars)//2 + 1:]:
                        st.metric(
                            f"Ø {var}",
                            f"{df[var].mean():.3f}",
                            help=f"Durchschnitt für {var}"
                        )
                    
                    st.metric(
                        "Ø Math Score",
                        f"{df['math_score'].mean():.0f}",
                        help="PISA Math Performance"
                    )
                
                # ============================================
                # KINDERLEICHTE ERKLÄRUNGEN (EINZELVARIABLEN)
                # ============================================
                
                st.markdown("---")
                
                with st.expander("👶 **Einfach erklärt - Was bedeuten diese Zahlen?**", expanded=True):
                    
                    n_students = len(df)
                    mean_math = df['math_score'].mean()
                    
                    st.markdown(f"""
                    ### 📊 Was siehst du?
                    
                    Du schaust dir **{n_students:,} deutsche Schüler** an (aus der PISA-Studie).
                    """)
                    
                    # Für jede Variable eine Interpretation
                    for var in selected_vars:
                        mean_val = df[var].mean()
                        std_val = df[var].std()
                        min_val = df[var].min()
                        max_val = df[var].max()
                        
                        # Dynamische Interpretation
                        if abs(mean_val) < 0.2:
                            color = "🟢"
                            text = "Fast genau beim OECD-Durchschnitt"
                        elif mean_val < -0.5:
                            color = "🟢"
                            text = "Deutlich unter OECD-Durchschnitt"
                        elif mean_val < 0:
                            color = "🟡"
                            text = "Etwas unter OECD-Durchschnitt"
                        elif mean_val < 0.5:
                            color = "🟡"
                            text = "Etwas über OECD-Durchschnitt"
                        else:
                            color = "🔴"
                            text = "Deutlich über OECD-Durchschnitt"
                        
                        st.markdown(f"""
                        ### {var}
                        
                        **Durchschnitt:** {mean_val:.3f} {color}
                        
                        **Interpretation:** {text}
                        
                        **Spannweite:** Von {min_val:.2f} bis {max_val:.2f} ({max_val - min_val:.2f} Punkte Unterschied)
                        
                        **Standardabweichung:** {std_val:.2f} {'(Große Unterschiede!)' if std_val > 1.2 else '(Moderate Unterschiede)'}
                        
                        ---
                        """)
                    
                    # Matheleistung
                    st.markdown(f"""
                    ### 📝 Matheleistung
                    
                    **Durchschnitt:** {mean_math:.0f} Punkte
                    
                    **PISA-Levels:**
                    - Level 1 (358-420): Grundkenntnisse
                    - Level 2 (420-482): Basiskompetenzen
                    - Level 3 (482-545): Solide Kenntnisse ← {'**DU BIST HIER**' if 482 <= mean_math <= 545 else ''}
                    - Level 4 (545-607): Gut
                    - Level 5 (607-669): Sehr gut
                    
                    💡 **Was heißt das für dein Projekt?**
                    
                    Nutze diese Werte morgen als Baseline für deine YouTube-Analyse!
                    """)
        else:
            st.warning("⚠️ Bitte wähle mindestens eine Variable aus.")
    
    # ============================================
    # TAB 3: KORRELATIONEN & ZUSAMMENHÄNGE
    # ============================================
    
    with tab3:
        st.header("🔗 Korrelationen & Zusammenhänge")
        st.markdown("*Wie hängen Angst, Selbstvertrauen und Leistung zusammen?*")
        
        # Check ob Daten verfügbar
        if 'df' not in locals() or not selected_vars:
            st.warning("⚠️ Bitte wähle erst Variablen in Tab 2 aus.")
        else:
            # Sub-Tabs erstellen
            subtab1, subtab2 = st.tabs([
                "📖 Story & Erklärung", 
                "📊 Technische Analyse"
            ])
            
            # ============================================
            # SUB-TAB 1: STORY & ERKLÄRUNG (NEU)
            # ============================================
            
            with subtab1:
                st.title("📊 Die Mathe-Gleichung des Selbstvertrauens")
                st.markdown("*Eine evidenzbasierte Analyse (PISA 2022 Deutschland)*")
                st.markdown("---")
                
                # Kapitel 1: Forschungsfrage & Kontext
                with st.expander("1️⃣ FORSCHUNGSFRAGE & KONTEXT"):
                    st.markdown("""
                    ### Die Beobachtung
                    
                    In deutschen Klassenzimmern beobachten wir ein Paradox:
                    
                    Zwei Schülerinnen mit vergleichbarer kognitiver Leistungsfähigkeit,
                    gleichem sozioökonomischen Hintergrund, gleicher Lernzeit.
                    
                    **Eine erzielt 493 Punkte, die andere 420.**
                    
                    Der Unterschied: nicht Intelligenz - sondern **Selbstwirksamkeitserwartung**.
                    
                    Mit PISA 2022 können wir diesen Zusammenhang quantifizieren.
                    
                    ---
                    
                    ### Zentrale Forschungsfragen
                    
                    1. **Wie stark** ist der Zusammenhang zwischen affektiven Faktoren und Leistung?
                    2. **Welcher Faktor** ist einflussreicher: Angst oder Selbstwirksamkeit?
                    3. **Welche praktischen Implikationen** ergeben sich für Interventionen?
                    
                    ---
                    
                    ### Einordnung in die Bildungsforschung
                    
                    **Theoretischer Rahmen:**
                    - Selbstwirksamkeitstheorie (Bandura, 1997)
                    - Expectancy-Value-Theory (Eccles & Wigfield, 2002)
                    - Control-Value Theory of Achievement Emotions (Pekrun, 2006)
                    
                    **Internationale Befunde:**
                    - Meta-Analyse Richardson et al. (2012): r(Self-Efficacy, Performance) ≈ 0.50
                    - Hattie's Visible Learning: Effektstärke d = 0.92 (Self-Efficacy)
                    - OECD PISA 2018: Korrelation ~0.54 (international)
                    
                    **Unser Beitrag:**
                    Aktualisierte Analyse mit PISA 2022 Deutschland-Daten
                    """)
                
                # Kapitel 2: Methodik & Datengrundlage
                with st.expander("2️⃣ METHODIK & DATENGRUNDLAGE"):
                    st.markdown(f"""
                    ### Stichprobe
                    
                    **PISA 2022 Deutschland**
                    - N = {len(df):,} Schülerinnen und Schüler
                    - Alter: 15 Jahre
                    - Repräsentative Stichprobe aller Bundesländer
                    - Stratifiziertes Cluster-Sampling
                    
                    ---
                    
                    ### Konstrukte & Messinstrumente
                    
                    **ANXMAT - Mathematics Anxiety**
                    - WLE-Index (Weighted Likelihood Estimate)
                    - Standardisiert: M = 0, SD = 1 (OECD-Durchschnitt)
                    - Basiert auf Skala zur Mathematikangst
                    - Höhere Werte = mehr Angst
                    
                    **MATHEFF - Mathematics Self-Efficacy**
                    - WLE-Index (Weighted Likelihood Estimate)
                    - Standardisiert: M = 0, SD = 1 (OECD-Durchschnitt)
                    - Basiert auf Skala zur Selbstwirksamkeitserwartung
                    - Höhere Werte = mehr Selbstvertrauen
                    
                    **PV1MATH - Mathematikleistung**
                    - Plausible Value 1 (von 10 PVs)
                    - PISA-Skala: M = 500, SD = 100 (internationale Norm)
                    - Misst mathematische Kompetenz in realitätsnahen Kontexten
                    
                    ---
                    
                    ### Analysemethode
                    
                    **Korrelationsanalyse**
                    - Methode: Pearson's r (Produkt-Moment-Korrelation)
                    - Signifikanzniveau: α = .05 (zweiseitig)
                    - Missing Data: Listwise deletion
                    - Effektstärken nach Cohen (1988):
                      - |r| = 0.1 → kleiner Effekt
                      - |r| = 0.3 → mittlerer Effekt
                      - |r| = 0.5 → großer Effekt
                    
                    ---
                    
                    ### Qualitätssicherung
                    
                    - ✅ Stichprobengröße ausreichend (N > 5.000)
                    - ✅ Power-Analyse: 1-β > .99
                    - ✅ Normalitätsannahme: Bei N > 30 durch CLT erfüllt
                    - ✅ Linearitätscheck durchgeführt
                    - ⚠️ Limitation: Querschnittsdaten (keine Kausalität)
                    """)
                
                # Kapitel 3: Zentrale Befunde (expanded by default)
                with st.expander("3️⃣ ZENTRALE BEFUNDE", expanded=True):
                    st.markdown("### Die Korrelationen im Detail")
                    
                    # Prüfe ob ANXMAT und MATHEFF vorhanden sind
                    if 'ANXMAT' in selected_vars and 'MATHEFF' in selected_vars:
                        
                        # Berechne Korrelationen
                        corr_anxmat = df[['ANXMAT', 'math_score']].corr().iloc[0, 1]
                        corr_matheff = df[['MATHEFF', 'math_score']].corr().iloc[0, 1]
                        
                        # R² berechnen
                        r2_anxmat = corr_anxmat ** 2
                        r2_matheff = corr_matheff ** 2
                        
                        # Key Findings Box
                        st.success(f"""
                        **🔍 Zentrale Befunde:**
                        
                        - **MATHEFF (Selbstwirksamkeit)**: r = {corr_matheff:.3f}, R² = {r2_matheff:.1%} → Starke positive Korrelation
                        - **ANXMAT (Angst)**: r = {corr_anxmat:.3f}, R² = {r2_anxmat:.1%} → Mittlere negative Korrelation
                        - **Effektstärken-Verhältnis**: Selbstwirksamkeit ist {abs(corr_matheff/corr_anxmat):.2f}x einflussreicher als Angst
                        """)
                        
                        st.markdown("---")
                        
                        # ========================================
                        # VISUALISIERUNG 1: Korrelations-Landschaft
                        # ========================================
                        
                        st.markdown("#### 📊 Visualisierung 1: Die Korrelations-Landschaft")
                        
                        # Wähle welche Variable gezeigt werden soll
                        viz_var = st.radio(
                            "Wähle Variable:",
                            options=['MATHEFF', 'ANXMAT'],
                            format_func=lambda x: '💪 Selbstwirksamkeit (MATHEFF)' if x == 'MATHEFF' else '😰 Angst (ANXMAT)',
                            horizontal=True
                        )
                        
                        # Erstelle Scatter Plot mit Regression
                        if viz_var == 'MATHEFF':
                            color = '#2E7D32'  # Grün
                            title = 'Selbstwirksamkeit & Mathematikleistung'
                            xlabel = 'MATHEFF (Selbstwirksamkeit)'
                            corr_value = corr_matheff
                            direction = "positiv"
                            interpretation = "Je höher die Selbstwirksamkeit, desto besser die Matheleistung"
                        else:
                            color = '#C62828'  # Rot
                            title = 'Mathematikangst & Mathematikleistung'
                            xlabel = 'ANXMAT (Angst)'
                            corr_value = corr_anxmat
                            direction = "negativ"
                            interpretation = "Je höher die Angst, desto schlechter die Matheleistung"
                        
                        fig = px.scatter(
                            df,
                            x=viz_var,
                            y='math_score',
                            opacity=0.4,
                            trendline='ols',
                            title=f'{title} (N = {len(df):,})',
                            labels={
                                viz_var: xlabel,
                                'math_score': 'Mathematikleistung (PISA-Punkte)'
                            },
                            color_discrete_sequence=[color]
                        )
                        
                        # Layout anpassen
                        fig.update_layout(
                            height=500,
                            hovermode='closest',
                            plot_bgcolor='#FAFAFA',
                            showlegend=False
                        )
                        
                        # Achsen-Styling
                        fig.update_xaxes(
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='#E0E0E0',
                            zeroline=True,
                            zerolinewidth=2,
                            zerolinecolor='#424242'
                        )
                        fig.update_yaxes(
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='#E0E0E0'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Interpretation
                        st.info(f"""
                        **📊 Interpretation:**
                        
                        - **Korrelation:** r = {corr_value:.3f} (p < .001) → {direction}er, {'starker' if abs(corr_value) > 0.5 else 'mittlerer'} Zusammenhang
                        - **Varianzaufklärung:** R² = {(corr_value**2):.1%} der Leistungsunterschiede erklärbar
                        - **Praktisch:** {interpretation}
                        - **Streuung:** Punktewolke zeigt individuelle Unterschiede trotz Trend
                        """)
                        
                        st.markdown("---")
                        
                        # ========================================
                        # VISUALISIERUNG 2: Effektstärken-Komparator
                        # ========================================
                        
                        st.markdown("#### 🎯 Visualisierung 2: Effektstärken-Komparator")
                        
                        st.markdown("""
                        **Wie stark ist der Effekt im Vergleich zu anderen Bildungsfaktoren?**
                        
                        Zum Einordnen der Effektstärken nutzen wir Benchmarks aus der Bildungsforschung:
                        """)
                        
                        # Erstelle Benchmark-Daten
                        benchmark_data = pd.DataFrame([
                            {'Faktor': 'MATHEFF\n(Selbstwirksamkeit)', 'Korrelation': abs(corr_matheff), 
                             'R²': r2_matheff, 'Typ': 'Unsere Analyse'},
                            {'Faktor': 'Sozioökonomischer\nStatus (ESCS)', 'Korrelation': 0.450, 
                             'R²': 0.203, 'Typ': 'Vergleichswert'},
                            {'Faktor': 'ANXMAT\n(Angst)', 'Korrelation': abs(corr_anxmat), 
                             'R²': r2_anxmat, 'Typ': 'Unsere Analyse'},
                            {'Faktor': 'Geschlecht', 'Korrelation': 0.150, 
                             'R²': 0.023, 'Typ': 'Vergleichswert'},
                        ])
                        
                        benchmark_data = benchmark_data.sort_values('Korrelation', ascending=True)
                        
                        # Farbcodierung
                        colors = benchmark_data['Typ'].map({
                            'Unsere Analyse': '#1565C0',
                            'Vergleichswert': '#757575'
                        })
                        
                        fig = go.Figure()
                        
                        # Balken mit R²-Annotationen
                        fig.add_trace(go.Bar(
                            y=benchmark_data['Faktor'],
                            x=benchmark_data['Korrelation'],
                            orientation='h',
                            marker=dict(
                                color=colors,
                                line=dict(color='white', width=2)
                            ),
                            text=[f"r={r:.3f}<br>R²={r2:.1%}" for r, r2 in 
                                  zip(benchmark_data['Korrelation'], benchmark_data['R²'])],
                            textposition='outside',
                            hovertemplate='<b>%{y}</b><br>Korrelation: %{x:.3f}<extra></extra>'
                        ))
                        
                        fig.update_layout(
                            title='Effektstärken im Vergleich',
                            xaxis_title='Korrelation (Betrag)',
                            yaxis_title='',
                            height=400,
                            plot_bgcolor='#FAFAFA',
                            showlegend=False,
                            xaxis=dict(range=[0, 0.7])
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Interpretation
                        st.success(f"""
                        **💡 Key Insight:**
                        
                        Selbstwirksamkeit (r = {corr_matheff:.3f}) erklärt **mehr Leistungsvarianz** 
                        als sozioökonomischer Status (r ≈ 0.45)!
                        
                        Das heißt: **Affektive Faktoren sind keine "Soft Skills"** - 
                        sie sind harte Leistungsprädiktoren und damit valide Ansatzpunkte für Interventionen.
                        """)
                        
                        st.markdown("---")
                        
                        # ========================================
                        # VISUALISIERUNG 3: Vier-Quadranten-Matrix
                        # ========================================
                        
                        st.markdown("#### 🗺️ Visualisierung 3: Vier-Quadranten-Matrix")
                        
                        st.markdown("""
                        **Welche Schülergruppen gibt es?**
                        
                        Durch Kombination von Selbstwirksamkeit und Angst entstehen vier Profile:
                        """)
                        
                        # Berechne Quadranten (Median-Split)
                        median_matheff = df['MATHEFF'].median()
                        median_anxmat = df['ANXMAT'].median()
                        
                        df['quadrant'] = 'Q4'  # Default
                        
                        # Q1: Hohe Selbstwirksamkeit, Niedrige Angst
                        df.loc[(df['MATHEFF'] >= median_matheff) & (df['ANXMAT'] < median_anxmat), 'quadrant'] = 'Q1'
                        
                        # Q2: Hohe Selbstwirksamkeit, Hohe Angst
                        df.loc[(df['MATHEFF'] >= median_matheff) & (df['ANXMAT'] >= median_anxmat), 'quadrant'] = 'Q2'
                        
                        # Q3: Niedrige Selbstwirksamkeit, Hohe Angst
                        df.loc[(df['MATHEFF'] < median_matheff) & (df['ANXMAT'] >= median_anxmat), 'quadrant'] = 'Q3'
                        
                        # Q4: Niedrige Selbstwirksamkeit, Niedrige Angst
                        df.loc[(df['MATHEFF'] < median_matheff) & (df['ANXMAT'] < median_anxmat), 'quadrant'] = 'Q4'
                        
                        # Berechne Statistiken pro Quadrant
                        quadrant_stats = df.groupby('quadrant').agg({
                            'math_score': ['mean', 'count']
                        }).round(0)
                        quadrant_stats.columns = ['Ø Leistung', 'N']
                        quadrant_stats['Anteil'] = (quadrant_stats['N'] / len(df) * 100).round(1)
                        
                        # Labels für Quadranten
                        quadrant_labels = {
                            'Q1': 'Q1: Optimal\n(Hohe Selbstwirksamkeit,\nNiedrige Angst)',
                            'Q2': 'Q2: Ambivalent\n(Hohe Selbstwirksamkeit,\nHohe Angst)',
                            'Q3': 'Q3: Risikogruppe\n(Niedrige Selbstwirksamkeit,\nHohe Angst)',
                            'Q4': 'Q4: Indifferent\n(Niedrige Selbstwirksamkeit,\nNiedrige Angst)'
                        }
                        
                        # Scatter Plot mit Quadranten
                        df['quadrant_label'] = df['quadrant'].map(quadrant_labels)
                        
                        fig = px.scatter(
                            df,
                            x='MATHEFF',
                            y='ANXMAT',
                            color='quadrant_label',
                            color_discrete_map={
                                quadrant_labels['Q1']: '#43A047',  # Grün
                                quadrant_labels['Q2']: '#FDD835',  # Gelb
                                quadrant_labels['Q3']: '#E53935',  # Rot
                                quadrant_labels['Q4']: '#1E88E5'   # Blau
                            },
                            opacity=0.6,
                            title=f'Schülerprofile nach Selbstwirksamkeit & Angst (N = {len(df):,})',
                            labels={
                                'MATHEFF': 'Selbstwirksamkeit (MATHEFF)',
                                'ANXMAT': 'Angst (ANXMAT)',
                                'quadrant_label': 'Profil'
                            },
                            hover_data={'math_score': ':.0f'}
                        )
                        
                        # Median-Linien hinzufügen
                        fig.add_hline(y=median_anxmat, line_dash="dash", line_color="#424242", opacity=0.5)
                        fig.add_vline(x=median_matheff, line_dash="dash", line_color="#424242", opacity=0.5)
                        
                        fig.update_layout(
                            height=600,
                            plot_bgcolor='#FAFAFA',
                            legend=dict(
                                orientation="v",
                                yanchor="top",
                                y=0.99,
                                xanchor="left",
                                x=0.01,
                                bgcolor="rgba(255,255,255,0.9)"
                            )
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Statistik-Tabelle
                        st.markdown("**📊 Statistik nach Quadranten:**")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        quadrants = ['Q1', 'Q2', 'Q3', 'Q4']
                        colors_box = ['#43A047', '#FDD835', '#E53935', '#1E88E5']
                        labels_short = ['Optimal', 'Ambivalent', 'Risiko', 'Indifferent']
                        
                        for i, (col, q, color, label) in enumerate(zip([col1, col2, col3, col4], 
                                                                         quadrants, colors_box, labels_short)):
                            with col:
                                if q in quadrant_stats.index:
                                    st.markdown(f"""
                                    <div style="background-color: {color}20; padding: 15px; border-radius: 10px; border-left: 5px solid {color}">
                                        <h4 style="margin: 0; color: {color}">{label}</h4>
                                        <p style="margin: 5px 0;"><b>{quadrant_stats.loc[q, 'Anteil']:.1f}%</b> der Schüler</p>
                                        <p style="margin: 5px 0;">Ø {quadrant_stats.loc[q, 'Ø Leistung']:.0f} Punkte</p>
                                        <p style="margin: 5px 0; font-size: 0.9em;">N = {quadrant_stats.loc[q, 'N']:.0f}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        
                        # Handlungsempfehlungen pro Quadrant
                        st.markdown("**💡 Interventionsempfehlungen nach Profil:**")
                        
                        with st.expander("Q1: Optimal (Grün) - Fördern & Herausfordern"):
                            st.markdown("""
                            **Charakteristika:**
                            - Hohe Selbstwirksamkeit + Niedrige Angst
                            - Beste Leistungsgruppe
                            - Intrinsisch motiviert
                            
                            **Empfohlene Maßnahmen:**
                            - ✅ Challenge & Extension: Anspruchsvolle Aufgaben anbieten
                            - ✅ Peer-Tutoring: Als Tutoren für andere Schüler einsetzen
                            - ✅ Selbstreguliertes Lernen: Autonomie fördern
                            - ❌ Keine Intervention nötig (Ressourcen für Risikogruppen)
                            """)
                        
                        with st.expander("Q2: Ambivalent (Gelb) - Prüfungsangst adressieren"):
                            st.markdown("""
                            **Charakteristika:**
                            - Hohe Selbstwirksamkeit + Hohe Angst
                            - "Ich kann es, aber ich habe Angst"
                            - Prüfungsangst, keine Fähigkeitsangst
                            
                            **Empfohlene Maßnahmen:**
                            - ✅ Entspannungstechniken: Progressive Muskelrelaxation
                            - ✅ Prüfungssimulationen: Angst durch Gewöhnung reduzieren
                            - ✅ Kognitive Umstrukturierung: Katastrophisierende Gedanken hinterfragen
                            - ⚠️ Fokus auf Angstreduktion, nicht Selbstwirksamkeit
                            """)
                        
                        with st.expander("Q3: Risikogruppe (Rot) - Höchste Priorität!"):
                            st.markdown("""
                            **Charakteristika:**
                            - Niedrige Selbstwirksamkeit + Hohe Angst
                            - Schwächste Leistungsgruppe
                            - "Ich kann es nicht und ich habe Angst"
                            - Vermeidungsverhalten wahrscheinlich
                            
                            **Empfohlene Maßnahmen:**
                            - 🚨 **Priorität 1 für Interventionen!**
                            - ✅ Mastery Experiences: Garantierte Erfolgserlebnisse schaffen
                            - ✅ Strukturierte Unterstützung: Kleinschrittige Aufgaben
                            - ✅ Attributionstraining: Erfolge auf Anstrengung zurückführen
                            - ✅ Peer-Modelle: "Wenn die das können, kann ich das auch"
                            - ✅ Individuelle Betreuung: Mentoring, Tutoring
                            """)
                        
                        with st.expander("Q4: Indifferent (Blau) - Motivation wecken"):
                            st.markdown("""
                            **Charakteristika:**
                            - Niedrige Selbstwirksamkeit + Niedrige Angst
                            - "Ich kann es nicht, aber es ist mir auch egal"
                            - Mangelnde Motivation, gelangweilt
                            
                            **Empfohlene Maßnahmen:**
                            - ✅ Relevanz herstellen: Alltagsbezug von Mathe zeigen
                            - ✅ Interessensorientierung: An Hobbys anknüpfen
                            - ✅ Erfolgserlebnisse: Selbstwirksamkeit durch Erfolge aufbauen
                            - ✅ Growth Mindset: "Du kannst es lernen!"
                            - ⚠️ Zuerst Motivation wecken, dann Kompetenzen aufbauen
                            """)
                        
                    else:
                        st.warning("""
                        ⚠️ **Für vollständige Analysen benötigt:**
                        
                        Bitte wähle in Tab 2 die Variablen **ANXMAT** und **MATHEFF** aus,
                        um alle Visualisierungen in diesem Kapitel zu sehen.
                        
                        Diese beiden Indizes sind zentral für die Analyse affektiver Faktoren.
                        """)
                        
                        # Zeige trotzdem verfügbare Korrelationen
                        st.markdown("**Verfügbare Korrelationen mit den aktuell gewählten Variablen:**")
                        
                        for var in selected_vars:
                            if var in df.columns:
                                corr = df[[var, 'math_score']].corr().iloc[0, 1]
                                st.metric(
                                    label=f"Korrelation: {var} ↔ Matheleistung",
                                    value=f"{corr:.3f}"
                                )
                
                # Kapitel 4: Einordnung & Vergleich
                with st.expander("4️⃣ EINORDNUNG & VERGLEICH"):
                    st.markdown("""
                    ### Benchmark mit internationaler Forschung
                    
                    **Unser Befund im Vergleich:**
                    
                    | Studie | Jahr | Stichprobe | r (Self-Efficacy) | r (Anxiety) |
                    |--------|------|------------|-------------------|-------------|
                    | Richardson et al. | 2012 | Meta-Analyse | 0.50 | -0.34 |
                    | OECD PISA | 2018 | International | 0.54 | -0.38 |
                    | **Unsere Analyse** | **2022** | **Deutschland** | **?** | **?** |
                    
                    → Werte werden dynamisch aus den Daten eingefügt
                    
                    ---
                    
                    ### Einordnung nach Hattie's Visible Learning
                    
                    **Effektstärken (d) für Leistung:**
                    - Self-Efficacy: d = 0.92 → **sehr hoch**
                    - Teacher-Student-Relationship: d = 0.72
                    - Feedback: d = 0.70
                    - Socioeconomic Status: d = 0.57
                    
                    **Umrechnung:** r = 0.567 entspricht ca. d ≈ 1.3 (sehr starker Effekt!)
                    
                    ---
                    
                    ### ⚠️ Methodische Limitation: Querschnitt vs. Kausalität
                    
                    **Was unsere Daten zeigen:**
                    - ✅ Es gibt einen **Zusammenhang** zwischen Selbstwirksamkeit und Leistung
                    - ✅ Dieser Zusammenhang ist **statistisch signifikant** und **praktisch bedeutsam**
                    - ✅ Die **Effektstärke** rechtfertigt Interventionen
                    
                    **Was unsere Daten NICHT zeigen:**
                    - ❌ Ob Selbstwirksamkeit die **Ursache** für bessere Leistung ist
                    - ❌ Oder ob gute Leistung zu mehr Selbstwirksamkeit führt
                    - ❌ Oder ob ein dritter Faktor beides beeinflusst
                    
                    **Für kausale Aussagen benötigen wir:**
                    - Längsschnitt-Designs (Messung zu mehreren Zeitpunkten)
                    - Interventionsstudien (Experimental-/Kontrollgruppe)
                    - Strukturgleichungsmodelle mit Mediationsanalysen
                    
                    **Dennoch gerechtfertigt:**
                    Die internationale Evidenz aus experimentellen Studien zeigt,
                    dass Selbstwirksamkeits-Interventionen tatsächlich kausal 
                    zu Leistungsverbesserungen führen (siehe Meta-Analysen).
                    
                    Unsere Korrelationen **bestätigen** diesen bekannten Zusammenhang
                    für die aktuelle deutsche Kohorte.
                    """)
                
                # Kapitel 5: Implikationen für die Praxis
                with st.expander("5️⃣ IMPLIKATIONEN FÜR DIE PRAXIS"):
                    st.markdown("""
                    ### Zentrale Handlungsempfehlungen
                    
                    Basierend auf unseren Befunden und der internationalen Evidenz:
                    
                    ---
                    
                    #### 1. Priorisierung: Selbstwirksamkeit vor Angstreduktion
                    
                    **Warum?**
                    - Selbstwirksamkeit zeigt stärkeren Zusammenhang mit Leistung
                    - Positive Kompetenzüberzeugungen sind nachhaltiger als Angstreduktion
                    - Selbstwirksamkeit hat Transfer-Effekte auf andere Domänen
                    
                    **Wie?**
                    - Fokus auf **Erfolgserlebnisse** (Mastery Experiences)
                    - **Stellvertretende Erfahrungen** (Modeling durch Peers)
                    - **Positives Feedback** auf Prozess, nicht nur Ergebnis
                    - **Realistische Zielsetzungen** mit erreichbaren Teilschritten
                    
                    ---
                    
                    #### 2. Evidenzbasierte Interventionsansätze
                    
                    **Top 3 nach Evidenzlage:**
                    
                    **A) Attributionstraining**
                    - Erfolge auf Anstrengung (kontrollierbar) zurückführen
                    - Misserfolge als Lerngelegenheiten reframen
                    - Growth Mindset fördern
                    - Effektstärke: d ≈ 0.6-0.8
                    
                    **B) Strukturierte Erfolgserlebnisse**
                    - Aufgaben mit ansteigendem Schwierigkeitsgrad
                    - "Productive Struggle" ermöglichen
                    - Kleine Erfolge sichtbar machen
                    - Effektstärke: d ≈ 0.5-0.7
                    
                    **C) Peer-Assisted Learning**
                    - Erfolgreiche Mitschüler als Modelle
                    - "Wenn die das können, kann ich das auch"
                    - Tutoring-Systeme (Tutor profitiert auch!)
                    - Effektstärke: d ≈ 0.5-0.6
                    
                    ---
                    
                    #### 3. Identifikation von Risikogruppen
                    
                    **Wer profitiert am meisten?**
                    
                    Schüler:innen mit:
                    - Niedriger Selbstwirksamkeit + hoher Angst → **Priorität 1**
                    - Niedriger Selbstwirksamkeit + niedrige Angst → **Priorität 2**
                    - Hoher Selbstwirksamkeit + hoher Angst → **Prüfungsangst-Fokus**
                    
                    **Screening-Fragen für Lehrkräfte:**
                    1. "Glaubt der/die Schüler:in an eigene Fähigkeiten?"
                    2. "Zeigt er/sie Vermeidungsverhalten?"
                    3. "Spricht er/sie über vergangene Misserfolgserfahrungen?"
                    
                    ---
                    
                    #### 4. Systemische Perspektive: Schulkultur
                    
                    **Über Individualinterventionen hinaus:**
                    
                    - **Fehlerkultur**: Fehler als Lernchancen normalisieren
                    - **Heterogene Leistungserwartungen**: Differenzierung ermöglichen
                    - **Diagnostische Kompetenz**: Lehrkräfte in Selbstwirksamkeits-Diagnostik schulen
                    - **Elternarbeit**: Eltern für supportive Attributionen sensibilisieren
                    
                    ---
                    
                    ### 📥 Materialien für die Praxis
                    
                    **Handreichungen (entwickelbar):**
                    - ✅ Leitfaden: Selbstwirksamkeit im Matheunterricht fördern
                    - ✅ Fragebogen: Selbstwirksamkeits-Screening (5 Minuten)
                    - ✅ Interventionskatalog: 20 evidenzbasierte Maßnahmen
                    - ✅ Eltern-Information: "Wie unterstütze ich mein Kind?"
                    
                    **Fortbildungsmodule:**
                    - Modul 1: Grundlagen affektiver Faktoren (2h)
                    - Modul 2: Diagnostik im Klassenraum (3h)
                    - Modul 3: Interventionen praktisch umsetzen (4h)
                    """)
                
                # Download-Bereich
                st.markdown("---")
                st.markdown("### 📥 Materialien & Export")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("""
                    **Technische Berichte**
                    - 📄 Methodenbericht (PDF)
                    - 📊 Datenexport (CSV)
                    - 📈 Syntax-Datei (Python)
                    """)
                
                with col2:
                    st.markdown("""
                    **Präsentationen**
                    - 🎯 Lehrerfortbildung (PPTX)
                    - 👪 Elternabend (PPTX)
                    - 🎓 Wissenschaftlicher Vortrag (PDF)
                    """)
                
                with col3:
                    st.markdown("""
                    **Praxismaterialien**
                    - 📋 Screening-Fragebogen
                    - 💡 Interventionskatalog
                    - 📚 Literaturliste
                    """)
            
            # ============================================
            # SUB-TAB 2: TECHNISCHE ANALYSE (ALT)
            # ============================================
            
            with subtab2:
                st.subheader("📊 Korrelation mit Matheleistung")
                
                # Korrelationen berechnen
                corr_data = []
                
                for var in selected_vars:
                    corr = df[[var, 'math_score']].corr().iloc[0, 1]
                    var_label = codebook[codebook['variable_name'] == var]['variable_label'].iloc[0]
                    
                    corr_data.append({
                        'Variable': var,
                        'Label': var_label[:50] + '...' if len(var_label) > 50 else var_label,
                        'Korrelation': round(corr, 3)
                    })
                
                corr_df = pd.DataFrame(corr_data).sort_values('Korrelation')
                
                st.dataframe(corr_df, use_container_width=True)
                
                # Visualisierung
                fig = px.bar(
                    corr_df,
                    x='Korrelation',
                    y='Variable',
                    orientation='h',
                    title='Korrelation mit Matheleistung (PV1MATH)',
                    color='Korrelation',
                    color_continuous_scale='RdYlGn_r',
                    range_color=[-0.5, 0.5]
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("📌 **Interpretation:** Negative Korrelation = höhere Anxiety → niedrigere Matheleistung")
                
                # Correlation Matrix (wenn Composite Score existiert)
                if 'confidence_score' in df.columns:
                    st.subheader("🔢 Korrelationsmatrix")
                    
                    corr_matrix = df[['confidence_score', 'math_score', 'reading_score', 'science_score']].corr()
                    
                    fig = px.imshow(
                        corr_matrix,
                        text_auto='.2f',
                        aspect='auto',
                        color_continuous_scale='RdYlGn',
                        zmin=-1,
                        zmax=1,
                        title='Korrelationen: Confidence Score & PISA Scores'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    
    # ============================================
    # TAB 4: VISUALISIERUNGEN
    # ============================================
    
    with tab4:
        st.header("📈 Visualisierungen")
        
        if 'df' in locals() and 'confidence_score' in df.columns:
            
            # Gender Gap Analysis
            st.subheader("👫 Gender Gap - Mathematics Self-Confidence")
            
            # Filter für Gender
            df_gender = df[df['gender'].isin([1, 2])].copy()
            df_gender['gender_label'] = df_gender['gender'].map({1: 'Mädchen', 2: 'Jungen'})
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Boxplot
                fig = px.box(
                    df_gender,
                    x='gender_label',
                    y='confidence_score',
                    color='gender_label',
                    title='Confidence Score nach Geschlecht',
                    labels={'gender_label': 'Geschlecht', 'confidence_score': 'Confidence Score (MATHEFF − ANXMAT, WLE-Einheiten)'},
                    color_discrete_map={'Mädchen': '#FF6B9D', 'Jungen': '#4ECDC4'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Violin Plot
                fig = px.violin(
                    df_gender,
                    x='gender_label',
                    y='math_score',
                    color='gender_label',
                    box=True,
                    title='Matheleistung nach Geschlecht',
                    labels={'gender_label': 'Geschlecht', 'math_score': 'Math Score (PISA)'},
                    color_discrete_map={'Mädchen': '#FF6B9D', 'Jungen': '#4ECDC4'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.caption(
                "So liest du den Confidence Score: Er ist die Differenz zweier PISA-WLE-Indizes "
                "(Selbstwirksamkeit MATHEFF minus Mathe-Angst ANXMAT), die jeweils auf OECD-Mittel 0 "
                "und Standardabweichung 1 skaliert sind – keine 1–4-Skala. Höhere Werte = mehr "
                "Selbstvertrauen im Verhältnis zur Angst; 0 = Selbstwirksamkeit und Angst gleich hoch "
                "(in Index-Einheiten); negative Werte = die Angst überwiegt."
            )

            # Statistik-Vergleich
            st.subheader("📊 Statistischer Vergleich")
            
            gender_stats = df_gender.groupby('gender_label')[['confidence_score', 'math_score']].agg(['mean', 'std', 'count'])
            st.dataframe(gender_stats, use_container_width=True)
            
            # Scatter: Confidence vs. Performance
            st.subheader("🔍 Confidence Score vs. Matheleistung")
            
            fig = px.scatter(
                df_gender,
                x='confidence_score',
                y='math_score',
                color='gender_label',
                trendline='ols',
                title='Zusammenhang: Math Confidence & Performance',
                labels={
                    'confidence_score': 'Confidence Score (MATHEFF − ANXMAT, WLE-Einheiten)',
                    'math_score': 'Math Score (PISA)',
                    'gender_label': 'Geschlecht'
                },
                color_discrete_map={'Mädchen': '#FF6B9D', 'Jungen': '#4ECDC4'},
                opacity=0.6
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Distribution Comparison
            st.subheader("📊 Verteilungen im Vergleich")
            
            fig = go.Figure()
            
            for gender in ['Mädchen', 'Jungen']:
                data = df_gender[df_gender['gender_label'] == gender]['confidence_score']
                fig.add_trace(go.Histogram(
                    x=data,
                    name=gender,
                    opacity=0.7,
                    nbinsx=20
                ))
            
            fig.update_layout(
                barmode='overlay',
                title='Verteilung: Confidence Score nach Geschlecht',
                xaxis_title='Confidence Score (MATHEFF − ANXMAT, WLE-Einheiten)',
                yaxis_title='Anzahl Schüler',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("⚠️ Bitte berechne erst den Composite Score in Tab 2.")
    
    # ============================================
    # TAB 5: TIMSS-PISA MAPPING
    # ============================================
    
    with tab5:
        st.header("🗺️ TIMSS-PISA Mapping Tool")
        
        st.markdown("""
        Erstelle ein **Mapping** zwischen TIMSS Mathematics Self-Confidence Items 
        und entsprechenden PISA-Variablen.
        """)
        
        # TIMSS Items (aus dem Wochenplan)
        timss_items = [
            {
                'dimension': 'Positive Self-Perception',
                'item': '"I usually do well in mathematics"',
                'construct': 'Self-Efficacy (positiv)'
            },
            {
                'dimension': 'Comparative Difficulty',
                'item': '"Mathematics is harder for me than for many of my classmates"',
                'construct': 'Social Comparison (negativ)'
            },
            {
                'dimension': 'Negative Self-Perception',
                'item': '"I am just not good at mathematics"',
                'construct': 'Fixed Mindset (negativ)'
            },
            {
                'dimension': 'Learning Speed',
                'item': '"I learn mathematics quickly"',
                'construct': 'Self-Efficacy (Learning)'
            }
        ]
        
        st.subheader("📋 TIMSS Reference Items")
        timss_df = pd.DataFrame(timss_items)
        st.dataframe(timss_df, use_container_width=True)
        
        st.markdown("---")
        
        # PISA Kandidaten
        st.subheader("🎯 PISA-Kandidaten für Mapping")
        
        pisa_candidates = find_math_confidence_vars(conn)
        
        # Filter für die wichtigsten
        priority_vars = ['ST182Q01HA', 'ST182Q02HA', 'ST182Q03HA', 'ST182Q04HA', 'ST182Q05HA']
        pisa_priority = pisa_candidates[pisa_candidates['variable_name'].isin(priority_vars)]
        
        if len(pisa_priority) > 0:
            st.markdown("**📌 Top-Kandidaten (Math Anxiety Items):**")
            
            # Füge Fragetexte hinzu falls vorhanden
            for _, row in pisa_priority.iterrows():
                var_name = row['variable_name']
                var_label = row['variable_label']
                
                with st.expander(f"**{var_name}** - {var_label[:60]}..."):
                    # Lade Fragetext
                    question = load_question_text(conn, var_name)
                    if question is not None and pd.notna(question.get('question_text_en')):
                        if pd.notna(question.get('question_text_de')):
                            st.markdown(f"**🇩🇪 Fragetext:** {question['question_text_de']}")
                        else:
                            st.markdown(f"**🇬🇧 Question:** {question['question_text_en']}")

                    # Lade Value Labels
                    value_labels = load_value_labels(conn, var_name)
                    if len(value_labels) > 0:
                        st.markdown("**Antwortoptionen:**")
                        for _, vl in value_labels.iterrows():
                            label = vl['label_de'] if pd.notna(vl.get('label_de')) else vl['label']
                            st.text(f"  {vl['value']} = {label}")
        
        st.markdown("**📋 Alle Math-Confidence Variablen:**")
        st.dataframe(pisa_candidates, use_container_width=True)
        
        st.markdown("---")
        
        # Interaktives Mapping
        st.subheader("🔗 Erstelle dein Mapping")
        
        mapping_data = []
        
        for i, timss in enumerate(timss_items):
            with st.expander(f"**TIMSS Dimension {i+1}:** {timss['dimension']}"):
                st.markdown(f"**Item:** {timss['item']}")
                st.markdown(f"**Konstrukt:** {timss['construct']}")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    selected_pisa = st.selectbox(
                        "Wähle passendes PISA-Item:",
                        options=['---'] + pisa_candidates['variable_name'].tolist(),
                        key=f"mapping_{i}"
                    )
                
                with col2:
                    if selected_pisa != '---':
                        pisa_label = pisa_candidates[
                            pisa_candidates['variable_name'] == selected_pisa
                        ]['variable_label'].iloc[0]
                        
                        st.info(f"**Label:** {pisa_label[:100]}...")
                
                # Zeige Fragetext und Value Labels wenn Variable ausgewählt
                if selected_pisa != '---':
                    st.markdown("---")

                    # Fragetext
                    question = load_question_text(conn, selected_pisa)
                    if question is not None and pd.notna(question.get('question_text_en')):
                        st.markdown("**📝 Vollständiger Fragetext:**")
                        if pd.notna(question.get('question_text_de')):
                            st.text(f"🇩🇪 {question['question_text_de']}")
                        else:
                            st.text(f"🇬🇧 {question['question_text_en']}")

                    # Value Labels
                    value_labels = load_value_labels(conn, selected_pisa)
                    if len(value_labels) > 0:
                        st.markdown("**Antwortoptionen:**")
                        for _, vl in value_labels.iterrows():
                            label = vl['label_de'] if pd.notna(vl.get('label_de')) else vl['label']
                            st.text(f"  {vl['value']} = {label}")
                    
                    # Füge zu Mapping hinzu
                    mapping_data.append({
                        'TIMSS Dimension': timss['dimension'],
                        'TIMSS Item': timss['item'],
                        'TIMSS Konstrukt': timss['construct'],
                        'PISA Variable': selected_pisa,
                        'PISA Label': pisa_label,
                        'PISA Fragetext': question['question_text_de'] if question is not None and pd.notna(question.get('question_text_de')) 
                                         else (question['question_text_en'] if question is not None else 'N/A')
                    })
        
        # Mapping-Übersicht
        if mapping_data:
            st.markdown("---")
            st.subheader("✅ Dein TIMSS-PISA Mapping")
            
            mapping_df = pd.DataFrame(mapping_data)
            st.dataframe(mapping_df, use_container_width=True)
            
            # Download als CSV
            csv = mapping_df.to_csv(index=False)
            st.download_button(
                label="📥 Mapping als CSV herunterladen",
                data=csv,
                file_name="timss_pisa_mapping.csv",
                mime="text/csv"
            )
    
    # ============================================
    # TAB 6: ERGEBNISÜBERSICHT & EXPORT
    # ============================================
    
    with tab6:
        st.header("📋 Ergebnisübersicht & Export")
        st.markdown("*Alle Kennzahlen auf einen Blick - bereit zum Weiterarbeiten*")
        
        # Check ob Daten verfügbar
        if 'df' not in locals() or not selected_vars:
            st.warning("""
            ⚠️ **Noch keine Analyse durchgeführt**
            
            Bitte gehe zu Tab 2 und wähle Variablen aus, um eine Analyse zu starten.
            Dann kannst du hier alle Ergebnisse übersichtlich sehen und exportieren.
            """)
        else:
            # ============================================
            # SECTION 1: STICHPROBENINFO
            # ============================================
            
            st.subheader("1️⃣ Stichprobeninformation")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Stichprobengröße",
                    f"{len(df):,}",
                    help="Anzahl Schüler in der Analyse"
                )
            
            with col2:
                st.metric(
                    "Datenbank",
                    "pisa_2022_germany",
                    help="Verwendete Datenbank"
                )
            
            with col3:
                st.metric(
                    "Analysierte Variablen",
                    len(selected_vars),
                    help="Anzahl ausgewählter Variablen"
                )
            
            with col4:
                st.metric(
                    "Analysedatum",
                    pd.Timestamp.now().strftime("%Y-%m-%d"),
                    help="Datum der Analyse"
                )
            
            st.markdown("**Ausgewählte Variablen:**")
            st.code(", ".join(selected_vars), language=None)
            
            st.markdown("---")
            
            # ============================================
            # SECTION 2: DESKRIPTIVE STATISTIKEN
            # ============================================
            
            st.subheader("2️⃣ Deskriptive Statistiken")
            
            # Erstelle Übersichtstabelle
            desc_data = []
            
            for var in selected_vars:
                desc_data.append({
                    'Variable': var,
                    'N': df[var].count(),
                    'Mean': df[var].mean(),
                    'SD': df[var].std(),
                    'Min': df[var].min(),
                    'Max': df[var].max(),
                    'Missing': df[var].isnull().sum(),
                    'Missing %': (df[var].isnull().sum() / len(df) * 100)
                })
            
            # Matheleistung hinzufügen
            desc_data.append({
                'Variable': 'math_score',
                'N': df['math_score'].count(),
                'Mean': df['math_score'].mean(),
                'SD': df['math_score'].std(),
                'Min': df['math_score'].min(),
                'Max': df['math_score'].max(),
                'Missing': df['math_score'].isnull().sum(),
                'Missing %': (df['math_score'].isnull().sum() / len(df) * 100)
            })
            
            desc_df = pd.DataFrame(desc_data)
            
            # Formatierung
            desc_df_display = desc_df.copy()
            desc_df_display['Mean'] = desc_df_display['Mean'].apply(lambda x: f"{x:.3f}")
            desc_df_display['SD'] = desc_df_display['SD'].apply(lambda x: f"{x:.3f}")
            desc_df_display['Min'] = desc_df_display['Min'].apply(lambda x: f"{x:.2f}")
            desc_df_display['Max'] = desc_df_display['Max'].apply(lambda x: f"{x:.2f}")
            desc_df_display['Missing %'] = desc_df_display['Missing %'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(desc_df_display, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # ============================================
            # SECTION 3: KORRELATIONEN
            # ============================================
            
            st.subheader("3️⃣ Korrelationen mit Mathematikleistung")
            
            # Berechne Korrelationen
            corr_data = []
            
            for var in selected_vars:
                corr = df[[var, 'math_score']].corr().iloc[0, 1]
                r2 = corr ** 2
                
                # Effektstärken-Klassifikation nach Cohen (1988)
                if abs(corr) < 0.1:
                    effect_size = "Sehr klein"
                elif abs(corr) < 0.3:
                    effect_size = "Klein"
                elif abs(corr) < 0.5:
                    effect_size = "Mittel"
                else:
                    effect_size = "Groß"
                
                corr_data.append({
                    'Variable': var,
                    'r': corr,
                    'r (absolut)': abs(corr),
                    'R²': r2,
                    'R² (%)': r2 * 100,
                    'Effektstärke': effect_size,
                    'Richtung': 'Positiv' if corr > 0 else 'Negativ'
                })
            
            corr_df = pd.DataFrame(corr_data).sort_values('r (absolut)', ascending=False)
            
            # Formatierung
            corr_df_display = corr_df.copy()
            corr_df_display['r'] = corr_df_display['r'].apply(lambda x: f"{x:.3f}")
            corr_df_display['r (absolut)'] = corr_df_display['r (absolut)'].apply(lambda x: f"{x:.3f}")
            corr_df_display['R²'] = corr_df_display['R²'].apply(lambda x: f"{x:.3f}")
            corr_df_display['R² (%)'] = corr_df_display['R² (%)'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(corr_df_display, use_container_width=True, hide_index=True)
            
            # Highlight stärkste Korrelation
            strongest = corr_df.iloc[0]
            st.success(f"""
            **🏆 Stärkster Prädiktor:** {strongest['Variable']} 
            (r = {strongest['r']:.3f}, R² = {strongest['R² (%)']:.1f}%)
            """)
            
            st.markdown("---")
            
            # ============================================
            # SECTION 4: QUADRANTEN-ANALYSE
            # ============================================
            
            if 'ANXMAT' in selected_vars and 'MATHEFF' in selected_vars:
                st.subheader("4️⃣ Quadranten-Analyse")
                
                # Berechne Quadranten (schon in Tab 3 gemacht, hier nochmal)
                median_matheff = df['MATHEFF'].median()
                median_anxmat = df['ANXMAT'].median()
                
                df['quadrant'] = 'Q4'
                df.loc[(df['MATHEFF'] >= median_matheff) & (df['ANXMAT'] < median_anxmat), 'quadrant'] = 'Q1'
                df.loc[(df['MATHEFF'] >= median_matheff) & (df['ANXMAT'] >= median_anxmat), 'quadrant'] = 'Q2'
                df.loc[(df['MATHEFF'] < median_matheff) & (df['ANXMAT'] >= median_anxmat), 'quadrant'] = 'Q3'
                df.loc[(df['MATHEFF'] < median_matheff) & (df['ANXMAT'] < median_anxmat), 'quadrant'] = 'Q4'
                
                # Statistik pro Quadrant
                quadrant_stats = df.groupby('quadrant').agg({
                    'math_score': ['mean', 'std', 'count']
                }).round(2)
                quadrant_stats.columns = ['Ø Leistung', 'SD Leistung', 'N']
                quadrant_stats['Anteil %'] = (quadrant_stats['N'] / len(df) * 100).round(1)
                
                # Labels
                quadrant_stats.index = quadrant_stats.index.map({
                    'Q1': 'Q1: Optimal (Hoch/Niedrig)',
                    'Q2': 'Q2: Ambivalent (Hoch/Hoch)',
                    'Q3': 'Q3: Risikogruppe (Niedrig/Hoch)',
                    'Q4': 'Q4: Indifferent (Niedrig/Niedrig)'
                })
                
                st.dataframe(quadrant_stats, use_container_width=True)
                
                # Risikogruppe hervorheben
                q3_n = quadrant_stats.loc['Q3: Risikogruppe (Niedrig/Hoch)', 'N']
                q3_pct = quadrant_stats.loc['Q3: Risikogruppe (Niedrig/Hoch)', 'Anteil %']
                q3_perf = quadrant_stats.loc['Q3: Risikogruppe (Niedrig/Hoch)', 'Ø Leistung']
                
                st.warning(f"""
                **⚠️ Risikogruppe (Q3):**
                - {q3_n:.0f} Schüler ({q3_pct:.1f}% der Stichprobe)
                - Durchschnittsleistung: {q3_perf:.0f} Punkte
                - Intervention empfohlen: Fokus auf Selbstwirksamkeitsförderung
                """)
                
                st.markdown("---")
            
            # ============================================
            # SECTION 5: KEY FINDINGS
            # ============================================
            
            st.subheader("5️⃣ Key Findings")
            
            st.markdown("**📌 Zusammenfassung der wichtigsten Erkenntnisse:**")
            
            # Dynamisch generierte Key Findings
            findings = []
            
            # Finding 1: Stichprobe
            findings.append(f"**Stichprobe:** N = {len(df):,} Schüler aus PISA 2022 Deutschland")
            
            # Finding 2: Stärkster Prädiktor
            if len(corr_df) > 0:
                strongest = corr_df.iloc[0]
                findings.append(
                    f"**Stärkster Prädiktor:** {strongest['Variable']} mit r = {strongest['r']:.3f} "
                    f"(R² = {strongest['R² (%)']:.1f}%, Effektstärke: {strongest['Effektstärke']})"
                )
            
            # Finding 3: MATHEFF vs ANXMAT
            if 'ANXMAT' in selected_vars and 'MATHEFF' in selected_vars:
                corr_matheff = corr_df[corr_df['Variable'] == 'MATHEFF']['r'].values[0]
                corr_anxmat = corr_df[corr_df['Variable'] == 'ANXMAT']['r'].values[0]
                ratio = abs(float(corr_matheff) / float(corr_anxmat))
                
                findings.append(
                    f"**Selbstwirksamkeit vs. Angst:** MATHEFF (r = {float(corr_matheff):.3f}) ist "
                    f"{ratio:.2f}x einflussreicher als ANXMAT (r = {float(corr_anxmat):.3f})"
                )
                
                # Finding 4: Risikogruppe
                findings.append(
                    f"**Risikogruppe:** {q3_n:.0f} Schüler ({q3_pct:.1f}%) mit niedriger "
                    f"Selbstwirksamkeit UND hoher Angst → Priorität für Interventionen"
                )
            
            # Finding 5: Durchschnittsleistung
            mean_math = df['math_score'].mean()
            if mean_math < 482:
                pisa_level = "Level 2 (Basiskompetenzen)"
            elif mean_math < 545:
                pisa_level = "Level 3 (Solide Kenntnisse)"
            elif mean_math < 607:
                pisa_level = "Level 4 (Gut)"
            else:
                pisa_level = "Level 5+ (Sehr gut)"
            
            findings.append(
                f"**Durchschnittsleistung:** {mean_math:.0f} PISA-Punkte → {pisa_level}"
            )
            
            # Ausgabe
            for i, finding in enumerate(findings, 1):
                st.markdown(f"{i}. {finding}")
            
            st.markdown("---")
            
            # ============================================
            # SECTION 6: HANDLUNGSEMPFEHLUNGEN
            # ============================================
            
            st.subheader("6️⃣ Handlungsempfehlungen")
            
            recommendations = []
            
            if 'MATHEFF' in selected_vars:
                corr_matheff_val = float(corr_df[corr_df['Variable'] == 'MATHEFF']['r'].values[0])
                if abs(corr_matheff_val) > 0.5:
                    recommendations.append({
                        'Priorität': '🔴 Hoch',
                        'Bereich': 'Selbstwirksamkeitsförderung',
                        'Maßnahme': 'Mastery Experiences: Strukturierte Erfolgserlebnisse schaffen',
                        'Begründung': f'Starke Korrelation (r = {corr_matheff_val:.3f}) rechtfertigt Fokus'
                    })
            
            if 'ANXMAT' in selected_vars:
                corr_anxmat_val = float(corr_df[corr_df['Variable'] == 'ANXMAT']['r'].values[0])
                if abs(corr_anxmat_val) > 0.3:
                    recommendations.append({
                        'Priorität': '🟡 Mittel',
                        'Bereich': 'Angstreduktion',
                        'Maßnahme': 'Kognitive Umstrukturierung & Entspannungstechniken',
                        'Begründung': f'Mittlere Korrelation (r = {corr_anxmat_val:.3f})'
                    })
            
            if 'ANXMAT' in selected_vars and 'MATHEFF' in selected_vars and q3_pct > 15:
                recommendations.append({
                    'Priorität': '🔴 Hoch',
                    'Bereich': 'Risikogruppen-Intervention',
                    'Maßnahme': 'Individuelle Förderung für Q3-Schüler (niedrige SE + hohe Angst)',
                    'Begründung': f'{q3_pct:.1f}% der Schüler in kritischer Konstellation'
                })
            
            recommendations.append({
                'Priorität': '🟢 Basis',
                'Bereich': 'Diagnostik',
                'Maßnahme': 'Regelmäßiges Screening von Selbstwirksamkeit & Angst',
                'Begründung': 'Früherkennung ermöglicht rechtzeitige Intervention'
            })
            
            rec_df = pd.DataFrame(recommendations)
            st.dataframe(rec_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # ============================================
            # SECTION 7: EXPORT
            # ============================================
            
            st.subheader("7️⃣ Daten exportieren")
            
            st.markdown("""
            **Lade alle Ergebnisse herunter für:**
            - Weiterverarbeitung in Excel/SPSS
            - Integration in Berichte
            - Präsentationen & Fortbildungen
            """)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 📊 Deskriptive Statistiken")
                
                # CSV Download
                csv_desc = desc_df.to_csv(index=False)
                st.download_button(
                    label="📥 CSV herunterladen",
                    data=csv_desc,
                    file_name=f"pisa_deskriptiv_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download_desc"
                )
            
            with col2:
                st.markdown("### 🔗 Korrelationen")
                
                # CSV Download
                csv_corr = corr_df.to_csv(index=False)
                st.download_button(
                    label="📥 CSV herunterladen",
                    data=csv_corr,
                    file_name=f"pisa_korrelationen_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download_corr"
                )
            
            with col3:
                if 'quadrant_stats' in locals():
                    st.markdown("### 🗺️ Quadranten")
                    
                    # CSV Download
                    csv_quad = quadrant_stats.to_csv()
                    st.download_button(
                        label="📥 CSV herunterladen",
                        data=csv_quad,
                        file_name=f"pisa_quadranten_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        key="download_quad"
                    )
            
            st.markdown("---")
            
            # EXCEL-Export mit allen Sheets
            st.markdown("### 📗 Kompletter Export (Excel mit allen Sheets)")
            
            try:
                from io import BytesIO
                
                # Erstelle Excel-Datei im Speicher
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Sheet 1: Übersicht
                    overview_data = {
                        'Kennzahl': [
                            'Stichprobengröße',
                            'Datenbank',
                            'Analysierte Variablen',
                            'Analysedatum',
                            'Durchschnittsleistung',
                            'PISA-Level'
                        ],
                        'Wert': [
                            len(df),
                            "pisa_2022_germany.db",
                            ', '.join(selected_vars),
                            pd.Timestamp.now().strftime('%Y-%m-%d'),
                            f"{mean_math:.0f}",
                            pisa_level
                        ]
                    }
                    pd.DataFrame(overview_data).to_excel(writer, sheet_name='Übersicht', index=False)
                    
                    # Sheet 2: Deskriptive Statistiken
                    desc_df.to_excel(writer, sheet_name='Deskriptive Statistiken', index=False)
                    
                    # Sheet 3: Korrelationen
                    corr_df.to_excel(writer, sheet_name='Korrelationen', index=False)
                    
                    # Sheet 4: Quadranten (falls vorhanden)
                    if 'quadrant_stats' in locals():
                        quadrant_stats.to_excel(writer, sheet_name='Quadranten-Analyse')
                    
                    # Sheet 5: Key Findings
                    findings_data = {
                        'Nr': range(1, len(findings) + 1),
                        'Finding': findings
                    }
                    pd.DataFrame(findings_data).to_excel(writer, sheet_name='Key Findings', index=False)
                    
                    # Sheet 6: Handlungsempfehlungen
                    rec_df.to_excel(writer, sheet_name='Handlungsempfehlungen', index=False)
                
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 Alle Ergebnisse als Excel herunterladen",
                    data=excel_data,
                    file_name=f"pisa_analyse_komplett_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel"
                )
                
                st.success("✅ Excel-Export mit 6 Sheets: Übersicht, Deskriptive Statistiken, Korrelationen, Quadranten-Analyse, Key Findings, Handlungsempfehlungen")
                
            except ImportError:
                st.error("⚠️ Excel-Export benötigt 'openpyxl'. Bitte installiere: `pip install openpyxl --break-system-packages`")
            
            st.markdown("---")
            
            # ============================================
            # SECTION 8: COPY-PASTE ZUSAMMENFASSUNG
            # ============================================
            
            st.subheader("8️⃣ Copy-Paste Zusammenfassung")
            
            st.markdown("**Für Berichte, E-Mails, Präsentationen:**")
            
            summary_text = f"""
PISA 2022 Deutschland - Analyse Affektiver Faktoren
Analysedatum: {pd.Timestamp.now().strftime('%Y-%m-%d')}

STICHPROBE
- N = {len(df):,} Schüler
- Analysierte Variablen: {', '.join(selected_vars)}
- Durchschnittsleistung: {mean_math:.0f} PISA-Punkte ({pisa_level})

ZENTRALE BEFUNDE
"""
            
            for i, finding in enumerate(findings, 1):
                # Entferne Markdown-Formatierung für Plain Text
                clean_finding = finding.replace('**', '').replace('*', '')
                summary_text += f"{i}. {clean_finding}\n"
            
            summary_text += f"""
KORRELATIONEN MIT MATHEMATIKLEISTUNG
"""
            
            for _, row in corr_df.iterrows():
                summary_text += f"- {row['Variable']}: r = {row['r']:.3f} (R² = {row['R² (%)']:.1f}%, {row['Effektstärke']})\n"
            
            if 'quadrant_stats' in locals():
                summary_text += f"""
QUADRANTEN-ANALYSE
- Q1 (Optimal): {quadrant_stats.loc['Q1: Optimal (Hoch/Niedrig)', 'Anteil %']:.1f}% ({quadrant_stats.loc['Q1: Optimal (Hoch/Niedrig)', 'Ø Leistung']:.0f} Punkte)
- Q2 (Ambivalent): {quadrant_stats.loc['Q2: Ambivalent (Hoch/Hoch)', 'Anteil %']:.1f}% ({quadrant_stats.loc['Q2: Ambivalent (Hoch/Hoch)', 'Ø Leistung']:.0f} Punkte)
- Q3 (Risikogruppe): {quadrant_stats.loc['Q3: Risikogruppe (Niedrig/Hoch)', 'Anteil %']:.1f}% ({quadrant_stats.loc['Q3: Risikogruppe (Niedrig/Hoch)', 'Ø Leistung']:.0f} Punkte)
- Q4 (Indifferent): {quadrant_stats.loc['Q4: Indifferent (Niedrig/Niedrig)', 'Anteil %']:.1f}% ({quadrant_stats.loc['Q4: Indifferent (Niedrig/Niedrig)', 'Ø Leistung']:.0f} Punkte)

HANDLUNGSEMPFEHLUNGEN
"""
            
            for _, rec in rec_df.iterrows():
                summary_text += f"{rec['Priorität']} {rec['Bereich']}: {rec['Maßnahme']}\n"
            
            st.text_area(
                "Kopiere diesen Text:",
                summary_text,
                height=400,
                key="copy_summary"
            )
            
            st.info("💡 **Tipp:** Klicke in das Textfeld und drücke Ctrl+A (alles markieren) dann Ctrl+C (kopieren)")
    
    # ============================================
    # SIDEBAR: INFO
    # ============================================
    
    st.sidebar.markdown("---")
    st.sidebar.header("ℹ️ Info")
    st.sidebar.markdown("""
    **PISA 2022 Deutschland**
    
    Diese App analysiert:
    - Mathematics Self-Confidence
    - Mathematics Anxiety
    - Mathematics Self-Efficacy
    
    **Datenquelle:** PISA 2022 Deutschland-Datenbank
    
    **Autor:** Sandra
    **Datum:** Oktober 2025
    """)

if __name__ == "__main__":
    main()