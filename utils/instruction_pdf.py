"""
PDF-Anleitung Generator für Lehrkräfte

Erstellt Schritt-für-Schritt Anleitung für die Nutzung der PISA-Befragung.
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from typing import List, Dict


def create_teacher_instructions(
    scale_name: str,
    scale_title: str,
    scale_description: str,
    num_items: int,
    estimated_minutes: int,
    qr_code_buffer: BytesIO = None
) -> BytesIO:
    """
    Erstellt PDF-Anleitung für Lehrkräfte.

    Args:
        scale_name: Skalen-Code
        scale_title: Deutscher Titel
        scale_description: Beschreibung der Skala
        num_items: Anzahl Fragen
        estimated_minutes: Geschätzte Bearbeitungszeit
        qr_code_buffer: Optional QR-Code Image

    Returns:
        BytesIO object mit PDF
    """

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#4472C4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#4472C4'),
        spaceAfter=12,
        spaceBefore=12
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        leftIndent=20,
        bulletIndent=10
    )

    # Story (content)
    story = []

    # ===================================
    # PAGE 1: TITLE & OVERVIEW
    # ===================================

    story.append(Paragraph("📊 PISA Schüler-Befragung", title_style))
    story.append(Paragraph(f"<b>{scale_title}</b>", styles['Heading2']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>Anleitung für Lehrkräfte</b>", heading_style))

    intro_text = f"""
    Diese Anleitung hilft Ihnen dabei, eine wissenschaftlich fundierte Schüler-Befragung
    in Ihrer Klasse durchzuführen. Die Befragung basiert auf der PISA 2022 Studie und
    ermöglicht Ihnen, Ihre Schüler mit internationalen Standards zu vergleichen.
    """
    story.append(Paragraph(intro_text, normal_style))
    story.append(Spacer(1, 0.5*cm))

    # Info box
    info_data = [
        ['Skala:', scale_name],
        ['Titel:', scale_title],
        ['Anzahl Fragen:', str(num_items)],
        ['Bearbeitungszeit:', f'ca. {estimated_minutes} Minuten'],
        ['Quelle:', 'PISA 2022 Skalenhandbuch']
    ]

    info_table = Table(info_data, colWidths=[5*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E7E6E6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    story.append(info_table)
    story.append(Spacer(1, 1*cm))

    # What is being measured
    story.append(Paragraph("📝 Was wird gemessen?", heading_style))
    story.append(Paragraph(scale_description, normal_style))
    story.append(Spacer(1, 0.5*cm))

    story.append(PageBreak())

    # ===================================
    # PAGE 2: STEP-BY-STEP INSTRUCTIONS
    # ===================================

    story.append(Paragraph("🎯 Schritt-für-Schritt Anleitung", title_style))
    story.append(Spacer(1, 0.5*cm))

    # Step 1
    story.append(Paragraph("1️⃣ Vorbereitung (5 Minuten)", heading_style))

    step1_items = [
        "Öffnen Sie die Datei <b>'auswertung_template.xlsx'</b> und laden Sie sie in Google Drive hoch",
        "Öffnen Sie die Datei mit Google Sheets (Rechtsklick → Öffnen mit → Google Sheets)",
        "Öffnen Sie die Datei <b>'befragung.html'</b> in einem Browser",
        "Alternativ: Laden Sie die HTML-Datei auf einen Webserver hoch (z.B. Netlify, GitHub Pages)"
    ]

    for item in step1_items:
        story.append(Paragraph(f"• {item}", bullet_style))

    story.append(Spacer(1, 0.5*cm))

    # Step 2
    story.append(Paragraph("2️⃣ Google Sheets mit HTML verbinden (10 Minuten)", heading_style))

    step2_items = [
        "Öffnen Sie in Google Sheets: <b>Erweiterungen → Apps Script</b>",
        "Löschen Sie den vorhandenen Code",
        "Kopieren Sie den Code aus der Datei <b>'google_apps_script.txt'</b> (im ZIP enthalten)",
        "Fügen Sie den Code ein und klicken Sie auf <b>'Bereitstellen → Neue Bereitstellung'</b>",
        "Wählen Sie <b>'Web-App'</b> als Typ",
        "Setzen Sie 'Ausführen als': <b>'Mich'</b>",
        "Setzen Sie 'Zugriff': <b>'Jeder'</b>",
        "Klicken Sie auf <b>'Bereitstellen'</b> und kopieren Sie die <b>Web-App URL</b>",
        "Öffnen Sie die Datei <b>'befragung.html'</b> in einem Text-Editor",
        "Suchen Sie nach <b>'GOOGLE_SCRIPT_URL'</b> und ersetzen Sie den leeren String durch Ihre URL",
        "Speichern Sie die Datei"
    ]

    for item in step2_items:
        story.append(Paragraph(f"• {item}", bullet_style))

    story.append(Spacer(1, 0.5*cm))

    # Important note
    note_text = """
    <b>⚠️ Wichtig:</b> Die Verbindung zwischen HTML-Formular und Google Sheets erfordert
    einmalig etwas technisches Verständnis. Alternativ können Sie die Daten auch manuell
    aus den heruntergeladenen JSON-Dateien übertragen.
    """
    story.append(Paragraph(note_text, normal_style))

    story.append(PageBreak())

    # ===================================
    # PAGE 3: CONDUCTING THE SURVEY
    # ===================================

    story.append(Paragraph("3️⃣ Befragung durchführen (1 Schulstunde)", heading_style))

    step3_items = [
        "Zeigen Sie den QR-Code (aus diesem PDF oder aus 'qr_code.png') über Beamer/Whiteboard",
        "Alternativ: Teilen Sie den Link zur befragung.html per E-Mail/Chat",
        "Schüler scannen den QR-Code mit ihrem Smartphone",
        "Schüler füllen das Formular aus (ca. {min} Minuten)".format(min=estimated_minutes),
        "Daten erscheinen automatisch in Google Sheets Tab 'Rohdaten'",
        "Oder: Schüler laden JSON-Datei herunter und senden sie Ihnen per E-Mail"
    ]

    for item in step3_items:
        story.append(Paragraph(f"• {item}", bullet_style))

    story.append(Spacer(1, 1*cm))

    # QR Code if provided
    if qr_code_buffer:
        story.append(Paragraph("📱 QR-Code für Schüler:", heading_style))
        story.append(Spacer(1, 0.3*cm))

        qr_code_buffer.seek(0)
        img = Image(qr_code_buffer, width=8*cm, height=8*cm)
        story.append(img)
        story.append(Spacer(1, 0.5*cm))

    story.append(PageBreak())

    # ===================================
    # PAGE 4: ANALYSIS
    # ===================================

    story.append(Paragraph("4️⃣ Auswertung verstehen", heading_style))

    story.append(Paragraph("<b>Tab 'Rohdaten':</b>", normal_style))
    story.append(Paragraph("• Enthält alle originalen Schüler-Antworten", bullet_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>Tab 'Auswertung':</b>", normal_style))
    auswert_items = [
        "Zeigt für jeden Schüler den Durchschnitt aller Antworten",
        "Vergleicht mit PISA Deutschland Durchschnitt",
        "Markiert Risikoschüler (Durchschnitt < 2.0) mit ⚠️",
        "Grüne Zellen: Über PISA Durchschnitt",
        "Gelbe Zellen: Nahe PISA Durchschnitt",
        "Rote Zellen: Unter PISA Durchschnitt"
    ]
    for item in auswert_items:
        story.append(Paragraph(f"• {item}", bullet_style))

    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>Tab 'Dashboard':</b>", normal_style))
    dash_items = [
        "Klassendurchschnitt auf einen Blick",
        "Vergleich mit PISA Deutschland",
        "Anzahl Risikoschüler",
        "Visualisierungen und Charts"
    ]
    for item in dash_items:
        story.append(Paragraph(f"• {item}", bullet_style))

    story.append(Spacer(1, 1*cm))

    # ===================================
    # PAGE 5: ACTION RECOMMENDATIONS
    # ===================================

    story.append(Paragraph("5️⃣ Handlungsempfehlungen", heading_style))

    story.append(Paragraph("<b>Risikoschüler identifiziert (< 2.0)?</b>", normal_style))
    risk_items = [
        "Führen Sie Einzelgespräche",
        "Entwickeln Sie individuelle Förderpläne",
        "Erwägen Sie Peer-Tutoring Programme",
        "Kontaktieren Sie ggf. Schulpsychologie"
    ]
    for item in risk_items:
        story.append(Paragraph(f"• {item}", bullet_style))

    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>Klasse unter PISA Durchschnitt?</b>", normal_style))
    class_items = [
        "Analysieren Sie mögliche strukturelle Ursachen",
        "Implementieren Sie klassenweite Interventionen",
        "Nutzen Sie PISA-basierte Unterrichtsmaterialien",
        "Führen Sie Follow-up Befragung durch (z.B. nach 3 Monaten)"
    ]
    for item in class_items:
        story.append(Paragraph(f"• {item}", bullet_style))

    story.append(Spacer(1, 1*cm))

    # Footer
    footer_text = """
    <b>💡 Wissenschaftliche Fundierung:</b><br/>
    Diese Befragung basiert auf den validierten PISA 2022 Skalen. Die Ergebnisse sind
    direkt vergleichbar mit internationalen Standards und bieten eine evidenzbasierte
    Grundlage für pädagogische Interventionen.
    """
    story.append(Paragraph(footer_text, normal_style))

    story.append(Spacer(1, 0.5*cm))

    contact_text = """
    <b>📚 Weitere Informationen:</b><br/>
    OECD PISA Website: <b>www.oecd.org/pisa</b><br/>
    PISA 2022 Technical Report: Verfügbar auf der OECD Website
    """
    story.append(Paragraph(contact_text, normal_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)

    return buffer


def create_quick_start_guide(scale_name: str, scale_title: str) -> BytesIO:
    """
    Erstellt eine kompakte 1-Seiten Quick-Start Anleitung.

    Args:
        scale_name: Skalen-Code
        scale_title: Deutscher Titel

    Returns:
        BytesIO object mit PDF
    """

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=20)
    story.append(Paragraph(f"⚡ Quick Start: {scale_title}", title_style))
    story.append(Spacer(1, 0.5*cm))

    steps = [
        ("1", "Lade 'auswertung_template.xlsx' in Google Drive hoch"),
        ("2", "Öffne 'befragung.html' im Browser"),
        ("3", "Zeige QR-Code den Schülern"),
        ("4", "Schüler füllen Formular aus"),
        ("5", "Siehe Ergebnisse in Google Sheets")
    ]

    for num, text in steps:
        story.append(Paragraph(f"<b>{num}.</b> {text}", styles['Normal']))
        story.append(Spacer(1, 0.3*cm))

    doc.build(story)
    buffer.seek(0)

    return buffer
