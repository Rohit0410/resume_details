import os
import google.generativeai as genai
# import docx2txt
import nltk 
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('punkt_tab')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
stop_words = set(stopwords.words('english'))
import re
import random
import shutil
from llama_index.core import SimpleDirectoryReader
api_list = ["AIzaSyA51WTz0t69sBFs8D2ZmLLypKs6X9rIcEI","AIzaSyDlCk6V9XXwHEYJSjSC4-g28N69UgNcVYA"]
api_key=random.choices(api_list)
genai.configure(api_key=api_key[0])
import requests
import logging
import json
from flask import jsonify,Flask,request
import traceback

app = Flask(__name__)

def preprocessing(document):
    text = document.replace('\n', ' ').replace('\t', ' ').lower()
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    tokens = word_tokenize(text)
    tokens = [re.sub(r'[^a-zA-Z\s]', '', token) for token in tokens]
    tokens = [token for token in tokens if token and token not in stop_words]
    preprocessed_text = ' '.join(tokens)
    return preprocessed_text

def download_file(url, save_dir):
    try:
        # Get the filename from the URL
        file_name = os.path.basename(url)

        # Create the full path to save the file
        save_path = os.path.join(save_dir, file_name)

        # Send a GET request to download the file
        response = requests.get(url)
        response.raise_for_status()  # Raise an error if the download failed

        # Write the file to the local directory
        with open(save_path, 'wb') as file:
            file.write(response.content)

        print(f"File saved as: {save_path}")
        return save_path

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def get_gemini_response(input_text,prompt):
    input_text = preprocessing(input_text) 
    model=genai.GenerativeModel('gemini-1.5-flash')
    response=model.generate_content([input_text,prompt],generation_config = genai.GenerationConfig(
        temperature=0.3
    ))
    return response.text

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        data = SimpleDirectoryReader(input_files=[uploaded_file]).load_data()
        data1 = " ".join([doc.text for doc in data])
        print("DATA",data1)
        document_resume = " ".join([doc.text.replace('\n', ' ').replace('\t', ' ').replace('\xa0', ' ') for doc in data])
        final = preprocessing(document_resume)
        return data1,final
    else:
        raise FileNotFoundError("No file uploaded")
    
prompt="""
Extract the following information from the job description and format it as JSON:
- Title
- Company Name
- Hide Company (keep false)
- Qualification
- Job Type
- Workplace Type
- Experience (provide as an object with min and max values)
- Currency ( INR (₹))
- Salary (provide as an object with min and max values)
- Hide Salary (keep false)
- Hiring For
- Description
- Industries (provide as a list of strings)
- Skills (provide as a list of strings)
- Location (provide as a list of strings)

Provide the information in the following key-value format:

"title": "",
"company": "",
"hideCompany": "",
"qualification": "",
"jobType": "",
"workplaceType": "",
"experience": {
    "min": "",
    "max": ""
},
"currency": "",
"salary": {
    "min": "",
    "max": ""
},
"hideSalary": "",
"hiringFor": "",
"description": "",
"industries": [""],
"skills": [""],
"location": [""]

"""
@app.route('/v1/jd_autofilling', methods=['POST'])
def scoring():
    try:
        if 'jd_file' not in request.form:
            return jsonify({'error': 'Please provide a JD file.'}), 400

        jd = request.form['jd_file']
        print('resume',jd)

        resume_folder_path = r'temp5/'
        os.makedirs(resume_folder_path, exist_ok=True)

        resume_file_path = download_file(jd,resume_folder_path)
        print('jd_file_path',resume_file_path)
        
        # for i in resume_paths:
        data1,input_text = input_pdf_setup(resume_file_path)
        if input_text is None:
            return jsonify({'error': 'Error processing the JD file.'}), 500
        response = get_gemini_response(input_text,prompt)
        if response:
            try:
                # Remove any extra formatting or markdown if present
                clean_response = response.strip().strip('```json').strip('```')
                # Parse the cleaned response as JSON
                parsed_response = json.loads(clean_response)
                return jsonify({"data": parsed_response})
            except json.JSONDecodeError:
                logging.error("Error decoding JSON from response")
                return jsonify({"error": "Invalid JSON response"}), 500
            except Exception as e:
                logging.error(f"Error processing response: {e}")
                return jsonify({"error": "Response processing error"}), 500
        else:
            return jsonify({"error": "Failed to generate response."}), 500        
    except Exception as e:
        logging.error(f"An error occurred: {e}. Line: {traceback.format_exc()}")
        return jsonify({'error': 'An internal server error occurred.'}), 500
    
if __name__ == '__main__':
    app.run(debug=True,port=5005)

