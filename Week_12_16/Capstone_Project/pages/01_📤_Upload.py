import streamlit as st
from document_handler import extract_text, clean_text
import tempfile, os, json, time, openai
import streamlit.components.v1 as components
from jd_parser import parse_jd
from cv_parser import mini_cv, get_breakdown, parse_skills, extract_languages, get_relevance, combine_cv_json
from error_handler import fix_json
from RanKIT import JSON_readfile

# Check/Set API key
if 'api_key' not in st.session_state:
    st.warning("API key is not set")
    st.text('Please set the API key in Homepage.\nYou can set the API key by clicking the homepage button in the sidebar\nor by entering your API key in the Homepage.')
    st.stop()
else:
    os.environ["OPENAI_API_KEY"] = st.session_state["api_key"]
    
# function that creates a radio button that preserve its state
def radio_waves(title, labels, key, index=0):
    if key not in st.session_state:
        st.session_state[key] = {'index': index}
    index = st.session_state[key]['index']
    label = st.radio(title, labels, index=index, horizontal=True)
    new_index = labels.index(label)
    st.session_state[key]['index'] = new_index
    return label

def update_progress_log(looped_files, total_files):
    looped_files += 1
    percent_completed = looped_files/total_files
    my_bar.progress(percent_completed, text=f"{looped_files}/{total_files} parsed. Please wait...")
    logtxt.text('Parsing log: (X) Fail | (V) Success | (S) Skipped (for files in cache)\n'+'\n'.join(st.session_state.cv_parsing_log))
    return looped_files

# Initialize streamlit states to save paths to parsed files
if 'job_description_path' not in st.session_state:
    st.session_state.job_description_path = None

if 'cv_paths' not in st.session_state:
    st.session_state.cv_paths = []
# To keep track of the parsing success and failures
if 'cv_parsing_log' not in st.session_state:
    st.session_state.cv_parsing_log = []

st.header('Upload a Job Description')
# Choose upload mode
jd_upload_mode = radio_waves("Upload job description or write down job description", ("Upload", "Paste"), "jd_radio")
if jd_upload_mode == "Upload":
    uploaded_file = st.file_uploader("Choose a file to upload (.pdf, .docx). We recommend PDF files.", type=["docx", "pdf"])
else:
    manual_jd = st.text_area("Paste your job description here:", height = 200, key = 'manual-jd')
    parsed_jd_filename = st.text_input("Provide a filename to the parsed job description file")

st.button("Upload", key = 'upload-jd')
temp_dir = tempfile.gettempdir()

if st.session_state['upload-jd']:
    if jd_upload_mode == "Paste":
        if len(manual_jd):
            cleaned_text = clean_text(manual_jd)
            st.text("The text you entered is:")
            st.write(cleaned_text)
            if len(parsed_jd_filename):
                with st.spinner('Wait for it...'):
                    parsed_jd = parse_jd(cleaned_text)
                st.text('The parsed job description JSON is:')
                st.write(parsed_jd)
                jd_path = os.path.join(temp_dir, f"{parsed_jd_filename}.json")
                with open(jd_path, 'w') as f:
                    json.dump(parsed_jd, f)
                print(f"JSON data saved to {jd_path}")
                st.session_state.job_description_path = jd_path
                st.success(f'File was saved in {jd_path}')
            else:
                st.error("Please provide a filename for the JSON file to be saved")
    else:
        if uploaded_file is not None:
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.read())
            # Check if JSON already exists
            base_name = os.path.splitext(uploaded_file.name)[0]
            print(base_name)
            jd_path = os.path.join(temp_dir, f"{base_name}.json")
            if os.path.exists(jd_path):
                st.warning('A job description with the same filename already exists! Parsing Skipped!')
                st.session_state.job_description_path = jd_path
            else:
                try:
                    with st.spinner('Wait for it...'):
                        extracted_jd = extract_text(temp_path)
                        cleaned_text = clean_text(extracted_jd)
                    if len(cleaned_text) > 100:
                        st.success("Job description extracted successfully. Parsing...", icon ="✅")
                        with st.spinner('Wait for it...'):
                            parsed_jd = parse_jd(cleaned_text)
                            st.success("Job description parsed successfully.", icon = "✅")
                        st.text('The parsed job description JSON is:')
                        st.write(parsed_jd)
                        # Save the JSON file to a temporary path
                        with open(jd_path, 'w') as f:
                            json.dump(parsed_jd, f)
                        st.session_state.job_description_path = jd_path
                        st.success(f'File was saved in {jd_path}')
                    else:
                        st.error("Extracted text is too short. Possible parsing error.", icon = '⚠️')
                except:
                    st.error("Failed to read/parse the file. Try again or paste the job description.", icon = "❌")

