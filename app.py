import streamlit as st
import pandas as pd
import numpy as np
import json
import io

# ============================================================
# BATCH ANALYSIS FUNCTIONS
# ============================================================

def run_batch(df_input, models_data, max_scores, labels, low_max, mid_max):
    results = []
    for _, row in df_input.iterrows():
        patient = row.to_dict()
        record = {}
        record['Patient_ID'] = patient.get('Patient_ID', '')
        record['Hospital']   = patient.get('Hospital', '')
        for outcome_key, model in models_data.items():
            max_sc  = max_scores.get(outcome_key, 1)
            label   = labels.get(outcome_key, outcome_key)
            raw = sum(
                info['weight'] * float(patient.get(pred, 0))
                for pred, info in model.items()
                if pred in patient
            )
            risk_pct = round(max(0.0, min(100.0,
                (raw / max_sc * 100) if max_sc != 0 else 0)), 1)
            if risk_pct < low_max:
                stratum = 'LOW'
            elif risk_pct < mid_max:
                stratum = 'INTERMEDIATE'
            else:
                stratum = 'HIGH'
            short = label.replace('30-Day ', '').replace(' ', '_')[:20]
            record[f'{short}_Score_Pct'] = risk_pct
            record[f'{short}_Stratum']   = stratum
        results.append(record)
    return pd.DataFrame(results)

def results_to_excel(df_results):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_results.to_excel(writer, sheet_name='Risk_Scores', index=False)
        wb  = writer.book
        ws  = writer.sheets['Risk_Scores']
        hdr_fmt = wb.add_format({'bold': True, 'bg_color': '#1F4E79',
                                  'font_color': 'white', 'border': 1})
        low_fmt  = wb.add_format({'bg_color': '#D5F5E3', 'border': 1})
        mid_fmt  = wb.add_format({'bg_color': '#FEF9E7', 'border': 1})
        high_fmt = wb.add_format({'bg_color': '#FADBD8', 'border': 1})
        norm_fmt = wb.add_format({'border': 1})
        for col_idx, col_name in enumerate(df_results.columns):
            ws.write(0, col_idx, col_name, hdr_fmt)
            ws.set_column(col_idx, col_idx, max(12, len(col_name) + 2))
        for row_idx, row in enumerate(df_results.itertuples(), start=1):
            for col_idx, col_name in enumerate(df_results.columns):
                val = df_results.iloc[row_idx-1, col_idx]
                if 'Stratum' in col_name:
                    fmt = low_fmt if val == 'LOW' else (
                          mid_fmt if val == 'INTERMEDIATE' else high_fmt)
                else:
                    fmt = norm_fmt
                ws.write(row_idx, col_idx, val, fmt)
        stratum_cols = [c for c in df_results.columns if 'Stratum' in c]
        summary_rows = []
        for sc in stratum_cols:
            counts = df_results[sc].value_counts()
            total  = len(df_results)
            for stratum in ['LOW', 'INTERMEDIATE', 'HIGH']:
                n = counts.get(stratum, 0)
                summary_rows.append({
                    'Outcome':   sc.replace('_Stratum','').replace('_',' '),
                    'Stratum':   stratum,
                    'N':         n,
                    'Percent':   round(100 * n / total, 1) if total > 0 else 0
                })
        pd.DataFrame(summary_rows).to_excel(
            writer, sheet_name='Summary', index=False)
    output.seek(0)
    return output

# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title='ERAS Africa Risk Calculator | 7 Outcome Models',
    page_icon='Hospital',
    layout='wide',
    initial_sidebar_state='expanded'
)

