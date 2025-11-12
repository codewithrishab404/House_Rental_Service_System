
# STEP1: Create Virtual Environment:
python3 -m venv backendvenv


# STEP2: Now Activate the Virtual Environment:
 # (Mac/Linux)
source backendvenv/bin/activate  
# OR on Windows:
backendvenv\Scripts\activate


# STEP3: Install dependencies :
 # For MacOS / Linux
pip install -r requirements.txt

 # For Windows:
pip install -r windows_requirements.txt

# STEP4 : Run the app
uvicorn main:app --reload
