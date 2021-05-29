import pandas as pd
import numpy as np
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
import dash_table as table
from flask import send_file
import io
from dash.dependencies import Input, Output, State

from app import app
from apps.niosh import figure_niosh, df_niosh_patient_detail, df_niosh_latest_year, df_niosh_sts_patients
from apps.osha import figures_osha, get_osha_patients_detail
from apps.refer import figure_refer, df_refer_corp_count, df_refer_patient_detail, df_refer_patients

_, df_osha_lastyear, df_osha_sts_patients, df_osha_sts_patients_repeated, figure_osha = figures_osha["+baseline+age"]


@app.server.route('/download_excel/')
def download_excel():
    # Convert DF
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df_osha_lastyear.drop(["%", "text"], axis=1).to_excel(excel_writer, sheet_name="แผนกที่เข้า OSHA STS ปีล่าสุด")
    df_niosh_latest_year.drop(["%", "text"], axis=1).to_excel(excel_writer, sheet_name="แผนกที่เข้า NIOSH STS ปีล่าสุด")
    df_refer_corp_count[df_refer_corp_count["year"] == df_refer_corp_count["year"].unique().max()].to_excel(
        excel_writer, sheet_name="สถิติแผนกที่ต้องส่ง ENT ล่าสุด")
    df_niosh_sts_patients.to_excel(excel_writer, sheet_name="เข้าเกณฑ์ NIOSH STS ในแต่ละปี")
    df_niosh_patient_detail.to_excel(excel_writer, sheet_name="Audiogram เข้าเกณฑ์ NIOSH STS")
    df_osha_sts_patients.to_excel(excel_writer, sheet_name="เข้าเกณฑ์ OSHA STS ในแต่ละปี")
    get_osha_patients_detail(df_osha_sts_patients_repeated).to_excel(excel_writer,
                                                                     sheet_name="Audiogram เข้าเกณฑ์ OSHA STS")
    df_refer_patients.to_excel(excel_writer, sheet_name="ส่งต่อ ENT ในแต่ละปี")
    df_refer_patient_detail.to_excel(excel_writer, sheet_name="Audiogram ส่งต่อ ENT")
    excel_writer.save()
    excel_data = strIO.getvalue()
    strIO.seek(0)

    return send_file(strIO,
                     attachment_filename='AudiometryResult.xlsx',
                     as_attachment=True)


layout = html.Div(children=[
    html.H1(children="สรุปผลการตรวจการได้ยินของโรงพยาบาลจุฬาลงกรณ์ ปี 2558 - 2563"),
    html.A("download excel", href="/download_excel/",className="button"),
    html.H2(children="NIOSH Significant Threshold Shift"),
    dcc.Graph(figure=figure_niosh),
    html.H3(children="OSHA Standard Threshold Shift"),
    html.P(children="คำนวนโดยปรับ Baseline และปรับตามอายุ"),
    dcc.Graph(figure=figure_osha),
    html.H2(children="ส่งต่อไปยัง ENT"),
    dcc.Graph(figure=figure_refer),
    html.H3(children="จำนวนแผนกที่ต้องส่งไปยัง ENT ในปี " + str(df_refer_corp_count["year"].unique().max())),
    table.DataTable(
        id="refer-table",
        columns=[{"name": "แผนก", "id": "sub_corp_name"}, {"name": "จำนวนคน", "id": "count"}, {"name": "ปี", "id": "year"}],
        data=df_refer_corp_count.to_dict(orient='records')
    )

])
