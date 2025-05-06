import plotly.graph_objects as go
import numpy as np
import pandas as pd
import streamlit as st

def create_matrix_visualization(pathways_df, x_metric, y_metric, metrics_data):
    """
    Create a 2x2 matrix visualization for the pathways.
    
    Args:
        pathways_df (DataFrame): The pathways dataframe
        x_metric (str): The metric to use for the x-axis
        y_metric (str): The metric to use for the y-axis
        metrics_data (dict): Information about the metrics
        
    Returns:
        go.Figure: The plotly figure object
    """
    # Extract the metrics values for each pathway
    x_values = []
    y_values = []
    names = []
    categories = []
    pathway_ids = []
    
    for _, pathway in pathways_df.iterrows():
        # Skip pathways that don't have the required metrics
        if x_metric not in pathway['metrics'] or y_metric not in pathway['metrics']:
            continue
            
        x_values.append(pathway['metrics'][x_metric]['value'])
        y_values.append(pathway['metrics'][y_metric]['value'])
        names.append(pathway['name'])
        categories.append(pathway['category'])
        pathway_ids.append(pathway['id'])
    
    # Create a color map for categories
    category_colors = {
        "Tech & Software": "#4C78A8",
        "Materials & Energy": "#72B7B2",
        "Education": "#54A24B",
        "3D & Manufacturing": "#EECA3B",
        "Content & Media": "#F58518",
        "Finance & Investment": "#E45756",
        "Traditional Professions": "#B279A2",
        "Retail & Consumer": "#FF9DA6",
        "Health & Wellness": "#9D755D"
    }
    
    colors = [category_colors.get(cat, "#000000") for cat in categories]
    
    # Create the figure
    fig = go.Figure()
    
    # Add the scatter plot
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='markers+text',
        marker=dict(
            size=12,
            color=colors,
            line=dict(width=1, color='black')
        ),
        text=names,
        textposition="top center",
        textfont=dict(size=10),
        customdata=pathway_ids,
        hovertemplate='<b>%{text}</b><br>' +
                      f'{metrics_data[x_metric]["name"]}: %{{x}}/10<br>' +
                      f'{metrics_data[y_metric]["name"]}: %{{y}}/10<br>' +
                      'Category: %{marker.color}<br>' +
                      '<extra></extra>'
    ))
    
    # Add quadrant lines
    fig.add_shape(
        type="line",
        x0=5.5, y0=0, x1=5.5, y1=10,
        line=dict(color="gray", width=1, dash="dot")
    )
    fig.add_shape(
        type="line",
        x0=0, y0=5.5, x1=10, y1=5.5,
        line=dict(color="gray", width=1, dash="dot")
    )
    
    # Add quadrant labels
    fig.add_annotation(
        x=2.75, y=7.75,
        text=f"Low {metrics_data[x_metric]['name']}<br>High {metrics_data[y_metric]['name']}",
        showarrow=False,
        font=dict(size=10)
    )
    fig.add_annotation(
        x=8.25, y=7.75,
        text=f"High {metrics_data[x_metric]['name']}<br>High {metrics_data[y_metric]['name']}",
        showarrow=False,
        font=dict(size=10)
    )
    fig.add_annotation(
        x=2.75, y=2.75,
        text=f"Low {metrics_data[x_metric]['name']}<br>Low {metrics_data[y_metric]['name']}",
        showarrow=False,
        font=dict(size=10)
    )
    fig.add_annotation(
        x=8.25, y=2.75,
        text=f"High {metrics_data[x_metric]['name']}<br>Low {metrics_data[y_metric]['name']}",
        showarrow=False,
        font=dict(size=10)
    )
    
    # Configure the layout
    fig.update_layout(
        xaxis=dict(
            title=f"{metrics_data[x_metric]['name']} ({metrics_data[x_metric]['low_label']} → {metrics_data[x_metric]['high_label']})",
            range=[0, 11],
            tickmode='linear',
            tick0=0,
            dtick=1
        ),
        yaxis=dict(
            title=f"{metrics_data[y_metric]['name']} ({metrics_data[y_metric]['low_label']} → {metrics_data[y_metric]['high_label']})",
            range=[0, 11],
            tickmode='linear',
            tick0=0,
            dtick=1
        ),
        height=600,
        margin=dict(l=50, r=50, t=30, b=50),
        hovermode='closest',
        showlegend=False
    )
    
    # Add legend for categories
    for category, color in category_colors.items():
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=10, color=color),
            name=category,
            showlegend=True
        ))
    
    # Configure click events
    fig.update_layout(clickmode='event')
    
    # Add a callback for clicking on a pathway
    fig.update_traces(
        mode='markers+text',
        marker=dict(size=12),
        textposition="top center"
    )
    
    # Configure the config for downloads
    config = {
        'displayModeBar': True,
        'toImageButtonOptions': {
            'format': 'png',
            'filename': 'career_pathways_matrix',
            'scale': 2
        }
    }
    
    # Return the figure and attach the click event handler
    return fig
