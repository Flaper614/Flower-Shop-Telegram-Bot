from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import inline, reply
from states import AdminStates
from config import ADMIN_IDS
import json
import aiosqlite
from config import DB_NAME

router = Router()
db = Database()

# Фильтр для проверки админа
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(F.text == "⚙️ Админ панель")
async def admin_panel(message: Message):
    """Админ панель"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к админ панели")
        return
    
    await message.answer(
        "⚙️ *Админ панель*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=inline.get_admin_keyboard()
    )

@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    """Возврат в админ панель"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    await callback.message.edit_text(
        "⚙️ *Админ панель*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=inline.get_admin_keyboard()
    )

# ============= УПРАВЛЕНИЕ КОЛИЧЕСТВОМ ТОВАРОВ =============

@router.callback_query(F.data == "admin_list_products")
async def admin_list_products(callback: CallbackQuery):
    """Список товаров для админа с возможностью управления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    products = await db.get_all_products()
    if not products:
        await callback.message.edit_text(
            "Товаров пока нет",
            reply_markup=inline.get_admin_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "📦 *Управление товарами*\n\n"
        "Выберите товар для редактирования:",
        parse_mode="Markdown",
        reply_markup=inline.get_admin_product_list_keyboard(products)
    )

@router.callback_query(F.data.startswith("admin_page_"))
async def admin_paginate_products(callback: CallbackQuery):
    """Пагинация в админском списке товаров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    page = int(callback.data.replace("admin_page_", ""))
    products = await db.get_all_products()
    
    await callback.message.edit_text(
        "📦 *Управление товарами*\n\n"
        "Выберите товар для редактирования:",
        parse_mode="Markdown",
        reply_markup=inline.get_admin_product_list_keyboard(products, page)
    )

@router.callback_query(F.data.startswith("admin_product_"))
async def admin_product_details(callback: CallbackQuery):
    """Детальная информация о товаре для админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    product_id = int(callback.data.replace("admin_product_", ""))
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    text = f"📦 *Товар: {product['name']}*\n\n"
    text += f"📝 Описание: {product['description']}\n"
    text += f"💰 Цена: {product['price']}₽\n"
    text += f"📊 В наличии: {product['stock']} шт.\n"
    text += f"📁 Категория: {product['category']}\n"
    text += f"🆔 ID: {product['id']}\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=inline.get_admin_product_actions_keyboard(product_id)
    )

@router.callback_query(F.data.startswith("admin_edit_stock_"))
async def admin_edit_stock_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования количества товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    product_id = int(callback.data.replace("admin_edit_stock_", ""))
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    await state.update_data(product_id=product_id, product_name=product['name'])
    await callback.message.edit_text(
        f"Товар: *{product['name']}*\n"
        f"Текущее количество: {product['stock']} шт.\n\n"
        f"Введите новое количество товара в наличии (целое число):",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_for_stock_input)

@router.message(AdminStates.waiting_for_stock_input, F.text)
async def admin_process_stock_input(message: Message, state: FSMContext):
    """Обработка ввода нового количества"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой функции")
        await state.clear()
        return
    
    try:
        new_stock = int(message.text)
        if new_stock < 0:
            await message.answer("Количество не может быть отрицательным. Введите число >= 0:")
            return
        
        data = await state.get_data()
        product_id = data.get('product_id')
        product_name = data.get('product_name')
        
        if not product_id:
            await message.answer("Произошла ошибка. Попробуйте снова.")
            await state.clear()
            return
        
        # Обновляем количество в базе данных
        await db.update_product_stock(product_id, new_stock)
        
        await message.answer(
            f"✅ Количество товара *{product_name}* успешно изменено!\n"
            f"Новое количество: {new_stock} шт.",
            parse_mode="Markdown",
            reply_markup=reply.get_main_keyboard(True)
        )
        
        # Показываем обновленную информацию о товаре
        product = await db.get_product(product_id)
        if product:
            text = f"📦 *Товар: {product['name']}*\n\n"
            text += f"📝 Описание: {product['description']}\n"
            text += f"💰 Цена: {product['price']}₽\n"
            text += f"📊 В наличии: {product['stock']} шт.\n"
            text += f"📁 Категория: {product['category']}\n"
            
            await message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=inline.get_admin_product_actions_keyboard(product_id)
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer("Пожалуйста, введите целое число")

