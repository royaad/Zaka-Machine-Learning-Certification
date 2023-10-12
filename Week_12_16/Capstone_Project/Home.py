import streamlit as st
from openai_api_key import OPENAI_API_KEY

st.set_page_config(layout = "wide", page_title='RanKIT: Home', page_icon='🎈')

# Initialize api button state
if "api_button" not in st.session_state:
    st.session_state["api_button"]= False

# Option to input API key from side bar
if st.session_state["api_button"]:
    st.sidebar.success(f"API key set manually")
    st.sidebar.text(f"API's last 4 charaters are - {st.session_state.api_key[-4:]}")
    if st.sidebar.button("Reset API", key = 'reset_button'):
        st.session_state["api_button"] = False
else:
    # Set api key from api file
    st.session_state["api_key"] = OPENAI_API_KEY
    api_input = st.sidebar.text_input("OpenAI API Key", type="password")
    if st.sidebar.button("Apply API Key"):
        if len(api_input):
            st.session_state["api_key"] = api_input
            st.session_state["api_button"] = True

st.title("🎈Introducing RanKIT:")
st.markdown('#### Developed by: Edgard El Cham & Roy Aad')
st.divider()
st.header('Your Ultimate Resume Ranker powered by AI and OpenAI API')

st.markdown("<p style='text-align: justify;'>RanKIT revolutionizes the way HR professionals and companies evaluate resumes, providing an unparalleled blend of speed and precision. Leveraging cutting-edge AI technology and harnessing the power of the OpenAI API, RanKIT emerges as the indispensable companion for HR teams and organizations seeking to swiftly and accurately rank resumes.\nSay goodbye to manual resume screening and welcome a new era of efficiency. RanKIT swiftly sifts through resumes, analyzing crucial attributes with lightning speed. Its AI-driven algorithms meticulously assess qualifications, skills, and experiences, ensuring that every candidate is evaluated fairly and without bias.\nDesigned to be every HR professional's and company's best friend, RanKIT goes beyond traditional methods. It comprehensively assesses and scores resumes, allowing you to effortlessly identify the cream of the crop. With RanKIT, your search for top-tier talent becomes effortless, enabling you to build a winning team without the usual time-consuming efforts.\nUnlock the potential of AI-driven resume ranking with RanKIT and experience the seamless fusion of innovation, accuracy, and speed. Elevate your recruitment process and redefine success with a tool that truly understands your needs.</p>", unsafe_allow_html=True)
st.divider()
st.markdown("#### Welcome to the future of resume evaluation - welcome to RanKIT.")
st.markdown("Start Ranking in 3 simple steps:")
st.markdown("1. Upload a job description.")
st.markdown("2. Upload the resumes of the candidates.")
st.markdown("3. Wait for the rankings.")
if st.button("Press button for some balloons!!!"):
    st.balloons()