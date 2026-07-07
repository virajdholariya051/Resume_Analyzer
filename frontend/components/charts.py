"""
Visualization components using Plotly for dashboard charts.

All charts produced here are *read-only*: interactive editing tools (zoom, pan,
box/lasso select, drawing, axis editing, legend/annotation editing and
double-click reset) are disabled globally. Hover tooltips, responsive resizing
and an optional "download as PNG" button are preserved.

Use ``STATIC_CHART_CONFIG`` for every ``st.plotly_chart(...)`` call so all
charts behave consistently across the application.
"""

import logging
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Tuple

logger = logging.getLogger("resume_analyzer.charts")


# ---------------------------------------------------------------------------
# Global, consistent read-only Plotly configuration
# ---------------------------------------------------------------------------
# Passed as ``config=STATIC_CHART_CONFIG`` to every st.plotly_chart call.
#
# Disabled : editing mode, dragging, zoom, pan, box/lasso select, drawing
#            tools, shape editing, axis editing, chart config editing,
#            double-click reset and scroll zoom.
# Enabled  : hover tooltips, responsive resizing and (optionally) downloading
#            the chart as a PNG image.
STATIC_CHART_CONFIG: Dict = {
    "staticPlot": False,          # keep hover tooltips alive
    "editable": False,            # no title / axis / annotation editing
    "scrollZoom": False,          # no scroll-wheel zoom
    "doubleClick": False,         # no double-click reset/zoom
    "showTips": False,            # no "double click to zoom" hints
    "displaylogo": False,         # hide the Plotly logo
    "responsive": True,           # responsive resizing
    "showAxisDragHandles": False,
    "showAxisRangeEntryBoxes": False,
    "displayModeBar": True,       # show a minimal modebar...
    # ...containing only the optional "download as PNG" button.
    "modeBarButtons": [["toImage"]],
    "toImageButtonOptions": {"format": "png", "filename": "chart"},
}


def _apply_readonly_layout(fig: go.Figure) -> go.Figure:
    """Lock a figure so it renders as a read-only visualization.

    Disables drag-based interactions (zoom/pan/select), fixes axis ranges and
    turns off legend click toggling, while leaving hover tooltips intact.

    Args:
        fig: The Plotly figure to lock.

    Returns:
        The same figure, mutated in place, for convenient chaining.
    """
    try:
        fig.update_layout(
            dragmode=False,
            legend=dict(itemclick=False, itemdoubleclick=False),
        )
        # fixedrange disables zoom on cartesian axes. This is a no-op for
        # figures without cartesian axes (pie/polar), so it is always safe.
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)
    except Exception:  # pragma: no cover - never let styling break a chart
        logger.debug("Could not fully apply read-only layout to figure.", exc_info=True)
    return fig


def _empty_figure(message: str, title: str = "", height: int = 350) -> go.Figure:
    """Build a locked, empty placeholder figure with a centered message."""
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font_size=16)
    if title:
        fig.update_layout(title=title, height=height)
    else:
        fig.update_layout(height=height)
    return _apply_readonly_layout(fig)


def create_skill_distribution_chart(skills: List[Tuple[str, int]]) -> go.Figure:
    """
    Create a bar chart showing skill distribution.

    Args:
        skills: List of (skill_name, count) tuples.

    Returns:
        Read-only Plotly figure object.
    """
    if not skills:
        return _empty_figure("No skills data available", height=400)

    names = [s[0] for s in skills]
    counts = [s[1] for s in skills]

    fig = px.bar(
        x=names, y=counts,
        labels={"x": "Skills", "y": "Frequency"},
        title="Most Common Skills",
        color=counts,
        color_continuous_scale="viridis",
    )
    fig.update_layout(
        showlegend=False,
        xaxis_tickangle=-45,
        height=400,
    )
    return _apply_readonly_layout(fig)


