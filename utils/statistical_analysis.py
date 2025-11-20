"""
Statistical analysis utilities for Phase 4: Tiefenanalyse

Provides functions for:
- Correlation analysis
- Statistical tests (t-tests, ANOVA)
- Effect size calculations
- Normality testing
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Dict, List, Optional


def compute_correlation_matrix(
    df: pd.DataFrame,
    method: str = 'pearson',
    min_periods: int = 30
) -> pd.DataFrame:
    """
    Compute correlation matrix

    Args:
        df: Input dataframe with numeric columns
        method: 'pearson', 'spearman', or 'kendall'
        min_periods: Minimum observations required

    Returns:
        Correlation matrix as DataFrame
    """
    return df.corr(method=method, min_periods=min_periods)


def correlation_with_pvalue(
    x: pd.Series,
    y: pd.Series,
    method: str = 'pearson'
) -> Tuple[float, float]:
    """
    Compute correlation coefficient and p-value

    Args:
        x: First variable
        y: Second variable
        method: 'pearson', 'spearman', or 'kendall'

    Returns:
        (correlation_coefficient, p_value)
    """
    # Remove NaN values
    mask = ~(x.isna() | y.isna())
    x_clean = x[mask]
    y_clean = y[mask]

    if len(x_clean) < 3:
        return (np.nan, np.nan)

    if method == 'pearson':
        return stats.pearsonr(x_clean, y_clean)
    elif method == 'spearman':
        return stats.spearmanr(x_clean, y_clean)
    elif method == 'kendall':
        return stats.kendalltau(x_clean, y_clean)
    else:
        raise ValueError(f"Unknown method: {method}")


def cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size for two groups

    Cohen's d interpretation:
    - 0.2: small effect
    - 0.5: medium effect
    - 0.8: large effect

    Args:
        group1: First group data
        group2: Second group data

    Returns:
        Cohen's d value
    """
    n1, n2 = len(group1), len(group2)

    if n1 < 2 or n2 < 2:
        return np.nan

    var1 = np.var(group1, ddof=1)
    var2 = np.var(group2, ddof=1)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))

    if pooled_std == 0:
        return np.nan

    return (np.mean(group1) - np.mean(group2)) / pooled_std


def eta_squared(groups: List[np.ndarray]) -> float:
    """
    Calculate eta-squared effect size for ANOVA

    Eta-squared interpretation:
    - 0.01: small effect
    - 0.06: medium effect
    - 0.14: large effect

    Args:
        groups: List of group data arrays

    Returns:
        Eta-squared value
    """
    # Flatten all groups
    all_data = np.concatenate(groups)
    grand_mean = np.mean(all_data)

    # Sum of squares between groups
    ss_between = sum([
        len(g) * (np.mean(g) - grand_mean)**2
        for g in groups
    ])

    # Total sum of squares
    ss_total = sum([(x - grand_mean)**2 for x in all_data])

    if ss_total == 0:
        return np.nan

    return ss_between / ss_total


def check_normality(data: pd.Series) -> Dict[str, any]:
    """
    Check normality assumptions using multiple tests

    Args:
        data: Series to test for normality

    Returns:
        Dictionary with test results
    """
    clean_data = data.dropna()

    if len(clean_data) < 3:
        return {
            'shapiro_statistic': np.nan,
            'shapiro_pvalue': np.nan,
            'ks_statistic': np.nan,
            'ks_pvalue': np.nan,
            'is_normal': False,
            'n': len(clean_data)
        }

    # Shapiro-Wilk test (best for n < 5000)
    shapiro_stat, shapiro_p = stats.shapiro(clean_data)

    # Kolmogorov-Smirnov test
    # Standardize data for KS test
    standardized = (clean_data - clean_data.mean()) / clean_data.std()
    ks_stat, ks_p = stats.kstest(standardized, 'norm')

    return {
        'shapiro_statistic': shapiro_stat,
        'shapiro_pvalue': shapiro_p,
        'ks_statistic': ks_stat,
        'ks_pvalue': ks_p,
        'is_normal': shapiro_p > 0.05 and ks_p > 0.05,
        'n': len(clean_data)
    }


def independent_ttest(
    group1: pd.Series,
    group2: pd.Series,
    equal_var: bool = True
) -> Dict[str, any]:
    """
    Perform independent samples t-test with effect size

    Args:
        group1: First group data
        group2: Second group data
        equal_var: Assume equal variances (True = Student's t-test, False = Welch's t-test)

    Returns:
        Dictionary with test results
    """
    g1 = group1.dropna().values
    g2 = group2.dropna().values

    if len(g1) < 2 or len(g2) < 2:
        return {
            't_statistic': np.nan,
            'p_value': np.nan,
            'cohens_d': np.nan,
            'mean_g1': np.nan,
            'mean_g2': np.nan,
            'std_g1': np.nan,
            'std_g2': np.nan,
            'n_g1': len(g1),
            'n_g2': len(g2),
            'significant': False
        }

    t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=equal_var)
    d = cohens_d(g1, g2)

    return {
        't_statistic': t_stat,
        'p_value': p_val,
        'cohens_d': d,
        'mean_g1': np.mean(g1),
        'mean_g2': np.mean(g2),
        'std_g1': np.std(g1, ddof=1),
        'std_g2': np.std(g2, ddof=1),
        'n_g1': len(g1),
        'n_g2': len(g2),
        'significant': p_val < 0.05
    }


