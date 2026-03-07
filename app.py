import streamlit as st
import numpy as np

# ────────────────────────────────────────────────
# PWA Manifest Injection for Android "Add to Home Screen"
# ────────────────────────────────────────────────
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#ffffff">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="manifest" href="data:application/manifest+json,{
  \"name\": \"ERAS Africa Risk Calculator\",
  \"short_name\": \"ERAS Risk\",
  \"start_url\": \"/\",
  \"display\": \"standalone\",
  \"background_color\": \"#ffffff\",
  \"theme_color\": \"#0066cc\",
  \"icons\": [{
    "src": "https://raw.githubusercontent.com/Ama-tom/eras-africa-risk-pwa/main/icons/eras-192.jpg",
"sizes": "192x192",
"type": "image/jpeg"
}, {
"src": "https://raw.githubusercontent.com/Ama-tom/eras-africa-risk-pwa/main/icons/eras-512.jpg",
"sizes": "512x512",
"type": "image/jpeg"
  }]
}">
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Internal point mapping — user never sees keys
# ────────────────────────────────────────────────
prolonged_mapping = {
    "What is the surgical complexity?": {"Major complex surgery": 6, "Major Surgery": 6, "Intermediate Surgery": 0},
    "What is the patient’s literacy level?": {"High school/College /University level education": -2, "Primary and elementary level education": 0, "No formal education": 0},
    "Was thromboprophylaxis initiated pre-operatively?": {"Yes": 10, "No": 0},
    "What is the urgency of the surgery?": {"Emergency": 7, "Elective": 0},
    "What is the ASA Physical Status classification?": {"ASA I–II": 0, "ASA III–IV": 5},
    "Was carbohydrate loading performed pre-operatively?": {"Yes": -5, "No": 0},
    "What surgical approach was used?": {"Minimally invasive": -7, "Open": 0},
    "Were surgical drains removed early (within 24 hours)?": {"Yes, within recommended timeframe": 6, "No, delayed removal": 0},
    "Is discharge planning documentation completed?": {"Yes": 6, "No": 0},
    "Was early mobilization achieved (<24 hrs)?": {"Yes": -7, "No": 0},
    "Type of admission:": {"Outpatient": -8, "Inpatient": 0}
}

complications_mapping = {
    "Does the patient have renal comorbidity?": {"Yes": 8, "No": 0},
    "Does the patient have diabetes mellitus?": {"Yes": 6, "No": 0},
    "ASA Physical Status (re-check):": {"ASA I–II": 0, "ASA III–IV": 7},
    "Urgency of surgery (re-check):": {"Emergency": -6, "Elective": 0},
    "Was epidural analgesia/anesthesia management used?": {"Yes": -5, "No": 0},
    "Was extubation performed in the operating room or early in PACU (within 2hrs)?": {"Yes": -7, "No": 0},
    "Was nutritional support provided post-operatively?": {"Yes": 4, "No": 0},
    "Were IV fluids discontinued early (by POD 1)?": {"Yes": -9, "No": 0},
    "Were factors associated with 30-day postoperative complications present?": {"Yes": 16, "No": 0}
}

# ────────────────────────────────────────────────
# Calculation Functions
# ────────────────────────────────────────────────
def calc_prolonged(responses):
    total = 0
    for q, ans in responses.items():
        if q in prolonged_mapping and ans in prolonged_mapping[q]:
            total += prolonged_mapping[q][ans]
    return total

def calc_complications(responses):
    total = 0
    for q, ans in responses.items():
        if q in complications_mapping and ans in complications_mapping[q]:
            total += complications_mapping[q][ans]
    return total

def scale_100(raw):
    return int(np.clip(round(100 * (raw + 30) / 75), 0, 100))

def risk_category(score):
    if score < 30:
        return "Low risk (<30)"
    elif score <= 59:
        return "Moderate risk (31–59)"
    else:
        return "High risk (≥60)"

def approx_prob(raw, baseline):
    logit = np.log(baseline / (1 - baseline)) + raw * 0.085
    return round(100 / (1 + np.exp(-logit)), 1)

# ────────────────────────────────────────────────
# Streamlit App
# ────────────────────────────────────────────────
st.set_page_config(page_title="Postop Risk Calculator – Pilot", layout="wide")

st.title("Postoperative Adverse Outcome Risk Calculator (Pilot)")