MODELS_DATA = {
  "POCR_Toal": {
    "Renal_Comorbidity":                    {"B_coeff": 1.6781,  "weight": 16.78, "OR": 5.356, "p_value": 0.1407},
    "ASA_physical_status":                  {"B_coeff": 1.0985,  "weight": 10.99, "OR": 3.000, "p_value": 0.0057},
    "ERAS_PE_Adherence_rate":               {"B_coeff": -1.1451, "weight": -11.45,"OR": 0.318, "p_value": 0.0},
    "Diabetic_Mellitus":                    {"B_coeff": 0.9286,  "weight": 9.29,  "OR": 2.531, "p_value": 0.099},
    "Thromboprophylaxis_initiated_preop":   {"B_coeff": 0.7491,  "weight": 7.49,  "OR": 2.115, "p_value": 0.0244},
    "VTE_prophylaxis_continued_postop":     {"B_coeff": 0.5536,  "weight": 5.54,  "OR": 1.739, "p_value": 0.0},
    "Nutritional_support_postop_if_ap":     {"B_coeff": 0.4454,  "weight": 4.45,  "OR": 1.561, "p_value": 0.0},
    "Epidural_management_perprotocol_":     {"B_coeff": 0.3603,  "weight": 3.60,  "OR": 1.434, "p_value": 0.0},
    "Nutritional_risk_assessment_Preop":    {"B_coeff": 0.3503,  "weight": 3.50,  "OR": 1.420, "p_value": 0.0888},
    "Patient_Satisfaction":                 {"B_coeff": 0.2912,  "weight": 2.91,  "OR": 1.338, "p_value": 0.0},
    "Surgical_Complexity":                  {"B_coeff": 0.2988,  "weight": 2.99,  "OR": 1.348, "p_value": 0.0219},
    "Pain_Severity":                        {"B_coeff": 0.2585,  "weight": 2.59,  "OR": 1.295, "p_value": 0.0},
    "Early_removal_of_surgical_drains":     {"B_coeff": -0.2392, "weight": -2.39, "OR": 0.787, "p_value": 0.0},
    "Urinary_catheter_use_optimized":       {"B_coeff": -0.2900, "weight": -2.90, "OR": 0.748, "p_value": 0.5629},
    "Avoidance_of_sedative_premedicat":     {"B_coeff": -0.3204, "weight": -3.20, "OR": 0.726, "p_value": 0.159},
    "Goal_directed_restricted_fluid_t":     {"B_coeff": -0.3107, "weight": -3.11, "OR": 0.733, "p_value": 0.0517},
    "Regional_anesthesia_used_block_L":     {"B_coeff": -0.3737, "weight": -3.74, "OR": 0.688, "p_value": 0.3886},
    "Early_Foley_catheter_removal":         {"B_coeff": -0.3662, "weight": -3.66, "OR": 0.693, "p_value": 0.0},
    "Smoking_alcohol_cessation_Counselling":{"B_coeff": -0.4943, "weight": -4.94, "OR": 0.610, "p_value": 0.1164},
    "Urgency":                              {"B_coeff": -0.4845, "weight": -4.85, "OR": 0.616, "p_value": 0.0005},
    "Early_extubation_in_OR":              {"B_coeff": -0.4588, "weight": -4.59, "OR": 0.632, "p_value": 0.0},
    "Nasogastric_tube_avoided_removed":     {"B_coeff": -0.5393, "weight": -5.39, "OR": 0.583, "p_value": 0.0},
    "Postop_nausea_well_managed":           {"B_coeff": -0.6571, "weight": -6.57, "OR": 0.518, "p_value": 0.0},
    "Early_oral_intake_resumed_POD_01":     {"B_coeff": -0.6312, "weight": -6.31, "OR": 0.532, "p_value": 0.0},
    "IV_fluids_discontinued_early_by_":     {"B_coeff": -0.7970, "weight": -7.97, "OR": 0.451, "p_value": 0.0},
    "Early_mobilization_within_24hrs":      {"B_coeff": -0.8240, "weight": -8.24, "OR": 0.439, "p_value": 0.0},
    "First_Postop_moblization_time_hrs":    {"B_coeff": 0.0110,  "weight": 0.11,  "OR": 1.011, "p_value": 0.0},
  },
  "Total_LOHS_Binary": {
    "Thromboprophylaxis_initiated_preop": {"B_coeff": 1.0744, "weight": 10.74, "OR": 2.928, "p_value": 0.0006},
    "Surgical_Complexity": {"B_coeff": 0.4574, "weight": 4.57, "OR": 1.58, "p_value": 0.0021},
    "Smoking_alcohol_cessation_Counselling": {"B_coeff": 0.6104, "weight": 6.1, "OR": 1.841, "p_value": 0.1687},
    "Urgency": {"B_coeff": 0.6488, "weight": 6.49, "OR": 1.913, "p_value": 0.0001},
    "Minimally_invasive_approach_used": {"B_coeff": -0.5545, "weight": -5.54, "OR": 0.574, "p_value": 0.0023},
    "Literacy ": {"B_coeff": -0.2414, "weight": -2.41, "OR": 0.786, "p_value": 0.0035},
    "Urinary_catheter_use_optimized": {"B_coeff": 0.5279, "weight": 5.28, "OR": 1.695, "p_value": 0.0377},
    "Surgical_Speciality": {"B_coeff": 0.0762, "weight": 0.76, "OR": 1.079, "p_value": 0.1446},
    "Time_from_antibiotic_administration_to_Incision": {"B_coeff": 0.0108, "weight": 0.11, "OR": 1.011, "p_value": 0.0054},
    "Antiemetic_prophylaxis_given": {"B_coeff": 0.3627, "weight": 3.63, "OR": 1.437, "p_value": 0.9804},
    "Admission_Type": {"B_coeff": -0.6634, "weight": -6.63, "OR": 0.515, "p_value": 0.0129},
    "ASA_physical_status": {"B_coeff": 0.4935, "weight": 4.93, "OR": 1.638, "p_value": 0.0131},
    "Medical_risk_optimization": {"B_coeff": 0.3308, "weight": 3.31, "OR": 1.392, "p_value": 0.7702},
    "Preemptive_analgesia_given_acet_Diclo": {"B_coeff": 0.3209, "weight": 3.21, "OR": 1.378, "p_value": 0.1496},
    "Multi_Comorbidity": {"B_coeff": -0.3071, "weight": -3.07, "OR": 0.736, "p_value": 0.5097},
    "Comorbidity": {"B_coeff": -0.3626, "weight": -3.63, "OR": 0.696, "p_value": 0.9522},
    "Preoperative_education_counselin": {"B_coeff": -0.3517, "weight": -3.52, "OR": 0.704, "p_value": 0.235},
    "Carbohydrate_loading_given_preop": {"B_coeff": -0.3114, "weight": -3.11, "OR": 0.732, "p_value": 0.0079},
    "Regional_anesthesia_used_block_L": {"B_coeff": 0.2728, "weight": 2.73, "OR": 1.314, "p_value": 0.6541},
    "Surgical_drains_avoided_or_used_": {"B_coeff": -0.2669, "weight": -2.67, "OR": 0.766, "p_value": 0.2861},
    "Neurological_comorbidity": {"B_coeff": 1.622, "weight": 16.22, "OR": 5.063, "p_value": 0.2694}
  },
  "Postop_Adverse_4": {
    "Surgical_Complexity": {"B_coeff": 0.6372, "weight": 6.37, "OR": 1.891, "p_value": 0.0109},
    "ASA_physical_status": {"B_coeff": 1.0889, "weight": 10.89, "OR": 2.971, "p_value": 0.0},
    "Thromboprophylaxis_initiated_preop": {"B_coeff": 1.357, "weight": 13.57, "OR": 3.885, "p_value": 0.0015},
    "Literacy ": {"B_coeff": -0.2649, "weight": -2.65, "OR": 0.767, "p_value": 0.0052},
    "Medical_risk_optimization": {"B_coeff": 0.528, "weight": 5.28, "OR": 1.695, "p_value": 0.8913},
    "Nutritional_risk_assessment_Preop": {"B_coeff": 0.5324, "weight": 5.32, "OR": 1.703, "p_value": 0.7187},
    "Smoking_alcohol_cessation_Counselling": {"B_coeff": 0.4652, "weight": 4.65, "OR": 1.592, "p_value": 0.4488},
    "Prehabilitation_exercise_program": {"B_coeff": 0.5534, "weight": 5.53, "OR": 1.739, "p_value": 0.3769},
    "Urgency": {"B_coeff": 0.4511, "weight": 4.51, "OR": 1.57, "p_value": 0.0099},
    "Antiemetic_prophylaxis_given": {"B_coeff": 0.4178, "weight": 4.18, "OR": 1.519, "p_value": 0.4338},
    "Abbreviated_fasting_protocol_2hrs": {"B_coeff": -0.4135, "weight": -4.13, "OR": 0.661, "p_value": 0.1631},
    "Multimodal_analgesia_intraop_opi": {"B_coeff": -0.4058, "weight": -4.06, "OR": 0.666, "p_value": 0.9061},
    "Surgical_Speciality": {"B_coeff": 0.066, "weight": 0.66, "OR": 1.068, "p_value": 0.0158},
    "Avoidance_ofmechanicalbowelprep": {"B_coeff": 0.3535, "weight": 3.53, "OR": 1.424, "p_value": 0.3956},
    "Preemptive_analgesia_given_acet_Diclo": {"B_coeff": 0.3629, "weight": 3.63, "OR": 1.438, "p_value": 0.337},
    "Surgical_drains_avoided_or_used_": {"B_coeff": -0.3484, "weight": -3.48, "OR": 0.706, "p_value": 0.0353},
    "Urinary_catheter_use_optimized": {"B_coeff": 0.3497, "weight": 3.5, "OR": 1.419, "p_value": 0.0193},
    "Avoidance_of_sedative_premedicat": {"B_coeff": 0.2586, "weight": 2.59, "OR": 1.295, "p_value": 0.3281},
    "Normothermia_maintained_actively": {"B_coeff": 0.2391, "weight": 2.39, "OR": 1.27, "p_value": 0.46}
  },
  "SSI_Outcome": {
    "Preemptive_analgesia_given_acet_Diclo": {"B_coeff": 1.248,   "weight": 12.48, "OR": 3.483, "p_value": 0.0003},
    "Obesity_BMI_30":                        {"B_coeff": 1.2179,  "weight": 12.18, "OR": 3.380, "p_value": 0.4105},
    "Renal_Comorbidity":                     {"B_coeff": 1.2179,  "weight": 12.18, "OR": 3.380, "p_value": 0.2428},
    "Normothermia_maintained_actively":      {"B_coeff": 0.9814,  "weight": 9.81,  "OR": 2.668, "p_value": 0.1932},
    "Avoidance_of_sedative_premedicat":      {"B_coeff": 0.9761,  "weight": 9.76,  "OR": 2.654, "p_value": 0.2052},
    "Preoperative_education_counselin":      {"B_coeff": 0.9067,  "weight": 9.07,  "OR": 2.476, "p_value": 0.4449},
    "Antiemetic_prophylaxis_given":          {"B_coeff": 0.8348,  "weight": 8.35,  "OR": 2.304, "p_value": 0.6607},
    "Surgical_Complexity":                   {"B_coeff": 0.7749,  "weight": 7.75,  "OR": 2.170, "p_value": 0.0926},
    "Thromboprophylaxis_initiated_preop":    {"B_coeff": 0.7667,  "weight": 7.67,  "OR": 2.153, "p_value": 0.2175},
    "Epidural_management_perprotocol_":      {"B_coeff": 0.7368,  "weight": 7.37,  "OR": 2.089, "p_value": 0.512},
    "Multimodal_analgesia_postop_opio":      {"B_coeff": 0.732,   "weight": 7.32,  "OR": 2.079, "p_value": 0.9406},
    "Nutritional_risk_assessment_Preop":     {"B_coeff": 0.6886,  "weight": 6.89,  "OR": 1.991, "p_value": 0.6579},
    "Medical_risk_optimization":             {"B_coeff": 0.663,   "weight": 6.63,  "OR": 1.941, "p_value": 0.2931},
    "ASA_physical_status":                   {"B_coeff": 0.6553,  "weight": 6.55,  "OR": 1.926, "p_value": 0.4716},
    "Nutritional_support_postop_if_ap":      {"B_coeff": 0.5951,  "weight": 5.95,  "OR": 1.813, "p_value": 0.5162},
    "Prehabilitation_exercise_program":      {"B_coeff": 0.4151,  "weight": 4.15,  "OR": 1.515, "p_value": 0.1804},
    "Literacy ":                             {"B_coeff": -0.1977, "weight": -1.98, "OR": 0.821, "p_value": 0.3378},
    "Urgency":                               {"B_coeff": -0.5062, "weight": -5.06, "OR": 0.603, "p_value": 0.0065},
    "Abbreviated_fasting_protocol_2hrs":     {"B_coeff": -1.0006, "weight": -10.01,"OR": 0.368, "p_value": 0.1628},
    "Multimodal_analgesia_intraop_opi":      {"B_coeff": -1.4949, "weight": -14.95,"OR": 0.224, "p_value": 0.0073},
  },
  "Death_30_Mortality": {
    "Neurological_comorbidity":          {"B_coeff": 2.5286,  "weight": 25.29, "OR": 12.539, "p_value": 0.0345},
    "ASA_physical_status":               {"B_coeff": 2.205,   "weight": 22.05, "OR": 9.069,  "p_value": 0.035},
    "Obesity_BMI_30":                    {"B_coeff": 1.9647,  "weight": 19.65, "OR": 7.133,  "p_value": 0.5279},
    "Renal_Comorbidity":                 {"B_coeff": 1.9647,  "weight": 19.65, "OR": 7.133,  "p_value": 0.3136},
    "Surgical_Complexity":               {"B_coeff": 1.8776,  "weight": 18.78, "OR": 6.537,  "p_value": 0.1252},
    "Antiemetic_prophylaxis_given":      {"B_coeff": 1.6039,  "weight": 16.04, "OR": 4.972,  "p_value": 0.1126},
    "Asthma":                            {"B_coeff": 1.6037,  "weight": 16.04, "OR": 4.971,  "p_value": 0.724},
    "Diabetic_Mellitus":                 {"B_coeff": 1.2786,  "weight": 12.79, "OR": 3.592,  "p_value": 0.7284},
    "VTE_prophylaxis_continued_postop":  {"B_coeff": 1.1431,  "weight": 11.43, "OR": 3.137,  "p_value": 0.7441},
    "Thromboprophylaxis_initiated_preop":{"B_coeff": 1.1034,  "weight": 11.03, "OR": 3.014,  "p_value": 0.9787},
    "Nutritional_support_postop_if_ap":  {"B_coeff": 0.9027,  "weight": 9.03,  "OR": 2.467,  "p_value": 0.5243},
    "Age_Catagory":                      {"B_coeff": 0.876,   "weight": 8.76,  "OR": 2.401,  "p_value": 0.8951},
    "Nutritional_risk_assessment_Preop": {"B_coeff": 1.0501,  "weight": 10.50, "OR": 2.858,  "p_value": 0.5513},
    "Regional_anesthesia_used_block_L":  {"B_coeff": -1.1637, "weight": -11.64,"OR": 0.312,  "p_value": 0.1264},
    "Nasogastric_tube_avoided_removed":  {"B_coeff": -1.1306, "weight": -11.31,"OR": 0.323,  "p_value": 0.3048},
    "Urgency":                           {"B_coeff": -1.069,  "weight": -10.69,"OR": 0.344,  "p_value": 0.1975},
    "IV_fluids_discontinued_early_by_":  {"B_coeff": -1.2511, "weight": -12.51,"OR": 0.286,  "p_value": 0.8176},
    "Early_oral_intake_resumed_POD_01":  {"B_coeff": -1.2435, "weight": -12.44,"OR": 0.288,  "p_value": 0.5294},
    "Early_removal_of_surgical_drains":  {"B_coeff": -0.9209, "weight": -9.21, "OR": 0.398,  "p_value": 0.8269},
    "Early_Foley_catheter_removal":      {"B_coeff": -0.7657, "weight": -7.66, "OR": 0.465,  "p_value": 0.1507},
    "Early_mobilization_within_24hrs":   {"B_coeff": -2.0738, "weight": -20.74,"OR": 0.126,  "p_value": 0.009},
  },
  "Reoperation_30_Day": {
    "Obesity_BMI_30":                    {"B_coeff": 1.6521,  "weight": 16.52, "OR": 5.218,  "p_value": 0.6531},
    "Diabetic_Mellitus":                 {"B_coeff": 1.4449,  "weight": 14.45, "OR": 4.242,  "p_value": 0.0468},
    "Surgical_Complexity":               {"B_coeff": 1.4381,  "weight": 14.38, "OR": 4.213,  "p_value": 0.0773},
    "Prehabilitation_exercise_program":  {"B_coeff": 0.9041,  "weight": 9.04,  "OR": 2.470,  "p_value": 0.3967},
    "Thromboprophylaxis_initiated_preop":{"B_coeff": 1.0232,  "weight": 10.23, "OR": 2.782,  "p_value": 0.4973},
    "Nutritional_risk_assessment_Preop": {"B_coeff": 0.8471,  "weight": 8.47,  "OR": 2.333,  "p_value": 0.524},
    "ASA_physical_status":               {"B_coeff": 0.9228,  "weight": 9.23,  "OR": 2.516,  "p_value": 0.3499},
    "Minimally_invasive_approach_used":  {"B_coeff": 0.6623,  "weight": 6.62,  "OR": 1.939,  "p_value": 0.8701},
    "Multimodal_analgesia_intraop_opi":  {"B_coeff": -0.7416, "weight": -7.42, "OR": 0.477,  "p_value": 0.3203},
    "Early_Foley_catheter_removal":      {"B_coeff": -0.8408, "weight": -8.41, "OR": 0.431,  "p_value": 0.8617},
    "Nasogastric_tube_avoided_removed":  {"B_coeff": -1.2969, "weight": -12.97,"OR": 0.273,  "p_value": 0.0159},
    "Early_oral_intake_resumed_POD_01":  {"B_coeff": -1.1158, "weight": -11.16,"OR": 0.328,  "p_value": 0.4098},
    "IV_fluids_discontinued_early_by_":  {"B_coeff": -1.3319, "weight": -13.32,"OR": 0.264,  "p_value": 0.9979},
    "Early_mobilization_within_24hrs":   {"B_coeff": -1.2439, "weight": -12.44,"OR": 0.288,  "p_value": 0.1944},
    "Urgency":                           {"B_coeff": -1.5319, "weight": -15.32,"OR": 0.216,  "p_value": 0.0003},
  },
  "Readmission_30_day": {
    "Preoperative_education_counselin":      {"B_coeff": 1.8124,  "weight": 18.12, "OR": 6.124,  "p_value": 0.0192},
    "Nasogastric_tube_avoided_removed":      {"B_coeff": 0.935,   "weight": 9.35,  "OR": 2.547,  "p_value": 0.0595},
    "IV_fluids_discontinued_early_by_":      {"B_coeff": 0.6342,  "weight": 6.34,  "OR": 1.886,  "p_value": 0.2966},
    "Early_removal_of_surgical_drains":      {"B_coeff": 0.5878,  "weight": 5.88,  "OR": 1.800,  "p_value": 0.3557},
    "Smoking_alcohol_cessation_Counselling": {"B_coeff": 0.5836,  "weight": 5.84,  "OR": 1.793,  "p_value": 0.4207},
  }
}

