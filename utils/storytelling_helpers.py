"""
Storytelling Helper Functions
Generiert kinderleichte Erklärungen für PISA-Daten
"""

import pandas as pd
import numpy as np
import streamlit as st


def interpret_oecd_score(value: float, scale_name: str = "Variable") -> dict:
    """
    Interpretiert einen OECD-standardisierten Score

    Args:
        value: Der Durchschnittswert (0 = OECD-Durchschnitt)
        scale_name: Name der Skala (z.B. "ANXMAT", "MATHEFF")

    Returns:
        Dictionary mit color, text, detail
    """
    is_anxiety = "ANX" in scale_name.upper() or "ANGST" in scale_name.upper()

    if abs(value) < 0.2:
        return {
            'color': '🟢',
            'text': '**Fast genau beim OECD-Durchschnitt!**',
            'detail': f'Deutsche Schüler liegen genau im internationalen Durchschnitt.'
        }
    elif value > 0.5:
        if is_anxiety:
            return {
                'color': '🔴',
                'text': '**Deutlich über dem OECD-Durchschnitt!**',
                'detail': 'Deutsche Schüler haben mehr Angst als der internationale Durchschnitt. Hier besteht Handlungsbedarf!'
            }
        else:
            return {
                'color': '🟢',
                'text': '**Deutlich über dem OECD-Durchschnitt!**',
                'detail': 'Deutsche Schüler liegen deutlich über dem internationalen Durchschnitt. Super!'
            }
    elif value > 0:
        if is_anxiety:
            return {
                'color': '🟡',
                'text': '**Etwas über dem OECD-Durchschnitt**',
                'detail': 'Deutsche Schüler haben etwas mehr Angst als der internationale Durchschnitt.'
            }
        else:
            return {
                'color': '🟢',
                'text': '**Etwas über dem OECD-Durchschnitt**',
                'detail': 'Deutsche Schüler liegen etwas über dem internationalen Durchschnitt.'
            }
    elif value > -0.5:
        if is_anxiety:
            return {
                'color': '🟢',
                'text': '**Etwas unter dem OECD-Durchschnitt**',
                'detail': 'Deutsche Schüler haben etwas weniger Angst als der internationale Durchschnitt - das ist gut!'
            }
        else:
            return {
                'color': '🟡',
                'text': '**Etwas unter dem OECD-Durchschnitt**',
                'detail': 'Deutsche Schüler liegen etwas unter dem internationalen Durchschnitt.'
            }
    else:
        if is_anxiety:
            return {
                'color': '🟢',
                'text': '**Deutlich unter dem OECD-Durchschnitt!**',
                'detail': 'Deutsche Schüler haben viel weniger Angst als der internationale Durchschnitt. Super!'
            }
        else:
            return {
                'color': '🔴',
                'text': '**Deutlich unter dem OECD-Durchschnitt!**',
                'detail': 'Deutsche Schüler liegen deutlich unter dem internationalen Durchschnitt. Hier können Interventionen helfen!'
            }


def create_emoji_scale(value: float, scale_type: str = 'anxiety') -> str:
    """
    Erstellt eine Emoji-Skala zur Visualisierung

    Args:
        value: Wert zwischen -2 und +2
        scale_type: 'anxiety' oder 'confidence'

    Returns:
        Formatierter String mit Emojis
    """
    value_pos = max(-2, min(2, value))
    scale_positions = [-2, -1, 0, 1, 2]

    if scale_type == 'anxiety':
        emojis = ["😊😊", "🙂", "😐", "😟", "😰😰"]
    else:  # confidence
        emojis = ["😔😔", "😕", "😐", "🙂", "😊😊"]

    scale_str = ""
    for i, pos in enumerate(scale_positions):
        if abs(value_pos - pos) < 0.3:
            scale_str += f"**[{emojis[i]}]** "
        else:
            scale_str += f"{emojis[i]} "

    return scale_str


def interpret_std(std_value: float) -> dict:
    """
    Interpretiert Standardabweichung

    Args:
        std_value: Standardabweichung

    Returns:
        Dictionary mit text und detail
    """
    if std_value > 1.3:
        return {
            'text': '**Sehr große Unterschiede!**',
            'detail': 'Manche Schüler sind total entspannt, andere sehr ängstlich. Die Gruppe ist sehr heterogen.',
            'visual': """
        ```
        Entspannt                           Ängstlich
        |                                         |
        👤              👤👤👤              👤👤
        ← Wenige hier   Viele hier   Viele hier →
        ```
        → Das Schulsystem erzeugt **sehr unterschiedliche** Ergebnisse!
        """
        }
    elif std_value > 1.0:
        return {
            'text': '**Große Unterschiede**',
            'detail': 'Es gibt deutliche Unterschiede zwischen den Schülern - manche ängstlich, manche entspannt.',
            'visual': """
        ```
        Entspannt                           Ängstlich
        |                                         |
            👤👤      👤👤👤👤      👤👤
            ← Einige hier   Viele hier   Einige hier →
        ```
        → Es gibt verschiedene Gruppen von Schülern.
        """
        }
    else:
        return {
            'text': '**Moderate Unterschiede**',
            'detail': 'Die Schüler sind sich relativ ähnlich.',
            'visual': """
        ```
        Entspannt                           Ängstlich
        |                                         |
               👤👤👤👤👤👤👤
               ← Die meisten hier →
        ```
        → Die meisten Schüler sind sich ähnlich.
        """
        }


