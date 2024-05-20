import logging
import re

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from dotenv import load_dotenv
from pathlib import Path
import paramiko
import os
from telegram.ext import CallbackContext
import psycopg2
from psycopg2 import Error

base_dir = Path(__file__).resolve().parent.parent
dotenv_path = base_dir / '.env'

load_dotenv(dotenv_path=dotenv_path)

TOKEN = os.getenv('TOKEN')

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt',\
    filemode='a',\
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',\
    level=logging.INFO, encoding='utf-8'
)
#logging.disable(logging.CRITICAL)
logger = logging.getLogger(__name__)

def execute_sql_command(sql_command, params = None, command=None):
    # подключаемся к бд
    connection = None
    try:
        connection = psycopg2.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),  
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_DATABASE')
        )
        cursor = connection.cursor()
        # передаем запрос
        cursor.execute(sql_command, params)
        if sql_command.lower().startswith('select'):
            if command == 'get_repl_logs':
                records = cursor.fetchone()
                records = records[0].splitlines()

                records = [str(row) for row in records if "replica" in row.lower()]
                return '\n'.join([str(row) for row in records])
            else:
                records = cursor.fetchall()
                return '\n'.join([f"{i + 1}. {row[1]}" for i, row in enumerate(records)])
        connection.commit()
        return "Команда успешно выполнена"
    # обработка исключений
    except (Exception, psycopg2.Error) as error:
        return f"Ошибка при работе с PostgreSQL: {error}"
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def ssh_command(update: Update, context: CallbackContext):
    logger.info('FUNCTION ----ssh_connect----')
    command_map = {
        'get_release': 'cat /etc/os-release',
        'get_uname': 'uname -a',
        'get_uptime': 'uptime',
        'get_df': 'df -h',
        'get_free':'free -h',
        'get_mpstat': 'mpstat',
        'get_w': 'w',
        'get_auths': 'last -n 10',
        'get_critical': 'journalctl -p crit -n 5',
        'get_ps': 'ps aux | head -20',
        'get_ss': 'ss -tulwn',
        'get_apt_list': '',
        'get_services': 'systemctl list-units --type=service --state=running',
        'get_repl_logs':  'SELECT pg_read_file(pg_current_logfile());',
        'get_emails': "SELECT * FROM emails;",
        'get_phone_numbers': "SELECT * FROM phone_numbers;"
    }

    # Получение команды
    command_key = update.message.text.strip().lower().replace('/', '')
    logger.info(f'command_key = {command_key}')
    if command_key == 'get_apt_list' and 'command' not in context.user_data:
        update.message.reply_text("Введите название пакета или отправьте 'all' для вывода всех пакетов.")
        return 'get_apt_list'

    if command_key in ['get_emails', 'get_phone_numbers', 'get_repl_logs']:
        sql_command = command_map.get(command_key)
        if sql_command:
            result = execute_sql_command(sql_command, command=command_key)
            update.message.reply_text(f"Результаты:\n{result}")
        else:
            update.message.reply_text("SQL команда не найдена.")
        return ConversationHandler.END
    
    system_command = context.user_data.get('command', command_map.get(command_key))
    logger.info(f'system_command = {system_command}')

    if system_command is None:
        update.message.reply_text("Такой команды нет.")
        return ConversationHandler.END


    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PAS')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(system_command)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    logger.info(f'data - {data if data else "Нет данных."}')
    update.message.reply_text(data if data else "Нет данных.")

def apt_list_input(update: Update, context: CallbackContext):
    user_input = update.message.text.strip().lower()
    if user_input == 'all':
        context.user_data['command'] = 'dpkg -l | tail -20'
    else:
        context.user_data['command'] = f"dpkg -s {user_input}"
    
    return ssh_command(update, context)

