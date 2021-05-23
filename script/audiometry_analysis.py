import pandas as pd
import numpy as np

# Age Adjustment
age_adjustment_male = pd.read_excel("age_adjustment.xlsx", sheet_name="Male", usecols="A:F")
age_adjustment_male["gender"] = "Male"
age_adjustment_female = pd.read_excel("age_adjustment.xlsx", sheet_name="Female", usecols="A:F")
age_adjustment_female["gender"] = "Female"
age_adjustment = pd.concat([age_adjustment_male,age_adjustment_female],axis=0,ignore_index=True)
age_adjustment.columns=age_adjustment.columns.astype(str)
del age_adjustment_male,age_adjustment_female
def get_age_adjustment(gender:str, age:float, age_comparing:float):
    if age < 20:
        age = 20
    elif age > 60:
        age = 60
    baseline = age_adjustment[(age_adjustment["gender"]==gender) & (age_adjustment["age"]==age)].reset_index(drop=True)
    target = age_adjustment[(age_adjustment["gender"]==gender) & (age_adjustment["age"]==age_comparing)].reset_index(drop=True)
    diff = pd.DataFrame(columns=["gender","age_baseline","age_comparing","2000","3000","4000","average"])
    diff["gender"] = baseline["gender"]
    diff["age_baseline"] = baseline["age"]
    diff["age_comparing"] = target["age"]
    diff["2000"] = target["2000"] - baseline["2000"]
    diff["3000"] = target["3000"] - baseline["3000"]
    diff["4000"] = target["4000"] - baseline["4000"]
    diff["average"] = (diff["2000"] + diff["3000"] + diff["4000"])/3
    return diff

# NIOSH
def calculate_niosh_sts_internal(df_niosh:pd.DataFrame, show_diff=False) -> pd.DataFrame:
    df_niosh_cal = df_niosh[["title","patient_name","show_hn","sub_corp_name"]].copy()
    df_niosh_cal["niosh_sts"] = False
    if show_diff is True:
        # Iterrows Version
        df_niosh_cal["used_diff"] = 0
        for index,row in df_niosh.iterrows():
            for side in ["l","r"]:
                if df_niosh_cal.loc[index,"niosh_sts"] == True:continue
                for freq in [500,1000,2000,3000,4000,6000]:
                    if df_niosh_cal.loc[index,"niosh_sts"] == True:continue
                    df_niosh_cal.loc[index,"used_diff"] = row["audio_"+str(freq)+"_"+side+"_comparing"] - row["audio_"+str(freq)+"_"+side+"_baseline"]
                    df_niosh_cal.loc[index,"niosh_sts"] = (df_niosh_cal.loc[index,"used_diff"] >= 15 or np.isclose(df_niosh_cal.loc[index,"used_diff"], 15)) and (row["audio_"+str(freq)+"_"+side+"_comparing"] > 25)
    else:
        # Vectorized Version
            for side in ["l","r"]:
                for freq in [500,1000,2000,3000,4000,6000]:
                    df_temp = pd.DataFrame(index=range(len(df_niosh_cal)),columns=["diff"], dtype='float')
                    df_temp["comparing"] = df_niosh["audio_"+str(freq)+"_"+side+"_comparing"]
                    df_temp["diff"] = df_niosh["audio_"+str(freq)+"_"+side+"_comparing"] - df_niosh["audio_"+str(freq)+"_"+side+"_baseline"]
                    df_niosh_cal["niosh_sts"] = np.where(df_niosh_cal["niosh_sts"] | (((df_temp["diff"] >= 15) | np.isclose(df_temp["diff"],15)) & (df_temp["comparing"] > 25)),True,False)
    return df_niosh_cal
