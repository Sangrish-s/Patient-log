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

# Section 2: Speech Prompt for Diagnostic Phrases
st.header("2. Generate Diagnostic Phrases from Speech Prompt")

# Input field for user prompt
prompt = st.text_input("Enter a speech prompt for diagnosis:")

# Generate button for diagnostics
if st.button("Generate Diagnostics"):
    if prompt:
        diagnostics = generate_diagnostics(prompt)
        if diagnostics:
            # Display the diagnostics in a select box
            selected_diagnosis = st.selectbox("Select a Diagnosis", diagnostics)
            
            # Enhanced display of selected diagnosis with additional formatting
            st.markdown("### Selected Diagnosis Details")
            st.write(f"**Diagnosis:** {selected_diagnosis}")

            # Display additional information or formatted output
            with st.expander("More Information"):
                st.write(f"You have selected: **{selected_diagnosis}**. Here are additional details that could be included.")
        else:
            st.write("No diagnostics were generated. Please try a different prompt.")
    else:
        st.write("Please enter a prompt.")
