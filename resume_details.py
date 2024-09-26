# from dotenv import load_dotenv

# load_dotenv()
import os
import google.generativeai as genai
import pandas as pd
import docx2txt
import nltk 
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('punkt_tab')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
stop_words = set(stopwords.words('english'))
import re
import requests
from llama_index.core import SimpleDirectoryReader
import random
api_list = ["AIzaSyA51WTz0t69sBFs8D2ZmLLypKs6X9rIcEI","AIzaSyDlCk6V9XXwHEYJSjSC4-g28N69UgNcVYA"]
api_key=random.choices(api_list)
print(api_key[0])
genai.configure(api_key=api_key[0])
from flask import Flask, jsonify, request
import logging
import traceback
import streamlit as st

# app =Flask(__name__)

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

def preprocessing(document):
    text = document.replace('\n', ' ').replace('\t', ' ').lower()
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    tokens = word_tokenize(text)
    tokens = [re.sub(r'[^a-zA-Z\s]', '', token) for token in tokens]
    tokens = [token for token in tokens if token and token not in stop_words]
    preprocessed_text = ' '.join(tokens)
    return preprocessed_text


def get_gemini_response(input_text,prompt):
    model=genai.GenerativeModel('gemini-1.5-flash')
    response=model.generate_content([input_text,prompt],generation_config = genai.GenerationConfig(
        temperature=0.1
    ))
    return response.text

def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        data = SimpleDirectoryReader(input_files=[uploaded_file]).load_data()
        data1 = " ".join([doc.text for doc in data])
        print("DATA",data1)
        document_resume = " ".join([doc.text.replace('\n', ' ').replace('\t', ' ').replace('\xa0', ' ') for doc in data])
        # final = preprocessing(document_resume)
        return data1,document_resume
    else:
        raise FileNotFoundError("No file uploaded")
    
Prompt = """Please extract the following information from the attached resume in the exact format provided below. 
Ensure the data is as it appears in the resume, and if certain details are not available, mark them as "Not Available".

Data=[
- Designation:
- Years of Experience(calculate it if not mentioned directly, only numeric number):
- Current Organization:

- Skills (List all relevant and valid skills mentioned. "," seperated):

- Education History (from oldest to latest):
    {NameInstitution: ,
    Degree: ,
    FieldStudy: ,
    Grade (if available): ,
    Start Year & Month: , 
    End Year & Month: ,
    Description (if available): ,}//n

- Professional Experience (from oldest to latest, no personal projects/work):
    {Company Name: ,
    Role/Title: ,
    Location: ,
    Employment Type (e.g., Full-time, Part-time, Internship): ,
    Start Year & Month: , 
    End Year & Month: ,
    Skills Used for this job: ,
    Description of Roles and Responsibilities: ,
    Achievement: ,
    Rewards: 
    }//n

- First Name:
- Last Name:
- Current Location: 
- Professional Summary: 
- Rewards(overall): 
- Achievement(overall): 
]

"""

prompt1 = """you are an expert resume builder and you have this resume data.
create a new perfectly structured resume using this provided data. hide the organization/company while recreating the professional resume.
"""

key_mapping_edu = {
    "Degree": "degree",
    "Description (if available)": "description",
    "Start Year & Month": "startDate",
    "End Year & Month": "endDate",
    "FieldStudy": "fieldOfStudy",
    "Grade (if available)": "grade",
    "NameInstitution": "institute"
}

key_mapping_prof = {"Company Name":"organization" ,
    "Role/Title":"designation" ,
    "Location":"location" ,
    "Employment Type (e.g., Full-time, Part-time, Internship)":"employmentType" ,
    "Start Year & Month":"startDate" ,
    "End Year & Month":"endDate" ,
    "Skills Used":"skillUsed" ,
    "Description of Roles and Responsibilities":"description",
    "Achievement":"achievement" , "Rewards":"rewards"
    }

st.markdown('''# Auto Resume Filling 🌟''')

uploaded_file=st.file_uploader("Upload your resume...",accept_multiple_files=True)
print("uploaded files",uploaded_file)

if uploaded_file is not None:
    st.write("PDF Uploaded Successfully")

submit1 = st.button("Data Segregation")

