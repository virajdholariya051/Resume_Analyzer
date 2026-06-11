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
