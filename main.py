import argparse
import os
import json
from docx import Document
import tempfile
import shutil
import boto3
from json_grid_recommendation import *
from summarize import *
from process import *



def parse_arguments():
    parser = argparse.ArgumentParser(description="Upload document to S3 and process slides")
    parser.add_argument("document_path", type=str, help="Path to the document file")
    parser.add_argument("--user_input", type=str, help="User input JSON string")
    args = parser.parse_args()
    return args

def extract_elements(docx_path):
    # print("Inside extract_elements")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_docx_path = os.path.join(temp_dir, os.path.basename(docx_path))
        shutil.copy(docx_path, temp_docx_path)
        tempdir = extract_items(temp_docx_path)
        md_path = os.path.join(temp_dir, "output.md")
        media_path = os.path.join(temp_dir, "media")
        return tempdir, md_path, media_path

def main():
    args = parse_arguments()
    document_path = args.document_path
    user_input = None
    if args.user_input:
        # print("User input from command line arguments:")
        # print(args.user_input)
        user_input = json.loads(args.user_input)
    else:
        print("no input in arg")

    if user_input is None:
        user_input = {
            "username": "XYZ",
            "DocumentId": 2,
            "presentationId": 254,
            "companyName": "TOTAL MEDIA SERVICE",
            "themecolor": "#E3B23C"
        }
    # user_input = json.loads(args.user_input) if args.user_input else {
    #     "username": "XYZ",
    #     "DocumentId": 2,
    #     "presentationId": 254,
    #     "companyName": "TOTAL MEDIA SERVICE",
    #     "themecolor": "#E3B23C"
    # }
    tempdir, md, media = extract_elements(document_path)
    tempdir_path = Path(tempdir)
    md_path = Path(md)
    media_path = Path(media)


    convert_docx_to_md_with_images(document_path, md_path, media_path)

    with open(md_path, "r") as md_file:
                md_content = md_file.read()

                chunk_size = 2000
                chunks = [md_content[i:i + chunk_size] for i in range(0, len(md_content), chunk_size)]

                extracted_elements = ""

                for chunk in chunks:

                    extracted_elements += extract_elements_from_markdown(chunk)

                # print("extracted_elements", extracted_elements)
                converted_text = convert_text_to_format(extracted_elements)
                # for title, element_type, content in converted_text:
                    # print(f"Title: {title}")
                    # print(f"{element_type}: {content}\n")


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
<<<<<<< HEAD
                # print(response_content)

                output = organize_folders_and_upload(slide_data, tempdir_path, user_input)

                return output
=======
   
                output = organize_folders_and_upload(slide_data, tempdir_path, user_input,images_filenames)
                return output 
>>>>>>> f1bd743800909986798306486bcb73b730ee137b

if __name__ == "__main__":
    output = main()
    print(output)
<<<<<<< HEAD








# import argparse
# import os
# import json
# from docx import Document
# import tempfile
# import shutil
# import boto3
# from json_grid_recommendation import *
# from summarize import *
# from process import *



# # def parse_arguments():
# #     parser = argparse.ArgumentParser(description="Upload document to S3 and process slides")
# #     parser.add_argument("document_path", type=str, help="Path to the document file")
# #     parser.add_argument("--user_input", type=str, help="User input JSON string")
# #     args = parser.parse_args()
# #     return args

# def extract_elements(docx_path):
#     # print("Inside extract_elements")
#     with tempfile.TemporaryDirectory() as temp_dir:
#         temp_docx_path = os.path.join(temp_dir, os.path.basename(docx_path))
#         shutil.copy(docx_path, temp_docx_path)
#         tempdir , images_filenames = extract_items(temp_docx_path)
#         md_path = os.path.join(temp_dir, "output.md")
#         media_path = os.path.join(temp_dir, "media")
#         return tempdir, md_path, media_path ,images_filenames

# def main(document_path, user_input_json):
#     print(user_input_json)
#     if not user_input_json:
#         user_input_json = {
#             "username": "XYZ",
#             "DocumentId": 2,
#             "presentationId": 254,
#             "companyName": "TOTAL MEDIA SERVICE",
#             "themecolor": "#E3B23C"
#         }
 
#     tempdir, md, media,images_filenames = extract_elements(document_path)
#     print(tempdir)
#     tempdir_path = Path(tempdir)
#     md_path = Path(md)
#     media_path = Path(media)


#     convert_docx_to_md_with_images(document_path, md_path, media_path)

#     with open(md_path, "r") as md_file:
#                 md_content = md_file.read()
            
#                 chunk_size = 2000  
#                 chunks = [md_content[i:i + chunk_size] for i in range(0, len(md_content), chunk_size)]

#                 extracted_elements = ""

#                 for chunk in chunks:
                    
#                     extracted_elements += extract_elements_from_markdown(chunk)
                    
#                 # print("extracted_elements", extracted_elements)
#                 converted_text = convert_text_to_format(extracted_elements)
#                 # for title, element_type, content in converted_text:
#                     # print(f"Title: {title}")
#                     # print(f"{element_type}: {content}\n")
                    
#                 json_output = convert_to_json(converted_text)
                

#                 # Processing large number of elements: considering 4 elements for 1 slide
#                 chunk_size = 1
#                 total_elements = len(json_output)

#                 slide_data = []

#                 for slide_number in range(0, total_elements, chunk_size):
#                 # This is for adding this message to the final response
#                     slide_number_display = slide_number // chunk_size + 1
        
#                     # Extracting data for the current slide
#                     slide_elements = json_output[slide_number:slide_number + chunk_size]
        
#                     # Adding slide data to the list
#                     slide_data.append({
#                     "slide_number": slide_number_display,
#                     "elements": slide_elements
#                     })

#                 # Constructing the response content with only slide data
#                 response_content = {"elements_per_slide": slide_data}
   
#     output = organize_folders_and_upload(slide_data, tempdir_path, user_input,images_filenames)


#     return output 

# if __name__ == "__main__":
#     main()
=======
>>>>>>> f1bd743800909986798306486bcb73b730ee137b


