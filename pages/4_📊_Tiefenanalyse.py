import streamlit as st
import pandas as pd
import numpy as np
import sys
sys.path.append('..')
from utils.db_loader import get_db_connection, load_student_data
from utils.scale_info import get_scale_category, get_scale_info, SCALE_DESCRIPTIONS
from utils.feature_descriptions import get_feature_label
from utils.statistical_analysis import (
    compute_correlation_matrix, correlation_with_pvalue,
    independent_ttest, one_way_anova, check_normality,
    get_effect_size_interpretation
)
from utils.visualization_helpers import (
    create_correlation_heatmap, create_scatter_with_regression,
    create_distribution_plot, create_grouped_boxplot,
    create_scatter_with_marginals, create_combined_distribution_plot,
    create_qq_plot
)
from utils.data_filters import (
    filter_by_gender, filter_by_performance_level,
    get_complete_cases, select_wle_scales,
    create_performance_groups, prepare_export_data
)
from pathlib import Path

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="Tiefenanalyse",
    page_icon="📊",
    layout="wide"
)

# ============================================
# TITLE
# ============================================

st.title("📊 Phase 4: Tiefenanalyse")
st.markdown("**Statistische Analysen und Visualisierungen der PISA 2022 Daten**")

st.divider()

# ============================================
# DATA LOADING
# ============================================

