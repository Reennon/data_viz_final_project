#%%
# Define Imports
import os
import googlemaps
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import pydeck as pdk
from dash import Dash, dcc, html
from dotenv import load_dotenv
import numpy as np
import requests
import dash_deck
import dash
from dash import Output, Input
#%%
# Load ENV variables
load_dotenv(dotenv_path='../.env')
#%%
# Read Golden Submissions Dataset
submissions_golden_df = pd.read_csv("../data/submissions_golden.csv")
#%%
# Read Raw Submissions Dataset (Needed for a time-line plot)
submissions_raw_df = pd.read_csv("../data/submissions.csv")
submissions_raw_df = submissions_raw_df.dropna()
submissions_raw_df.loc[:, 'submission_date'] = pd.to_datetime(submissions_raw_df.loc[:, 'submission_date'])
#%%
# Define a tooltip for map
tooltip = {
    'html': '<b>Initiator Region:</b> {initiator_region}<br>'
            '<b>{tooltip_title}:</b> {tooltip_category}<br>'
            '<b>Number of Submissions:</b> {number_of_submissions}',
    'style': {
        'color': 'white',
        'z-index': 99
    }
}
#%%
# Define plot parameters
BARPLOT_HEIGHT: int = 400
LINEPLOT_HEIGHT: int = 300
PYDECK_STATUS_MAP_COLOR_MAP: dict = {
    'approval': [72, 143, 49],
    'active': [142, 174, 84],
    'pending': [202, 205, 128],
    'withdrawn': [247, 188, 125],
    'unsuccessful': [239, 131, 95],
    'declined': [222, 66, 91],
}
# Transform rgb list which PyDeck use to RGB format for plotly
# Henceforth, we stay consistent and easy to update
PLOTLY_STATUS_BARPLOT_COLOR_MAP: dict = {
    k: f"rgb({r}, {g}, {b})" for k, (r, g, b) in PYDECK_STATUS_MAP_COLOR_MAP.items()
}
PYDECK_ITEM_CLASSIFICATION_COLOR_MAP: dict = {
    'kitchen': [124, 198, 116],
    'shelter': [115, 197, 197]
}
PLOTLY_ITEM_CLASSIFICATION_COLOR_MAP: dict = {
    k: f"rgb({r}, {g}, {b})" for k, (r, g, b) in PYDECK_ITEM_CLASSIFICATION_COLOR_MAP.items()
}
#%%
# Add GeoJSON layer to visualize admin units
geojson_url = "https://github.com/wmgeolab/geoBoundaries/raw/905b0ba/releaseData/gbOpen/UKR/ADM1/geoBoundaries-UKR-ADM1_simplified.geojson"
response = requests.get(geojson_url)
ukraine_geojson = response.json()

geojson_layer = pdk.Layer(
    'GeoJsonLayer',
    data=ukraine_geojson,
    stroked=True,
    filled=True,
    get_line_color=[255, 255, 255],
    get_line_width=1000,
    get_fill_color=[0, 0, 0, 20],
    wireframe=True,
    extruded=False,
)
#%%
# Prepare a placeholders for a map
# Set the viewport location
view_state = pdk.ViewState(
    latitude=submissions_golden_df['latitude'].mean(),
    longitude=submissions_golden_df['longitude'].mean() + 4,
    zoom=5,
    pitch=33
)
# Create the initial Deck object
initial_deck = pdk.Deck(
    layers=[geojson_layer],
    initial_view_state=view_state,
    tooltip=tooltip,
    map_style='mapbox://styles/mapbox/dark-v10',
)

# Create the DeckGL component
deck_component = dash_deck.DeckGL(
    initial_deck.to_json(),
    id='deck-gl',
    tooltip=tooltip,
    mapboxKey=os.getenv("MAPBOX_API_KEY"),
    style={"height": '42.5vh', "position": 'relative'}
)
#%%
# Prepare Bar Plot and Annotations
# Create the bar plot
status_counts = submissions_golden_df.loc[:,
                    'submission_status'
                ].value_counts(
                ).reset_index()
