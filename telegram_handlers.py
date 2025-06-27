from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from datetime import datetime, timezone, timedelta
from functools import wraps

from carwash.models import Services, ServiceClasses, WashOrders, TelegramUser
from employees.models import Employees

FALLBACK_ADMIN_IDS = {
    1207702857,
}

TASHKENT_TZ = timezone(timedelta(hours=5))


class OrderStates(StatesGroup):
    choosing_service = State()
    choosing_class = State()
    choosing_employee = State()
    uploading_photo = State()
    confirming_order = State()


class AdminStates(StatesGroup):
    adding_user = State()
    deleting_user = State()


router = Router()


@sync_to_async
def get_telegram_user(telegram_id):
    try:
        return TelegramUser.objects.get(telegram_id=str(telegram_id))
    except TelegramUser.DoesNotExist:
        return None


@sync_to_async
def is_user_authorized(telegram_id):
    return TelegramUser.objects.filter(telegram_id=str(telegram_id)).exists()


@sync_to_async
def is_user_admin(telegram_id):
    try:
        user = TelegramUser.objects.get(telegram_id=str(telegram_id))
        return user.is_admin
    except TelegramUser.DoesNotExist:
        return telegram_id in FALLBACK_ADMIN_IDS


@sync_to_async
def get_all_telegram_users():
    return list(TelegramUser.objects.all().order_by('-created_at'))


@sync_to_async
def create_telegram_user(telegram_id, username=None, first_name=None, is_admin=False):
    try:
        user = TelegramUser.objects.create(
            telegram_id=str(telegram_id),
            username=username,
            first_name=first_name or f"User_{telegram_id}",
            is_admin=is_admin
        )
        return user
    except Exception as e:
        print(f"Ошибка создания пользователя: {e}")
        return None


@sync_to_async
def delete_telegram_user(telegram_id):
    try:
        user = TelegramUser.objects.get(telegram_id=str(telegram_id))
        user.delete()
        return True
    except TelegramUser.DoesNotExist:
        return False


@sync_to_async
def update_telegram_user(telegram_id, username=None, first_name=None):
    try:
        user = TelegramUser.objects.get(telegram_id=str(telegram_id))
        if username:
            user.username = username
        if first_name:
            user.first_name = first_name
        user.save()
        return user
    except TelegramUser.DoesNotExist:
        return None


async def check_access(telegram_id):
    return await is_user_authorized(telegram_id) or telegram_id in FALLBACK_ADMIN_IDS


async def check_admin_access(telegram_id):
    return await is_user_admin(telegram_id) or telegram_id in FALLBACK_ADMIN_IDS


def access_required(func):
    @wraps(func)
    async def wrapper(update, *args, **kwargs):
        user_id = None

        if isinstance(update, Message):
            user_id = update.from_user.id
        elif isinstance(update, CallbackQuery):
            user_id = update.from_user.id

        if not await check_access(user_id):
            await send_access_denied(update)
            return

        return await func(update, *args, **kwargs)

    return wrapper


async def send_access_denied(update):
    user_id = update.from_user.id
    user_name = update.from_user.first_name or "Пользователь"

    deny_text = f"""
🚫 <b>ДОСТУП ЗАПРЕЩЕН</b> 🚫

❌ <b>Извините, {user_name}!</b>

🔒 Этот бот доступен только для авторизованных пользователей

👤 <b>Ваш ID:</b> <code>{user_id}</code>

📞 <b>Для получения доступа обратитесь к администратору</b>

⚠️ <b>Укажите ваш ID при обращении</b>

💡 <b>Администратор может добавить вас через команду /add_user в боте</b>
"""

    if isinstance(update, Message):
        await update.answer(deny_text, parse_mode="HTML")
    elif isinstance(update, CallbackQuery):
        await update.answer("🚫 Доступ запрещен", show_alert=True)


@sync_to_async
def get_all_services():
    return list(Services.objects.all())


@sync_to_async
def get_service_by_id(service_id):
    return Services.objects.get(id=service_id)


@sync_to_async
def get_service_classes_by_service(service_id):
    return list(ServiceClasses.objects.filter(services_id=service_id))


@sync_to_async
def get_service_class_by_id(class_id):
    return ServiceClasses.objects.get(id=class_id)


@sync_to_async
def get_all_employees():
    return list(Employees.objects.all())


@sync_to_async
def get_employee_by_id(employee_id):
    return Employees.objects.get(id=employee_id)


