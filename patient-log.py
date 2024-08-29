import streamlit as st
import speech_recognition as sr
from mistralai import Mistral
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Initialize Mistral API
api_key = os.environ['MISTRAL_API_KEY']
client = Mistral(api_key=api_key)

# Streamlit App Title
st.title("Medical Assistant Streamlit App")

# Function to continuously capture audio and stop on "stop recording"
def capture_audio():
    r = sr.Recognizer()
    st.write("Adjusting for ambient noise... Please wait.")
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1)
        st.write(f"Listening... You can say 'stop recording' to finish.")
        text = ""
        while True:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            try:
                phrase = r.recognize_google(audio).lower()
                st.write(f"Recognized: {phrase}")
                if "stop recording" in phrase:
                    st.write("Stopping recording.")
                    break
                text += " " + phrase
            except sr.UnknownValueError:
                st.write("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                st.write(f"Could not request results from Google Speech Recognition service; {e}")
                break
    return text.strip()

# Function to transcribe audio using Mistral API
def mistral_transcription(text):
    response = client.chat.complete(
        model='mistral-small-latest',
        messages=[{"role": "user", "content": f"summarize this conversation in one paragraph: {text}"}]
    )
    transcription = response.choices[0].message.content
    st.write(f"Transcription from Mistral: {transcription}")
    return transcription

# Function to generate medical phrases based on a speech prompt
def generate_diagnostics(prompt):
    try:
        # Call Mistral API for generating diagnostics
        response = client.chat.complete(
            model='mistral-small-latest',
            messages=[{"role": "user", "content": f"Based on the input by the doctor, generate a numbered list of potential diagnostics based on the input: {prompt}"}]
        )
        diagnostics = response.choices[0].message.content
        # Extract diagnostics into a list
        diagnostics_list = re.findall(r'\d+\.\s*(.*)', diagnostics)
        return diagnostics_list
    except Exception as e:
        st.error(f"Error generating diagnostics: {e}")
        return []
    

# Section 1: Audio Capture and Transcription
st.header("1. Capture and Transcribe Patient-Doctor Dialogue")
if st.button("Start Recording"):
    transcript = capture_audio()
    if transcript:
        mistral_transcription(transcript)

def generate_diagnostics(prompt):
    try:
        # Call Mistral API for generating diagnostics
        response = client.chat.complete(
            model='mistral-small-latest',
            messages=[{"role": "user", "content": f"""Based on the input provided by the doctor The input: {prompt}, suggest a list of potential diagnoses for a radiology report and provide specific phrases that can be used to fill out the report based on the selected diagnosis.

The input will be details of a scan (e.g., ultrasound, CT scan, MRI) or a condition observed in the scan. Based on this input, generate a numbered list of possible diagnoses and provide three corresponding medical phrases for each diagnosis. These phrases should describe the condition in detail and use placeholders for customizable information (such as specific vertebra levels, severity, or associated conditions).

Ensure the output is formatted as follows in a numbered list format:
Diagnosis Name
1. "Medical phrase 1 with placeholders for specific details."
2. "Medical phrase 2 with placeholders for specific details."
3. "Medical phrase 3 with placeholders for specific details."
Some Examples of possible diagnoses include Herniated Disc, Spinal Stenosis, Spondylolisthesis, Osteophyte Formation, Fracture, Degenerative Disc Disease, Compression Fracture, Facet Joint Arthropathy, Vertebral Body Collapse, and Spinal Cord Compression.
Provide the output in a way that allows for easy selection and customization of phrases based on the diagnosis selected by the doctor."""}]
        )
        diagnostics = response.choices[0].message.content
        print(diagnostics)  # Debugging print to verify API output

        # Adjusted regex to match the diagnosis name and its corresponding phrases
        diagnostics_dict = {}
        # Updated regex pattern to capture "Diagnosis Name:" followed by phrases
        matches = re.findall(r'Diagnosis Name:\s*(.*?)\n(1\.\s*".*?"\n2\.\s*".*?"\n3\.\s*".*?")', diagnostics, re.DOTALL)

        # Process each match to build the structured dictionary
        for match in matches:
            diagnosis_name = match[0].strip()  # Extract diagnosis name
            phrases = match[1].strip().split("\n")  # Extract phrases and split them by newline
            # Clean and format the phrases
            phrases = [phrase.strip() for phrase in phrases]
            diagnostics_dict[diagnosis_name] = phrases
        
        return diagnostics_dict

    except Exception as e:
        st.error(f"Error generating diagnostics: {e}")
        return {}

# Initialize session state for selected diagnosis and diagnostics list if not already set
if 'selected_diagnosis' not in st.session_state:
    st.session_state.selected_diagnosis = None
if 'diagnostics_list' not in st.session_state:
    st.session_state.diagnostics_list = {}

# Section 2: Speech Prompt for Diagnostic Phrases
st.header("2. Generate Diagnostic Phrases from Speech Prompt")

# Input field for user prompt
prompt = st.text_input("Enter a speech prompt for diagnosis:")

# Generate button for diagnostics
if st.button("Generate Diagnostics"):
    if prompt:
        diagnostics = generate_diagnostics(prompt)
        if diagnostics:
            # Store the generated diagnostics in session state
            st.session_state.diagnostics_list = diagnostics
            st.session_state.selected_diagnosis = None  # Reset selection when new diagnostics are generated
        else:
            st.write("No diagnostics were generated. Please try a different prompt.")
            st.session_state.diagnostics_list = {}  # Clear diagnostics list if no diagnostics generated
    else:
        st.write("Please enter a prompt.")
        st.session_state.diagnostics_list = {}  # Clear diagnostics list if no prompt is entered

# Display the diagnostics if available
if st.session_state.diagnostics_list:
    # Display the diagnostics in a select box and store the selection in session state
    selected_diagnosis = st.selectbox(
        "Select a Diagnosis",
        list(st.session_state.diagnostics_list.keys()),
        index=list(st.session_state.diagnostics_list.keys()).index(st.session_state.selected_diagnosis) if st.session_state.selected_diagnosis in st.session_state.diagnostics_list else 0
    )

    # Update session state with the selected diagnosis
    st.session_state.selected_diagnosis = selected_diagnosis

    # Enhanced display of selected diagnosis with additional formatting
    st.markdown("### Selected Diagnosis Details")
    st.write(f"**Diagnosis:** {selected_diagnosis}")

    # Display corresponding phrases for the selected diagnosis
    phrases = st.session_state.diagnostics_list[selected_diagnosis]
    st.write("Possible phrases for the report:")
    for phrase in phrases:
        st.write(f"- {phrase}")

    # Display additional information or formatted output
    with st.expander("More Information"):
        st.write(f"You have selected: **{selected_diagnosis}**. Here are additional details that could be included.")