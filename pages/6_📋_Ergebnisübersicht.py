import streamlit as st
import pandas as pd
import numpy as np
import sys
sys.path.append('..')
from utils.db_loader import get_db_connection
from utils.scale_info import get_scale_info, SCALE_DESCRIPTIONS
from utils.statistical_analysis import correlation_with_pvalue
from pathlib import Path
from io import BytesIO
from utils.quadrants import QUADRANT_LABELS, MODEL_TEXT as QUADRANT_MODEL_TEXT, summarize_quadrants, interpretation_markdown as quadrant_interpretation, support_markdown as quadrant_support_text, support_finding as quadrant_support_finding, assign_quadrants, coverage_caption as quadrant_coverage_caption

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="Ergebnisübersicht",
    page_icon="📋",
    layout="wide"
)

# ============================================
# TITLE
# ============================================

st.title("📋 Phase 6: Ergebnisübersicht & Handlungsempfehlungen")
st.markdown("**Professionelles Reporting mit Key Findings und evidenzbasierten Interventionsvorschlägen**")

st.divider()

# ============================================
# INFO
# ============================================

st.info("""
**Diese Seite erstellt einen vollständigen Ergebnis-Report:**
- 📊 Deskriptive Statistiken
- 🔗 Korrelationsanalyse mit Effektstärken
- 🗺️ Quadranten-Analyse (MATHEFF vs ANXMAT)
- 📌 Key Findings (dynamisch generiert)
- 💡 Handlungsempfehlungen (evidenzbasiert)
- 📥 Export-Funktionen (Excel, CSV)
""")

# ============================================
# VARIABLE SELECTION
# ============================================

st.header("1️⃣ Variablen-Auswahl")

available_scales = sorted(list(SCALE_DESCRIPTIONS.keys()))

col1, col2 = st.columns([2, 1])

with col1:
    # Pre-select important variables
    default_vars = ['ANXMAT', 'MATHEFF', 'BELONG', 'ESCS', 'HOMEPOS']
    default_vars = [v for v in default_vars if v in available_scales]

    selected_vars = st.multiselect(
        "WLE-Skalen für Analyse:",
        options=available_scales,
        default=default_vars,
        help="Wähle 3-10 Variablen für umfassende Analyse"
    )

with col2:
    performance_var = st.selectbox(
        "Leistungsvariable:",
        options=['PV1MATH', 'PV1READ', 'PV1SCIE'],
        format_func=lambda x: {
            'PV1MATH': 'Mathematik',
            'PV1READ': 'Lesen',
            'PV1SCIE': 'Naturwissenschaften'
        }[x],
        index=0
    )

# ============================================
# DATA LOADING
# ============================================

