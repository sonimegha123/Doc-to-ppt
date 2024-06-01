import subprocess
import os
import streamlit as st
import openai
from openai import OpenAI
import json
import re
import tempfile
import dotenv
import getpass


# Load environment variables from a .env file
dotenv.load_dotenv()

# Get the OpenAI API key securely
def get_openai_api_key():
    api_key_env_var = "OPENAI_API_KEY"
    api_key = os.getenv(api_key_env_var)
    
    if api_key is None:
        print("OpenAI API key not found in environment variables.")
        api_key = getpass.getpass("Enter OpenAI API Key: ")
        os.environ[api_key_env_var] = api_key  
    else:
        print("OpenAI API key found in environment variables.")
    
    return api_key

# Get the API key
api_key = get_openai_api_key()

client = OpenAI(api_key=api_key)

def convert_docx_to_md_with_images(docx_file_path, md_path, media_path):
    if not os.path.exists(media_path):
        os.makedirs(media_path)
    
    with open(docx_file_path, "rb") as f:
        docx_content = f.read()

    temp_docx_path = tempfile.mktemp(suffix=".docx")
    with open(temp_docx_path, "wb") as temp_docx:
        temp_docx.write(docx_content)

    pandoc_path = os.getenv('PANDOC_PATH')
    print("pandoc path = ", pandoc_path)
    if pandoc_path is None:
        raise ValueError("PANDOC_PATH environment variable is not set. Please check your .env file or environment variables.")

    temp_file_dir = os.getenv('TEMP_FILE_PATH', tempfile.gettempdir()) # Default path if not specified in .env

    temp_docx_path = os.path.join(temp_file_dir, os.path.basename(tempfile.mktemp(suffix=".docx")))

    with open(docx_file_path, "rb") as f:
        docx_content = f.read()

    with open(temp_docx_path, "wb") as temp_docx:
        temp_docx.write(docx_content)

    try:
        subprocess.run([pandoc_path, "-s", temp_docx_path, "-t", "markdown", "--extract-media", media_path, "-o", md_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")
    finally:
        os.remove(temp_docx_path)


def extract_elements_from_markdown(markdown_content):

    prompt = """
    Task: Fact Extraction for Engaging Presentations

Objective:
Your task is to extract factual information from the provided markdown document, specifically tailored for effective presentations. Categorize each element into the following types: Paragraph, Bullet Points, and Table. For each identified element, focus on presenting key facts and data without narrative language or conclusions. Provide suitable titles for each extracted element to be used as slide titles.

Guidelines:

Paragraph: Extract key facts and information from paragraphs in a concise and straightforward manner. Output the extracted factual content in the format 'Title: {title}', followed by 'Paragraph: {content}'. Avoid using a narrative style in the content.

Bullet Points: Reframe bullet points into concise factual statements, ensuring clarity and completeness. There should be a minimum of 2 sub points in every bullet point category. Maintain the original structure, including hierarchy and subpoints. Output the extracted factual content in the format 'Title: {title}', followed by 'Bullet Points: {content}''. Do not include the word "Paragraph" within bullet point text.

Table: Identify tables based on the presence of vertical bars ("|") indicating columns and rows. Preserve the tabular structure exactly as in the original markdown. Each row and column should be clearly identified. Do not introduce additional paragraphs or bullet points within the table section. Tables should be presented as raw markdown content. Output in the format 'Title: {title}', followed by 'Table: {content}'.

Additional Notes:

Structured Content: Organize extracted factual information into distinct sections under their respective headings for Paragraph, Bullet Points, and Table. This creates a clear and organized presentation structure.

Engaging Language: Use language that maintains engagement while prioritizing factual accuracy over style. Avoid a narrative writing style. Focus on presenting key facts and data in a concise and clear manner.

Presentation Focus: Tailor extracted information specifically for presentation effectiveness, ensuring clarity and relevance to the audience.

Slide Titles: Provide appropriate titles for each extracted element to be used as slide titles, enhancing the overall presentation's quality and clarity.

Remember, the goal is to extract factual information from the provided markdown document, presenting it in a clear and engaging manner suitable for presentation slides. Your ability to extract key facts and data will enhance the overall presentation's quality and effectiveness.
    """
    
    full_prompt = prompt + markdown_content

    response = client.chat.completions.create(model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an assistant helping with the extraction of elements from a markdown document."},
        {"role": "user", "content": full_prompt}
    ],
    max_tokens=2000,
    temperature=0.7)

    extracted_elements = response.choices[0].message.content
    
    if isinstance(extracted_elements, list):
        extracted_elements = " ".join(extracted_elements)

    return extracted_elements


def convert_text_to_format(text):
    result = []

    # Define the pattern to capture each element with title
    pattern = re.compile(r'Title: (.*?)\n(Paragraph|Bullet Points|Table):\s*(.*?)(?=\n\n(?:Title|Paragraph|Bullet Points|Table)|\Z)', re.DOTALL)

    # Iterate through matches
    for match in pattern.finditer(text):
        title, element_type, content = match.groups()

        if element_type == 'Bullet Points':
            content = [point.strip().replace(':', '').replace('\"', '') for point in content.split('\n') if point]

        elif element_type == 'Paragraph':
            content = content.replace(':', '').replace('\"', '')

        elif element_type == 'Table':
            content = content.strip().split('\n')

        result.append((title, element_type, content))

    return result
  

def convert_to_json(result_list):
    output_list = []

    for title, element_type, content in result_list:
        if element_type == 'Paragraph':
            content = content.replace('\n', ' ')
            paragraph_data = {"title": title, "shape": "Paragraph", "data": [{"text": content}]}
            output_list.append(paragraph_data)

        elif element_type == 'Bullet Points':
            bullet_points_data = [{"text": point} for point in content]
            bullet_points_entry = {"title": title, "shape": "Bullet Points", "data": bullet_points_data}
            output_list.append(bullet_points_entry)

        elif element_type == 'Table':
            table_data = {"title": title, "shape": "Table", "data": [{"Text": content}]}
            output_list.append(table_data)

    return output_list