def one_way_anova(groups: Dict[str, pd.Series]) -> Dict[str, any]:
    """
    Perform one-way ANOVA with effect size

    Args:
        groups: Dictionary mapping group names to Series

    Returns:
        Dictionary with test results
    """
    # Convert to arrays and remove NaN
    group_arrays = [g.dropna().values for g in groups.values()]
    group_names = list(groups.keys())

    # Check minimum requirements
    if len(group_arrays) < 2:
        return {
            'f_statistic': np.nan,
            'p_value': np.nan,
            'eta_squared': np.nan,
            'group_means': {},
            'significant': False
        }

    if any(len(g) < 2 for g in group_arrays):
        return {
            'f_statistic': np.nan,
            'p_value': np.nan,
            'eta_squared': np.nan,
            'group_means': {name: np.mean(arr) if len(arr) > 0 else np.nan
                           for name, arr in zip(group_names, group_arrays)},
            'significant': False
        }

    # Perform ANOVA
    f_stat, p_val = stats.f_oneway(*group_arrays)
    eta2 = eta_squared(group_arrays)

    # Calculate group means
    group_means = {
        name: np.mean(arr)
        for name, arr in zip(group_names, group_arrays)
    }

    return {
        'f_statistic': f_stat,
        'p_value': p_val,
        'eta_squared': eta2,
        'group_means': group_means,
        'group_sizes': {name: len(arr) for name, arr in zip(group_names, group_arrays)},
        'significant': p_val < 0.05
    }


def levene_test(groups: Dict[str, pd.Series]) -> Dict[str, any]:
    """
    Perform Levene's test for homogeneity of variances

    Tests whether groups have equal variances (assumption for ANOVA)

    Args:
        groups: Dictionary mapping group names to Series

    Returns:
        Dictionary with test results
    """
    group_arrays = [g.dropna().values for g in groups.values()]

    if len(group_arrays) < 2 or any(len(g) < 2 for g in group_arrays):
        return {
            'statistic': np.nan,
            'p_value': np.nan,
            'equal_variances': False
        }

    stat, p_val = stats.levene(*group_arrays)

    return {
        'statistic': stat,
        'p_value': p_val,
        'equal_variances': p_val > 0.05
    }


def tukey_hsd(groups: Dict[str, pd.Series]) -> Optional[pd.DataFrame]:
    """
    Perform Tukey's HSD post-hoc test

    Note: Requires statsmodels package

    Args:
        groups: Dictionary mapping group names to Series

    Returns:
        DataFrame with pairwise comparisons or None if statsmodels not available
    """
    try:
        from statsmodels.stats.multicomp import pairwise_tukeyhsd
    except ImportError:
        return None

    # Prepare data for Tukey HSD
    all_data = []
    all_groups = []

    for group_name, data in groups.items():
        clean_data = data.dropna()
        all_data.extend(clean_data.values)
        all_groups.extend([group_name] * len(clean_data))

    if len(set(all_groups)) < 2:
        return None

    # Perform Tukey HSD
    tukey_result = pairwise_tukeyhsd(all_data, all_groups, alpha=0.05)

    # Convert to DataFrame
    result_df = pd.DataFrame({
        'Group 1': tukey_result.groupsunique[tukey_result._results_table.data[1:, 0].astype(int)],
        'Group 2': tukey_result.groupsunique[tukey_result._results_table.data[1:, 1].astype(int)],
        'Mean Diff': tukey_result._results_table.data[1:, 2],
        'Lower CI': tukey_result._results_table.data[1:, 3],
        'Upper CI': tukey_result._results_table.data[1:, 4],
        'p-value': tukey_result._results_table.data[1:, 5],
        'Reject': tukey_result._results_table.data[1:, 6]
    })

    return result_df


def get_effect_size_interpretation(value: float, measure: str = 'cohens_d') -> str:
    """
    Get interpretation of effect size

    Args:
        value: Effect size value
        measure: 'cohens_d' or 'eta_squared'

    Returns:
        Interpretation string
    """
    if np.isnan(value):
        return "N/A"

    abs_value = abs(value)

    if measure == 'cohens_d':
        if abs_value < 0.2:
            return "Negligible"
        elif abs_value < 0.5:
            return "Small"
        elif abs_value < 0.8:
            return "Medium"
        else:
            return "Large"

    elif measure == 'eta_squared':
        if abs_value < 0.01:
            return "Negligible"
        elif abs_value < 0.06:
            return "Small"
        elif abs_value < 0.14:
            return "Medium"
        else:
            return "Large"

    return "Unknown"
