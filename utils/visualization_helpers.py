"""
Visualization utilities for Phase 4: Tiefenanalyse

Provides reusable Plotly visualization functions for:
- Correlation heatmaps
- Scatter plots with regression lines
- Distribution plots
- Group comparisons
- Statistical annotations
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from typing import Optional, List, Dict, Tuple


# ============================================
# COLOR SCHEMES
# ============================================

PISA_COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e',
    'success': '#2ca02c',
    'danger': '#d62728',
    'warning': '#ff7f0e',
    'info': '#17a2b8',
    'sequential': 'RdYlBu_r',
    'diverging': 'RdBu',
    'categorical': px.colors.qualitative.Set2
}


# ============================================
# CORRELATION VISUALIZATIONS
# ============================================

def create_correlation_heatmap(
    corr_matrix: pd.DataFrame,
    title: str = "Korrelationsmatrix",
    annotations: bool = True,
    mask_diagonal: bool = False,
    color_scale: str = 'RdBu'
) -> go.Figure:
    """
    Create interactive correlation heatmap

    Args:
        corr_matrix: Correlation matrix (DataFrame)
        title: Plot title
        annotations: Show correlation values as text
        mask_diagonal: Hide diagonal (always 1.0)
        color_scale: Plotly color scale name

    Returns:
        Plotly Figure object
    """
    # Mask diagonal if requested
    display_matrix = corr_matrix.copy()
    if mask_diagonal:
        np.fill_diagonal(display_matrix.values, np.nan)

    # Create text annotations
    text_values = None
    if annotations:
        text_values = np.around(display_matrix.values, decimals=2)

    fig = go.Figure(data=go.Heatmap(
        z=display_matrix.values,
        x=display_matrix.columns,
        y=display_matrix.index,
        colorscale=color_scale,
        zmid=0,  # Center at 0
        zmin=-1,
        zmax=1,
        text=text_values,
        texttemplate='%{text}' if annotations else None,
        textfont={"size": 10},
        colorbar=dict(title="Korrelation")
    ))

    fig.update_layout(
        title=title,
        xaxis_title="",
        yaxis_title="",
        height=max(400, len(corr_matrix) * 40),
        width=max(600, len(corr_matrix) * 40)
    )

    return fig


def create_correlation_scatter_matrix(
    df: pd.DataFrame,
    variables: List[str],
    color_by: Optional[str] = None,
    title: str = "Scatter Matrix"
) -> go.Figure:
    """
    Create scatter matrix for multiple variables

    Args:
        df: Input DataFrame
        variables: List of variables to plot
        color_by: Optional variable for color coding
        title: Plot title

    Returns:
        Plotly Figure object
    """
    fig = px.scatter_matrix(
        df,
        dimensions=variables,
        color=color_by,
        title=title,
        height=800
    )

    fig.update_traces(diagonal_visible=False, showupperhalf=False)

    return fig


# ============================================
# SCATTER PLOTS
# ============================================

def create_scatter_with_regression(
    df: pd.DataFrame,
    x_var: str,
    y_var: str,
    title: str = "",
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    color_by: Optional[str] = None,
    add_trendline: bool = True,
    show_stats: bool = True
) -> go.Figure:
    """
    Create scatter plot with regression line and statistics

    Args:
        df: Input DataFrame
        x_var: X-axis variable name
        y_var: Y-axis variable name
        title: Plot title
        x_label: X-axis label (default: x_var)
        y_label: Y-axis label (default: y_var)
        color_by: Optional variable for color coding
        add_trendline: Add linear regression line
        show_stats: Show correlation statistics

    Returns:
        Plotly Figure object
    """
    # Remove NaN values
    plot_df = df[[x_var, y_var]].dropna()
    if color_by and color_by in df.columns:
        plot_df[color_by] = df.loc[plot_df.index, color_by]

    # Create scatter plot
    fig = px.scatter(
        plot_df,
        x=x_var,
        y=y_var,
        color=color_by,
        trendline='ols' if add_trendline else None,
        title=title,
        labels={
            x_var: x_label or x_var,
            y_var: y_label or y_var
        },
        opacity=0.6
    )

    # Calculate statistics
    if show_stats and len(plot_df) >= 3:
        corr, p_value = stats.pearsonr(plot_df[x_var], plot_df[y_var])

        # Add annotation with statistics
        fig.add_annotation(
            text=f"r = {corr:.3f}<br>p = {p_value:.4f}<br>N = {len(plot_df)}",
            xref="paper", yref="paper",
            x=0.05, y=0.95,
            showarrow=False,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1,
            font=dict(size=12)
        )

    fig.update_layout(height=500)

    return fig


def create_scatter_with_marginals(
    df: pd.DataFrame,
    x_var: str,
    y_var: str,
    marginal_type: str = 'histogram',
    color_by: Optional[str] = None,
    title: str = ""
) -> go.Figure:
    """
    Create scatter plot with marginal distributions

    Args:
        df: Input DataFrame
        x_var: X-axis variable
        y_var: Y-axis variable
        marginal_type: 'histogram', 'box', or 'violin'
        color_by: Optional color variable
        title: Plot title

    Returns:
        Plotly Figure object
    """
    fig = px.scatter(
        df,
        x=x_var,
        y=y_var,
        color=color_by,
        marginal_x=marginal_type,
        marginal_y=marginal_type,
        title=title,
        opacity=0.6
    )

    fig.update_layout(height=600)

    return fig


# ============================================
# DISTRIBUTION PLOTS
# ============================================

def create_distribution_plot(
    df: pd.DataFrame,
    variable: str,
    title: str = "",
    bins: int = 30,
    show_normal_curve: bool = True,
    show_stats: bool = True
) -> go.Figure:
    """
    Create distribution plot with histogram and optional normal curve

    Args:
        df: Input DataFrame
        variable: Variable to plot
        title: Plot title
        bins: Number of histogram bins
        show_normal_curve: Overlay normal distribution curve
        show_stats: Show descriptive statistics

    Returns:
        Plotly Figure object
    """
    clean_data = df[variable].dropna()

    fig = go.Figure()

    # Histogram
    fig.add_trace(go.Histogram(
        x=clean_data,
        nbinsx=bins,
        name='Histogram',
        opacity=0.7,
        marker_color=PISA_COLORS['primary']
    ))

    # Normal curve
    if show_normal_curve and len(clean_data) > 0:
        mean = clean_data.mean()
        std = clean_data.std()

        x_range = np.linspace(clean_data.min(), clean_data.max(), 100)
        normal_curve = stats.norm.pdf(x_range, mean, std)

        # Scale to histogram
        hist_counts, _ = np.histogram(clean_data, bins=bins)
        scale_factor = hist_counts.max() / normal_curve.max()
        normal_curve_scaled = normal_curve * scale_factor

        fig.add_trace(go.Scatter(
            x=x_range,
            y=normal_curve_scaled,
            mode='lines',
            name='Normal-Verteilung',
            line=dict(color='red', width=2)
        ))

    # Statistics annotation
    if show_stats and len(clean_data) > 0:
        stats_text = (
            f"N = {len(clean_data)}<br>"
            f"Mean = {clean_data.mean():.2f}<br>"
            f"SD = {clean_data.std():.2f}<br>"
            f"Median = {clean_data.median():.2f}"
        )

        fig.add_annotation(
            text=stats_text,
            xref="paper", yref="paper",
            x=0.95, y=0.95,
            showarrow=False,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="black",
            borderwidth=1,
            font=dict(size=11),
            align='left'
        )

    fig.update_layout(
        title=title,
        xaxis_title=variable,
        yaxis_title="Häufigkeit",
        showlegend=True,
        height=400
    )

    return fig


def create_combined_distribution_plot(
    df: pd.DataFrame,
    variable: str,
    title: str = ""
) -> go.Figure:
    """
    Create combined histogram + box plot

    Args:
        df: Input DataFrame
        variable: Variable to plot
        title: Plot title

    Returns:
        Plotly Figure object with subplots
    """
    from plotly.subplots import make_subplots

    clean_data = df[variable].dropna()

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05,
        subplot_titles=("Verteilung", "Box Plot")
    )

    # Histogram
    fig.add_trace(
        go.Histogram(x=clean_data, nbinsx=30, marker_color=PISA_COLORS['primary']),
        row=1, col=1
    )

    # Box plot
    fig.add_trace(
        go.Box(x=clean_data, marker_color=PISA_COLORS['secondary'], name=''),
        row=2, col=1
    )

    fig.update_layout(
        title_text=title,
        showlegend=False,
        height=500
    )

    fig.update_xaxes(title_text=variable, row=2, col=1)
    fig.update_yaxes(title_text="Häufigkeit", row=1, col=1)

    return fig


# ============================================
# GROUP COMPARISONS
# ============================================

def create_grouped_boxplot(
    df: pd.DataFrame,
    variable: str,
    group_by: str,
    title: str = "",
    show_points: bool = False,
    color_palette: Optional[List[str]] = None
) -> go.Figure:
    """
    Create grouped box plot

    Args:
        df: Input DataFrame
        variable: Numeric variable to plot
        group_by: Grouping variable
        title: Plot title
        show_points: Show individual data points
        color_palette: Optional custom color palette

    Returns:
        Plotly Figure object
    """
    fig = px.box(
        df,
        x=group_by,
        y=variable,
        title=title,
        color=group_by,
        color_discrete_sequence=color_palette or PISA_COLORS['categorical'],
        points='all' if show_points else False
    )

    fig.update_layout(
        showlegend=False,
        height=500
    )

    return fig


def create_grouped_violin_plot(
    df: pd.DataFrame,
    variable: str,
    group_by: str,
    title: str = "",
    show_box: bool = True
) -> go.Figure:
    """
    Create grouped violin plot

    Args:
        df: Input DataFrame
        variable: Numeric variable to plot
        group_by: Grouping variable
        title: Plot title
        show_box: Show box plot inside violin

    Returns:
        Plotly Figure object
    """
    fig = px.violin(
        df,
        x=group_by,
        y=variable,
        title=title,
        color=group_by,
        box=show_box,
        points=False,
        color_discrete_sequence=PISA_COLORS['categorical']
    )

    fig.update_layout(
        showlegend=False,
        height=500
    )

    return fig


def create_comparison_barplot(
    group_stats: pd.DataFrame,
    title: str = "",
    error_bars: bool = True
) -> go.Figure:
    """
    Create bar plot with error bars for group comparisons

    Args:
        group_stats: DataFrame with columns: group, mean, std (or sem)
        title: Plot title
        error_bars: Show error bars

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=group_stats.index if isinstance(group_stats.index, pd.Index) else group_stats['group'],
        y=group_stats['mean'],
        error_y=dict(
            type='data',
            array=group_stats['std'] if error_bars else None
        ) if error_bars else None,
        marker_color=PISA_COLORS['primary']
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Gruppe",
        yaxis_title="Mittelwert",
        height=400
    )

    return fig