# ============= ДОБАВЛЕНИЕ ТОВАРОВ =============

@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    await callback.message.edit_text(
        "Введите название товара:",
        reply_markup=None
    )
    await state.set_state(AdminStates.waiting_for_product_name)

@router.message(AdminStates.waiting_for_product_name, F.text)
async def admin_add_product_name(message: Message, state: FSMContext):
    """Получение названия товара"""
    await state.update_data(name=message.text)
    await message.answer(
        "Введите описание товара:",
        reply_markup=reply.get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_product_description)

@router.message(AdminStates.waiting_for_product_description, F.text)
async def admin_add_product_description(message: Message, state: FSMContext):
    """Получение описания товара"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Добавление товара отменено",
            reply_markup=reply.get_main_keyboard(True)
        )
        return
    
    await state.update_data(description=message.text)
    await message.answer(
        "Введите цену товара (только число):",
        reply_markup=reply.get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_product_price)

@router.message(AdminStates.waiting_for_product_price, F.text)
async def admin_add_product_price(message: Message, state: FSMContext):
    """Получение цены товара"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Добавление товара отменено",
            reply_markup=reply.get_main_keyboard(True)
        )
        return
    
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError
        await state.update_data(price=price)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число (например: 1000)")
        return
    
    await message.answer(
        "Отправьте фото товара (или отправьте 'пропустить'):",
        reply_markup=reply.get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_product_image)

@router.message(AdminStates.waiting_for_product_image, F.photo)
async def admin_add_product_image(message: Message, state: FSMContext):
    """Получение фото товара"""
    photo = message.photo[-1]
    file_id = photo.file_id
    await state.update_data(image_url=file_id)
    
    categories = await db.get_categories()
    categories_text = "\n".join([f"• {cat}" for cat in categories])
    
    await message.answer(
        f"Введите категорию товара из списка:\n\n{categories_text}\n\n"
        f"Или введите количество товара в наличии (по умолчанию 0):",
        reply_markup=reply.get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_product_category)

@router.message(AdminStates.waiting_for_product_image, F.text)
async def admin_add_product_skip_image(message: Message, state: FSMContext):
    """Пропуск добавления фото"""
    if message.text.lower() == "пропустить":
        await state.update_data(image_url=None)
        
        categories = await db.get_categories()
        categories_text = "\n".join([f"• {cat}" for cat in categories])
        
        await message.answer(
            f"Введите категорию товара из списка:\n\n{categories_text}\n\n"
            f"Или введите количество товара в наличии (по умолчанию 0):",
            reply_markup=reply.get_cancel_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_product_category)
    elif message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Добавление товара отменено",
            reply_markup=reply.get_main_keyboard(True)
        )
    else:
        await message.answer("Пожалуйста, отправьте фото или напишите 'пропустить'")

