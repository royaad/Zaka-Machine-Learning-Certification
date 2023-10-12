import openai
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate



def fix_json(json_string):
    
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=openai.api_key)
    '''
    This function simplifies the CV in order for ChatGPT to better extract the information
    '''
        
    # Define simplify template
    prompt_template = """
    Fix the JSON file, delimited by 3 ticks, to be in correct JSON format.
    
    Make sure the open and closing brackets are correctly placed.
    
    This is the JSON file to be fixed:
    ```{json_string}```
    """
    
    # Define prompt
    prompt = ChatPromptTemplate(
        messages=[
            HumanMessagePromptTemplate.from_template(prompt_template)
        ],
        input_variables=["json_string"]
    )
    
    # Get output
    input = prompt.format_prompt(json_string = json_string)
    response = chat(input.to_messages())
    
    return (response.content)