MAX_SCORES = {"POCR_Toal": 70.74, "Total_LOHS_Binary": 68.08, "Postop_Adverse_4": 76.6, "SSI_Outcome": 112.56}

LABELS = {
  "POCR_Toal": "30-Day Composite Complications",
  "Total_LOHS_Binary": "Length of Hospital Stay",
  "Postop_Adverse_4": "Postoperative Adverse Outcome",
  "SSI_Outcome": "Surgical Site Infection",
  "Death_30_Mortality": "30-Day Mortality",
  "Reoperation_30_Day": "30-Day Reoperation",
  "Readmission_30_day": "30-Day Readmission"
}

SHAP_DATA = {
  "POCR_Toal": {
    "predictors": ["SSI","ERAS_PE_Adherence_rate","Nutritional_support_postop_if_ap","Pneumonia","PONV","IV_fluids_discontinued_early_by_","Early_extubation_in_OR","Patient_Satisfaction","Urgency","Smoking_alcohol_cessation_Counselling"],
    "shap_vals": [0.7345394322502754,0.3104577009833155,0.30790089539216425,0.28791230355533826,0.22904538517246514,0.2237998030563109,0.2115573301850562,0.1828199853320767,0.17015983189590025,0.16357439680910815]
  },
  "Total_LOHS_Binary": {
    "predictors": ["Preop_LOHS_Days","First_Postop_moblization_time_hrs","Admission_Type","Minimally_invasive_approach_used","Early_Foley_catheter_removal","Surgical_Complexity","VTE_prophylaxis_continued_postop","Time_from_antibiotic_administration_to_Incision","Literacy ","Urgency"],
    "shap_vals": [2.1656793920693556,0.24782247303488364,0.23532389500636472,0.21644090831571805,0.20851640022653117,0.19112217812147106,0.17457729001231967,0.16754455930186898,0.16649689468849999,0.16194856828790302]
  },
  "Postop_Adverse_4": {
    "predictors": ["Preop_LOHS_Days","POD_15","Complication_timing","POCR_30","ERAS_PE_Adherence_rate","First_Postop_moblization_time_hrs","other_complications","Nutritional_risk_assessment_Preop","Antiemetic_prophylaxis_given","Urinary_catheter_use_optimized"],
    "shap_vals": [2.100565121398821,2.0126170899081623,1.7586565819798916,1.21732712605731,0.4410410765244811,0.40161495870716357,0.28649068636047054,0.2849976476720602,0.2842723580900896,0.283606498436825]
  },
  "SSI_Outcome": {
    "predictors": ["Multimodal_analgesia_intraop_opi","Abbreviated_fasting_protocol_2hrs","Preemptive_analgesia_given_acet_Diclo","Obesity_BMI_30","Renal_Comorbidity","Normothermia_maintained_actively","Avoidance_of_sedative_premedicat","Preoperative_education_counselin","Antiemetic_prophylaxis_given","Thromboprophylaxis_initiated_preop"],
    "shap_vals": [1.4949,1.0006,1.248,1.2179,1.2179,0.9814,0.9761,0.9067,0.8348,0.7667]
  },
  "Death_30_Mortality": {
    "predictors": ["Neurological_comorbidity","ASA_physical_status","Early_mobilization_within_24hrs","Obesity_BMI_30","Renal_Comorbidity","Surgical_Complexity","Antiemetic_prophylaxis_given","Diabetic_Mellitus","IV_fluids_discontinued_early_by_","Early_oral_intake_resumed_POD_01"],
    "shap_vals": [2.5286,2.205,2.0738,1.9647,1.9647,1.8776,1.6039,1.2786,1.2511,1.2435]
  },
  "Reoperation_30_Day": {
    "predictors": ["Urgency","IV_fluids_discontinued_early_by_","Obesity_BMI_30","Early_mobilization_within_24hrs","Nasogastric_tube_avoided_removed","Diabetic_Mellitus","Surgical_Complexity","Early_oral_intake_resumed_POD_01","Thromboprophylaxis_initiated_preop","ASA_physical_status"],
    "shap_vals": [1.5319,1.3319,1.6521,1.2439,1.2969,1.4449,1.4381,1.1158,1.0232,0.9228]
  },
  "Readmission_30_day": {
    "predictors": ["Preoperative_education_counselin","Nasogastric_tube_avoided_removed","IV_fluids_discontinued_early_by_","Early_removal_of_surgical_drains","Smoking_alcohol_cessation_Counselling"],
    "shap_vals": [1.8124,0.935,0.6342,0.5878,0.5836]
  }
}

