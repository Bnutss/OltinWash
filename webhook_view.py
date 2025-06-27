import json
import logging
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from carwash.models import TelegramUser, Services, ServiceClasses, WashOrders
from employees.models import Employees

logger = logging.getLogger(__name__)

BOT_TOKEN = "8087998931:AAGykWvkx-deJ8G5O0kmfoI_TcJXl2fLMtE"
FALLBACK_ADMIN_IDS = {1207702857}


def send_message(chat_id, text, reply_markup=None):
    """Отправка сообщения через Telegram API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)

    try:
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        return None


def edit_message(chat_id, message_id, text, reply_markup=None):
    """Редактирование сообщения"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)

    try:
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")
        return None


def answer_callback_query(callback_query_id, text=None, show_alert=False):
    """Ответ на callback query"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    data = {
        'callback_query_id': callback_query_id,
        'show_alert': show_alert
    }
    if text:
        data['text'] = text

    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        logger.error(f"Ошибка ответа на callback: {e}")


def is_user_authorized(telegram_id):
    """Проверка авторизации пользователя"""
    if telegram_id in FALLBACK_ADMIN_IDS:
        return True
    return TelegramUser.objects.filter(telegram_id=str(telegram_id)).exists()


def is_user_admin(telegram_id):
    """Проверка прав администратора"""
    if telegram_id in FALLBACK_ADMIN_IDS:
        return True
    try:
        user = TelegramUser.objects.get(telegram_id=str(telegram_id))
        return user.is_admin
    except TelegramUser.DoesNotExist:
        return False


def get_services_keyboard():
    """Клавиатура с услугами"""
    try:
        services = Services.objects.all()
        buttons = []

        service_emojis = ['🚗', '🚚', '🏍️', '🚌', '🚛', '🛻']

        for i, service in enumerate(services):
            emoji = service_emojis[i % len(service_emojis)]
            buttons.append([{
                'text': f"{emoji} {service.name_services}",
                'callback_data': f"service_{service.id}"
            }])

        return {'inline_keyboard': buttons}
    except Exception as e:
        logger.error(f"Ошибка получения услуг: {e}")
        return {'inline_keyboard': []}


def get_service_classes_keyboard(service_id):
    """Клавиатура с классами услуг"""
    try:
        classes = ServiceClasses.objects.filter(services_id=service_id)
        buttons = []

        class_emojis = {
            'эконом': '🥉',
            'стандарт': '🥈',
            'премиум': '🥇',
            'vip': '👑',
            'люкс': '💎'
        }

        for cls in classes:
            emoji = '⭐'
            for key, value in class_emojis.items():
                if key in cls.name.lower():
                    emoji = value
                    break

            price_text = f" • {int(cls.price):,} UZS" if cls.price else " • Договорная"
            buttons.append([{
                'text': f"{emoji} {cls.name}{price_text}",
                'callback_data': f"class_{cls.id}"
            }])

        buttons.append([{
            'text': "◀️ Назад к услугам",
            'callback_data': "back_to_services"
        }])

        return {'inline_keyboard': buttons}
    except Exception as e:
        logger.error(f"Ошибка получения классов: {e}")
        return {'inline_keyboard': []}


def get_employees_keyboard():
    """Клавиатура с сотрудниками"""
    try:
        employees = Employees.objects.all()
        buttons = []

        worker_emojis = ['👨‍🔧', '👩‍🔧', '🧑‍🔧', '👨‍💼', '👩‍💼']

        for i, employee in enumerate(employees):
            emoji = worker_emojis[i % len(worker_emojis)]
            buttons.append([{
                'text': f"{emoji} {str(employee)}",
                'callback_data': f"employee_{employee.id}"
            }])

        buttons.append([{
            'text': "◀️ Назад к классам",
            'callback_data': "back_to_classes"
        }])

        return {'inline_keyboard': buttons}
    except Exception as e:
        logger.error(f"Ошибка получения сотрудников: {e}")
        return {'inline_keyboard': []}


def get_admin_keyboard():
    """Клавиатура для админа"""
    buttons = [
        [{'text': '🚗 Создать заказ', 'callback_data': 'new_order'}],
        [{'text': '👤 Добавить пользователя', 'callback_data': 'add_user'}],
        [{'text': '📊 Список пользователей', 'callback_data': 'list_users'}],
        [{'text': '🗑️ Удалить пользователя', 'callback_data': 'delete_user'}],
    ]
    return {'inline_keyboard': buttons}


def handle_start_command(chat_id, user_data):
    """Обработка команды /start"""
    telegram_id = user_data['id']
    first_name = user_data.get('first_name', 'Пользователь')
    username = user_data.get('username')

    # Обновляем/создаем пользователя
    try:
        user, created = TelegramUser.objects.get_or_create(
            telegram_id=str(telegram_id),
            defaults={
                'first_name': first_name,
                'username': username,
                'is_admin': telegram_id in FALLBACK_ADMIN_IDS
            }
        )
        if not created:
            user.first_name = first_name
            user.username = username
            user.save()
    except Exception as e:
        logger.error(f"Ошибка создания/обновления пользователя: {e}")

    orders_count = WashOrders.objects.count()

    if is_user_admin(telegram_id):
        users_count = TelegramUser.objects.count()
        welcome_text = f"""
