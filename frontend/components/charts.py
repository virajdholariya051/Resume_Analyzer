"""
Visualization components using Plotly for dashboard charts.
"""

import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Tuple


def create_skill_distribution_chart(skills: List[Tuple[str, int]]) -> go.Figure:
    """
    Create a bar chart showing skill distribution.
    
    Args:
        skills: List of (skill_name, count) tuples.
    
    Returns:
        Plotly figure object.
    """
    if not skills:
        fig = go.Figure()
        fig.add_annotation(text="No skills data available", showarrow=False, font_size=16)
        return fig

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
    return fig


def create_ats_score_gauge(score: int) -> go.Figure:
    """
    Create a gauge chart for ATS score.
    
    Args:
        score: ATS score (0-100).
    
    Returns:
        Plotly figure object.
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
    return fig


def create_job_match_chart(match_data: Dict) -> go.Figure:
    """
    Create a radar chart showing job match components.
    
    Args:
        match_data: Dictionary with component scores.
    
    Returns:
        Plotly figure object.
    """
    components = match_data.get("component_scores", {})
    if not components:
        fig = go.Figure()
        fig.add_annotation(text="No match data available", showarrow=False, font_size=16)
        return fig

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
    return fig


def create_analysis_history_chart(analyses: List[Dict]) -> go.Figure:
    """
    Create a line chart showing analysis history trend.
    
    Args:
        analyses: List of analysis result dictionaries.
    
    Returns:
        Plotly figure object.
    """
    if not analyses:
        fig = go.Figure()
        fig.add_annotation(text="No analysis history", showarrow=False, font_size=16)
        return fig

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
    return fig


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
    return fig


def create_score_distribution_chart(scores: List[int], title: str, color: str = "#1f77b4") -> go.Figure:
    """
    Create a histogram showing the distribution of scores.

    Args:
        scores: List of numeric scores (0-100).
        title: Chart title.
        color: Bar color.

    Returns:
        Plotly figure object.
    """
    if not scores:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False, font_size=16)
        fig.update_layout(title=title, height=350)
        return fig

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
    return fig


def create_candidate_ranking_chart(ranked: List[Dict], top_n: int = 10) -> go.Figure:
    """
    Create a horizontal bar chart of top candidates by overall rank score.

    Args:
        ranked: List of ranked candidate dicts (must include candidate_name, rank_score).
        top_n: How many top candidates to display.

    Returns:
        Plotly figure object.
    """
    if not ranked:
        fig = go.Figure()
        fig.add_annotation(text="No ranked candidates yet", showarrow=False, font_size=16)
        fig.update_layout(title="Candidate Ranking", height=400)
        return fig

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
    return fig


def create_status_pie_chart(status_counts: Dict[str, int]) -> go.Figure:
    """Create a pie chart of candidate status distribution."""
    labels = list(status_counts.keys())
    values = list(status_counts.values())

    if sum(values) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No candidates yet", showarrow=False, font_size=16)
        fig.update_layout(title="Candidate Status", height=350)
        return fig

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=["#6c757d", "#ffc107", "#28a745", "#dc3545"]),
    ))
    fig.update_layout(title="Candidate Status Distribution", height=350)
    return fig


def create_time_series_chart(labels: List[str], values: List[int], title: str,
                             y_title: str = "Count", color: str = "#1f77b4",
                             fill: bool = True) -> go.Figure:
    """
    Create an interactive time-series line chart.

    Args:
        labels: X-axis labels (dates).
        values: Y-axis values.
        title: Chart title.
        y_title: Y-axis label.
        color: Line color.
        fill: Whether to fill under the line.

    Returns:
        Plotly figure object.
    """
    if not labels:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False, font_size=16)
        fig.update_layout(title=title, height=350)
        return fig

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
    return fig


def create_horizontal_bar_chart(pairs: List[Tuple[str, int]], title: str,
                                 color: str = "#667eea") -> go.Figure:
    """Create a horizontal bar chart from (label, value) pairs."""
    if not pairs:
        fig = go.Figure()
        fig.add_annotation(text="No data available", showarrow=False, font_size=16)
        fig.update_layout(title=title, height=350)
        return fig

    pairs = list(pairs)[::-1]  # largest on top
    labels = [p[0] for p in pairs]
    values = [p[1] for p in pairs]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=values, colorscale="Viridis"),
        text=values, textposition="auto",
    ))
    fig.update_layout(title=title, height=max(350, len(pairs) * 28))
    return fig
