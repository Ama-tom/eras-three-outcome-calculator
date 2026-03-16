import streamlit as st
import pandas as pd
import numpy as np
import json

st.set_page_config(
    page_title='ERAS Africa Risk Calculator',
    page_icon='Hospital',
    layout='wide',
    initial_sidebar_state='expanded'
)

MODELS_DATA = {
  "POCR_Toal": {
    "ASA_physical_status": {
      "B_coeff": 1.0985,
      "weight": 10.98,
      "OR": 3.0,
      "p_value": 0.0
    },
    "Thromboprophylaxis_initiated_preop": {
      "B_coeff": 0.7491,
      "weight": 7.49,
      "OR": 2.115,
      "p_value": 0.0017
    },
    "Smoking_alcohol_cessation_Counselling": {
      "B_coeff": -0.4943,
      "weight": -4.94,
      "OR": 0.61,
      "p_value": 0.0021
    },
    "Urgency": {
      "B_coeff": -0.4845,
      "weight": -4.84,
      "OR": 0.616,
      "p_value": 0.0027
    },
    "Diabetic_Mellitus": {
      "B_coeff": 0.9286,
      "weight": 9.29,
      "OR": 2.531,
      "p_value": 0.0127
    },
    "Surgical_Complexity": {
      "B_coeff": 0.2988,
      "weight": 2.99,
      "OR": 1.348,
      "p_value": 0.014
    },
    "Regional_anesthesia_used_block_L": {
      "B_coeff": -0.3739,
      "weight": -3.74,
      "OR": 0.688,
      "p_value": 0.0272
    },
    "Nutritional_risk_assessment_Preop": {
      "B_coeff": 0.3503,
      "weight": 3.5,
      "OR": 1.42,
      "p_value": 0.0295
    },
    "Renal_Comorbidity": {
      "B_coeff": 1.6781,
      "weight": 16.78,
      "OR": 5.356,
      "p_value": 0.0408
    },
    "Avoidance_of_sedative_premedicat": {
      "B_coeff": -0.3204,
      "weight": -3.2,
      "OR": 0.726,
      "p_value": 0.046
    },
    "Goal_directed_restricted_fluid_t": {
      "B_coeff": -0.3108,
      "weight": -3.11,
      "OR": 0.733,
      "p_value": 0.0477
    },
    "Urinary_catheter_use_optimized": {
      "B_coeff": -0.2904,
      "weight": -2.9,
      "OR": 0.748,
      "p_value": 0.0959
    }
  },
  "Total_LOHS_Binary": {
    "Thromboprophylaxis_initiated_preop": {
      "B_coeff": 1.0744,
      "weight": 10.74,
      "OR": 2.928,
      "p_value": 0.0
    },
    "Surgical_Complexity": {
      "B_coeff": 0.4574,
      "weight": 4.57,
      "OR": 1.58,
      "p_value": 0.0001
    },
    "Smoking_alcohol_cessation_Counselling": {
      "B_coeff": 0.6104,
      "weight": 6.1,
      "OR": 1.841,
      "p_value": 0.0001
    },
    "Urgency": {
      "B_coeff": 0.6488,
      "weight": 6.49,
      "OR": 1.913,
      "p_value": 0.0001
    },
    "Minimally_invasive_approach_used": {
      "B_coeff": -0.5545,
      "weight": -5.54,
      "OR": 0.574,
      "p_value": 0.001
    },
    "Literacy ": {
      "B_coeff": -0.2414,
      "weight": -2.41,
      "OR": 0.786,
      "p_value": 0.0021
    },
    "Urinary_catheter_use_optimized": {
      "B_coeff": 0.5279,
      "weight": 5.28,
      "OR": 1.695,
      "p_value": 0.0028
    },
    "Surgical_Speciality": {
      "B_coeff": 0.0762,
      "weight": 0.76,
      "OR": 1.079,
      "p_value": 0.0035
    },
    "Time_from_antibiotic_administration_to_Incision": {
      "B_coeff": 0.0108,
      "weight": 0.11,
      "OR": 1.011,
      "p_value": 0.011
    },
    "Antiemetic_prophylaxis_given": {
      "B_coeff": 0.3627,
      "weight": 3.63,
      "OR": 1.437,
      "p_value": 0.0175
    },
    "Admission_Type": {
      "B_coeff": -0.6634,
      "weight": -6.63,
      "OR": 0.515,
      "p_value": 0.0237
    },
    "ASA_physical_status": {
      "B_coeff": 0.4935,
      "weight": 4.93,
      "OR": 1.638,
      "p_value": 0.0319
    },
    "Medical_risk_optimization": {
      "B_coeff": 0.3308,
      "weight": 3.31,
      "OR": 1.392,
      "p_value": 0.0371
    },
    "Preemptive_analgesia_given_acet_Diclo": {
      "B_coeff": 0.3209,
      "weight": 3.21,
      "OR": 1.378,
      "p_value": 0.0453
    },
    "Multi_Comorbidity": {
      "B_coeff": -0.3071,
      "weight": -3.07,
      "OR": 0.736,
      "p_value": 0.0493
    },
    "Comorbidity": {
      "B_coeff": -0.3626,
      "weight": -3.63,
      "OR": 0.696,
      "p_value": 0.0596
    },
    "Preoperative_education_counselin": {
      "B_coeff": -0.3517,
      "weight": -3.52,
      "OR": 0.704,
      "p_value": 0.0654
    },
    "Carbohydrate_loading_given_preop": {
      "B_coeff": -0.3114,
      "weight": -3.11,
      "OR": 0.732,
      "p_value": 0.0816
    },
    "Regional_anesthesia_used_block_L": {
      "B_coeff": 0.2728,
      "weight": 2.73,
      "OR": 1.314,
      "p_value": 0.0873
    },
    "Surgical_drains_avoided_or_used_": {
      "B_coeff": -0.2669,
      "weight": -2.67,
      "OR": 0.766,
      "p_value": 0.1007
    },
    "Neurological_comorbidity": {
      "B_coeff": 1.622,
      "weight": 16.22,
      "OR": 5.063,
      "p_value": 0.1478
    }
  },
  "Postop_Adverse_4": {
    "Surgical_Complexity": {
      "B_coeff": 0.6372,
      "weight": 6.37,
      "OR": 1.891,
      "p_value": 0.0
    },
    "ASA_physical_status": {
      "B_coeff": 1.0889,
      "weight": 10.89,
      "OR": 2.971,
      "p_value": 0.0
    },
    "Thromboprophylaxis_initiated_preop": {
      "B_coeff": 1.357,
      "weight": 13.57,
      "OR": 3.885,
      "p_value": 0.0
    },
    "Literacy ": {
      "B_coeff": -0.2649,
      "weight": -2.65,
      "OR": 0.767,
      "p_value": 0.0008
    },
    "Medical_risk_optimization": {
      "B_coeff": 0.528,
      "weight": 5.28,
      "OR": 1.695,
      "p_value": 0.0008
    },
    "Nutritional_risk_assessment_Preop": {
      "B_coeff": 0.5324,
      "weight": 5.32,
      "OR": 1.703,
      "p_value": 0.0009
    },
    "Smoking_alcohol_cessation_Counselling": {
      "B_coeff": 0.4652,
      "weight": 4.65,
      "OR": 1.592,
      "p_value": 0.0025
    },
    "Prehabilitation_exercise_program": {
      "B_coeff": 0.5534,
      "weight": 5.53,
      "OR": 1.739,
      "p_value": 0.0034
    },
    "Urgency": {
      "B_coeff": 0.4511,
      "weight": 4.51,
      "OR": 1.57,
      "p_value": 0.0042
    },
    "Antiemetic_prophylaxis_given": {
      "B_coeff": 0.4178,
      "weight": 4.18,
      "OR": 1.519,
      "p_value": 0.006
    },
    "Abbreviated_fasting_protocol_2hrs": {
      "B_coeff": -0.4135,
      "weight": -4.13,
      "OR": 0.661,
      "p_value": 0.0062
    },
    "Multimodal_analgesia_intraop_opi": {
      "B_coeff": -0.4058,
      "weight": -4.06,
      "OR": 0.666,
      "p_value": 0.0072
    },
    "Surgical_Speciality": {
      "B_coeff": 0.066,
      "weight": 0.66,
      "OR": 1.068,
      "p_value": 0.0118
    },
    "Avoidance_ofmechanicalbowelprep": {
      "B_coeff": 0.3535,
      "weight": 3.53,
      "OR": 1.424,
      "p_value": 0.0189
    },
    "Preemptive_analgesia_given_acet_Diclo": {
      "B_coeff": 0.3629,
      "weight": 3.63,
      "OR": 1.438,
      "p_value": 0.0259
    },
    "Surgical_drains_avoided_or_used_": {
      "B_coeff": -0.3484,
      "weight": -3.48,
      "OR": 0.706,
      "p_value": 0.0304
    },
    "Urinary_catheter_use_optimized": {
      "B_coeff": 0.3497,
      "weight": 3.5,
      "OR": 1.419,
      "p_value": 0.0407
    },
    "Avoidance_of_sedative_premedicat": {
      "B_coeff": 0.2586,
      "weight": 2.59,
      "OR": 1.295,
      "p_value": 0.0987
    },
    "Normothermia_maintained_actively": {
      "B_coeff": 0.2391,
      "weight": 2.39,
      "OR": 1.27,
      "p_value": 0.1155
    }
  }
}
MAX_SCORES  = {
  "POCR_Toal": 51.03,
  "Total_LOHS_Binary": 68.08,
  "Postop_Adverse_4": 76.6
}
LABELS      = {
  "POCR_Toal": "30-Day Composite Complications",
  "Total_LOHS_Binary": "Length of Hospital Stay",
  "Postop_Adverse_4": "Postoperative Adverse Outcome"
}
SHAP_DATA   = {
  "POCR_Toal": {
    "predictors": [
      "SSI",
      "ERAS_PE_Adherence_rate",
      "Nutritional_support_postop_if_ap",
      "Pneumonia",
      "PONV",
      "IV_fluids_discontinued_early_by_",
      "Early_extubation_in_OR",
      "Patient_Satisfaction",
      "Urgency",
      "Smoking_alcohol_cessation_Counselling"
    ],
    "shap_vals": [
      0.7345394322502754,
      0.3104577009833155,
      0.30790089539216425,
      0.28791230355533826,
      0.22904538517246514,
      0.2237998030563109,
      0.2115573301850562,
      0.1828199853320767,
      0.17015983189590025,
      0.16357439680910815
    ]
  },
  "Total_LOHS_Binary": {
    "predictors": [
      "Preop_LOHS_Days",
      "First_Postop_moblization_time_hrs",
      "Admission_Type",
      "Minimally_invasive_approach_used",
      "Early_Foley_catheter_removal",
      "Surgical_Complexity",
      "VTE_prophylaxis_continued_postop",
      "Time_from_antibiotic_administration_to_Incision",
      "Literacy ",
      "Urgency"
    ],
    "shap_vals": [
      2.1656793920693556,
      0.24782247303488364,
      0.23532389500636472,
      0.21644090831571805,
      0.20851640022653117,
      0.19112217812147106,
      0.17457729001231967,
      0.16754455930186898,
      0.16649689468849999,
      0.16194856828790302
    ]
  },
  "Postop_Adverse_4": {
    "predictors": [
      "Preop_LOHS_Days",
      "POD_15",
      "Complication_timing",
      "POCR_30",
      "ERAS_PE_Adherence_rate",
      "First_Postop_moblization_time_hrs",
      "other_complications",
      "Nutritional_risk_assessment_Preop",
      "Antiemetic_prophylaxis_given",
      "Urinary_catheter_use_optimized"
    ],
    "shap_vals": [
      2.100565121398821,
      2.0126170899081623,
      1.7586565819798916,
      1.21732712605731,
      0.4410410765244811,
      0.40161495870716357,
      0.28649068636047054,
      0.2849976476720602,
      0.2842723580900896,
      0.283606498436825
    ]
  }
}
LOW_MAX     = 10
MID_MAX     = 30
GITHUB_USER = 'Ama-tom'
GITHUB_REPO = 'eras-africa-risk-pwa'