status_counts.columns = ['submission_status', 'count']
status_fig = px.bar(
    status_counts,
    x='submission_status',
    y='count',
    title='Distribution of Submissions by Status',
    labels={
        'submission_status': 'Submission Status',
        'count': 'Count'
    },
    color='submission_status',
    color_discrete_map=PLOTLY_STATUS_BARPLOT_COLOR_MAP,
    height=BARPLOT_HEIGHT,
    template='plotly_dark',
)
status_fig.update_layout(
    legend_title_text='Submission Status',
    legend=dict(
        x=1.05,
        y=1,
        traceorder='normal',
        bgcolor='rgba(255, 255, 255, 0)',
        bordercolor='rgba(255, 255, 255, 0)'
    ),
    margin=dict(r=150),
    font=dict(
        family="Helvetica",
        size=14,
        color="white"
    )
)
#%%
# Prepare Bar Plot for Item Classification
item_classification_counts = submissions_golden_df['item_classification'].value_counts().reset_index()
item_classification_counts.columns = ['item_classification', 'count']

# Create the bar plot
item_classification_fig = px.bar(
    item_classification_counts,
    x='item_classification',
    y='count',
    title='Distribution of Submissions by Item Classification',
    labels={
        'item_classification': 'Item Classification',
        'count': 'Count'
    },
    color='item_classification',
    color_discrete_map={
        'kitchen': 'rgb(124, 198, 116)',
        'shelter': 'rgb(115, 197, 197)'
    },
    height=BARPLOT_HEIGHT,
    template='plotly_dark',
)

item_classification_fig.update_layout(
    legend_title_text='Item Classification',
    legend=dict(
        x=1.05,
        y=1,
        traceorder='normal',
        bgcolor='rgba(255, 255, 255, 0)',
        bordercolor='rgba(255, 255, 255, 0)'
    ),
    margin=dict(r=150),
    font=dict(
        family="Helvetica",
        size=14,
        color="white"
    )
)
#%%
# Create time-series figure
time_series_fig = px.line(
    submissions_raw_df.groupby(pd.Grouper(key='submission_date', freq='D')).size().reset_index(name='count'),
    x='submission_date',
    y='count',
    title='Number of Daily Submissions',
    height=LINEPLOT_HEIGHT,
    markers=True,
    labels={
        'submission_date': 'Submission Date',
        'count': 'Count'
    },
    template='plotly_dark',
)
time_series_fig.data[0].line.color = 'skyblue'
#%%
# Create Annotations section
annotations_section_status = html.Div([
    html.H3("Annotations", style={'font-weight': 'bold'}),
    html.P("This plot shows the distribution of submissions by status for financing educational facilities. "
           "The data is provided by the DREAM API. Below are the categories of submission status with their respective colors:"),
    html.Ul([
        html.Li([html.Span("■ ", style={'color': PLOTLY_STATUS_BARPLOT_COLOR_MAP["approval"]}), "Approval - Submission has been approved."]),
        html.Li([html.Span("■ ", style={'color': PLOTLY_STATUS_BARPLOT_COLOR_MAP["active"]}), "Active - Submission is currently active."]),
        html.Li([html.Span("■ ", style={'color': PLOTLY_STATUS_BARPLOT_COLOR_MAP["pending"]}), "Pending - Submission is awaiting review."]),
        html.Li([html.Span("■ ", style={'color': PLOTLY_STATUS_BARPLOT_COLOR_MAP["withdrawn"]}), "Withdrawn - Submission was withdrawn by the applicant."]),
        html.Li([html.Span("■ ", style={'color': PLOTLY_STATUS_BARPLOT_COLOR_MAP["unsuccessful"]}), "Unsuccessful - Submission was not successful."]),
        html.Li([html.Span("■ ", style={'color': PLOTLY_STATUS_BARPLOT_COLOR_MAP["declined"]}), "Declined - Submission was declined."])
    ], style={'list-style-type': 'none', 'padding-left': '20px'}),
    html.Div([
    html.P("Moreover, we split the submissions by two groups as a gradation: from more successful, and green, like active (", style={'display': 'inline'}),
    html.Span('■', style={'color': PLOTLY_STATUS_BARPLOT_COLOR_MAP['approval'], 'display': 'inline'}),
    html.P(") to more red, as for example declined: (", style={'display': 'inline'}),
    html.Span('■', style={'color': PLOTLY_STATUS_BARPLOT_COLOR_MAP['declined'], 'display': 'inline'}),
    html.P(")", style={'display': 'inline'})
]),
], style={'color': 'white', 'font-family': 'Arial', 'font-size': '14px', 'padding': '20px', 'background-color': 'black', 'position': 'relative'})
annotations_section_classification = html.Div([
    html.H3("Annotations", style={'font-weight': 'bold'}),
    html.P("This plot shows the distribution of submissions by type for financing educational facilities. "
           "The data is provided by the DREAM API. Below are the categories of submission type with their respective colors:"),
    html.Ul([
        html.Li([html.Span("■ ", style={'color': PLOTLY_ITEM_CLASSIFICATION_COLOR_MAP["kitchen"]}), "Kitchen - Submission for kitchen facilities."]),
        html.Li([html.Span("■ ", style={'color': PLOTLY_ITEM_CLASSIFICATION_COLOR_MAP["shelter"]}), "Shelter - Submission for shelter facilities."])
    ], style={'list-style-type': 'none', 'padding-left': '20px'}),
], style={'color': 'white', 'font-family': 'Arial', 'font-size': '14px', 'padding': '20px', 'background-color': 'black', 'position': 'relative'})

