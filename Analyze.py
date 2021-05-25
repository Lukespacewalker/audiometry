# Import libs
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as table
from script.audiometry_analysis import calculate_niosh_sts, calculate_osha_sts
import pandas as pd
import numpy as np
import plotly
import plotly.express as px
import re
from typing import Callable
from dash.dependencies import Input, Output

plotly.offline.init_notebook_mode()
pd.set_option('display.max_colwidth', None)
pd.set_option("display.max_columns", None)
pd.set_option('display.max_rows', 600)
# Import datas

def extract_patient_name(df: pd.DataFrame):
    return pd.concat([df["patient_name"].str.extract(r"(?P<title>นาย|นาง สาว|นางสาว|นาง|.+\.|\S+\s+)(?P<patient_name>.+)", expand=True), df.drop(columns=["patient_name"], inplace=False)], axis=1)

def remove_junk_from_sub_corp_name_regex(name: str):
    result = re.search(r"^ฝ่าย(?P<corp>.+)", name)
    if result:
        return result.group("corp")
    else:
        return name

def remove_junk_from_age_regex(name: str):
    if name is float:
        return name
    result = re.search(r"(?P<age>\d+)", str(name))
    if result:
        return float(result.group("age"))
    else:
        print("Unable to convert this value : "+str(name))
        return name

def normalized_gender(gender: str):
    if gender == "M" or gender == "ชาย":
        return "Male"
    elif gender == "F" or gender == "หญิง":
        return "Female"
    elif gender == "Male" or gender == "Female":
        return gender
    else:
        print("Incorrect gender : " + gender)
        return gender


def apply_function_column(df: pd.DataFrame, col_name: str, func: Callable):
    df[col_name] = df[col_name].map(func)


audiometry58 = pd.read_excel("ผลตรวจการได้ยิน-ปี-58-63.xlsx",
                             sheet_name="58", usecols="B:T")  # Combined Title + Name
audiometry59 = pd.read_excel(
    "ผลตรวจการได้ยิน-ปี-58-63.xlsx", sheet_name="59", usecols="B:G,DA:DN")
audiometry61 = pd.read_excel(
    "ผลตรวจการได้ยิน-ปี-58-63.xlsx", sheet_name="61", usecols="B:G,I:V")
audiometry62 = pd.read_excel("ผลตรวจการได้ยิน-ปี-58-63.xlsx",
                             sheet_name="62", usecols="D:H,Q:AD")  # Combined Title + Name
audiometry63 = pd.read_excel("ผลตรวจการได้ยิน-ปี-58-63.xlsx",
                             sheet_name="63", usecols="B:H,CZ:DM")  # Combined Title + Name
# Clean
audiometry58.rename(columns={"hn": "show_hn"}, inplace=True)
audiometry63.rename(columns={"dept_name": "sub_corp_name"}, inplace=True)
audiometry58["year"] = 2558
audiometry59["year"] = 2559
audiometry61["year"] = 2561
audiometry62["year"] = 2562
audiometry63["year"] = 2563
audiometry58 = extract_patient_name(audiometry58)
audiometry62 = extract_patient_name(audiometry62)
audiometry63 = extract_patient_name(audiometry63)
# Combined
audiometries = pd.concat([audiometry58, audiometry59, audiometry61,
                         audiometry62, audiometry63], axis=0).drop(columns=["bmi", "pulse"])
apply_function_column(audiometries, "sub_corp_name",
                      remove_junk_from_sub_corp_name_regex)
apply_function_column(audiometries, "age", remove_junk_from_age_regex)
audiometries.rename(columns={"sex": "gender"}, inplace=True)
apply_function_column(audiometries, "gender", normalized_gender)

audiometries["year"] = audiometries["year"].astype("category")
audiometries.reset_index(drop=True, inplace=True)
del audiometry58, audiometry59, audiometry61, audiometry62, audiometry63

# Analysis
# NIOSH
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
    str)+" ("+df_niosh_graph["%"].map(lambda value: str(round(value*100, 1)))+"%)"

