
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from typing import Optional
import os
import json
import uuid
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE
import boto3
from dotenv import load_dotenv
from main1 import *  

# Load environment variables
load_dotenv()

# Get AWS credentials from environment variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

app = FastAPI()

# Initialize the SQS client using environment variables for credentials
sqs_client = boto3.client(
    'sqs',
    region_name='ap-south-1',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)
queue_url = 'https://sqs.ap-south-1.amazonaws.com/375008366655/revent-transform-response-queue'

def process_document_background(documentPath: str, user_input_json: dict, request_id: str):
    try:
        command = ["python", "main1.py", documentPath, "--userInput", json.dumps(user_input_json)]
        process = Popen(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            # Capture the output from the main function
            s3_url = stdout.strip()

            # Send the result to SQS
            sqs_message = {
                "requestId": request_id,
                "status": "SUCCESS",
                "s3Url": s3_url
            }
            sqs_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(sqs_message))
        else:
            raise Exception(stderr)
    except Exception as e:
        # Send the error to SQS
        sqs_message = {
            "requestId": request_id,
            "status": "ERROR",
            "errorMessage": str(e)
        }
        sqs_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(sqs_message))

@app.post("/get_recommendations_for_slides_based_on_doc")
async def process_document(
    document: UploadFile = File(...), 
    userInput: str = Form(default=''), 
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # Generate unique request ID
    request_id = str(uuid.uuid4())

    # Save the uploaded document
    with NamedTemporaryFile(delete=False) as tmp:
        tmp.write(document.file.read())
        documentPath = tmp.name

    # Convert user_input from string to JSON if non-empty
    user_input_json = json.loads(userInput) if userInput else {}

    # Schedule background processing
    background_tasks.add_task(process_document_background, documentPath, user_input_json, request_id)

    # Return immediate response
    return {"requestId": request_id, "status": "RECEIVED"}




















# from fastapi import FastAPI, File, UploadFile, Form
# from typing import Optional
# import os
# import json
# import uuid
# from tempfile import NamedTemporaryFile
# from subprocess import Popen, PIPE
# import boto3
# from dotenv import load_dotenv
# from main import *

# # Load environment variables
# load_dotenv()

# # Get AWS credentials from environment variables
# aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
# aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

# app = FastAPI()

# # Initialize the SQS client using environment variables for credentials
# sqs_client = boto3.client(
#     'sqs',
#     region_name='ap-south-1',
#     aws_access_key_id=aws_access_key_id,
#     aws_secret_access_key=aws_secret_access_key
# )
# queue_url = 'https://sqs.ap-south-1.amazonaws.com/375008366655/revent-transform-response-queue'

# @app.post("/get_recommendations_for_slides_based_on_doc")
# async def process_document(document: UploadFile = File(...), user_input: str = Form(...)):
#     # Generate unique request ID
#     request_id = str(uuid.uuid4())

#     # Save the uploaded document
#     with NamedTemporaryFile(delete=False) as tmp:
#         tmp.write(document.file.read())
#         document_path = tmp.name

#     # Convert user_input from string to JSON
#     user_input_json = json.loads(user_input)

#     command = ["python", "main1.py", document_path, "--user_input", json.dumps(user_input_json)]
#     process = Popen(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
#     stdout, stderr = process.communicate()

#     if process.returncode == 0:
#         # Capture the output from the main function
#         s3_url = stdout.strip()

#         # Send the result to SQS
#         sqs_message = {
#             "requestId": request_id,
#             "status": "SUCCESS",
#             "s3Url": s3_url
#         }
#         sqs_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(sqs_message))

#         # API Response
#         return {"requestId": request_id, "status": "SUCCESS"}
#     else:
#         # Send the error to SQS
#         sqs_message = {
#             "requestId": request_id,
#             "status": "ERROR",
#             "errorMessage": stderr
#         }
#         sqs_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(sqs_message))

#         return {"requestId": request_id, "status": "ERROR", "errorMessage": stderr}
