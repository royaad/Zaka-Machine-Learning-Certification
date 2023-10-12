import openai
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from datetime import datetime
from error_handler import fix_json


def handle_parsing_error(response, output_parser, key, counter = 0):
    if counter < 3:
        try:
            output = output_parser.parse(response)
            return output
        except Exception as e:
            print(f"Attempt {counter + 1} failed with error {e}. Attempting to fix...")
            fixed_json = fix_json(response)
            return handle_parsing_error(fixed_json, output_parser, key, counter + 1)
    else:
        return {key: {}}

def calculate_duration(full_dict):
    total_months = 0
    
    for role, durations in full_dict.get('breakdown_experience', {}).items():
        try:
            role_total_months = 0
            
            for duration in durations:
                if len(duration) == 1:
                    # If only one date is provided, interpret it differently depending on its format
                    date_str = duration[0]
                    if "/" in date_str:
                        # Consider it as one full month
                        diff = 1
                    else:
                        # Consider it as one full year
                        diff = 12
                else:
                    start_date_str, end_date_str = duration
                    # If only the year is provided, consider the month as January
                    start_date = datetime.strptime(start_date_str if "/" in start_date_str else f"01/{start_date_str}", "%m/%Y")
                    if end_date_str.lower() in ['present', 'current', 'ongoing']:
                        end_date = datetime.today()
                    else:
                        end_date = datetime.strptime(end_date_str if "/" in end_date_str else f"01/{end_date_str}", "%m/%Y")
                    diff = abs(end_date.year - start_date.year) * 12 + abs(end_date.month - start_date.month)

                role_total_months += diff

            role_duration = role_total_months / 12  # converting to years
            full_dict['breakdown_experience'][role] = round(role_duration, 2)
            total_months += role_total_months

        except Exception as e:
            print(f"Error calculating duration for role '{role}': {e}")
            # Set this specific key's value to 0
            full_dict['breakdown_experience'][role] = 0

    if 'breakdown_experience' in full_dict and full_dict['breakdown_experience']:
        full_dict['total_years'] = round(total_months / 12, 2)  # converting to years

    return full_dict


def simplify_cv(cv):
    
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=openai.api_key)
    '''
    This function simplifies the CV in order for ChatGPT to better extract the information
    '''
        
    # Define simplify template
    prompt_template = """
    You will be provided with a resume in between 3 backticks. EXTRACT the JOB TITLES/POSITIONS WITH DATES from the WORK EXPERIENCE SECTION.
    
    This is the resume ```{cv}```.
    """
    
    # Define prompt
    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(prompt_template)
        ],
        input_variables=["cv"]
    )
    
    # Get output
    input = prompt.format_prompt(cv = cv)
    response = chat(input.to_messages())
    
    return (response.content)
    
def remove_companies(simplified_cv):
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=openai.api_key)
    '''
    This function simplifies the CV in order for ChatGPT to better extract the information
    '''
        
    # Define simplify template
    prompt_template = """
    You will be provided with a simplified resume in between 3 backticks. Remove the organization names and keep the job title and dates.
    
    This is the resume ```{simplified_cv}```.
    """
    
    # Define prompt
    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(prompt_template)
        ],
        input_variables=["simplified_cv"]
    )
    
    # Get output
    input = prompt.format_prompt(simplified_cv = simplified_cv)
    response = chat(input.to_messages())
    
    return (response.content)

def mini_cv(cv):
    simplified_cv = simplify_cv(cv)
    mini_cv = remove_companies(simplified_cv)
    return mini_cv

def get_breakdown(simplified_cv):
    
    '''
    Breakdown the experiences and the duration.
    '''
    
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=openai.api_key)
    
    # Define template
    prompt_template = """
    Given the following resume, delimited by 3 backticks, extract each role, and the start and end date of each role in MM/YYYY format.

    If the same job title is present multiple times, report all the start and end dates.

    Each job title should be treated as a unique entity and not combined with similar ones. For example, "AI Engineer" and "Machine Learning Engineer" are considered separate entities.
    
    The output is a JSON file. This is an example of the output: 
    {{"breakdown_experience": {{"Job Title 1": [[MM/YYYY, MM/YYYY], [MM/YYYY, MM/YYYY]], "Job Title 2": [[MM/YYYY, MM/YYYY]]}}}}
    
    
    This is the resume:
    ```{cv}```

    For instances where the end date is "Present" or "Current", keep them as is.
    """
    
    # Define output schema
    cv_breakdown_schema = ResponseSchema(name = 'breakdown_experience', description = 'breakdown of roles and start and end in each role.')
    
    # Define output parser
    response_schemas = [cv_breakdown_schema]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions
    
    # Define prompt
    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(prompt_template)
        ],
        input_variables=["cv"]
    )
    
    input = prompt.format_prompt(cv=simplified_cv)
    response = chat(input.to_messages())
    #print(response.content)
    
    # Try to parse
    output = handle_parsing_error(response.content, output_parser, "breakdown_experience")
            
    return output
    
