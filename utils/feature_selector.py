"""
Feature Selector für PISA 2022 Daten
Basierend auf tatsächlich verfügbaren Skalen in der Datenbank

Update: 2025-11-03
- Alle 58 verfügbaren PISA-Skalen integriert (100% Verfügbarkeit)
- Alte nicht-verfügbare Skalen entfernt (ESCS, RESILIENCE, etc.)
- Kategorisierung nach Themen optimiert

Strategie: Data-Driven Feature Selection
- Fokus auf ALLE verfügbaren SKALEN (hohe Reliabilität)
- Nur essentielle EINZELITEMS (Demografie)
- 58 Skalen statt vorher 8
"""

# ============================================================
# ALLE 58 VERFÜGBAREN PISA-SKALEN (Stand: 2025-11-03)
# Quelle: scales_with_data_overview.csv + DB-Verifizierung
# ============================================================

ALLE_VERFUEGBAREN_SKALEN = [
    # Mathematik-spezifisch (12)
    'ANXMAT', 'COGACMCO', 'COGACRCO', 'DISCLIM',
    'EXPO21ST', 'EXPOFA', 'FAMCON', 'MATHEF21',
    'MATHEFF', 'MATHPERS', 'PQMIMP', 'TEACHSUP',

    # ICT/Digital (13)
    'ICTEFFIC', 'ICTENQ', 'ICTFEED', 'ICTHOME',
    'ICTINFO', 'ICTOUT', 'ICTQUAL', 'ICTREG',
    'ICTRES', 'ICTSCH', 'ICTSUBJ', 'ICTWKDY', 'ICTWKEND',

    # Psychologisch/Sozial (11)
    'ASSERAGR', 'BELONG', 'BULLIED', 'COOPAGR',
    'CURIOAGR', 'EMOCOAGR', 'EMPATAGR', 'GROSAGR',
    'PERSEVAGR', 'RELATST', 'STRESAGR',

    # Familie/Häuslich (8)
    'ATTIMMP', 'FAMSUP', 'FAMSUPSL', 'HOMEPOS',
    'PARINVOL', 'PASCHPOL', 'PQSCHOOL', 'FEELLAH',

    # Kreativität (11)
    'CREATACT', 'CREATAS', 'CREATEFF', 'CREATFAM',
    'CREATHME', 'CREATOOS', 'CREATOP', 'CREATOPN',
    'CREATOR', 'CREATSCH', 'OPENART',

    # Selbstgesteuertes Lernen & Schule (3)
    'PROBSELF', 'SCHSUST', 'SDLEFF'
]

# Kategorisiert für spätere Analyse und fachspezifische Modelle
FEATURE_CATEGORIES = {
    'math_specific': [
        'ANXMAT', 'COGACMCO', 'COGACRCO', 'DISCLIM',
        'EXPO21ST', 'EXPOFA', 'FAMCON', 'MATHEF21',
        'MATHEFF', 'MATHPERS', 'PQMIMP', 'TEACHSUP'
    ],
    'ict_digital': [
        'ICTEFFIC', 'ICTENQ', 'ICTFEED', 'ICTHOME',
        'ICTINFO', 'ICTOUT', 'ICTQUAL', 'ICTREG',
        'ICTRES', 'ICTSCH', 'ICTSUBJ', 'ICTWKDY', 'ICTWKEND'
    ],
    'psychological_social': [
        'ASSERAGR', 'BELONG', 'BULLIED', 'COOPAGR',
        'CURIOAGR', 'EMOCOAGR', 'EMPATAGR', 'GROSAGR',
        'PERSEVAGR', 'RELATST', 'STRESAGR'
    ],
    'family_home': [
        'ATTIMMP', 'FAMSUP', 'FAMSUPSL', 'HOMEPOS',
        'PARINVOL', 'PASCHPOL', 'PQSCHOOL', 'FEELLAH'
    ],
    'creativity': [
        'CREATACT', 'CREATAS', 'CREATEFF', 'CREATFAM',
        'CREATHME', 'CREATOOS', 'CREATOP', 'CREATOPN',
        'CREATOR', 'CREATSCH', 'OPENART'
    ],
    'self_directed_learning': ['PROBSELF', 'SCHSUST', 'SDLEFF']
}


