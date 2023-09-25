import os
import pyaudio
import wave
import boto3
import json
from datetime import datetime
import pygame
from AccessKeys import aws_access_key_id, aws_secret_access_key

# AWS configuration
region_name = 'ap-south-1'
transcribe = boto3.client('transcribe', region_name=region_name)
translate = boto3.client('translate', region_name=region_name)
polly = boto3.client('polly', region_name=region_name)

# Audio recording configuration
audio_file_name = 'recorded_audio.wav'
audio_format = pyaudio.paInt16
channels = 1
sample_rate = 16000
record_duration = 6  # Recording duration in seconds

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Create an audio stream for recording
stream = audio.open(format=audio_format, channels=channels,
                    rate=sample_rate, input=True,
                    frames_per_buffer=1024)

print("Recording audio...")

frames = []

# Record audio for the specified duration
for _ in range(0, int(sample_rate / 1024 * record_duration)):
    data = stream.read(1024)
    frames.append(data)

print("Recording finished.")

# Stop and close the audio stream
stream.stop_stream()
stream.close()

# Terminate the PyAudio instance
audio.terminate()

# Save the recorded audio to a WAV file
with wave.open(audio_file_name, 'wb') as wf:
    wf.setnchannels(channels)
    wf.setsampwidth(audio.get_sample_size(audio_format))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))

print(f"Audio saved as {audio_file_name}")

# Perform transcription using AWS Transcribe
job_name = f'transcription_job_{datetime.now().strftime("%Y%m%d%H%M%S")}'
language_code = 'en-US'  
bucket_name = 'jenaudiobucket' 

# Upload the recorded audio to S3
s3 = boto3.client('s3', region_name=region_name)
s3.upload_file(audio_file_name, bucket_name, audio_file_name)
json_file_name = f'transcribed_text.json'  # Name for the resulting JSON file 

# Start the transcription job
transcribe.start_transcription_job(
    TranscriptionJobName=job_name,
    LanguageCode=language_code,
    MediaFormat='wav',
    Media={
        'MediaFileUri': f's3://{bucket_name}/{audio_file_name}'
    },
    OutputBucketName=bucket_name,  # Specify the output S3 bucket
    OutputKey=f'transcribed_text/{json_file_name}'  # Specify the name for the JSON output file
)

print(f"Transcription job '{job_name}' started.")

# Wait for the transcription job to complete
while True:
    response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    if response['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
        break

# # Save the file to your D drive
if response['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
    
    # Initialize the S3 client
    s3 = boto3.client('s3', region_name=region_name, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

    # Upload JSON data to S3 bucket
    s3.put_object(Bucket=bucket_name, Key=json_file_name, Body=json_file_name)

    print(f"JSON file '{json_file_name}' uploaded to S3 bucket '{bucket_name}'")
else:
    print("Transcription job failed.")

#Clean up: Delete the audio file from S3 and locally
s3.delete_object(Bucket=bucket_name, Key=audio_file_name)
os.remove(audio_file_name)

# Specify the path to your JSON file
json_file_path = 'transcribed_text/' + json_file_name
current_directory = os.getcwd()
file_name = 'sample.json'
local_file_path = os.path.join(current_directory, file_name)

s3.download_file(bucket_name, json_file_path, local_file_path)

# Specify the path to your JSON file
json_file_path = 'sample.json'  

# Read and parse the JSON file
try:
    with open(json_file_path, 'r') as json_file:
        json_data = json.load(json_file)

    # Extract the transcribed text from the JSON data
    transcript = json_data.get("results", {}).get("transcripts", [{}])[0].get("transcript", "")

    # Print the extracted transcript
    print("Transcript:", transcript)

except FileNotFoundError:
    print("The specified JSON file does not exist.")
except Exception as e:
    print(f"An error occurred: {str(e)}")

# Obtain the language
while True:
    language = input("French/German/Spanish: ")
    target = language.lower()
    if target == "french":
        Targetlangcode = 'fr'
        voice_id = "Mathieu"
        language_code = 'fr-FR'
        break
    elif target == "spanish":
        Targetlangcode = 'es'
        voice_id = "Conchita"
        language_code = 'es-ES'
        break
    elif target == "german":
        Targetlangcode = 'de'
        voice_id = "Marlene"
        language_code = 'de-DE'
        break
    else:
        print("Invalid input. Please try again")

# Translating the text
response = translate.translate_text(
    Text=transcript,
    SourceLanguageCode='en',  # English
    TargetLanguageCode=Targetlangcode 
)

# Obtain the response
translated_text = response['TranslatedText']
print("Translated Text:", translated_text)

# Text to Audio (Poly)
response = polly.synthesize_speech(
    Text=translated_text,
    VoiceId=voice_id,
    LanguageCode=language_code,
    OutputFormat='mp3' 
)
output_file_path = 'output1.mp3'

# Save the incoming audio from Polly
with open(output_file_path, 'wb') as file:
    file.write(response['AudioStream'].read())

# PLay the audio file
pygame.init()
audio_file_path = 'output1.mp3'

# Create a Pygame mixer object
pygame.mixer.init()

# Load and play the audio
pygame.mixer.music.load(audio_file_path)
pygame.mixer.music.play()

# Keep the script running while the audio plays
while pygame.mixer.music.get_busy():
    pygame.time.Clock().tick(10)  # Adjust the tick rate as needed