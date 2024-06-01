from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tempfile import TemporaryDirectory
from typing import List
import os
import tempfile
import json
import logging
import shutil
from pathlib import Path


from json_grid_recommendation import *
from summarize import *
from extract import extract_items
from process import *

app = FastAPI()


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(self.format(record))

log_handler = LogCaptureHandler()
logger.addHandler(log_handler)

# Mount the static folder to serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=FileResponse)
async def read_root():
    return "static/file.html"

@app.post("/get_recommendations_for_slides_based_on_doc")
async def extract_elements(file: UploadFile = File(...)):
    print("Inside extract_elements")
    with tempfile.TemporaryDirectory() as temp_dir:
        docx_path = os.path.join(temp_dir, file.filename)
        with open(docx_path, "wb") as temp_file:
            temp_file.write(await file.read())

        tempdir = extract_items(docx_path)
        tempdir_path = Path(tempdir)
        print("temp dir in api", tempdir_path)

        # Pass tempdir to process.py
        subprocess.run(['python', 'process.py', docx_path, tempdir]) 

        print("Image and table Extraction complete")

        md_path = os.path.join(temp_dir, "output.md")
        media_path = os.path.join(temp_dir, "media")

        convert_docx_to_md_with_images(docx_path, md_path, media_path)

        with open(md_path, "r") as md_file:
            md_content = md_file.read()
        
            chunk_size = 2000  
            chunks = [md_content[i:i + chunk_size] for i in range(0, len(md_content), chunk_size)]

            extracted_elements = ""

            for chunk in chunks:
                
                extracted_elements += extract_elements_from_markdown(chunk)
                
            # print("extracted_elements", extracted_elements)
            converted_text = convert_text_to_format(extracted_elements)
            for title, element_type, content in converted_text:
                print(f"Title: {title}")
                print(f"{element_type}: {content}\n")
                
            
            json_output = convert_to_json(converted_text)
        

            # Processing large number of elements: considering 4 elements for 1 slide
            chunk_size = 1
            total_elements = len(json_output)

            slide_data = []

            for slide_number in range(0, total_elements, chunk_size):
            # This is for adding this message to the final response
                slide_number_display = slide_number // chunk_size + 1
    
                # Extracting data for the current slide
                slide_elements = json_output[slide_number:slide_number + chunk_size]
    
                # Adding slide data to the list
                slide_data.append({
                "slide_number": slide_number_display,
                "elements": slide_elements
                })

            # Constructing the response content with only slide data
            response_content = {"elements_per_slide": slide_data}

            

            # Returning the JSON response
            return JSONResponse(content=response_content)