ERAS_RECS = {
    'LOW': {
        'color':   '#1a7348',
        'bg':      '#f0faf4',
        'border':  '#1a7348',
        'icon':    'LOW',
        'label':   'LOW RISK',
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
        'color':   '#b45309',
        'bg':      '#fffbeb',
        'border':  '#b45309',
        'icon':    'INTERMEDIATE',
        'label':   'INTERMEDIATE RISK',
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
        'color':   '#c8102e',
        'bg':      '#fff1f2',
        'border':  '#c8102e',
        'icon':    'HIGH',
        'label':   'HIGH RISK',
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

st.markdown('''<style>
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
.risk-card {
    padding:1.8rem 2rem; border-radius:12px;
    border:2px solid; margin:1rem 0;
}
.risk-num {
    font-family:'JetBrains Mono',monospace;
    font-size:3.5rem; font-weight:600; line-height:1;
}
.stratum-label { font-size:1.3rem; font-weight:600; margin-top:0.4rem; }
.rec-section {
    background:#f8fafc; border-radius:8px;
    padding:1rem 1.2rem; margin:0.5rem 0;
    border-left:4px solid;
}
.rec-section h4 { margin:0 0 0.5rem; font-size:0.85rem; text-transform:uppercase; }
.rec-section ul { margin:0; padding-left:1.2rem; }
.rec-section li { margin:0.2rem 0; font-size:0.88rem; }
footer { visibility: hidden; }
</style>''', unsafe_allow_html=True)

st.markdown('''<div class="hero">
    <h1>ERAS Africa Risk Calculator</h1>
    <p>Three independent B-coefficient scoring models &nbsp;|&nbsp;
    30-Day Composite Complications &nbsp;|&nbsp;
    Length of Stay &nbsp;|&nbsp; Postoperative Adverse Outcome<br>
    TRIPOD+AI 2024 &nbsp;|&nbsp; CONSORT 2025 &nbsp;|&nbsp; Ethiopian Multicenter Cohort</p>
</div>''', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('### About')
    st.markdown(f'''
**Three independent models** built on univariate
logistic regression (p < 0.15), B-coefficient x 10 scoring.

**Risk strata:**
- Low: < 10%
- Intermediate: 10 to 30%
- High: > 30%

**Source:** Multicenter Ethiopian tertiary hospitals

**Standards:** TRIPOD+AI 2024 | CONSORT 2025 | SPIRIT 2025
    ''')
    st.markdown('---')
    st.markdown('**Disclaimer:** For clinical decision support only. Always apply clinical judgment.')


CATEGORICAL_VARS = {
    'ASA_physical_status':  [1, 2, 3, 4],
    'Age_Catagory':         [1, 2, 3, 4],
    'Surgical_Complexity':  [1, 2, 3],
    'Surgical_Speciality':  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    'Admission_Type':       [1, 2, 3],
}

SURGICAL_SPECIALITY_LABELS = {
    1:  '1 - Breast and Endocrine',
    2:  '2 - Cardiothoracic',
    3:  '3 - Colorectal',
    4:  '4 - General Surgery',
    5:  '5 - Gynaecology',
    6:  '6 - Hepatobiliary',
    7:  '7 - Neurosurgery',
    8:  '8 - Orthopaedics',
    9:  '9 - Paediatric Surgery',
    10: '10 - Urology',
    11: '11 - Upper GI',
    12: '12 - Vascular Surgery',
}

def smart_input(pred, info, outcome_key):
    direction = 'increases risk' if info['weight'] > 0 else 'decreases risk'
    help_text = f'OR={info["OR"]:.3f} | {direction} | p={info["p_value"]:.4f}'
    label_clean = pred.replace('_', ' ')
    if pred in CATEGORICAL_VARS:
        options = CATEGORICAL_VARS[pred]
        if pred == 'Surgical_Speciality':
            fmt_fn = lambda x: SURGICAL_SPECIALITY_LABELS.get(x, str(x))
        else:
            fmt_fn = lambda x: str(x)
        val = st.selectbox(
            label=label_clean,
            options=options,
            index=0,
            key=f'{outcome_key}_{pred}',
            help=help_text,
            format_func=fmt_fn
        )
        return float(val)
    else:
        val = st.radio(
            label=label_clean,
            options=[0, 1],
            index=0,
            horizontal=True,
            key=f'{outcome_key}_{pred}',
            help=help_text,
            format_func=lambda x: 'No' if x == 0 else 'Yes'
        )
        return float(val)

outcome_keys = list(MODELS_DATA.keys())
if not outcome_keys:
    st.error('No models found.')
    st.stop()

tabs = st.tabs([LABELS.get(k, k) for k in outcome_keys])

for tab, outcome_key in zip(tabs, outcome_keys):
    with tab:
        model  = MODELS_DATA[outcome_key]
        max_sc = MAX_SCORES.get(outcome_key, 1)
        label  = LABELS.get(outcome_key, outcome_key)

        input_col, result_col = st.columns([1.1, 0.9], gap='large')

        with input_col:
            st.markdown(f'#### Patient Parameters - {label}')
            st.caption(f'{len(model)} predictors selected (univariate p < 0.15). Enter 0 for absent/unknown.')
            patient_vals = {}
            preds = list(model.keys())
            for pred in preds:
                info = model[pred]
                direction = 'increases risk' if info['weight'] > 0 else 'decreases risk'
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    captured_val = smart_input(pred, info, outcome_key)
            calc_btn = st.button(
                'Calculate Risk',
                key=f'calc_{outcome_key}',
                type='primary',
                use_container_width=True
            )
            # Read actual current values from session_state
            for pred in preds:
                key = f'{outcome_key}_{pred}'
                if key in st.session_state:
                    patient_vals[pred] = float(st.session_state[key])

        with result_col:
            st.markdown('#### Risk Result')
            if calc_btn:
                risk_pct   = score_patient(patient_vals, model, max_sc)
                risk_class = classify(risk_pct)
                rec        = ERAS_RECS[risk_class]
                st.markdown(
                    f'<div class="risk-card" style="background:{rec["bg"]};border-color:{rec["border"]};">'
                    f'<div class="risk-num" style="color:{rec["color"]}">{risk_pct}%</div>'
                    f'<div class="stratum-label" style="color:{rec["color"]}">{rec["label"]}</div>'
                    f'<div style="margin-top:0.6rem;color:#374151">{rec["summary"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.progress(int(risk_pct))
                st.caption(f'Score: {risk_pct:.1f}% of max (max = {max_sc:.1f} points)')
                m1, m2, m3 = st.columns(3)
                with m1: st.metric('Risk %', f'{risk_pct:.1f}%')
                with m2: st.metric('Stratum', risk_class)
                with m3:
                    above = risk_pct - MID_MAX if risk_class == 'HIGH' else (risk_pct - LOW_MAX if risk_class == 'INTERMEDIATE' else 0)
                    st.metric('Above threshold', f'{max(0,above):.1f}pp')
                st.markdown('---')
                st.markdown(f'#### ERAS Bundle - {rec["label"]}')
                for phase, phase_label in [('preop','Pre-operative'),('intraop','Intraoperative'),('postop','Post-operative')]:
                    items_html = ''.join(f'<li>{item}</li>' for item in rec[phase])
                    st.markdown(
                        f'<div class="rec-section" style="border-left-color:{rec["border"]};">'
                        f'<h4 style="color:{rec["border"]}">{phase_label}</h4>'
                        f'<ul>{items_html}</ul></div>',
                        unsafe_allow_html=True
                    )
                with st.expander('Score breakdown per predictor'):
                    rows = []
                    for pred, info in model.items():
                        val     = patient_vals.get(pred, 0)
                        contrib = round(info['weight'] * float(val), 3)
                        rows.append({'Predictor': pred.replace('_',' '), 'Value': val, 'B x 10': info['weight'], 'Contribution': contrib, 'OR': info['OR'], 'p-value': info['p_value']})
                    st.dataframe(pd.DataFrame(rows).sort_values('Contribution', ascending=False), use_container_width=True, hide_index=True)
                shap_key = outcome_key
                if shap_key in SHAP_DATA and SHAP_DATA[shap_key]:
                    with st.expander('SHAP Predictor Importance'):
                        shap_preds = SHAP_DATA[shap_key]['predictors']
                        shap_vals  = SHAP_DATA[shap_key]['shap_vals']
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
                                f'</div></div>',
                                unsafe_allow_html=True
                            )
                        st.caption('Mean |SHAP value| - red = increases risk, green = decreases risk')
            else:
                st.info('Enter patient values and click Calculate Risk to see results')
                st.markdown('**Risk thresholds:**')
                for cls, pct_range, col in [
                        ('LOW',          f'< {LOW_MAX}%',             '#1a7348'),
                        ('INTERMEDIATE', f'{LOW_MAX}% to {MID_MAX}%', '#b45309'),
                        ('HIGH',         f'> {MID_MAX}%',             '#c8102e')]:
                    st.markdown(
                        f'<div style="padding:0.4rem 0.8rem;margin:0.3rem 0;border-left:4px solid {col};background:#f8fafc;border-radius:4px;font-size:0.9rem">'
                        f'<strong style="color:{col}">{cls}</strong> - {pct_range}</div>',
                        unsafe_allow_html=True
                    )
        st.markdown('---')
        with st.expander('All predictor weights for this model'):
            rows = []
            for pred, info in sorted(model.items(), key=lambda x: abs(x[1]['weight']), reverse=True):
                rows.append({'Predictor': pred.replace('_',' '), 'B-coefficient': info['B_coeff'], 'B x 10': info['weight'], 'Odds Ratio': info['OR'], 'p-value': info['p_value']})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown('---')
st.caption('ERAS Africa Risk Calculator | B-coefficient scoring | TRIPOD+AI 2024 | CONSORT 2025 | github.com/Ama-tom/eras-africa-risk-pwa')