figure_niosh = px.bar(df_niosh_graph, x="sub_corp_name", y="count", color="year", text="count", title="จำนวนพนักงานที่ผลตรวจเข้าตาม NIOSH Significant Threshould Shift แยกตามแผนกและปี",
                      barmode="group", height=600, labels={"count": "จำนวนพนักงาน", "sub_corp_name": "แผนก", "niosh_sts": "STS"})
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

# OSHA

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
        str)+" ("+df_osha_graph["%"].map(lambda value: str(round(value*100, 1)))+"%)"
    figure_osha = px.bar(df_osha_graph, x="sub_corp_name", y="count", text="count", color="year", title="จำนวนพนักงานที่เกิด OSHA Standard Threshould Shift "+("ปรับ"if baseline_revision else "ไม่ปรับ")+" Baseline "+("ปรับ"if age_adjustment else "ไม่ปรับ")+"อายุ",
                         barmode="group", height=600, labels={"count": "จำนวนพนักงาน", "sub_corp_name": "แผนก", "osha_sts": "STS"})
    figure_osha = figure_osha.update_xaxes(showgrid=True)
    return(df_osha_result, figure_osha)

# Data Preparation
freq_list = []
for f in [500, 1000, 2000, 3000, 4000, 6000, 8000]:
    for s in ["l", "r"]:
        freq_list.append("audio_"+str(f)+"_"+s)
long = audiometries.melt(
    id_vars=["sub_corp_name", "year"], value_vars=freq_list)
long = pd.concat([long.drop("variable", inplace=False, axis=1), long["variable"].str.extract(
    "audio_(?P<freq>\d+)_(?P<side>\S+)", expand=True)], axis=1)
long["freq"] = long["freq"].astype(int)

df_audiometry_trend_graph = long.groupby(["year", "sub_corp_name"]).agg(
    np.mean).reset_index().sort_values(["year", "sub_corp_name"])
df_audiometry_trend_graph["year"] = df_audiometry_trend_graph["year"].astype(
    str)
audiometry_trend_graph = px.bar(df_audiometry_trend_graph, x="sub_corp_name", y="value", color="year", title="แนวโน้มผล Audiogram ของทุกแผนก ในแต่ละปี",
                                barmode="group", height=600, labels={"freq": "ความถี่", "value": "ระดับการได้ยิน", "sub_corp_name": "แผนก"})

df_audiometry_trend_bycorp_graph = long.groupby(
    ["year", "sub_corp_name", "freq"]).agg(np.mean).reset_index()
df_audiometry_trend_bycorp_graph["year"] = df_audiometry_trend_bycorp_graph["year"].astype(
    str)
# DASH Application
departments_list = long["sub_corp_name"].unique()
app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1(
        children='วิเคราะห์ผล Audiogram',
        style={
            'textAlign': 'center'
        }
    ),
    dcc.Tabs([
        dcc.Tab(label='NIOSH', children=[
                html.H2(
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
                    ]),
                ]),
        dcc.Tab(label='OSHA', children=[
            html.H2(
                children='OSHA Standard Threshould Shift'
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
                    dcc.Graph(
                        id='figure-osha'
                    ),
                    html.H2(
                        children='รายชื่อผู้ที่เข้าได้กับ OSHA Standard Threshould Shift'
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
        ]),
        dcc.Tab(label='Refer', children=[

        ]),
        dcc.Tab(label='Trend', children=[
            html.H1(
                children='ค่าเฉลี่ยของระดับการได้ยินรวมทั้งสองหูของทุกแผนกในแต่ละปี'
            ),
            dcc.Graph(
                id='audiogram-trend-graph',
                figure=audiometry_trend_graph
            ),
            html.H3(
                children='ค่าเฉลี่ยของระดับการได้ยินรวมทั้งสองหู แยกตามแผนก ในแต่ละปี'
            ),
            html.Div([
                html.Label(["แผนก",
                            dcc.Dropdown(
                                id='filter-by-department',
                                options=[{'label': i, 'value': i}
                                         for i in departments_list],
                                value=departments_list[0],
                                placeholder="เลือกแผนกที่ต้องการดู"
                            )]),
            ]),
            dcc.Graph(
                id='filtered-by-department-graph'
            )
        ]),
    ])
])


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
                freq_list.append("audio_"+str(f)+"_"+side)
            c.append(table.DataTable(
                id=selected_patient.loc[0, "show_hn"]+"-"+side,
                columns=[{"name": "ปีที่ตรวจ", "id": "year"}]+[{"name": str(hz)+" Hz", "id": "audio_"+str(hz)+"_"+side}
                                                               for hz in [500, 1000, 2000, 3000, 4000, 6000, 8000]],
                data=selected_patient_audiometry[[
                    "year"]+freq_list].to_dict(orient='records')
            ))
        htmls.append(
            html.Div(className="left-right-audiometry-container", children=c))
        return ('ดูผลการตรวจของ '+selected_patient["title"]+' '+selected_patient["patient_name"], htmls)
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
            return (*generate(rows_repeated, derived_virtual_selected_rows_repeated), [], derived_virtual_selected_rows_repeated)
    else:
        return ('เลือกคนที่ต้องการดูรายละเอียดจากตารางด้านบน', dash.no_update, dash.no_update, dash.no_update)