AUC_DATA = {
    'POCR_Toal':          {'auc': 0.935, 'ci': '0.914-0.955'},
    'Total_LOHS_Binary':  {'auc': 0.911, 'ci': '0.887-0.932'},
    'Postop_Adverse_4':   {'auc': 0.918, 'ci': '0.897-0.938'},
    'SSI_Outcome':        {'auc': 0.918, 'ci': '0.893-0.941'},
    'Death_30_Mortality': {'auc': 1.000, 'ci': '1.000-1.000'},
    'Reoperation_30_Day': {'auc': 0.996, 'ci': '0.991-1.000'},
    'Readmission_30_day': {'auc': 0.827, 'ci': '0.789-0.863'},
}

LOW_MAX     = 10
MID_MAX     = 30
GITHUB_USER = 'Ama-tom'
GITHUB_REPO = 'eras-africa-risk-pwa'

ERAS_RECS = {
    'LOW': {
        'color': '#1a7348', 'bg': '#f0faf4', 'border': '#1a7348',
        'icon': 'LOW', 'label': 'LOW RISK',
        'summary': 'Standard ERAS bundle. Routine perioperative monitoring.',
        'preop': [
            'Standard carbohydrate loading: 200 mL maltodextrin 2-4 hrs pre-op',
            'Routine pre-operative assessment - no intensification needed',
            'Standard anaemia and nutrition screening',
            'Patient education and ERAS counselling',
        ],
        'intraop': [
            'Standard short-acting anaesthetics',
            'Goal-directed fluid therapy - standard protocol',
            'Avoid NGT and peritoneal drains unless clinically indicated',
            'Standard multimodal analgesia (paracetamol + NSAID + opioid PRN)',
        ],
        'postop': [
            'Early oral feeding within 6 hours of extubation',
            'Ambulation on POD 0 or POD 1 - routine ward physiotherapy',
            'Standard thromboprophylaxis',
            'Routine wound care',
            'Target discharge POD 3-5 when clinically fit',
        ],
    },
    'INTERMEDIATE': {
        'color': '#b45309', 'bg': '#fffbeb', 'border': '#b45309',
        'icon': 'INTERMEDIATE', 'label': 'INTERMEDIATE RISK',
        'summary': 'Enhanced ERAS bundle. Increased monitoring frequency.',
        'preop': [
            'Nutritional optimisation: dietitian if albumin <30 g/L or BMI <18',
            'Anaemia correction: iron therapy or transfusion if Hb <10 g/dL',
            'Extended carbohydrate loading protocol',
            'Smoking and alcohol cessation counselling (minimum 4 weeks pre-op)',
            'Glycaemic optimisation if diabetic (HbA1c target <8%)',
        ],
        'intraop': [
            'Enhanced multimodal analgesia including regional block where available',
            'Intensive goal-directed fluid therapy with cardiac output monitoring',
            'Strongly avoid NGT and drains - requires consultant sign-off',
            'Intraoperative temperature maintenance (forced-air warming)',
            'PONV prophylaxis with two agents',
        ],
        'postop': [
            'Mandatory early oral intake within 4 hours post-extubation',
            'Supervised ambulation on POD 0 with daily physiotherapy',
            'Twice-daily wound assessment',
            'Extended thromboprophylaxis 28 days post-op',
            'Daily nursing ERAS adherence checklist',
            'Pain reassessment every 6 hours for 48 hours',
            'Target discharge POD 4-6',
        ],
    },
    'HIGH': {
        'color': '#c8102e', 'bg': '#fff1f2', 'border': '#c8102e',
        'icon': 'HIGH', 'label': 'HIGH RISK',
        'summary': 'Maximum ERAS intensity. HDU/ICU step-down. Senior oversight required.',
        'preop': [
            'MANDATORY: Correct malnutrition, anaemia, and glycaemia before surgery',
            'Senior surgeon and anaesthetist briefing required pre-op',
            'Cardiopulmonary optimisation - consider cardiology input',
            'Infectious disease review if immunocompromised',
            'Renal review if GFR <45',
            'Intensive patient counselling with family involvement',
        ],
        'intraop': [
            'Invasive haemodynamic monitoring preferred (arterial line)',
            'Maximum goal-directed fluid therapy - individualised targets',
            'Epidural or regional anaesthesia strongly preferred',
            'Senior anaesthetist present throughout',
            'Limit operative time - damage control if applicable',
        ],
        'postop': [
            'HDU or ICU step-down minimum 24 hours',
            'Four-hourly vital signs for 48 hours minimum',
            'Daily consultant surgical review POD 1-7',
            'Proactive wound surveillance from POD 1',
            'Mandatory dietitian from POD 1 - enteral nutrition if oral intake <50%',
            'Extended VTE prophylaxis 35 days',
            'Low threshold for investigation: fever, tachycardia, or any deterioration',
            'Consider early specialist review: infectious disease, renal, cardiology',
            'Discharge only when clinically safe - no fixed day target',
            'Arrange community follow-up within 48 hours of discharge',
        ],
    },
}

ERAS_RECS_MORTALITY = {
    'LOW':  {'color':'#1a7348','bg':'#f0faf4','border':'#1a7348','label':'LOW MORTALITY RISK',
             'summary':'Standard perioperative care. Routine monitoring.',
             'preop':['Standard risk assessment and optimization','Routine nutrition and anaemia screening','Patient education on expected recovery'],
             'intraop':['Standard anesthetic technique','Goal-directed fluid therapy','Maintain normothermia'],
             'postop':['Early mobilization POD 0 or 1','Early oral intake within 6 hours','Standard thromboprophylaxis','Target discharge POD 3-5']},
    'INTERMEDIATE':{'color':'#b45309','bg':'#fffbeb','border':'#b45309','label':'INTERMEDIATE MORTALITY RISK',
             'summary':'Enhanced monitoring. Senior review recommended.',
             'preop':['Optimize ASA III-IV comorbidities pre-operatively','Correct malnutrition and anaemia','Renal and neurological review if indicated','Glycaemic optimization if diabetic'],
             'intraop':['Regional anesthesia preferred','Active normothermia','Minimize operative time','Avoid NGT unless essential'],
             'postop':['Early mobilization mandatory POD 0','Early oral intake within 4 hours','Daily consultant review','Extended VTE prophylaxis 28 days','Nutritional support from POD 1']},
    'HIGH': {'color':'#c8102e','bg':'#fff1f2','border':'#c8102e','label':'HIGH MORTALITY RISK',
             'summary':'Maximum intensity care. HDU/ICU step-down. Senior oversight mandatory.',
             'preop':['MANDATORY: Correct all modifiable risk factors before surgery','Cardiology and renal review','Infectious disease review if asthma or immunocompromised','Intensive family counseling and informed consent'],
             'intraop':['Invasive hemodynamic monitoring','Regional anesthesia strongly preferred','Senior anesthetist present throughout','Limit operative time — damage control if applicable'],
             'postop':['HDU or ICU step-down minimum 24 hours','Four-hourly vitals for 48 hours','Daily consultant review POD 1-7','Mandatory early mobilization and nutrition','Extended VTE prophylaxis 35 days','Low threshold for investigation of any deterioration']},
}

ERAS_RECS_REOPERATION = {
    'LOW':  {'color':'#1a7348','bg':'#f0faf4','border':'#1a7348','label':'LOW REOPERATION RISK',
             'summary':'Standard surgical care. Routine wound and bowel monitoring.',
             'preop':['Standard surgical risk assessment','Routine bowel preparation only if indicated','Nutrition screening'],
             'intraop':['Minimize drain use','Careful hemostasis','Avoid unnecessary bowel anastomoses if unstable'],
             'postop':['Early oral intake','Daily wound inspection','Standard thromboprophylaxis','Target discharge when bowel function returns']},
    'INTERMEDIATE':{'color':'#b45309','bg':'#fffbeb','border':'#b45309','label':'INTERMEDIATE REOPERATION RISK',
             'summary':'Enhanced surgical vigilance. Close bowel and wound monitoring.',
             'preop':['Optimize diabetes and BMI pre-operatively','Nutritional support if albumin <30 g/L','Prehabilitation if time permits'],
             'intraop':['Opioid-sparing analgesia preferred','Nasogastric tube avoided','Early Foley catheter removal planned'],
             'postop':['Early mobilization POD 0','Early oral intake within 4 hours','Daily wound inspection','Twice-daily abdominal examination for 48 hours','Extended thromboprophylaxis 28 days']},
    'HIGH': {'color':'#c8102e','bg':'#fff1f2','border':'#c8102e','label':'HIGH REOPERATION RISK',
             'summary':'Maximum surgical vigilance. Senior oversight. Low threshold for re-exploration.',
             'preop':['MANDATORY: Correct obesity and diabetes before elective surgery','Senior surgeon briefing required','Prehabilitation minimum 4 weeks'],
             'intraop':['Multimodal opioid-sparing analgesia mandatory','Minimize drains and catheters','Nasogastric tube avoided','Senior surgeon present throughout'],
             'postop':['Daily senior surgical review POD 1-7','Four-hourly abdominal assessment for 48 hours','Early IV fluid discontinuation by POD 1','Early mobilization POD 0','Low threshold for CT abdomen if any concern','Discharge only when fully assessed']},
}

