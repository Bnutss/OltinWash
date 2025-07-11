import json
import logging
import requests
import os
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from carwash.models import TelegramUser, Services, ServiceClasses, WashOrders
from employees.models import Employees
from django.core.files.base import ContentFile
from django.utils import timezone
import pytz
import re

logger = logging.getLogger('webhook_view')

BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
FALLBACK_ADMIN_IDS = {1207702857}

USER_STATES = {}
TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

if not BOT_TOKEN:
    logger.error("BOT_TOKEN not configured")
if not WEBHOOK_SECRET:
    logger.error("WEBHOOK_SECRET not configured")


def get_tashkent_time():
    return timezone.now().astimezone(TASHKENT_TZ)


def format_datetime(dt):
    if dt.tzinfo is None:
        dt = timezone.make_aware(dt)
    return dt.astimezone(TASHKENT_TZ).strftime('%d.%m.%Y %H:%M')


def get_user_state(user_id):
    return USER_STATES.get(str(user_id), {})


def set_user_state(user_id, state):
    USER_STATES[str(user_id)] = state


def clear_user_state(user_id):
    USER_STATES.pop(str(user_id), None)


def send_message(chat_id, text, reply_markup=None):
    if not BOT_TOKEN:
        return None

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
        logger.error(f"Send message error: {e}")
        return None


def edit_message(chat_id, message_id, text, reply_markup=None):
    if not BOT_TOKEN:
        return None

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
        logger.error(f"Edit message error: {e}")
        return None


def answer_callback_query(callback_query_id, text=None, show_alert=False):
    if not BOT_TOKEN:
        return

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
        logger.error(f"Callback query error: {e}")


def download_photo(file_id):
    if not BOT_TOKEN:
        return None

    try:
        file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        file_response = requests.get(file_url)
        file_data = file_response.json()

        if not file_data.get('ok'):
            return None

        file_path = file_data['result']['file_path']
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        photo_response = requests.get(download_url)

        if photo_response.status_code == 200:
            return photo_response.content
        return None
    except Exception as e:
        logger.error(f"Photo download error: {e}")
        return None


def is_user_authorized(telegram_id):
    if telegram_id in FALLBACK_ADMIN_IDS:
        return True
    return TelegramUser.objects.filter(telegram_id=str(telegram_id)).exists()


def is_user_admin(telegram_id):
    if telegram_id in FALLBACK_ADMIN_IDS:
        return True
    try:
        user = TelegramUser.objects.get(telegram_id=str(telegram_id))
        return user.is_admin
    except TelegramUser.DoesNotExist:
        return False


def get_today_orders_count():
    today = get_tashkent_time().date()
    return WashOrders.objects.filter(time_create__date=today).count()


def get_services_keyboard():
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

        buttons.append([{
            'text': "◀️ Назад в меню",
            'callback_data': "main_menu"
        }])

        return {'inline_keyboard': buttons}
    except Exception as e:
        logger.error(f"Services keyboard error: {e}")
        return {'inline_keyboard': []}


def get_service_classes_keyboard(service_id):
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
        logger.error(f"Service classes keyboard error: {e}")
        return {'inline_keyboard': []}


def get_employees_keyboard():
    try:
        employees = Employees.objects.filter(fired=False)
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
        logger.error(f"Employees keyboard error: {e}")
        return {'inline_keyboard': []}


def get_admin_keyboard():
    buttons = [
        [{'text': '🚗 Создать заказ', 'callback_data': 'new_order'}],
        [{'text': '👤 Добавить пользователя', 'callback_data': 'add_user'}],
        [{'text': '📊 Список пользователей', 'callback_data': 'list_users'}],
        [{'text': '📋 Последние заказы', 'callback_data': 'recent_orders'}],
    ]
    return {'inline_keyboard': buttons}


def handle_start_command(chat_id, user_data):
    telegram_id = user_data['id']
    first_name = user_data.get('first_name', 'Пользователь')
    username = user_data.get('username')

    clear_user_state(telegram_id)

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
        logger.error(f"User create/update error: {e}")

    today_orders_count = get_today_orders_count()

    if is_user_admin(telegram_id):
        users_count = TelegramUser.objects.count()
        welcome_text = f"""
🌟 <b>Добро пожаловать в OltinWash!</b> 🌟

Привет, <b>{first_name}</b>! 👋
👑 <b>Режим администратора</b>

🔥 <b>Премиальная автомойка в Чирчике</b>
✨ Профессиональный уход за вашим авто
💎 Высочайшее качество обслуживания

📊 Заказов сегодня: <b>{today_orders_count}</b>
👥 Авторизованных пользователей: <b>{users_count}</b>

🚗 <b>Выберите действие:</b>
"""
        keyboard = get_admin_keyboard()
    else:
        welcome_text = f"""
🌟 <b>Добро пожаловать в OltinWash!</b> 🌟

Привет, <b>{first_name}</b>! 👋

🔥 <b>Премиальная автомойка в Чирчике</b>
✨ Профессиональный уход за вашим авто
💎 Высочайшее качество обслуживания

📊 Заказов сегодня: <b>{today_orders_count}</b>

🚗 <b>Выберите услугу:</b>
"""
        keyboard = get_services_keyboard()

    send_message(chat_id, welcome_text, keyboard)


