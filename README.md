# kyle_vella_DGD62B_DA
 
# Setup Instructions

1. Open the terminal in visual studio or visual studio code. Type 'python -m venv env'. This will create the environment.

2. Before typing 'env\Scripts\activate', enter 'Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Unrestricted' inside the terminal as this will enable you to activate the environment. Then enter 'env\Scripts\activate'.

3. Make sure you are in the environment by having (env) next to the file path

4. Enter 'pip install fastapi uvicorn motor pydantic python-dotenv requests python-multipart' on terminal inside the environment

5. After installing these dependencies, run 'pip freeze > requirements.txt' to display all dependencies installed

6. Finally, enter 'uvicorn main:app --reload' on the terminal