# CropWatch

## Description
**CropWatch** aims to serve as a predictive approach to reducing post-Harvest losses while minimizing pesticide dependency in Rwanda. It aims to train ML models under varying storage technologies and environmental conditions to predict spoilage risks and then suggest chemical-free interventions to mitigate the outbreak of the predicted risks.  

Model training integrated different steps like **data cleaning, feature exploration, non-linear relationship analysis, and model training** to identify patterns in crop spoilage and learn how to predict spoilage risks.  

This project leverages experimental data collected under **controlled and uncontrolled environments** and uses advanced models like **XGBoost, Gradient Boosting, and Random Forest** to identify the model that best captures the complex relationships among variables such as temperature, humidity, storage method, and duration.

---

## Important Links
Link to Figma Design Prototype: [Figma Prototype](https://www.figma.com/proto/HeYYfDZr1FuFhiuX3QKn9d/Untitled?node-id=55-110&t=To9ZBosESzdP5faF-1)


Link to Demo_video: [Demo Video](https://github.com/Chrisos10/CropWatch.git)


Link to Github Repo: [Repository](https://github.com/Chrisos10/CropWatch.git)

---

## Environment Setup & Installation

The project's development environment Ssetup required the following;

**Backend**:

- Python 3.10+ with FastAPI installed (pip install fastapi uvicorn).

- xgboost, pandas, numpy, scikit-learn installed.

- Virtual environment

Follow these steps to run it

#### 1. Clone the Repository
```bash
git clone https://github.com/Chrisos10/CropWatch.git
cd CropWatch
```
#### 2. Creating a Virtual Environment

```bash
python -m venv venv
```
Activate it using
```bash
# On windows
venv/Scripts/activate
```
```bash
# On Mac/Linux
source venv/bin/activate
```

#### 3. Installing The Requirements
```bash
pip install -r requirements.txt
```

This will install all the necessary libraries that will be used in this project.

#### 4. Testing The API:

Command to start FastAPI:
```bash
uvicorn main:app --reload
```

For Running the notebook, 
Download the notebook and the datasets and upload them to google drive. Then mount your google drive by running

```bash
from google.colab import drive
drive.mount('/content/drive')
```