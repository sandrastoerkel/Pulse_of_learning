"""Quadranten-Analyse MATHEFF x ANXMAT: neutrale Labels und datengetriebene Texte (FIX4).

Die Einteilung (Median-Split) bleibt in den Seiten; dieses Modul liefert nur
Bezeichnungen und Aussagen, die aus den berechneten Mittelwerten abgeleitet werden,
damit Text und Tabelle nicht mehr auseinanderlaufen koennen.
"""

import pandas as pd

QUADRANT_SHORT = {
    'Q1': 'Viel Zutrauen, wenig Angst',
    'Q2': 'Viel Zutrauen, viel Angst',
    'Q3': 'Wenig Zutrauen, viel Angst',
    'Q4': 'Wenig Zutrauen, wenig Angst',
}

QUADRANT_LABELS = {
    'Q1': 'Q1: Viel Zutrauen, wenig Angst (Hoch/Niedrig)',
    'Q2': 'Q2: Viel Zutrauen, viel Angst (Hoch/Hoch)',
    'Q3': 'Q3: Wenig Zutrauen, viel Angst (Niedrig/Hoch)',
    'Q4': 'Q4: Wenig Zutrauen, wenig Angst (Niedrig/Niedrig)',
}

MODEL_TEXT = """
**Quadranten-Modell** (Median-Split von Selbstwirksamkeit MATHEFF und Mathe-Angst ANXMAT in dieser Stichprobe):
- **Q1:** Hohe Selbstwirksamkeit + niedrige Angst
- **Q2:** Hohe Selbstwirksamkeit + hohe Angst
- **Q3:** Niedrige Selbstwirksamkeit + hohe Angst
- **Q4:** Niedrige Selbstwirksamkeit + niedrige Angst

Welche Gruppe im Mittel am höchsten bzw. am niedrigsten abschneidet, zeigt die Tabelle.
"""


def assign_quadrants(df: pd.DataFrame, x: str = 'MATHEFF', y: str = 'ANXMAT'):
    """Median-Split in Q1-Q4. Schueler:innen ohne Wert bei x oder y erhalten KEIN Quadranten-Label (NaN).

    Frueher landeten fehlende Werte per Default in Q4 und verfaelschten dessen Mittelwert (FIX4).
    Die Mediane werden nur aus vollstaendigen Faellen berechnet.
    Rueckgabe: (Series mit 'Q1'..'Q4' oder NaN, median_x, median_y)
    """
    complete = df[x].notna() & df[y].notna()
    med_x = df.loc[complete, x].median()
    med_y = df.loc[complete, y].median()
    q = pd.Series(pd.NA, index=df.index, dtype='object')
    hi_x = df[x] >= med_x
    hi_y = df[y] >= med_y
    q[complete & hi_x & ~hi_y] = 'Q1'
    q[complete & hi_x & hi_y] = 'Q2'
    q[complete & ~hi_x & hi_y] = 'Q3'
    q[complete & ~hi_x & ~hi_y] = 'Q4'
    return q, med_x, med_y


def coverage_caption(q: pd.Series) -> str:
    n_in = int(q.notna().sum())
    n_out = int(q.isna().sum())
    txt = f"Quadranten-Analyse mit N = {_de_int(n_in)} Schüler:innen, die Angaben zu MATHEFF und ANXMAT haben"
    if n_out:
        txt += f"; {_de_int(n_out)} ohne diese Angaben sind nicht zugeordnet"
    return txt + "."


def summarize_quadrants(df: pd.DataFrame, score_col: str, quadrant_col: str = 'quadrant') -> dict:
    """Kennzahlen je Quadrant plus abgeleitete Aussagen (alles aus den Daten)."""
    data = df[[quadrant_col, score_col]].dropna()
    total = int(df[quadrant_col].notna().sum())
    means = data.groupby(quadrant_col)[score_col].mean()
    counts = data.groupby(quadrant_col)[score_col].count()

    s = {'means': means, 'counts': counts, 'total': total}
    present = [q for q in ['Q1', 'Q2', 'Q3', 'Q4'] if q in means.index]
    s['complete'] = len(present) == 4
    if not present:
        return s

    s['best'] = means.idxmax()
    s['worst'] = means.idxmin()

    high = data[data[quadrant_col].isin(['Q1', 'Q2'])][score_col]
    low = data[data[quadrant_col].isin(['Q3', 'Q4'])][score_col]
    s['high_se_mean'] = high.mean() if len(high) else float('nan')
    s['low_se_mean'] = low.mean() if len(low) else float('nan')
    s['se_gap'] = s['high_se_mean'] - s['low_se_mean']

    if s['complete']:
        s['high_range'] = (min(means['Q1'], means['Q2']), max(means['Q1'], means['Q2']))
        s['low_range'] = (min(means['Q3'], means['Q4']), max(means['Q3'], means['Q4']))
        # Unterschied wenig Angst minus viel Angst, getrennt nach Selbstwirksamkeit
        s['anx_gap_high_se'] = means['Q1'] - means['Q2']
        s['anx_gap_low_se'] = means['Q4'] - means['Q3']

    s['support_n'] = int(len(low))
    s['support_pct'] = (len(low) / total * 100) if total else 0.0
    s['support_perf'] = s['low_se_mean']
    return s