@router.message(AdminStates.waiting_for_product_category, F.text)
async def admin_add_product_category(message: Message, state: FSMContext):
    """Получение категории и количества"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "Добавление товара отменено",
            reply_markup=reply.get_main_keyboard(True)
        )
        return
    
    # Проверяем, может быть пользователь ввел количество
    try:
        stock = int(message.text)
        # Если ввели число, значит это количество, а категорию спросим дальше
        await state.update_data(stock=stock)
        
        categories = await db.get_categories()
        categories_text = "\n".join([f"• {cat}" for cat in categories])
        
        await message.answer(
            f"Введите категорию товара из списка:\n\n{categories_text}",
            reply_markup=reply.get_cancel_keyboard()
        )
        return
    except ValueError:
        # Если не число, значит это категория
        category = message.text
        categories = await db.get_categories()
        
        if category not in categories:
            categories_text = "\n".join([f"• {cat}" for cat in categories])
            await message.answer(
                f"Категория '{category}' не найдена. Выберите из списка:\n\n{categories_text}",
                reply_markup=reply.get_cancel_keyboard()
            )
            return
        
        data = await state.get_data()
        stock = data.get('stock', 0)  # По умолчанию 0, если не указали
        
        product_id = await db.add_product(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            image_url=data.get('image_url'),
            category=category,
            stock=stock
        )
        
        await message.answer(
            f"✅ Товар успешно добавлен!\n"
            f"ID товара: {product_id}\n"
            f"Количество: {stock} шт.",
            reply_markup=reply.get_main_keyboard(True)
        )
        await state.clear()

# ============= ДРУГИЕ АДМИН ФУНКЦИИ =============

@router.callback_query(F.data.startswith("admin_edit_price_"))
async def admin_edit_price_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования цены товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    product_id = int(callback.data.replace("admin_edit_price_", ""))
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    await state.update_data(product_id=product_id, product_name=product['name'])
    await callback.message.edit_text(
        f"Товар: *{product['name']}*\n"
        f"Текущая цена: {product['price']}₽\n\n"
        f"Введите новую цену товара:",
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.waiting_for_edit_price)

@router.message(AdminStates.waiting_for_edit_price, F.text)
async def admin_process_price_input(message: Message, state: FSMContext):
    """Обработка ввода новой цены"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой функции")
        await state.clear()
        return
    
    try:
        new_price = float(message.text)
        if new_price <= 0:
            await message.answer("Цена должна быть положительным числом. Введите снова:")
            return
        
        data = await state.get_data()
        product_id = data.get('product_id')
        product_name = data.get('product_name')
        
        if not product_id:
            await message.answer("Произошла ошибка. Попробуйте снова.")
            await state.clear()
            return
        
        # Обновляем цену в базе данных
        await db.update_product_price(product_id, new_price)
        
        await message.answer(
            f"✅ Цена товара *{product_name}* успешно изменена!\n"
            f"Новая цена: {new_price}₽",
            parse_mode="Markdown",
            reply_markup=reply.get_main_keyboard(True)
        )
        
        # Показываем обновленную информацию о товаре
        product = await db.get_product(product_id)
        if product:
            text = f"📦 *Товар: {product['name']}*\n\n"
            text += f"📝 Описание: {product['description']}\n"
            text += f"💰 Цена: {product['price']}₽\n"
            text += f"📊 В наличии: {product['stock']} шт.\n"
            text += f"📁 Категория: {product['category']}\n"
            
            await message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=inline.get_admin_product_actions_keyboard(product_id)
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число (например: 1000)")

@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_product(callback: CallbackQuery, state: FSMContext):
    """Удаление товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    product_id = int(callback.data.replace("admin_delete_", ""))
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    # Спрашиваем подтверждение
    await state.update_data(product_id=product_id, product_name=product['name'])
    
    confirm_keyboard = InlineKeyboardBuilder()
    confirm_keyboard.add(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"admin_confirm_delete_{product_id}"),
        InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"admin_product_{product_id}")
    )
    confirm_keyboard.adjust(1)
    
    await callback.message.edit_text(
        f"❗️ *Подтверждение удаления*\n\n"
        f"Вы действительно хотите удалить товар:\n"
        f"*{product['name']}*?\n\n"
        f"Это действие нельзя отменить!",
        parse_mode="Markdown",
        reply_markup=confirm_keyboard.as_markup()
    )

@router.callback_query(F.data.startswith("admin_confirm_delete_"))
async def admin_confirm_delete(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    product_id = int(callback.data.replace("admin_confirm_delete_", ""))
    
    # Удаляем товар
    await db.delete_product(product_id)
    
    await callback.message.edit_text(
        f"✅ Товар успешно удален!",
        reply_markup=inline.get_admin_keyboard()
    )
    await state.clear()

@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):
    """Просмотр заказов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    async with aiosqlite.connect(DB_NAME) as db_conn:
        db_conn.row_factory = aiosqlite.Row
        async with db_conn.execute('''
            SELECT * FROM orders 
            WHERE status = 'pending' 
            ORDER BY created_at DESC
        ''') as cursor:
            orders = await cursor.fetchall()
    
    if not orders:
        await callback.message.edit_text(
            "Новых заказов нет",
            reply_markup=inline.get_admin_keyboard()
        )
        return
    
    text = "📋 *Новые заказы:*\n\n"
    for order in orders:
        items = json.loads(order['items'])
        items_text = "\n".join([f"• {item['name']} x{item['quantity']}" for item in items])
        
        text += f"*Заказ #{order['id']}*\n"
        text += f"Сумма: {order['total_price']}₽\n"
        text += f"Телефон: {order['phone']}\n"
        text += f"Адрес: {order['address']}\n"
        text += f"Товары:\n{items_text}\n"
        text += "—​—​—​—​—​—​—​—​—​—​—​—​—​—​—​—​—​—​—​—​—\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=inline.get_admin_keyboard()
    )