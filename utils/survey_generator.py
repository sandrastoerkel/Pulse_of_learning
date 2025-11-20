"""
HTML-Formular Generator für PISA-Befragungen

Generiert mobil-optimierte HTML-Formulare basierend auf PISA-Items
mit Integration für Google Sheets.
"""

from typing import List, Dict, Optional
import pandas as pd
import numpy as np


# Mapping für häufige PISA Antwort-Skalen (EN -> DE)
ANSWER_LABEL_MAPPING = {
    # Likert 4-point agreement scale
    "Strongly agree": "Stimme völlig zu",
    "Agree": "Stimme zu",
    "Disagree": "Stimme nicht zu",
    "Strongly disagree": "Stimme überhaupt nicht zu",

    # Frequency scales
    "Never or hardly ever": "Nie oder fast nie",
    "Some lessons": "In einigen Stunden",
    "Most lessons": "In den meisten Stunden",
    "Every lesson": "In jeder Stunde",

    "Never": "Nie",
    "Rarely": "Selten",
    "Sometimes": "Manchmal",
    "Often": "Oft",
    "Always": "Immer",

    # Yes/No
    "Yes": "Ja",
    "No": "Nein",

    # Amount scales
    "None": "Keine",
    "One": "Eine",
    "Two": "Zwei",
    "Three": "Drei",
    "Four": "Vier",
    "Five or more": "Fünf oder mehr",

    # Confidence scales
    "Not at all confident": "Überhaupt nicht sicher",
    "Not very confident": "Nicht sehr sicher",
    "Confident": "Sicher",
    "Very confident": "Sehr sicher",

    # Time scales
    "Less than 1 hour": "Weniger als 1 Stunde",
    "1 to 2 hours": "1 bis 2 Stunden",
    "2 to 4 hours": "2 bis 4 Stunden",
    "4 to 6 hours": "4 bis 6 Stunden",
    "More than 6 hours": "Mehr als 6 Stunden",
}


def translate_label(english_label: str) -> str:
    """
    Übersetzt englische PISA Labels ins Deutsche.

    Args:
        english_label: Englisches Label

    Returns:
        Deutsches Label oder Original falls keine Übersetzung
    """
    if not english_label or pd.isna(english_label):
        return ""

    # Direct mapping
    if english_label in ANSWER_LABEL_MAPPING:
        return ANSWER_LABEL_MAPPING[english_label]

    # Return original if no translation
    return english_label


def is_missing_value(value: any) -> bool:
    """
    Prüft ob ein Wert ein Missing Code ist.

    Args:
        value: Der zu prüfende Wert

    Returns:
        True wenn Missing Code
    """
    if pd.isna(value):
        return True

    value_str = str(value).strip().upper()

    # Common missing patterns
    missing_patterns = [
        'SYSTEM MISSING',
        'MISSING',
        'NOT APPLICABLE',
        'VALID SKIP',
        'INVALID',
        'NO RESPONSE',
        '.V',
        '.N',
        '.I',
        '.M',
        '95',
        '96',
        '97',
        '98',
        '99'
    ]

    # Check if value starts with dot (SPSS missing codes)
    if value_str.startswith('.'):
        return True

    # Check patterns
    for pattern in missing_patterns:
        if pattern in value_str:
            return True

    return False