@st.cache_data(ttl=60)
def load_analysis_data(selected_vars, performance_vars):
    """Load data for analysis"""
    conn = get_db_connection()

    # Combine all needed variables
    all_vars = list(set(selected_vars + performance_vars + ['ST004D01T']))

    # Load data
    query = f"""
    SELECT {', '.join(all_vars)}
    FROM student_data
    WHERE PV1MATH IS NOT NULL
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


@st.cache_data
def get_available_wle_scales():
    """Get list of available WLE scales"""
    return sorted(list(SCALE_DESCRIPTIONS.keys()))


# ============================================
# SIDEBAR: GLOBAL SETTINGS
# ============================================

st.sidebar.header("⚙️ Globale Einstellungen")

# Performance variable selection
performance_var = st.sidebar.selectbox(
    "Leistungsvariable:",
    options=['PV1MATH', 'PV1READ', 'PV1SCIE'],
    format_func=lambda x: {
        'PV1MATH': 'Mathematik',
        'PV1READ': 'Lesen',
        'PV1SCIE': 'Naturwissenschaften'
    }[x],
    index=0
)

# Data filters
st.sidebar.subheader("🔍 Daten-Filter")

gender_filter = st.sidebar.selectbox(
    "Geschlecht:",
    options=['Alle', 'Weiblich', 'Männlich'],
    index=0
)

performance_level = st.sidebar.selectbox(
    "Leistungsniveau:",
    options=['Alle', 'Niedrig', 'Mittel', 'Hoch'],
    index=0,
    help="Niedrig: <482, Mittel: 482-607, Hoch: ≥607"
)

st.sidebar.divider()

# ============================================
# TABS
# ============================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Korrelationen",
    "🔵 Feature vs Performance",
    "📈 Verteilungen",
    "👥 Gruppenvergleiche",
    "🧪 Statistische Tests",
    "💾 Export"
])

# ============================================
# TAB 1: KORRELATIONEN
# ============================================

with tab1:
    st.header("📊 Korrelationsanalyse")

    st.info("""
    **Korrelation zeigt den linearen Zusammenhang zwischen Variablen:**
    - **r = 1**: Perfekte positive Korrelation
    - **r = 0**: Keine Korrelation
    - **r = -1**: Perfekte negative Korrelation

    **Interpretation (nach Cohen):**
    - |r| < 0.3: Schwach
    - |r| 0.3-0.5: Mittel
    - |r| > 0.5: Stark
    """)

    # Variable selection
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Variablen-Auswahl")

        # Get available scales
        available_scales = get_available_wle_scales()

        # Pre-select some interesting variables
        default_vars = ['ANXMAT', 'MATHEFF', 'BELONG', 'ESCS', 'HOMEPOS']
        default_vars = [v for v in default_vars if v in available_scales]

        selected_vars = st.multiselect(
            "WLE-Skalen:",
            options=available_scales,
            default=default_vars[:5],
            help="Wähle 2-10 Variablen für die Korrelationsmatrix"
        )

        include_performance = st.checkbox(
            "Leistungsvariable einbeziehen",
            value=True
        )

        if include_performance:
            selected_vars.append(performance_var)

    with col2:
        st.subheader("Optionen")

        corr_method = st.selectbox(
            "Korrelationsmethode:",
            options=['pearson', 'spearman', 'kendall'],
            format_func=lambda x: {
                'pearson': 'Pearson (linear)',
                'spearman': 'Spearman (Rang)',
                'kendall': 'Kendall (Rang)'
            }[x],
            index=0
        )

        show_annotations = st.checkbox("Werte anzeigen", value=True)
        mask_diagonal = st.checkbox("Diagonale maskieren", value=False)

    # Calculate and display correlation matrix
    if len(selected_vars) >= 2:
        # Load data
        df = load_analysis_data(selected_vars, [performance_var])

        # Apply filters
        df = filter_by_gender(df, gender_filter)
        df = filter_by_performance_level(df, performance_var, performance_level)

        # Get complete cases
        df_clean = get_complete_cases(df, selected_vars)

        st.divider()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Schüler (gesamt)", len(df))
        with col2:
            st.metric("✅ Vollständige Fälle", len(df_clean))
        with col3:
            st.metric("📉 Fehlende Daten", f"{(1 - len(df_clean)/len(df))*100:.1f}%")

        if len(df_clean) < 30:
            st.warning("⚠️ Weniger als 30 vollständige Fälle. Ergebnisse mit Vorsicht interpretieren!")

        # Compute correlation matrix
        corr_matrix = compute_correlation_matrix(df_clean[selected_vars], method=corr_method)

        # Visualization
        st.subheader("Korrelationsmatrix")

        fig = create_correlation_heatmap(
            corr_matrix,
            title=f"Korrelationen ({corr_method.capitalize()})",
            annotations=show_annotations,
            mask_diagonal=mask_diagonal
        )

        st.plotly_chart(fig, use_container_width=True)

        # Detailed correlation table
        with st.expander("📋 Detaillierte Korrelationstabelle"):
            st.dataframe(
                corr_matrix.style.background_gradient(cmap='RdBu', vmin=-1, vmax=1),
                use_container_width=True
            )

        # Top correlations
        st.subheader("🔝 Stärkste Korrelationen")

        # Extract correlations
        corr_list = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                var1 = corr_matrix.columns[i]
                var2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]

                # Calculate p-value
                r, p = correlation_with_pvalue(df_clean[var1], df_clean[var2], method=corr_method)

                corr_list.append({
                    'Variable 1': var1,
                    'Variable 2': var2,
                    'r': corr_value,
                    'p-value': p,
                    '|r|': abs(corr_value)
                })

        corr_df = pd.DataFrame(corr_list).sort_values('|r|', ascending=False)

        # Display top 10
        display_df = corr_df.head(10)[['Variable 1', 'Variable 2', 'r', 'p-value']].copy()
        display_df['Signifikanz'] = display_df['p-value'].apply(
            lambda p: '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else 'n.s.'))
        )

        st.dataframe(
            display_df.style.format({'r': '{:.3f}', 'p-value': '{:.4f}'}),
            use_container_width=True
        )

        st.caption("Signifikanz: *** p<0.001, ** p<0.01, * p<0.05, n.s. = nicht signifikant")

    else:
        st.warning("⚠️ Bitte wähle mindestens 2 Variablen für die Korrelationsanalyse.")

# ============================================
# TAB 2: FEATURE VS PERFORMANCE
# ============================================

with tab2:
    st.header("🔵 Feature vs Performance")

    st.info("""
    **Scatter Plots zeigen den Zusammenhang zwischen einem Feature und der Leistung.**
    - Jeder Punkt = ein Schüler
    - Trendlinie = Lineare Regression
    - Korrelation (r) zeigt Stärke des Zusammenhangs
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Feature selection
        available_scales = get_available_wle_scales()

        selected_feature = st.selectbox(
            "Feature (X-Achse):",
            options=available_scales,
            index=available_scales.index('ANXMAT') if 'ANXMAT' in available_scales else 0
        )

    with col2:
        # Plot options
        show_marginals = st.checkbox("Marginalverteilungen", value=False)
        color_by_gender = st.checkbox("Nach Geschlecht färben", value=False)

    # Load data
    df = load_analysis_data([selected_feature], [performance_var])

    # Apply filters (but not if we're coloring by gender)
    if not color_by_gender:
        df = filter_by_gender(df, gender_filter)
    df = filter_by_performance_level(df, performance_var, performance_level)

    # Remove missing values
    plot_df = df[[selected_feature, performance_var, 'ST004D01T']].dropna()

    st.divider()

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Schüler", len(plot_df))

    with col2:
        corr, p_val = correlation_with_pvalue(plot_df[selected_feature], plot_df[performance_var])
        st.metric("Korrelation (r)", f"{corr:.3f}")

    with col3:
        sig_label = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else ('*' if p_val < 0.05 else 'n.s.'))
        st.metric("p-Wert", f"{p_val:.4f} {sig_label}")

    with col4:
        r_squared = corr ** 2
        st.metric("R² (Varianzaufklärung)", f"{r_squared:.1%}")

    # Visualization
    st.subheader("Scatter Plot")

    # Get feature info for labels
    feature_info = get_scale_info(selected_feature)
    perf_labels = {
        'PV1MATH': 'Mathematik-Leistung',
        'PV1READ': 'Lese-Leistung',
        'PV1SCIE': 'Naturwissenschafts-Leistung'
    }

    if show_marginals:
        fig = create_scatter_with_marginals(
            plot_df,
            x_var=selected_feature,
            y_var=performance_var,
            marginal_type='histogram',
            color_by='ST004D01T' if color_by_gender else None,
            title=f"{feature_info.get('name_de', selected_feature)} vs {perf_labels[performance_var]}"
        )
    else:
        fig = create_scatter_with_regression(
            plot_df,
            x_var=selected_feature,
            y_var=performance_var,
            x_label=feature_info.get('name_de', selected_feature),
            y_label=perf_labels[performance_var],
            color_by='ST004D01T' if color_by_gender else None,
            add_trendline=True,
            show_stats=not color_by_gender  # Don't show stats if split by gender
        )

    st.plotly_chart(fig, use_container_width=True)

    # Interpretation help
    with st.expander("💡 Interpretation"):
        st.markdown(f"""
        **Korrelation:** r = {corr:.3f} (p = {p_val:.4f})

        **Bedeutung:**
        - Die Korrelation ist **{'stark' if abs(corr) > 0.5 else 'mittel' if abs(corr) > 0.3 else 'schwach'}**
        - Die Richtung ist **{'positiv' if corr > 0 else 'negativ'}**
        - Das Ergebnis ist **{'signifikant' if p_val < 0.05 else 'nicht signifikant'}**

        **R² = {r_squared:.1%}** bedeutet: {r_squared*100:.1f}% der Varianz in {perf_labels[performance_var]}
        können durch {feature_info.get('name_de', selected_feature)} erklärt werden.

        **Feature-Info:**
        {feature_info.get('description_de', 'Keine Beschreibung verfügbar')}
        """)

