"""
Data filtering and preparation utilities for Phase 4: Tiefenanalyse

Provides functions for:
- Filtering data by various criteria
- Creating data subsets
- Handling missing values
- Data validation
- Export preparation
"""

import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Tuple, Any
import streamlit as st


# ============================================
# GENDER FILTERS
# ============================================

def filter_by_gender(
    df: pd.DataFrame,
    gender_filter: str = 'Alle',
    gender_col: str = 'ST004D01T'
) -> pd.DataFrame:
    """
    Filter data by gender

    Args:
        df: Input DataFrame
        gender_filter: 'Alle', 'Weiblich', 'Männlich', or 'Divers'
        gender_col: Gender column name (default: ST004D01T)

    Returns:
        Filtered DataFrame
    """
    if gender_filter == 'Alle' or gender_col not in df.columns:
        return df

    gender_mapping = {
        'Weiblich': 1,
        'Männlich': 2,
        'Divers': 3
    }

    if gender_filter in gender_mapping:
        return df[df[gender_col] == gender_mapping[gender_filter]].copy()

    return df


# ============================================
# PERFORMANCE FILTERS
# ============================================

def filter_by_performance_quantile(
    df: pd.DataFrame,
    performance_var: str = 'PV1MATH',
    quantile_range: Tuple[float, float] = (0.0, 1.0)
) -> pd.DataFrame:
    """
    Filter by performance quantile range

    Args:
        df: Input DataFrame
        performance_var: Performance variable (PV1MATH, PV1READ, PV1SCIE)
        quantile_range: (min_quantile, max_quantile), e.g., (0.25, 0.75) for IQR

    Returns:
        Filtered DataFrame
    """
    if performance_var not in df.columns:
        return df

    clean_df = df[df[performance_var].notna()].copy()

    min_val = clean_df[performance_var].quantile(quantile_range[0])
    max_val = clean_df[performance_var].quantile(quantile_range[1])

    return clean_df[
        (clean_df[performance_var] >= min_val) &
        (clean_df[performance_var] <= max_val)
    ].copy()


def filter_by_performance_level(
    df: pd.DataFrame,
    performance_var: str = 'PV1MATH',
    level: str = 'Alle'
) -> pd.DataFrame:
    """
    Filter by performance level category

    PISA Performance Levels:
    - Level 1 (Below): < 420
    - Level 2 (Basic): 420-482
    - Level 3 (Proficient): 482-545
    - Level 4 (Advanced): 545-607
    - Level 5+ (Expert): >= 607

    Args:
        df: Input DataFrame
        performance_var: Performance variable
        level: 'Alle', 'Niedrig', 'Mittel', 'Hoch'

    Returns:
        Filtered DataFrame
    """
    if level == 'Alle' or performance_var not in df.columns:
        return df

    clean_df = df[df[performance_var].notna()].copy()

    if level == 'Niedrig':  # Below proficient
        return clean_df[clean_df[performance_var] < 482].copy()
    elif level == 'Mittel':  # Proficient
        return clean_df[
            (clean_df[performance_var] >= 482) &
            (clean_df[performance_var] < 607)
        ].copy()
    elif level == 'Hoch':  # Advanced/Expert
        return clean_df[clean_df[performance_var] >= 607].copy()

    return clean_df


# ============================================
# MISSING DATA HANDLING
# ============================================

def filter_by_missing_threshold(
    df: pd.DataFrame,
    variables: List[str],
    max_missing_pct: float = 0.5
) -> pd.DataFrame:
    """
    Filter rows based on missing data threshold

    Args:
        df: Input DataFrame
        variables: Variables to check for missing values
        max_missing_pct: Maximum allowed missing percentage (0.0 to 1.0)

    Returns:
        Filtered DataFrame
    """
    if not variables:
        return df

    available_vars = [v for v in variables if v in df.columns]
    if not available_vars:
        return df

    # Calculate missing percentage per row
    missing_pct = df[available_vars].isna().mean(axis=1)

    return df[missing_pct <= max_missing_pct].copy()