def handle_new_order(chat_id, message_id):
    text = """
🏆 <b>СОЗДАНИЕ ЗАКАЗА</b> 🏆

🔥 <b>Выберите тип мойки для вашего авто:</b>

📝 <i>Пошаги создания заказа:</i>
1️⃣ Выбор услуги
2️⃣ Выбор класса обслуживания  
3️⃣ Выбор мастера
4️⃣ Указание цены (если нужно)
5️⃣ Загрузка фото автомобиля
"""
    keyboard = get_services_keyboard()
    edit_message(chat_id, message_id, text, keyboard)


def handle_service_selection(chat_id, message_id, service_id, user_id):
    try:
        service = Services.objects.get(id=service_id)

        state = get_user_state(user_id)
        state['step'] = 'service_selected'
        state['service_id'] = service_id
        state['service_name'] = service.name_services
        set_user_state(user_id, state)

        text = f"""
🎯 <b>ВЫБОР КЛАССА УСЛУГИ</b>

🚗 <b>Выбранная услуга:</b> {service.name_services}

💎 <b>Выберите класс обслуживания:</b>
"""
        keyboard = get_service_classes_keyboard(service_id)
        edit_message(chat_id, message_id, text, keyboard)
    except Services.DoesNotExist:
        edit_message(chat_id, message_id, "❌ Услуга не найдена")


def handle_class_selection(chat_id, message_id, class_id, user_id):
    try:
        service_class = ServiceClasses.objects.get(id=class_id)

        state = get_user_state(user_id)
        state['step'] = 'class_selected'
        state['class_id'] = class_id
        state['class_name'] = service_class.name
        state['default_price'] = float(service_class.price) if service_class.price else 0
        set_user_state(user_id, state)

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


def handle_employee_selection(chat_id, message_id, employee_id, user_id):
    try:
        employee = Employees.objects.get(id=employee_id)

        state = get_user_state(user_id)
        state['step'] = 'employee_selected'
        state['employee_id'] = employee_id
        state['employee_name'] = str(employee)
        set_user_state(user_id, state)

        price_text = f"{int(state['default_price']):,} UZS" if state['default_price'] else "Договорная"

        text = f"""
💰 <b>УКАЗАНИЕ ЦЕНЫ</b>

👨‍🔧 <b>Выбранный мастер:</b> {employee}
💵 <b>Стандартная цена:</b> {price_text}

🔹 <b>Выберите действие:</b>
"""

        buttons = []
        if state['default_price']:
            buttons.append([{
                'text': f"✅ Оставить стандартную ({int(state['default_price']):,} UZS)",
                'callback_data': f"price_default"
            }])

        buttons.extend([
            [{'text': '✏️ Указать свою цену', 'callback_data': 'price_custom'}],
            [{'text': '◀️ Назад к мастерам', 'callback_data': 'back_to_employees'}]
        ])

        keyboard = {'inline_keyboard': buttons}
        edit_message(chat_id, message_id, text, keyboard)
    except Employees.DoesNotExist:
        edit_message(chat_id, message_id, "❌ Сотрудник не найден")


def handle_price_selection(chat_id, message_id, user_id, price_type):
    state = get_user_state(user_id)

    if price_type == 'default':
        state['step'] = 'price_set'
        state['final_price'] = state['default_price']
        set_user_state(user_id, state)
        request_photo(chat_id, message_id, user_id)

    elif price_type == 'custom':
        state['step'] = 'waiting_price'
        state['price_message_id'] = message_id
        set_user_state(user_id, state)

        text = f"""
✏️ <b>ВВОД ЦЕНЫ</b>

💰 <b>Введите цену заказа:</b>

📝 <i>Напишите сумму числом (например: 50000)</i>
⚠️ <i>Только цифры без пробелов и символов</i>

🔙 <i>Для отмены напишите /start</i>
"""

        edit_message(chat_id, message_id, text)