def interpret_confidence_score(confidence_score: float) -> dict:
    """
    Interpretiert den Confidence Score (MATHEFF - ANXMAT)

    Args:
        confidence_score: Differenz zwischen Selbstwirksamkeit und Angst

    Returns:
        Dictionary mit emoji, text, detail
    """
    if confidence_score > 0.5:
        return {
            'emoji': '🟢',
            'text': '**Super! Selbstvertrauen überwiegt deutlich!**',
            'detail': 'Deutsche Schüler haben mehr Selbstvertrauen als Angst. Das ist eine gute Grundlage für Lernerfolg!',
            'status': 'success'
        }
    elif confidence_score > 0:
        return {
            'emoji': '🟢',
            'text': '**Gut! Selbstvertrauen überwiegt leicht**',
            'detail': 'Deutsche Schüler haben etwas mehr Selbstvertrauen als Angst.',
            'status': 'success'
        }
    elif confidence_score > -0.5:
        return {
            'emoji': '🟡',
            'text': '**Ausgeglichen mit leichtem Angst-Überhang**',
            'detail': 'Selbstvertrauen und Angst halten sich fast die Waage, mit leichter Tendenz zur Angst.',
            'status': 'warning'
        }
    else:
        return {
            'emoji': '🔴',
            'text': '**Achtung! Angst überwiegt deutlich!**',
            'detail': 'Deutsche Schüler haben mehr Angst als Selbstvertrauen. Hier sollten Interventionen ansetzen!',
            'status': 'error'
        }


def create_balance_visualization(matheff: float, anxmat: float) -> str:
    """
    Erstellt eine Balance-Waage Visualisierung

    Args:
        matheff: Selbstwirksamkeit
        anxmat: Angst

    Returns:
        Formatierter String mit Balance-Darstellung
    """
    matheff_bar = "█" * max(1, int(abs(matheff) * 10))
    anxmat_bar = "█" * max(1, int(abs(anxmat) * 10))

    return f"""
    ```
    Selbstvertrauen  vs.  Angst
    {matheff_bar: <20} | {anxmat_bar}
    {matheff:.2f}           {anxmat:.2f}
    ```
    """


def get_pisa_level(score: float) -> str:
    """
    Bestimmt PISA-Level basierend auf Score

    Args:
        score: PISA-Score

    Returns:
        Level-Beschreibung
    """
    if score < 358:
        return "Unter Level 1 (Sehr schwach)"
    elif score < 420:
        return "Level 1 (Grundkenntnisse)"
    elif score < 482:
        return "Level 2 (Basiskompetenzen)"
    elif score < 545:
        return "Level 3 (Solide Kenntnisse)"
    elif score < 607:
        return "Level 4 (Gut)"
    elif score < 669:
        return "Level 5 (Sehr gut)"
    else:
        return "Level 6 (Herausragend)"


def create_recommendations(mean_anxmat: float, mean_matheff: float,
                          std_anxmat: float, corr: float) -> list:
    """
    Generiert dynamische Empfehlungen basierend auf den Daten

    Args:
        mean_anxmat: Durchschnittliche Angst
        mean_matheff: Durchschnittliche Selbstwirksamkeit
        std_anxmat: Standardabweichung Angst
        corr: Korrelation Selbstwirksamkeit-Leistung

    Returns:
        Liste mit Empfehlungen
    """
    recommendations = []

    if mean_anxmat > 0.3:
        recommendations.append("🎯 **Fokus auf**: Angstreduktion (ANXMAT ist erhöht)")

    if mean_matheff < -0.3:
        recommendations.append("🎯 **Fokus auf**: Selbstwirksamkeitsförderung (MATHEFF ist niedrig)")

    if std_anxmat > 1.3:
        recommendations.append("🎯 **Wichtig**: Individuelle Förderung (große Unterschiede zwischen Schülern!)")

    if abs(corr) > 0.4:
        recommendations.append(f"✅ **Evidenz**: Selbstvertrauen korreliert stark mit Leistung (r = {corr:.2f}) - Interventionen sind wirksam!")

    if not recommendations:
        recommendations.append("🎯 **Allgemein**: Ausgeglichene Förderung von Selbstvertrauen und Angstbewältigung")

    return recommendations


