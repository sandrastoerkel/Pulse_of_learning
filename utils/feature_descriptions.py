"""
Feature Descriptions for PISA 2022 Scales

This module contains descriptions for all 48 PISA scales used in the model.
Descriptions are extracted from pisa_scales_documentation.json

Source: data/skalen_infos/pisa_scales_documentation.json
"""

# Feature descriptions: {CODE: (English Description, German Description)}
FEATURE_DESCRIPTIONS = {
    # Mathematics-related scales
    'MATHEFF': ('Mathematics self-efficacy', 'Mathematische Selbstwirksamkeit'),
    'ANXMAT': ('Mathematics anxiety', 'Mathematikangst'),
    'TEACHSUP': ('Mathematics teacher support', 'Lehrerunterstützung'),
    'COGACMCO': ('Cognitive activation: Encourage mathematical thinking', 'Kognitive Aktivierung: Mathematisches Denken fördern'),
    'COGACRCO': ('Cognitive activation: Foster reasoning', 'Kognitive Aktivierung: Argumentieren fördern'),
    'DISCLIM': ('Disciplinary climate in mathematics', 'Disziplin im Unterricht'),
    'MATHPERS': ('Effort and persistence in mathematics', 'Anstrengung und Ausdauer in Mathematik'),
    'MATHEF21': ('Math self-efficacy: reasoning and 21st century skills', 'Mathematik-Selbstwirksamkeit: Argumentieren und 21. Jahrhundert Kompetenzen'),
    'EXPO21ST': ('Exposure to mathematical reasoning and 21st century tasks', 'Kontakt mit mathematischem Argumentieren und 21. Jahrhundert Aufgaben'),
    'EXPOFA': ('Exposure to formal and applied mathematics tasks', 'Kontakt mit formalen und angewandten Mathematikaufgaben'),
    'FAMCON': ('Subjective familiarity with mathematics concepts', 'Subjektive Vertrautheit mit Mathematikkonzepten'),

    # Well-being and psychosocial factors
    'BELONG': ('Sense of belonging', 'Zugehörigkeitsgefühl'),
    'BULLIED': ('Being bullied', 'Mobbing-Erfahrungen'),

    # Personality traits and attitudes
    'PERSEVAGR': ('Perseverance', 'Ausdauer'),
    'GROSAGR': ('Growth mindset', 'Wachstumsorientierte Denkweise'),
    'CURIOAGR': ('Curiosity', 'Neugier'),
    'STRESAGR': ('Stress resistance', 'Stressresistenz'),
    'EMOCOAGR': ('Emotional control', 'Emotionale Kontrolle'),
    'EMPATAGR': ('Empathy', 'Empathie'),
    'ASSERAGR': ('Assertiveness', 'Durchsetzungsvermögen'),
    'COOPAGR': ('Cooperation', 'Kooperation'),

    # Teacher-student relationship
    'RELATST': ('Teacher-student relationship quality', 'Qualität der Lehrer-Schüler-Beziehung'),

    # Family and home environment
    'HOMEPOS': ('Home possessions (socioeconomic status)', 'Häusliche Ausstattung (sozioökonomischer Status)'),
    'FAMSUP': ('Family support', 'Familienunterstützung'),
    'FAMSUPSL': ('Family support for self-directed learning', 'Familienunterstützung für selbstgesteuertes Lernen'),

    # Digital competencies and ICT
    'ICTEFFIC': ('Self-efficacy in digital competencies', 'Selbstwirksamkeit in digitalen Kompetenzen'),
    'ICTRES': ('ICT resources', 'ICT-Ressourcen'),
    'ICTHOME': ('ICT availability outside of school', 'ICT-Verfügbarkeit außerhalb der Schule'),
    'ICTSCH': ('ICT availability at school', 'ICT-Verfügbarkeit in der Schule'),
    'ICTSUBJ': ('Subject-related ICT use during lessons', 'Fachbezogene ICT-Nutzung im Unterricht'),
    'ICTWKDY': ('Frequency of ICT activity (weekday)', 'Häufigkeit der ICT-Nutzung (Wochentag)'),
    'ICTWKEND': ('Frequency of ICT activity (weekend)', 'Häufigkeit der ICT-Nutzung (Wochenende)'),
    'ICTENQ': ('ICT use in inquiry-based learning', 'ICT-Nutzung beim forschenden Lernen'),
    'ICTFEED': ('ICT-based feedback and support', 'ICT-basiertes Feedback und Unterstützung'),
    'ICTINFO': ('Practices regarding online information', 'Praktiken zum Umgang mit Online-Informationen'),
    'ICTOUT': ('ICT for school work outside classroom', 'ICT für Schularbeiten außerhalb des Unterrichts'),
    'ICTQUAL': ('Quality of access to ICT', 'Qualität des ICT-Zugangs'),
    'ICTREG': ('Views on regulated ICT use', 'Ansichten zu regulierter ICT-Nutzung'),

    # Creativity
    'CREATEFF': ('Creative self-efficacy', 'Kreative Selbstwirksamkeit'),
    'CREATOP': ('Creativity and intellectual openness', 'Kreativität und intellektuelle Offenheit'),
    'CREATAS': ('Creative activities at school', 'Kreative Aktivitäten in der Schule'),
    'CREATSCH': ('Creative school and class environment', 'Kreatives Schul- und Klassenumfeld'),
    'CREATFAM': ('Creative peers and family environment', 'Kreatives Umfeld bei Gleichaltrigen und Familie'),
    'CREATOOS': ('Creative activities outside of school', 'Kreative Aktivitäten außerhalb der Schule'),
    'OPENART': ('Openness to art and reflection', 'Offenheit für Kunst und Reflexion'),

    # Self-directed learning
    'SDLEFF': ('Self-directed learning efficacy', 'Selbstgesteuertes Lernen Selbstwirksamkeit'),
    'PROBSELF': ('Problems with self-directed learning', 'Probleme beim selbstgesteuerten Lernen'),

    # School support
    'SCHSUST': ('School support for sustained learning', 'Schulische Unterstützung für nachhaltiges Lernen'),
}


