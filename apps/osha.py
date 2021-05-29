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

from script.audiometry_analysis import calculate_osha_sts

from app import app, audiometries


def analyze_osha(baseline_revision=True, age_adjustment=True):
    df_osha_result = calculate_osha_sts(
        audiometries, baseline_revision, age_adjustment)
    df_osha_graph1 = df_osha_result.value_counts(
        ["year", "sub_corp_name", "osha_sts"]).reset_index()
    df_osha_graph1.columns.values[3] = "count"
    df_osha_graph2 = df_osha_result.value_counts(
        ["year", "sub_corp_name", "osha_sts"], normalize=True).reset_index()
    df_osha_graph2.columns.values[3] = "%"
    df_osha_graph = pd.concat(
        [df_osha_graph1, df_osha_graph2["%"]], axis=1).sort_values(by=["year"])
    df_osha_graph = df_osha_graph[df_osha_graph["osha_sts"] == True]
    df_osha_graph["text"] = df_osha_graph["count"].map(
        str) + " (" + df_osha_graph["%"].map(lambda value: str(round(value * 100, 1))) + "%)"

    df_osha_graph.sort_values(by=["year", "count"], ascending=[True, False], inplace=True)

    figure_osha = px.bar(df_osha_graph, x="sub_corp_name", y="count", text="count", color="year",
                         # title="จำนวนพนักงานที่เกิด OSHA Standard Threshould Shift " + (
                         #    "ปรับ" if baseline_revision else "ไม่ปรับ") + " Baseline " + (
                         #          "ปรับ" if age_adjustment else "ไม่ปรับ") + "อายุ",
                         barmode="group", height=600,
                         labels={"count": "จำนวนพนักงาน", "sub_corp_name": "แผนก", "osha_sts": "STS"})
    figure_osha = figure_osha.update_xaxes(showgrid=True)
    # แผนก 3 ลำดับแรกท่ี่มีพนักงานเข้าเกณฑ์มากสุดในปีล่าสุด
    df_osha_latest_year = df_osha_graph[df_osha_graph["year"] == df_osha_graph["year"].unique().max()]

    df_osha_sts_patients = df_osha_result[df_osha_result["osha_sts"] == True].reset_index(drop=True).drop(
        columns=["osha_sts"]).reset_index(drop=True).sort_values(["sub_corp_name", "patient_name"])
    df_osha_sts_patients_repeated = df_osha_sts_patients.value_counts(
        ["show_hn", "title", "patient_name"]).reset_index()
    df_osha_sts_patients_repeated.columns.values[3] = "repeated"
    df_osha_sts_patients_repeated = df_osha_sts_patients_repeated.sort_values(
        ["repeated", "patient_name"], ascending=[False, True])

    return (df_osha_result, df_osha_latest_year, df_osha_sts_patients, df_osha_sts_patients_repeated, figure_osha)


figures_osha = {"+baseline+age": analyze_osha(), "+baseline-age": None, "-baseline+age": None, "-baseline-age": None}

layout = html.Div(children=[
    html.H1(
        children='OSHA Standard Threshold Shift'
    ),
    html.Label(["เลือกประเภทการวิเคราะห์",
                dcc.Dropdown(
                    id='osha-analysis-mode',
                    options=[{'label': "ไม่ปรับ Baseline ไม่ปรับอายุ", 'value': "-baseline-age"},
                             {'label': "ไม่ปรับ Baseline ปรับอายุ",
                              'value': "-baseline+age"},
                             {'label': "ปรับ Baseline ไม่ปรับอายุ",
                              'value': "+baseline-age"},
                             {'label': "ปรับ Baseline ปรับอายุ", 'value': "+baseline+age"}],
                    value="+baseline+age",
                    placeholder="เลือกว่าจะปรับ Baseline และอายุ หรือไม่"
                )]),
    dcc.Loading(
        id="osha-loading",
        type="default",
        children=[
            html.H2("กราฟแสดงจำนวนพนักงานที่เข้าเกณฑ์ OSHA STS รายปีของแต่ละแผนก"),
            dcc.Graph(
                id='figure-osha'
            ),
            html.H2(
                children='รายชื่อผู้ที่เข้าได้กับ OSHA Standard Threshold Shift'
            ),
            table.DataTable(
                id='osha-latest-year',
                columns=[{"name": "แผนก", "id": "sub_corp_name"},
                         {"name": "เปรียบเทียบระหว่าง", "id": "year"},
                         {"name": "จำนวนพนักงานที่เข้าเกณฑ์", "id": "count"}],
                export_format="xlsx",
            ),
            dcc.Tabs([
                dcc.Tab(label='ตามปีที่เปรียบเทียบ', children=[
                    table.DataTable(
                        id='osha-sts-patients',
                        columns=[{"name": "HN", "id": "show_hn"},
                                 {"name": "คำนำหน้า", "id": "title"},
                                 {"name": "ชื่อ-นามสกุล",
                                  "id": "patient_name"},
                                 {"name": "แผนก", "id": "sub_corp_name"},
                                 {"name": "เปรียบเทียบระหว่าง", "id": "year"}],
                        data=[],
                        export_format="xlsx",
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
                            id='osha-sts-repeated-patients',
                            columns=[{"name": "HN", "id": "show_hn"},
                                     {"name": "คำนำหน้า", "id": "title"},
                                     {"name": "ชื่อ-นามสกุล",
                                      "id": "patient_name"},
                                     {"name": "จำนวนครั้งของ OSHA STS", "id": "repeated"}],
                            data=[],
                            export_format="xlsx",
                            sort_action="native",
                            sort_mode="multi",
                            filter_action="native",
                            page_action="native",
                            row_selectable="single",
                            page_current=0,
                            page_size=10,
                        )
                    ])
            ])
        ]),
    html.H3(
        id='osha-sts-detail-heading',
    ),
    dcc.Loading(
        id="osha-sts-detail-loading",
        type="default",
        children=[
            html.Div(
                id='osha-sts-detail-container'
            )
        ])
])