st.markdown(
    "**Model summary**  \n"
    "The final model included 11 and 9 independent predictors with sociodemographic variables for prolonged hospital stay and postoperative complication "
    "with adjusted odds ratios derived from the logistic regression (pseudo-R² = 0.3444; likelihood ratio χ² (32) = 340.80; P<0.0001). "
    "The model demonstrated good discriminative performance (area under the receiver-operating-characteristic curve = 0.8601) "
    "and adequate calibration (Hosmer–Lemeshow χ² (688) = 639.53; P = 0.9067). "
    "At the optimal threshold identified by Youden’s index (predicted probability ≈0.52), sensitivity was approximately 82% "
    "and specificity approximately 73%. A practical threshold of 0.50 provided higher sensitivity (≈85%) with acceptable specificity (≈70%)."
)

st.info("Pilot version – For internal hospital use only | ERAS-aligned questions | Select one option per question")

tab1, tab2 = st.tabs(["Prolonged Stay (>8 days)", "30-day Complications"])

with tab1:
    st.subheader("Prolonged Hospital Stay (>8 days)")
    responses_los = {}

    # Non-scoring additional information – placed at the beginning
    st.markdown("**Additional information**")
    st.radio("Sex", ["Male", "Female"], horizontal=True, key="sex_prolonged")
    
    st.selectbox("Age group", ["Below 20", "21–40", "41–60", "Above 61"], key="age_prolonged")
    
    st.selectbox("Surgical specialty", [
        "Breast & Endocrine", "Cardiothoracic", "Colorectal", "ENT / Pediatrics", "General Surgery",
        "Gynecology", "Hepatobiliary", "Neurosurgery", "Obstetrics", "Orthopedic", "Plastic", "Urology", "Vascular"
    ], key="specialty_prolonged")
    st.radio("Comorbidity presence", ["Yes", "No"], horizontal=True, key="comorbidity_prolonged")

    st.markdown("**Sociodemographic variables**")
    responses_los["What is the patient’s literacy level?"] = st.radio(
        "What is the patient’s literacy level?", 
        ["High school/College /University level education", "Primary and elementary level education", "No formal education"], 
        horizontal=True, key="literacy_prolonged"
    )

    st.markdown("**Clinical factors**")
    responses_los["What is the ASA Physical Status classification?"] = st.radio(
        "What is the ASA Physical Status classification?", ["ASA I–II", "ASA III–IV"], horizontal=True, key="asa_prolonged"
    )

    st.markdown("**Surgical factors**")
    responses_los["What is the surgical complexity?"] = st.radio(
        "What is the surgical complexity?", ["Major complex surgery", "Major Surgery", "Intermediate Surgery"], horizontal=True, key="complexity_prolonged"
    )
    responses_los["What is the urgency of the surgery?"] = st.radio(
        "What is the urgency of the surgery?", ["Emergency", "Elective"], horizontal=True, key="urgency_prolonged"
    )
    responses_los["What surgical approach was used?"] = st.radio(
        "What surgical approach was used?", ["Minimally invasive", "Open"], horizontal=True, key="approach_prolonged"
    )
    responses_los["Type of admission:"] = st.radio(
        "Type of admission:", ["Outpatient", "Inpatient"], horizontal=True, key="admission_prolonged"
    )

    st.markdown("**ERAS elements**")
    responses_los["Was thromboprophylaxis initiated pre-operatively?"] = st.radio(
        "Was thromboprophylaxis initiated pre-operatively?", ["Yes", "No"], horizontal=True, key="thromboprophylaxis_prolonged"
    )
    responses_los["Was carbohydrate loading performed pre-operatively?"] = st.radio(
        "Was carbohydrate loading performed pre-operatively?", ["Yes", "No"], horizontal=True, key="carbohydrate_prolonged"
    )
    responses_los["Were surgical drains removed early (within 24 hours)?"] = st.radio(
        "Were surgical drains removed early (within 24 hours)?", ["Yes, within recommended timeframe", "No, delayed removal"], horizontal=True, key="drains_prolonged"
    )
    responses_los["Was early mobilization achieved (<24 hrs)?"] = st.radio(
        "Was early mobilization achieved (<24 hrs)?", ["Yes", "No"], horizontal=True, key="mobilization_prolonged"
    )
    responses_los["Is discharge planning documentation completed?"] = st.radio(
        "Is discharge planning documentation completed?", ["Yes", "No"], horizontal=True, key="discharge_prolonged"
    )

    if st.button("Calculate Prolonged Stay Risk", type="primary"):
        raw = calc_prolonged(responses_los)
        score = scale_100(raw)
        prob = approx_prob(raw, 0.444)
        cat = risk_category(score)

        st.metric("Scaled Score (0–100)", score)
        st.progress(score / 100)
        st.write(f"**Risk category:** {cat}")
        st.write(f"**Approx. probability:** {prob}%")

        if score >= 60:
            st.error("**High risk** → Intensify ERAS compliance, prehabilitation, multidisciplinary team review, medical optimization (nutrition, anemia, glucose), enhanced monitoring")
        elif score >= 30:
            st.warning("**Moderate risk** → Reinforce core ERAS elements: early mobilization, multimodal analgesia, fluid optimization, close postoperative surveillance")
        else:
            st.success("**Low risk** → Standard ERAS pathway is appropriate")

