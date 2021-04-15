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

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'my_logger.log', maxBytes=50000000, backupCount=5
)
handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
)
logger.addHandler(handler)


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = (
            'Ревьюеру всё понравилось, '
            'можно приступать к следующему уроку.'
        )
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    adress = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(adress, headers=headers, params=params)
    return homework_statuses.json()


def send_message(message, bot_client):
    msg = bot_client.send_message(CHAT_ID, message)
    logger.info('Сообщение отправлено')
    return msg


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    logger.debug('Запуск бота')
    current_timestamp = int(time.time())
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
            print(msg)
            logger.exception(msg)
            send_message(msg, bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
