import os
import json
import shutil
import requests
import boto3
import argparse
import json
import tempfile
import subprocess
from pathlib import Path
from extract import extract_items


def upload_folder_to_s3(BUCKET_NAME, local_folder_path, userInput):
    s3 = boto3.client('s3')
    s3FolderName = userInput.get("s3FolderName", "default_folder")
    unique_folder_name = f"{s3FolderName}"
    s3_folder_path = f"{unique_folder_name}"
    
    for root, dirs, files in os.walk(local_folder_path):
        for file in files:
            local_file_path = os.path.join(root, file)
            # Normalize file paths to use forward slashes only
            s3_file_path = os.path.relpath(local_file_path, local_folder_path).replace("\\", "/")
            s3_key = f"{s3_folder_path}/{s3_file_path}"
            
            try:
                s3.upload_file(local_file_path, BUCKET_NAME, s3_key)
                # Optionally log success messages
                # print(f"Uploaded {local_file_path} to S3://{BUCKET_NAME}/{s3_key}")
            except Exception as e:
                print(f"Error uploading {local_file_path} to S3: {str(e)}")
    
    # Return only the path of the main folder created in S3
    return f"s3://{BUCKET_NAME}/{s3_folder_path}"



# Define a function to get the content of table_{table_index}.json
def get_table_content(table_index, tempdir_path):
    table_file_path = os.path.join(tempdir_path, f"table_{table_index}.json")
    if os.path.exists(table_file_path):
        with open(table_file_path, "r") as table_file:
            return json.load(table_file)
    else:
        print(f"Table file not found: {table_file_path}")
        return None
    
def get_slide_folders(slides_data, userInput,tempdir_path):
        image_index = 0
        table_index = 0

        main_folder_path = os.path.join(tempdir_path, "presentation_folder")
        os.makedirs(main_folder_path, exist_ok=True)

        # Iterate through each slide
        for slide in slides_data:
            slide_number = slide["slide_number"]
            slide_content = slide["elements"]

            # Append tags from user input to slide content
            slide_with_tags = {
                "presentationId": userInput["presentationId"],
                # "companyName": user_input["companyName"],
                "themeId": userInput["themeId"],
                "slideNumber": slide_number,
                "elements": slide_content
            }

            # Append all tags from user input to slide content dynamically
            for key, value in userInput.items():
                if key not in slide_with_tags:
                    slide_with_tags[key] = value

            # Create a folder for the slide
            slide_folder = os.path.join(main_folder_path, f"slide_{slide_number}")
            # slide_folder = os.path.join(KEY_PREFIX, f"slide_{slide_number}")
            os.makedirs(slide_folder, exist_ok=True)

            # Check if any image exists for this slide
            has_image = any("shape" in element and element["shape"] == "Image" for element in slide_content)
            # print("has image", has_image)

            # Check if any table exists for this slide
            has_table = any("shape" in element and element["shape"] == "Table" for element in slide_content)
            # print("has table", has_table)


            if has_image:
                # Create a folder for images in the slide
                image_folder = os.path.join(slide_folder, "images")
                os.makedirs(image_folder, exist_ok=True)

                #Iterate through slide content
                for element in slide_content:
                    if "shape" in element and element["shape"] == "Image":
                        # print("Trying to map the image")
                        image_name = f"image_{image_index}.png"
                        image_src = os.path.join(tempdir_path, image_name)
                        image_dest = os.path.join(image_folder, f"{image_name}")
                        # print("image_src", image_src)
                        # print("image_dest", image_dest)
                        # shutil.copy(image_src, image_dest)
                        # if os.path.exists(image_src):
                        #     print("Source image file exists")
                        # else:
                        #     print("Source image file does not exist")

                        try:
                            shutil.copy(image_src, image_dest)
                            # print("Image copied successfully")
                        except Exception as e:
                            print(f"Error copying image: {e}")

                        image_index += 1


            if has_table:
                for element in slide_content:
                    if "shape" in element and element["shape"] == "Table":
                        # print("Trying to map the table content")
                        table_content = get_table_content(table_index, tempdir_path)
                        if table_content:
                            element["data"] = table_content
                            # print("slide content", slide_content)
                        table_index += 1

            # Write JSON content to a file inside the slide folder
            with open(os.path.join(slide_folder, f"slide_{slide_number}.json"), "w") as f:
                json.dump(slide_with_tags, f, indent=4)




def organize_folders_and_upload(slide_data, tempdir_path, userInput):
    # Define constants for AWS S3
    BUCKET_NAME = 'revent-transform-files'
    # KEY_PREFIX = 'Doctoppt/'  # Ensure this is used as intended, possibly remove if not needed

    # Create folders for each slide and collect files
    get_slide_folders(slide_data, userInput, tempdir_path)

    # Path to the main presentation folder
    main_folder_path = os.path.join(tempdir_path, "presentation_folder")

    # Upload the entire main presentation folder to S3
    folder_path_in_s3 = upload_folder_to_s3(BUCKET_NAME, main_folder_path, userInput)

    # Cleanup: delete the temporary directory after upload
    try:
        shutil.rmtree(tempdir_path)
    except Exception as e:
        print(f"Error deleting temporary directory {tempdir_path}: {str(e)}")

    return folder_path_in_s3



# def organize_folders_and_upload(slide_data, tempdir_path, user_input,images_filenames):
#     # Define constants for AWS S3
#     BUCKET_NAME = 'revent-transform-files'
#     KEY_PREFIX = 'Doctoppt/'
#     # Call function to create folders for each slide
#     get_slide_folders(slide_data, user_input, tempdir_path,images_filenames)



#     # Path to the main presentation folder
#     main_folder_path = os.path.join(tempdir_path, "presentation_folder")

#     # Upload the entire main presentation folder to S3
#     paths = upload_folder_to_s3(KEY_PREFIX, BUCKET_NAME, main_folder_path,user_input)

#     # Cleanup: delete the temporary directory after upload
#     try:
#         shutil.rmtree(tempdir_path)
#         # print(f"Temporary directory {tempdir_path} deleted successfully.")
#     except Exception as e:
#         print(f"Error deleting temporary directory {tempdir_path}: {str(e)}")

#     return paths

