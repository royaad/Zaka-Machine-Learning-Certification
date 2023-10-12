import openai
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from error_handler import fix_json

def handle_parsing_error(response, output_parser, counter = 0):
    if counter < 3:
        try:
            output = output_parser.parse(response)
            return output
        except Exception as e:
            print(f"Attempt {counter + 1} failed with error {e}. Attempting to fix...")
            fixed_json = fix_json(response)
            return handle_parsing_error(fixed_json, output_parser, counter + 1)
    else:
        return {"Error": "Unable to parse job description"}
    
def parse_jd(job_description):
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=openai.api_key)
    
    # Define template
    jd_parser_template = """
    Extract from the job description, delimited by 3 backticks, the following information:

    The job position/title: in 2-3 words.
    Total Years of Professional Experience Required: The years of experience required (MUST BE A NUMBER).
    Languages Required: The languages required. If no language is mentioned, just report English.
    Required Skills: The skills required (Programming languages, frameworks, libraries, software, soft skills) - You can deduce required skills from the job description.

    It is to be formatted as a JSON file with the following keys:
    job_title
    total_years_required
    languages
    skills_required

    This is an example of the format: job_title: 'Civil Engineer', total_years_required: 4.25, languages: ['English', 'French', 'Arabic', 'Spanish', 'German'], skills_required: ['Python', 'Java', 'SQL', 'SVM', 'Leadership', 'PMP', 'Project Management'].

    This is the job description:
    ```{job_description}```
    """
    
    # Define Output Schema
    jd_job_title_schema = ResponseSchema(name = 'job_title', 
                                         description = 'The job position/title: in 2-3 words')

    jd_years_schema = ResponseSchema(name = 'total_years_required', 
                                     description = 'Total Years of Professional Experience Required: The years of experience required (MUST BE A NUMBER).')

    jd_languages_schema = ResponseSchema(name = 'languages', 
                                         description = 'The languages required. If no language is mentioned, just report English.')

    jd_skills_required_schema = ResponseSchema(name = 'skills_required', 
                                               description = 'The skills required (Programming languages, frameworks, libraries, softwares, soft skills) - You can deduce required skills from the job description.')
    
    jd_response_schemas = [jd_job_title_schema, jd_years_schema, jd_languages_schema, jd_skills_required_schema]
    
    # Define Output Parser
    jd_output_parser = StructuredOutputParser.from_response_schemas(jd_response_schemas)
    jd_format_instructions = jd_output_parser.get_format_instructions()
    
    # Define Prompt
    jd_prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(jd_parser_template)
        ],
        input_variables=["job_description"]
    )
    
    # Format Prompt
    input = jd_prompt.format_prompt(job_description=job_description)
    
    # Get Response
    jd_response = chat(input.to_messages())
    
    # Try to parse
    output = handle_parsing_error(jd_response.content, jd_output_parser)
    
    return output