def request_photo(chat_id, message_id, user_id):
    state = get_user_state(user_id)

    price_text = f"{int(state['final_price']):,} UZS" if state['final_price'] else "Договорная"

    text = f"""
📸 <b>ЗАГРУЗКА ФОТО</b>

✅ <b>Детали заказа:</b>
🚗 Услуга: {state['service_name']}
⭐ Класс: {state['class_name']}
👨‍🔧 Мастер: {state['employee_name']}
💰 Цена: {price_text}

📷 <b>Отправьте фото автомобиля</b>

⚠️ <i>Обязательно отправьте фото для создания заказа!</i>
🔙 <i>Для отмены напишите /start</i>
"""

    state['step'] = 'waiting_photo'
    set_user_state(user_id, state)

    if message_id:
        edit_message(chat_id, message_id, text)
    else:
        send_message(chat_id, text)


def create_order(chat_id, user_id, photo_content, file_name):
    try:
        state = get_user_state(user_id)

        service_class = ServiceClasses.objects.get(id=state['class_id'])
        employee = Employees.objects.get(id=state['employee_id'])

        order = WashOrders()
        order.type_of_car_wash = service_class
        order.employees = employee
        order.negotiated_price = state['final_price']

        order.car_photo.save(file_name, ContentFile(photo_content), save=False)
        order.save()

        clear_user_state(user_id)

        price_text = f"{int(state['final_price']):,} UZS" if state['final_price'] else "Договорная"

        success_text = f"""
✅ <b>ЗАКАЗ СОЗДАН УСПЕШНО!</b>

🎉 <b>Заказ №{order.id}</b>

📋 <b>Детали:</b>
🚗 Услуга: {state['service_name']}
⭐ Класс: {state['class_name']}
👨‍🔧 Мастер: {state['employee_name']}
💰 Цена: {price_text}
📅 Дата: {format_datetime(order.time_create)}

✨ <b>Спасибо за выбор OltinWash!</b>
"""

        keyboard = {
            'inline_keyboard': [[
                {'text': '🚗 Новый заказ', 'callback_data': 'new_order'},
                {'text': '🏠 Главное меню', 'callback_data': 'main_menu'}
            ]]
        }

        send_message(chat_id, success_text, keyboard)
        return True

    except Exception as e:
        logger.error(f"Order creation error: {e}")
        error_text = """
❌ <b>ОШИБКА СОЗДАНИЯ ЗАКАЗА</b>

🔧 Произошла техническая ошибка
📞 Обратитесь к администратору

🔄 Попробуйте создать заказ заново
"""
        send_message(chat_id, error_text)
        clear_user_state(user_id)
        return False


def handle_recent_orders(chat_id, message_id):
    try:
        orders = WashOrders.objects.order_by('-time_create')[:10]

        if not orders:
            text = "📋 <b>ЗАКАЗЫ НЕ НАЙДЕНЫ</b>\n\n🔍 Пока нет ни одного заказа"
        else:
            text = f"📋 <b>ПОСЛЕДНИЕ ЗАКАЗЫ</b>\n\n📊 <b>Показано:</b> {len(orders)}\n\n"

            for order in orders:
                status = "✅" if order.is_completed else "⏳"
                price = f"{int(order.negotiated_price):,} UZS" if order.negotiated_price else "Договорная"
                date = format_datetime(order.time_create)

                text += f"{status} <b>#{order.id}</b> - {order.type_of_car_wash.name}\n"
                text += f"👨‍🔧 {order.employees}\n"
                text += f"💰 {price} | 📅 {date}\n\n"

        back_button = {
            'inline_keyboard': [[
                {'text': '◀️ Назад', 'callback_data': 'admin_menu'}
            ]]
        }

        edit_message(chat_id, message_id, text, back_button)

    except Exception as e:
        logger.error(f"Recent orders error: {e}")
        edit_message(chat_id, message_id, "❌ Ошибка получения заказов")


def handle_list_users(chat_id, message_id):
    users = TelegramUser.objects.all().order_by('-created_at')

    users_text = f"""
👥 <b>СПИСОК ПОЛЬЗОВАТЕЛЕЙ</b>

📊 <b>Всего:</b> {users.count()}

👤 <b>Пользователи:</b>
"""

    for i, user in enumerate(users[:20], 1):
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
    today_orders_count = get_today_orders_count()
    users_count = TelegramUser.objects.count()

    text = f"""
🌟 <b>Админ панель OltinWash</b> 🌟

👑 <b>Режим администратора</b>

📊 Заказов сегодня: <b>{today_orders_count}</b>
👥 Авторизованных пользователей: <b>{users_count}</b>

🚗 <b>Выберите действие:</b>
"""

    keyboard = get_admin_keyboard()
    edit_message(chat_id, message_id, text, keyboard)