@sync_to_async
def create_wash_order(type_of_car_wash, employee, car_photo_content, filename):
    from django.core.files.base import ContentFile
    return WashOrders.objects.create(
        type_of_car_wash=type_of_car_wash,
        employees=employee,
        car_photo=ContentFile(car_photo_content, name=filename)
    )


@sync_to_async
def get_orders_count():
    return WashOrders.objects.count()


async def get_services_keyboard():
    services = await get_all_services()
    buttons = []

    service_emojis = ['🚗', '🚚', '🏍️', '🚌', '🚛', '🛻']

    for i, service in enumerate(services):
        emoji = service_emojis[i % len(service_emojis)]
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {service.name_services}",
            callback_data=f"service_{service.id}"
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_service_classes_keyboard(service_id):
    classes = await get_service_classes_by_service(service_id)
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
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {cls.name}{price_text}",
            callback_data=f"class_{cls.id}"
        )])

    buttons.append([InlineKeyboardButton(
        text="◀️ Назад к услугам",
        callback_data="back_to_services"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def get_employees_keyboard():
    employees = await get_all_employees()
    buttons = []

    worker_emojis = ['👨‍🔧', '👩‍🔧', '🧑‍🔧', '👨‍💼', '👩‍💼']

    for i, employee in enumerate(employees):
        emoji = worker_emojis[i % len(worker_emojis)]
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {str(employee)}",
            callback_data=f"employee_{employee.id}"
        )])

    buttons.append([InlineKeyboardButton(
        text="◀️ Назад к классам",
        callback_data="back_to_classes"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirmation_keyboard():
    buttons = [
        [InlineKeyboardButton(
            text="✨ Подтвердить заказ 👑",
            callback_data="confirm_order"
        )],
        [InlineKeyboardButton(
            text="❌ Отменить заказ",
            callback_data="cancel_order"
        )],
        [InlineKeyboardButton(
            text="◀️ Изменить мойщика",
            callback_data="back_to_employees"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_keyboard():
    buttons = [
        [InlineKeyboardButton(
            text="🚗 Создать заказ",
            callback_data="new_order"
        )],
        [InlineKeyboardButton(
            text="👤 Добавить пользователя",
            callback_data="add_user"
        )],
        [InlineKeyboardButton(
            text="📊 Список пользователей",
            callback_data="list_users"
        )],
        [InlineKeyboardButton(
            text="🗑️ Удалить пользователя",
            callback_data="delete_user"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("start"))
@access_required
async def start_command(message: Message, state: FSMContext):
    await state.clear()

    user_name = message.from_user.first_name or "Друг"
    user_id = message.from_user.id
    orders_count = await get_orders_count()

    await update_telegram_user(
        telegram_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )

    if await check_admin_access(user_id):
        all_users = await get_all_telegram_users()
        welcome_text = f"""
🌟 <b>Добро пожаловать в OltinWash!</b> 🌟

Привет, <b>{user_name}</b>! 👋
👑 <b>Режим администратора</b>

🔥 <b>Премиальная автомойка в Ташкенте</b>
✨ Профессиональный уход за вашим авто
💎 Высочайшее качество обслуживания

📊 Всего заказов выполнено: <b>{orders_count}</b>
👥 Авторизованных пользователей: <b>{len(all_users)}</b>

🚗 <b>Выберите действие:</b>
"""
        keyboard = get_admin_keyboard()
    else:
        welcome_text = f"""
🌟 <b>Добро пожаловать в OltinWash!</b> 🌟

Привет, <b>{user_name}</b>! 👋

🔥 <b>Премиальная автомойка в Ташкенте</b>
✨ Профессиональный уход за вашим авто
💎 Высочайшее качество обслуживания

📊 Всего заказов выполнено: <b>{orders_count}</b>

🚗 <b>Выберите услугу:</b>
"""
        keyboard = await get_services_keyboard()
        await state.set_state(OrderStates.choosing_service)

    await message.answer(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("users"))
async def admin_users_command(message: Message):
    if not await check_admin_access(message.from_user.id):
        await send_access_denied(message)
        return

    all_users = await get_all_telegram_users()

    users_text = f"""
👥 <b>СПИСОК TELEGRAM ПОЛЬЗОВАТЕЛЕЙ</b>

📊 <b>Всего пользователей:</b> {len(all_users)}

👤 <b>Пользователи:</b>
"""

    for i, user in enumerate(all_users, 1):
        admin_mark = " 👑" if user.is_admin else ""
        username_text = f" (@{user.username})" if user.username else ""
        users_text += f"<code>{i}. {user.telegram_id}</code> - {user.first_name}{username_text}{admin_mark}\n"

    await message.answer(users_text, parse_mode="HTML")


@router.message(AdminStates.adding_user)
async def add_user_process(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await message.answer("❌ Добавление пользователя отменено")
        await state.clear()
        return

    try:
        user_id = int(message.text.strip())

        if await is_user_authorized(user_id):
            await message.answer(f"⚠️ Пользователь {user_id} уже имеет доступ")
        else:
            user = await create_telegram_user(
                telegram_id=user_id,
                username=None,
                first_name=f"User_{user_id}",
                is_admin=False
            )

            if user:
                all_users = await get_all_telegram_users()
                success_text = f"""
✅ <b>ПОЛЬЗОВАТЕЛЬ ДОБАВЛЕН!</b>

👤 <b>ID:</b> <code>{user_id}</code>
🎉 <b>Теперь этот пользователь может использовать бота</b>
💾 <b>Профиль сохранен в базе данных</b>

👥 <b>Всего пользователей:</b> {len(all_users)}
"""
                await message.answer(success_text, parse_mode="HTML")
            else:
                await message.answer("❌ Ошибка при создании пользователя")

    except ValueError:
        await message.answer("❌ Неверный формат ID. Отправьте числовой ID пользователя")
        return

    await state.clear()


@router.message(AdminStates.deleting_user)
async def delete_user_process(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await message.answer("❌ Удаление пользователя отменено")
        await state.clear()
        return

    try:
        user_id = int(message.text.strip())

        if user_id == message.from_user.id:
            await message.answer("❌ Нельзя удалить самого себя")
            await state.clear()
            return

        if await delete_telegram_user(user_id):
            all_users = await get_all_telegram_users()
            success_text = f"""
✅ <b>ПОЛЬЗОВАТЕЛЬ УДАЛЕН!</b>

👤 <b>ID:</b> <code>{user_id}</code>
🗑️ <b>Пользователь больше не может использовать бота</b>

👥 <b>Всего пользователей:</b> {len(all_users)}
"""
            await message.answer(success_text, parse_mode="HTML")
        else:
            await message.answer(f"❌ Пользователь {user_id} не найден")

    except ValueError:
        await message.answer("❌ Неверный формат ID. Отправьте числовой ID пользователя")
        return

    await state.clear()


@router.message(F.photo, OrderStates.uploading_photo)
@access_required
async def upload_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)

    data = await state.get_data()
    price_text = f"{int(data['price']):,} UZS" if data['price'] else "Договорная"

    confirmation_text = f"""
✨ <b>ПОДТВЕРЖДЕНИЕ ЗАКАЗА</b> ✨

🎯 <b>ДЕТАЛИ ВАШЕГО ЗАКАЗА:</b>

🚗 <b>Услуга:</b> {data['service_name']}
⭐ <b>Класс:</b> {data['class_name']}
💎 <b>Стоимость:</b> {price_text}
👨‍🔧 <b>Мастер:</b> {data['employee_name']}
📸 <b>Фото автомобиля:</b> ✅ Загружено

💫 <b>Подтвердить заказ?</b>
"""

    await message.answer(
        confirmation_text,
        reply_markup=get_confirmation_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.confirming_order)


@router.message(OrderStates.uploading_photo)
@access_required
async def wrong_photo_format(message: Message):
    error_text = f"""
❌ <b>НУЖНО ФОТО АВТОМОБИЛЯ</b>

📸 <b>Пожалуйста, отправьте именно фотографию</b>
"""

    await message.answer(
        error_text,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "add_user")
async def add_user_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin_access(callback.from_user.id):
        await callback.answer("🚫 Только для администраторов", show_alert=True)
        return

    add_text = f"""
👤 <b>ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ</b>

📝 <b>Отправьте ID пользователя, которому хотите дать доступ</b>

💡 <b>Как получить ID:</b>
- Пользователь должен написать @userinfobot
- Или переслать сообщение от пользователя боту @userinfobot

❌ <b>Отправьте /cancel для отмены</b>
"""

    await callback.message.edit_text(add_text, parse_mode="HTML")
    await state.set_state(AdminStates.adding_user)


@router.callback_query(F.data == "delete_user")
async def delete_user_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin_access(callback.from_user.id):
        await callback.answer("🚫 Только для администраторов", show_alert=True)
        return

    delete_text = f"""
🗑️ <b>УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ</b>

📝 <b>Отправьте ID пользователя, которого хотите удалить</b>

⚠️ <b>Внимание! Это действие нельзя отменить</b>

❌ <b>Отправьте /cancel для отмены</b>
"""

    await callback.message.edit_text(delete_text, parse_mode="HTML")
    await state.set_state(AdminStates.deleting_user)


@router.callback_query(F.data == "list_users")
async def list_users(callback: CallbackQuery):
    if not await check_admin_access(callback.from_user.id):
        await callback.answer("🚫 Только для администраторов", show_alert=True)
        return

    all_users = await get_all_telegram_users()

    users_text = f"""
👥 <b>СПИСОК ПОЛЬЗОВАТЕЛЕЙ</b>

📊 <b>Всего:</b> {len(all_users)}

👤 <b>Пользователи:</b>
"""

    for i, user in enumerate(all_users, 1):
        admin_mark = " 👑" if user.is_admin else ""
        username_text = f" (@{user.username})" if user.username else ""
        users_text += f"<code>{i}. {user.telegram_id}</code> - {user.first_name}{username_text}{admin_mark}\n"

    back_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")]
    ])

    await callback.message.edit_text(
        users_text,
        reply_markup=back_button,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery, state: FSMContext):
    if not await check_admin_access(callback.from_user.id):
        await callback.answer("🚫 Только для администраторов", show_alert=True)
        return

    await state.clear()

    user_name = callback.from_user.first_name or "Администратор"
    orders_count = await get_orders_count()
    all_users = await get_all_telegram_users()

    welcome_text = f"""
🌟 <b>Добро пожаловать в OltinWash!</b> 🌟

Привет, <b>{user_name}</b>! 👋
👑 <b>Режим администратора</b>

🔥 <b>Премиальная автомойка в Ташкенте</b>
✨ Профессиональный уход за вашим авто
💎 Высочайшее качество обслуживания

📊 Всего заказов выполнено: <b>{orders_count}</b>
👥 Авторизованных пользователей: <b>{len(all_users)}</b>

🚗 <b>Выберите действие:</b>
"""

    await callback.message.edit_text(
        welcome_text,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "new_order")
@access_required
async def new_order(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        f"""
🏆 <b>ВЫБОР УСЛУГИ</b> 🏆

🔥 <b>Выберите тип мойки для вашего авто:</b>
""",
        reply_markup=await get_services_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.choosing_service)


@router.callback_query(F.data.startswith("service_"))
@access_required
async def choose_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[1])
    service = await get_service_by_id(service_id)

    await state.update_data(service_id=service_id, service_name=service.name_services)

    service_text = f"""
🎯 <b>ВЫБОР КЛАССА УСЛУГИ</b>

🚗 <b>Выбранная услуга:</b> {service.name_services}

💎 <b>Выберите класс обслуживания:</b>
"""

    await callback.message.edit_text(
        service_text,
        reply_markup=await get_service_classes_keyboard(service_id),
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.choosing_class)


@router.callback_query(F.data.startswith("class_"))
@access_required
async def choose_class(callback: CallbackQuery, state: FSMContext):
    class_id = int(callback.data.split("_")[1])
    service_class = await get_service_class_by_id(class_id)

    await state.update_data(
        class_id=class_id,
        class_name=service_class.name,
        price=float(service_class.price) if service_class.price else 0
    )

    price_text = f"{int(service_class.price):,} UZS" if service_class.price else "Договорная цена"

    class_text = f"""
👨‍🔧 <b>ВЫБОР МАСТЕРА</b>

⭐ <b>Выбранный класс:</b> {service_class.name}
💰 <b>Стоимость:</b> {price_text}

🔥 <b>Выберите мастера:</b>
"""

    await callback.message.edit_text(
        class_text,
        reply_markup=await get_employees_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.choosing_employee)


@router.callback_query(F.data.startswith("employee_"))
@access_required
async def choose_employee(callback: CallbackQuery, state: FSMContext):
    employee_id = int(callback.data.split("_")[1])
    employee = await get_employee_by_id(employee_id)

    await state.update_data(employee_id=employee_id, employee_name=str(employee))

    photo_text = f"""
📸 <b>ЗАГРУЗКА ФОТО АВТОМОБИЛЯ</b>

👨‍🔧 <b>Выбранный мастер:</b> {employee}

📷 <b>Пожалуйста, сделайте фото вашего автомобиля:</b>
"""

    await callback.message.edit_text(
        photo_text,
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.uploading_photo)


@router.callback_query(F.data == "confirm_order")
@access_required
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bot = callback.bot

    try:
        file_info = await bot.get_file(data['photo_file_id'])
        file_data = await bot.download_file(file_info.file_path)
        service_class = await get_service_class_by_id(data['class_id'])
        employee = await get_employee_by_id(data['employee_id'])
        filename = f"car_{callback.from_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        order = await create_wash_order(service_class, employee, file_data.getvalue(), filename)
        price_text = f"{int(order.negotiated_price):,} UZS" if order.negotiated_price else "Договорная"
        local_time = order.time_create.replace(tzinfo=timezone.utc).astimezone(TASHKENT_TZ)

        success_text = f"""
🎉 <b>ЗАКАЗ УСПЕШНО СОЗДАН!</b> 🎉

🆔 <b>Номер заказа:</b> #{order.id}

📋 <b>ДЕТАЛИ ЗАКАЗА:</b>
━━━━━━━━━━━━━━━━━━━
🚗 <b>Услуга:</b> {data['service_name']}
⭐ <b>Класс:</b> {data['class_name']}
💎 <b>Стоимость:</b> {price_text}
👨‍🔧 <b>Мастер:</b> {data['employee_name']}
📅 <b>Дата создания:</b> {local_time.strftime('%d.%m.%Y в %H:%M')}
━━━━━━━━━━━━━━━━━━━

✨ <b>Спасибо за выбор OltinWash!</b>
"""
        if await check_admin_access(callback.from_user.id):
            new_order_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🚗 Создать новый заказ",
                    callback_data="new_order"
                )],
                [InlineKeyboardButton(
                    text="👑 Админ меню",
                    callback_data="admin_menu"
                )]
            ])
        else:
            new_order_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="🚗 Создать новый заказ",
                    callback_data="new_order"
                )]
            ])

        await callback.message.edit_text(
            success_text,
            reply_markup=new_order_button,
            parse_mode="HTML"
        )

    except Exception as e:
        error_text = f"""
❌ <b>ОШИБКА ПРИ СОЗДАНИИ ЗАКАЗА</b>

🔧 <b>Техническая проблема:</b> {str(e)}

💡 Попробуйте еще раз
"""

        retry_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔄 Попробовать снова",
                callback_data="new_order"
            )]
        ])

        await callback.message.edit_text(
            error_text,
            reply_markup=retry_button,
            parse_mode="HTML"
        )

    await state.clear()


