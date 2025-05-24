import streamlit as st
import pandas as pd
import base64

# --- Constants ---
MINUTES = {
    'Theory': 800,
    'Lab': 1600,
    'Internship': 2475,
    'Clinical': 2400
}

OSU_ORANGE = "#FF6300"
FONT_URL = "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap"

# --- Load and prepare data ---
df = pd.read_excel("processed_courses.xlsx")

# Ensure expected columns
for col in ['TheoryCredits', 'LabCredits', 'InternshipCredits', 'ClinicalCredits', 'CurrentSeatTime']:
    df[col] = df[col].fillna(0).astype(int)

df['TotalCredits'] = df['TotalCredits'].fillna(0).astype(int)
df['CourseCode'] = df['CourseCode'].fillna('')
df['SubjectCode'] = df['CourseCode'].str.extract(r'^([A-Z]+)', expand=False).fillna('UNKNOWN')

# --- Page configuration and style ---
st.set_page_config(page_title="OSUIT Course Credit Allocator", layout="wide")

st.markdown(f"""
    <style>
    @import url('{FONT_URL}');
    html, body, [class*="css"]  {{
        font-family: 'Montserrat', sans-serif;
        background-color: #ffffff;
    }}
    .stButton>button {{
        background-color: {OSU_ORANGE};
        color: white;
        border-radius: 8px;
        padding: 0.5em 1em;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: #cc4d00;
    }}
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown(f"<h1 style='color:{OSU_ORANGE}'>OSUIT Course Credit Hour Adjustment Tool</h1>", unsafe_allow_html=True)
st.write("Adjust theory, lab, internship, and clinical credit hours per course. Compare seat time impact and download your custom data.")

# --- Filters ---
school_options = sorted(df['School'].dropna().unique().tolist())
school = st.selectbox("📚 Select School", ["Show All"] + school_options)

if school != "Show All":
    filtered = df[df['School'] == school].copy()
else:
    filtered = df.copy()

subject_options = sorted(filtered['SubjectCode'].dropna().unique().tolist())
subject = st.selectbox("🏷️ Select Subject Code", ["Show All"] + subject_options)

if subject != "Show All":
    filtered = filtered[filtered['SubjectCode'] == subject]

st.write(f"Showing **{len(filtered)}** courses")

# --- Editable Table ---
updated_rows = []

for idx, row in filtered.iterrows():
    st.markdown(f"### {row['CourseCode']} – {row['CourseName']}")
    
    # Display current percentages
    st.markdown(f"""
    <div style="background-color:#f4f4f4; padding:10px; border-left:5px solid {OSU_ORANGE};">
    <strong>Current Credit Distribution:</strong><br>
    • Theory: {row.get('TheoryPercent', 0) * 100:.0f}%<br>
    • Lab: {row.get('LabPercent', 0) * 100:.0f}%<br>
    • Internship: {row.get('InternshipPercent', 0) * 100:.0f}%<br>
    • Clinical: {row.get('ClinicalPercent', 0) * 100:.0f}%
    </div>
    """, unsafe_allow_html=True)

    # Entry section
    col1, col2, col3, col4 = st.columns(4)
    theory = col1.number_input("Theory Credits", value=0, step=1, min_value=0, key=f"theory_{idx}")
    lab = col2.number_input("Lab Credits", value=0, step=1, min_value=0, key=f"lab_{idx}")
    intern = col3.number_input("Internship Credits", value=0, step=1, min_value=0, key=f"intern_{idx}")
    clinical = col4.number_input("Clinical Credits", value=0, step=1, min_value=0, key=f"clinical_{idx}")

    total_adjusted = theory + lab + intern + clinical
    original_credits = row['TotalCredits']
    original_seat_time = row['CurrentSeatTime']

    new_seat_time = (
        theory * MINUTES['Theory'] +
        lab * MINUTES['Lab'] +
        intern * MINUTES['Internship'] +
        clinical * MINUTES['Clinical']
    )

    # Credit validation
    if total_adjusted > original_credits:
        st.error(f"⚠️ Adjusted credits ({total_adjusted}) exceed total allowed credits ({original_credits}).")
    elif total_adjusted < original_credits:
        st.warning(f"⚠️ Adjusted credits ({total_adjusted}) are **less than** the required total credits ({original_credits}).")
    else:
        st.success(f"✅ Adjusted credits match the original total: {original_credits}.")

    # Seat time metrics
    col5, col6, col7 = st.columns(3)
    col5.metric("Original Seat Time", f"{int(original_seat_time):,} min")
    col6.metric("New Seat Time", f"{int(new_seat_time):,} min")
    col7.metric("Change", f"{int(new_seat_time - original_seat_time):+} min", delta_color="inverse")

    st.markdown("---")

    updated_rows.append({
        'CourseCode': row['CourseCode'],
        'CourseName': row['CourseName'],
        'School': row['School'],
        'SubjectCode': row['SubjectCode'],
        'TotalCredits': original_credits,
        'TheoryCredits': theory,
        'LabCredits': lab,
        'InternshipCredits': intern,
        'ClinicalCredits': clinical,
        'OriginalSeatTime': original_seat_time,
        'NewSeatTime': new_seat_time,
        'SeatTimeDifference': new_seat_time - original_seat_time
    })

# --- Export Button ---
st.markdown("## 📥 Export Your Adjusted Course Data")

if updated_rows:
    result_df = pd.DataFrame(updated_rows)
    file_name = "osu_course_adjustments.xlsx"
    result_df.to_excel(file_name, index=False)

    with open(file_name, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">📤 Download Adjusted Excel File</a>'
    st.markdown(href, unsafe_allow_html=True)
else:
    st.info("No changes have been made yet.")