def get_complete_cases(
    df: pd.DataFrame,
    variables: List[str]
) -> pd.DataFrame:
    """
    Get only complete cases (no missing values) for specified variables

    Args:
        df: Input DataFrame
        variables: Variables that must be non-missing

    Returns:
        DataFrame with complete cases only
    """
    available_vars = [v for v in variables if v in df.columns]
    if not available_vars:
        return df

    return df.dropna(subset=available_vars).copy()


def impute_missing_values(
    df: pd.DataFrame,
    variables: List[str],
    strategy: str = 'median'
) -> pd.DataFrame:
    """
    Impute missing values

    Args:
        df: Input DataFrame
        variables: Variables to impute
        strategy: 'median', 'mean', or 'mode'

    Returns:
        DataFrame with imputed values
    """
    df_imputed = df.copy()

    for var in variables:
        if var not in df.columns:
            continue

        if df_imputed[var].isna().sum() == 0:
            continue

        if strategy == 'median':
            fill_value = df_imputed[var].median()
        elif strategy == 'mean':
            fill_value = df_imputed[var].mean()
        elif strategy == 'mode':
            fill_value = df_imputed[var].mode()[0] if len(df_imputed[var].mode()) > 0 else 0
        else:
            continue

        df_imputed[var] = df_imputed[var].fillna(fill_value)

    return df_imputed


# ============================================
# VARIABLE SELECTION
# ============================================

def select_numeric_variables(
    df: pd.DataFrame,
    exclude_patterns: Optional[List[str]] = None
) -> List[str]:
    """
    Select numeric variables from DataFrame

    Args:
        df: Input DataFrame
        exclude_patterns: Patterns to exclude (e.g., ['PV', 'W_'])

    Returns:
        List of numeric variable names
    """
    numeric_vars = df.select_dtypes(include=[np.number]).columns.tolist()

    if exclude_patterns:
        numeric_vars = [
            var for var in numeric_vars
            if not any(pattern in var for pattern in exclude_patterns)
        ]

    return numeric_vars


def select_wle_scales(df: pd.DataFrame) -> List[str]:
    """
    Select only WLE scale variables from DataFrame

    Args:
        df: Input DataFrame

    Returns:
        List of WLE scale variable names
    """
    # Common WLE scale patterns
    wle_patterns = [
        'MATHEFF', 'ANXMAT', 'BELONG', 'EUDMO', 'COMPETE',
        'GFOFAIL', 'HOMEPOS', 'SCHRISK', 'RESILIENCE',
        'SWBP', 'EMOSUPS', 'ATTLNACT', 'ESCS'
    ]

    all_vars = df.columns.tolist()
    wle_vars = []

    for var in all_vars:
        # Check if variable contains any WLE pattern
        if any(pattern in var for pattern in wle_patterns):
            wle_vars.append(var)

    return sorted(wle_vars)


# ============================================
# OUTLIER DETECTION
# ============================================

def detect_outliers_iqr(
    series: pd.Series,
    multiplier: float = 1.5
) -> pd.Series:
    """
    Detect outliers using IQR method

    Args:
        series: Input Series
        multiplier: IQR multiplier (default: 1.5)

    Returns:
        Boolean Series indicating outliers
    """
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1

    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR

    return (series < lower_bound) | (series > upper_bound)


def detect_outliers_zscore(
    series: pd.Series,
    threshold: float = 3.0
) -> pd.Series:
    """
    Detect outliers using Z-score method

    Args:
        series: Input Series
        threshold: Z-score threshold (default: 3.0)

    Returns:
        Boolean Series indicating outliers
    """
    z_scores = np.abs((series - series.mean()) / series.std())
    return z_scores > threshold


