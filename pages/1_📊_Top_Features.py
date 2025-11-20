import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys
sys.path.append('..')
from utils.scale_info import get_scale_category, get_scale_info, SCALE_CATEGORIES
from utils.feature_descriptions import get_feature_description_bilingual, get_feature_label

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="Top 15 Features",
    page_icon="📊",
    layout="wide"
)

# ============================================
# TITLE
# ============================================

st.title("📊 Phase 1: Top 15 Features")
st.markdown("**Die wichtigsten Einflussfaktoren auf Leistung (Math, Reading, Science)**")

st.divider()

# ============================================
# LOAD FEATURE IMPORTANCE
# ============================================

@st.cache_data(ttl=10)  # Cache nur 10 Sekunden, dann neu laden
def load_feature_importance():
    """Lädt Top Features aus SHAP-Analyse (falls vorhanden)"""
    importance_path = Path("outputs/feature_importance.csv")

    if importance_path.exists():
        return pd.read_csv(importance_path)
    else:
        return None


# Add reload button in sidebar
if st.sidebar.button("🔄 Daten neu laden"):
    st.cache_data.clear()
    st.rerun()

importance_df = load_feature_importance()

# ============================================
# MAIN CONTENT
# ============================================

if importance_df is None:
    # Keine SHAP-Daten vorhanden - zeige Platzhalter
    st.warning("""
    ⚠️ **Noch keine Top Features berechnet**

    Die Top 15 Features werden durch eine SHAP-Analyse (XGBoost) berechnet.

    **Nächste Schritte:**
    1. Gehe zu **Phase 5: ML Pipeline** in der Sidebar
    2. Führe dort Preprocessing, Training und SHAP-Analyse durch
    3. Komme hierher zurück für die Ergebnisse

    **Oder:** Nutze die vorhandenen 58 Skalen in **Phase 2: Skalen-Explorer**
    """)

    # Quick Action Button
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("🔬 Zu Phase 5: ML Pipeline", type="primary", use_container_width=True):
            st.switch_page("pages/5_🔬_ML_Pipeline.py")

    st.divider()

    st.header("📚 Was sind die Top 15 Features?")

    st.info("""
    Die Top 15 Features sind die **einflussreichsten Faktoren** auf die Leistung
    (Math/Reading/Science), identifiziert durch Machine Learning (XGBoost + SHAP).

    **Warum Top 15?**
    - Fokussierung auf das Wesentliche
    - Evidenzbasiert (nicht theoretisch)
    - Praktisch umsetzbar für Interventionen

    **Beispiel aus internationaler Forschung:**
    1. MATHEFF (Mathe-Selbstwirksamkeit) - 16.2%
    2. ANXMAT (Mathe-Angst) - 12.8%
    3. HOMEPOS (Sozioökonomischer Status) - 9.4%
    ...

    *Ihre eigenen Daten können abweichen!*
    """)