def handle_add_user_start(chat_id, message_id, user_id):
    state = get_user_state(user_id)
    state['step'] = 'waiting_user_id'
    set_user_state(user_id, state)

    text = """
👤 <b>ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ</b>

📝 <b>Введите Telegram ID пользователя:</b>

💡 <i>Пользователь должен написать боту @userinfobot чтобы узнать свой ID</i>

⚠️ <i>Введите только числовой ID (например: 123456789)</i>

🔙 <i>Для отмены напишите /start</i>
"""

    edit_message(chat_id, message_id, text)


def handle_add_user_process(chat_id, user_id, telegram_id_to_add):
    try:
        if TelegramUser.objects.filter(telegram_id=str(telegram_id_to_add)).exists():
            error_text = f"""
❌ <b>ПОЛЬЗОВАТЕЛЬ УЖЕ СУЩЕСТВУЕТ</b>

👤 Пользователь с ID <code>{telegram_id_to_add}</code> уже добавлен в систему

🔄 Попробуйте добавить другого пользователя или используйте /start для возврата в меню
"""
            send_message(chat_id, error_text)
            return

        user = TelegramUser.objects.create(
            telegram_id=str(telegram_id_to_add),
            first_name="Новый пользователь",
            is_admin=False
        )

        clear_user_state(user_id)

        success_text = f"""
✅ <b>ПОЛЬЗОВАТЕЛЬ ДОБАВЛЕН УСПЕШНО!</b>

👤 <b>Telegram ID:</b> <code>{telegram_id_to_add}</code>
📅 <b>Дата добавления:</b> {format_datetime(user.created_at)}

✨ Пользователь может теперь пользоваться ботом!

💡 <i>Имя и username обновятся автоматически при первом обращении к боту</i>
"""

        keyboard = {
            'inline_keyboard': [[
                {'text': '👤 Добавить еще пользователя', 'callback_data': 'add_user'},
                {'text': '🏠 Главное меню', 'callback_data': 'admin_menu'}
            ]]
        }

        send_message(chat_id, success_text, keyboard)

    except Exception as e:
        logger.error(f"Add user error: {e}")
        error_text = """
❌ <b>ОШИБКА ДОБАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯ</b>

🔧 Произошла техническая ошибка
📞 Обратитесь к разработчику

🔄 Попробуйте еще раз или напишите /start
"""
        send_message(chat_id, error_text)
        clear_user_state(user_id)


def send_access_denied(chat_id, user_data):
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
    chat_id = message_data['chat']['id']
    user_data = message_data['from']
    user_id = user_data['id']
    text = message_data.get('text', '')

    if not is_user_authorized(user_id):
        send_access_denied(chat_id, user_data)
        return

    state = get_user_state(user_id)

    if text == '/start':
        handle_start_command(chat_id, user_data)
        return

    if state.get('step') == 'waiting_price':
        if re.match(r'^\d+$', text.strip()):
            price = float(text.strip())
            state['step'] = 'price_set'
            state['final_price'] = price
            set_user_state(user_id, state)
            request_photo(chat_id, None, user_id)
        else:
            error_text = """
❌ <b>НЕВЕРНЫЙ ФОРМАТ ЦЕНЫ</b>

💰 Введите цену числом (например: 50000)
⚠️ Только цифры без пробелов и символов

🔄 Попробуйте еще раз или напишите /start для отмены
"""
            send_message(chat_id, error_text)
        return

    if state.get('step') == 'waiting_user_id':
        if re.match(r'^\d+$', text.strip()):
            telegram_id_to_add = int(text.strip())
            handle_add_user_process(chat_id, user_id, telegram_id_to_add)
        else:
            error_text = """
❌ <b>НЕВЕРНЫЙ ФОРМАТ ID</b>

👤 Введите Telegram ID числом (например: 123456789)
⚠️ Только цифры без пробелов и символов

💡 Пользователь может узнать свой ID у бота @userinfobot

🔄 Попробуйте еще раз или напишите /start для отмены
"""
            send_message(chat_id, error_text)
        return

    if text == '/users' and is_user_admin(user_id):
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