def create_ats_score_gauge(score: int) -> go.Figure:
    """
    Create a gauge chart for ATS score.

    Args:
        score: ATS score (0-100).

    Returns:
        Read-only Plotly figure object.
    """
    color = "#28a745" if score >= 70 else "#ffc107" if score >= 50 else "#dc3545"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "ATS Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 40], "color": "#ffcccc"},
                {"range": [40, 70], "color": "#fff3cd"},
                {"range": [70, 100], "color": "#d4edda"},
            ],
            "threshold": {
                "line": {"color": "black", "width": 4},
                "thickness": 0.75,
                "value": score,
            },
        },
    ))
    fig.update_layout(height=300)
    return _apply_readonly_layout(fig)


def create_quality_score_gauge(score: int) -> go.Figure:
    """
    Create a gauge chart for the overall resume quality score.

    Args:
        score: Resume quality score (0-100).

    Returns:
        Read-only Plotly figure object.
    """
    color = "#28a745" if score >= 70 else "#ffc107" if score >= 50 else "#dc3545"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Resume Quality"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 40], "color": "#ffe5d0"},
                {"range": [40, 70], "color": "#e2e3f3"},
                {"range": [70, 100], "color": "#d4edda"},
            ],
        },
    ))
    fig.update_layout(height=300)
    return _apply_readonly_layout(fig)


def create_job_match_chart(match_data: Dict) -> go.Figure:
    """
    Create a radar chart showing job match components.

    Args:
        match_data: Dictionary with component scores.

    Returns:
        Read-only Plotly figure object.
    """
    components = match_data.get("component_scores", {})
    if not components:
        return _empty_figure("No match data available", height=400)

    categories = [k.replace("_", " ").title() for k in components.keys()]
    values = list(components.values())
    # Close the radar chart
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure(go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        name="Match Score",
        line_color="#667eea",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="Job Match Breakdown",
        height=400,
    )
    return _apply_readonly_layout(fig)


def create_analysis_history_chart(analyses: List[Dict]) -> go.Figure:
    """
    Create a line chart showing analysis history trend.

    Args:
        analyses: List of analysis result dictionaries.

    Returns:
        Read-only Plotly figure object.
    """
    if not analyses:
        return _empty_figure("No analysis history", height=350)

    dates = [a.get("created_at", "N/A") for a in analyses]
    ats_scores = [a.get("ats_score", 0) for a in analyses]
    match_scores = [a.get("job_match_percentage", 0) for a in analyses]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=ats_scores,
        mode="lines+markers",
        name="ATS Score",
        line=dict(color="#1f77b4", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=match_scores,
        mode="lines+markers",
        name="Job Match %",
        line=dict(color="#ff7f0e", width=2),
    ))
    fig.update_layout(
        title="Analysis Score Trends",
        xaxis_title="Date",
        yaxis_title="Score",
        yaxis=dict(range=[0, 100]),
        height=350,
    )
    return _apply_readonly_layout(fig)


def create_score_comparison_chart(ats_score: int, match_score: int) -> go.Figure:
    """Create a comparison bar chart for ATS and match scores."""
    fig = go.Figure(go.Bar(
        x=["ATS Score", "Job Match %"],
        y=[ats_score, match_score],
        marker_color=["#1f77b4", "#ff7f0e"],
        text=[f"{ats_score}%", f"{match_score}%"],
        textposition="auto",
    ))
    fig.update_layout(
        title="Score Comparison",
        yaxis=dict(range=[0, 100]),
        height=300,
    )
    return _apply_readonly_layout(fig)


