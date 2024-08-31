import os
import pyaudio
import wave
import boto3
import json
from datetime import datetime
import pygame
from AccessKeys import aws_access_key_id, aws_secret_access_key

class AudioRecorder:
    def __init__(self, audio_file_name='recorded_audio.wav', channels=1, sample_rate=16000, record_duration=6):
        self.audio_file_name = audio_file_name
        self.audio_format = pyaudio.paInt16
        self.channels = channels
        self.sample_rate = sample_rate
        self.record_duration = record_duration

    def record_audio(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=self.audio_format, channels=self.channels,
                            rate=self.sample_rate, input=True,
                            frames_per_buffer=1024)
        print("Recording audio...")
        frames = [stream.read(1024) for _ in range(0, int(self.sample_rate / 1024 * self.record_duration))]
        print("Recording finished.")
        stream.stop_stream()
        stream.close()
        audio.terminate()
        with wave.open(self.audio_file_name, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(self.audio_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
        print(f"Audio saved as {self.audio_file_name}")

class AWSTranscriber:
    def __init__(self, region_name='ap-south-1', bucket_name='jenaudiobucket', language_code='fr-FR'):
        self.transcribe = boto3.client('transcribe', region_name=region_name)
        self.s3 = boto3.client('s3', region_name=region_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        self.bucket_name = bucket_name
        self.language_code = language_code

    def transcribe_audio(self, audio_file_name):
        job_name = f'transcription_job_{datetime.now().strftime("%Y%m%d%H%M%S")}'
        json_file_name = f'transcribed_text.json'
        self.s3.upload_file(audio_file_name, self.bucket_name, audio_file_name)
        self.transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            LanguageCode=self.language_code,
            MediaFormat='wav',
            Media={'MediaFileUri': f's3://{self.bucket_name}/{audio_file_name}'},
            OutputBucketName=self.bucket_name,
            OutputKey=f'transcribed_text/{json_file_name}'
        )
        print(f"Transcription job '{job_name}' started.")
        while True:
            response = self.transcribe.get_transcription_job(TranscriptionJobName=job_name)
            if response['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break
        if response['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            self.s3.put_object(Bucket=self.bucket_name, Key=json_file_name, Body=json_file_name)
            print(f"JSON file '{json_file_name}' uploaded to S3 bucket '{self.bucket_name}'")
            return json_file_name
        else:
            print("Transcription job failed.")
            return None

    def download_transcription(self, json_file_name, local_file_name='sample.json'):
        json_file_path = f'transcribed_text/{json_file_name}'
        self.s3.download_file(self.bucket_name, json_file_path, local_file_name)
        print(f"Downloaded transcription as {local_file_name}")
        return local_file_name

class Translator:
    def __init__(self, region_name='ap-south-1', source_language_code='fr', target_language_code='en'):
        self.translate = boto3.client('translate', region_name=region_name)
        self.source_language_code = source_language_code
        self.target_language_code = target_language_code

    def translate_text(self, text):
        response = self.translate.translate_text(
            Text=text,
            SourceLanguageCode=self.source_language_code,
            TargetLanguageCode=self.target_language_code
        )
        translated_text = response['TranslatedText']
        print("Translated Text:", translated_text)
        return translated_text

class PollySynthesizer:
    def __init__(self, region_name='ap-south-1', voice_id='Joanna', language_code='en-US'):
        self.polly = boto3.client('polly', region_name=region_name)
        self.voice_id = voice_id
        self.language_code = language_code

    def text_to_speech(self, text, output_file_path='output1.mp3'):
        response = self.polly.synthesize_speech(
            Text=text,
            VoiceId=self.voice_id,
            LanguageCode=self.language_code,
            OutputFormat='mp3'
        )
        with open(output_file_path, 'wb') as file:
            file.write(response['AudioStream'].read())
        print(f"Audio saved as {output_file_path}")

    def play_audio(self, audio_file_path='output1.mp3'):
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

if __name__ == "__main__":
    recorder = AudioRecorder()
    recorder.record_audio()

    transcriber = AWSTranscriber()
    json_file_name = transcriber.transcribe_audio(recorder.audio_file_name)

    if json_file_name:
        local_file_name = transcriber.download_transcription(json_file_name)
        with open(local_file_name, 'r') as json_file:
            json_data = json.load(json_file)
            transcript = json_data.get("results", {}).get("transcripts", [{}])[0].get("transcript", "")
            print("Transcript:", transcript)

            translator = Translator()
            translated_text = translator.translate_text(transcript)

            synthesizer = PollySynthesizer()
            synthesizer.text_to_speech(translated_text)
            synthesizer.play_audio()
