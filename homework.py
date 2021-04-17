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
    homework_name = homework.get('homework_name')
    if homework_name is not None:
        status = homework.get('status')
        if status == 'rejected':
            verdict = 'К сожалению в работе нашлись ошибки.'
        elif status == 'reviewing':
            verdict = 'Работа взята в ревью.'
        elif status == 'approved':
            verdict = (
                'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.'
            )
        else:
            verdict = 'Статус не определен'
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    return 'Неверный ответ сервера'


def get_homework_statuses(current_timestamp):
    address = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(address, headers=headers, params=params)
    if isinstance(homework_statuses, requests.models.Response):
        homework_statuses.raise_for_status()
    return homework_statuses.json()


def send_message(message, bot_client):
    msg = bot_client.send_message(CHAT_ID, message)
    logging.info('Сообщение отправлено')
    return msg


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    logging.debug('Запуск бота')
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
            if current_timestamp is None:
                current_timestamp = int(time.time())
            time.sleep(1200)
            continue
        except requests.exceptions.ConnectionError as con_error:
            logging.exception(con_error)
            msg = 'Соединение не установлено'
        except requests.exceptions.HTTPError as http_error:
            logging.exception(http_error)
            msg = f'Ошибка запроса. Код: {http_error.response.status_code}'
        except requests.exceptions.Timeout as time_error:
            logging.exception(time_error)
            msg = 'Время ожидания ответа от сервера истекло'
        except requests.exceptions.RequestException as rest_error:
            logging.exception(rest_error)
            msg = 'Ошибка запроса'
        except Exception as e:
            msg = f'Бот столкнулся с ошибкой: {e}'
            logging.exception(msg)
        finally:
            if msg != 'Соединение не установлено':
                send_message(msg, bot)
            time.sleep(600)


if __name__ == '__main__':
    main()
