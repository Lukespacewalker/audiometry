import pandas as pd
import re
from typing import Callable

def initialize_data():
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
    return audiometries