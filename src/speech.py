from dotenv import load_dotenv
from re import sub
from os import getenv
from time import sleep
import logging
import azure.cognitiveservices.speech as speechsdk

# === Return audio input (file / microphone) to text ===
def Speech2Txt(filename: str = "", use_default_microphone: bool = False):
	load_dotenv()
	SPEECH_REGION = getenv("AZURE_SPEECH_REGION")
	SPEECH_KEY = getenv("AZURE_SPEECH_KEY")
	speech_config = speechsdk.SpeechConfig(subscription = SPEECH_KEY, region = SPEECH_REGION)
	speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "15000")
	auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["vi-VN", "en-US"])

	# Differentiate input from microphone or file
	if use_default_microphone:
		logging.info("Using the default microphone.")
		logging.info("Speak into your microphone.")
		audio_config = speechsdk.audio.AudioConfig(use_default_microphone = use_default_microphone)
	else:
		if not filename:
			raise ValueError("No audio file provided.")
		logging.info(f"Using the audio file: {filename}")
		audio_config = speechsdk.audio.AudioConfig(filename = filename)

	speechRegconizer = speechsdk.SpeechRecognizer(speech_config = speech_config, audio_config = audio_config, auto_detect_source_language_config = auto_detect_source_language_config)
	result = speechRegconizer.recognize_once_async().get()
	if result.reason == speechsdk.ResultReason.RecognizedSpeech: # type: ignore
		result = result.text # type: ignore
	elif result.reason == speechsdk.ResultReason.NoMatch: # type: ignore
		result = "Speech could not be recognized."
	elif result.reason == speechsdk.ResultReason.Canceled: # type: ignore
		cancellation_details = result.cancellation_details # type: ignore
		result = f"Canceled: {cancellation_details.reason}. Error details: {cancellation_details.error_details}"
	else:
		result = ""

	return sub(r'(?<=\d)\s+(?=\d)', '', result.casefold())


if __name__ == '__main__':
	for i in range(5, 0, -1):
		print(f"\rMic sẽ bật sau: {i}", end = '', flush = True)
		sleep(1)
	print("\r", end = '', flush = True)
	print("Mic đã được bật! ")
	print(Speech2Txt("", True))