try:
    # for i in resume_paths:
    if submit1:
        Dict = {}
        resume_embeddings = []  # Dictionary to store resume embeddings
        not_uploaded=[]
        RESUME_folder_path = r'D:\Rohit\jdcv_score_app\jdcv_score_app\resume_Details\temp5'
        os.makedirs(RESUME_folder_path,exist_ok=True)
        print(f"The directory {RESUME_folder_path} has been created successfully.")
        # data1,input_text = input_pdf_setup(uploaded_file)

        if uploaded_file is not None:
            for i in uploaded_file:
                print('kkkkkkk',len(uploaded_file))
                print('done')
                if i is not None:
                    try:
                        file_path = os.path.join(RESUME_folder_path, i.name)
                        print('FILE',file_path)
                        with open(file_path, "wb") as f:   
                            f.write(i.getbuffer()) 
                            resume_embeddings.append(file_path)
                            print('ttt',resume_embeddings)
                    except Exception as e:
                        print('hh')
            for i in resume_embeddings:
                data1,pdf_content = input_pdf_setup(i)
                print('pdf',pdf_content)
                response=get_gemini_response(Prompt,pdf_content)
                st.subheader(os.path.basename(i))
                # st.write(str(i))
                # st.write(response)
        
        # print(input_text)
        
        phone_pattern1 = re.compile(r'\+?\d{1,3}[-.\s]?\d{10}')
        phone_pattern2=re.compile(r'\+?\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}')
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        social_media_pattern = re.compile(r'(https?://(?:www\.)?(?:linkedin|github|twitter|facebook|instagram)\.com/[^\s]+)')

        phone_numbers = phone_pattern1.findall(data1.replace("-",""))    
        print(phone_numbers)
        if not phone_numbers:
            phone_numbers = phone_pattern2.findall(data1)
        emails = email_pattern.findall(data1)
        emails=str(emails)
        social_media_links = social_media_pattern.findall(data1)
        social_media_links=list(social_media_links)
        valid_phone_numbers = [num for num in phone_numbers if 10 <= len(re.sub(r'\D', '', num)) <= 12]

        print(valid_phone_numbers)

        Country_code=''

        if len(valid_phone_numbers[0])==10:
            Country_code = ''
            valid_phone_numbers=valid_phone_numbers[0]
        elif len(valid_phone_numbers[0])>=12:
            Country_code = valid_phone_numbers[0][1:3]
            valid_phone_numbers=valid_phone_numbers[0][-10:]

        

        response = get_gemini_response(pdf_content,Prompt)
        print("response",response)
        
        t=response.split("\n-")
        print(t[-1])

        Designation = t[1].replace("Designation:","").replace('\n','')
        total_exp=t[2].replace("Years of Experience:","").replace('\n','')
        organization=t[3].replace("Current Organization:","").replace('\n','')
        skills=t[4].replace("Skills (List all relevant and valid skills mentioned):","").replace('\n','').replace("Skills:","")
        name=t[7].replace("First Name:","").replace('\n','').replace('[','').replace(']','')
        surname=t[8].replace("Last Name:","").replace('\n','').replace('[','').replace(']','')
        phone=str(valid_phone_numbers).replace('[','').replace(']','')
        country=Country_code.replace('[','').replace(']','')
        email=emails.replace('[','').replace(']','')
        social=social_media_links #.replace('[','').replace(']','')
        location=t[9].replace("Current Location:","").replace('\n','').replace('[','').replace(']','')
        summary = t[10]

        educationHistory=t[5].replace("Education History (from oldest to latest):","").replace('\n','').replace('Education History:',"").replace("{","").replace("}","")
        edu=[element for element in educationHistory.split("//n") if len(element) > 0]
        final_edu=[]
        for i in edu:
            pairs = i.strip().split(',')
            result_dict={}
            for pair in pairs:
                if ':' in pair:  # Ensure there is a key-value pair to split
                    key, value = pair.split(":", 1)  # Split by the first occurrence of ":"
                    result_dict[key.strip()] = value.strip()
                    new_dict = {key_mapping_edu[key]: value for key, value in result_dict.items() if key in key_mapping_edu}
            final_edu.append(new_dict)

        final_edu1 = final_edu.copy()
        for i in final_edu1:
            if "NameInstitution" in i:
                del i['NameInstitution']
        print(final_edu1)
        

        professionalExperience=t[6].replace("Professional Experience (from oldest to latest):","").replace("{","").replace("}","").replace("Professional Experience:","")
        prof=[element for element in professionalExperience.split("//n") if len(element) > 0]
        final_prof=[]
        for i in prof:
            pairs = i.strip().split(',')
            result_dict={}
            for pair in pairs:
                if ':' in pair:  # Ensure there is a key-value pair to split
                    key, value = pair.split(":", 1)  # Split by the first occurrence of ":"
                    result_dict[key.strip()] = value.strip()
                    new_dict = {key_mapping_prof[key]: value for key, value in result_dict.items() if key in key_mapping_prof}
            final_prof.append(new_dict)
        
        final_prof1 = final_prof.copy()
        for item in final_prof1:
            if "Company Name" in item:
                del item["Company Name"]
        print('fianl prof1', final_prof1)


        final = {'designation':Designation,
                'totalExperience':int(total_exp),
                "organization":organization,
                "SkillsInfo":skills,
                'firstName':name,
                'lastName':surname,
                'phoneNo':int(phone),
                "email":email,
                "socialInfo":social,
                "countryCode":int(country),
                'location':location,
                "educationHistory":final_edu, "professionalHistory":final_prof,"yearOfExperience":int(total_exp),"summary":summary}
        
        print('final',final)

        formatted_string = f"""
        Designation: {Designation}
        Total Experience: {int(total_exp)} years
        Skills: {skills}
        Country Code: {int(country)}
        Location: {location}
        Education History: {final_edu1}
        Professional History: {final_prof1}
        Professional Summary: {summary}
        """
        
        print(formatted_string)
        formatted_string_clean = formatted_string.encode('ascii', 'ignore').decode('utf-8')
        print(formatted_string_clean)
        
        para = get_gemini_response(formatted_string_clean,Prompt)
        print(para)
        # print(t)
        # print("---------",jsonify(final, para),200)
        st.write(final)
        st.write(para)

except Exception as e:
    logging.error(f"An error occurred: {e}. Line: {traceback.format_exc()}")
    st.error({'error': 'An internal server error occurred.'}), 500