@app.callback(
    [Output('osha-sts-detail-heading', 'children'),
     Output('osha-sts-detail-container', 'children'),
     Output('osha-sts-patients', 'selected_rows'),
     Output('osha-sts-repeated-patients', 'selected_rows')
     ],
    [Input('osha-sts-patients', "derived_virtual_data"),
     Input('osha-sts-patients', 'derived_virtual_selected_rows'),
     Input('osha-sts-repeated-patients', "derived_virtual_data"),
     Input('osha-sts-repeated-patients', 'derived_virtual_selected_rows')])
def update_osha_detail(rows, derived_virtual_selected_rows, rows_repeated, derived_virtual_selected_rows_repeated):
    def generate(rows, index):
        selected_patient = pd.DataFrame(
            rows).loc[index, :].reset_index(drop=True)
        selected_patient_audiometry = pd.merge(left=selected_patient.drop(columns=["year"]), right=(
            audiometries.drop(columns=["patient_name", "title", "sub_corp_name"])), on=["show_hn"], how="inner")

        selected_patient_audiometry["average_l"] = (selected_patient_audiometry["audio_2000_l"] +
                                                    selected_patient_audiometry["audio_3000_l"] +
                                                    selected_patient_audiometry["audio_4000_l"]) / 3
        selected_patient_audiometry["average_r"] = (selected_patient_audiometry["audio_2000_r"] +
                                                    selected_patient_audiometry["audio_3000_r"] +
                                                    selected_patient_audiometry["audio_4000_r"]) / 3
        cols = list(selected_patient_audiometry)
        # move the column to head of list using index, pop and insert
        cols.insert(0, cols.pop(cols.index('title')))
        cols.insert(6, cols.pop(cols.index('average_l')))
        cols.insert(7, cols.pop(cols.index('average_r')))
        selected_patient_audiometry = selected_patient_audiometry.loc[:, cols]
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
    if trigger_id == "osha-sts-patients":
        if derived_virtual_selected_rows is None:
            return ('เลือกคนที่ต้องการดูรายละเอียดจากตารางด้านบน', [], dash.no_update, dash.no_update)
        elif len(derived_virtual_selected_rows) == 0:
            return (dash.no_update, dash.no_update, dash.no_update, dash.no_update)
        else:
            return (*generate(rows, derived_virtual_selected_rows), derived_virtual_selected_rows, [])
    elif trigger_id == "osha-sts-repeated-patients":
        if derived_virtual_selected_rows_repeated is None:
            return ('เลือกคนที่ต้องการดูรายละเอียดจากตารางด้านบน', [], dash.no_update, dash.no_update)
        elif len(derived_virtual_selected_rows_repeated) == 0:
            return (dash.no_update, dash.no_update, dash.no_update, dash.no_update)
        else:
            return (*generate(rows_repeated, derived_virtual_selected_rows_repeated), [],
                    derived_virtual_selected_rows_repeated)
    else:
        return ('เลือกคนที่ต้องการดูรายละเอียดจากตารางด้านบน', dash.no_update, dash.no_update, dash.no_update)


@app.callback(
    [Output('figure-osha', 'figure'),
     Output('osha-sts-patients', 'data'),
     Output('osha-sts-repeated-patients', 'data'),
     Output('osha-latest-year', 'data')],
    [Input('osha-analysis-mode', 'value')])
def dash_generate_osha_graph(mode: str):
    return generate_osha_graph(mode)


def generate_osha_graph(mode: str):
    if figures_osha[mode] is not None:
        result, lastyear, df_osha_sts_patients, df_osha_sts_patients_repeated, figure = figures_osha[mode]
    else:
        if mode == "-baseline-age":
            result, lastyear, df_osha_sts_patients, df_osha_sts_patients_repeated, figure = analyze_osha(
                baseline_revision=False, age_adjustment=False)
        elif mode == "+baseline-age":
            result, lastyear, df_osha_sts_patients, df_osha_sts_patients_repeated, figure = analyze_osha(
                age_adjustment=False)
        elif mode == "-baseline+age":
            result, lastyear, df_osha_sts_patients, df_osha_sts_patients_repeated, figure = analyze_osha(
                baseline_revision=False)
        elif mode == "+baseline+age":
            result, lastyear, df_osha_sts_patients, df_osha_sts_patients_repeated, figure = analyze_osha()

    # รายชื่อผู้ที่มี OSHA STS
    figures_osha[mode] = result, lastyear, df_osha_sts_patients, df_osha_sts_patients_repeated, figure

    return (
        figure, df_osha_sts_patients.to_dict(orient='records'), df_osha_sts_patients_repeated.to_dict(orient='records'),
        lastyear.to_dict(orient='records'))


def get_osha_patients_detail(df_osha_sts_patients_repeated: pd.DataFrame):
    df_osha_patient_detail = pd.merge(left=df_osha_sts_patients_repeated, right=(
        audiometries.drop(columns=["title", "patient_name"])), on=["show_hn"], how="inner")
    cols = list(df_osha_patient_detail)
    cols.insert(0, cols.pop(cols.index('title')))
    return df_osha_patient_detail.loc[:, cols]
