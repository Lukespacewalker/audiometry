import pandas as pd
import numpy as np
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
import dash_table as table
from dash.dependencies import Input, Output, State

from app import app
from apps.niosh import figure_niosh
from apps.osha import figures_osha
from apps.refer import figure_refer, df_refer_patients

_, figure_osha = figures_osha["+baseline+age"]


df_refer_corp_count = df_refer_patients.value_counts(["year", "sub_corp_name"]).reset_index()
df_refer_corp_count.columns.values[2] = "count"
df_refer_corp_count.sort_values(
    ["year", "count"],ascending=[True,False] ,inplace=True)
df_refer_corp_count["year"] = df_refer_corp_count["year"].astype("int")
df_refer_corp_count = df_refer_corp_count[df_refer_corp_count["year"]==df_refer_corp_count["year"].unique().max()]

layout = html.Div(children=[
    html.H1(children="สรุปผลการตรวจการได้ยินของโรงพยาบาลจุฬาลงกรณ์ ปี 2558 - 2563"),
    html.H2(children="NIOSH Significant Threshold Shift"),
    dcc.Graph(figure=figure_niosh),
    html.H3(children="OSHA Standard Threshold Shift"),
    html.P(children="คำนวนโดยปรับ Baseline และปรับตามอายุ"),
    dcc.Graph(figure=figure_osha),
    html.H2(children="ส่งต่อไปยัง ENT"),
    dcc.Graph(figure=figure_refer),
    html.H3(children="จำนวนแผนกที่ต้องส่งไปยัง ENT ในปี "+str(df_refer_corp_count["year"].unique().max())),
    table.DataTable(
        id="refer-table",
        columns=[{"name": "แผนก","id": "sub_corp_name"},{"name": "จำนวนคน","id": "count"}],
        data=df_refer_corp_count.to_dict(orient='records')
    )
])