@st.cache_data(ttl=60)
def load_report_data(variables, perf_var):
    """Load data for report generation"""
    conn = get_db_connection()

    all_vars = list(set(variables + [perf_var, 'ST004D01T']))
    var_str = ', '.join(all_vars)

    query = f"""
    SELECT {var_str}
    FROM student_data
    WHERE {perf_var} IS NOT NULL
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Rename for easier access
    df.rename(columns={
        perf_var: 'performance',
        'ST004D01T': 'gender'
    }, inplace=True)

    return df


if len(selected_vars) >= 2:

    # Load data
    df = load_report_data(selected_vars, performance_var)

    st.success(f"✅ Daten geladen: N = {len(df):,} Schüler")

    st.divider()

    # ============================================
    # SECTION 1: ÜBERSICHT
    # ============================================

    st.header("2️⃣ Stichproben-Übersicht")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("👨‍🎓 Schüler (gesamt)", f"{len(df):,}")

    with col2:
        female_count = (df['gender'] == 1).sum()
        st.metric("👩 Weiblich", f"{female_count:,}")

    with col3:
        male_count = (df['gender'] == 2).sum()
        st.metric("👨 Männlich", f"{male_count:,}")

    with col4:
        mean_perf = df['performance'].mean()
        st.metric("Ø Leistung", f"{mean_perf:.0f}")

    st.divider()

    # ============================================
    # SECTION 2: DESKRIPTIVE STATISTIK
    # ============================================

    st.header("3️⃣ Deskriptive Statistiken")

    desc_data = []

    for var in selected_vars:
        var_info = get_scale_info(var)

        desc_data.append({
            'Variable': var,
            'Bezeichnung': var_info.get('name_de', var),
            'N': df[var].notna().sum(),
            'Mean': df[var].mean(),
            'SD': df[var].std(),
            'Min': df[var].min(),
            'Max': df[var].max(),
            'Missing': df[var].isna().sum(),
            'Missing %': (df[var].isna().sum() / len(df) * 100)
        })

    # Add performance variable
    desc_data.append({
        'Variable': performance_var,
        'Bezeichnung': {
            'PV1MATH': 'Mathematik-Leistung',
            'PV1READ': 'Lese-Leistung',
            'PV1SCIE': 'Naturwiss.-Leistung'
        }[performance_var],
        'N': df['performance'].notna().sum(),
        'Mean': df['performance'].mean(),
        'SD': df['performance'].std(),
        'Min': df['performance'].min(),
        'Max': df['performance'].max(),
        'Missing': df['performance'].isna().sum(),
        'Missing %': (df['performance'].isna().sum() / len(df) * 100)
    })

    desc_df = pd.DataFrame(desc_data)

    # Format for display
    desc_df_display = desc_df.copy()
    desc_df_display['Mean'] = desc_df_display['Mean'].apply(lambda x: f"{x:.3f}")
    desc_df_display['SD'] = desc_df_display['SD'].apply(lambda x: f"{x:.3f}")
    desc_df_display['Min'] = desc_df_display['Min'].apply(lambda x: f"{x:.2f}")
    desc_df_display['Max'] = desc_df_display['Max'].apply(lambda x: f"{x:.2f}")
    desc_df_display['Missing %'] = desc_df_display['Missing %'].apply(lambda x: f"{x:.1f}%")

    st.dataframe(desc_df_display, use_container_width=True, hide_index=True)

    st.divider()

    # ============================================
    # SECTION 3: KORRELATIONEN
    # ============================================

    st.header("4️⃣ Korrelationen mit Leistung")

    st.markdown(f"**Korrelationen aller Variablen mit {performance_var}:**")

    # Calculate correlations
    corr_data = []

    for var in selected_vars:
        # Remove NaN
        clean_df = df[[var, 'performance']].dropna()

        if len(clean_df) >= 3:
            corr, p_val = correlation_with_pvalue(clean_df[var], clean_df['performance'])
            r2 = corr ** 2

            # Effect size classification (Cohen 1988)
            if abs(corr) < 0.1:
                effect_size = "Sehr klein"
            elif abs(corr) < 0.3:
                effect_size = "Klein"
            elif abs(corr) < 0.5:
                effect_size = "Mittel"
            else:
                effect_size = "Groß"

            var_info = get_scale_info(var)

            corr_data.append({
                'Variable': var,
                'Bezeichnung': var_info.get('name_de', var),
                'r': corr,
                'r (absolut)': abs(corr),
                'R²': r2,
                'R² (%)': r2 * 100,
                'p-Wert': p_val,
                'Signifikant': 'Ja' if p_val < 0.05 else 'Nein',
                'Effektstärke': effect_size,
                'Richtung': 'Positiv' if corr > 0 else 'Negativ'
            })

    corr_df = pd.DataFrame(corr_data).sort_values('r (absolut)', ascending=False)

    # Format for display
    corr_df_display = corr_df.copy()
    corr_df_display['r'] = corr_df_display['r'].apply(lambda x: f"{x:.3f}")
    corr_df_display['r (absolut)'] = corr_df_display['r (absolut)'].apply(lambda x: f"{x:.3f}")
    corr_df_display['R²'] = corr_df_display['R²'].apply(lambda x: f"{x:.3f}")
    corr_df_display['R² (%)'] = corr_df_display['R² (%)'].apply(lambda x: f"{x:.1f}%")
    corr_df_display['p-Wert'] = corr_df_display['p-Wert'].apply(lambda x: f"{x:.4f}")

    st.dataframe(corr_df_display, use_container_width=True, hide_index=True)

    # Highlight strongest predictor
    if len(corr_df) > 0:
        strongest = corr_df.iloc[0]
        st.success(f"""
        **🏆 Stärkster Prädiktor:** {strongest['Bezeichnung']} ({strongest['Variable']})
        - Korrelation: r = {strongest['r']:.3f}
        - Varianzaufklärung: R² = {strongest['R² (%)']:.1f}%
        - Effektstärke: {strongest['Effektstärke']}
        - Richtung: {strongest['Richtung']}
        """)

    st.divider()

    # ============================================
    # SECTION 4: QUADRANTEN-ANALYSE
    # ============================================

    if 'ANXMAT' in selected_vars and 'MATHEFF' in selected_vars:
        st.header("5️⃣ Quadranten-Analyse: MATHEFF vs ANXMAT")

        st.info(QUADRANT_MODEL_TEXT)

        # Quadranten (Median-Split, nur vollständige Fälle; FIX4)
        df['quadrant'], median_matheff, median_anxmat = assign_quadrants(df)
        st.caption(quadrant_coverage_caption(df['quadrant']))

        # Statistics per quadrant
        quadrant_stats = df.groupby('quadrant').agg({
            'performance': ['mean', 'std', 'count']
        }).round(2)
        quadrant_stats.columns = ['Ø Leistung', 'SD Leistung', 'N']
        quadrant_stats['Anteil %'] = (quadrant_stats['N'] / quadrant_stats['N'].sum() * 100).round(1)

        # Datengetriebene Aussagen (FIX4): aus den berechneten Mittelwerten abgeleitet
        quad_summary = summarize_quadrants(df, 'performance')

        # Relabel quadrants (neutral, beschreibend)
        quadrant_stats.index = quadrant_stats.index.map(QUADRANT_LABELS)

        st.dataframe(quadrant_stats, use_container_width=True)

        st.info(quadrant_interpretation(quad_summary))

        # Gruppe mit Foerderbedarf (Q3 + Q4)
        support_n = quad_summary.get('support_n', 0)
        support_pct = quad_summary.get('support_pct', 0.0)
        st.warning(quadrant_support_text(quad_summary))

        # Gruppe mit viel Zutrauen und wenig Angst (Q1)
        if 'Q1' in quad_summary['means'].index:
            q1_n = quad_summary['counts']['Q1']
            q1_pct = q1_n / quad_summary['total'] * 100
            q1_perf = quad_summary['means']['Q1']

            st.success(f"""
            **✅ Viel Zutrauen, wenig Angst (Q1):**
            - **{q1_n:.0f} Schüler:innen** ({q1_pct:.1f}% der Stichprobe)
            - **Durchschnittsleistung:** {q1_perf:.0f} Punkte
            - **Status:** Stärken erhalten und weiter herausfordern
            """)

        st.divider()

    # ============================================
    # SECTION 5: KEY FINDINGS
    # ============================================

    st.header("6️⃣ Key Findings")

    st.markdown("**📌 Zusammenfassung der wichtigsten Erkenntnisse:**")

    # Dynamically generated key findings
    findings = []

    # Finding 1: Sample
    findings.append(f"**Stichprobe:** N = {len(df):,} Schüler aus PISA 2022 Deutschland")

    # Finding 2: Strongest predictor
    if len(corr_df) > 0:
        strongest = corr_df.iloc[0]
        findings.append(
            f"**Stärkster Prädiktor:** {strongest['Bezeichnung']} mit r = {strongest['r']:.3f} "
            f"(R² = {strongest['R² (%)']:.1f}%, Effektstärke: {strongest['Effektstärke']})"
        )

    # Finding 3: MATHEFF vs ANXMAT
    if 'ANXMAT' in selected_vars and 'MATHEFF' in selected_vars:
        corr_matheff = corr_df[corr_df['Variable'] == 'MATHEFF']['r'].values[0]
        corr_anxmat = corr_df[corr_df['Variable'] == 'ANXMAT']['r'].values[0]

        if float(corr_anxmat) != 0:
            ratio = abs(float(corr_matheff) / float(corr_anxmat))

            findings.append(
                f"**Selbstwirksamkeit vs. Angst:** MATHEFF (r = {float(corr_matheff):.3f}) ist "
                f"{ratio:.2f}x einflussreicher als ANXMAT (r = {float(corr_anxmat):.3f})"
            )

        # Finding 4: Gruppe mit Foerderbedarf (aus den Daten abgeleitet)
        if 'quad_summary' in locals() and quad_summary.get('complete'):
            findings.append(quadrant_support_finding(quad_summary))

    # Finding 5: Average performance
    mean_perf = df['performance'].mean()
    if mean_perf < 482:
        pisa_level = "Level 2 (Basiskompetenzen)"
    elif mean_perf < 545:
        pisa_level = "Level 3 (Solide Kenntnisse)"
    elif mean_perf < 607:
        pisa_level = "Level 4 (Gut)"
    else:
        pisa_level = "Level 5+ (Sehr gut)"

    findings.append(
        f"**Durchschnittsleistung:** {mean_perf:.0f} PISA-Punkte → {pisa_level}"
    )

    # Output findings
    for i, finding in enumerate(findings, 1):
        st.markdown(f"{i}. {finding}")

    st.divider()

    # ============================================
    # SECTION 6: HANDLUNGSEMPFEHLUNGEN
    # ============================================

    st.header("7️⃣ Handlungsempfehlungen")

    st.markdown("**💡 Evidenzbasierte Interventionsvorschläge:**")

    recommendations = []

    # MATHEFF-based recommendations
    if 'MATHEFF' in selected_vars:
        corr_matheff_val = float(corr_df[corr_df['Variable'] == 'MATHEFF']['r'].values[0])
        if abs(corr_matheff_val) > 0.5:
            recommendations.append({
                'Priorität': '🔴 Hoch',
                'Bereich': 'Selbstwirksamkeitsförderung',
                'Maßnahme': 'Mastery Experiences: Strukturierte Erfolgserlebnisse schaffen (z.B. gestufte Aufgaben)',
                'Begründung': f'Starke Korrelation (r = {corr_matheff_val:.3f}) rechtfertigt hohen Fokus',
                'Theorie': 'Bandura (1997): Self-Efficacy Theory'
            })

    # ANXMAT-based recommendations
    if 'ANXMAT' in selected_vars:
        corr_anxmat_val = float(corr_df[corr_df['Variable'] == 'ANXMAT']['r'].values[0])
        if abs(corr_anxmat_val) > 0.3:
            recommendations.append({
                'Priorität': '🟡 Mittel',
                'Bereich': 'Angstreduktion',
                'Maßnahme': 'Kognitive Umstrukturierung & Entspannungstechniken (z.B. progressive Muskelrelaxation)',
                'Begründung': f'Mittlere Korrelation (r = {corr_anxmat_val:.3f})',
                'Theorie': 'Beck (1976): Cognitive Therapy'
            })

    # Foerderung bei niedriger Selbstwirksamkeit (Q3 + Q4)
    if 'ANXMAT' in selected_vars and 'MATHEFF' in selected_vars and 'quad_summary' in locals():
        if support_pct > 15:
            recommendations.append({
                'Priorität': '🔴 Hoch',
                'Bereich': 'Förderung bei niedriger Selbstwirksamkeit',
                'Maßnahme': 'Gezielte Förderung für Q3 + Q4: Selbstwirksamkeit durch gestufte Erfolgserlebnisse aufbauen; in Q3 zusätzlich Umgang mit Mathe-Angst',
                'Begründung': f'{support_pct:.1f}% der Schüler:innen mit niedriger Selbstwirksamkeit (Ø {quad_summary["support_perf"]:.0f} Punkte)',
                'Theorie': 'Bandura (1997): Mastery Experiences'
            })

    # General recommendations
    recommendations.append({
        'Priorität': '🟢 Basis',
        'Bereich': 'Diagnostik & Monitoring',
        'Maßnahme': 'Regelmäßiges Screening von Selbstwirksamkeit & Angst (z.B. quartalsweise)',
        'Begründung': 'Früherkennung ermöglicht rechtzeitige Intervention',
        'Theorie': 'Response to Intervention (RTI) Framework'
    })

    recommendations.append({
        'Priorität': '🟢 Basis',
        'Bereich': 'Lehrkräftefortbildung',
        'Maßnahme': 'Professionalisierung im Bereich motivationale Überzeugungen und Emotionsregulation',
        'Begründung': 'Lehrkräfte benötigen Wissen über psychologische Faktoren',
        'Theorie': 'Professional Development Research'
    })

    rec_df = pd.DataFrame(recommendations)
    st.dataframe(rec_df, use_container_width=True, hide_index=True)

    st.divider()

    # ============================================
    # SECTION 7: EXPORT
    # ============================================

    st.header("8️⃣ Ergebnisse exportieren")

    st.markdown("""
    **Lade alle Ergebnisse herunter für:**
    - Weiterverarbeitung in Excel/SPSS
    - Integration in Berichte und Präsentationen
    - Dokumentation und Archivierung
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📊 Deskriptive Statistiken")

        csv_desc = desc_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV herunterladen",
            data=csv_desc,
            file_name=f"pisa_deskriptiv_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key="download_desc"
        )

    with col2:
        st.markdown("### 🔗 Korrelationen")

        csv_corr = corr_df.to_csv(index=False, encoding='utf-8-sig')
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

            csv_quad = quadrant_stats.to_csv(encoding='utf-8-sig')
            st.download_button(
                label="📥 CSV herunterladen",
                data=csv_quad,
                file_name=f"pisa_quadranten_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_quad"
            )

    st.divider()

    # EXCEL Export with all sheets
    st.markdown("### 📗 Kompletter Export (Excel mit allen Sheets)")

    try:
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: Overview
            overview_data = {
                'Kennzahl': [
                    'Analysedatum',
                    'Leistungsvariable',
                    'Anzahl Schüler',
                    'Durchschnittsleistung',
                    'PISA-Level',
                    'Anzahl analysierte Variablen'
                ],
                'Wert': [
                    pd.Timestamp.now().strftime('%Y-%m-%d'),
                    performance_var,
                    len(df),
                    f"{mean_perf:.2f}",
                    pisa_level,
                    len(selected_vars)
                ]
            }
            pd.DataFrame(overview_data).to_excel(writer, sheet_name='Übersicht', index=False)

            # Sheet 2: Descriptive Statistics
            desc_df.to_excel(writer, sheet_name='Deskriptive Statistik', index=False)

            # Sheet 3: Correlations
            corr_df.to_excel(writer, sheet_name='Korrelationen', index=False)

            # Sheet 4: Quadrants (if available)
            if 'quadrant_stats' in locals():
                quadrant_stats.to_excel(writer, sheet_name='Quadranten-Analyse')

            # Sheet 5: Recommendations
            rec_df.to_excel(writer, sheet_name='Handlungsempfehlungen', index=False)

        output.seek(0)

        st.download_button(
            label="📥 Excel-Report herunterladen",
            data=output,
            file_name=f"PISA_Ergebnisreport_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.success("✅ Excel-Report bereit zum Download!")

    except Exception as e:
        st.error(f"❌ Fehler beim Erstellen des Excel-Reports: {e}")
        st.info("💡 Tipp: Installiere openpyxl mit `pip install openpyxl`")

else:
    st.warning("⚠️ Bitte wähle mindestens 2 Variablen für die Analyse.")

# ============================================
# FOOTER
# ============================================

st.divider()

st.caption("""
📋 **Ergebnisübersicht** | PISA 2022 Deutschland |
Evidenzbasierte Handlungsempfehlungen nach wissenschaftlichen Standards
""")
