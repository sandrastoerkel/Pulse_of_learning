import streamlit as st
import pandas as pd
import sys
sys.path.append('..')
from utils.db_loader import get_db_connection, get_available_scales, count_non_null
from utils.scale_info import SCALE_CATEGORIES, get_scale_category, get_scale_info, get_all_scales

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="Skalen Explorer",
    page_icon="🔍",
    layout="wide"
)

# ============================================
# TITLE
# ============================================

st.title("🔍 Phase 2: Skalen-Explorer")
st.markdown("**58 verfügbare WLE-Skalen durchsuchen und verstehen**")

st.divider()

# ============================================
# LOAD DATA
# ============================================

conn = get_db_connection()

# Load available scales from database
db_scales = get_available_scales(conn)

# ============================================
# FILTER SECTION
# ============================================

st.header("🎯 Filter & Suche")

col1, col2 = st.columns([2, 1])

with col1:
    search_term = st.text_input(
        "🔍 Suche nach Skalennamen oder Konstrukt:",
        placeholder="z.B. 'self-efficacy', 'anxiety', 'ICT'",
        help="Durchsucht Variablennamen und Labels"
    )

with col2:
    show_only_available = st.checkbox(
        "Nur verfügbare Skalen (58)",
        value=True,
        help="Blendet leere Skalen aus"
    )

st.markdown("**📊 Filter nach Konstrukt:**")

# Multi-select for categories
selected_categories = st.multiselect(
    "Wähle Kategorien:",
    options=list(SCALE_CATEGORIES.keys()),
    default=list(SCALE_CATEGORIES.keys()),
    help="Filtern nach thematischen Gruppen"
)

st.divider()

# ============================================
# BUILD FILTERED LIST
# ============================================

# Get scales from selected categories
filtered_scales = []
for category in selected_categories:
    filtered_scales.extend(SCALE_CATEGORIES[category]["scales"])

# Apply search filter
if search_term:
    search_lower = search_term.lower()
    filtered_scales = [
        s for s in filtered_scales
        if search_lower in s.lower() or
           search_lower in get_scale_info(s).get('name_de', '').lower() or
           search_lower in get_scale_info(s).get('name_en', '').lower()
    ]

# Build display dataframe
display_data = []

for scale in filtered_scales:
    info = get_scale_info(scale)
    category = get_scale_category(scale)

    # Count non-null values
    n_available = count_non_null(conn, scale)

    # Filter by availability
    if show_only_available and n_available == 0:
        continue

    display_data.append({
        'Variable': scale,
        'Deutsche Bezeichnung': info.get('name_de', scale),
        'Englische Bezeichnung': info.get('name_en', scale),
        'Kategorie': category,
        'N (Verfügbar)': n_available,
        'Status': '✅ Verfügbar' if n_available > 0 else '❌ Leer'
    })

result_df = pd.DataFrame(display_data)

# ============================================
# RESULTS SECTION
# ============================================

st.header(f"📋 Ergebnisse ({len(result_df)} Skalen)")

if len(result_df) == 0:
    st.warning("Keine Skalen gefunden. Passe deine Filter an.")
else:
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Gefundene Skalen", len(result_df))

    with col2:
        available_count = len(result_df[result_df['N (Verfügbar)'] > 0])
        st.metric("Verfügbar", available_count)

    with col3:
        if len(result_df) > 0:
            avg_n = result_df[result_df['N (Verfügbar)'] > 0]['N (Verfügbar)'].mean()
            st.metric("Ø N", f"{avg_n:,.0f}" if not pd.isna(avg_n) else "0")

    with col4:
        category_count = result_df['Kategorie'].nunique()
        st.metric("Kategorien", category_count)

    st.divider()

    # Sort options
    sort_by = st.selectbox(
        "Sortieren nach:",
        options=['Variable', 'N (Verfügbar)', 'Kategorie', 'Deutsche Bezeichnung'],
        index=1  # Default: by N
    )

    result_df_sorted = result_df.sort_values(sort_by, ascending=(sort_by != 'N (Verfügbar)'))

    # Display table
    st.dataframe(
        result_df_sorted,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Variable": st.column_config.TextColumn("Variable", width="small"),
            "Deutsche Bezeichnung": st.column_config.TextColumn("Deutsche Bezeichnung", width="medium"),
            "Englische Bezeichnung": st.column_config.TextColumn("Englische Bezeichnung", width="medium"),
            "Kategorie": st.column_config.TextColumn("Kategorie", width="medium"),
            "N (Verfügbar)": st.column_config.NumberColumn("N", format="%d", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small")
        }
    )

    st.divider()

    # ============================================
    # CATEGORY BREAKDOWN
    # ============================================

    st.header("📊 Verteilung nach Kategorie")

    category_summary = result_df.groupby('Kategorie').agg({
        'Variable': 'count',
        'N (Verfügbar)': 'sum'
    }).reset_index()
    category_summary.columns = ['Kategorie', 'Anzahl Skalen', 'Gesamt N']

    # Add description
    category_summary['Beschreibung'] = category_summary['Kategorie'].apply(
        lambda x: SCALE_CATEGORIES.get(x, {}).get('description', '')
    )

    st.dataframe(
        category_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Kategorie": st.column_config.TextColumn("Kategorie", width="medium"),
            "Anzahl Skalen": st.column_config.NumberColumn("Skalen", format="%d", width="small"),
            "Gesamt N": st.column_config.NumberColumn("Gesamt N", format="%d", width="small"),
            "Beschreibung": st.column_config.TextColumn("Beschreibung", width="large")
        }
    )

    st.divider()

    # ============================================
    # DETAIL VIEW FOR SELECTED SCALE
    # ============================================

    st.header("🔎 Skalen-Details")

    if len(result_df_sorted) > 0:
        selected_scale = st.selectbox(
            "Wähle eine Skala für Details:",
            options=result_df_sorted['Variable'].tolist(),
            format_func=lambda x: f"{x} - {get_scale_info(x).get('name_de', x)}"
        )

        if selected_scale:
            info = get_scale_info(selected_scale)
            category = get_scale_category(selected_scale)
            n_avail = count_non_null(conn, selected_scale)

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"### {selected_scale}")
                st.markdown(f"**🇩🇪 Deutsch:** {info.get('name_de', 'N/A')}")
                st.markdown(f"**🇬🇧 English:** {info.get('name_en', 'N/A')}")

                if info.get('description_de'):
                    st.info(info['description_de'])

            with col2:
                st.markdown("**📊 Statistik:**")
                st.metric("Kategorie", category)
                st.metric("Verfügbare Daten", f"{n_avail:,} Schüler")

                if n_avail > 0:
                    coverage_pct = (n_avail / 6116) * 100
                    st.metric("Coverage", f"{coverage_pct:.1f}%")

            st.divider()

            # Action buttons
            st.markdown("**🎯 Nächste Schritte:**")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.info("📝 **Phase 3:**\nEinzelfragen ansehen")

            with col2:
                st.info("📈 **Phase 4:**\nTiefenanalyse durchführen")

            with col3:
                st.info("📥 **Phase 3:**\nTest-Template erstellen")

# ============================================
# FOOTER
# ============================================

st.divider()

st.caption("""
📚 **Quelle:** PISA 2022 Deutschland-Daten (6,116 Schüler)
📊 **WLE-Skalen:** Weighted Likelihood Estimates (IRT-basiert)
""")
