import streamlit as st
import requests
import pandas as pd
import time
import json
from google import genai

# Page Layout Setup
st.set_page_config(page_title="Telecom & IT AI Job Matcher", layout="wide")
st.title("📡 Telecom & IT AI Job Search & Resume Scorer")
st.write("Phase 3: Automated Search + Gemini AI Resume Matching")

# ---------------------------------------------------------
# SIDEBAR: DYNAMIC CONTROL PANEL & CREDENTIALS
# ---------------------------------------------------------
st.sidebar.header("⚙️ API Keys & Credentials")

rapid_api_key = st.sidebar.text_input(
    "RapidAPI Key", 
    value="f288936babmsh6ab7b1f26864cbap1fd9a9jsnb7ee24d8c3b8", 
    type="password"
)

gemini_api_key = st.sidebar.text_input(
    "Gemini API Key", 
    value="PASTE_YOUR_GEMINI_API_KEY_HERE", 
    type="password"
)

st.sidebar.divider()
st.sidebar.header("🎯 Search Filters")

# Job Titles Selection
selected_titles = st.sidebar.multiselect(
    "Target Job Titles",
    options=["NOC Manager", "Incident Manager", "Operation Manager", "Service Delivery Manager", "Network Operations Lead"],
    default=["NOC Manager", "Incident Manager", "Service Delivery Manager"]
)

# Expanded Industry Filter (Multi-select or custom text)
selected_industries = st.sidebar.multiselect(
    "Industry / Domain",
    options=["Telecom", "IT Network", "Cloud Operations", "Cybersecurity"],
    default=["Telecom", "IT Network"]
)

# Combine selected industries into query string format (e.g. "Telecom OR IT Network")
industry_keyword = " OR ".join(selected_industries) if selected_industries else "Telecom"

# Target Countries Selection
selected_locations = st.sidebar.multiselect(
    "Target Locations",
    options=["USA", "Canada", "KSA", "Qatar", "UAE"],
    default=["USA", "Canada", "KSA"]
)

min_match_threshold = st.sidebar.slider("Minimum AI Match Score (%)", min_value=50, max_value=95, value=75, step=5)

# Master Resume Summary for AI Matching
resume_summary = st.sidebar.text_area(
    "Master Resume Profile Summary",
    value="10+ years senior leadership in Telecommunications, NOC Operations Management, Service Delivery, Incident Management, and Enterprise IT/Cloud transitions. Hands-on experience with 24/7 SLA governance, incident triage, vendor management, and network infrastructure.",
    height=150
)

# ---------------------------------------------------------
# GEMINI EVALUATION FUNCTION
# ---------------------------------------------------------
def evaluate_job_with_gemini(client, job_title, job_desc, resume_text):
    prompt = f"""
    You are an executive IT recruiter. Evaluate the fit between the candidate's profile and the job posting.
    
    Candidate Profile:
    {resume_text}
    
    Job Title: {job_title}
    Job Description: {job_desc}
    
    Return strictly a raw JSON object (no markdown formatting, no code block backticks) with two keys:
    1. "match_score": an integer between 0 and 100 representing how well the candidate matches.
    2. "justification": a concise 2-sentence explanation highlighting strategic fit or missing gaps.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_text)
        return int(data.get("match_score", 0)), data.get("justification", "N/A")
    except Exception as e:
        return 0, f"Evaluation error: {str(e)}"

# ---------------------------------------------------------
# SEARCH ENGINE EXECUTION
# ---------------------------------------------------------
if st.sidebar.button("🚀 Search & AI Score Jobs", type="primary"):
    if not selected_titles or not selected_locations:
        st.warning("Please select at least one Job Title and one Location.")
    elif gemini_api_key == "PASTE_YOUR_GEMINI_API_KEY_HERE":
        st.error("Please enter a valid Gemini API Key in the sidebar.")
    else:
        ai_client = genai.Client(api_key=gemini_api_key)
        all_found_jobs = []
        url = "https://jsearch.p.rapidapi.com/search-v2"
        headers = {
            "X-RapidAPI-Key": rapid_api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_searches = len(selected_titles) * len(selected_locations)
        current_step = 0

        for title in selected_titles:
            for loc in selected_locations:
                current_step += 1
                search_query = f"{title} {industry_keyword} in {loc}"
                status_text.text(f"🔍 Scouting & Scoring ({current_step}/{total_searches}): {search_query}")
                
                querystring = {"query": search_query, "page": "1", "num_pages": "1"}
                
                try:
                    response = requests.get(url, headers=headers, params=querystring)
                    if response.status_code == 200:
                        data = response.json()
                        raw_data = data.get('data', data)
                        
                        if isinstance(raw_data, dict):
                            jobs_list = raw_data.get('jobs', [])
                        elif isinstance(raw_data, list):
                            jobs_list = raw_data
                        else:
                            jobs_list = []
                            
                        for job in jobs_list:
                            if isinstance(job, dict):
                                j_title = job.get("job_title", "N/A")
                                j_desc = job.get("job_description", "")
                                
                                # Run Gemini AI Evaluation
                                match_score, justification = evaluate_job_with_gemini(
                                    ai_client, j_title, j_desc, resume_summary
                                )
                                
                                # Filter by threshold
                                if match_score >= min_match_threshold:
                                    all_found_jobs.append({
                                        "Match %": f"{match_score}%",
                                        "Job Title": j_title,
                                        "Company": job.get("employer_name", "N/A"),
                                        "City/Country": f"{job.get('job_city', 'N/A')}, {job.get('job_country', 'N/A')}",
                                        "Remote?": "Yes" if job.get("job_is_remote") else "No",
                                        "Strategic Fit Justification": justification,
                                        "Apply Link": job.get("job_apply_link", "N/A")
                                    })
                except Exception as e:
                    st.error(f"Error evaluating {search_query}: {e}")
                
                progress_bar.progress(current_step / total_searches)
                time.sleep(1.5)

        status_text.success(f"🎉 Evaluation complete! Found {len(all_found_jobs)} high-match roles (>= {min_match_threshold}%).")
        
        if all_found_jobs:
            df = pd.DataFrame(all_found_jobs)
            # Sort by Match % descending
            df['Score_Num'] = df['Match %'].str.replace('%', '').astype(int)
            df = df.sort_values(by='Score_Num', ascending=False).drop(columns=['Score_Num'])
            
            st.subheader("🎯 High-Match Qualified Roles")
            st.dataframe(
                df,
                column_config={
                    "Apply Link": st.column_config.LinkColumn("Apply Link")
                },
                use_container_width=True
            )
