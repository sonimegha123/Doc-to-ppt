from fastapi import FastAPI, File, UploadFile, Form
from typing import Optional
import os
import json
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE
from main import *

app = FastAPI()

@app.post("/get_recommendations_for_slides_based_on_doc")
async def process_document(document: UploadFile = File(...), user_input: str = Form(...)):
    # Save the uploaded document
    with NamedTemporaryFile(delete=False) as tmp:
        tmp.write(document.file.read())
        document_path = tmp.name

    # Convert user_input from string to JSON
    user_input_json = json.loads(user_input)

    command = ["python", "main1.py", document_path, "--user_input", json.dumps(user_input_json)]
    process = Popen(command, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        # Capture the output from the main function
        main_output = stdout.strip()
        return {"output": main_output}
    else:
        return {"error": stderr}








# from fastapi import FastAPI, File, UploadFile, Form
# from typing import Optional
# import os
# import json
# from tempfile import NamedTemporaryFile
# from subprocess import Popen, PIPE
# import uvicorn
# from main import *


# app = FastAPI()

# @app.post("/get_recommendations_for_slides_based_on_doc")
# async def process_document(document: UploadFile = File(...), user_input: str = Form(...)):
#     # Save the uploaded document to a temporary file
#     with NamedTemporaryFile(delete=False) as tmp:
#         contents = await document.read()  # Read file asynchronously
#         tmp.write(contents)
#         document_path = tmp.name  # Temporary file path

#     # Convert user_input from string to JSON
#     user_input_json = json.loads(user_input)

#         # Execute the main function with the document path and user input JSON
#     try:
#         result = main(document_path, user_input_json)  # Adjust the main function to accept these parameters directly

#         # Clean up the temporary file
#         os.unlink(document_path)

#         return {"message": "Document processed successfully", "data": result}
#     except Exception as e:
#         # Clean up the temporary file in case of exception too
#         os.unlink(document_path)
#         return {"error": f"An exception occurred: {str(e)}"}

#     # Run your existing script with the document path and user input
#     command = ["python", "main.py", document_path, "--user_input", json.dumps(user_input_json)]
    
#     try:
#         process = Popen(command, stdout=PIPE, stderr=PIPE)
#         stdout, stderr = process.communicate()

#         # Clean up the temporary file
#         os.unlink(document_path)

#         if process.returncode == 0:
#             return {"message": "Document processed successfully", "output": stdout.decode('utf-8')}
#         else:
#             return {"error": "Error processing document", "stderr": stderr.decode("utf-8")}
#     except Exception as e:
#         return {"error": f"An exception occurred: {str(e)}"}

# # if __name__ == "__main__":
# #     import uvicorn
# #     uvicorn.run(app, host="0.0.0.0", port=8000)