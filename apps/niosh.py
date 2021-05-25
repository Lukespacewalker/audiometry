from dash.exceptions import PreventUpdate
import dash
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table as table

from script.audiometry_analysis import calculate_niosh_sts

from app import app, audiometries

df_niosh_result = calculate_niosh_sts(audiometries)
df_niosh_graph1 = df_niosh_result.value_counts(
    ["year", "sub_corp_name", "niosh_sts"]).reset_index()
df_niosh_graph1.columns.values[3] = "count"
df_niosh_graph2 = df_niosh_result.value_counts(
    ["year", "sub_corp_name", "niosh_sts"], normalize=True).reset_index()
df_niosh_graph2.columns.values[3] = "%"
df_niosh_graph = pd.concat([df_niosh_graph1, df_niosh_graph2["%"]], axis=1).sort_values(
    by=["year", "sub_corp_name"])
df_niosh_graph = df_niosh_graph[df_niosh_graph["niosh_sts"] == True]
df_niosh_graph["text"] = df_niosh_graph["count"].map(
    str) + " (" + df_niosh_graph["%"].map(lambda value: str(round(value * 100, 1))) + "%)"

figure_niosh = px.bar(df_niosh_graph, x="sub_corp_name", y="count", color="year", text="count",
                      title="จำนวนพนักงานที่ผลตรวจเข้าตาม NIOSH Significant Threshould Shift แยกตามแผนกและปี",
                      barmode="group", height=600,
                      labels={"count": "จำนวนพนักงาน", "sub_corp_name": "แผนก", "niosh_sts": "STS"})
figure_niosh = figure_niosh.update_xaxes(showgrid=True)
# รายชื่อผู้ที่มี NIOSH STS
df_niosh_sts_patients = df_niosh_result[df_niosh_result["niosh_sts"] == True].drop(
    columns=["niosh_sts"]).reset_index(drop=True).sort_values(["sub_corp_name", "patient_name"])
df_niosh_sts_patients_repeated = df_niosh_sts_patients.value_counts(
    ["show_hn", "title", "patient_name"]).reset_index()
df_niosh_sts_patients_repeated.columns.values[3] = "repeated"
df_niosh_sts_patients_repeated = df_niosh_sts_patients_repeated.sort_values(
    ["repeated", "patient_name"], ascending=[False, True])
# รายละเอียดผลตรวจ Audiogram ของผู้ที่เข้าเกณฑ์
df_niosh_patient_detail = pd.merge(left=df_niosh_sts_patients_repeated, right=(
    audiometries.drop(columns=["title", "patient_name"])), on=["show_hn"], how="inner")
cols = list(df_niosh_patient_detail)
# move the column to head of list using index, pop and insert
cols.insert(0, cols.pop(cols.index('title')))
df_niosh_patient_detail = df_niosh_patient_detail.loc[:, cols]

layout = html.Div(children=[html.H2(
    children='NIOSH Significant Threshould Shift'
),
    dcc.Graph(
        id='figure-niosh',
        figure=figure_niosh
    ),
    html.H2(
        children='รายชื่อผู้ที่เข้าได้กับ NIOSH Significant Threshould Shift'
    ),
    dcc.Tabs([
        dcc.Tab(label='ตามปีที่เปรียบเทียบ', children=[
            table.DataTable(
                id='niosh-sts-patients',
                columns=[{"name": "HN", "id": "show_hn"},
                         {"name": "คำนำหน้า", "id": "title"},
                         {"name": "ชื่อ-นามสกุล",
                          "id": "patient_name"},
                         {"name": "แผนก", "id": "sub_corp_name"},
                         {"name": "เปรียบเทียบระหว่าง", "id": "year"}],
                data=df_niosh_sts_patients.to_dict(
                    orient='records'),
                sort_action="native",
                sort_mode="multi",
                filter_action="native",
                page_action="native",
                row_selectable="single",
                page_current=0,
                page_size=10,
            )
        ]),
        dcc.Tab(
            label='ตามจำนวนครั้งที่เข้าได้', children=[
                table.DataTable(
                    id='niosh-sts-repeated-patients',
                    columns=[{"name": "HN", "id": "show_hn"},
                             {"name": "คำนำหน้า", "id": "title"},
                             {"name": "ชื่อ-นามสกุล",
                              "id": "patient_name"},
                             {"name": "จำนวนครั้งของ NIOSH STS", "id": "repeated"}],
                    data=df_niosh_sts_patients_repeated.to_dict(
                        orient='records'),
                    sort_action="native",
                    sort_mode="multi",
                    filter_action="native",
                    page_action="native",
                    row_selectable="single",
                    page_current=0,
                    page_size=10,
                )
            ]),
    ]),
    html.H3(
        id='niosh-sts-detail-heading',
        children=''
    ),
    dcc.Loading(
        id="niosh-sts-detail-loading",
        type="default",
        children=[
            html.Div(
                id='niosh-sts-detail-container'
            ),
        ])])


