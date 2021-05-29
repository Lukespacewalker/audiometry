import dash
import pandas as pd
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table as table

from script.audiometry_analysis import calculate_ent_refer

from app import app, audiometries

df_refer_result = calculate_ent_refer(audiometries)
df_refer_graph1 = df_refer_result.value_counts(
    ["year", "sub_corp_name", "refer"]).reset_index()
df_refer_graph1.columns.values[3] = "count"
df_refer_graph2 = df_refer_result.value_counts(
    ["year", "sub_corp_name", "refer"], normalize=True).reset_index()
df_refer_graph2.columns.values[3] = "%"
df_refer_graph = pd.concat([df_refer_graph1, df_refer_graph2["%"]], axis=1).sort_values(
    by=["year", "sub_corp_name"])
df_refer_graph = df_refer_graph[df_refer_graph["refer"] == True]
df_refer_graph["text"] = df_refer_graph["count"].map(
    str) + " (" + df_refer_graph["%"].map(lambda value: str(round(value * 100, 1))) + "%)"
df_refer_graph["year"] = df_refer_graph["year"].astype("category")

df_refer_graph.sort_values(by=["year", "count"], ascending=[True, False], inplace=True)

figure_refer = px.bar(df_refer_graph, x="sub_corp_name", y="count", color="year", text="count",
                      #title="พนักงานที่ต้องส่งต่อไปยังแพทย์ หู คอ จมูก",
                      barmode="group", height=600,
                      labels={"count": "จำนวนพนักงาน", "sub_corp_name": "แผนก", "refer": "ส่งต่อ"})
figure_refer = figure_refer.update_xaxes(showgrid=True)

# รายชื่อผู้ที่มี NIOSH STS
df_refer_patients = df_refer_result[df_refer_result["refer"] == True].drop(
    columns=["refer"]).reset_index(drop=True).sort_values(["sub_corp_name", "patient_name"])
df_refer_patients_repeated = df_refer_patients.value_counts(
    ["show_hn", "title", "patient_name"]).reset_index()
df_refer_patients_repeated.columns.values[3] = "repeated"
df_refer_patients_repeated = df_refer_patients_repeated.sort_values(
    ["repeated", "patient_name"], ascending=[False, True])
# แต่ละแผนก
df_refer_corp_count = df_refer_patients.value_counts(["year", "sub_corp_name"]).reset_index()
df_refer_corp_count.columns.values[2] = "count"
df_refer_corp_count.sort_values(
    ["year", "count"], ascending=[True, False], inplace=True)
df_refer_corp_count["year"] = df_refer_corp_count["year"].astype("int")
#df_refer_corp_count = df_refer_corp_count[df_refer_corp_count["year"] == df_refer_corp_count["year"].unique().max()]

# รายละเอียดผลตรวจ Audiogram ของผู้ที่เข้าเกณฑ์
df_refer_patient_detail = pd.merge(left=df_refer_patients_repeated, right=(
    audiometries.drop(columns=["title", "patient_name"])), on=["show_hn"], how="inner")
cols = list(df_refer_patient_detail)
# move the column to head of list using index, pop and insert
cols.insert(0, cols.pop(cols.index('title')))
df_refer_patient_detail = df_refer_patient_detail.loc[:, cols]

layout = html.Div(children=[html.H1(
    children='พนักงานที่ต้องส่งต่อไปยังแพทย์หู คอ จมูก'
),
    dcc.Graph(
        id='figure-refer',
        figure=figure_refer
    ),
    html.H2(children="จำนวนแผนกที่ต้องส่งไปยัง ENT ในปี " + str(df_refer_corp_count["year"].unique().max())),
    table.DataTable(
        id="refer-table",
        columns=[{"name": "แผนก", "id": "sub_corp_name"}, {"name": "จำนวนคน", "id": "count"}, {"name": "ปี", "id": "year"}],
        data=df_refer_corp_count.to_dict(orient='records'),
        export_format="xlsx",
    ),
    html.H2(
        children='รายชื่อผู้ที่ต้องส่งต่อ'
    ),
    dcc.Tabs([
        dcc.Tab(label='ตามปี', children=[
            table.DataTable(
                id='refer-patients',
                columns=[{"name": "HN", "id": "show_hn"},
                         {"name": "คำนำหน้า", "id": "title"},
                         {"name": "ชื่อ-นามสกุล",
                          "id": "patient_name"},
                         {"name": "แผนก", "id": "sub_corp_name"},
                         {"name": "ปี", "id": "year"}],
                data=df_refer_patients.to_dict(
                    orient='records'),
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
            label='ตามจำนวนครั้งที่ต้องส่ง Refer', children=[
                table.DataTable(
                    id='refer-repeated-patients',
                    columns=[{"name": "HN", "id": "show_hn"},
                             {"name": "คำนำหน้า", "id": "title"},
                             {"name": "ชื่อ-นามสกุล",
                              "id": "patient_name"},
                             {"name": "จำนวนครั้งที่ต้อง Refer", "id": "repeated"}],
                    data=df_refer_patients_repeated.to_dict(
                        orient='records'),
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
    ]),
    html.H3(
        id='refer-detail-heading',
        children=''
    ),
    dcc.Loading(
        id="refer-detail-loading",
        type="default",
        children=[
            html.Div(
                id='refer-detail-container'
            ),
        ])])


@app.callback(
    [Output('refer-detail-heading', 'children'),
     Output('refer-detail-container', 'children'),
     Output('refer-patients', 'selected_rows'),
     Output('refer-repeated-patients', 'selected_rows')],
    [Input('refer-patients', "derived_virtual_data"),
     Input('refer-patients', 'derived_virtual_selected_rows'),
     Input('refer-repeated-patients', "derived_virtual_data"),
     Input('refer-repeated-patients', 'derived_virtual_selected_rows')])
def update_styles(rows, derived_virtual_selected_rows, rows_repeated, derived_virtual_selected_rows_repeated):
    def generate(rows, index):
        selected_patient = pd.DataFrame(
            rows).loc[index, :].reset_index(drop=True)
        selected_patient_audiometry = df_refer_patient_detail[
            df_refer_patient_detail["show_hn"] == selected_patient.loc[0, "show_hn"]]
        selected_patient_audiometry.sort_values(["year"], inplace=True)
        htmls = [html.Div(className="left-right-audiometry-container",
                          children=[html.H4(children="Left"), html.H4(children="Right")])]
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
        return 'ดูผลการตรวจของ ' + selected_patient["title"] + ' ' + selected_patient["patient_name"], htmls

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "refer-patients":
        if derived_virtual_selected_rows is None:
            return 'เลือกคนที่ต้องการดูรายละเอียดจากตารางด้านบน', [], dash.no_update, dash.no_update
        elif len(derived_virtual_selected_rows) == 0:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        else:
            return *generate(rows, derived_virtual_selected_rows), derived_virtual_selected_rows, []
    elif trigger_id == "refer-repeated-patients":
        if derived_virtual_selected_rows_repeated is None:
            return 'เลือกคนที่ต้องการดูรายละเอียดจากตารางด้านบน', [], dash.no_update, dash.no_update
        elif len(derived_virtual_selected_rows_repeated) == 0:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        else:
            return (*generate(rows_repeated, derived_virtual_selected_rows_repeated), [],
                    derived_virtual_selected_rows_repeated)
    else:
        return 'เลือกคนที่ต้องการดูรายละเอียดจากตารางด้านบน', dash.no_update, dash.no_update, dash.no_update