if st.session_state['job_description_path'] is not None:
    st.divider()
    st.warning(f'File **{st.session_state.job_description_path}** already allocated', icon = "🚨")
    if st.button("Show JSON"):
        st.write(JSON_readfile(st.session_state.job_description_path))
    st.text('Upload another job description if you want to change it.')

st.divider()
st.header('Upload Candidate Resumes')
# Upload files
uploaded_files = st.file_uploader("Choose files to upload (.pdf, .docx). We recommend PDF files.", type=["docx", "pdf"], accept_multiple_files = True)

st.button("Upload", key = 'upload-cvs')

if st.session_state['upload-cvs']:
    if len(uploaded_files) > 0:
        # Reset log
        st.session_state.cv_paths = []
        st.session_state.cv_parsing_log = []
        # Initiate progress bar and log
        looped_files = 0
        total_files = len(uploaded_files)
        my_bar = st.progress(0, text=f"{looped_files}/{total_files} parsed. Please wait...")
        logtxt = st.empty()
        # Start the parsing loop
        for uploaded_file in uploaded_files:
            #save uploaded files to temporary directory
            file_name = uploaded_file.name
            temp_path = os.path.join(temp_dir, file_name)
            with open(temp_path, 'wb') as f:
               f.write(uploaded_file.read()) 
            #check if Parse JSON file already exists
            base_name = os.path.splitext(uploaded_file.name)[0]
            print(base_name)
            jd_path = os.path.join(temp_dir, f"{base_name}.json")
            if os.path.exists(jd_path):
                st.session_state.cv_paths.append(jd_path)
                st.session_state.cv_paths = list(set(st.session_state.cv_paths))
                st.session_state.cv_parsing_log.append(f"(S) file: {file_name}")
            else:
                # Try to extract the CV
                try:
                    extracted_jd = extract_text(temp_path)
                    cleaned_text = clean_text(extracted_jd)
                except:
                    st.session_state.cv_parsing_log.append(f"(X) file: {file_name} | type: Read Error")
                    looped_files = update_progress_log(looped_files, total_files)
                    continue
                # Try to simplify the CV
                try:
                    minimized_cv = mini_cv(cleaned_text)
                except:
                    st.session_state.cv_parsing_log.append(f"(X) file: {file_name} | type: Token Error")
                    looped_files = update_progress_log(looped_files, total_files)
                    continue
                # Get JSONS
                breakdown_json = get_breakdown(minimized_cv)
                skills_json = parse_skills(cleaned_text)
                languages_json = extract_languages(cleaned_text)
                parsed_cv = combine_cv_json(breakdown_json, skills_json, languages_json)
                with open(jd_path, 'w') as f:
                    json.dump(parsed_cv, f)
                st.session_state.cv_parsing_log.append(f"(V) file: {file_name}")
                st.session_state.cv_paths.append(jd_path)

            looped_files = update_progress_log(looped_files, total_files)

if len(st.session_state['cv_paths']):
    st.divider()
    text_to_display = [path.split('\\')[-1] for path in st.session_state.cv_paths]
    st.warning(f'Files below already allocated', icon = "🚨")
    st.text('\n'.join(text_to_display))
    st.text('Upload other CVs if you want to change it.')

print(f"Job Description Path: {st.session_state.job_description_path}")
print("CV Paths:")
for path in st.session_state.cv_paths:
    print(path)