# Pulse of Learning - PISA 2022 Explorer

Eine interaktive Streamlit-App zur Analyse von PISA 2022 Daten für Deutschland mit Fokus auf Mathematikleistung, Selbstwirksamkeit und Mathematikangst.

## Überblick

Diese App ermöglicht:
- 📊 **Explorative Datenanalyse** der PISA 2022 Deutschland-Daten
- 🔍 **Skalen-Explorer** mit 110 PISA-Skalen (39 mit vollständigen Items)
- 📝 **Einzelfragen-Ansicht** mit Original-Fragetexten aus dem PISA Skalenhandbuch
- 📈 **Tiefenanalyse** mit Korrelationen und Gruppenvergleichen
- 🔬 **Machine Learning Pipeline** mit SHAP-Analysen
- 📋 **Ergebnisübersichten** und Handlungsempfehlungen
- 📖 **Storytelling Dashboard** für evidenzbasierte Erkenntnisse

## Features

### Phase 1: Top 15 Features
Identifikation der wichtigsten Einflussfaktoren auf Mathematikleistung mittels Machine Learning.

### Phase 2: Skalen-Explorer
Durchsuche 110 PISA-Skalen nach Kategorien:
- Mathematik-bezogene Skalen
- Sozial-emotionale Kompetenzen
- Kreativität
- ICT/Digitale Kompetenzen
- Lehrkräfte und Unterricht
- u.v.m.

### Phase 3: Einzelfragen verstehen
- **39 Skalen mit Items**: Vollständige Fragetexte aus PISA 2022 Skalenhandbuch
- **71 berechnete Indizes**: Dokumentation mit Berechnungshinweisen
- **Fragebogen-Export**: Test-Templates für eigene Schüler

### Phase 4: Tiefenanalyse
- Korrelationsanalysen
- Gruppenvergleiche (Geschlecht, Schultyp, etc.)
- Verteilungsanalysen

### Phase 5: ML Pipeline
- Feature Importance
- SHAP Value Analysen
- Interaktive ML-Modelle

### Phase 6: Ergebnisübersicht
- Professionelle Berichte
- Evidenzbasierte Handlungsempfehlungen

### Phase 7: Storytelling Dashboard
- Narrative Datenvisualisierung
- Erkenntnisse kommunizieren

## Datengrundlage

### PISA 2022 Deutschland
- **Schüler**: 6,116
- **Variablen**: 1,200+
- **WLE-Skalen**: 110
  - 39 mit vollständigen Items (398 Einzelfragen)
  - 71 berechnete Indizes

### Datenquellen
1. **pisa_2022_germany.db**: Vollständige Produktionsdatenbank
2. **pisa_2022_germany_sample100.db**: Test-/Entwicklungsdatenbank
3. **PISA 2022 Skalenhandbuch**: Offizielle Dokumentation
   - Quelle: `/Users/sandra/Documents/Pulse_of_learning/wichtige_allgemeine_infos/Skaleninformation_Features/wichtig!!!Skaleninfos/`
   - `pisa_skalen.json`: 39 Skalen mit Items
   - `pisa_indizes_erweitert.json`: 71 Indizes mit Berechnungshinweisen

## Installation

### Voraussetzungen
- Python 3.9+
- venv (virtuelle Umgebung)

### Setup

1. **Repository klonen / Verzeichnis öffnen**
```bash
cd "/Users/sandra/Documents/Pulse_of_learning/pulse_of_learning_hauptapp"
```

2. **Virtuelle Umgebung aktivieren**
```bash
source venv/bin/activate
```

3. **Abhängigkeiten installieren** (falls noch nicht geschehen)
```bash
pip install -r requirements.txt
```

4. **App starten**
```bash
streamlit run Home.py
```

Die App läuft dann unter: http://localhost:8501

## Projektstruktur

