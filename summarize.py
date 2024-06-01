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
        os.environ[api_key_env_var] = api_key  # Optionally, set the API key in environment variables for the current session
    # else:
    #     print("OpenAI API key found in environment variables.")
    
    return api_key

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
    # print("pandoc path = ", pandoc_path)
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
    Task: Tailored Document Summarization for Engaging Presentations

    Objective:
    Craft concise and meaningful summaries of elements from the markdown document, tailored for effective presentations. 
    Categorize elements as Paragraphs, Bullet Points, or Tables, and provide suitable slide titles for each. 


    Guidelines:
    Extract Key Points: Summarize the main ideas directly from the markdown document without incorporating any text from the prompt itself.
    
    Follow the Sequence: Extract elements from the markdown document in the order they appear, ensuring coherence with the original content flow.

    Paragraphs: Summarize paragraph content into impactful no more than 25 words summaries capturing key takeaways. Use the format 'Title: {title}', followed by 'Paragraph: {content}'.

    Bullet Points: Condense bullet points into clear and complete statements while maintaining hierarchy. Ensure a minimum of 2 bullet points per summary. Every sub point must not be longer than 10 words. Use the format 'Title: {title}', followed by 'Bullet Points: {content}'.

    Tables: Identify and preserve tabular structures from the markdown. Each row and column should be clearly identified. Present tables as raw markdown content in the format 'Title: {title}', followed by 'Table: {content}'.

    Image: Identify the caption if the image as it's content. Present the image caption in the format 'Title: {title}', followed by 'Image: {content}'.

    Additional Notes:

    Structured Content: Organize summaries into distinct sections under their respective headings for clarity and organization. Avoid merging the content of elements.

    Engaging Language: Use captivating language throughout, as if directly communicating with the audience. Employ vivid descriptions, concise phrases, and rhetorical devices to maintain audience engagement.

    Presentation Focus: Tailor summaries for presentation effectiveness, conveying key points in a concise and memorable manner.

    Slide Titles: Provide suitable titles for each extracted element to enhance presentation quality and clarity.

    The goal is to transform the markdown document into concise, engaging, and impactful summaries for an effective presentation, enhancing overall quality and clarity.
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
    # pattern = re.compile(r'Title: (.*?)\n(Paragraph|Bullet Points|Table):\s*(.*?)(?=\n\n(?:Title|Paragraph|Bullet Points|Table)|\Z)', re.DOTALL)
    pattern = re.compile(r'Title: (.*?)\n(Paragraph|Bullet Points|Table|Image):\s*(.*?)(?=\n\n(?:Title|Paragraph|Bullet Points|Table|Image)|\Z)', re.DOTALL)

    # Iterate through matches
    for match in pattern.finditer(text):
        title, element_type, content = match.groups()

        if element_type == 'Bullet Points':
            content = [point.strip().replace(':', '').replace('\"', '') for point in content.split('\n') if point]

        elif element_type == 'Paragraph':
            content = content.replace(':', '').replace('\"', '')

        elif element_type == 'Table':
            content = ""
            
        elif element_type == 'Image':
            content = ""

        result.append((title, element_type, content))

    return result
  

def convert_to_json(result_list):
    output_list = []

    for title, element_type, content in result_list:
        if element_type == 'Paragraph':
            content = re.sub(r'^\s*paragraph\s*|\s*Paragraph\s*', '', content)
            content = content.replace('\n', ' ')
            paragraph_data = {"title": title, "shape": "Paragraph", "data": [{"text": content}]}
            output_list.append(paragraph_data)

        elif element_type == 'Bullet Points':
            # bullet_points_data = [{"text": point} for point in content]
            bullet_points_data = [{"text": point.lstrip('- ')} for point in content]
            bullet_points_entry = {"title": title, "shape": "BulletTitle", "data": bullet_points_data}
            output_list.append(bullet_points_entry)

        elif element_type == 'Table':
            table_data = {"title": title, "shape": "Table", "data": content}
            output_list.append(table_data)

        elif element_type == "Image":
            image_data = {"title": title, "shape": "Image", "data": [{"Text": content}]}
            output_list.append(image_data)
            
    return output_list