import requests
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    logging.info('Response: %r', response)
    return jsonify(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']

    if req['session']['new']:
        sessionStorage[user_id] = {
            'waiting_for_translation': False
        }
        res['response'][
            'text'] = 'Привет! Я могу переводить слова с русского на английский. Скажите "Переведи слово <слово>".'
        return

    command = req['request']['original_utterance'].lower()

    if 'переведи слово' in command or 'переведите слово' in command:
        word = command.split('слово')[-1].strip()
        if word:
            translation = translate_word(word)
            if translation:
                res['response']['text'] = f'Перевод: {translation}'
            else:
                res['response']['text'] = 'Не удалось перевести это слово. Попробуйте другое.'
        else:
            res['response']['text'] = 'Вы не указали слово для перевода. Попробуйте снова.'
    else:
        res['response']['text'] = 'Я могу переводить слова. Скажите "Переведи слово <слово>".'


def translate_word(word, source_lang='ru', target_lang='en'):
    try:
        url = f"https://api.mymemory.translated.net/get?q={word}&langpair={source_lang}|{target_lang}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('responseData'):
                return data['responseData']['translatedText'].lower()
        return None
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return None


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)