#%%
def adjust_color(color, alpha=50):
    """Adjust alpha of given color."""

    return color[:3] + [alpha]

# Create the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define App Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("DREAM Dashboard"),
                html.H3("Submissions Grouped by Region"),
                html.Hr(),
            ], style={'background-color': 'black', 'color': 'white', 'padding-left': '20px', 'padding-top': '10px'}),
        ], md=12),
        dbc.Col([
            html.Div([
                html.H4("Select Group By Option:", style={"color": "white"}),
                dcc.Dropdown(
                    id='groupby-dropdown',
                    options=[
                        {'label': 'Item Classification', 'value': 'item_classification'},
                        {'label': 'Submission Status', 'value': 'submission_status'},
                    ],
                    value='item_classification',
                    clearable=False,
                ),
            ], style={'background-color': 'black', 'color': 'black', 'padding-left': '20px'}),
            # Annotations
            html.Div(id='annotations-container'),
        ], md=5),
        dbc.Col([
            # BarPlot
            dcc.Graph(id='barplot'),
        ], md=7),
        dbc.Col([
            html.Div(
                deck_component,
            )
        ], md=12),
        dbc.Col([
            # Time-Series Selector
            dcc.Graph(figure=time_series_fig),
        ], md=12),
    ])
], fluid=True, style={"background-color": "black"})

