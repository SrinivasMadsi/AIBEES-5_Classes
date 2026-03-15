## Install below libraries
"fastapi (==0.115.0)",
"uvicorn (==0.34.0)",
"google-cloud-aiplatform (==1.94.0)",
"python-multipart (>=0.0.22,<0.0.23)",

# Execute the below command first to authenticate
gcloud auth application-default login

# Also set your project
gcloud config set project YOUR_PROJECT_ID   #project-b629d2c5-6ec0-4b7d-b32
gcloud auth application-default set-quota-project YOUR_PROJECT_ID   #project-b629d2c5-6ec0-4b7d-b32


INDEX_ENDPOINT_ID=projects/YOUR_PROJECT_NUM/locations/us-central1/indexEndpoints/YOUR_ENDPOINT_ID
DEPLOYED_INDEX_ID=rag_deployed_index
INDEX_ID=your_index_id

Think of it like: Index = database, Endpoint = server, Deployed Index = the database mounted on that server.

# INDEX_ID
it is the vector search -> Indexes -> ID

# run below command to get the project number
cloud projects describe project-b629d2c5-6ec0-4b7d-b32 --format="value(projectNumber)"
you get something like : 633985011262

# INDEX_ENDPOINT_ID
Once index is deployed you ll get this url

## Run the code using below command
uvicorn main:app --reload --port 8000 

# Go to swagger UI
http://localhost:8000/docs#/