def generate_html_form(
    scale_name: str,
    scale_title: str,
    items: List[Dict],
    value_labels: Dict[str, pd.DataFrame],
    fragestamm: Optional[str] = None,
    google_script_url: str = ""
) -> str:
    """
    Generiert ein mobil-optimiertes HTML-Formular.

    Args:
        scale_name: Skalen-Code (z.B. "ANXMAT")
        scale_title: Deutscher Titel der Skala
        items: Liste von Items mit 'variable_name' und 'question_text_de'
        value_labels: Dictionary mit DataFrames für Antwortoptionen pro Item
        fragestamm: Gemeinsamer Einleitungstext (optional)
        google_script_url: URL zum Google Apps Script (optional)

    Returns:
        HTML string des kompletten Formulars
    """

    # CSS für mobile-first responsive design
    css_styles = """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            padding: 30px;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 24px;
        }

        h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 18px;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }

        .intro-box {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #667eea;
        }

        .fragestamm {
            font-style: italic;
            color: #555;
            margin-bottom: 20px;
            padding: 15px;
            background: #e8f4f8;
            border-radius: 6px;
        }

        .form-group {
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 2px solid #e9ecef;
        }

        .form-group:last-of-type {
            border-bottom: none;
        }

        .question-number {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .question-text {
            font-size: 16px;
            color: #333;
            margin-bottom: 15px;
            font-weight: 500;
        }

        .radio-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .radio-option {
            display: flex;
            align-items: center;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .radio-option:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }

        .radio-option input[type="radio"] {
            margin-right: 12px;
            width: 20px;
            height: 20px;
            cursor: pointer;
        }

        .radio-option label {
            cursor: pointer;
            flex: 1;
            font-size: 15px;
        }

        .student-name {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .student-name:focus {
            outline: none;
            border-color: #667eea;
        }

        .submit-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .submit-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .progress-bar {
            width: 100%;
            height: 6px;
            background: #e9ecef;
            border-radius: 3px;
            margin-bottom: 20px;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s;
        }

        .required-note {
            color: #dc3545;
            font-size: 14px;
            margin-bottom: 20px;
        }

        .thank-you {
            display: none;
            text-align: center;
            padding: 60px 20px;
        }

        .thank-you h2 {
            color: #28a745;
            font-size: 32px;
            margin-bottom: 20px;
        }

        .thank-you p {
            font-size: 18px;
            color: #666;
        }

        @media (max-width: 600px) {
            .container {
                padding: 20px;
            }

            h1 {
                font-size: 20px;
            }

            .question-text {
                font-size: 15px;
            }
        }
    </style>
    """

    # JavaScript für Formular-Handling und Google Sheets Integration
    javascript = f"""
    <script>
        let currentProgress = 0;
        const totalQuestions = {len(items)};

        // Update progress bar
        function updateProgress() {{
            const form = document.getElementById('surveyForm');
            const answeredQuestions = form.querySelectorAll('input[type="radio"]:checked').length;
            currentProgress = (answeredQuestions / totalQuestions) * 100;
            document.querySelector('.progress-fill').style.width = currentProgress + '%';

            // Enable submit button when all questions answered
            const submitBtn = document.getElementById('submitBtn');
            if (answeredQuestions === totalQuestions && form.student_name.value.trim() !== '') {{
                submitBtn.disabled = false;
            }} else {{
                submitBtn.disabled = true;
            }}
        }}

        // Add event listeners when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            const radios = document.querySelectorAll('input[type="radio"]');
            radios.forEach(radio => radio.addEventListener('change', updateProgress));

            const nameInput = document.getElementById('student_name');
            nameInput.addEventListener('input', updateProgress);
        }});

        // Submit form
        async function submitSurvey(event) {{
            event.preventDefault();

            const form = document.getElementById('surveyForm');
            const submitBtn = document.getElementById('submitBtn');

            submitBtn.disabled = true;
            submitBtn.textContent = 'Wird gesendet...';

            // Collect form data
            const formData = new FormData(form);
            const data = {{}};
            for (let [key, value] of formData.entries()) {{
                data[key] = value;
            }}

            // Add metadata
            data.timestamp = new Date().toISOString();
            data.scale_name = '{scale_name}';

            try {{
                // Option A: Google Apps Script
                if ('{google_script_url}' !== '') {{
                    const response = await fetch('{google_script_url}', {{
                        method: 'POST',
                        mode: 'no-cors',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify(data)
                    }});

                    showThankYou();
                }} else {{
                    // Fallback: Download as JSON
                    downloadAsJSON(data);
                    showThankYou();
                }}
            }} catch (error) {{
                console.error('Error:', error);
                alert('Fehler beim Senden. Daten werden heruntergeladen...');
                downloadAsJSON(data);
                showThankYou();
            }}
        }}

        function downloadAsJSON(data) {{
            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `befragung_${{data.student_name}}_${{Date.now()}}.json`;
            a.click();
        }}

        function showThankYou() {{
            document.getElementById('formContainer').style.display = 'none';
            document.getElementById('thankYou').style.display = 'block';
        }}
    </script>
    """

    # HTML Structure
    html_parts = []

    # Header
    html_parts.append(f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{scale_title} - PISA Befragung</title>
        {css_styles}
    </head>
    <body>
        <div class="container">
            <div id="formContainer">
                <h1>📊 {scale_title}</h1>
                <p class="subtitle">Basierend auf PISA 2022 Skala: {scale_name}</p>

                <div class="intro-box">
                    <p><strong>📋 Anleitung:</strong></p>
                    <p>Beantworte bitte alle Fragen ehrlich. Es gibt keine richtigen oder falschen Antworten.</p>
                    <p><strong>⏱️ Geschätzte Zeit:</strong> ca. {max(5, len(items) // 2)} Minuten</p>
                </div>
    """)

    # Fragestamm if available
    if fragestamm:
        html_parts.append(f"""
                <div class="fragestamm">
                    <strong>📝 Einleitungstext für alle folgenden Fragen:</strong><br>
                    {fragestamm}
                </div>
        """)

    # Progress bar
    html_parts.append("""
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>

                <p class="required-note">* Alle Felder sind Pflichtfelder</p>

                <form id="surveyForm" onsubmit="submitSurvey(event)">
                    <div class="form-group">
                        <label for="student_name" class="question-text">👤 Dein Name:</label>
                        <input type="text" id="student_name" name="student_name" class="student-name"
                               placeholder="Vorname Nachname" required>
                    </div>
    """)

    # Generate questions
    for idx, item in enumerate(items, 1):
        variable = item.get('variable_name', 'N/A')
        question_text = item.get('question_text_de', item.get('question_text_en', 'N/A'))

        html_parts.append(f"""
                    <div class="form-group">
                        <span class="question-number">Frage {idx} von {len(items)}</span>
                        <div class="question-text">{question_text}</div>
                        <div class="radio-group">
        """)

        # Get value labels for this item
        if variable in value_labels and len(value_labels[variable]) > 0:
            vl_df = value_labels[variable]

            for _, row in vl_df.iterrows():
                value = row['value']

                # Skip missing values
                if is_missing_value(value):
                    continue

                # Get labels
                label_de = row.get('label_de')
                label_en = row.get('label')

                # Determine final label
                if label_de and pd.notna(label_de) and str(label_de).strip() != '':
                    label = label_de
                elif label_en and pd.notna(label_en) and str(label_en).strip() != '':
                    # Try to translate English label to German
                    label = translate_label(label_en)
                else:
                    label = f"Option {value}"  # Fallback

                html_parts.append(f"""
                            <div class="radio-option">
                                <input type="radio" id="{variable}_{value}" name="{variable}"
                                       value="{value}" required>
                                <label for="{variable}_{value}">{value}. {label}</label>
                            </div>
                """)

        html_parts.append("""
                        </div>
                    </div>
        """)

    # Submit button
    html_parts.append("""
                    <button type="submit" class="submit-btn" id="submitBtn" disabled>
                        ✅ Befragung abschicken
                    </button>
                </form>
            </div>

            <div id="thankYou" class="thank-you">
                <h2>✅ Vielen Dank!</h2>
                <p>Deine Antworten wurden erfolgreich gespeichert.</p>
                <p style="margin-top: 20px;">Du kannst dieses Fenster jetzt schließen.</p>
            </div>
        </div>
    """)

    # Footer
    html_parts.append(f"""
        {javascript}
    </body>
    </html>
    """)

    return ''.join(html_parts)


def estimate_survey_duration(num_items: int) -> int:
    """
    Schätzt die Bearbeitungszeit in Minuten.

    Args:
        num_items: Anzahl der Fragen

    Returns:
        Geschätzte Minuten (aufgerundet auf 5er)
    """
    # Durchschnittlich 20 Sekunden pro Frage
    minutes = (num_items * 20) / 60

    # Aufrunden auf nächste 5
    return max(5, int((minutes + 4) // 5 * 5))
