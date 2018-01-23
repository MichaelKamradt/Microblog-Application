import json
from google.cloud import translate

def translate_text(target, text):
    # Translate text into the target language. Target language must be an ISO 639-1 language code

    # Instantiate client
    translate_client = translate.Client()

    # translate
    translation = translate_client.translate(text, target_language=target)
    return translation['translatedText']