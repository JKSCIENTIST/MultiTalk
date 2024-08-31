import os
import json
import pygame
from AccessKeys import aws_access_key_id, aws_secret_access_key
from audio_transcriber import AudioRecorder, AWSTranscriber, Translator, PollySynthesizer

class LanguageProcessor:
    def __init__(self, audio_file_name='recorded_audio.wav', target_language='french'):
        self.recorder = AudioRecorder(audio_file_name=audio_file_name)
        self.transcriber = AWSTranscriber(language_code='en-US')
        self.target_language = target_language.lower()
        self.translator = Translator(source_language_code='en')
        self.synthesizer = PollySynthesizer()

    def get_language_config(self):
        if self.target_language == 'french':
            return 'fr', 'Mathieu', 'fr-FR'
        elif self.target_language == 'spanish':
            return 'es', 'Conchita', 'es-ES'
        elif self.target_language == 'german':
            return 'de', 'Marlene', 'de-DE'
        else:
            raise ValueError("Invalid language selected")

    def process_language(self):
        self.recorder.record_audio()
        json_file_name = self.transcriber.transcribe_audio(self.recorder.audio_file_name)
        if json_file_name:
            local_file_name = self.transcriber.download_transcription(json_file_name)
            with open(local_file_name, 'r') as json_file:
                json_data = json.load(json_file)
                transcript = json_data.get("results", {}).get("transcripts", [{}])[0].get("transcript", "")
                print("Transcript:", transcript)

                target_lang_code, voice_id, language_code = self.get_language_config()
                self.translator.target_language_code = target_lang_code
                translated_text = self.translator.translate_text(transcript)

                self.synthesizer.voice_id = voice_id
                self.synthesizer.language_code = language_code
                self.synthesizer.text_to_speech(translated_text)
                self.synthesizer.play_audio()

if __name__ == "__main__":
    target_language = input("Enter the target language (French/German/Spanish): ")
    processor = LanguageProcessor(target_language=target_language)
    processor.process_language()