def calculate_niosh_sts(df_longformat:pd.DataFrame):
    year_list = df_longformat["year"].unique()
    df_temp=[]
    for index in range(len(year_list)):
        if index+1>=len(year_list): break
        # Transform to wide-format 
        df_matched_audiometries = pd.merge(left=df_longformat[df_longformat["year"]==year_list[index]],right=df_longformat[df_longformat["year"]==year_list[index+1]], on=["show_hn"],how="inner",suffixes=("_baseline","_comparing"))
        df_matched_audiometries.rename(columns={"sub_corp_name_baseline":"sub_corp_name"},inplace=True)
        df_matched_audiometries.rename(columns={"patient_name_baseline":"patient_name"},inplace=True)
        df_matched_audiometries.rename(columns={"title_baseline":"title"},inplace=True)
        df_matched_audiometries_cal = calculate_niosh_sts_internal(df_matched_audiometries,show_diff=False)
        df_matched_audiometries_cal["year"]=str(year_list[index+1])+"-"+str(year_list[index])
        df_temp.append(df_matched_audiometries_cal)
    return pd.concat(df_temp,axis=0)
# OSHA
def calculate_osha_sts(df_longformat:pd.DataFrame,age_adjustment=True,baseline_revision=True):
    year_list = df_longformat["year"].unique()
    df_temp=[]
    # Calculate OSHA Average
    df_osha = df_longformat.copy()
    df_osha["average_l"] = (df_osha["audio_2000_l"] + df_osha["audio_3000_l"] + df_osha["audio_4000_l"])/3
    df_osha["average_r"] = (df_osha["audio_2000_r"] + df_osha["audio_3000_r"] + df_osha["audio_4000_r"])/3
    #df_osha_baseline = pd.DataFrame(columns=["show_hn","average_l_baseline","average_r_baseline","average_l_1","average_r_1","average_l_2","average_r_2","average_l_3","average_r_3"], dtype=['str','float','float','float','float','float','float','float','float'])
    df_osha_baseline = pd.DataFrame(columns=["show_hn"],dtype='str')
    for i in range(1,4):
        df_osha_baseline["average_l_"+str(i)] = np.NaN
        df_osha_baseline["average_r_"+str(i)] = np.NaN
    for year_index in range(len(year_list)):
        # Copy audiometries data of the 1st year to baseline
        if year_index==0:
            df_osha_baseline["show_hn"] = df_osha[df_osha["year"]==year_list[year_index]]["show_hn"]
            df_osha_baseline["age"] = df_osha[df_osha["year"]==year_list[year_index]]["age"]
            df_osha_baseline["average_l_baseline"] = df_osha[df_osha["year"]==year_list[year_index]]["average_l"]
            df_osha_baseline["average_r_baseline"] = df_osha[df_osha["year"]==year_list[year_index]]["average_r"]
            continue
        else:
            # Calculate OSHA STS of the subsequent year
            df_osha_comparing = df_osha[df_osha["year"]==year_list[year_index]]
            df_osha_matched_comparing_with_baseline = pd.merge(left=df_osha_baseline,right=df_osha_comparing,on=["show_hn"],how="inner",suffixes=("","_comparing"))
            #print(df_osha_matched_comparing_with_baseline.head())
            df_osha_matched_comparing_with_baseline["osha_sts"] = False
            df_osha_matched_comparing_with_baseline.rename(columns={"average_l":"average_l_comparing","average_r":"average_r_comparing"},inplace=True)
            for side in ["l","r"]:
                df_osha_matched_comparing_with_baseline["diff_"+side] = df_osha_matched_comparing_with_baseline["average_"+side+"_comparing"] - df_osha_matched_comparing_with_baseline["average_"+side+"_baseline"]
                df_osha_matched_comparing_with_baseline["sig_better_"+side] = np.where(np.isclose(df_osha_matched_comparing_with_baseline["diff_"+side],-5.0) | (df_osha_matched_comparing_with_baseline["diff_"+side]<=-5.0),True,False)
                df_osha_matched_comparing_with_baseline["osha_sts_"+side] = np.where((df_osha_matched_comparing_with_baseline["average_"+side+"_comparing"]>25) & (np.isclose(df_osha_matched_comparing_with_baseline["diff_"+side],10.0) | (df_osha_matched_comparing_with_baseline["diff_"+side]>=10.0)),True,False)
            df_osha_matched_comparing_with_baseline["osha_sts"] = np.where(df_osha_matched_comparing_with_baseline["osha_sts_l"]|df_osha_matched_comparing_with_baseline["osha_sts_r"],True,False)
            df_osha_matched_comparing_with_baseline["sig_better"] = np.where(df_osha_matched_comparing_with_baseline["sig_better_l"]|df_osha_matched_comparing_with_baseline["sig_better_r"],True,False)
            # Add Data to Baseline calculation
            if baseline_revision or age_adjustment:
                for i,row in df_osha_matched_comparing_with_baseline[(df_osha_matched_comparing_with_baseline["osha_sts"]==True) | (df_osha_matched_comparing_with_baseline["sig_better"]==True)].reset_index().iterrows():
                    i = row["index"]
                    if age_adjustment:
                        for side in ["l","r"]:
                            adjustment = get_age_adjustment(row["gender"],row["age"],row["age_comparing"])
                            if len(adjustment["average"])>0:
                                df_osha_matched_comparing_with_baseline.loc[i,"diff_"+side] = df_osha_matched_comparing_with_baseline.loc[i,"diff_"+side] - adjustment["average"][0]
                            df_osha_matched_comparing_with_baseline.loc[i,"sig_better_"+side] = df_osha_matched_comparing_with_baseline.loc[i,"diff_"+side] <= -5.0 or np.isclose(df_osha_matched_comparing_with_baseline.loc[i,"diff_"+side],-5.0)
                            df_osha_matched_comparing_with_baseline.loc[i,"osha_sts_"+side] = df_osha_matched_comparing_with_baseline.loc[i,"diff_"+side] >= 10.0 or np.isclose(df_osha_matched_comparing_with_baseline.loc[i,"diff_"+side],10.0)
                        df_osha_matched_comparing_with_baseline.loc[i,"sig_better"] = df_osha_matched_comparing_with_baseline.loc[i,"sig_better_r"] or df_osha_matched_comparing_with_baseline.loc[i,"sig_better_l"]
                        df_osha_matched_comparing_with_baseline.loc[i,"osha_sts"] = df_osha_matched_comparing_with_baseline.loc[i,"osha_sts_r"] or df_osha_matched_comparing_with_baseline.loc[i,"osha_sts_l"] 
                        
                    if baseline_revision:
                        for index,baseline_row in df_osha_baseline.iterrows():
                            if baseline_row["show_hn"] == row["show_hn"]: break           
                        for side in ["l","r"]:
                            if pd.isna(baseline_row["average_"+side+"_1"]):
                                df_osha_baseline.loc[index,"average_"+side+"_1"] = row["average_"+side+"_comparing"]
                                continue
                            elif pd.isna(baseline_row["average_"+side+"_2"]):
                                df_osha_baseline.loc[index,"average_"+side+"_2"] = row["average_"+side+"_comparing"]
                                # Calculate
                                bv2 = df_osha_baseline.loc[index,"average_"+side+"_2"] - df_osha_baseline.loc[index,"average_"+side+"_baseline"]
                                bv1 = df_osha_baseline.loc[index,"average_"+side+"_1"] - df_osha_baseline.loc[index,"average_"+side+"_baseline"]
                                if ((bv2 >= 10) or (np.isclose(bv2,10))) and ((bv1 >= 10) or (np.isclose(bv1,10))):
                                    if bv2 >= bv1 or np.isclose(bv2,bv1):
                                        df_osha_baseline.loc[index,"average_"+side+"_baseline"] = df_osha_baseline.loc[index,"average_"+side+"_2"]
                                    else:
                                        df_osha_baseline.loc[index,"average_"+side+"_baseline"] = df_osha_baseline.loc[index,"average_"+side+"_1"]
                                    df_osha_baseline.loc[index,"age"] = row["age_comparing"]
                                    df_osha_baseline.loc[index,"average_"+side+"_1"] = np.NaN
                                    df_osha_baseline.loc[index,"average_"+side+"_2"] = np.NaN
                                elif ((bv2 <= -5) or (np.isclose(bv2,-5))) and ((bv1 <= -5) or (np.isclose(bv1,-5))):
                                    if bv2 <= bv1 or np.isclose(bv2,bv1):
                                        df_osha_baseline.loc[index,"average_"+side+"_baseline"] = df_osha_baseline.loc[index,"average_"+side+"_2"]
                                    else:
                                        df_osha_baseline.loc[index,"average_"+side+"_baseline"] = df_osha_baseline.loc[index,"average_"+side+"_1"]
                                    df_osha_baseline.loc[index,"age"] = row["age_comparing"]
                                    df_osha_baseline.loc[index,"average_"+side+"_1"] = np.NaN
                                    df_osha_baseline.loc[index,"average_"+side+"_2"] = np.NaN
                                else:
                                    continue
                            elif pd.isna(baseline_row["average_"+side+"_3"]):
                                df_osha_baseline.loc[index,"average_"+side+"_3"] = row["average_"+side+"_comparing"]
                                # Calculate
                                bv3 = df_osha_baseline.loc[index,"average_"+side+"_3"] - df_osha_baseline.loc[index,"average_"+side+"_baseline"]
                                bv2 = df_osha_baseline.loc[index,"average_"+side+"_2"] - df_osha_baseline.loc[index,"average_"+side+"_baseline"]
                                if ((bv3 >= 10) or (np.isclose(bv3,10))) and ((bv2 >= 10) or (np.isclose(bv2,10))):
                                    if bv3 >= bv2 or np.isclose(bv3,bv2):
                                        df_osha_baseline.loc[index,"average_"+side+"_baseline"] = df_osha_baseline.loc[index,"average_"+side+"_3"]
                                    else:
                                        df_osha_baseline.loc[index,"average_"+side+"_baseline"] = df_osha_baseline.loc[index,"average_"+side+"_2"]
                                    df_osha_baseline.loc[index,"age"] = row["age_comparing"]
                                    df_osha_baseline.loc[index,"average_"+side+"_1"] = np.NaN
                                    df_osha_baseline.loc[index,"average_"+side+"_2"] = np.NaN
                                    df_osha_baseline.loc[index,"average_"+side+"_3"] = np.NaN
                                elif ((bv3 <= -5) or (np.isclose(bv3,-5))) and ((bv2 <= -5) or (np.isclose(bv2,-5))):
                                    if bv3 <= bv2 or np.isclose(bv3,bv2):
                                        df_osha_baseline.loc[index,"average_"+side+"_baseline"] = df_osha_baseline.loc[index,"average_"+side+"_3"]
                                    else:
                                        df_osha_baseline.loc[index,"average_"+side+"_baseline"] = df_osha_baseline.loc[index,"average_"+side+"_2"]
                                    df_osha_baseline.loc[index,"age"] = row["age_comparing"]
                                    df_osha_baseline.loc[index,"average_"+side+"_1"] = np.NaN
                                    df_osha_baseline.loc[index,"average_"+side+"_2"] = np.NaN
                                    df_osha_baseline.loc[index,"average_"+side+"_3"] = np.NaN
                                else:
                                    df_osha_baseline.loc[index,"average_"+side+"_1"] = df_osha_baseline.loc[index,"average_"+side+"_2"]
                                    df_osha_baseline.loc[index,"average_"+side+"_2"] = df_osha_baseline.loc[index,"average_"+side+"_3"]
                                    df_osha_baseline.loc[index,"average_"+side+"_3"] = np.NaN
            # Add New People to baseline
            df_osha_new_people = df_osha_comparing[~df_osha_comparing["show_hn"].isin(df_osha_baseline["show_hn"])] # not in df_osha_baseline
            df_osha_baseline = df_osha_baseline.append(df_osha_new_people[["show_hn","average_l","average_r"]].rename(columns={"average_l":"average_l_baseline","average_r":"average_r_baseline"}),ignore_index=True)
            df_osha_cal = df_osha_matched_comparing_with_baseline[["show_hn","title","patient_name","sub_corp_name","osha_sts"]].copy()
            df_osha_cal["year"]=str(year_list[year_index])+"- Baseline"
            df_temp.append(df_osha_cal)
    return pd.concat(df_temp,axis=0)