with tab2:
    st.subheader("30-Day Postoperative Complications")
    responses_comp = {}

    st.markdown("**Additional information**")
    st.radio("Sex", ["Male", "Female"], horizontal=True, key="sex_complications")
    
    st.selectbox("Age group", ["Below 20", "21–40", "41–60", "Above 61"], key="age_complications")
    
    st.selectbox("Surgical specialty", [
        "Breast & Endocrine", "Cardiothoracic", "Colorectal", "ENT / Pediatrics", "General Surgery",
        "Gynecology", "Hepatobiliary", "Neurosurgery", "Obstetrics", "Orthopedic", "Plastic", "Urology", "Vascular"
    ], key="specialty_complications")
    st.radio("Comorbidity presence", ["Yes", "No"], horizontal=True, key="comorbidity_complications")

    st.markdown("**Sociodemographic variables**")
    # (no sociodemographic predictors in complications model)

    st.markdown("**Clinical factors**")
    responses_comp["Does the patient have renal comorbidity?"] = st.radio(
        "Does the patient have renal comorbidity?", ["Yes", "No"], horizontal=True, key="renal_complications"
    )
    responses_comp["Does the patient have diabetes mellitus?"] = st.radio(
        "Does the patient have diabetes mellitus?", ["Yes", "No"], horizontal=True, key="diabetes_complications"
    )
    responses_comp["ASA Physical Status (re-check):"] = st.radio(
        "ASA Physical Status (re-check):", ["ASA I–II", "ASA III–IV"], horizontal=True, key="asa_complications"
    )

    st.markdown("**Surgical factors**")
    responses_comp["Urgency of surgery (re-check):"] = st.radio(
        "Urgency of surgery (re-check):", ["Emergency", "Elective"], horizontal=True, key="urgency_complications"
    )

    st.markdown("**ERAS elements**")
    responses_comp["Was epidural analgesia/anesthesia management used?"] = st.radio(
        "Was epidural analgesia/anesthesia management used?", ["Yes", "No"], horizontal=True, key="epidural_complications"
    )
    responses_comp["Was extubation performed in the operating room or early in PACU (within 2hrs)?"] = st.radio(
        "Was extubation performed in the operating room or early in PACU (within 2hrs)?", ["Yes", "No"], horizontal=True, key="extubation_complications"
    )
    responses_comp["Was nutritional support provided post-operatively?"] = st.radio(
        "Was nutritional support provided post-operatively?", ["Yes", "No"], horizontal=True, key="nutritional_complications"
    )
    responses_comp["Were IV fluids discontinued early (by POD 1)?"] = st.radio(
        "Were IV fluids discontinued early (by POD 1)?", ["Yes", "No"], horizontal=True, key="fluids_complications"
    )
    responses_comp["Were factors associated with 30-day postoperative complications present?"] = st.radio(
        "Were factors associated with 30-day postoperative complications present?", ["Yes", "No"], horizontal=True, key="factors_complications"
    )

    # Extra question (not mapped)
    st.radio(
        "Was post-operative nausea & vomiting well-managed?", ["Yes", "No"], horizontal=True, key="nausea_complications"
    )

    if st.button("Calculate Complications Risk", type="primary"):
        raw = calc_complications(responses_comp)
        score = scale_100(raw)
        prob = approx_prob(raw, 0.363)
        cat = risk_category(score)

        st.metric("Scaled Score (0–100)", score)
        st.progress(score / 100)
        st.write(f"**Risk category:** {cat}")
        st.write(f"**Approx. probability:** {prob}%")

        if score >= 60:
            st.error("**High risk** → Strengthen infection prevention, VTE prophylaxis, wound care vigilance, early sepsis recognition, possible delayed discharge or higher-level care")
        elif score >= 30:
            st.warning("**Moderate risk** → Enhance ERAS components: antibiotic stewardship, respiratory physio, glucose control, early ambulation, patient education")
        else:
            st.success("**Low risk** → Standard perioperative ERAS care sufficient")

st.markdown("---")
st.caption("Pilot version – Internal hospital use only | Based on multivariable-adjusted model | ERAS-aligned questions")