@router.callback_query(F.data == "back_to_services")
@access_required
async def back_to_services(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        f"""
🏆 <b>ВЫБОР УСЛУГИ</b> 🏆

🔥 <b>Выберите тип мойки для вашего авто:</b>
""",
        reply_markup=await get_services_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.choosing_service)


@router.callback_query(F.data == "back_to_classes")
@access_required
async def back_to_classes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    service_id = data.get('service_id')
    service_name = data.get('service_name')

    service_text = f"""
🎯 <b>ВЫБОР КЛАССА УСЛУГИ</b>

🚗 <b>Выбранная услуга:</b> {service_name}

💎 <b>Выберите класс обслуживания:</b>
"""

    await callback.message.edit_text(
        service_text,
        reply_markup=await get_service_classes_keyboard(service_id),
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.choosing_class)


@router.callback_query(F.data == "back_to_employees")
@access_required
async def back_to_employees(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    price_text = f"{int(data['price']):,} UZS" if data['price'] else "Договорная цена"

    class_text = f"""
👨‍🔧 <b>ВЫБОР МАСТЕРА</b>

⭐ <b>Выбранный класс:</b> {data['class_name']}
💰 <b>Стоимость:</b> {price_text}

🔥 <b>Выберите мастера:</b>
"""

    await callback.message.edit_text(
        class_text,
        reply_markup=await get_employees_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.choosing_employee)


@router.callback_query(F.data == "cancel_order")
@access_required
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    cancel_text = f"""
❌ <b>ЗАКАЗ ОТМЕНЕН</b>

🔥 <b>Создайте новый заказ когда будете готовы!</b>
"""

    restart_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Создать новый заказ", callback_data="new_order")]
    ])

    await callback.message.edit_text(
        cancel_text,
        reply_markup=restart_button,
        parse_mode="HTML"
    )
    await state.clear()


@router.message()
async def handle_unauthorized_messages(message: Message):
    user_id = message.from_user.id

    if await check_access(user_id):
        help_text = f"""
❓ <b>НЕИЗВЕСТНАЯ КОМАНДА</b>

💡 <b>Доступные команды:</b>
- /start - Главное меню
- /users - Список пользователей (для админов)

🚗 <b>Используйте /start для создания заказа</b>
"""
        await message.answer(help_text, parse_mode="HTML")
    else:
        await send_access_denied(message)
