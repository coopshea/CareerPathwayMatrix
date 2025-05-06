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
            
        # Get the base values for each metric
        x_base = pathway['metrics'][x_metric]['value']
        y_base = pathway['metrics'][y_metric]['value']
        
        # Add the pathway data
        x_values.append(x_base)
        y_values.append(y_base)
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
    
    # Add jitter to the data points to prevent exact overlaps
    jittered_x = []
    jittered_y = []
    
    # Create a dictionary to track positions and apply jitter only when needed
    positions = {}
    
    for i in range(len(x_values)):
        x_val = x_values[i]
        y_val = y_values[i]
        pos_key = f"{x_val},{y_val}"
        
        # Check if this position already exists
        if pos_key in positions:
            # Apply small random jitter (±0.2) to both coordinates
            jitter_x = np.random.uniform(-0.2, 0.2)
            jitter_y = np.random.uniform(-0.2, 0.2)
            jittered_x.append(x_val + jitter_x)
            jittered_y.append(y_val + jitter_y)
        else:
            # No jitter needed for first occurrence at this position
            positions[pos_key] = True
            jittered_x.append(x_val)
            jittered_y.append(y_val)
    
    # Create the figure
    fig = go.Figure()
    
    # Prepare customdata with additional information for hover
    hover_data = []
    for i in range(len(pathway_ids)):
        hover_data.append([pathway_ids[i], categories[i]])
    
    # Add the scatter plot with jittered coordinates
    fig.add_trace(go.Scatter(
        x=jittered_x,
        y=jittered_y,
        mode='markers',  # Remove text to avoid clutter, will show on hover
        marker=dict(
            size=12,
            color=colors,
            line=dict(width=1, color='black')
        ),
        text=names,
        customdata=hover_data,
        hoverinfo='text',
        hovertemplate='<b>%{text}</b><br>' +
                      f'{metrics_data[x_metric]["name"]}: %{{x:.1f}}/10<br>' +
                      f'{metrics_data[y_metric]["name"]}: %{{y:.1f}}/10<br>' +
                      'Category: %{customdata[1]}<br>' +
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
    
    # No need to update all traces as we want to keep the markers-only mode
    # for better visualization with the jitter effect
    
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
