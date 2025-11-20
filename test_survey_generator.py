"""
Test-Skript für die Survey Generator Funktionalität

Testet alle Komponenten des digitalen Befragungssystems
"""

import sys
sys.path.append('.')

from utils.survey_generator import generate_html_form, estimate_survey_duration
from utils.sheets_template import create_excel_template, create_google_apps_script_template
from utils.qr_generator import generate_qr_code_with_instructions
from utils.instruction_pdf import create_teacher_instructions
from utils.db_loader import get_db_connection, load_value_labels
from utils.json_item_loader import get_scale_items, get_fragestamm
from utils.scale_info import get_scale_info

import zipfile
from io import BytesIO


def test_survey_generation(scale_name: str = "ANXMAT"):
    """
    Testet die komplette Survey-Generierung für eine Skala
    """

    print(f"\n{'='*60}")
    print(f"🧪 TESTE SURVEY GENERATION FÜR: {scale_name}")
    print(f"{'='*60}\n")

    # 1. Load scale data
    print("1️⃣ Lade Skalen-Daten...")
    items = get_scale_items(scale_name)
    print(f"   ✅ {len(items)} Items gefunden")

    if len(items) == 0:
        print(f"   ❌ Keine Items für {scale_name} gefunden. Test abgebrochen.")
        return False

    fragestamm = get_fragestamm(scale_name)
    if fragestamm:
        print(f"   ✅ Fragestamm vorhanden: {fragestamm[:50]}...")

    info = get_scale_info(scale_name)
    scale_title = info.get('name_de', scale_name)
    scale_description = info.get('description_de', 'Keine Beschreibung')

    # 2. Load value labels
    print("\n2️⃣ Lade Antwort-Labels...")
    conn = get_db_connection()
    value_labels_dict = {}
    for item in items:
        variable = item.get('variable_name', 'N/A')
        value_labels_dict[variable] = load_value_labels(conn, variable)
    print(f"   ✅ Value labels für {len(value_labels_dict)} Items geladen")

    # 3. Generate HTML
    print("\n3️⃣ Generiere HTML-Formular...")
    try:
        html_content = generate_html_form(
            scale_name=scale_name,
            scale_title=scale_title,
            items=items,
            value_labels=value_labels_dict,
            fragestamm=fragestamm,
            google_script_url=""
        )
        print(f"   ✅ HTML generiert ({len(html_content)} Zeichen)")
        radio_count = html_content.count('<input type="radio"')
        print(f"   📄 Enthält {radio_count} Radio-Buttons")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return False

    # 4. Generate Excel
    print("\n4️⃣ Generiere Excel-Template...")
    try:
        excel_buffer = create_excel_template(
            scale_name=scale_name,
            scale_title=scale_title,
            items=items,
            pisa_average=2.5
        )
        print(f"   ✅ Excel generiert ({len(excel_buffer.getvalue())} Bytes)")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return False

    # 5. Generate Google Apps Script
    print("\n5️⃣ Generiere Google Apps Script...")
    try:
        gas_script = create_google_apps_script_template(
            scale_name=scale_name,
            items=items
        )
        print(f"   ✅ Script generiert ({len(gas_script)} Zeichen)")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return False

    # 6. Generate QR Code
    print("\n6️⃣ Generiere QR-Code...")
    try:
        qr_buffer = generate_qr_code_with_instructions(
            url="http://example.com/befragung.html",
            scale_title=scale_title
        )
        print(f"   ✅ QR-Code generiert ({len(qr_buffer.getvalue())} Bytes)")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return False

    # 7. Generate PDF
    print("\n7️⃣ Generiere PDF-Anleitung...")
    try:
        estimated_minutes = estimate_survey_duration(len(items))
        pdf_buffer = create_teacher_instructions(
            scale_name=scale_name,
            scale_title=scale_title,
            scale_description=scale_description,
            num_items=len(items),
            estimated_minutes=estimated_minutes,
            qr_code_buffer=qr_buffer
        )
        print(f"   ✅ PDF generiert ({len(pdf_buffer.getvalue())} Bytes)")
        print(f"   ⏱️ Geschätzte Bearbeitungszeit: {estimated_minutes} Min")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 8. Create ZIP package
    print("\n8️⃣ Erstelle ZIP-Paket...")
    try:
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('befragung.html', html_content)
            zip_file.writestr('auswertung_template.xlsx', excel_buffer.getvalue())
            zip_file.writestr('google_apps_script.txt', gas_script)
            qr_buffer.seek(0)
            zip_file.writestr('qr_code.png', qr_buffer.read())
            pdf_buffer.seek(0)
            zip_file.writestr('anleitung_lehrer.pdf', pdf_buffer.read())
            zip_file.writestr('README.md', '# Test README')

        print(f"   ✅ ZIP erstellt ({len(zip_buffer.getvalue())} Bytes)")

        # List contents
        zip_buffer.seek(0)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            print(f"\n   📦 ZIP-Inhalt:")
            for info in zip_file.filelist:
                print(f"      • {info.filename} ({info.file_size} bytes)")

    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n{'='*60}")
    print(f"✅ ALLE TESTS ERFOLGREICH FÜR {scale_name}")
    print(f"{'='*60}\n")

    return True


if __name__ == "__main__":
    # Test mit ANXMAT (Mathe-Angst)
    success = test_survey_generation("ANXMAT")

    if success:
        print("\n💡 Die Survey-Generierung funktioniert einwandfrei!")
        print("   Du kannst jetzt die Streamlit App starten und die Funktion nutzen.")
        print("\n   Starte mit: streamlit run Home.py")
        print("   Dann gehe zu: Einzelfragen → Wähle ANXMAT → Klicke auf 'Digitale Befragung erstellen'\n")
    else:
        print("\n❌ Test fehlgeschlagen. Bitte Fehler prüfen.\n")
        sys.exit(1)