def remove_outliers(
    df: pd.DataFrame,
    variables: List[str],
    method: str = 'iqr',
    **kwargs
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Remove outliers from DataFrame

    Note: PISA research standard is to NOT remove outliers.
    Use this only if explicitly required.

    Args:
        df: Input DataFrame
        variables: Variables to check for outliers
        method: 'iqr' or 'zscore'
        **kwargs: Additional arguments for outlier detection

    Returns:
        (Filtered DataFrame, Dict with outlier counts per variable)
    """
    df_clean = df.copy()
    outlier_counts = {}

    for var in variables:
        if var not in df.columns:
            continue

        if method == 'iqr':
            outliers = detect_outliers_iqr(df_clean[var], **kwargs)
        elif method == 'zscore':
            outliers = detect_outliers_zscore(df_clean[var], **kwargs)
        else:
            continue

        outlier_counts[var] = outliers.sum()
        df_clean = df_clean[~outliers].copy()

    return df_clean, outlier_counts


# ============================================
# DATA VALIDATION
# ============================================

def validate_data_quality(
    df: pd.DataFrame,
    variables: List[str]
) -> Dict[str, Any]:
    """
    Validate data quality for analysis

    Args:
        df: Input DataFrame
        variables: Variables to validate

    Returns:
        Dictionary with validation results
    """
    results = {
        'n_rows': len(df),
        'variables': {},
        'overall_quality': 'Good'
    }

    for var in variables:
        if var not in df.columns:
            results['variables'][var] = {
                'exists': False,
                'quality': 'Missing'
            }
            continue

        var_data = df[var]
        n_total = len(var_data)
        n_missing = var_data.isna().sum()
        n_valid = n_total - n_missing
        missing_pct = (n_missing / n_total * 100) if n_total > 0 else 100

        # Quality assessment
        if missing_pct > 50:
            quality = 'Poor'
        elif missing_pct > 20:
            quality = 'Fair'
        else:
            quality = 'Good'

        results['variables'][var] = {
            'exists': True,
            'n_valid': n_valid,
            'n_missing': n_missing,
            'missing_pct': missing_pct,
            'quality': quality
        }

        # Update overall quality
        if quality == 'Poor':
            results['overall_quality'] = 'Poor'
        elif quality == 'Fair' and results['overall_quality'] != 'Poor':
            results['overall_quality'] = 'Fair'

    return results


# ============================================
# GROUPING FUNCTIONS
# ============================================

def create_performance_groups(
    df: pd.DataFrame,
    performance_var: str = 'PV1MATH',
    n_groups: int = 3,
    labels: Optional[List[str]] = None
) -> pd.Series:
    """
    Create performance groups using quantiles

    Args:
        df: Input DataFrame
        performance_var: Performance variable
        n_groups: Number of groups (default: 3 for low/medium/high)
        labels: Optional group labels

    Returns:
        Series with group labels
    """
    if performance_var not in df.columns:
        return pd.Series(index=df.index, dtype='category')

    if labels is None:
        if n_groups == 3:
            labels = ['Niedrig', 'Mittel', 'Hoch']
        elif n_groups == 4:
            labels = ['Sehr Niedrig', 'Niedrig', 'Mittel', 'Hoch']
        elif n_groups == 5:
            labels = ['Sehr Niedrig', 'Niedrig', 'Mittel', 'Hoch', 'Sehr Hoch']
        else:
            labels = [f'Gruppe {i+1}' for i in range(n_groups)]

    return pd.qcut(
        df[performance_var],
        q=n_groups,
        labels=labels,
        duplicates='drop'
    )


def create_binary_groups(
    df: pd.DataFrame,
    variable: str,
    threshold: Optional[float] = None,
    above_label: str = 'Hoch',
    below_label: str = 'Niedrig'
) -> pd.Series:
    """
    Create binary groups based on threshold

    Args:
        df: Input DataFrame
        variable: Variable to split
        threshold: Split threshold (default: median)
        above_label: Label for values above threshold
        below_label: Label for values below threshold

    Returns:
        Series with binary labels
    """
    if variable not in df.columns:
        return pd.Series(index=df.index, dtype='category')

    if threshold is None:
        threshold = df[variable].median()

    return pd.Series(
        np.where(df[variable] >= threshold, above_label, below_label),
        index=df.index,
        dtype='category'
    )


# ============================================
# EXPORT PREPARATION
# ============================================

def prepare_export_data(
    df: pd.DataFrame,
    variables: List[str],
    include_performance: bool = True,
    include_demographics: bool = True
) -> pd.DataFrame:
    """
    Prepare data for export (CSV/Excel)

    Args:
        df: Input DataFrame
        variables: Main variables to export
        include_performance: Include performance variables
        include_demographics: Include demographic variables

    Returns:
        Cleaned DataFrame ready for export
    """
    export_vars = list(variables)

    if include_performance:
        perf_vars = ['PV1MATH', 'PV1READ', 'PV1SCIE']
        export_vars.extend([v for v in perf_vars if v in df.columns])

    if include_demographics:
        demo_vars = ['ST004D01T', 'ESCS', 'HOMEPOS']
        export_vars.extend([v for v in demo_vars if v in df.columns])

    # Remove duplicates
    export_vars = list(dict.fromkeys(export_vars))

    # Filter to available variables
    export_vars = [v for v in export_vars if v in df.columns]

    return df[export_vars].copy()


def create_summary_statistics(
    df: pd.DataFrame,
    variables: List[str],
    group_by: Optional[str] = None
) -> pd.DataFrame:
    """
    Create summary statistics table for export

    Args:
        df: Input DataFrame
        variables: Variables to summarize
        group_by: Optional grouping variable

    Returns:
        DataFrame with summary statistics
    """
    if group_by and group_by in df.columns:
        summary = df.groupby(group_by)[variables].agg([
            ('N', 'count'),
            ('Mean', 'mean'),
            ('SD', 'std'),
            ('Median', 'median'),
            ('Min', 'min'),
            ('Max', 'max')
        ]).round(2)
    else:
        summary = df[variables].agg([
            ('N', 'count'),
            ('Mean', 'mean'),
            ('SD', 'std'),
            ('Median', 'median'),
            ('Min', 'min'),
            ('Max', 'max')
        ]).T.round(2)

    return summary


# ============================================
# STREAMLIT UI HELPERS
# ============================================

def create_filter_ui(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create Streamlit sidebar UI for data filtering

    Args:
        df: Input DataFrame

    Returns:
        Dictionary with filter settings
    """
    st.sidebar.subheader("🔍 Daten-Filter")

    filters = {}

    # Gender filter
    filters['gender'] = st.sidebar.selectbox(
        "Geschlecht:",
        options=['Alle', 'Weiblich', 'Männlich', 'Divers'],
        index=0
    )

    # Performance filter
    filters['performance_level'] = st.sidebar.selectbox(
        "Leistungsniveau:",
        options=['Alle', 'Niedrig', 'Mittel', 'Hoch'],
        index=0
    )

    # Missing data handling
    filters['missing_strategy'] = st.sidebar.selectbox(
        "Fehlende Werte:",
        options=['Nur vollständige Fälle', 'Median-Imputation', 'Alle Fälle'],
        index=0
    )

    # Outlier handling
    filters['remove_outliers'] = st.sidebar.checkbox(
        "Ausreißer entfernen (nicht empfohlen)",
        value=False,
        help="PISA-Standard: Ausreißer NICHT entfernen"
    )

    return filters


def apply_filters(
    df: pd.DataFrame,
    filters: Dict[str, Any],
    variables: List[str],
    performance_var: str = 'PV1MATH'
) -> pd.DataFrame:
    """
    Apply filters to DataFrame

    Args:
        df: Input DataFrame
        filters: Filter settings from create_filter_ui()
        variables: Variables needed for analysis
        performance_var: Performance variable to use

    Returns:
        Filtered DataFrame
    """
    df_filtered = df.copy()

    # Apply gender filter
    df_filtered = filter_by_gender(df_filtered, filters['gender'])

    # Apply performance filter
    df_filtered = filter_by_performance_level(
        df_filtered,
        performance_var,
        filters['performance_level']
    )

    # Handle missing values
    if filters['missing_strategy'] == 'Nur vollständige Fälle':
        df_filtered = get_complete_cases(df_filtered, variables)
    elif filters['missing_strategy'] == 'Median-Imputation':
        df_filtered = impute_missing_values(df_filtered, variables, strategy='median')

    # Remove outliers (if requested)
    if filters.get('remove_outliers', False):
        df_filtered, _ = remove_outliers(df_filtered, variables, method='iqr')

    return df_filtered
