import streamlit as st
import requests
import pandas as pd
import time

# Page Layout Setup
st.set_page_config(page_title="Telecom & IT Job Finder", layout="wide")
st.title("📡 Telecom & IT Network Job Search Dashboard")
st.write("Select your filters on the left sidebar and click **Search Jobs Now**.")

# ---------------------------------------------------------
# SIDEBAR: DYNAMIC CONTROL PANEL
# ---------------------------------------------------------
st.sidebar.header("⚙️ Search Filters")

# Saved API Key
api_key = st.sidebar.text_input(
    "RapidAPI Key", 
    value="f288936babmsh6ab7b1f26864cbap1fd9a9jsnb7ee24d8c3b8", 
    type="password"
)

# Job Titles Selection
selected_titles = st.sidebar.multiselect(
    "Target Job Titles",
    options=["NOC Manager", "Incident Manager", "Operation Manager", "Service Delivery Manager", "Network Operations Lead"],
    default=["NOC Manager", "Incident Manager"]
)

# Industry Keyword
industry_keyword = st.sidebar.text_input("Industry Keyword", value="Telecom")

# Target Countries Selection
selected_locations = st.sidebar.multiselect(
    "Target Locations",
    options=["USA", "Canada", "KSA", "Qatar", "UAE"],
    default=["USA", "Canada", "KSA"]
)

# ---------------------------------------------------------
# SEARCH ENGINE EXECUTION
# ---------------------------------------------------------
if st.sidebar.button("🚀 Search Jobs Now", type="primary"):
    if not selected_titles or not selected_locations:
        st.warning("Please select at least one Job Title and one Location.")
    else:
        all_found_jobs = []
        url = "https://jsearch.p.rapidapi.com/search-v2"
        headers = {
            "X-RapidAPI-Key": api_key,
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
                status_text.text(f"🔍 Scouting ({current_step}/{total_searches}): {search_query}")
                
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
                                all_found_jobs.append({
                                    "Search Title": title,
                                    "Search Location": loc,
                                    "Job Title": job.get("job_title", "N/A"),
                                    "Company": job.get("employer_name", "N/A"),
                                    "City/Country": f"{job.get('job_city', 'N/A')}, {job.get('job_country', 'N/A')}",
                                    "Remote?": "Yes" if job.get("job_is_remote") else "No",
                                    "Apply Link": job.get("job_apply_link", "N/A")
                                })
                except Exception as e:
                    st.error(f"Error searching {search_query}: {e}")
                
                progress_bar.progress(current_step / total_searches)
                time.sleep(1.5)

        status_text.success(f"🎉 Search complete! Found {len(all_found_jobs)} total job listings.")
        
        if all_found_jobs:
            df = pd.DataFrame(all_found_jobs)
            df.to_csv("phase2_results.csv", index=False)
            
            st.subheader("📋 Live Job Results")
            st.dataframe(
                df,
                column_config={
                    "Apply Link": st.column_config.LinkColumn("Apply Link")
                },
                use_container_width=True
            )