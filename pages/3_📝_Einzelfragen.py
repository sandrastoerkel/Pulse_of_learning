import streamlit as st
import pandas as pd
import sys
import zipfile
from io import BytesIO
sys.path.append('..')
from utils.db_loader import get_db_connection, load_question_text, load_value_labels, count_non_null
from utils.scale_info import get_all_scales, get_scale_info, get_scale_category, SCALE_CATEGORIES
from utils.json_item_loader import (
    has_json_items,
    get_scale_items,
    get_fragestamm,
    get_scale_metadata,
    get_items_availability_summary,
    is_calculated_index,
    get_index_info,
    get_calculation_note
)
from utils.survey_generator import generate_html_form, estimate_survey_duration
from utils.sheets_template import create_excel_template, create_google_apps_script_template
from utils.qr_generator import generate_qr_code_with_instructions
from utils.instruction_pdf import create_teacher_instructions

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="Einzelfragen",
    page_icon="📝",
    layout="wide"
)

# ============================================
# TITLE
# ============================================

st.title("📝 Phase 3: Einzelfragen verstehen")
st.markdown("**Welche Fragen wurden gestellt? Teste deine eigenen Schüler!**")

st.divider()

# ============================================
# ITEMS AVAILABILITY OVERVIEW
# ============================================

with st.expander("📊 Übersicht: Verfügbare Item-Informationen aus PISA Skalenhandbuch"):
    summary = get_items_availability_summary()

    # Statistiken
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gesamt Skalen", summary['total_scales'])
    with col2:
        st.metric("✅ Mit Items", summary['scales_with_items'])
    with col3:
        st.metric("❌ Ohne Items", summary['scales_without_items'])

    st.info(f"**Gesamt: {summary['total_items']} Einzelfragen** verfügbar aus dem PISA 2022 Skalenhandbuch")

    # Tabelle mit allen Skalen
    import pandas as pd
    df_summary = pd.DataFrame(summary['scales'])
    df_summary['Status'] = df_summary['hat_items'].apply(lambda x: '✅' if x else '❌')

    # Zeige nur relevante Spalten
    display_df = df_summary[['Status', 'code', 'titel', 'anzahl_items']].copy()
    display_df.columns = ['Status', 'Skala', 'Titel', 'Anzahl Items']

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )

    st.caption("✅ = Items vorhanden | ❌ = Keine Items (Index/Composite Variable)")

st.divider()

# ============================================
# LOAD DATA
# ============================================

conn = get_db_connection()

# ============================================
# SCALE SELECTION
# ============================================

st.header("🎯 Skalen-Auswahl")

# Category selection first
selected_category = st.selectbox(
    "1️⃣ Wähle Konstrukt:",
    options=list(SCALE_CATEGORIES.keys()),
    index=0
)

# Get scales in category
available_scales = SCALE_CATEGORIES[selected_category]["scales"]

# Scale selection
selected_scale = st.selectbox(
    "2️⃣ Wähle Skala:",
    options=available_scales,
    format_func=lambda x: f"{x} - {get_scale_info(x).get('name_de', x)}"
)

st.divider()

# ============================================
# SCALE OVERVIEW
# ============================================