else:
    # SHAP-Daten vorhanden - zeige Ranking

    st.success(f"✅ Top {len(importance_df)} Features aus SHAP-Analyse geladen")

    # ============================================
    # TOP N AUSWAHL
    # ============================================

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("🏆 Feature Importance Ranking")

    with col2:
        top_n = st.selectbox(
            "Anzahl Features:",
            options=[10, 15, 20, 25, 30],
            index=1,  # Default: 15
            help="Forscher-Standard: Top 15"
        )

    # Begrenze auf Top N
    top_features = importance_df.head(top_n).copy()

    # ============================================
    # VISUALISIERUNG
    # ============================================

    # Bar Chart
    fig = px.bar(
        top_features,
        x='Importance_%',
        y='Feature',
        orientation='h',
        title=f'Top {top_n} Features nach Importance',
        labels={'Importance_%': 'Importance (%)', 'Feature': ''},
        color='Importance_%',
        color_continuous_scale='Blues',
        text='Importance_%'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        height=max(400, top_n * 25),
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ============================================
    # DETAILLIERTE TABELLE MIT KATEGORIEN
    # ============================================

    st.subheader("📋 Detaillierte Feature-Informationen")

    # Füge Kategorie und Beschreibung hinzu
    display_df = top_features.copy()
    display_df['Rank'] = range(1, len(display_df) + 1)
    display_df['Kategorie'] = display_df['Feature'].apply(get_scale_category)

    # Füge deutsche Namen hinzu (mit Fallback auf feature_descriptions)
    def get_german_name(feature):
        info = get_scale_info(feature)
        if info.get('name_de') and info['name_de'] != feature:
            return info['name_de']
        else:
            # Fallback: try feature_descriptions
            return get_feature_label(feature, language='de', include_code=False)

    display_df['Deutsche Bezeichnung'] = display_df['Feature'].apply(get_german_name)

    # Add bilingual description column
    display_df['Beschreibung'] = display_df['Feature'].apply(get_feature_description_bilingual)

    # Spalten ordnen
    display_df = display_df[['Rank', 'Feature', 'Deutsche Bezeichnung', 'Beschreibung', 'Kategorie', 'Importance_%']]
    display_df['Importance_%'] = display_df['Importance_%'].round(2)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("🏆 Rang", width="small"),
            "Feature": st.column_config.TextColumn("Variable", width="small"),
            "Deutsche Bezeichnung": st.column_config.TextColumn("Bezeichnung", width="medium"),
            "Beschreibung": st.column_config.TextColumn("Beschreibung (EN/DE)", width="large"),
            "Kategorie": st.column_config.TextColumn("Kategorie", width="medium"),
            "Importance_%": st.column_config.NumberColumn("Importance (%)", format="%.2f", width="small")
        }
    )

    st.divider()

    # ============================================
    # VERTEILUNG NACH KATEGORIE
    # ============================================

    st.subheader("📈 Verteilung nach Konstrukt")

    category_summary = display_df.groupby('Kategorie').agg({
        'Importance_%': 'sum',
        'Feature': 'count'
    }).reset_index()
    category_summary.columns = ['Kategorie', 'Gesamt Importance (%)', 'Anzahl Features']
    category_summary = category_summary.sort_values('Gesamt Importance (%)', ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        # Pie Chart
        fig_pie = px.pie(
            category_summary,
            values='Gesamt Importance (%)',
            names='Kategorie',
            title='Importance nach Kategorie'
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # Bar Chart
        fig_cat = px.bar(
            category_summary,
            x='Gesamt Importance (%)',
            y='Kategorie',
            orientation='h',
            title='Features pro Kategorie',
            text='Anzahl Features',
            color='Anzahl Features',
            color_continuous_scale='Greens'
        )
        fig_cat.update_traces(textposition='inside')
        st.plotly_chart(fig_cat, use_container_width=True)

    st.divider()

    # ============================================
    # EXPANDABLE FEATURE DETAILS
    # ============================================

    st.subheader("🔍 Feature Details")

    for idx, row in display_df.iterrows():
        rank = row['Rank']
        feature = row['Feature']
        importance = row['Importance_%']
        category = row['Kategorie']

        # Emoji basierend auf Rang
        if rank == 1:
            emoji = "🥇"
        elif rank == 2:
            emoji = "🥈"
        elif rank == 3:
            emoji = "🥉"
        else:
            emoji = "✅"

        with st.expander(f"{emoji} {rank}. {feature} - {get_german_name(feature)} ({importance:.2f}%)"):
            info = get_scale_info(feature)

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**📊 Impact Score:** {importance:.2f}% (Rang {rank})")
                st.markdown(f"**📂 Konstrukt:** {category}")
                st.markdown(f"**📝 Beschreibung:**")
                st.info(info.get('description_de', 'Keine Beschreibung verfügbar'))

            with col2:
                st.markdown("**🎯 Nächste Schritte:**")
                st.markdown("- [Phase 3] Einzelfragen ansehen")
                st.markdown("- [Phase 4] Tiefenanalyse")
                st.markdown("- [Phase 3] Test-Template erstellen")

# ============================================
# FOOTER
# ============================================

st.divider()

st.caption("""
📚 **Methodik:** XGBoost + SHAP (SHapley Additive exPlanations)
📊 **Basis:** PISA 2022 Deutschland-Daten
""")
