# CropWatch

## Overview
**CropWatch** provides predictive analytics for crop storage management, specifically targeting maize storage in Rwanda. It combines machine learning predictions with real-time weather data to help farmers monitor storage conditions continuously, predict spoilage percentages before they occur, receive actionable recommendations to prevent crop loss, and track storage sessions over time.  

## Features
The application offers:
- Secure user authentication with JWT tokens
- Automated daily ML-powered spoilage predictions 
- Real-time weather data integration for each district
- Context-aware smart notifications with risk assessment 
- On-demand predictions with custom inputs
- Profiles management with updates of users' information and preferences

## Important Links
Link to CropWatch: [CropWatch Website](https://cropwatch-management-system.onrender.com/login.html)


Link to Demo_video: 
[![Watch the video](https://img.youtube.com/vi/MMUu5lhs7qc/maxresdefault.jpg)](https://youtu.be/MMUu5lhs7qc)

### [Watch Solution Demonstration Demo](https://youtu.be/MMUu5lhs7qc)

Link to CropWatch FastAPI : [CropWatch FastAPI](https://cropwatch-1.onrender.com/docs) 

Link to Raw Datasets used in model training: [Raw Datasets](https://data.mendeley.com/datasets/fmtgzw5mmp/1) 

---

## Tech Stack
The backend is built with FastAPI (Python 3.11.9), PostgreSQL with SQLAlchemy ORM, JWT authentication, APScheduler for automation, and scikit-learn for machine learning. Security is handled through werkzeug password hashing.

The frontend uses HTML5, CSS3, and JavaScript with LocalStorage for tokens and cache, following an event-driven architecture. The infrastructure runs on Uvicorn server with python-dotenv for configuration management.


CropWatch/
├── api/
│   ├── main.py                     # FastAPI application & API endpoints
│
├── data/                           # Datasets used for model training
│   ├── Capstone_dataset.csv         # Cleaned dataset
│   └── Capstone_dataset_encoded.csv # Dataset with encoded categorical features
│
├── frontend/                       # Dashboard and static web interface
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── notifications.html
│   ├── analysis.html
│   │
│   ├── css/                        # Styling files
│   │   ├── index.css
│   │   ├── register.css
│   │   ├── login.css
│   │   ├── profile.css
│   │   ├── notifications.css
│   │   └── analysis.css
│   │
│   └── js/                         # Client-side logic
│       ├── api.js                  # API wrapper & HTTP client
│       ├── common.js               # Navigation & shared utilities
│       ├── register.js
│       ├── login.js
│       ├── profile.js
│       ├── notifications.js
│       └── analysis.js
│
├── model_training/
│   └── Capstone_Model_Training.ipynb  # Model training and evaluation notebook
│
├── models/                         # Serialized models and encoders
│   ├── best_xgb_model.pkl
│   └── encoder.pkl
│
├── weather_info/                   # Weather API integration modules
│   ├── locations.py
│   └── weather.py
│
├── database.py                     # Database schema and ORM models
├── automation.py                   # Automated scheduling and prediction tasks
├── preprocess.py                   # Feature engineering and preprocessing functions
├── model.py                        # Model loading and prediction logic
├── recommendations.py              # Risk assessment and recommendation engine
│
├── requirements.txt                # Project dependencies
└── README.md                       # Project documentation


---
## Environment Setup & Installation

Follow these steps to run the application:
1. Clone the Repository

```bash
clone https://github.com/Chrisos10/CropWatch.git
```
```bash
cd CropWatch
```

2. Create a Virtual Environment
```bash
python -m venv venv
```
Activate it using:
```bash
# On Windows
venv\Scripts\activate
```
```bash
# On Mac/Linux
source venv/bin/activate
```
3. Install the Requirements
```bash
pip install -r requirements.txt
```
This will install all the necessary libraries that will be used in this project.

4. Configure Environment Variables
Create a .env file in the project root and generate a secret key that will be used in your api using this link: https://generate-random.org/api-keys

Then in your .env file, add

SECRET_KEY=your-super-secret
DATABASE_URL=postgresql://username:password@localhost:5432/crop_storage_db

5. Initialize the Database
Create your POSTGRESQL datavase and after replacing your DATABASE_URL in your .env file, run
```bash
python database.py
```
6. Start the FastAPI Server
```bash
uvicorn main:app --reload
```
Access the application