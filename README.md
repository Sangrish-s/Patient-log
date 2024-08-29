Here's the updated text for your README file with the **Getting Started** section:

---

# Patient-log

## Getting Started

To get started with the Patient-log project, follow these steps:

### 1. Clone the Repository

First, clone the repository to your local machine using the following command:

```bash
git clone https://github.com/Sangrish-s/Patient-log.git
```

After cloning, navigate to the project directory:

```bash
cd Patient-log
```

### 2. Set Up the Environment

Ensure you have Python installed on your system. Then, install the required Python libraries by running:

```bash
pip install -r requirements.txt
```

This command installs all the necessary packages for the project, including Streamlit, SpeechRecognition, Mistral, and Python-dotenv.

### 3. Configure Environment Variables

Create a `.env` file in the root of the project directory and add your Mistral API key

*not needed*

### 4. Run the Streamlit App

To start the Streamlit application, run the following command:

```bash
streamlit run patient-log.py
```

Replace `app.py` with the name of your Streamlit Python file if it is named differently.

### 5. Using the App

- **Capture and Transcribe Patient-Doctor Dialogue**: Click on "Start Recording" to capture audio and transcribe it.
- **Generate Diagnostic Phrases from Speech Prompt**: Enter a textual prompt in the provided input box and click "Generate Diagnostics" to get potential diagnostic phrases.

## Feature List

1. **Speech Recognition and Summary**: The app captures audio from the user, recognizes speech, and summarizes the conversation using the Mistral API.
    **Future work**: Add speaker diarization
   
2. **Diagnosis Based on Textual Prompt**: The app accepts a textual input prompt and generates a list of potential diagnoses using the Mistral API.
    **Future work**: Gain more clarity on requirment and make changes



### Tech-Stack information
1. Streamlit backend and display
2. Mistralai as api for generative ai
3. **Future work:**Pyannotate for diarization
4. Pygame and google for speech recognition 