# ============================================
# TAB 3: VERTEILUNGEN
# ============================================

with tab3:
    st.header("📈 Verteilungsanalyse")

    st.info("""
    **Untersuche die Verteilung von Variablen:**
    - Histogram zeigt Häufigkeiten
    - Box Plot zeigt Median, Quartile und Ausreißer
    - Q-Q Plot testet Normalverteilung
    """)

    # Variable selection
    available_scales = get_available_wle_scales()

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_var = st.selectbox(
            "Variable:",
            options=available_scales + [performance_var],
            index=available_scales.index('ANXMAT') if 'ANXMAT' in available_scales else 0
        )

    with col2:
        plot_type = st.radio(
            "Darstellung:",
            options=['Histogram', 'Histogram + Box Plot', 'Q-Q Plot'],
            index=0
        )

    # Load data
    df = load_analysis_data([selected_var], [performance_var])

    # Apply filters
    df = filter_by_gender(df, gender_filter)
    df = filter_by_performance_level(df, performance_var, performance_level)

    # Remove missing
    clean_data = df[selected_var].dropna()

    st.divider()

    # Descriptive statistics
    st.subheader("📊 Deskriptive Statistik")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("N", len(clean_data))
    with col2:
        st.metric("Mittelwert", f"{clean_data.mean():.2f}")
    with col3:
        st.metric("Median", f"{clean_data.median():.2f}")
    with col4:
        st.metric("SD", f"{clean_data.std():.2f}")
    with col5:
        st.metric("Spannweite", f"{clean_data.max() - clean_data.min():.2f}")

    # Normality test
    normality_results = check_normality(clean_data)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Shapiro-Wilk Test",
            f"W = {normality_results['shapiro_statistic']:.3f}",
            delta=f"p = {normality_results['shapiro_pvalue']:.4f}"
        )
    with col2:
        st.metric(
            "KS Test",
            f"D = {normality_results['ks_statistic']:.3f}",
            delta=f"p = {normality_results['ks_pvalue']:.4f}"
        )
    with col3:
        is_normal = normality_results['is_normal']
        st.metric(
            "Normalverteilt?",
            "✅ Ja" if is_normal else "❌ Nein"
        )

    st.divider()

    # Visualization
    st.subheader("Visualisierung")

    var_info = get_scale_info(selected_var)
    var_label = var_info.get('name_de', selected_var)

    if plot_type == 'Histogram':
        fig = create_distribution_plot(
            df,
            variable=selected_var,
            title=f"Verteilung: {var_label}",
            bins=30,
            show_normal_curve=True,
            show_stats=True
        )
        st.plotly_chart(fig, use_container_width=True)

    elif plot_type == 'Histogram + Box Plot':
        fig = create_combined_distribution_plot(
            df,
            variable=selected_var,
            title=f"Verteilung: {var_label}"
        )
        st.plotly_chart(fig, use_container_width=True)

    elif plot_type == 'Q-Q Plot':
        fig = create_qq_plot(
            clean_data,
            title=f"Q-Q Plot: {var_label}"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption("""
        **Q-Q Plot Interpretation:** Wenn die Punkte auf der roten Linie liegen,
        ist die Variable normalverteilt. Abweichungen zeigen Nicht-Normalität.
        """)

# ============================================
# TAB 4: GRUPPENVERGLEICHE
# ============================================

with tab4:
    st.header("👥 Gruppenvergleiche")

    st.info("""
    **Vergleiche Gruppen hinsichtlich einer Variable:**
    - Box Plots zeigen Unterschiede zwischen Gruppen
    - T-Test für 2 Gruppen
    - ANOVA für 3+ Gruppen
    - **NEU:** Quadranten-Analyse (MATHEFF vs ANXMAT)
    """)

    # Settings
    col1, col2, col3 = st.columns(3)

    with col1:
        available_scales = get_available_wle_scales()
        dependent_var = st.selectbox(
            "Abhängige Variable:",
            options=available_scales + [performance_var],
            index=len(available_scales)  # Default: performance
        )

    with col2:
        grouping_method = st.selectbox(
            "Gruppierung:",
            options=['Geschlecht', 'Leistungsniveau', 'MATHEFF vs ANXMAT (Quadranten)', 'Custom'],
            index=0
        )

    with col3:
        if grouping_method == 'Leistungsniveau':
            n_groups = st.selectbox(
                "Anzahl Gruppen:",
                options=[2, 3, 4],
                index=1
            )

    # Load data - include MATHEFF and ANXMAT if quadrant analysis
    if grouping_method == 'MATHEFF vs ANXMAT (Quadranten)':
        load_vars = [dependent_var, 'MATHEFF', 'ANXMAT']
    else:
        load_vars = [dependent_var]

    df = load_analysis_data(load_vars, [performance_var])

    # Create groups
    if grouping_method == 'Geschlecht':
        df['Gruppe'] = df['ST004D01T'].map({1: 'Weiblich', 2: 'Männlich'})
        df = df[df['Gruppe'].notna()]

    elif grouping_method == 'Leistungsniveau':
        df['Gruppe'] = create_performance_groups(df, performance_var, n_groups=n_groups)
        df = df[df['Gruppe'].notna()]

    elif grouping_method == 'MATHEFF vs ANXMAT (Quadranten)':
        # Check if variables are available
        if 'MATHEFF' not in df.columns or 'ANXMAT' not in df.columns:
            st.error("⚠️ MATHEFF und ANXMAT müssen in der Datenbank verfügbar sein für Quadranten-Analyse!")
            st.stop()

        # Calculate medians
        median_matheff = df['MATHEFF'].median()
        median_anxmat = df['ANXMAT'].median()

        # Create quadrants
        df['Gruppe'] = 'Q4: Indifferent'
        df.loc[(df['MATHEFF'] >= median_matheff) & (df['ANXMAT'] < median_anxmat), 'Gruppe'] = 'Q1: Optimal'
        df.loc[(df['MATHEFF'] >= median_matheff) & (df['ANXMAT'] >= median_anxmat), 'Gruppe'] = 'Q2: Ambivalent'
        df.loc[(df['MATHEFF'] < median_matheff) & (df['ANXMAT'] >= median_anxmat), 'Gruppe'] = 'Q3: Risikogruppe'
        df.loc[(df['MATHEFF'] < median_matheff) & (df['ANXMAT'] < median_anxmat), 'Gruppe'] = 'Q4: Indifferent'

        # Info box
        st.info(f"""
        **Quadranten-Definition:**
        - **Q1 (Optimal):** MATHEFF ≥ {median_matheff:.2f} & ANXMAT < {median_anxmat:.2f}
        - **Q2 (Ambivalent):** MATHEFF ≥ {median_matheff:.2f} & ANXMAT ≥ {median_anxmat:.2f}
        - **Q3 (Risikogruppe):** MATHEFF < {median_matheff:.2f} & ANXMAT ≥ {median_anxmat:.2f}
        - **Q4 (Indifferent):** MATHEFF < {median_matheff:.2f} & ANXMAT < {median_anxmat:.2f}
        """)

    else:  # Custom
        st.warning("Custom grouping: Wähle eine Variable aus der Datenbank")
        df['Gruppe'] = 'Alle'

    # Remove missing
    df_clean = df[[dependent_var, 'Gruppe']].dropna()

    st.divider()

    # Group statistics
    st.subheader("📊 Gruppen-Statistik")

    group_stats = df_clean.groupby('Gruppe')[dependent_var].agg([
        ('N', 'count'),
        ('Mittelwert', 'mean'),
        ('SD', 'std'),
        ('Median', 'median'),
        ('Min', 'min'),
        ('Max', 'max')
    ]).round(2)

    st.dataframe(group_stats, use_container_width=True)

    # Visualization
    st.subheader("📊 Visualisierung")

    var_info = get_scale_info(dependent_var)
    var_label = var_info.get('name_de', dependent_var)

    fig = create_grouped_boxplot(
        df_clean,
        variable=dependent_var,
        group_by='Gruppe',
        title=f"{var_label} nach Gruppe",
        show_points=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Statistical test
    st.subheader("🧪 Statistischer Test")

    groups_dict = {name: group[dependent_var] for name, group in df_clean.groupby('Gruppe')}
    n_groups_actual = len(groups_dict)

    if n_groups_actual == 2:
        # T-Test
        group_names = list(groups_dict.keys())
        result = independent_ttest(
            groups_dict[group_names[0]],
            groups_dict[group_names[1]],
            equal_var=True
        )

        st.markdown(f"""
        **Independent Samples T-Test**

        - **t-Statistik:** {result['t_statistic']:.3f}
        - **p-Wert:** {result['p_value']:.4f} {'***' if result['p_value'] < 0.001 else ('**' if result['p_value'] < 0.01 else ('*' if result['p_value'] < 0.05 else 'n.s.'))}
        - **Cohen's d:** {result['cohens_d']:.3f} ({get_effect_size_interpretation(result['cohens_d'], 'cohens_d')})
        - **Signifikant:** {'✅ Ja' if result['significant'] else '❌ Nein'}

        **Mittelwerte:**
        - {group_names[0]}: M = {result['mean_g1']:.2f} (SD = {result['std_g1']:.2f}, N = {result['n_g1']})
        - {group_names[1]}: M = {result['mean_g2']:.2f} (SD = {result['std_g2']:.2f}, N = {result['n_g2']})
        """)

    elif n_groups_actual >= 3:
        # ANOVA
        from utils.statistical_analysis import one_way_anova

        result = one_way_anova(groups_dict)

        st.markdown(f"""
        **One-Way ANOVA**

        - **F-Statistik:** {result['f_statistic']:.3f}
        - **p-Wert:** {result['p_value']:.4f} {'***' if result['p_value'] < 0.001 else ('**' if result['p_value'] < 0.01 else ('*' if result['p_value'] < 0.05 else 'n.s.'))}
        - **Eta²:** {result['eta_squared']:.3f} ({get_effect_size_interpretation(result['eta_squared'], 'eta_squared')})
        - **Signifikant:** {'✅ Ja' if result['significant'] else '❌ Nein'}
        """)

        st.markdown("**Gruppen-Mittelwerte:**")
        for name, mean in result['group_means'].items():
            n = result['group_sizes'][name]
            st.markdown(f"- {name}: M = {mean:.2f} (N = {n})")

    else:
        st.warning("⚠️ Mindestens 2 Gruppen erforderlich für Vergleich.")

# ============================================
# TAB 5: STATISTISCHE TESTS
# ============================================

with tab5:
    st.header("🧪 Statistische Tests")

    st.info("""
    **Teste spezifische Hypothesen:**
    - Korrelationen mit p-Werten
    - Mittelwertvergleiche
    - Normalitätstests
    """)

    test_type = st.selectbox(
        "Test-Typ:",
        options=[
            'Korrelationstest',
            'T-Test',
            'Normalitätstest'
        ],
        index=0
    )

    st.divider()

    if test_type == 'Korrelationstest':
        st.subheader("Korrelationstest")

        available_scales = get_available_wle_scales()

        col1, col2, col3 = st.columns(3)

        with col1:
            var1 = st.selectbox(
                "Variable 1:",
                options=available_scales,
                index=0
            )

        with col2:
            var2 = st.selectbox(
                "Variable 2:",
                options=available_scales + [performance_var],
                index=len(available_scales)
            )

        with col3:
            method = st.selectbox(
                "Methode:",
                options=['pearson', 'spearman'],
                format_func=lambda x: {'pearson': 'Pearson', 'spearman': 'Spearman'}[x]
            )

        # Load and filter data
        df = load_analysis_data([var1, var2], [performance_var])
        df = filter_by_gender(df, gender_filter)
        df = filter_by_performance_level(df, performance_var, performance_level)

        df_clean = df[[var1, var2]].dropna()

        if len(df_clean) >= 3:
            r, p = correlation_with_pvalue(df_clean[var1], df_clean[var2], method=method)

            st.divider()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("N", len(df_clean))
            with col2:
                st.metric("Korrelation (r)", f"{r:.3f}")
            with col3:
                st.metric("p-Wert", f"{p:.4f}")
            with col4:
                sig = '***' if p < 0.001 else ('**' if p < 0.01 else ('*' if p < 0.05 else 'n.s.'))
                st.metric("Signifikanz", sig)

            # Interpretation
            st.markdown(f"""
            **Interpretation:**
            - Korrelation ist **{'stark' if abs(r) > 0.5 else 'mittel' if abs(r) > 0.3 else 'schwach'}**
            - Richtung: **{'positiv' if r > 0 else 'negativ'}**
            - Statistisch {'signifikant' if p < 0.05 else 'nicht signifikant'} (α = 0.05)
            """)
        else:
            st.warning("⚠️ Zu wenig Daten für Korrelationstest (min. 3 Fälle erforderlich)")

    elif test_type == 'T-Test':
        st.subheader("Independent Samples T-Test")

        st.markdown("Implementierung analog zu Tab 4 (Gruppenvergleiche)")

    elif test_type == 'Normalitätstest':
        st.subheader("Normalitätstest")

        available_scales = get_available_wle_scales()

        selected_var = st.selectbox(
            "Variable:",
            options=available_scales + [performance_var]
        )

        # Load data
        df = load_analysis_data([selected_var], [performance_var])
        df = filter_by_gender(df, gender_filter)
        df = filter_by_performance_level(df, performance_var, performance_level)

        clean_data = df[selected_var].dropna()

        if len(clean_data) >= 3:
            results = check_normality(clean_data)

            st.divider()

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                **Shapiro-Wilk Test:**
                - W = {results['shapiro_statistic']:.3f}
                - p = {results['shapiro_pvalue']:.4f}
                - Normalverteilt: **{'✅ Ja' if results['shapiro_pvalue'] > 0.05 else '❌ Nein'}**
                """)

            with col2:
                st.markdown(f"""
                **Kolmogorov-Smirnov Test:**
                - D = {results['ks_statistic']:.3f}
                - p = {results['ks_pvalue']:.4f}
                - Normalverteilt: **{'✅ Ja' if results['ks_pvalue'] > 0.05 else '❌ Nein'}**
                """)

            st.markdown(f"""
            **Gesamt-Ergebnis:** Variable ist **{'normalverteilt' if results['is_normal'] else 'nicht normalverteilt'}** (beide Tests p > 0.05)
            """)

# ============================================
# TAB 6: EXPORT
# ============================================

with tab6:
    st.header("💾 Daten-Export")

    st.info("""
    **Exportiere gefilterte Daten und Analysen:**
    - CSV für Excel/SPSS
    - Zusammenfassungen als Tabellen
    """)

    # Variable selection for export
    available_scales = get_available_wle_scales()

    export_vars = st.multiselect(
        "Variablen zum Export:",
        options=available_scales,
        default=['ANXMAT', 'MATHEFF'] if 'ANXMAT' in available_scales else []
    )

    include_performance = st.checkbox("Leistungsvariablen einbeziehen", value=True)
    include_demographics = st.checkbox("Demografische Variablen (Gender, ESCS)", value=True)

    if export_vars:
        # Load data
        df = load_analysis_data(export_vars, [performance_var])

        # Apply filters
        df = filter_by_gender(df, gender_filter)
        df = filter_by_performance_level(df, performance_var, performance_level)

        # Prepare export
        export_df = prepare_export_data(
            df,
            export_vars,
            include_performance=include_performance,
            include_demographics=include_demographics
        )

        st.divider()

        st.subheader("📊 Vorschau")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Zeilen", len(export_df))
        with col2:
            st.metric("Spalten", len(export_df.columns))
        with col3:
            st.metric("Fehlende Werte", f"{export_df.isna().sum().sum()}")

        st.dataframe(export_df.head(100), use_container_width=True)

        st.divider()

        # Download button
        csv = export_df.to_csv(index=False, encoding='utf-8')

        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"pisa_export_{performance_var}.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.success(f"✅ {len(export_df)} Zeilen bereit zum Export!")

    else:
        st.warning("⚠️ Bitte wähle mindestens eine Variable zum Export.")

# ============================================
# FOOTER
# ============================================

st.divider()

st.caption("""
📊 **Phase 4: Tiefenanalyse** | PISA 2022 Deutschland-Daten |
Statistische Tests folgen wissenschaftlichen Standards (α = 0.05)
""")