# ============================================
# ADVANCED VISUALIZATIONS
# ============================================

def create_regression_residual_plot(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    title: str = "Residual Plot"
) -> go.Figure:
    """
    Create residual plot for regression diagnostics

    Args:
        y_true: True values
        y_pred: Predicted values
        title: Plot title

    Returns:
        Plotly Figure object
    """
    residuals = y_true - y_pred

    fig = go.Figure()

    # Scatter plot of residuals
    fig.add_trace(go.Scatter(
        x=y_pred,
        y=residuals,
        mode='markers',
        marker=dict(color=PISA_COLORS['primary'], opacity=0.6),
        name='Residuals'
    ))

    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color="red")

    fig.update_layout(
        title=title,
        xaxis_title="Predicted Values",
        yaxis_title="Residuals",
        height=400
    )

    return fig


def create_qq_plot(
    data: pd.Series,
    title: str = "Q-Q Plot"
) -> go.Figure:
    """
    Create Q-Q plot for normality assessment

    Args:
        data: Data series
        title: Plot title

    Returns:
        Plotly Figure object
    """
    clean_data = data.dropna()

    # Calculate theoretical quantiles
    theoretical_quantiles = stats.probplot(clean_data, dist="norm")[0][0]
    sample_quantiles = stats.probplot(clean_data, dist="norm")[0][1]

    fig = go.Figure()

    # Q-Q scatter
    fig.add_trace(go.Scatter(
        x=theoretical_quantiles,
        y=sample_quantiles,
        mode='markers',
        marker=dict(color=PISA_COLORS['primary']),
        name='Data'
    ))

    # Reference line
    min_val = min(theoretical_quantiles.min(), sample_quantiles.min())
    max_val = max(theoretical_quantiles.max(), sample_quantiles.max())
    fig.add_trace(go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode='lines',
        line=dict(color='red', dash='dash'),
        name='Normal'
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Theoretical Quantiles",
        yaxis_title="Sample Quantiles",
        height=400
    )

    return fig


def create_feature_importance_plot(
    importance_df: pd.DataFrame,
    top_n: int = 15,
    title: str = "Feature Importance"
) -> go.Figure:
    """
    Create horizontal bar chart for feature importance

    Args:
        importance_df: DataFrame with 'Feature' and 'Importance_%' columns
        top_n: Number of top features to show
        title: Plot title

    Returns:
        Plotly Figure object
    """
    plot_df = importance_df.head(top_n).copy()

    fig = px.bar(
        plot_df,
        x='Importance_%',
        y='Feature',
        orientation='h',
        title=title,
        color='Importance_%',
        color_continuous_scale='Blues',
        text='Importance_%'
    )

    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        height=max(400, top_n * 25),
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )

    return fig