🌟 <b>Добро пожаловать в OltinWash!</b> 🌟

Привет, <b>{first_name}</b>! 👋
👑 <b>Режим администратора</b>

🔥 <b>Премиальная автомойка в Ташкенте</b>
✨ Профессиональный уход за вашим авто
💎 Высочайшее качество обслуживания

📊 Всего заказов выполнено: <b>{orders_count}</b>
👥 Авторизованных пользователей: <b>{users_count}</b>

🚗 <b>Выберите действие:</b>
"""
        keyboard = get_admin_keyboard()
    else:
        welcome_text = f"""
🌟 <b>Добро пожаловать в OltinWash!</b> 🌟

Привет, <b>{first_name}</b>! 👋

🔥 <b>Премиальная автомойка в Ташкенте</b>
✨ Профессиональный уход за вашим авто
💎 Высочайшее качество обслуживания

📊 Всего заказов выполнено: <b>{orders_count}</b>

🚗 <b>Выберите услугу:</b>
"""
        keyboard = get_services_keyboard()

    send_message(chat_id, welcome_text, keyboard)


def handle_new_order(chat_id, message_id):
    """Начало создания заказа"""
    text = """
🏆 <b>ВЫБОР УСЛУГИ</b> 🏆

🔥 <b>Выберите тип мойки для вашего авто:</b>
"""
    keyboard = get_services_keyboard()
    edit_message(chat_id, message_id, text, keyboard)


def handle_service_selection(chat_id, message_id, service_id):
    """Выбор услуги"""
    try:
        service = Services.objects.get(id=service_id)
        text = f"""
🎯 <b>ВЫБОР КЛАССА УСЛУГИ</b>

🚗 <b>Выбранная услуга:</b> {service.name_services}

💎 <b>Выберите класс обслуживания:</b>
"""
        keyboard = get_service_classes_keyboard(service_id)
        edit_message(chat_id, message_id, text, keyboard)
    except Services.DoesNotExist:
        edit_message(chat_id, message_id, "❌ Услуга не найдена")


def handle_class_selection(chat_id, message_id, class_id):
    """Выбор класса услуги"""
    try:
        service_class = ServiceClasses.objects.get(id=class_id)
        price_text = f"{int(service_class.price):,} UZS" if service_class.price else "Договорная цена"

        text = f"""
👨‍🔧 <b>ВЫБОР МАСТЕРА</b>

⭐ <b>Выбранный класс:</b> {service_class.name}
💰 <b>Стоимость:</b> {price_text}

🔥 <b>Выберите мастера:</b>
"""
        keyboard = get_employees_keyboard()
        edit_message(chat_id, message_id, text, keyboard)
    except ServiceClasses.DoesNotExist:
        edit_message(chat_id, message_id, "❌ Класс услуги не найден")


def handle_employee_selection(chat_id, message_id, employee_id):
    """Выбор сотрудника"""
    try:
        employee = Employees.objects.get(id=employee_id)
        text = f"""
✅ <b>ЗАКАЗ ОФОРМЛЕН!</b>

👨‍🔧 <b>Выбранный мастер:</b> {employee}

📞 <b>Для завершения оформления заказа свяжитесь с нами:</b>
- Телефон: +998 XX XXX XX XX
- Или напишите администратору

🕐 <b>Ожидайте звонка для уточнения деталей</b>

✨ <b>Спасибо за выбор OltinWash!</b>
"""

        new_order_button = {
            'inline_keyboard': [[
                {'text': '🚗 Создать новый заказ', 'callback_data': 'new_order'}
            ]]
        }

        edit_message(chat_id, message_id, text, new_order_button)
    except Employees.DoesNotExist:
        edit_message(chat_id, message_id, "❌ Сотрудник не найден")


def handle_list_users(chat_id, message_id):
    """Список пользователей"""
    users = TelegramUser.objects.all().order_by('-created_at')

    users_text = f"""
👥 <b>СПИСОК ПОЛЬЗОВАТЕЛЕЙ</b>

📊 <b>Всего:</b> {users.count()}

👤 <b>Пользователи:</b>
"""

    for i, user in enumerate(users[:20], 1):  # Показываем только первые 20
        admin_mark = " 👑" if user.is_admin else ""
        username_text = f" (@{user.username})" if user.username else ""
        users_text += f"<code>{i}. {user.telegram_id}</code> - {user.first_name}{username_text}{admin_mark}\n"

    if users.count() > 20:
        users_text += f"\n... и еще {users.count() - 20} пользователей"

    back_button = {
        'inline_keyboard': [[
            {'text': '◀️ Назад', 'callback_data': 'admin_menu'}
        ]]
    }

    edit_message(chat_id, message_id, users_text, back_button)


def handle_admin_menu(chat_id, message_id):
    """Админ меню"""
    orders_count = WashOrders.objects.count()
    users_count = TelegramUser.objects.count()

    text = f"""