def process_photo(message_data):
    chat_id = message_data['chat']['id']
    user_data = message_data['from']
    user_id = user_data['id']

    if not is_user_authorized(user_id):
        send_access_denied(chat_id, user_data)
        return

    state = get_user_state(user_id)

    if state.get('step') != 'waiting_photo':
        send_message(chat_id, "❌ Сначала создайте заказ командой /start")
        return

    try:
        photo = message_data['photo'][-1]
        file_id = photo['file_id']

        photo_content = download_photo(file_id)

        if photo_content:
            tashkent_time = get_tashkent_time()
            file_name = f"car_photo_{user_id}_{tashkent_time.strftime('%Y%m%d_%H%M%S')}.jpg"

            success = create_order(chat_id, user_id, photo_content, file_name)

            if not success:
                send_message(chat_id, "❌ Ошибка при сохранении заказа. Попробуйте еще раз.")
        else:
            send_message(chat_id, "❌ Ошибка при загрузке фото. Попробуйте отправить другое фото.")

    except Exception as e:
        logger.error(f"Photo processing error: {e}")
        send_message(chat_id, "❌ Ошибка при обработке фото. Попробуйте еще раз.")


def process_callback_query(callback_data):
    query_id = callback_data['id']
    chat_id = callback_data['message']['chat']['id']
    message_id = callback_data['message']['message_id']
    user_data = callback_data['from']
    user_id = user_data['id']
    data = callback_data['data']

    if not is_user_authorized(user_id):
        answer_callback_query(query_id, "🚫 Доступ запрещен", show_alert=True)
        return

    answer_callback_query(query_id)

    if data == 'main_menu':
        clear_user_state(user_id)
        handle_start_command(chat_id, user_data)
    elif data == 'new_order':
        clear_user_state(user_id)
        handle_new_order(chat_id, message_id)
    elif data == 'list_users':
        if is_user_admin(user_id):
            handle_list_users(chat_id, message_id)
    elif data == 'recent_orders':
        if is_user_admin(user_id):
            handle_recent_orders(chat_id, message_id)
    elif data == 'admin_menu':
        if is_user_admin(user_id):
            handle_admin_menu(chat_id, message_id)
    elif data == 'back_to_services':
        clear_user_state(user_id)
        handle_new_order(chat_id, message_id)
    elif data == 'back_to_classes':
        state = get_user_state(user_id)
        if 'service_id' in state:
            handle_service_selection(chat_id, message_id, state['service_id'], user_id)
    elif data == 'back_to_employees':
        state = get_user_state(user_id)
        if 'class_id' in state:
            handle_class_selection(chat_id, message_id, state['class_id'], user_id)
    elif data.startswith('service_'):
        service_id = int(data.split('_')[1])
        handle_service_selection(chat_id, message_id, service_id, user_id)
    elif data.startswith('class_'):
        class_id = int(data.split('_')[1])
        handle_class_selection(chat_id, message_id, class_id, user_id)
    elif data.startswith('employee_'):
        employee_id = int(data.split('_')[1])
        handle_employee_selection(chat_id, message_id, employee_id, user_id)
    elif data == 'price_default':
        handle_price_selection(chat_id, message_id, user_id, 'default')
    elif data == 'price_custom':
        handle_price_selection(chat_id, message_id, user_id, 'custom')
    elif data == 'add_user':
        if is_user_admin(user_id):
            clear_user_state(user_id)
            handle_add_user_start(chat_id, message_id, user_id)


def verify_telegram_request(request):
    user_agent = request.headers.get('User-Agent', '')
    if not user_agent.startswith('TelegramBot'):
        logger.warning(f"Invalid User-Agent: {user_agent}")
        return False

    if WEBHOOK_SECRET:
        secret_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if secret_token != WEBHOOK_SECRET:
            logger.warning(f"Invalid secret token from {request.META.get('REMOTE_ADDR')}")
            return False

    return True


@csrf_exempt
@require_POST
def telegram_webhook(request):
    try:
        if not verify_telegram_request(request):
            logger.warning(f"Unauthorized access from {request.META.get('REMOTE_ADDR')}")
            return HttpResponseForbidden("Access denied")

        if not BOT_TOKEN:
            logger.error("Bot not configured")
            return HttpResponseForbidden("Bot not configured")

        logger.info("Secure webhook received")

        update_data = json.loads(request.body.decode('utf-8'))

        if 'message' in update_data:
            message = update_data['message']

            if 'photo' in message:
                process_photo(message)
            elif 'text' in message:
                process_message(message)

        elif 'callback_query' in update_data:
            process_callback_query(update_data['callback_query'])

        return HttpResponse("OK")

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return HttpResponse("Invalid JSON", status=400)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return HttpResponse(f"Error: {str(e)}", status=500)