@app.callback(
    [Output('annotations-container', 'children'),
     Output('barplot', 'figure')],
    [Input('groupby-dropdown', 'value')]
)
def update_layout(group_by):
    if group_by == 'item_classification':
        annotations = annotations_section_classification

        # Prepare Bar Plot for Item Classification
        item_classification_counts = submissions_golden_df['item_classification'].value_counts().reset_index()
        item_classification_counts.columns = ['item_classification', 'count']

        # Create the bar plot
        fig = px.bar(
            item_classification_counts,
            x='item_classification',
            y='count',
            title='Distribution of Submissions by Item Classification',
            labels={
                'item_classification': 'Item Classification',
                'count': 'Count'
            },
            color='item_classification',
            color_discrete_map={
                'kitchen': 'rgb(124, 198, 116)',
                'shelter': 'rgb(115, 197, 197)'
            },
            height=BARPLOT_HEIGHT,
            template='plotly_dark',
        )
        fig.update_layout(
            legend_title_text='Item Classification',
            legend=dict(
                x=1.05,
                y=1,
                traceorder='normal',
                bgcolor='rgba(255, 255, 255, 0)',
                bordercolor='rgba(255, 255, 255, 0)'
            ),
            margin=dict(r=150),
            font=dict(
                family="Helvetica",
                size=14,
                color="white"
            )
        )

    elif group_by == 'submission_status':
        annotations = annotations_section_status

        # Prepare Bar Plot for Submission Status
        status_counts = submissions_golden_df['submission_status'].value_counts().reset_index()
        status_counts.columns = ['submission_status', 'count']

        # Create the bar plot
        fig = px.bar(
            status_counts,
            x='submission_status',
            y='count',
            title='Distribution of Submissions by Status',
            labels={
                'submission_status': 'Submission Status',
                'count': 'Count'
            },
            color='submission_status',
            color_discrete_map=PLOTLY_STATUS_BARPLOT_COLOR_MAP,
            height=BARPLOT_HEIGHT,
            template='plotly_dark',
        )
        fig.update_layout(
            legend_title_text='Submission Status',
            legend=dict(
                x=1.05,
                y=1,
                traceorder='normal',
                bgcolor='rgba(255, 255, 255, 0)',
                bordercolor='rgba(255, 255, 255, 0)'
            ),
            margin=dict(r=150),
            font=dict(
                family="Helvetica",
                size=14,
                color="white"
            )
        )

    return annotations, fig

@app.callback(
Output('deck-gl', 'data'),
Input('groupby-dropdown', 'value')
)
def update_map(group_by):
    if group_by == 'item_classification':
        lat_col = f'latitude_grid_{group_by}'
        long_col = f'longitude_grid_{group_by}'
        grouped_df = submissions_golden_df.groupby(
            ['initiator_region', group_by],
            as_index=False
        ).agg({
            'number_of_submissions': 'count',
            lat_col: 'first',
            long_col: 'first',
        })
        color_map = PYDECK_ITEM_CLASSIFICATION_COLOR_MAP
        grouped_df['color'] = grouped_df.apply(
            lambda row: adjust_color(
                color_map[row['item_classification']],
                alpha=75
            ) if row['number_of_submissions'] == 0 else color_map[row['item_classification']],
            axis=1
        )

    elif group_by == 'submission_status':
        lat_col = f'latitude_grid_{group_by}'
        long_col = f'longitude_grid_{group_by}'
        grouped_df = submissions_golden_df.groupby(
            ['initiator_region', group_by],
            as_index=False
        ).agg({
            'number_of_submissions': 'count',
            lat_col: 'first',
            long_col: 'first',
        })
        color_map = PYDECK_STATUS_MAP_COLOR_MAP
        grouped_df['color'] = grouped_df.apply(
            lambda row: adjust_color(
                color_map[row['submission_status']],
                alpha=75
            ) if row['number_of_submissions'] == 0 else color_map[row['submission_status']],
            axis=1
        )

    grouped_df = grouped_df.loc[:, [
        "initiator_region",
        "number_of_submissions",
        "color",
        lat_col,
        long_col
    ] + [group_by]].dropna()
    grouped_df.loc[:, "tooltip_title"] = group_by.replace("_", " ").title()
    grouped_df.loc[:, "tooltip_category"] = grouped_df.loc[:, group_by].str.title()

    # Create the layer
    layer = pdk.Layer(
        'ColumnLayer',
        elevation_scale=5000,
        data=grouped_df,
        get_position=[long_col, lat_col],
        get_fill_color='color',
        get_elevation="number_of_submissions",
        radius=800,
        radius_scale=3000,
        radius_min_pixels=1,
        radius_max_pixels=500,
        pickable=True,
        auto_highlight=True,
        extruded=True,
        coverage=7,
        elevation_range=[0, 5000],
        tooltip=tooltip,
    )

    deck = pdk.Deck(
        layers=[layer, geojson_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style='mapbox://styles/mapbox/dark-v10',
    )

    return deck.to_json()

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
