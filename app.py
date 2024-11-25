import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from pydub import AudioSegment
import speech_recognition as sr
from googletrans import Translator

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
TRANSLATED_FOLDER = 'translated_files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TRANSLATED_FOLDER'] = TRANSLATED_FOLDER

# Ensure folders exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(TRANSLATED_FOLDER):
    os.makedirs(TRANSLATED_FOLDER)

def prepare_voice_file(path: str) -> str:
    audio_file = AudioSegment.from_file(path)
    wav_file = os.path.splitext(path)[0] + '_converted.wav'
    audio_file = audio_file.set_frame_rate(16000).set_channels(1)  
    audio_file.export(wav_file, format='wav')
    return wav_file

def transcribe_audio(audio_file_path, language) -> str:
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file_path) as source:
        audio_data = recognizer.record(source)
    text = recognizer.recognize_google(audio_data, language=language)
    return text

def translate_to_english(text: str, source_lang: str) -> str:
    translator = Translator()
    translation = translator.translate(text, src=source_lang, dest='en')
    return translation.text

def save_translation_to_file(translated_text: str, filename: str) -> str:
    file_path = os.path.join(app.config['TRANSLATED_FOLDER'], filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(translated_text)
    return file_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    file = request.files['audio']
    language = request.form.get('language')
    if file.filename == '' or language == '':
        return jsonify({'error': 'File or language not provided'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    try:
        wav_file = prepare_voice_file(filepath)
        transcription = transcribe_audio(wav_file, language)
        translation = translate_to_english(transcription, language[:2])
        translated_file_path = save_translation_to_file(translation, file.filename.split('.')[0] + '_translated.txt')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'transcription': transcription,
        'translation': translation,
        'download_link': f"/download/{os.path.basename(translated_file_path)}"
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['TRANSLATED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)