def extract_skills(simplified_cv):
    '''
    Extract skills
    '''
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=openai.api_key)
    # Define template
    prompt_template = """

    Given the resume enclosed within triple backticks, extract all soft AND technical skills mentioned in the the work experiences, skills sections, technical environment section or any other sections.

    Skills must be 2-3 words maximum. Do not extract spoken languages.

    The extracted data should be returned in a Python dictionary or JSON object with the key 'skills'.
    {{"skills": ["Python", "Java", "SQL", "SVM", "Leadership", "PMP", "Project Management"]}}

    This is the resume:
    ```{simplified_cv}```
    """
    
    # Define output schema

    cv_skills_schema = ResponseSchema(name = 'skills', description = 'The skills of the candidate (Programming languages, frameworks, libraries, software, soft skills). 2-3 words max.')
    
    # Define output parser
    response_schemas = [cv_skills_schema]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
    
    # Define prompt
    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(prompt_template)
        ],
        input_variables=["simplified_cv"]
    )
    
    input = prompt.format_prompt(simplified_cv = simplified_cv)
    response = chat(input.to_messages())
    #print(response.content)
    
    # Try to parse
    output = handle_parsing_error(response.content, output_parser, "skills")
            
    return output
def clean_skills(skills_list):
    '''
    Extract skills
    '''
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=openai.api_key)
    # Define template
    prompt_template = """

    From the following list between three back ticks, return the skills that are MOST relevant to Computer Scientist, Mobile Developer, Solution Architect, IT, DevOps, Backend Engineer, Frontend Engineer, Software Engineer, Data Engineer, Web Developer, or similar jobs.

    This is the list:
    ```{skills_list}```
    
    It should be returned in JSON format with the key "skills".
    """
    
    # Define output schema

    cv_simple_skills_schema = ResponseSchema(name = 'skills', description = 'The skills of the candidate (Programming languages, frameworks, libraries, software, soft skills). 2-3 words max.')
    
    # Define output parser
    response_schemas = [cv_simple_skills_schema]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
    
    # Define prompt
    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(prompt_template)
        ],
        input_variables=["skills_list"]
    )
    
    input = prompt.format_prompt(skills_list = skills_list)
    response = chat(input.to_messages())
    
    # Try to parse
    output = handle_parsing_error(response.content, output_parser, "skills")
            
    return output

def parse_skills(cv):
    extracted_skills = extract_skills(cv)
    cleaned_skills = clean_skills(extracted_skills['skills'])
    return cleaned_skills

def extract_languages(simplified_cv):
    '''
    Extract languages
    '''
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=openai.api_key)
    # Define template
    prompt_template = """
    Given the resume enclosed within triple backticks, extract the following information: 'Languages Spoken'.

    Languages should be reported along with their proficiency level, ranked from 0 to 5 (0 being no proficiency, 1 being elementary proficiency, 2 being limited working proficiency, 3 being professional working proficiency/intermediate, 4 being full professional proficiency and 5 being native/fluent). If no proficiency level is provided, report as 'N/A'. Note that 'Fluent' is considered as a score of 5, 'Intermediate' as 3, and 'Elementary' as 1.
    If no language is mentioned at all, just return English with a proficiency of "N/A".

    The extracted data should be returned in a JSON object with the key 'languages'. For example:
    {{"languages": {{"English": 5, "French": 4, "Arabic": 4}}}}

    This is the resume:
    ```{simplified_cv}```
    """
    
    # Define output schema

    cv_languages_schema = ResponseSchema(name = 'languages', description = 'Languages should be reported along with their proficiency level, ranked from 0 to 5 (0 being no proficiency, 1 being elementary proficiency, 2 being limited working proficiency, 3 being professional working proficiency/intermediate, 4 being full professional proficiency and 5 being native/fluent). If no proficiency level is provided, report as N/A. Note that Fluent is considered as a score of 5, Intermediate as 3, and Elementary as 1.')
    
    # Define output parser
    response_schema = [cv_languages_schema]
    output_parser = StructuredOutputParser.from_response_schemas(response_schema)
    format_instructions = output_parser.get_format_instructions()
    
    # Define prompt
    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(prompt_template)
        ],
        input_variables=["simplified_cv"]
    )
    
    input = prompt.format_prompt(simplified_cv = simplified_cv)
    response = chat(input.to_messages())
    #print(response.content)
    
    # Try to parse
    output = handle_parsing_error(response.content, output_parser, "languages")
            
    return output

def get_relevance(breakdown_json, jd_json):
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=openai.api_key)
    '''
    Get relevance of experiences to the job description.
    '''
    # Define template
    prompt_template = """
    Rank the relevance of the positions extracted from the CV in the JSON file delimited by 3 backticks, to the job title extracted from the job description, found in the JSON delimited by 3 asterisks.
    Rank these from 0 to 5, 0 being irrelevant, and 5 being fully relevant.

    This is the JSON from the CV:
    ```{breakdown_json}```

    This is the JSON from the job description:
    ***{jd_json}***

    The output should be a JSON file. This is an example of the output:
    {{"experience_relevance": {{"Mechanical Engineer": 1, "AI Engineer": 5, "Computer Science": 4}}}}
    """
    # Define output schema
    cv_relevance_schema = ResponseSchema(name = 'experience_relevance', description = 'ranking of the relevance of the positions held to the job title in the job description.')    
    
    # Define output parser
    response_schemas = [cv_relevance_schema]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
    # Define prompt
    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(prompt_template)
        ],
        input_variables=["breakdown_json", "jd_json"]
    )
    
    input = prompt.format_prompt(breakdown_json = breakdown_json, jd_json = jd_json)
    response = chat(input.to_messages())
    #print(cv_rank_response.content)
    
    # Try to parse
    output = handle_parsing_error(response.content, output_parser, "experience_relevance")
            
    return output
    
    
def combine_cv_json(breakdown_json, skills_json, languages_json, relevance_json = {}):
    combined_json = breakdown_json | skills_json | languages_json | relevance_json
    parsed_cv = calculate_duration(combined_json)
    
    return parsed_cv
    
    