ERAS_RECS_READMISSION = {
    'LOW':  {'color':'#1a7348','bg':'#f0faf4','border':'#1a7348','label':'LOW READMISSION RISK',
             'summary':'Standard discharge planning. Routine follow-up.',
             'preop':['Standard education and counseling','Routine risk assessment'],
             'intraop':['Standard ERAS care'],
             'postop':['Standard discharge planning','Patient education on warning signs','Follow-up appointment within 2 weeks']},
    'INTERMEDIATE':{'color':'#b45309','bg':'#fffbeb','border':'#b45309','label':'INTERMEDIATE READMISSION RISK',
             'summary':'Enhanced discharge planning. Close community follow-up.',
             'preop':['Smoking cessation counseling minimum 4 weeks pre-op','Structured patient education on recovery'],
             'intraop':['Early IV fluid discontinuation planned','Minimize drains to reduce readmission risk'],
             'postop':['Structured discharge planning documented before discharge','Patient education on wound care and danger signs','Telephone follow-up at 48 hours post-discharge','Outpatient review within 7 days']},
    'HIGH': {'color':'#c8102e','bg':'#fff1f2','border':'#c8102e','label':'HIGH READMISSION RISK',
             'summary':'Intensive discharge planning. Community follow-up within 48 hours mandatory.',
             'preop':['MANDATORY: Smoking and alcohol cessation counseling','Full structured preoperative education','Social support assessment'],
             'intraop':['Early nasogastric tube removal','Early drain removal planned','IV fluid discontinuation by POD 1'],
             'postop':['Discharge planning documented from POD 1','Community nurse referral before discharge','Telephone review at 24 and 48 hours post-discharge','Outpatient review within 48-72 hours','Clear written instructions on danger signs and when to return']},
}

ERAS_RECS_SSI = {
    'LOW': {
        'color': '#1a7348', 'bg': '#f0faf4', 'border': '#1a7348',
        'label': 'LOW SSI RISK',
        'summary': 'Standard SSI prevention bundle. Routine wound surveillance.',
        'preop': [
            'Standard preoperative skin preparation (chlorhexidine-alcohol)',
            'Routine antibiotic prophylaxis per local protocol',
            'Standard nutritional screening',
            'Patient education on wound care and hygiene',
        ],
        'intraop': [
            'Standard aseptic technique',
            'Maintain normothermia throughout surgery',
            'Goal-directed fluid therapy standard protocol',
            'Minimize operative time where possible',
        ],
        'postop': [
            'Routine wound inspection POD 1, 3, and 5',
            'Standard dressing changes',
            'Early mobilization POD 0 or POD 1',
            'Target discharge when wound is clean and dry',
        ],
    },
    'INTERMEDIATE': {
        'color': '#b45309', 'bg': '#fffbeb', 'border': '#b45309',
        'label': 'INTERMEDIATE SSI RISK',
        'summary': 'Enhanced SSI prevention. Increased wound surveillance frequency.',
        'preop': [
            'Optimize BMI and glycaemic control preoperatively',
            'Nutritional support if albumin <30 g/L',
            'Smoking cessation minimum 4 weeks pre-op',
            'Renal function optimization if comorbid renal disease',
            'Enhanced antibiotic prophylaxis per local sensitivity patterns',
        ],
        'intraop': [
            'Active normothermia maintenance - forced-air warming mandatory',
            'Epidural analgesia preferred to reduce physiological stress response',
            'Minimize drain and catheter use - remove by POD 2 if possible',
            'Restrict intraoperative opioids - multimodal analgesia protocol',
            'PONV prophylaxis with two agents to enable early oral intake',
        ],
        'postop': [
            'Daily wound inspection POD 1 through POD 7',
            'Multimodal postoperative analgesia - opioid-sparing',
            'Nutritional support from POD 1 - dietitian review',
            'Extended thromboprophylaxis 28 days',
            'Twice-weekly wound swabs if any signs of inflammation',
        ],
    },
    'HIGH': {
        'color': '#c8102e', 'bg': '#fff1f2', 'border': '#c8102e',
        'label': 'HIGH SSI RISK',
        'summary': 'Maximum SSI prevention intensity. Senior surgical oversight required.',
        'preop': [
            'MANDATORY: Correct obesity, renal comorbidity, and malnutrition before surgery',
            'Preoperative decolonization protocol (MRSA screen and decolonization)',
            'Infectious disease review if immunocompromised or prior SSI history',
            'Optimize HbA1c to <8% if diabetic',
            'Prehabilitation program - exercise and nutrition minimum 4 weeks',
            'Senior surgeon and anesthesiologist briefing required',
        ],
        'intraop': [
            'Active forced-air warming - target normothermia throughout',
            'Epidural or regional anesthesia strongly preferred',
            'Maximize opioid-sparing multimodal analgesia intraoperatively',
            'Strict aseptic technique - consultant scrub surgeon',
            'Minimize surgical drains - remove within 24 hours where possible',
            'Redose antibiotics if operative time exceeds 3 hours',
        ],
        'postop': [
            'Daily senior surgical review POD 1 through POD 7',
            'Four-hourly wound temperature and erythema assessment for 48 hours',
            'Mandatory dietitian review from POD 1',
            'Multimodal postoperative opioid-sparing analgesia protocol',
            'Early Foley catheter removal by POD 1',
            'Extended VTE prophylaxis 35 days',
            'Low threshold for wound swab, imaging, or re-exploration',
            'Discharge only when wound fully assessed as clean - no fixed day target',
        ],
    },
}

def score_patient(patient_values, model, max_score):
    raw = sum(
        info['weight'] * float(patient_values.get(pred, 0))
        for pred, info in model.items()
    )
    if max_score == 0:
        return 0.0
    return round(max(0.0, min(100.0, (raw / max_score) * 100)), 1)