@app.callback(
    [Output('osha-sts-detail-heading', 'children'),
     Output('osha-sts-detail-container', 'children'),
     Output('osha-sts-patients', 'selected_rows'),
     Output('osha-sts-repeated-patients', 'selected_rows')],
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
                                                    selected_patient_audiometry["audio_3000_l"] + selected_patient_audiometry["audio_4000_l"])/3
        selected_patient_audiometry["average_r"] = (selected_patient_audiometry["audio_2000_r"] +
                                                    selected_patient_audiometry["audio_3000_r"] + selected_patient_audiometry["audio_4000_r"])/3
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
                freq_list.append("audio_"+str(f)+"_"+side)
            c.append(table.DataTable(
                id=selected_patient.loc[0, "show_hn"]+"-"+side,
                columns=[{"name": "ปีที่ตรวจ", "id": "year"}]+[{"name": str(hz)+" Hz", "id": "audio_"+str(hz)+"_"+side}
                                                               for hz in [500, 1000, 2000, 3000, 4000, 6000, 8000]],
                data=selected_patient_audiometry[[
                    "year"]+freq_list].to_dict(orient='records')
            ))
        htmls.append(
            html.Div(className="left-right-audiometry-container", children=c))
        return ('ดูผลการตรวจของ '+selected_patient["title"]+' '+selected_patient["patient_name"], htmls)
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
            return (*generate(rows_repeated, derived_virtual_selected_rows_repeated), [], derived_virtual_selected_rows_repeated)
    else:
        return ('เลือกคนที่ต้องการดูรายละเอียดจากตารางด้านบน', dash.no_update, dash.no_update, dash.no_update)





@ app.callback(
    [Output('figure-osha', 'figure'),
     Output('osha-sts-patients', 'data'),
     Output('osha-sts-repeated-patients', 'data')],
    [Input('osha-analysis-mode', 'value')])
def update_osha_graph(mode: str):
    if mode == "-baseline-age":
        result, figure = analyze_osha(
            baseline_revision=False, age_adjustment=False)
    elif mode == "+baseline-age":
        result, figure = analyze_osha(age_adjustment=False)
    elif mode == "-baseline+age":
        result, figure = analyze_osha(baseline_revision=False)
    elif mode == "+baseline+age":
        result, figure = analyze_osha()
    # รายชื่อผู้ที่มี OSHA STS
    df_osha_sts_patients = result[result["osha_sts"] == True].reset_index(drop=True).drop(
        columns=["osha_sts"]).reset_index(drop=True).sort_values(["sub_corp_name", "patient_name"])
    df_osha_sts_patients_repeated = df_osha_sts_patients.value_counts(
        ["show_hn", "title", "patient_name"]).reset_index()
    df_osha_sts_patients_repeated.columns.values[3] = "repeated"
    df_osha_sts_patients_repeated = df_osha_sts_patients_repeated.sort_values(
        ["repeated", "patient_name"], ascending=[False, True])

    return (figure, df_osha_sts_patients.to_dict(orient='records'), df_osha_sts_patients_repeated.to_dict(orient='records'))


if __name__ == '__main__':
    app.run_server(debug=True)