```
.
├── Home.py                      # Hauptseite
├── pages/                       # Streamlit Multi-Page App
│   ├── 1_📊_Top_Features.py
│   ├── 2_🔍_Skalen_Explorer.py
│   ├── 3_📝_Einzelfragen.py
│   ├── 4_📊_Tiefenanalyse.py
│   ├── 5_🔬_ML_Pipeline.py
│   ├── 6_📋_Ergebnisübersicht.py
│   └── 7_📖_Storytelling_Dashboard.py
├── utils/                       # Utility-Module
│   ├── db_loader.py            # Datenbankzugriff
│   ├── scale_info.py           # Skalen-Metadaten
│   ├── json_item_loader.py     # JSON Items Loader
│   ├── feature_descriptions.py
│   ├── feature_selector.py
│   ├── statistical_analysis.py
│   ├── visualization_helpers.py
│   ├── data_filters.py
│   └── storytelling_helpers.py
├── data/
│   └── feature_names.txt
├── pisa_2022_germany.db        # Hauptdatenbank
├── pisa_2022_germany_sample100.db  # Test-DB
├── requirements.txt
├── README.md
└── AUFRAEUM_PLAN.md           # Dokumentation des Aufräumens

Archiv-Ordner:
└── Dokumentationsdateien_Datenbank/  # DB-Aufbau Dokumentation
```

## Verwendung

### Quick Start

1. **App starten**
2. Gehe zu **Phase 1: Top 15 Features**
3. Wähle eine interessante Skala (z.B. MATHEFF)
4. Navigiere zu **Phase 3: Einzelfragen** um die Fragetexte zu sehen
5. Lade ein Test-Template für deine Schüler herunter

### Für Forscher

1. **Phase 4**: Tiefenanalyse für Korrelationen und Gruppenvergleiche
2. **Phase 5**: ML Pipeline für SHAP-Analysen
3. **Phase 6**: Professionelle Berichte erstellen
4. **Phase 7**: Erkenntnisse kommunizieren

## Wichtige Skalen

### Mathematik-bezogen
- **MATHEFF**: Mathematikbezogene Selbstwirksamkeitserwartung (9 Items)
- **ANXMAT**: Mathematikbezogene Ängstlichkeit (6 Items)
- **MATHPERS**: Proaktives Lernverhalten in Mathematik (18 Items)
- **TEACHSUP**: Unterstützung durch Lehrkraft (4 Items)
- **DISCLIM**: Disziplin im Klassenzimmer (7 Items)

### Sozial-emotional
- **BELONG**: Gefühl der Zugehörigkeit (6 Items)
- **RELATST**: Beziehung zu Lehrkräften (7 Items)
- **PERSEVAGR**: Ausdauer (9 Items)
- **STRESAGR**: Stressresistenz (10 Items)

### Kreativität
- **CREATEFF**: Selbstwirksamkeit Kreativität (9 Items)
- **CREATSCH**: Kreatives Schulklima (6 Items)

## Technische Details

### Abhängigkeiten
- streamlit >= 1.28.0
- pandas
- numpy
- matplotlib >= 3.5.0
- seaborn
- scikit-learn
- plotly
- openpyxl

### Datenbankschema
- **student_data**: Schülerdaten mit allen Variablen
- **codebook**: Variable Metadaten
- **question_text**: Original-Fragetexte
- **value_labels**: Antwortkategorien

## Updates & Änderungen

### Version 2.0 (2025-11-10)
- ✅ Integration von 110 PISA-Skalen
- ✅ 39 Skalen mit vollständigen Items (398 Einzelfragen)
- ✅ 71 Indizes mit Berechnungshinweisen
- ✅ JSON-basierter Item-Loader
- ✅ Code-Aufräumung (von 65 auf 25 Dateien)
- ✅ Verbesserte Dokumentation

### Version 1.0
- Initiale Version mit 7 Phasen
- ML Pipeline mit SHAP
- Grundlegende Skalen-Explorer

## Lizenz

Basierend auf PISA 2022 Daten - siehe OECD Lizenzbestimmungen.

Skalenhandbuch: CC BY-SA 4.0 International

## Kontakt & Support

Bei Fragen zur App oder den Daten:
- PISA 2022 Technical Report: https://www.oecd.org/pisa/
- Skalenhandbuch: Waxmann 2025

## Acknowledgments

- PISA 2022 Deutschland-Daten (OECD)
- PISA 2022 Skalenhandbuch - Dokumentation der Erhebungsinstrumente
- Streamlit Framework