def interpretation_markdown(s: dict) -> str:
    """Kernaussagen zur Tabelle, abgeleitet aus den Mittelwerten."""
    if not s.get('complete'):
        return "Nicht alle vier Gruppen sind besetzt – keine zusammenfassende Aussage möglich."
    m = s['means']
    hr, lr = s['high_range'], s['low_range']
    lines = ["**Was die Tabelle zeigt:**"]
    if s['se_gap'] > 0:
        lines.append(
            f"- **Selbstwirksamkeit trennt die Gruppen:** mit hoher Selbstwirksamkeit "
            f"Ø {hr[0]:.0f}–{hr[1]:.0f} Punkte, mit niedriger Ø {lr[0]:.0f}–{lr[1]:.0f} Punkte "
            f"(Unterschied der beiden Hälften: {s['se_gap']:.0f} Punkte)."
        )
    else:
        lines.append(
            f"- **Selbstwirksamkeit:** hohe Selbstwirksamkeit Ø {hr[0]:.0f}–{hr[1]:.0f} Punkte, "
            f"niedrige Ø {lr[0]:.0f}–{lr[1]:.0f} Punkte."
        )
    gh, gl = s['anx_gap_high_se'], s['anx_gap_low_se']
    lines.append(
        f"- **Mathe-Angst:** Bei hoher Selbstwirksamkeit liegt die Gruppe mit wenig Angst "
        f"{gh:+.0f} Punkte gegenüber der Gruppe mit viel Angst, bei niedriger Selbstwirksamkeit {gl:+.0f} Punkte."
    )
    if abs(gh) > abs(gl):
        lines.append("  Der Unterschied durch Angst ist also vor allem bei hoher Selbstwirksamkeit sichtbar.")
    elif abs(gl) > abs(gh):
        lines.append("  Der Unterschied durch Angst ist also vor allem bei niedriger Selbstwirksamkeit sichtbar.")
    lines.append(
        f"- **Höchster Mittelwert:** {QUADRANT_LABELS[s['best']]} ({m[s['best']]:.0f}) · "
        f"**Niedrigster Mittelwert:** {QUADRANT_LABELS[s['worst']]} ({m[s['worst']]:.0f})"
    )
    lines.append("- Beschreibende Mittelwerte; ein Signifikanztest zwischen einzelnen Quadranten wird hier nicht berechnet.")
    return "\n".join(lines)


def _de_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def support_markdown(s: dict) -> str:
    """Hinweis zur Gruppe mit Foerderbedarf (Q3 + Q4)."""
    return (
        f"**Gruppe mit Förderbedarf (Q3 + Q4, niedrige Selbstwirksamkeit):**\n"
        f"- **{_de_int(s['support_n'])} Schüler:innen** ({s['support_pct']:.1f} % der Stichprobe)\n"
        f"- **Durchschnittsleistung:** {s['support_perf']:.0f} Punkte\n"
        f"- **Ansatzpunkt:** Selbstwirksamkeit durch echte, gestufte Erfolgserlebnisse stärken; "
        f"in Q3 zusätzlich den Umgang mit Mathe-Angst begleiten"
    )


def support_finding(s: dict) -> str:
    return (
        f"**Gruppe mit Förderbedarf:** {s['support_pct']:.1f} % der Schüler:innen haben eine niedrige "
        f"Selbstwirksamkeit (Q3 + Q4, Ø {s['support_perf']:.0f} Punkte gegenüber Ø {s['high_se_mean']:.0f} "
        f"bei hoher Selbstwirksamkeit) → Selbstwirksamkeit ist der wichtigste Ansatzpunkt"
    )