@app.callback(
    [Output('niosh-sts-detail-heading', 'children'),
     Output('niosh-sts-detail-container', 'children'),
     Output('niosh-sts-patients', 'selected_rows'),
     Output('niosh-sts-repeated-patients', 'selected_rows')],
    [Input('niosh-sts-patients', "derived_virtual_data"),
     Input('niosh-sts-patients', 'derived_virtual_selected_rows'),
     Input('niosh-sts-repeated-patients', "derived_virtual_data"),
     Input('niosh-sts-repeated-patients', 'derived_virtual_selected_rows')])
def update_styles(rows, derived_virtual_selected_rows, rows_repeated, derived_virtual_selected_rows_repeated):
    def generate(rows, index):
        selected_patient = pd.DataFrame(
            rows).loc[index, :].reset_index(drop=True)
        selected_patient_audiometry = df_niosh_patient_detail[
            df_niosh_patient_detail["show_hn"] == selected_patient.loc[0, "show_hn"]]
        selected_patient_audiometry.sort_values(["year"], inplace=True)
        htmls = []
        htmls.append(html.Div(className="left-right-audiometry-container",
                              children=[html.H4(children="Left"), html.H4(children="Right")]))
        c = []
        for side in ["l", "r"]:
            freq_list = []
            for f in [500, 1000, 2000, 3000, 4000, 6000, 8000]:
                freq_list.append("audio_" + str(f) + "_" + side)
            c.append(table.DataTable(
                id=selected_patient.loc[0, "show_hn"] + "-" + side,
                columns=[{"name": "ปีที่ตรวจ", "id": "year"}] + [
                    {"name": str(hz) + " Hz", "id": "audio_" + str(hz) + "_" + side}
                    for hz in [500, 1000, 2000, 3000, 4000, 6000, 8000]],
                data=selected_patient_audiometry[[
                                                     "year"] + freq_list].to_dict(orient='records')
            ))
        htmls.append(
            html.Div(className="left-right-audiometry-container", children=c))
        return ('ดูผลการตรวจของ ' + selected_patient["title"] + ' ' + selected_patient["patient_name"], htmls)

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "niosh-sts-patients":
        if derived_virtual_selected_rows is None:
            return ('เลือกคนที่ต้องการดูรายละเอียดจากตารางด้านบน', [], dash.no_update, dash.no_update)
        elif len(derived_virtual_selected_rows) == 0:
            return (dash.no_update, dash.no_update, dash.no_update, dash.no_update)
        else:
            return (*generate(rows, derived_virtual_selected_rows), derived_virtual_selected_rows, [])
    elif trigger_id == "niosh-sts-repeated-patients":
        if derived_virtual_selected_rows_repeated is None:
            return ('เลือกคนที่ต้องการดูรายละเอียดจากตารางด้านบน', [], dash.no_update, dash.no_update)
        elif len(derived_virtual_selected_rows_repeated) == 0:
            return (dash.no_update, dash.no_update, dash.no_update, dash.no_update)
        else:
            return (*generate(rows_repeated, derived_virtual_selected_rows_repeated), [],
                    derived_virtual_selected_rows_repeated)
    else:
        return ('เลือกคนที่ต้องการดูรายละเอียดจากตารางด้านบน', dash.no_update, dash.no_update, dash.no_update)
