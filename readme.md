DataInsight Pro - AI-Powered Data Analytics App
About the App
DataInsight Pro is an AI-powered data analysis and visualization application built with Streamlit for the frontend and FastAPI for the backend. The app supports uploading multiple file formats (CSV, PDF, DOCX, Excel), performs automatic data insights, natural language queries, and generates professional visualizations with customizable plots.

The backend uses powerful APIs and vector databases for fast query responses and intelligent analysis.

Features
Upload CSV, PDF, DOCX, Excel files for data analysis

Automatic AI-generated data summaries and insights

Natural language querying of uploaded datasets

Rich built-in and custom visualizations using Plotly

Seamless backend and frontend integration with API endpoints

Containerized with Docker for easy deployment on Render or locally

Getting Started
Prerequisites
Docker installed on your machine

Docker Hub account (optional for pulling images)

Render account (optional for deployment)

Running Locally with Docker
Clone this repository:

bash
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo/csv_doc_analyst
Build frontend and backend Docker images:

Backend:

bash
docker build -f Dockerfile.backend -t your_dockerhub_backend_image .
Frontend:

bash
docker build -f Dockerfile.frontend -t your_dockerhub_frontend_image .
Run backend (replace keys with your API keys):

bash
docker run -p 8000:8000 -e PINECONE_API_KEY='yourkey' -e GROQ_API_KEY='yourkey' -e COHERE_API_KEY='yourkey' your_dockerhub_backend_image
Run frontend (set backend API URL):

bash
docker run -p 8501:8501 -e API_URL='http://localhost:8000' your_dockerhub_frontend_image
Open your browser:

Frontend UI: http://localhost:8501

Backend docs (Swagger UI): http://localhost:8000/docs

Deploying on Render
Push your frontend and backend images to Docker Hub.

Create two new Web Services on Render:

Backend service: Use your backend image, port 8000, set required API keys as environment variables.

Frontend service: Use your frontend image, port 8501, set API_URL environment variable to backend's Render URL.

Deploy and access your apps via Render URLs.

Using the App with Sample Data
Upload the test datasets from the datasets directory:

sample_sales.csv

employee_performance.xlsx

You can use these files to test upload, query, and visualization features.

Contributing
Feel free to open issues or submit pull requests for improvements and bug fixes.