🌟 <b>Админ панель OltinWash</b> 🌟

👑 <b>Режим администратора</b>

📊 Всего заказов выполнено: <b>{orders_count}</b>
👥 Авторизованных пользователей: <b>{users_count}</b>

🚗 <b>Выберите действие:</b>
"""

    keyboard = get_admin_keyboard()
    edit_message(chat_id, message_id, text, keyboard)


def send_access_denied(chat_id, user_data):
    """Отправка сообщения об отказе в доступе"""
    user_id = user_data['id']
    user_name = user_data.get('first_name', 'Пользователь')

    deny_text = f"""
🚫 <b>ДОСТУП ЗАПРЕЩЕН</b> 🚫

❌ <b>Извините, {user_name}!</b>

🔒 Этот бот доступен только для авторизованных пользователей

👤 <b>Ваш ID:</b> <code>{user_id}</code>

📞 <b>Для получения доступа обратитесь к администратору</b>

⚠️ <b>Укажите ваш ID при обращении</b>
"""

    send_message(chat_id, deny_text)


def process_message(message_data):
    """Обработка текстового сообщения"""
    chat_id = message_data['chat']['id']
    user_data = message_data['from']
    text = message_data.get('text', '')

    # Проверяем доступ
    if not is_user_authorized(user_data['id']):
        send_access_denied(chat_id, user_data)
        return

    if text == '/start':
        handle_start_command(chat_id, user_data)
    elif text == '/users' and is_user_admin(user_data['id']):
        # Отправляем список пользователей как новое сообщение
        users = TelegramUser.objects.all().order_by('-created_at')
        users_text = f"👥 <b>СПИСОК ПОЛЬЗОВАТЕЛЕЙ</b>\n\n📊 <b>Всего:</b> {users.count()}\n\n"

        for i, user in enumerate(users[:20], 1):
            admin_mark = " 👑" if user.is_admin else ""
            username_text = f" (@{user.username})" if user.username else ""
            users_text += f"<code>{i}. {user.telegram_id}</code> - {user.first_name}{username_text}{admin_mark}\n"

        send_message(chat_id, users_text)
    else:
        help_text = """
❓ <b>НЕИЗВЕСТНАЯ КОМАНДА</b>

💡 <b>Доступные команды:</b>
- /start - Главное меню
- /users - Список пользователей (для админов)

🚗 <b>Используйте /start для работы с ботом</b>
"""
        send_message(chat_id, help_text)


def process_callback_query(callback_data):
    """Обработка callback query"""
    query_id = callback_data['id']
    chat_id = callback_data['message']['chat']['id']
    message_id = callback_data['message']['message_id']
    user_data = callback_data['from']
    data = callback_data['data']

    # Проверяем доступ
    if not is_user_authorized(user_data['id']):
        answer_callback_query(query_id, "🚫 Доступ запрещен", show_alert=True)
        return

    # Отвечаем на callback query
    answer_callback_query(query_id)

    if data == 'new_order':
        handle_new_order(chat_id, message_id)
    elif data == 'list_users':
        if is_user_admin(user_data['id']):
            handle_list_users(chat_id, message_id)
        else:
            answer_callback_query(query_id, "🚫 Только для администраторов", show_alert=True)
    elif data == 'admin_menu':
        if is_user_admin(user_data['id']):
            handle_admin_menu(chat_id, message_id)
    elif data == 'back_to_services':
        handle_new_order(chat_id, message_id)
    elif data.startswith('service_'):
        service_id = int(data.split('_')[1])
        handle_service_selection(chat_id, message_id, service_id)
    elif data.startswith('class_'):
        class_id = int(data.split('_')[1])
        handle_class_selection(chat_id, message_id, class_id)
    elif data.startswith('employee_'):
        employee_id = int(data.split('_')[1])
        handle_employee_selection(chat_id, message_id, employee_id)
    elif data == 'add_user':
        if is_user_admin(user_data['id']):
            text = """
👤 <b>ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ</b>

📝 <b>Функция в разработке</b>

💡 <b>Пока добавляйте пользователей через Django админку:</b>
/admin/

🔄 <b>Используйте /start для возврата в меню</b>
"""
            edit_message(chat_id, message_id, text)
    elif data == 'delete_user':
        if is_user_admin(user_data['id']):
            text = """
🗑️ <b>УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ</b>

📝 <b>Функция в разработке</b>

💡 <b>Пока удаляйте пользователей через Django админку:</b>
/admin/

🔄 <b>Используйте /start для возврата в меню</b>
"""
            edit_message(chat_id, message_id, text)


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """Основная функция webhook"""
    try:
        logger.info("Webhook получен")

        # Читаем данные обновления
        update_data = json.loads(request.body.decode('utf-8'))
        logger.info(f"Update data: {update_data}")

        # Обрабатываем сообщение
        if 'message' in update_data:
            process_message(update_data['message'])

        # Обрабатываем callback query
        elif 'callback_query' in update_data:
            process_callback_query(update_data['callback_query'])

        return HttpResponse("OK")

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return HttpResponse("Invalid JSON", status=400)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error: {str(e)}", status=500)