class PISAFeatureSelector:
    """
    Feature Selection für PISA 2022 Deutschland-Datenbank

    Update 2025-11-03:
    - Alle 58 verfügbaren Skalen integriert
    - 100% Verfügbarkeit in der Datenbank
    - Optimiert für Multi-Fach-Analysen (Math, Read, Science)

    Referenz:
    - Chinesische Forscher (2024): 151 → 15 Features
    - Unsere Basis: 58 verfügbare → 40-50 Features (nach ML-Selektion)
    """

    def __init__(self):
        """Definiere Feature-Gruppen basierend auf verfügbaren PISA-Skalen"""

        # ============================================================
        # HAUPTFOKUS: Alle 58 verfügbaren PISA-SKALEN
        # (IRT-skaliert, hohe Reliabilität, 100% in DB vorhanden)
        # ============================================================

        # Mathematik-spezifische Skalen (12)
        self.math_scales = [
            'MATHEFF',      # Mathematics Self-Efficacy ⭐ TOP FAKTOR!
            'ANXMAT',       # Mathematics Anxiety ⭐ #2 FAKTOR
            'TEACHSUP',     # Mathematics Teacher Support
            'COGACMCO',     # Cognitive activation: math thinking
            'COGACRCO',     # Cognitive activation: math reasoning
            'DISCLIM',      # Disciplinary climate in mathematics
            'MATHPERS',     # Math effort and persistence
            'MATHEF21',     # Math self-efficacy: 21st century
            'EXPO21ST',     # Exposure to math reasoning
            'EXPOFA',       # Exposure to formal/applied math
            'FAMCON',       # Familiarity with math concepts
            'PQMIMP',       # Parent attitudes toward math
        ]

        # Psychologische & soziale Skalen (11) - GENERISCH für alle Fächer
        self.psychological_scales = [
            'BELONG',       # Sense of Belonging ⭐ WICHTIG
            'PERSEVAGR',    # Perseverance ⭐ WICHTIG
            'GROSAGR',      # Growth Mindset ⭐ WICHTIG
            'CURIOAGR',     # Curiosity
            'STRESAGR',     # Stress resistance
            'EMOCOAGR',     # Emotional control
            'EMPATAGR',     # Empathy
            'ASSERAGR',     # Assertiveness
            'COOPAGR',      # Cooperation
            'BULLIED',      # Being bullied (negativ)
            'RELATST',      # Student-teacher relationships
        ]

        # Familie & häusliches Umfeld (8) - GENERISCH
        self.family_home_scales = [
            'HOMEPOS',      # Home possessions (SES Proxy) ⭐ WICHTIG
            'FAMSUP',       # Family support
            'FAMSUPSL',     # Family support self-directed learning
            'PARINVOL',     # Parental Involvement
            'PASCHPOL',     # School policies for parental involvement
            'PQSCHOOL',     # School quality
            'ATTIMMP',      # Parents' attitudes toward immigrants
            'FEELLAH',      # Feelings about learning at home
        ]

        # ICT & Digital (13) - GENERISCH, wichtig für alle Fächer
        self.ict_scales = [
            'ICTEFFIC',     # Self-efficacy in digital competencies
            'ICTRES',       # ICT Resources
            'ICTHOME',      # ICT availability outside school
            'ICTSCH',       # ICT availability at school
            'ICTSUBJ',      # Subject-related ICT during lessons
            'ICTWKDY',      # ICT frequency weekday
            'ICTWKEND',     # ICT frequency weekend
            'ICTENQ',       # ICT in enquiry-based learning
            'ICTFEED',      # Support/feedback via ICT
            'ICTINFO',      # Online information practices
            'ICTOUT',       # ICT for school outside classroom
            'ICTQUAL',      # Quality of ICT access
            'ICTREG',       # Views on regulated ICT use
        ]

        # Kreativität (11) - GENERISCH, besonders relevant für Science & Reading
        self.creativity_scales = [
            'CREATEFF',     # Creative self-efficacy ⭐
            'CREATOP',      # Creativity and Openness ⭐
            'CREATAS',      # Creative Activities at school
            'CREATSCH',     # Creative school/class environment
            'CREATFAM',     # Creative peers/family environment
            'CREATOOS',     # Creative Activities outside school
            'CREATOPN',     # Creativity and Openness (alt)
            'OPENART',      # Openness to Art and Reflection
            'CREATOR',      # Openness to creativity: Other's report
            'CREATHME',     # Creative Home Environment
            'CREATACT',     # Creative activities outside school
        ]

        # Selbstgesteuertes Lernen & Schule (3) - GENERISCH
        self.learning_scales = [
            'SDLEFF',       # Self-directed learning efficacy
            'PROBSELF',     # Problems with self-directed learning
            'SCHSUST',      # School activities to sustain learning
        ]

        # ============================================================
        # EINZELITEMS: ENTFERNT FÜR WISSENSCHAFTLICHE PUBLIKATION
        # ============================================================

        # Demografische Items wurden entfernt (ST001D01T, ST004D01T)
        # Grund: Nicht validierte PISA-Skalen, können Ergebnisse verfälschen
        # Grade-Level (ST001D01T) war Top Feature - aber kein echtes Konstrukt

        self.demographic_items = []

        # SC001Q01TA und SC013Q01TA sind nicht in DB verfügbar
        self.school_context_items = []

        # ============================================================
        # AUSSCHLUSS: Administrative & ID-Variablen
        # ============================================================

        self.exclude_patterns = [
            'CNTSTUID',     # Student ID
            'CNTSCHID',     # School ID
            'CNT',          # Country Code
            'CNTRYID',      # Country ID
            'STRATUM',      # Stratum
            'SUBNATIO',     # Subnational Region
            'OECD',         # OECD Member
            'ADMINMODE',    # Administration Mode
            'LANGTEST_QQQ', # Test Language
            'BOOKID',       # Booklet ID
            'CLCUSE',       # Calculator Use
        ]

        # Auch Plausible Values ausschließen (außer Ziel-Variable)
        self.exclude_pv_patterns = [
            'PV1MATH', 'PV2MATH', 'PV3MATH', 'PV4MATH', 'PV5MATH',
            'PV6MATH', 'PV7MATH', 'PV8MATH', 'PV9MATH', 'PV10MATH',
            'PV1READ', 'PV2READ', 'PV3READ', 'PV4READ', 'PV5READ',
            'PV6READ', 'PV7READ', 'PV8READ', 'PV9READ', 'PV10READ',
            'PV1SCIE', 'PV2SCIE', 'PV3SCIE', 'PV4SCIE', 'PV5SCIE',
            'PV6SCIE', 'PV7SCIE', 'PV8SCIE', 'PV9SCIE', 'PV10SCIE',
        ]

        # ============================================================
        # BACKWARD COMPATIBILITY: Aliase für alte Streamlit-App
        # ============================================================

        # socioeconomic_scales war früher separat, jetzt in family_home_scales
        self.socioeconomic_scales = self.family_home_scales

        # teacher_school_scales: Kombination aus TEACHSUP und DISCLIM
        self.teacher_school_scales = [
            'TEACHSUP',  # Mathematics Teacher Support
            'DISCLIM',   # Disciplinary climate in mathematics
        ]

    def get_all_features(self, target_var='PV1MATH', include_reading=None):
        """
        Gibt Features zurück abhängig von der Zielvariable

        Args:
            target_var: Ziel-Variable (PV1MATH, PV1READ, PV1SCIE)
            include_reading: DEPRECATED - nur für Backward-Compatibility
                           Wenn True, wird target_var='PV1READ' verwendet

        Returns:
            list: Liste aller Feature-Namen
        """
        # Backward-Compatibility: include_reading Parameter
        if include_reading is not None:
            if include_reading:
                target_var = 'PV1READ'
            else:
                target_var = 'PV1MATH'

        features = []

        # Mathematik-spezifische Skalen NUR für PV1MATH
        if 'MATH' in target_var:
            features.extend(self.math_scales)

        # Generische Skalen für ALLE Fächer
        features.extend(self.psychological_scales)
        features.extend(self.family_home_scales)
        features.extend(self.ict_scales)
        features.extend(self.creativity_scales)
        features.extend(self.learning_scales)

        # Einzelitems
        features.extend(self.demographic_items)
        features.extend(self.school_context_items)

        return features

    def select_features(self, df, target_var='PV1MATH'):
        """
        Wählt Features aus DataFrame aus

        Args:
            df: DataFrame mit allen PISA-Variablen
            target_var: Ziel-Variable (PV1MATH, PV1READ, PV1SCIE)

        Returns:
            tuple: (X, y, selected_feature_names, selection_report)
        """
        # Alle gewünschten Features
        desired_features = self.get_all_features(target_var=target_var)

        # Prüfe welche Features tatsächlich vorhanden sind
        available_features = []
        missing_features = []

        for feature in desired_features:
            if feature in df.columns:
                available_features.append(feature)
            else:
                missing_features.append(feature)

        # Erstelle Selection Report
        selection_report = {
            'total_desired': len(desired_features),
            'available': len(available_features),
            'missing': len(missing_features),
            'available_features': available_features,
            'missing_features': missing_features,
            'breakdown': {
                'math_scales': sum(1 for f in self.math_scales if f in available_features) if 'MATH' in target_var else 0,
                'psychological_scales': sum(1 for f in self.psychological_scales if f in available_features),
                'family_home_scales': sum(1 for f in self.family_home_scales if f in available_features),
                'ict_scales': sum(1 for f in self.ict_scales if f in available_features),
                'creativity_scales': sum(1 for f in self.creativity_scales if f in available_features),
                'learning_scales': sum(1 for f in self.learning_scales if f in available_features),
                'demographic_items': sum(1 for f in self.demographic_items if f in available_features),
                'school_context_items': sum(1 for f in self.school_context_items if f in available_features),
                # Backward-Compatibility: Alte Keys für Streamlit-App
                'socioeconomic_scales': sum(1 for f in self.socioeconomic_scales if f in available_features),
                'teacher_school_scales': sum(1 for f in self.teacher_school_scales if f in available_features),
            }
        }

        # Extrahiere X und y
        X = df[available_features].copy()
        y = df[target_var].copy()

        return X, y, available_features, selection_report

    def get_feature_groups_display(self):
        """
        Gibt Feature-Gruppen für UI-Anzeige zurück

        Returns:
            dict: Feature-Gruppen mit Emojis und Beschreibungen
        """
        return {
            "📐 Mathematik-Skalen (12)": {
                'features': self.math_scales,
                'description': 'Math-Selbstwirksamkeit, Angst, Unterricht, Exposition',
                'research_note': 'MATHEFF (#1) & ANXMAT (#2) sind TOP-Faktoren'
            },
            "💪 Psychologisch/Sozial (11)": {
                'features': self.psychological_scales,
                'description': 'Zugehörigkeit, Durchhaltevermögen, Growth Mindset, Neugier',
                'research_note': 'Generisch für alle Fächer - BELONG, PERSEVAGR, GROSAGR sind key!'
            },
            "🏠 Familie & Häuslich (8)": {
                'features': self.family_home_scales,
                'description': 'SES (HOMEPOS), Familienunterstützung, elterliche Beteiligung',
                'research_note': 'HOMEPOS als Proxy für sozioökonomischen Status'
            },
            "💻 ICT & Digital (13)": {
                'features': self.ict_scales,
                'description': 'Digitale Kompetenzen, ICT-Nutzung, Ressourcen',
                'research_note': 'Wichtig für alle modernen Lernprozesse'
            },
            "🎨 Kreativität (11)": {
                'features': self.creativity_scales,
                'description': 'Kreative Selbstwirksamkeit, Offenheit, Aktivitäten',
                'research_note': 'Besonders relevant für Naturwissenschaften & Lesen'
            },
            "📚 Selbstgest. Lernen (3)": {
                'features': self.learning_scales,
                'description': 'Selbstwirksamkeit, Probleme, Schulaktivitäten',
                'research_note': 'Wichtig für eigenständiges Lernen'
            },
            "👤 Demografische Items (2)": {
                'features': self.demographic_items,
                'description': 'Geschlecht, Klassenstufe',
                'research_note': 'Essentielle Kontrollvariablen'
            },
            "🏫 Schulkontext Items (2)": {
                'features': self.school_context_items,
                'description': 'Schulstandort, Schultyp',
                'research_note': 'Strukturelle Faktoren'
            },
        }

    def validate_against_research(self, selected_features):
        """
        Validiert Feature-Selection gegen Forscher-Standards

        Args:
            selected_features: Liste der ausgewählten Features

        Returns:
            dict: Validierungsergebnis
        """
        validation = {
            'checks': [],
            'score': 0,
            'max_score': 5,
        }

        # Check 1: MATHEFF vorhanden?
        if 'MATHEFF' in selected_features:
            validation['checks'].append({
                'name': 'MATHEFF (Top Faktor)',
                'status': '✅',
                'note': 'Wichtigster Faktor laut Forschung (16.17%)'
            })
            validation['score'] += 1
        else:
            validation['checks'].append({
                'name': 'MATHEFF (Top Faktor)',
                'status': '⚠️',
                'note': 'Nur für Mathematik relevant'
            })

        # Check 2: ANXMAT vorhanden?
        if 'ANXMAT' in selected_features:
            validation['checks'].append({
                'name': 'ANXMAT (Angst)',
                'status': '✅',
                'note': 'Zweitwichtigster Faktor für Mathematik'
            })
            validation['score'] += 1
        else:
            validation['checks'].append({
                'name': 'ANXMAT (Angst)',
                'status': '⚠️',
                'note': 'Nur für Mathematik relevant'
            })

        # Check 3: HOMEPOS vorhanden? (Ersatz für ESCS)
        if 'HOMEPOS' in selected_features:
            validation['checks'].append({
                'name': 'HOMEPOS (SES Proxy)',
                'status': '✅',
                'note': 'Proxy für sozioökonomischen Status (ESCS nicht verfügbar)'
            })
            validation['score'] += 1
        else:
            validation['checks'].append({
                'name': 'HOMEPOS (SES Proxy)',
                'status': '❌',
                'note': 'FEHLT! Essentielle Kontrollvariable.'
            })

        # Check 4: Mindestens 40 Features?
        if len(selected_features) >= 40:
            validation['checks'].append({
                'name': 'Feature-Anzahl (40-60)',
                'status': '✅',
                'note': f'{len(selected_features)} Features (optimal mit 58 verfügbaren)'
            })
            validation['score'] += 1
        elif len(selected_features) >= 30:
            validation['checks'].append({
                'name': 'Feature-Anzahl (40-60)',
                'status': '⚠️',
                'note': f'{len(selected_features)} Features (akzeptabel, könnte mehr sein)'
            })
            validation['score'] += 0.5
        else:
            validation['checks'].append({
                'name': 'Feature-Anzahl (40-60)',
                'status': '❌',
                'note': f'{len(selected_features)} Features (zu wenig - nutze mehr der 58 verfügbaren!)'
            })

        # Check 5: Überwiegend Skalen (nicht Einzelitems)?
        scales = [f for f in selected_features if f not in self.demographic_items + self.school_context_items]
        scale_ratio = len(scales) / len(selected_features) if selected_features else 0

        if scale_ratio >= 0.90:
            validation['checks'].append({
                'name': 'Skalen-Fokus (>90%)',
                'status': '✅',
                'note': f'{scale_ratio*100:.1f}% Skalen (exzellent!)'
            })
            validation['score'] += 1
        elif scale_ratio >= 0.85:
            validation['checks'].append({
                'name': 'Skalen-Fokus (>90%)',
                'status': '⚠️',
                'note': f'{scale_ratio*100:.1f}% Skalen (gut)'
            })
            validation['score'] += 0.5
        else:
            validation['checks'].append({
                'name': 'Skalen-Fokus (>90%)',
                'status': '❌',
                'note': f'{scale_ratio*100:.1f}% Skalen (zu viele Einzelitems!)'
            })

        return validation


# Convenience Functions
def get_recommended_features(target_var='PV1MATH'):
    """
    Quick Access: Gibt empfohlene Features zurück

    Args:
        target_var: Ziel-Variable (PV1MATH, PV1READ, PV1SCIE)

    Returns:
        list: Feature-Namen
    """
    selector = PISAFeatureSelector()
    return selector.get_all_features(target_var=target_var)


def select_features_from_df(df, target_var='PV1MATH'):
    """
    Quick Access: Feature Selection aus DataFrame

    Args:
        df: DataFrame mit PISA-Daten
        target_var: Ziel-Variable

    Returns:
        tuple: (X, y, feature_names, report)
    """
    selector = PISAFeatureSelector()
    return selector.select_features(df, target_var=target_var)


# Export für direkten Import
__all__ = [
    'PISAFeatureSelector',
    'get_recommended_features',
    'select_features_from_df',
    'ALLE_VERFUEGBAREN_SKALEN',
    'FEATURE_CATEGORIES'
]
