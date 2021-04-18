import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

handler = RotatingFileHandler(
    'my_logger.log', maxBytes=50000000, backupCount=5
)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    handlers=[handler]
)


def parse_homework_status(homework):
    verdict = {
        'rejected': 'К сожалению в работе нашлись ошибки.',
        'approved': 'Ревьюеру всё понравилось, можно приступать '
        'к следующему уроку.',
        'reviewing': 'Работа взята в ревью.'
    }
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status is None or homework_name is None:
        error_msg = 'Неверный ответ сервера'
        logging.error(error_msg)
        return error_msg
    else:
        verdict_msg = verdict[homework_status]
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict_msg}'


def get_homework_statuses(current_timestamp):
    current_timestamp = current_timestamp or int(time.time())
    address = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            address, headers=headers, params=params
        )
        return homework_statuses.json()
    except Exception as error:
        logging.exception(error)
        return {}


def send_message(message, bot_client):
    msg = bot_client.send_message(CHAT_ID, message)
    logging.info('Сообщение отправлено')
    return msg


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    logging.debug('Запуск бота')
    current_timestamp = 0
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(
                        new_homework.get('homeworks')[0]
                    ), bot
                )
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            time.sleep(1200)
        except Exception as e:
            msg = f'Бот столкнулся с ошибкой: {e}'
            logging.exception(msg)
            send_message(msg, bot)
            time.sleep(600)


if __name__ == '__main__':
    main()
