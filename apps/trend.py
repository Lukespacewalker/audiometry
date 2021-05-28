import pandas as pd
import numpy as np
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from app import app, audiometries

freq_list = []
for f in [500, 1000, 2000, 3000, 4000, 6000, 8000]:
    for s in ["l", "r"]:
        freq_list.append("audio_" + str(f) + "_" + s)
long = audiometries.melt(
    id_vars=["sub_corp_name", "year"], value_vars=freq_list)
long = pd.concat([long.drop("variable", inplace=False, axis=1), long["variable"].str.extract(
    "audio_(?P<freq>\d+)_(?P<side>\S+)", expand=True)], axis=1)
long["freq"] = long["freq"].astype(int)
departments_list = long["sub_corp_name"].unique()
df_audiometry_trend_graph = long.groupby(["year", "sub_corp_name"]).agg(
    np.mean).reset_index().sort_values(["year", "sub_corp_name"])
df_audiometry_trend_graph["year"] = df_audiometry_trend_graph["year"].astype(
    str)
audiometry_trend_graph = px.bar(df_audiometry_trend_graph, x="sub_corp_name", y="value", color="year",
                                title="แนวโน้มผล Audiogram ของทุกแผนก ในแต่ละปี",
                                barmode="group", height=600,
                                labels={"freq": "ความถี่", "value": "ระดับการได้ยิน", "sub_corp_name": "แผนก"})

layout = html.Div(children=[
    dcc.Store(id="audiometries",storage_type="session"),
    html.H1(
        children='ค่าเฉลี่ยของระดับการได้ยินรวมทั้งสองหูของทุกแผนกในแต่ละปี'
    ),
    dcc.Graph(
        id='audiogram-trend-graph',
        figure= audiometry_trend_graph
    ),
    html.H3(
        children='ค่าเฉลี่ยของระดับการได้ยินรวมทั้งสองหู แยกตามแผนก ในแต่ละปี'
    ),
    html.Div([
        html.Label(["แผนก",
                    dcc.Dropdown(
                        id='filter-by-department',
                        options = [{'label': i, 'value': i} for i in departments_list],
                        value = departments_list[0],
                        placeholder="เลือกแผนกที่ต้องการดู",
                    )]),
    ]),
    dcc.Graph(
        id='filtered-by-department-graph'
    )
])

@ app.callback(
    Output('filtered-by-department-graph', 'figure'),
    [Input('filter-by-department', 'value')])
def update_graph(department_name: str):
    df_audiometry_trend_bycorp_graph = long.groupby(
        ["year", "sub_corp_name", "freq"]).agg(np.mean).reset_index()
    df_audiometry_trend_bycorp_graph["year"] = df_audiometry_trend_bycorp_graph["year"].astype(
        str)
    fig = px.line(df_audiometry_trend_bycorp_graph[df_audiometry_trend_bycorp_graph["sub_corp_name"] == department_name], range_x=[250, 9000], x="freq", y="value", color="year",
                  title="แนวโน้มผล Audiogram ในแต่ละปี ของแผนก"+department_name, labels={"freq": "ความถี่", "value": "ระดับการได้ยินเฉลี่ย", "sub_corp_name": "แผนก"})
    return fig
