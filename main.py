from audio_transcriber import AudioRecorder, AWSTranscriber, Translator, PollySynthesizer
from language_translator import LanguageProcessor

def main():
    print("1: Transcribe French and Translate to English")
    print("2: Transcribe English and Translate to another language")
    choice = input("Choose an option: ")

    if choice == "1":
        recorder = AudioRecorder()
        transcriber = AWSTranscriber()
        translator = Translator()
        synthesizer = PollySynthesizer()

        recorder.record_audio()
        json_file_name = transcriber.transcribe_audio(recorder.audio_file_name)
        if json_file_name:
            local_file_name = transcriber.download_transcription(json_file_name)
            with open(local_file_name, 'r') as json_file:
                json_data = json.load(json_file)
                transcript = json_data.get("results", {}).get("transcripts", [{}])[0].get("transcript", "")
                print("Transcript:", transcript)
                translated_text = translator.translate_text(transcript)
                synthesizer.text_to_speech(translated_text)
                synthesizer.play_audio()

    elif choice == "2":
        target_language = input("Enter the target language (French/German/Spanish): ")
        processor = LanguageProcessor(target_language=target_language)
        processor.process_language()
    else:
        print("Invalid choice. Please choose 1 or 2.")

if __name__ == "__main__":
    main()
