import requests
from flask import Flask, request, jsonify
import logging
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

cities = {
    'москва': {
        'images': ['937455/616fb274379909eb9890', '997614/f21869857cc7b0f780d3'],
        'country': 'Россия'
    },
    'нью-йорк': {
        'images': ['937455/9da405d1a9178c1e70d6', '937455/bc7f29d53f1729bb64b3'],
        'country': 'США'
    },
    'париж': {
        'images': ["1521359/e0fe22f5848814946066", '1540737/3941c6ae7a70d4fe1698'],
        'country': 'Франция'
    }
}

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
            'first_name': None,
            'game_started': False,
            'guessing_country': False,
            'attempt': 1,
            'guessed_cities': []
        }
        res['response']['text'] = 'Привет! Как тебя зовут?'
        return

    first_name = sessionStorage[user_id]['first_name']

    if first_name is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Извини, я не расслышала твое имя. Можешь повторить?'
        else:
            sessionStorage[user_id]['first_name'] = first_name
            res['response'][
                'text'] = f'{first_name.title()}, приятно познакомиться! Я Алиса. Хочешь сыграть в игру "Угадай город по фото"?'
            res['response']['buttons'] = [
                {'title': 'Да', 'hide': True},
                {'title': 'Нет', 'hide': True}
            ]
        return

    if not sessionStorage[user_id]['game_started']:
        if 'да' in req['request']['nlu']['tokens']:
            if len(sessionStorage[user_id]['guessed_cities']) == len(cities):
                res['response']['text'] = f'{first_name.title()}, ты отгадал все города!'
                res['response']['end_session'] = True
            else:
                sessionStorage[user_id]['game_started'] = True
                sessionStorage[user_id]['attempt'] = 1
                play_game(res, req, first_name)
        elif 'нет' in req['request']['nlu']['tokens']:
            res['response'][
                'text'] = f'{first_name.title()}, как хочешь! '
            res['response']['end_session'] = True
        else:
            res['response']['text'] = f'{first_name.title()}, я не поняла твой ответ.'
            res['response']['buttons'] = [
                {'title': 'Да', 'hide': True},
                {'title': 'Нет', 'hide': True}
            ]
    else:
        play_game(res, req, first_name)


def play_game(res, req, first_name):
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']

    if sessionStorage[user_id]['guessing_country']:
        user_country = get_country_response(req)
        correct_country = cities[sessionStorage[user_id]['city']]['country']

        if user_country and user_country.lower() == correct_country.lower():
            city = sessionStorage[user_id]['city']
            res['response'][
                'text'] = f'{first_name.title()}, правильно! {city.title()} находится в {correct_country}. Вот ссылка на карту: https://yandex.ru/maps/?mode=search&text={city}\nПродолжаем?'
            sessionStorage[user_id]['guessed_cities'].append(city)
            sessionStorage[user_id]['game_started'] = False
            sessionStorage[user_id]['guessing_country'] = False

            if len(sessionStorage[user_id]['guessed_cities']) < len(cities):
                res['response']['buttons'] = [
                    {'title': 'Да', 'hide': True},
                    {'title': 'Нет', 'hide': True}
                ]
            else:
                res['response']['text'] = f'{first_name.title()}, ты отгадал все города! Отличный результат!'
                res['response']['end_session'] = True
        else:
            res['response'][
                'text'] = f'{first_name.title()}, не совсем. Попробуй еще раз. В какой стране находится {sessionStorage[user_id]["city"].title()}?'
        return

    if attempt == 1:
        available_cities = [city for city in cities if city not in sessionStorage[user_id]['guessed_cities']]
        city = random.choice(available_cities)
        sessionStorage[user_id]['city'] = city

        res['response']['card'] = {
            'type': 'BigImage',
            'title': f'{first_name.title()}, что это за город?',
            'image_id': cities[city]['images'][attempt - 1]
        }
        res['response']['text'] = f'{first_name.title()}, давай сыграем! Угадай город по фото!'
    else:
        city = sessionStorage[user_id]['city']
        guessed_city = get_city(req)

        if guessed_city and guessed_city.lower() == city.lower():
            sessionStorage[user_id]['guessing_country'] = True
            res['response'][
                'text'] = f'{first_name.title()}, правильно! Теперь скажи, в какой стране находится {city.title()}?'
        else:
            if attempt == 3:
                res['response']['text'] = f'{first_name.title()}, это был {city.title()}. Хочешь сыграть ещё?'
                sessionStorage[user_id]['guessed_cities'].append(city)
                sessionStorage[user_id]['game_started'] = False

                if len(sessionStorage[user_id]['guessed_cities']) < len(cities):
                    res['response']['buttons'] = [
                        {'title': 'Да', 'hide': True},
                        {'title': 'Нет', 'hide': True}
                    ]
                else:
                    res['response']['text'] = f'{first_name.title()}, ты отгадал все города! Отличная работа!'
                    res['response']['end_session'] = True
            else:
                res['response']['card'] = {
                    'type': 'BigImage',
                    'title': f'{first_name.title()}, вот дополнительное фото',
                    'image_id': cities[city]['images'][attempt - 1]
                }
                res['response']['text'] = f'{first_name.title()}, попробуй еще раз угадать город!'

    sessionStorage[user_id]['attempt'] += 1


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)
    return None


def get_country_response(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('country', None)

    tokens = req['request']['nlu']['tokens']
    if tokens:
        return ' '.join(tokens)
    return None


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)
    return None


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)