if selected_scale:
    info = get_scale_info(selected_scale)
    category = get_scale_category(selected_scale)
    n_avail = count_non_null(conn, selected_scale)

    st.header(f"📊 {selected_scale} - {info.get('name_de', 'N/A')}")

    col1, col2, col3 = st.columns(3)

    with col1:
        status = "✅ Verfügbar" if n_avail > 0 else "❌ Keine Daten"
        st.metric("Status", status)

    with col2:
        st.metric("Verfügbare Daten", f"{n_avail:,} Schüler" if n_avail > 0 else "0")

    with col3:
        if n_avail > 0:
            coverage = (n_avail / 6116) * 100
            st.metric("Coverage", f"{coverage:.1f}%")

    # Description
    if info.get('description_de'):
        st.info(f"**Beschreibung:** {info['description_de']}")

    st.divider()

    # ============================================
    # FIND INDIVIDUAL ITEMS
    # ============================================

    st.header("📝 Einzelfragen zu dieser Skala")

    # Check JSON first
    json_has_items = has_json_items(selected_scale)
    items_found = []
    source = "Unbekannt"

    if json_has_items:
        # Load from JSON
        items_found = get_scale_items(selected_scale)
        source = "PISA 2022 Skalenhandbuch (JSON)"

        # Show Fragestamm if available
        fragestamm = get_fragestamm(selected_scale)
        if fragestamm:
            st.info(f"""
            **📋 Fragestamm (Einleitungstext für alle Items):**

            _{fragestamm}_

            ---

            **Quelle:** {source}
            """)
        else:
            st.info(f"**Quelle:** {source}")

    else:
        # Fallback to database search
        st.info("""
        **Hinweis:** WLE-Skalen werden aus mehreren Einzelfragen berechnet.
        Hier suchst du nach den zugehörigen Items.

        Für diese Skala sind keine Items im PISA Skalenhandbuch dokumentiert.
        Suche in der Datenbank...
        """)

        # Extract potential base variable name (e.g., ST290 from ST290Q01IA)
        base_patterns = []

        # Common patterns for scale items
        if selected_scale.startswith('MATHEFF'):
            base_patterns = ['ST290']  # Math self-efficacy items
        elif selected_scale.startswith('ANXMAT'):
            base_patterns = ['ST292']  # Math anxiety items
        elif selected_scale.startswith('BELONG'):
            base_patterns = ['ST034']  # Belonging items
        elif selected_scale.startswith('TEACHSUP'):
            base_patterns = ['ST100']  # Teacher support items
        elif selected_scale.startswith('DISCLIM'):
            base_patterns = ['ST097']  # Disciplinary climate
        else:
            # Generic search
            base_patterns = [selected_scale[:5]]

        # Search for items
        for pattern in base_patterns:
            query = f"""
            SELECT DISTINCT variable_name, question_text_en, question_text_de
            FROM question_text
            WHERE variable_name LIKE '{pattern}%'
            ORDER BY variable_name
            """
            try:
                items_df = pd.read_sql_query(query, conn)
                if len(items_df) > 0:
                    items_found.extend(items_df.to_dict('records'))
            except:
                pass

        source = "Datenbank (Automatische Suche)"

    if len(items_found) == 0:
        # Prüfe ob es ein berechneter Index ist
        if is_calculated_index(selected_scale):
            index_info = get_index_info(selected_scale)
            calculation_note = get_calculation_note(selected_scale)

            st.info(f"""
            ℹ️ **BERECHNETER INDEX / ZUSAMMENGESETZTE VARIABLE**

            Die Skala `{selected_scale}` ist ein **zusammengesetzter Index** ohne direkte Einzelfragen.
            Dieser wird aus mehreren anderen Variablen berechnet.

            **Verwendungszweck:**
            - ✅ Kontextualisierung und Differenzierung
            - ✅ Wissenschaftliche Fundierung
            - ✅ Gruppierung und Stratifizierung

            **Typ:** {index_info.get('typ', 'N/A') if index_info else 'Zusammengesetzter Index'}
            """)

            if calculation_note:
                with st.expander("📊 Berechnungshinweise und Details"):
                    st.markdown(f"**Anmerkung zur Berechnung:**\n\n{calculation_note}")

                    if index_info:
                        if 'fragestamm' in index_info and index_info['fragestamm']:
                            st.markdown(f"\n**Fragestamm:** {index_info['fragestamm']}")

            st.warning("""
            **Wichtig für die Nutzung:**

            Diese Skala hat keine direkten Einzelfragen, die du in einem Fragebogen verwenden kannst.
            Sie dient zur:
            - Differenzierung von Schülergruppen (z.B. nach ESCS)
            - Kontextualisierung von Ergebnissen
            - Wissenschaftlichen Fundierung deiner Analysen

            Weitere Details findest du im PISA 2022 Skalenhandbuch.
            """)
        else:
            st.warning(f"""
            ⚠️ **Keine Einzelfragen gefunden**

            Für die Skala `{selected_scale}` wurden keine zugehörigen Fragetexte gefunden.

            **Mögliche Gründe:**
            - Diese Skala ist ein aggregierter Index ohne Einzelfragen
            - Die Fragetexte sind unter einem anderen Namen gespeichert
            - Die Items sind nicht in der öffentlichen Datenbank enthalten

            **Alternativen:**
            - Konsultiere das [PISA 2022 Technical Report](https://www.oecd.org/pisa/)
            - Verwende das offizielle Skalenhandbuch
            - Kontaktiere die OECD für vollständige Item-Listen
            """)

    else:
        st.success(f"✅ **{len(items_found)} Einzelfragen gefunden!**")

        # ============================================
        # DISPLAY INDIVIDUAL ITEMS
        # ============================================

        for idx, item in enumerate(items_found, 1):
            variable = item.get('variable_name', 'N/A')
            text_en = item.get('question_text_en', 'N/A')
            text_de = item.get('question_text_de', None)

            st.markdown(f"### 📝 Frage {idx} von {len(items_found)}: `{variable}`")

            # German text (if available)
            if text_de and pd.notna(text_de) and text_de != 'N/A':
                st.success(f"**🇩🇪 DEUTSCHER FRAGETEXT:**\n\n{text_de}")

                # Nur Expander zeigen wenn EN text anders ist
                if text_en != text_de and text_en != 'N/A':
                    with st.expander("🇬🇧 Englischen Text anzeigen"):
                        st.text(text_en)
            else:
                st.success(f"**🇬🇧 QUESTION TEXT:**\n\n{text_en}")

            # Load value labels
            value_labels = load_value_labels(conn, variable)

            if len(value_labels) > 0:
                st.markdown("**📊 ANTWORTOPTIONEN:**")

                # Create display table
                display_vl = value_labels.copy()

                # Use German labels if available
                display_vl['Antwort'] = display_vl.apply(
                    lambda row: row['label_de'] if pd.notna(row.get('label_de'))
                    else row['label'],
                    axis=1
                )

                # Format percentage
                if 'percent' in display_vl.columns and display_vl['percent'].notna().any():
                    display_vl['Häufigkeit'] = display_vl.apply(
                        lambda row: f"{row['percent']:.1f}%" if pd.notna(row['percent']) else "",
                        axis=1
                    )
                    display_cols = ['value', 'Antwort', 'Häufigkeit']
                else:
                    display_cols = ['value', 'Antwort']

                # Mark missing codes
                if 'is_missing_code' in display_vl.columns:
                    display_vl['value'] = display_vl.apply(
                        lambda row: f"~~{row['value']}~~" if row.get('is_missing_code') == 1
                        else str(row['value']),
                        axis=1
                    )

                st.dataframe(
                    display_vl[display_cols],
                    use_container_width=True,
                    hide_index=True
                )

                if (display_vl.get('is_missing_code') == 1).any():
                    st.caption("~~Durchgestrichene Werte~~ = Missing Codes (97, 98, 99)")

            st.divider()

        # ============================================
        # TEMPLATE DOWNLOAD SECTION
        # ============================================

        st.header("📥 Test-Template für deine Schüler")

        st.info("""
        **Verwende diese Fragen für deine eigene Klasse!**

        Erstelle einen Fragebogen basierend auf den PISA-Items und vergleiche
        deine Schüler mit den PISA-Ergebnissen.
        """)

        # Estimate duration
        estimated_minutes = estimate_survey_duration(len(items_found))

        # Info metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📝 Anzahl Fragen", len(items_found))
        with col2:
            st.metric("⏱️ Geschätzte Zeit", f"{estimated_minutes} Min")
        with col3:
            st.metric("📱 Mobil-optimiert", "✅ Ja")

        st.divider()

        # Main button to generate complete package
        if st.button("📱 Digitale Befragung erstellen", type="primary", use_container_width=True):
            with st.spinner("Erstelle Befragungspaket... Dies kann einen Moment dauern."):
                try:
                    # Prepare data
                    value_labels_dict = {}
                    for item in items_found:
                        variable = item.get('variable_name', 'N/A')
                        value_labels_dict[variable] = load_value_labels(conn, variable)

                    # Get PISA average (placeholder - you can add real values from DB)
                    pisa_average = 2.5  # Default

                    # 1. Generate HTML Form
                    html_content = generate_html_form(
                        scale_name=selected_scale,
                        scale_title=info.get('name_de', selected_scale),
                        items=items_found,
                        value_labels=value_labels_dict,
                        fragestamm=fragestamm,
                        google_script_url=""  # Will be filled by teacher
                    )

                    # 2. Generate Excel Template
                    excel_buffer = create_excel_template(
                        scale_name=selected_scale,
                        scale_title=info.get('name_de', selected_scale),
                        items=items_found,
                        pisa_average=pisa_average
                    )

                    # 3. Generate Google Apps Script
                    gas_script = create_google_apps_script_template(
                        scale_name=selected_scale,
                        items=items_found
                    )

                    # 4. Generate QR Code
                    qr_url = "file:///path/to/befragung.html"  # Placeholder
                    qr_buffer = generate_qr_code_with_instructions(
                        url=qr_url,
                        scale_title=info.get('name_de', selected_scale)
                    )

                    # 5. Generate PDF Instructions
                    pdf_buffer = create_teacher_instructions(
                        scale_name=selected_scale,
                        scale_title=info.get('name_de', selected_scale),
                        scale_description=info.get('description_de', 'Keine Beschreibung verfügbar'),
                        num_items=len(items_found),
                        estimated_minutes=estimated_minutes,
                        qr_code_buffer=qr_buffer
                    )

                    # 6. Create ZIP package
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        # Add HTML
                        zip_file.writestr('befragung.html', html_content)

                        # Add Excel
                        zip_file.writestr('auswertung_template.xlsx', excel_buffer.getvalue())

                        # Add Google Apps Script
                        zip_file.writestr('google_apps_script.txt', gas_script)

                        # Add QR Code
                        qr_buffer.seek(0)
                        zip_file.writestr('qr_code.png', qr_buffer.read())

                        # Add PDF Instructions
                        pdf_buffer.seek(0)
                        zip_file.writestr('anleitung_lehrer.pdf', pdf_buffer.read())

                        # Add README
                        readme_content = f"""# PISA Befragung: {info.get('name_de', selected_scale)}

## 📦 Inhalt dieses Pakets

1. **befragung.html** - Mobil-optimiertes Formular für Schüler
2. **auswertung_template.xlsx** - Google Sheets kompatibles Excel mit Formeln
3. **google_apps_script.txt** - Code zum Einfügen in Google Sheets
4. **qr_code.png** - QR-Code für einfachen Zugriff
5. **anleitung_lehrer.pdf** - Vollständige Schritt-für-Schritt Anleitung

## 🚀 Quick Start

1. Lese die **anleitung_lehrer.pdf** komplett durch
2. Lade **auswertung_template.xlsx** in Google Drive hoch
3. Richte Google Apps Script ein (siehe Anleitung)
4. Zeige den QR-Code deinen Schülern
5. Analysiere die Ergebnisse in Google Sheets

## 📊 Über diese Skala

**Skala:** {selected_scale}
**Titel:** {info.get('name_de', selected_scale)}
**Anzahl Fragen:** {len(items_found)}
**Bearbeitungszeit:** ca. {estimated_minutes} Minuten

**Beschreibung:**
{info.get('description_de', 'Keine Beschreibung verfügbar')}

## 📚 Quelle

PISA 2022 Skalenhandbuch
OECD Programme for International Student Assessment

## 💡 Support

Bei Fragen oder Problemen konsultieren Sie die PDF-Anleitung oder
besuchen Sie die OECD PISA Website: www.oecd.org/pisa

---
Generiert mit Pulse of Learning - PISA 2022 Explorer
"""
                        zip_file.writestr('README.md', readme_content)

                    zip_buffer.seek(0)

                    # Success message
                    st.success("✅ Befragungspaket erfolgreich erstellt!")

                    # Download button
                    st.download_button(
                        label="📥 Befragungspaket herunterladen (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"PISA_Befragung_{selected_scale}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )

                    # Show what's included
                    with st.expander("📦 Was ist im Paket enthalten?"):
                        st.markdown("""
                        ✅ **befragung.html** - Mobil-optimiertes Formular (öffne im Browser)

                        ✅ **auswertung_template.xlsx** - Excel mit automatischen Formeln

                        ✅ **google_apps_script.txt** - Code für Google Sheets Integration

                        ✅ **qr_code.png** - QR-Code zum Ausdrucken/Teilen

                        ✅ **anleitung_lehrer.pdf** - Vollständige Anleitung (START HIER!)

                        ✅ **README.md** - Übersicht und Quick Start
                        """)

                        st.info("""
                        **💡 Tipp:** Beginne mit der **anleitung_lehrer.pdf** - dort findest du
                        eine detaillierte Schritt-für-Schritt Anleitung für die komplette Einrichtung!
                        """)

                except Exception as e:
                    st.error(f"❌ Fehler beim Erstellen des Pakets: {str(e)}")
                    st.exception(e)

        # ============================================
        # MANUAL COPY-PASTE
        # ============================================

        st.markdown("---")
        st.markdown("### ✂️ Oder kopiere die Fragen manuell:")

        # Create simple text export
        export_text = f"# {selected_scale} - {info.get('name_de', 'N/A')}\n\n"
        export_text += f"**Anzahl Fragen:** {len(items_found)}\n\n"
        export_text += "---\n\n"

        for idx, item in enumerate(items_found, 1):
            variable = item['variable_name']
            text_de = item.get('question_text_de', item.get('question_text_en', ''))

            export_text += f"## Frage {idx}: {variable}\n\n"
            export_text += f"{text_de}\n\n"

            # Add answer options
            value_labels = load_value_labels(conn, variable)
            if len(value_labels) > 0:
                export_text += "**Antwortoptionen:**\n\n"
                for _, vl in value_labels.iterrows():
                    if vl.get('is_missing_code') != 1:
                        label = vl['label_de'] if pd.notna(vl.get('label_de')) else vl['label']
                        export_text += f"- [ ] {vl['value']}: {label}\n"

            export_text += "\n---\n\n"

        st.text_area(
            "Kopiere diesen Text:",
            export_text,
            height=300,
            help="Markiere den gesamten Text und kopiere ihn (Ctrl+C / Cmd+C)"
        )

# ============================================
# FOOTER
# ============================================

st.divider()

st.caption("""
📚 **Quelle:** PISA 2022 Fragebogendaten
💡 **Tipp:** Nutze diese Items für eigene Schülerbefragungen
""")
