# Revent_Doc_to_PPT
This is a FastAPI application designed to extract elements from a document and provide recommendations for slides based on the extracted elements.  

**Usage**
1. Clone the repository to your local machine:  

2. Install the required dependencies:  
pip install -r requirements.txt

3. Change the Pandoc path in .env file   

4. Run the fastAPI application:  
uvicorn api1:app --reload  

5. Access the API via http://localhost:8000 in your browser.  

**Endpoints**

POST /get_recommendations_for_slides_based_on_doc - Process the Document file and convert it into multiple slides Store the slides in JSON format in AWS ECR.

**Curl Command**
curl -X POST "http://localhost:8000/get_recommendations_for_slides_based_on_doc" -F "document=@\"C:\Users\Aditya\Downloads\The Transformative Power of Artificial Intelligence.docx\"" -F "user_input={\"username\": \"SCMProject\", \"Folder_Name\": \"third_folder_docker\", \"DocumentId\": 3, \"presentationId\": 255, \"companyName\": \"TOTAL MEDIA SERVICE\", \"themecolor\": \"#E3B23C\"}"


**File Structure**

main1.py: Main script containing the lates code. 
api1.py : lates api code.
json_grid_recommendation.py: Script for recommending grids.  
test.py: Script to convert docx into markdown and extracting elements using openAI integration(currently takes 3-4 mins to process).  
static/: Contains an HTML file providing a frontend interface for users to upload Word documents and generate slide recommendations. 