def get_feature_label(feature_code, language='en', include_code=True):
    """
    Get the feature label in the specified language.

    Args:
        feature_code: The PISA feature code (e.g., 'MATHEFF')
        language: 'en' for English, 'de' for German
        include_code: If True, prepends the feature code to the label

    Returns:
        Formatted feature label

    Example:
        >>> get_feature_label('MATHEFF', 'en', True)
        'MATHEFF - Mathematics self-efficacy'
        >>> get_feature_label('MATHEFF', 'de', False)
        'Mathematische Selbstwirksamkeit'
    """
    if feature_code not in FEATURE_DESCRIPTIONS:
        return feature_code

    en_desc, de_desc = FEATURE_DESCRIPTIONS[feature_code]

    if language == 'de':
        label = de_desc
    else:
        label = en_desc

    if include_code:
        return f"{feature_code} - {label}"
    else:
        return label


def get_feature_description_bilingual(feature_code):
    """
    Get bilingual feature description.

    Args:
        feature_code: The PISA feature code

    Returns:
        String with format: "English Description (German Description)"

    Example:
        >>> get_feature_description_bilingual('MATHEFF')
        'Mathematics self-efficacy (Mathematische Selbstwirksamkeit)'
    """
    if feature_code not in FEATURE_DESCRIPTIONS:
        return feature_code

    en_desc, de_desc = FEATURE_DESCRIPTIONS[feature_code]
    return f"{en_desc} ({de_desc})"


def get_all_features_with_descriptions(language='en'):
    """
    Get all features with their descriptions.

    Args:
        language: 'en' or 'de'

    Returns:
        Dictionary mapping feature codes to descriptions
    """
    if language == 'de':
        return {code: desc[1] for code, desc in FEATURE_DESCRIPTIONS.items()}
    else:
        return {code: desc[0] for code, desc in FEATURE_DESCRIPTIONS.items()}


def format_feature_for_display(feature_code, importance_pct=None):
    """
    Format feature for display with description and optional importance.

    Args:
        feature_code: The PISA feature code
        importance_pct: Optional importance percentage

    Returns:
        Formatted string for display

    Example:
        >>> format_feature_for_display('MATHEFF', 18.1)
        'MATHEFF (18.1%) - Mathematics self-efficacy (Mathematische Selbstwirksamkeit)'
    """
    bilingual_desc = get_feature_description_bilingual(feature_code)

    if importance_pct is not None:
        return f"{feature_code} ({importance_pct:.1f}%) - {bilingual_desc}"
    else:
        return f"{feature_code} - {bilingual_desc}"