def classify(pct):
    if pct < LOW_MAX:  return 'LOW'
    if pct < MID_MAX:  return 'INTERMEDIATE'
    return 'HIGH'

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*='css'] { font-family: 'Source Serif 4', Georgia, serif; }
.hero {
    background: linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
    color:white; padding:2rem 2.5rem 1.5rem;
    border-radius:14px; margin-bottom:1.5rem;
    border-left:6px solid #c8102e;
}
.hero h1 { color:white; margin:0; font-size:2rem; font-weight:600; }
.hero p  { color:#94a3b8; margin:0.4rem 0 0; font-size:0.95rem; }
.risk-card { padding:1.8rem 2rem; border-radius:12px; border:2px solid; margin:1rem 0; }
.risk-num { font-family:'JetBrains Mono',monospace; font-size:3.5rem; font-weight:600; line-height:1; }
.stratum-label { font-size:1.3rem; font-weight:600; margin-top:0.4rem; }
.rec-section { background:#f8fafc; border-radius:8px; padding:1rem 1.2rem; margin:0.5rem 0; border-left:4px solid; }
.rec-section h4 { margin:0 0 0.5rem; font-size:0.85rem; text-transform:uppercase; }
.rec-section ul { margin:0; padding-left:1.2rem; }
.rec-section li { margin:0.2rem 0; font-size:0.88rem; }
footer { visibility: hidden; }
</style>""", unsafe_allow_html=True)

st.markdown("""<div class="hero">
    <h1>ERAS Africa Risk Calculator</h1>
    <p>Seven independent B-coefficient scoring models &nbsp;|&nbsp;
    30-Day Composite Complications &nbsp;|&nbsp;
    Length of Hospital Stay &nbsp;|&nbsp;
    Postoperative Adverse Outcome &nbsp;|&nbsp;
    Surgical Site Infection &nbsp;|&nbsp;
    30-Day Mortality &nbsp;|&nbsp;
    30-Day Reoperation &nbsp;|&nbsp;
    30-Day Readmission<br>
    AUC range 0.827&ndash;1.000 &nbsp;|&nbsp;
    TRIPOD+AI 2024 &nbsp;|&nbsp; CONSORT 2025 &nbsp;|&nbsp; SPIRIT 2025 &nbsp;|&nbsp;
    Ethiopian Multicenter Cohort &nbsp;|&nbsp; 721 Patients &nbsp;|&nbsp; 7 Hospitals</p>
</div>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('### About')
    st.markdown("""
**Seven independent models** built on univariate
logistic regression (p < 0.15), B-coefficient x 10 scoring,
with forward stepwise selection.

**Outcomes modelled:**
- 30-Day Composite Complications
- Length of Hospital Stay
- Postoperative Adverse Outcome
- Surgical Site Infection
- 30-Day Mortality
- 30-Day Reoperation
- 30-Day Readmission

**Risk strata:**
- Low: < 10%
- Intermediate: 10 to 30%
- High: > 30%

**Source:** 721 patients across 7 Ethiopian tertiary hospitals

**Standards:** TRIPOD+AI 2024 | CONSORT 2025 | SPIRIT 2025

**Model Performance (AUC):**
| Outcome | AUC | 95% CI |
|---|---|---|
| 30-Day Complications | 0.935 | 0.914-0.955 |
| Length of Stay | 0.911 | 0.887-0.932 |
| Adverse Outcome | 0.918 | 0.897-0.938 |
| Surgical Site Infection | 0.918 | 0.893-0.941 |
| 30-Day Mortality | 1.000 | 1.000-1.000 |
| 30-Day Reoperation | 0.996 | 0.991-1.000 |
| 30-Day Readmission | 0.827 | 0.789-0.863 |
    """)
    st.markdown('---')
    st.markdown('**Disclaimer:** For clinical decision support only. Always apply clinical judgment.')

SURGICAL_SPECIALITY_LABELS = {
    1: '1 - Breast and Endocrine', 2: '2 - Cardiothoracic',
    3: '3 - Colorectal', 4: '4 - General Surgery',
    5: '5 - Gynaecology', 6: '6 - Hepatobiliary',
    7: '7 - Neurosurgery', 8: '8 - Orthopaedics',
    9: '9 - Paediatric Surgery', 10: '10 - Urology',
    11: '11 - Upper GI', 12: '12 - Vascular Surgery',
}

PREDICTOR_META = {
    'Literacy ':                             {'category': 'Sociodemographic',     'question': "What is the patient's literacy level?",                                                                             'type': 'radio',  'options': [0,1], 'labels': {0:'No formal / Primary education', 1:'Secondary / Tertiary education'}},
    'ASA_physical_status':                   {'category': 'Clinical',             'question': 'What is the ASA Physical Status classification?',                                                                   'type': 'select', 'options': [1,2,3,4], 'labels': {1:'ASA I', 2:'ASA II', 3:'ASA III', 4:'ASA IV'}},
    'Diabetic_Mellitus':                     {'category': 'Clinical',             'question': 'Does the patient have a diagnosis of Diabetes Mellitus?',                                                           'type': 'yesno'},
    'Renal_Comorbidity':                     {'category': 'Clinical',             'question': 'Does the patient have renal comorbidity (CKD, AKI, or GFR <60)?',                                                  'type': 'yesno'},
    'Neurological_comorbidity':              {'category': 'Clinical',             'question': 'Does the patient have a neurological comorbidity?',                                                                  'type': 'yesno'},
    'Comorbidity':                           {'category': 'Clinical',             'question': 'Does the patient have any comorbidity?',                                                                             'type': 'yesno'},
    'Multi_Comorbidity':                     {'category': 'Clinical',             'question': 'Does the patient have multiple comorbidities (2 or more)?',                                                         'type': 'yesno'},
    'Obesity_BMI_30':                        {'category': 'Clinical',             'question': 'Does the patient have obesity (BMI >= 30 kg/m2)?',                                                                  'type': 'yesno'},
    'Surgical_Complexity':                   {'category': 'Surgical',             'question': 'What is the surgical complexity?',                                                                                   'type': 'select', 'options': [1,2,3], 'labels': {1:'Intermediate Surgery', 2:'Major Surgery', 3:'Major Complex Surgery'}},
    'Surgical_Speciality':                   {'category': 'Surgical',             'question': 'What is the surgical specialty?',                                                                                    'type': 'select', 'options': [1,2,3,4,5,6,7,8,9,10,11,12], 'labels': SURGICAL_SPECIALITY_LABELS},
    'Urgency':                               {'category': 'Surgical',             'question': 'What is the urgency of the surgical procedure?',                                                                    'type': 'radio',  'options': [0,1], 'labels': {0:'Elective', 1:'Emergency / Urgent'}},
    'Admission_Type':                        {'category': 'Surgical',             'question': 'What is the type of patient admission?',                                                                            'type': 'select', 'options': [1,2,3], 'labels': {1:'Elective Inpatient', 2:'Emergency', 3:'Urgent'}},
    'Minimally_invasive_approach_used':      {'category': 'Surgical',             'question': '13. Was a minimally invasive surgical approach used (laparoscopic or robotic)?',                                   'type': 'yesno'},
    'Time_from_antibiotic_administration_to_Incision': {'category': 'Surgical',  'question': '8.  Was antibiotic prophylaxis administered within 60 minutes before incision?',                                   'type': 'yesno'},
    'Preoperative_education_counselin':      {'category': 'ERAS - Preoperative',  'question': '1.  Was preoperative education and counseling provided to the patient and family?',                                 'type': 'yesno'},
    'Medical_risk_optimization':             {'category': 'ERAS - Preoperative',  'question': '2.  Was medical risk optimization performed prior to surgery?',                                                     'type': 'yesno'},
    'Nutritional_risk_assessment_Preop':     {'category': 'ERAS - Preoperative',  'question': '3.  Was a nutritional risk assessment conducted, with appropriate intervention if indicated?',                     'type': 'yesno'},
    'Abbreviated_fasting_protocol_2hrs':     {'category': 'ERAS - Preoperative',  'question': '4.  Was an abbreviated fasting protocol followed (clear fluids allowed up to 2 hours preoperatively)?',           'type': 'yesno'},
    'Carbohydrate_loading_given_preop':      {'category': 'ERAS - Preoperative',  'question': '5.  Was preoperative carbohydrate loading administered?',                                                          'type': 'yesno'},
    'Avoidance_ofmechanicalbowelprep':       {'category': 'ERAS - Preoperative',  'question': '6.  Was mechanical bowel preparation avoided (for gastrointestinal procedures only)?',                             'type': 'yesno'},
    'Thromboprophylaxis_initiated_preop':    {'category': 'ERAS - Preoperative',  'question': '7.  Was thromboprophylaxis initiated preoperatively?',                                                             'type': 'yesno'},
    'Preemptive_analgesia_given_acet_Diclo': {'category': 'ERAS - Preoperative',  'question': '9.  Was pre-emptive analgesia (e.g., acetaminophen or diclofenac) administered preoperatively?',                  'type': 'yesno'},
    'Smoking_alcohol_cessation_Counselling': {'category': 'ERAS - Preoperative',  'question': '10. Was smoking and/or alcohol cessation advised and supported preoperatively?',                                    'type': 'yesno'},
    'Prehabilitation_exercise_program':      {'category': 'ERAS - Preoperative',  'question': '11. Was a prehabilitation or structured exercise program implemented preoperatively?',                             'type': 'yesno'},
    'Avoidance_of_sedative_premedicat':      {'category': 'ERAS - Preoperative',  'question': '12. Was sedative premedication avoided?',                                                                          'type': 'yesno'},
    'Regional_anesthesia_used_block_L':      {'category': 'ERAS - Intraoperative','question': '14. Was regional anesthesia utilized (nerve block, epidural, or local anesthetic infiltration)?',                 'type': 'yesno'},
    'Multimodal_analgesia_intraop_opi':      {'category': 'ERAS - Intraoperative','question': '16. Was multimodal, opioid-sparing analgesia administered intraoperatively?',                                     'type': 'yesno'},
    'Antiemetic_prophylaxis_given':          {'category': 'ERAS - Intraoperative','question': '17. Was antiemetic prophylaxis provided intraoperatively?',                                                        'type': 'yesno'},
    'Normothermia_maintained_actively':      {'category': 'ERAS - Intraoperative','question': '18. Was active maintenance of normothermia ensured throughout the procedure?',                                     'type': 'yesno'},
    'Goal_directed_restricted_fluid_t':      {'category': 'ERAS - Intraoperative','question': '19. Was goal-directed or restricted fluid therapy applied intraoperatively?',                                      'type': 'yesno'},
    'Surgical_drains_avoided_or_used_':      {'category': 'ERAS - Intraoperative','question': '21. Were surgical drains avoided or used only selectively?',                                                       'type': 'yesno'},
    'Urinary_catheter_use_optimized':        {'category': 'ERAS - Intraoperative','question': '22. Was urinary catheter use optimized and limited to clinical indication?',                                       'type': 'yesno'},
    'Epidural_management_perprotocol_':      {'category': 'ERAS - Intraoperative','question': '28. Was epidural management followed according to protocol (if an epidural was placed)?',                          'type': 'yesno'},
    'Nutritional_support_postop_if_ap':      {'category': 'ERAS - Postoperative', 'question': '33. Was appropriate nutritional support provided postoperatively (if indicated)?',                                 'type': 'yesno'},
    'Multimodal_analgesia_postop_opio':      {'category': 'ERAS - Postoperative', 'question': '27. Was multimodal, non-opioid analgesia used postoperatively?',                                                  'type': 'yesno'},
    'VTE_prophylaxis_continued_postop':     {'category': 'ERAS - Postoperative', 'question': '24. Was VTE prophylaxis continued postoperatively?',                                                                   'type': 'yesno'},
    'Early_Foley_catheter_removal':         {'category': 'ERAS - Postoperative', 'question': '29. Was the Foley catheter removed early (by POD 1)?',                                                                 'type': 'yesno'},
    'Early_removal_of_surgical_drains':     {'category': 'ERAS - Postoperative', 'question': '30. Were surgical drains removed early (if placed)?',                                                                  'type': 'yesno'},
    'IV_fluids_discontinued_early_by_':     {'category': 'ERAS - Postoperative', 'question': '31. Were intravenous fluids discontinued early (by POD 1)?',                                                          'type': 'yesno'},
    'Postop_nausea_well_managed':           {'category': 'ERAS - Postoperative', 'question': '32. Was postoperative nausea and vomiting effectively managed?',                                                       'type': 'yesno'},
    'Early_oral_intake_resumed_POD_01':     {'category': 'ERAS - Postoperative', 'question': '25. Was early oral intake resumed on postoperative day 0 or 1?',                                                       'type': 'yesno'},
    'Early_mobilization_within_24hrs':      {'category': 'ERAS - Postoperative', 'question': '26. Was early mobilization initiated within 24 hours of surgery?',                                                     'type': 'yesno'},
    'Early_extubation_in_OR':               {'category': 'ERAS - Postoperative', 'question': '23. Was early extubation performed in the operating room or PACU?',                                                   'type': 'yesno'},
    'Nasogastric_tube_avoided_removed':     {'category': 'ERAS - Postoperative', 'question': '20. Was nasogastric tube avoided or removed early postoperatively?',                                                   'type': 'yesno'},
    'First_Postop_moblization_time_hrs':    {'category': 'ERAS - Postoperative', 'question': '26b. What was the time to first postoperative mobilization (hours from end of surgery)?',                             'type': 'yesno'},
    'Asthma':                               {'category': 'Clinical',             'question': 'Does the patient have a diagnosis of asthma or chronic respiratory disease?',                          'type': 'yesno'},
    'Age_Catagory':                         {'category': 'Sociodemographic',     'question': 'What is the patient age category?',                                                                             'type': 'select', 'options': [1,2,3,4], 'labels': {1:'Below 20 years', 2:'21-40 years', 3:'41-60 years', 4:'Above 61 years'}},
    'ERAS_PE_Adherence_rate':               {'category': 'EXCLUDE',              'question': '',                                                                                                                       'type': 'exclude'},
    'Patient_Satisfaction':                 {'category': 'EXCLUDE',              'question': '',                                                                                                                       'type': 'exclude'},
    'Pain_Severity':                        {'category': 'EXCLUDE',              'question': '',                                                                                                                       'type': 'exclude'},
}

CATEGORY_ORDER = [
    'Sociodemographic', 'Clinical', 'Surgical',
    'ERAS - Preoperative', 'ERAS - Intraoperative', 'ERAS - Postoperative',
]

CATEGORY_ICONS = {
    'Sociodemographic':      '👤 Sociodemographic Data',
    'Clinical':              '🏥 Clinical Factors',
    'Surgical':              '🔪 Surgical Factors',
    'ERAS - Preoperative':   '📋 ERAS Preoperative Components (Items 1-12)',
    'ERAS - Intraoperative': '🫀 ERAS Intraoperative Components (Items 13-22)',
    'ERAS - Postoperative':  '🛏 ERAS Postoperative Components (Items 23-34)',
}

ERAS_INSTRUCTION = (
    'Was each of the following Enhanced Recovery After Surgery (ERAS) protocol elements '
    'fully implemented and documented for this patient, according to the established guidelines?'
)

def smart_input(pred, info, outcome_key):
    meta      = PREDICTOR_META.get(pred, {})
    direction = 'increases risk' if info['weight'] > 0 else 'decreases risk'
    help_text = f'{direction} | p={info["p_value"]:.4f}'
    question  = meta.get('question', pred.replace('_', ' '))
    itype     = meta.get('type', 'yesno')
    if itype == 'select':
        options = meta.get('options', [1, 2, 3])
        lbl_map = meta.get('labels', {})
        return float(st.selectbox(label=question, options=options, index=0,
                                   key=f'{outcome_key}_{pred}', help=help_text,
                                   format_func=lambda x: lbl_map.get(x, str(x))))
    elif itype == 'number':
        return float(st.number_input(label=question, min_value=0, max_value=120, value=40,
                                      key=f'{outcome_key}_{pred}', help=help_text))
    elif itype == 'radio':
        lbl_map = meta.get('labels', {0: 'No', 1: 'Yes'})
        options = meta.get('options', [0, 1])
        return float(st.radio(label=question, options=options, index=0, horizontal=True,
                               key=f'{outcome_key}_{pred}', help=help_text,
                               format_func=lambda x: lbl_map.get(x, str(x))))
    elif itype == 'exclude':
        return 0.0
    else:
        return float(st.radio(label=question, options=[0, 1], index=0, horizontal=True,
                               key=f'{outcome_key}_{pred}', help=help_text,
                               format_func=lambda x: 'No' if x == 0 else 'Yes'))


outcome_keys = list(MODELS_DATA.keys())
if not outcome_keys:
    st.error('No models found.')
    st.stop()

tab_labels = [LABELS.get(k, k) for k in outcome_keys] + ['Batch Analysis']
*tabs_list, batch_tab = st.tabs(tab_labels)
tabs = tabs_list

for tab, outcome_key in zip(tabs, outcome_keys):
    with tab:
        model  = MODELS_DATA[outcome_key]
        max_sc = MAX_SCORES.get(outcome_key, 1)
        label  = LABELS.get(outcome_key, outcome_key)
        input_col, result_col = st.columns([1.1, 0.9], gap='large')
        with input_col:
            st.markdown(f'#### Patient Parameters - {label}')
            st.caption(f'{len(model)} predictors | Univariate p < 0.15 | Classified by domain')
            patient_vals = {}
            preds = list(model.keys())
            from collections import defaultdict
            grouped = defaultdict(list)
            for pred in preds:
                cat = PREDICTOR_META.get(pred, {}).get('category', 'Other')
                grouped[cat].append(pred)
            for cat in CATEGORY_ORDER:
                if cat not in grouped:
                    continue
                if cat == 'EXCLUDE':
                    continue
                st.markdown(
                    f'<div style="margin:1rem 0 0.3rem;padding:0.4rem 0.8rem;'
                    f'background:#1F4E79;color:white;border-radius:6px;'
                    f'font-size:0.85rem;font-weight:600;">'
                    + CATEGORY_ICONS.get(cat, cat) + '</div>',
                    unsafe_allow_html=True)
                if cat == 'Sociodemographic':
                    st.number_input('Patient Age (years) — reference only, not scored', min_value=0, max_value=120, value=40, key=f'{outcome_key}_Age_display')
                    st.radio('Patient Sex — reference only, not scored', options=['Female', 'Male'], horizontal=True, key=f'{outcome_key}_Sex_display')
                if cat == 'ERAS - Preoperative':
                    st.caption(ERAS_INSTRUCTION)
                for pred in grouped[cat]:
                    if PREDICTOR_META.get(pred, {}).get('type') in ('exclude',):
                        continue
                    info = model[pred]
                    smart_input(pred, info, outcome_key)
            for pred in preds:
                if PREDICTOR_META.get(pred, {}).get('category', 'Other') == 'Other':
                    info = model[pred]
                    smart_input(pred, info, outcome_key)
            calc_btn = st.button('Calculate Risk', key=f'calc_{outcome_key}',
                                  type='primary', use_container_width=True)
            for pred in preds:
                key = f'{outcome_key}_{pred}'
                if key in st.session_state:
                    patient_vals[pred] = float(st.session_state[key])
        with result_col:
            st.markdown('#### Risk Result')
            if calc_btn:
                risk_pct   = score_patient(patient_vals, model, max_sc)
                risk_class = classify(risk_pct)
                rec        = (ERAS_RECS_SSI[risk_class] if outcome_key == 'SSI_Outcome'
                       else ERAS_RECS_MORTALITY[risk_class] if outcome_key == 'Death_30_Mortality'
                       else ERAS_RECS_REOPERATION[risk_class] if outcome_key == 'Reoperation_30_Day'
                       else ERAS_RECS_READMISSION[risk_class] if outcome_key == 'Readmission_30_day'
                       else ERAS_RECS[risk_class])
                st.markdown(
                    f'<div class="risk-card" style="background:{rec["bg"]};border-color:{rec["border"]};">'
                    f'<div class="risk-num" style="color:{rec["color"]}">{risk_pct}%</div>'
                    f'<div class="stratum-label" style="color:{rec["color"]}">{rec["label"]}</div>'
                    f'<div style="margin-top:0.6rem;color:#374151">{rec["summary"]}</div>'
                    f'</div>', unsafe_allow_html=True)
                st.progress(int(risk_pct))
                st.caption(f'Score: {risk_pct:.1f}% of max (max = {max_sc:.1f} points)')
                m1, m2, m3 = st.columns(3)
                with m1: st.metric('Risk %', f'{risk_pct:.1f}%')
                with m2: st.metric('Stratum', risk_class)
                with m3:
                    above = risk_pct - MID_MAX if risk_class == 'HIGH' else (risk_pct - LOW_MAX if risk_class == 'INTERMEDIATE' else 0)
                    st.metric('Above threshold', f'{max(0,above):.1f}pp')
                auc_info = AUC_DATA.get(outcome_key, {})
                if auc_info:
                    auc_val = auc_info['auc']
                    auc_ci  = auc_info['ci']
                    auc_col = ('#1a7348' if auc_val >= 0.80
                               else '#b45309' if auc_val >= 0.70
                               else '#c8102e')
                    auc_lbl = ('Excellent' if auc_val >= 0.80
                               else 'Good' if auc_val >= 0.70
                               else 'Fair')
                    st.markdown(
                        f'<div style="margin:0.6rem 0;padding:0.5rem 0.8rem;'
                        f'background:#f8fafc;border-radius:8px;'
                        f'border-left:4px solid {auc_col};">'
                        f'<span style="font-size:0.8rem;color:#6b7280;">'
                        f'Model Discrimination (AUC)</span><br>'
                        f'<span style="font-size:1.4rem;font-weight:700;'
                        f'font-family:monospace;color:{auc_col};">{auc_val:.3f}</span>'
                        f'<span style="font-size:0.8rem;color:#6b7280;margin-left:0.5rem;">'
                        f'95% CI {auc_ci}</span>'
                        f'<span style="float:right;font-size:0.8rem;font-weight:600;'
                        f'color:{auc_col};">{auc_lbl}</span>'
                        f'</div>',
                        unsafe_allow_html=True)
                st.markdown('---')
                st.markdown(f'#### ERAS Bundle - {rec["label"]}')
                for phase, phase_label in [('preop','Pre-operative'),('intraop','Intraoperative'),('postop','Post-operative')]:
                    items_html = ''.join(f'<li>{item}</li>' for item in rec[phase])
                    st.markdown(
                        f'<div class="rec-section" style="border-left-color:{rec["border"]};">'
                        f'<h4 style="color:{rec["border"]}">{phase_label}</h4>'
                        f'<ul>{items_html}</ul></div>', unsafe_allow_html=True)
                with st.expander('Score breakdown per predictor'):
                    rows = []
                    for pred, info in model.items():
                        val = patient_vals.get(pred, 0)
                        contrib = round(info['weight'] * float(val), 3)
                        rows.append({'Predictor': pred.replace('_',' '), 'Value': val,
                                     'B x 10': info['weight'], 'Contribution': contrib,
                                     'OR': info['OR'], 'p-value': info['p_value']})
                    st.dataframe(pd.DataFrame(rows).sort_values('Contribution', ascending=False),
                                 use_container_width=True, hide_index=True)
                if outcome_key in SHAP_DATA and SHAP_DATA[outcome_key]:
                    with st.expander('SHAP Predictor Importance'):
                        shap_preds = SHAP_DATA[outcome_key]['predictors']
                        shap_vals  = SHAP_DATA[outcome_key]['shap_vals']
                        n_show = min(10, len(shap_preds))
                        max_v  = max(shap_vals[:n_show]) if shap_vals else 1
                        for i in range(n_show):
                            pname = shap_preds[i].replace('_', ' ')
                            sval  = shap_vals[i]
                            width = int((sval / max_v) * 100)
                            bar_c = '#c8102e' if model.get(shap_preds[i], {}).get('weight', 0) > 0 else '#1a7348'
                            st.markdown(
                                f'<div style="margin:0.3rem 0">'
                                f'<div style="font-size:0.8rem;margin-bottom:2px">{pname}'
                                f'<span style="float:right;font-family:monospace;font-size:0.75rem">{sval:.4f}</span></div>'
                                f'<div style="background:#e5e7eb;border-radius:4px;height:10px">'
                                f'<div style="width:{width}%;background:{bar_c};height:10px;border-radius:4px"></div>'
                                f'</div></div>', unsafe_allow_html=True)
                        st.caption('Mean |SHAP value| - red = increases risk, green = decreases risk')
            else:
                st.info('Enter patient values and click Calculate Risk to see results')
                auc_info = AUC_DATA.get(outcome_key, {})
                if auc_info:
                    auc_val = auc_info['auc']
                    auc_ci  = auc_info['ci']
                    auc_col = '#1a7348' if auc_val >= 0.80 else '#b45309' if auc_val >= 0.70 else '#c8102e'
                    auc_lbl = 'Excellent' if auc_val >= 0.80 else 'Good' if auc_val >= 0.70 else 'Fair'
                    st.markdown(
                        f'<div style="margin:0.4rem 0;padding:0.5rem 0.8rem;'
                        f'background:#f8fafc;border-radius:8px;'
                        f'border-left:4px solid {auc_col};">'
                        f'<span style="font-size:0.75rem;color:#6b7280;">Model AUC</span>'
                        f'&nbsp;&nbsp;<strong style="font-family:monospace;color:{auc_col};'
                        f'font-size:1.1rem;">{auc_val:.3f}</strong>'
                        f'<span style="font-size:0.75rem;color:#6b7280;"> (95% CI {auc_ci})</span>'
                        f'&nbsp;&nbsp;<span style="font-size:0.75rem;font-weight:600;'
                        f'color:{auc_col};">{auc_lbl}</span>'
                        f'</div>',
                        unsafe_allow_html=True)
                st.markdown('**Risk thresholds:**')
                for cls, pct_range, col in [
                        ('LOW', f'< {LOW_MAX}%', '#1a7348'),
                        ('INTERMEDIATE', f'{LOW_MAX}% to {MID_MAX}%', '#b45309'),
                        ('HIGH', f'> {MID_MAX}%', '#c8102e')]:
                    st.markdown(
                        f'<div style="padding:0.4rem 0.8rem;margin:0.3rem 0;border-left:4px solid {col};'
                        f'background:#f8fafc;border-radius:4px;font-size:0.9rem">'
                        f'<strong style="color:{col}">{cls}</strong> - {pct_range}</div>',
                        unsafe_allow_html=True)
        st.markdown('---')
        with st.expander('All predictor weights for this model'):
            rows = []
            for pred, info in sorted(model.items(), key=lambda x: abs(x[1]['weight']), reverse=True):
                rows.append({'Predictor': pred.replace('_',' '), 'B-coefficient': info['B_coeff'],
                             'B x 10': info['weight'], 'p-value': info['p_value']})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# -- Batch Analysis Tab -------------------------------------
with batch_tab:
    st.subheader('Batch Analysis')
    st.markdown("""
Upload an Excel or CSV file with multiple patients.
Download the template first to ensure correct column names.
""")
    col_dl, col_up = st.columns(2)
    with col_dl:
        st.markdown('#### Step 1: Download Template')
        try:
            with open('ERAS_Batch_Template.xlsx', 'rb') as tf:
                st.download_button(
                    label='Download Batch Template (.xlsx)',
                    data=tf.read(),
                    file_name='ERAS_Batch_Template.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True)
        except FileNotFoundError:
            st.warning('Template file not found. Contact administrator.')
    with col_up:
        st.markdown('#### Step 2: Upload Completed File')
        uploaded = st.file_uploader('Upload completed template',
                                     type=['xlsx', 'xls', 'csv'], key='batch_upload')
    if uploaded is not None:
        try:
            if uploaded.name.endswith('.csv'):
                df_batch = pd.read_csv(uploaded)
            else:
                df_batch = pd.read_excel(uploaded, header=0)
            df_batch = df_batch.dropna(how='all')
            st.success(f'Loaded {len(df_batch)} patients from {uploaded.name}')
            st.dataframe(df_batch.head(5), use_container_width=True)
            if st.button('Run Batch Analysis', type='primary', use_container_width=True):
                with st.spinner('Scoring all patients...'):
                    df_results = run_batch(df_batch, MODELS_DATA, MAX_SCORES, LABELS, LOW_MAX, MID_MAX)
                st.success(f'Scored {len(df_results)} patients')
                st.markdown('#### Results Preview')
                st.dataframe(df_results, use_container_width=True)
                st.markdown('#### Risk Distribution')
                stratum_cols = [c for c in df_results.columns if 'Stratum' in c]
                dist_cols = st.columns(len(stratum_cols))
                for dc, sc in zip(dist_cols, stratum_cols):
                    counts = df_results[sc].value_counts()
                    total  = len(df_results)
                    with dc:
                        st.markdown(f'**{sc.replace("_Stratum","").replace("_"," ")}**')
                        for stratum, col_c in [('LOW','#1a7348'),('INTERMEDIATE','#b45309'),('HIGH','#c8102e')]:
                            n   = counts.get(stratum, 0)
                            pct = round(100*n/total, 1) if total > 0 else 0
                            st.markdown(
                                f'<div style="padding:0.3rem 0.6rem;border-left:4px solid {col_c};'
                                f'margin:0.2rem 0;font-size:0.85rem">'
                                f'<strong style="color:{col_c}">{stratum}</strong>: {n} ({pct}%)</div>',
                                unsafe_allow_html=True)
                excel_output = results_to_excel(df_results)
                st.download_button(
                    label='Download Results Excel',
                    data=excel_output,
                    file_name='ERAS_Risk_Results.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True)
        except Exception as e:
            st.error(f'Error reading file: {e}')
            st.info('Make sure you used the correct template and did not rename any columns.')

st.markdown('---')
st.caption('ERAS Africa Risk Calculator | 7 outcome models | B-coefficient scoring | TRIPOD+AI 2024 | CONSORT 2025 | SPIRIT 2025 | 721 patients | 7 Ethiopian hospitals | github.com/Ama-tom/eras-africa-risk-pwa')