def create_score_distribution_chart(scores: List[int], title: str, color: str = "#1f77b4") -> go.Figure:
    """
    Create a histogram showing the distribution of scores.

    Args:
        scores: List of numeric scores (0-100).
        title: Chart title.
        color: Bar color.

    Returns:
        Read-only Plotly figure object.
    """
    if not scores:
        return _empty_figure("No data available", title=title, height=350)

    fig = go.Figure(go.Histogram(
        x=scores,
        nbinsx=10,
        marker_color=color,
        opacity=0.85,
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Score",
        yaxis_title="Number of Candidates",
        xaxis=dict(range=[0, 100]),
        bargap=0.05,
        height=350,
    )
    return _apply_readonly_layout(fig)


def create_candidate_ranking_chart(ranked: List[Dict], top_n: int = 10) -> go.Figure:
    """
    Create a horizontal bar chart of top candidates by overall rank score.

    Args:
        ranked: List of ranked candidate dicts (must include candidate_name, rank_score).
        top_n: How many top candidates to display.

    Returns:
        Read-only Plotly figure object.
    """
    if not ranked:
        return _empty_figure("No ranked candidates yet", title="Candidate Ranking", height=400)

    top = ranked[:top_n][::-1]  # reverse so #1 is at the top
    names = [f"#{c.get('rank', i + 1)} {c['candidate_name']}" for i, c in enumerate(top[::-1])][::-1]
    scores = [c["rank_score"] for c in top]

    fig = go.Figure(go.Bar(
        x=scores,
        y=names,
        orientation="h",
        marker=dict(color=scores, colorscale="Blues"),
        text=[f"{s:.1f}" for s in scores],
        textposition="auto",
    ))
    fig.update_layout(
        title=f"Top {min(top_n, len(ranked))} Candidates (Overall Score)",
        xaxis_title="Overall Ranking Score",
        xaxis=dict(range=[0, 100]),
        height=max(400, len(top) * 35),
    )
    return _apply_readonly_layout(fig)


def create_status_pie_chart(status_counts: Dict[str, int]) -> go.Figure:
    """Create a pie chart of candidate status distribution."""
    labels = list(status_counts.keys())
    values = list(status_counts.values())

    if sum(values) == 0:
        return _empty_figure("No candidates yet", title="Candidate Status", height=350)

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=["#6c757d", "#ffc107", "#28a745", "#dc3545"]),
    ))
    fig.update_layout(title="Candidate Status Distribution", height=350)
    return _apply_readonly_layout(fig)


def create_pie_chart(data: Dict[str, int], title: str) -> go.Figure:
    """Create a generic read-only donut/pie chart from a label -> value mapping."""
    labels = list(data.keys())
    values = list(data.values())

    if sum(values) == 0:
        return _empty_figure("No data available", title=title, height=350)

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=["#1f77b4", "#16a34a", "#ff7f0e", "#9b59b6", "#dc3545"]),
    ))
    fig.update_layout(title=title, height=350)
    return _apply_readonly_layout(fig)


def create_time_series_chart(labels: List[str], values: List[int], title: str,
                             y_title: str = "Count", color: str = "#1f77b4",
                             fill: bool = True) -> go.Figure:
    """
    Create a read-only time-series line chart.

    Args:
        labels: X-axis labels (dates).
        values: Y-axis values.
        title: Chart title.
        y_title: Y-axis label.
        color: Line color.
        fill: Whether to fill under the line.

    Returns:
        Read-only Plotly figure object.
    """
    if not labels:
        return _empty_figure("No data available", title=title, height=350)

    fig = go.Figure(go.Scatter(
        x=labels,
        y=values,
        mode="lines+markers",
        line=dict(color=color, width=2),
        fill="tozeroy" if fill else None,
        fillcolor="rgba(31,119,180,0.1)" if fill else None,
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=y_title,
        height=350,
        hovermode="x unified",
    )
    return _apply_readonly_layout(fig)


def create_horizontal_bar_chart(pairs: List[Tuple[str, int]], title: str,
                                 color: str = "#667eea") -> go.Figure:
    """Create a horizontal bar chart from (label, value) pairs."""
    if not pairs:
        return _empty_figure("No data available", title=title, height=350)

    pairs = list(pairs)[::-1]  # largest on top
    labels = [p[0] for p in pairs]
    values = [p[1] for p in pairs]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=values, colorscale="Viridis"),
        text=values, textposition="auto",
    ))
    fig.update_layout(title=title, height=max(350, len(pairs) * 28))
    return _apply_readonly_layout(fig)