def display_simple_explanation(df: pd.DataFrame,
                               mean_anxmat: float,
                               mean_matheff: float,
                               expanded: bool = True):
    """
    Zeigt die komplette "Einfach erklärt" Sektion

    Args:
        df: DataFrame mit Schülerdaten
        mean_anxmat: Durchschnittliche Angst
        mean_matheff: Durchschnittliche Selbstwirksamkeit
        expanded: Ob Expander standardmäßig geöffnet sein soll
    """

    with st.expander("👶 **Einfach erklärt - Was bedeuten diese Zahlen?**", expanded=expanded):

        # Berechne Werte
        n_students = len(df)
        mean_confidence = mean_matheff - mean_anxmat
        mean_math = df['math_score'].mean() if 'math_score' in df.columns else df['PV1MATH'].mean()
        std_anxmat = df['ANXMAT'].std() if 'ANXMAT' in df.columns else 1.0
        std_matheff = df['MATHEFF'].std() if 'MATHEFF' in df.columns else 1.0

        # Section 1: Was siehst du?
        st.markdown(f"""
        ## 📊 Was siehst du?

        Du schaust dir **{n_students:,} deutsche Schüler** an (aus der PISA-Studie).

        Für jeden haben wir gemessen:
        - **ANXMAT** = Mathe-Angst (je höher, desto ängstlicher)
        - **MATHEFF** = Selbstvertrauen in Mathe (je höher, desto selbstbewusster)
        - **Math Score** = Matheleistung in Punkten
        """)

        st.divider()

        # Section 2: Der Durchschnitt erklärt
        st.markdown("## 🎯 Der Durchschnitt erklärt")

        col1, col2 = st.columns(2)

        with col1:
            anxmat_interp = interpret_oecd_score(mean_anxmat, "ANXMAT")
            st.markdown(f"""
            **😰 Mathe-Angst: {mean_anxmat:.3f}**

            {anxmat_interp['color']} {anxmat_interp['text']}

            {anxmat_interp['detail']}

            **Merke:** 0 = OECD-Durchschnitt
            """)

        with col2:
            matheff_interp = interpret_oecd_score(mean_matheff, "MATHEFF")
            st.markdown(f"""
            **💪 Selbstvertrauen: {mean_matheff:.3f}**

            {matheff_interp['color']} {matheff_interp['text']}

            {matheff_interp['detail']}

            **Merke:** 0 = OECD-Durchschnitt
            """)

        st.divider()

        # Section 3: Emoji-Skala
        st.markdown("## 😊 Wo steht Deutschland?")

        st.markdown("**😰 Mathe-Angst Skala:**")
        st.markdown(create_emoji_scale(mean_anxmat, 'anxiety'))
        st.markdown("← Wenig Angst&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Viel Angst →")

        st.markdown("")
        st.markdown("**💪 Selbstvertrauen Skala:**")
        st.markdown(create_emoji_scale(mean_matheff, 'confidence'))
        st.markdown("← Wenig Selbstvertrauen&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Viel Selbstvertrauen →")

        st.divider()

        # Section 4: Standardabweichung
        st.markdown("## 📏 Wie unterschiedlich sind die Schüler?")

        std_interp = interpret_std(std_anxmat)
        st.markdown(f"""
        **Standardabweichung (std)** = Wie verschieden sind die Schüler?

        - ANXMAT: {std_anxmat:.2f} → {std_interp['text']}
        - MATHEFF: {std_matheff:.2f}

        {std_interp['detail']}

        **Visualisiert:**
        """)

        st.markdown(std_interp['visual'])

        st.divider()

        # Section 5: Confidence Score
        st.markdown("## 🏆 Der Confidence Score")

        st.markdown(f"""
        **Formel:** Confidence Score = MATHEFF - ANXMAT

        **Dein Ergebnis:** {mean_confidence:.3f}
        """)

        conf_interp = interpret_confidence_score(mean_confidence)
        st.markdown(f"""
        {conf_interp['emoji']} {conf_interp['text']}

        {conf_interp['detail']}
        """)

        # Balance-Visualisierung
        st.markdown("**Visualisierung:**")
        st.markdown(create_balance_visualization(mean_matheff, mean_anxmat))

        if conf_interp['status'] == 'success':
            st.success("✅ Selbstvertrauen ist stärker!")
        elif conf_interp['status'] == 'warning':
            st.info("⚖️ Fast ausgeglichen")
        else:
            st.warning("⚠️ Angst ist stärker")