def start(update: Update, context):
    user = update.effective_user
    logger.info(f'user = {user.full_name}')
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def find_phone_number_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    
    logger.info('FUNCTION ----find_phone_number_command----')
    logger.info('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'


def find_phone_number (update: Update, context):
    logger.info('FUNCTION ----find_phone_number----')
    
    user_input = update.message.text # Получаем текст
    logger.info(f'user_input - {user_input}')

    phoneNumRegex = re.compile(r'\+?[7-8][\s\-]?[\(]?\d{3}[\)]?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}')

    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера 
    logger.info(f'phoneNumberList - {phoneNumberList}')
    
    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        logger.info('Телефонные номера не найдены')
        return ConversationHandler.END

    response = "Найденные номера:\n" + "\n".join(phoneNumberList) + "\nСохранить их в базу данных?\n Отправьте 'да' для сохранения."
    context.user_data['phoneNumberList'] = phoneNumberList
    update.message.reply_text(response)
    return 'confirm_save_phone_number'

def confirm_save_phone_number(update: Update, context):
    logger.info('FUNCTION ----confirm_save_phone_number----')
    if update.message.text.lower() == 'да':
        phone_numbers = context.user_data['phoneNumberList']
        for number in phone_numbers:
            print (number)
            execute_sql_command("INSERT INTO phone_numbers (phone_number) VALUES (%s);", [number])
            logger.info("INSERT INTO phone_numbers (phone_number) VALUES (%s);", [number])
        update.message.reply_text('Номера сохранены.')
    else:
        update.message.reply_text('Сохранение отменено.')
    return ConversationHandler.END

def find_email_command(update: Update, context):
    update.message.reply_text('Введите текст для поиска email: ')
    
    logger.info('FUNCTION ----find_email_command----')
    logger.info('Введите текст для поиска email: ')
    
    return 'find_email'

def find_email(update: Update, context):
    logger.info('FUNCTION ----find_email----')

    user_input = update.message.text # Получаем текст
    logger.info(f'user_input - {user_input}')

    email_re = re.compile(r'[\w.-]+@[\w.-]+\.[a-z]{2,}')

    email_list = email_re.findall(user_input)
    logger.info(f'email_list - {email_list}')

    if not email_list: # Обрабатываем случай, когда email не найдены
        update.message.reply_text('Email не найдены')
        logger.info('Email не найдены')
        return ConversationHandler.END # Завершаем выполнение функции
    
    emails = ''
    for i in range(len(email_list)):
        emails += f'{i+1}. {email_list[i]}\n' # Записываем email

    logger.info(f'emails - {emails}')

    response = f"Найденные email-адреса:\n{emails}\nХотите сохранить их в базу данных?\n\
          Отправьте 'да' для сохранения."
    context.user_data['email_list'] = email_list
    update.message.reply_text(response)
    return 'confirm_save_email'

def confirm_save_email(update: Update, context):
    logger.info('FUNCTION ----confirm_email----')
    if update.message.text.lower() == 'да':
        email_list = context.user_data['email_list']
        for email in email_list:
            execute_sql_command("INSERT INTO emails (email) VALUES (%s);",  [email])
            logger.info("INSERT INTO emails (email) VALUES (%s);",  [email])
        update.message.reply_text('Email-адреса сохранены.')
    else:
        update.message.reply_text('Сохранение отменено.')
    return ConversationHandler.END

def verify_password_command(update: Update, context):
    update.message.reply_text('Введите пароль для проверки его сложности: ')

    logger.info('FUNCTION ----verify_password_command----')
    logger.info('Введите пароль для проверки его сложности: ')

    return 'verify_password'

def verify_password(update: Update, context):
    logger.info('FUNCTION ----verify_password----')

    user_input = update.message.text # Получаем текст
    if user_input != None:
        logger.info('Пользователь ввел пароль.')
    if re.match(r'(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}', user_input):
        update.message.reply_text('Пароль сложный.')
        logger.info('Пароль сложный.')
    else:
        update.message.reply_text('Пароль простой.')
        logger.info('Пароль простой.')
    return ConversationHandler.END # Завершаем работу обработчика диалога


def echo(update: Update, context):
    logger.info('FUNCTION ----echo----')
    user_message = update.message.text
    update.message.reply_text(update.message.text)
    logger.info(f'user_message - {user_message}')

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('Операция отменена.')
    return ConversationHandler.END

def get_Handler(command, command_function, states, fallbacks=[CommandHandler('cancel', cancel)]):
    return ConversationHandler(
        entry_points=[CommandHandler(command, command_function)],
        states=states,
        fallbacks=fallbacks
    )

def main():
    print("main", TOKEN)
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    HandlerFindNumbers = get_Handler('find_phone_number',find_phone_number_command,
    {
        'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, find_phone_number)],
        'confirm_save_phone_number': [MessageHandler(Filters.text & ~Filters.command, confirm_save_phone_number)]
    })

# Для команды find_email
    HandlerFindEmail = get_Handler('find_email',find_email_command,
    {
        'find_email': [MessageHandler(Filters.text & ~Filters.command, find_email)],
        'confirm_save_email': [MessageHandler(Filters.text & ~Filters.command, confirm_save_email)]
    })


    HandlerVerifyPassword = get_Handler('verify_password',verify_password_command,
    {
        'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)]
    })

    HandlerGetAptList = get_Handler('get_apt_list',ssh_command,  # Это функция, которая начинает диалог
    {
        'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, apt_list_input)]
    })
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(HandlerFindNumbers)
    dp.add_handler(HandlerFindEmail)
    dp.add_handler(HandlerVerifyPassword)
    dp.add_handler(CommandHandler('get_release', ssh_command))
    dp.add_handler(CommandHandler('get_uname', ssh_command))
    dp.add_handler(CommandHandler('get_uptime', ssh_command))
    dp.add_handler(CommandHandler('get_df', ssh_command))
    dp.add_handler(CommandHandler('get_free', ssh_command))
    dp.add_handler(CommandHandler('get_mpstat', ssh_command))
    dp.add_handler(CommandHandler('get_w', ssh_command))
    dp.add_handler(CommandHandler('get_auths', ssh_command))
    dp.add_handler(CommandHandler('get_critical', ssh_command))
    dp.add_handler(CommandHandler('get_ps', ssh_command))
    dp.add_handler(CommandHandler('get_ss', ssh_command))
    dp.add_handler(HandlerGetAptList)
    dp.add_handler(CommandHandler('get_services', ssh_command))
    dp.add_handler(CommandHandler('get_release', ssh_command))

    dp.add_handler(CommandHandler('get_repl_logs', ssh_command))
    dp.add_handler(CommandHandler('get_emails', ssh_command))
    dp.add_handler(CommandHandler('get_phone_numbers', ssh_command))
	# Регистрируем обработчик текстовых сообщений
    #dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
