# ERAS Africa Risk Calculator

Three independent B-coefficient scoring models
for perioperative risk stratification in Ethiopian tertiary hospitals.

## Models
- 30-Day Composite Complications: 12 predictors
- Length of Hospital Stay: 21 predictors
- Postoperative Adverse Outcome: 19 predictors

## Scoring Method
B-coefficient x 10 per predictor, summed as percentage of max score.

## Risk Strata
Low: less than 10% - Standard ERAS bundle
Intermediate: 10 to 30% - Enhanced ERAS bundle
High: greater than 30% - Maximum ERAS intensity

## Run Locally
pip install -r requirements.txt
streamlit run app.py

## Standards
CONSORT 2025 | SPIRIT 2025 | TRIPOD+AI 2024
