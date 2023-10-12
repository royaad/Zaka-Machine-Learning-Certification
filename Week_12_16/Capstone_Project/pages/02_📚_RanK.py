import streamlit as st
import pandas as pd
import os
from RanKIT import JSON_readfile
from RanKIT import CV_Ranker

@st.cache_data
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

# Check/Set API key
if 'api_key' not in st.session_state:
    st.warning("API key is not set")
    st.text('Please set the API key in Homepage.\nYou can set the API key by clicking the homepage button in the sidebar\nor by entering your API key in the Homepage.')
    st.stop()
else:
    os.environ["OPENAI_API_KEY"] = st.session_state["api_key"]

if 'job_description_path' not in st.session_state:
    st.warning(f'Job description is not defined', icon = "🚨")
    st.stop()
else:
    if st.session_state['job_description_path'] is None:
        st.warning(f'Job description is not defined', icon = "🚨")
        st.stop()

if 'cv_paths' not in st.session_state:
    st.warning(f'CVs are not defined', icon = "🚨")
    st.stop()
else:
    if len(st.session_state['cv_paths']) == 0:
        st.warning(f'CVs are not defined', icon = "🚨")
        st.stop()
        
if 'job_list' not in st.session_state:
    st.session_state.job_list = None

if 'rankings' not in st.session_state:
    st.session_state.rankings = None

#st.write(st.session_state)

st.title('Configurate the ranking mode')
st.divider()
lang_mode = st.radio("Choose your language mode:", ('Strict', 'Relaxed'), horizontal=True)
st.text('"Strict": Candidate should speak all required languages.\n"Relaxed": Candidate should speak 2/3 of required languages.')
st.divider()
match_mode = st.radio("Choose your ranking mode:", ("Match", "ADA", "ADAMa"), index=2, horizontal=True)
st.text('"Match": Experience and Skills are scored using a "fuzzy matching" mechanism.\n"ADA": Experience and Skills are scored using OpenAI\'s ada-002 embedding model.\n"ADAMa": Experience is scored using a combined mode between ADA and Match. Skills are still scored in ADA mode.')
st.divider()

Job_Dict = JSON_readfile(st.session_state.job_description_path)
Job_List = Job_Dict["job_title"]

new_job_list = st.text_input('If you wish to change the job title, enter the desired job title(s) below:')

change_job_title = st.button("Change / Update job title(s)")

if change_job_title:
    new_job_list = new_job_list.split(',')
    new_job_list = [i.strip() for i in new_job_list]
    st.session_state.job_list = new_job_list

if st.session_state.job_list is None:
    st.warning(f'The ranking session is using **"{Job_List}"** as job title', icon="🚨")
else:
    if type(st.session_state.job_list) is list:
        str_render = " || ".join(st.session_state.job_list)
        st.warning(f'The ranking session is using **"{str_render}"** as job title', icon="🚨")
    else:
        st.warning(f'The ranking session is using **"{st.session_state.job_list}"** as job title', icon="🚨")

st.divider()

st.markdown("You can enter a simple title, **example: Backend Engineer**.\n\n"
            "Or a list of comma-separated titles, **example: Backend Engineer, Full Stack Engineer, Software Developer**.\n\n"
            "For better results **avoid general 1-word job titles**, such as:\n\n"
            "* Engineer. Developer, Intern, etc...\n\n"
            "Use job/task -specific words or titles, such as:\n\n"
            "* Full Stack, Backend, Frontend, etc...\n\n"
            "* Full Stack Engineer, Software Developer, Software Engineer, etc...")

st.divider()
rows = st.slider("Choose number of CVs to show", min_value=5, max_value=15, value=10)
st.divider()

start = st.button("Rank / Update Rank")

if start:
    with st.spinner('Ranking in progress...'):
        st.session_state.ranking_modes = f'Language Mode: "{lang_mode}"\t Ranking Mode: "{match_mode}"'
        
        scores = {}
        st.session_state.rankings = None
        for JSON_CV in st.session_state.cv_paths:
            print(JSON_CV)
            CV_Dict = JSON_readfile(JSON_CV)
            score = CV_Ranker(Job_Dict, CV_Dict, st.session_state.job_list, lang_mode, match_mode, match_mode)
            CV_name = JSON_CV.split('\\')[-1]
            CV_name = ''.join(CV_name.split('.')[:-1])
            scores[CV_name] = score
        scores = sorted(scores.items(), key=lambda x:x[1], reverse=True)
        scores = dict(scores)
        df = pd.DataFrame.from_dict(scores, orient='index')
        df.reset_index(inplace=True)
        df.columns = ['CV', 'score']
        st.session_state.rankings = df

if "rankings" in st.session_state:
    if st.session_state.rankings is not None:
        show_scores = st.checkbox('Show/Hide scores')
        st.text(st.session_state.ranking_modes)
        if st.session_state.rankings.shape[0] > (rows - 1):
            df_2_show = st.session_state.rankings.iloc[:(rows),:]
        else:
            df_2_show = st.session_state.rankings
        if show_scores:
            st.dataframe(df_2_show, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_2_show, use_container_width=True, hide_index=True, column_config={"score": None})


if st.session_state.rankings is not None:
    csv = convert_df(st.session_state.rankings)

    st.download_button("Press to Download",
                       csv,
                       "rankings.csv",
                       "text/csv",
                       key='download-csv'
                       )