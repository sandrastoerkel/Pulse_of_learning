"""
Information about the 58 available PISA 2022 WLE scales
Grouped by construct for easy navigation
"""

# Scale categories based on VERFÜGBARKEIT_ZUSAMMENFASSUNG.md
SCALE_CATEGORIES = {
    "Affektive & Lernfaktoren": {
        "description": "Selbstwirksamkeit, Angst, Unterstützung und kognitive Aktivierung",
        "scales": [
            "ANXMAT",      # Mathematics Anxiety
            "MATHEFF",     # Mathematics self-efficacy
            "MATHEF21",    # Math self-efficacy: 21st century
            "MATHPERS",    # Effort and Persistence in Math
            "TEACHSUP",    # Teacher Support
            "DISCLIM",     # Disciplinary climate
            "COGACMCO",    # Cognitive activation: Math thinking
            "COGACRCO",    # Cognitive activation: Reasoning
            "RELATST",     # Student-teacher relationships
            "EXPOFA",      # Exposure to Formal/Applied Math
            "EXPO21ST",    # Exposure to 21st century math
            "FAMCON",      # Familiarity with math concepts
        ]
    },
    "Wohlbefinden & Soziales": {
        "description": "Soziale Integration und emotionales Wohlbefinden",
        "scales": [
            "BELONG",      # Sense of belonging
            "BULLIED",     # Being bullied
            "FAMSUP",      # Family support
        ]
    },
    "Persönlichkeit & Charakter": {
        "description": "Big Five Persönlichkeitsmerkmale (agreement scales)",
        "scales": [
            "GROSAGR",     # Growth Mindset
            "PERSEVAGR",   # Perseverance
            "CURIOAGR",    # Curiosity
            "COOPAGR",     # Cooperation
            "EMPATAGR",    # Empathy
            "ASSERAGR",    # Assertiveness
            "STRESAGR",    # Stress resistance
            "EMOCOAGR",    # Emotional control
        ]
    },
    "Kreativität": {
        "description": "Kreativität und kreatives Umfeld",
        "scales": [
            "CREATEFF",    # Creative self-efficacy
            "CREATOPN",    # Creativity and Openness
            "CREATOR",     # Openness to creativity
            "CREATSCH",    # Creative school environment
            "CREATFAM",    # Creative family environment
            "CREATAS",     # Creative Activities at school
            "CREATOOS",    # Creative Activities outside school
        ]
    },
    "ICT & Digitale Kompetenzen": {
        "description": "Digitale Kompetenzen und ICT-Nutzung",
        "scales": [
            "ICTEFFIC",    # Self-efficacy in digital competencies
            "ICTHOME",     # ICT availability outside school
            "ICTSCH",      # ICT availability at school
            "ICTQUAL",     # Quality of ICT access
            "ICTINFO",     # Practices regarding online information
            "ICTSUBJ",     # Subject-related ICT use
            "ICTENQ",      # ICT in enquiry-based learning
            "ICTFEED",     # Support/feedback via ICT
            "ICTOUT",      # ICT for school outside classroom
            "ICTWKDY",     # ICT activity frequency (weekday)
            "ICTWKEND",    # ICT activity frequency (weekend)
            "ICTREG",      # Views on regulated ICT use
        ]
    },
    "Eltern & Haushalt": {
        "description": "Sozioökonomischer Status und Elternbeteiligung",
        "scales": [
            "HOMEPOS",     # Home possessions (SES)
            "PARINVOL",    # Parental involvement
            "PASCHPOL",    # School policies for parental involvement
            "ATTIMMP",     # Parents' attitudes toward immigrants
        ]
    },
    "COVID-19 Kontext": {
        "description": "COVID-19 bezogene Lernfaktoren",
        "scales": [
            "SCHSUST",     # School actions to sustain learning
            "PROBSELF",    # Problems with self-directed learning
            "FAMSUPSL",    # Family support for self-directed learning
            "FEELLAH",     # Feelings about learning at home
            "SDLEFF",      # Self-directed learning self-efficacy
        ]
    }
}


# Detailed scale descriptions (English + German)
SCALE_DESCRIPTIONS = {
    # Mathematics & Performance
    "ANXMAT": {
        "name_en": "Mathematics Anxiety",
        "name_de": "Mathematik-Angst",
        "description_de": "Emotionale Angst und Unbehagen bei mathematischen Aufgaben"
    },
    "MATHEFF": {
        "name_en": "Mathematics Self-Efficacy",
        "name_de": "Mathematik-Selbstwirksamkeit",
        "description_de": "Überzeugung, mathematische Aufgaben erfolgreich lösen zu können"
    },
    "MATHEF21": {
        "name_en": "Math Self-Efficacy: 21st Century Skills",
        "name_de": "Mathe-Selbstwirksamkeit: 21. Jahrhundert",
        "description_de": "Selbstwirksamkeit für mathematisches Denken und 21. Jahrhundert Kompetenzen"
    },
    "MATHPERS": {
        "name_en": "Effort and Persistence in Mathematics",
        "name_de": "Anstrengung und Ausdauer in Mathematik",
        "description_de": "Bereitschaft, sich in Mathematik anzustrengen und durchzuhalten"
    },
    "TEACHSUP": {
        "name_en": "Teacher Support",
        "name_de": "Lehrerunterstützung",
        "description_de": "Wahrgenommene Unterstützung durch Mathematiklehrkraft"
    },
    "DISCLIM": {
        "name_en": "Disciplinary Climate",
        "name_de": "Disziplin im Unterricht",
        "description_de": "Ordnung und Disziplin im Mathematikunterricht"
    },

    # Wellbeing & Social
    "BELONG": {
        "name_en": "Sense of Belonging",
        "name_de": "Zugehörigkeitsgefühl",
        "description_de": "Gefühl der sozialen Integration in der Schule"
    },
    "BULLIED": {
        "name_en": "Being Bullied",
        "name_de": "Mobbing-Erfahrungen",
        "description_de": "Häufigkeit von Mobbing-Erlebnissen"
    },
    "FAMSUP": {
        "name_en": "Family Support",
        "name_de": "Familienunterstützung",
        "description_de": "Emotionale Unterstützung durch die Familie"
    },

    # Personality
    "GROSAGR": {
        "name_en": "Growth Mindset",
        "name_de": "Wachstumsorientiertes Denken",
        "description_de": "Überzeugung, dass Fähigkeiten entwickelbar sind"
    },
    "PERSEVAGR": {
        "name_en": "Perseverance",
        "name_de": "Ausdauer",
        "description_de": "Fähigkeit, an Zielen festzuhalten"
    },
    "CURIOAGR": {
        "name_en": "Curiosity",
        "name_de": "Neugier",
        "description_de": "Interesse an neuen Erfahrungen und Lernen"
    },

    # Creativity
    "CREATEFF": {
        "name_en": "Creative Self-Efficacy",
        "name_de": "Kreative Selbstwirksamkeit",
        "description_de": "Überzeugung, kreativ sein zu können"
    },
    "CREATSCH": {
        "name_en": "Creative School Environment",
        "name_de": "Kreatives Schulumfeld",
        "description_de": "Wahrnehmung der Schule als kreativitätsfördernd"
    },

    # ICT
    "ICTEFFIC": {
        "name_en": "Self-Efficacy in Digital Competencies",
        "name_de": "Digitale Selbstwirksamkeit",
        "description_de": "Überzeugung, digitale Aufgaben bewältigen zu können"
    },
    "ICTHOME": {
        "name_en": "ICT Availability at Home",
        "name_de": "ICT-Verfügbarkeit zuhause",
        "description_de": "Zugang zu digitalen Geräten außerhalb der Schule"
    },

    # Parents & Household
    "HOMEPOS": {
        "name_en": "Home Possessions (SES)",
        "name_de": "Besitztümer im Haushalt (SES)",
        "description_de": "Indikator für sozioökonomischen Status"
    },
    "PARINVOL": {
        "name_en": "Parental Involvement",
        "name_de": "Elternbeteiligung",
        "description_de": "Engagement der Eltern in schulischen Angelegenheiten"
    },

    # COVID-19
    "SCHSUST": {
        "name_en": "School Actions to Sustain Learning",
        "name_de": "Schulmaßnahmen zur Lernunterstützung",
        "description_de": "Schulische Unterstützung während COVID-19"
    },
    "SDLEFF": {
        "name_en": "Self-Directed Learning Self-Efficacy",
        "name_de": "Selbstgesteuertes Lernen Selbstwirksamkeit",
        "description_de": "Überzeugung, selbstständig lernen zu können"
    }
}


def get_all_scales():
    """Returns list of all 58 available scale names"""
    all_scales = []
    for category_data in SCALE_CATEGORIES.values():
        all_scales.extend(category_data["scales"])
    return all_scales


def get_scale_category(scale_name):
    """Returns the category name for a given scale"""
    for category, data in SCALE_CATEGORIES.items():
        if scale_name in data["scales"]:
            return category
    return "Unbekannt"


def get_category_scales(category_name):
    """Returns all scales in a category"""
    if category_name in SCALE_CATEGORIES:
        return SCALE_CATEGORIES[category_name]["scales"]
    return []


def get_scale_info(scale_name):
    """Returns description for a scale (with fallback)"""
    if scale_name in SCALE_DESCRIPTIONS:
        return SCALE_DESCRIPTIONS[scale_name]
    return {
        "name_en": scale_name,
        "name_de": scale_name,
        "description_de": "Keine Beschreibung verfügbar"
    }
