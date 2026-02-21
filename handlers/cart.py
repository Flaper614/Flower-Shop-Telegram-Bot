from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import inline, reply
from states import CartStates

router = Router()
db = Database()

@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    """Добавление товара в корзину"""
    await callback.answer()  # Сразу отвечаем на callback, чтобы кнопка не "светилась"
    
    product_id = int(callback.data.replace("add_to_cart_", ""))
    product = await db.get_product(product_id)
    
    if not product or product['stock'] <= 0:
        await callback.answer("Товар недоступен для заказа", show_alert=True)
        return
    
    await state.update_data(product_id=product_id)
    
    # Проверяем тип сообщения и соответствующим образом редактируем
    if callback.message.photo:
        # Если есть фото, редактируем caption
        await callback.message.edit_caption(
            caption=f"Выберите количество для товара '{product['name']}':",
            reply_markup=inline.get_quantity_keyboard(product_id)
        )
    else:
        # Если нет фото, редактируем текст
        await callback.message.edit_text(
            text=f"Выберите количество для товара '{product['name']}':",
            reply_markup=inline.get_quantity_keyboard(product_id)
        )

@router.callback_query(F.data.startswith("qty_"))
async def process_quantity(callback: CallbackQuery, state: FSMContext):
    """Обработка выбранного количества при добавлении"""
    await callback.answer()  # Сразу отвечаем на callback
    
    _, product_id, quantity = callback.data.split("_")
    product_id = int(product_id)
    quantity = int(quantity)
    
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    if product['stock'] < quantity:
        await callback.answer(f"Доступно только {product['stock']} шт.", show_alert=True)
        return
    
    # Добавляем в корзину
    await db.add_to_cart(callback.from_user.id, product_id, quantity)
    await callback.answer(f"✅ Товар добавлен в корзину! ({quantity} шт.)", show_alert=False)
    
    # Проверяем, есть ли товар в корзине
    cart_items = await db.get_cart(callback.from_user.id)
    in_cart = any(item['product_id'] == product_id for item in cart_items)
    
    stock_status = "✅ В наличии" if product['stock'] > 0 else "❌ Нет в наличии"
    
    text = f"*{product['name']}*\n\n"
    text += f"{product['description']}\n\n"
    text += f"💰 Цена: {product['price']}₽\n"
    text += f"📦 {stock_status}\n"
    text += f"📁 Категория: {product['category']}"
    
    # Возвращаемся к детальной странице товара
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=text,
                parse_mode="Markdown",
                reply_markup=inline.get_product_detail_keyboard(product_id, in_cart)
            )
        else:
            await callback.message.edit_text(
                text=text,
                parse_mode="Markdown",
                reply_markup=inline.get_product_detail_keyboard(product_id, in_cart)
            )
    except Exception as e:
        # Если не удалось отредактировать, отправляем новое сообщение
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="Markdown",
            reply_markup=inline.get_product_detail_keyboard(product_id, in_cart)
        )

@router.callback_query(F.data.startswith("inc_"))
async def increase_quantity(callback: CallbackQuery):
    """Увеличение количества товара на 1"""
    await callback.answer()
    
    product_id = int(callback.data.replace("inc_", ""))
    cart_items = await db.get_cart(callback.from_user.id)
    
    current_item = next((item for item in cart_items if item['product_id'] == product_id), None)
    if not current_item:
        await callback.answer("Товар не найден в корзине", show_alert=True)
        return
    
    product = await db.get_product(product_id)
    if not product or product['stock'] < current_item['quantity'] + 1:
        await callback.answer("Недостаточно товара в наличии", show_alert=True)
        return
    
    await db.update_cart_quantity(callback.from_user.id, product_id, current_item['quantity'] + 1)
    await callback.answer("➕ Количество увеличено")
    
    await show_updated_cart(callback)

@router.callback_query(F.data.startswith("dec_"))
async def decrease_quantity(callback: CallbackQuery):
    """Уменьшение количества товара на 1"""
    await callback.answer()
    
    product_id = int(callback.data.replace("dec_", ""))
    cart_items = await db.get_cart(callback.from_user.id)
    
    current_item = next((item for item in cart_items if item['product_id'] == product_id), None)
    if not current_item:
        await callback.answer("Товар не найден в корзине", show_alert=True)
        return
    
    new_quantity = current_item['quantity'] - 1
    await db.update_cart_quantity(callback.from_user.id, product_id, new_quantity)
    
    if new_quantity <= 0:
        await callback.answer("🗑 Товар удален из корзины")
    else:
        await callback.answer("➖ Количество уменьшено")
    
    await show_updated_cart(callback)

@router.callback_query(F.data.startswith("adjust_"))
async def adjust_quantity_menu(callback: CallbackQuery, state: FSMContext):
    """Открыть меню настройки количества"""
    await callback.answer()
    
    product_id = int(callback.data.replace("adjust_", ""))
    cart_items = await db.get_cart(callback.from_user.id)
    
    current_item = next((item for item in cart_items if item['product_id'] == product_id), None)
    if not current_item:
        await callback.answer("Товар не найден в корзине", show_alert=True)
        return
    
    await callback.message.edit_text(
        text=f"Товар: *{current_item['name']}*\n"
             f"Текущее количество: {current_item['quantity']} шт.\n"
             f"Цена за шт: {current_item['price']}₽\n\n"
             f"Выберите новое количество или введите свое число:",
        parse_mode="Markdown",
        reply_markup=inline.get_quantity_edit_keyboard(product_id, current_item['quantity'])
    )

@router.callback_query(F.data.startswith("set_qty_"))
async def set_quantity(callback: CallbackQuery):
    """Установка конкретного количества"""
    await callback.answer()
    
    _, product_id, quantity = callback.data.split("_")
    product_id = int(product_id)
    quantity = int(quantity)
    
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    if product['stock'] < quantity:
        await callback.answer(f"Доступно только {product['stock']} шт.", show_alert=True)
        return
    
    await db.update_cart_quantity(callback.from_user.id, product_id, quantity)
    await callback.answer(f"✅ Количество изменено на {quantity}")
    
    await show_updated_cart(callback)

@router.callback_query(F.data.startswith("input_custom_"))
async def input_custom_quantity(callback: CallbackQuery, state: FSMContext):
    """Запрос на ввод своего числа"""
    await callback.answer()
    
    product_id = int(callback.data.replace("input_custom_", ""))
    product = await db.get_product(product_id)
    
    await state.update_data(editing_product_id=product_id)
    await callback.message.edit_text(
        text=f"Товар: *{product['name']}*\n"
             f"Доступно: {product['stock']} шт.\n\n"
             f"Введите желаемое количество (целое число):",
        parse_mode="Markdown"
    )
    await state.set_state(CartStates.waiting_for_cart_quantity_input)

@router.callback_query(F.data.startswith("input_qty_"))
async def input_quantity_from_cart(callback: CallbackQuery, state: FSMContext):
    """Запрос на ввод количества из корзины"""
    await callback.answer()
    
    product_id = int(callback.data.replace("input_qty_", ""))
    product = await db.get_product(product_id)
    
    await state.update_data(editing_product_id=product_id)
    await callback.message.edit_text(
        text=f"Товар: *{product['name']}*\n"
             f"Доступно: {product['stock']} шт.\n\n"
             f"Введите желаемое количество (целое число):",
        parse_mode="Markdown"
    )
    await state.set_state(CartStates.waiting_for_cart_quantity_input)

@router.message(CartStates.waiting_for_cart_quantity_input, F.text)
async def process_custom_quantity(message: Message, state: FSMContext):
    """Обработка введенного пользователем количества"""
    try:
        quantity = int(message.text)
        if quantity <= 0:
            await message.answer("❌ Пожалуйста, введите положительное число")
            return
        
        data = await state.get_data()
        product_id = data.get('editing_product_id')
        
        if not product_id:
            await message.answer("❌ Произошла ошибка. Попробуйте снова.")
            await state.clear()
            return
        
        product = await db.get_product(product_id)
        if not product:
            await message.answer("❌ Товар не найден")
            await state.clear()
            return
        
        if product['stock'] < quantity:
            await message.answer(f"❌ Доступно только {product['stock']} шт. Введите другое число:")
            return
        
        await db.update_cart_quantity(message.from_user.id, product_id, quantity)
        await message.answer(f"✅ Количество изменено на {quantity}")
        
        # Показываем обновленную корзину
        cart_items = await db.get_cart(message.from_user.id)
        if not cart_items:
            await message.answer("🛒 Ваша корзина пуста")
        else:
            total = sum(item['price'] * item['quantity'] for item in cart_items)
            text = "🛒 *Ваша корзина:*\n\n"
            for item in cart_items:
                text += f"• *{item['name']}*\n"
                text += f"  {item['quantity']} шт. x {item['price']}₽ = {item['price'] * item['quantity']}₽\n"
            text += f"\n*Итого: {total}₽*"
            
            await message.answer(
                text=text,
                parse_mode="Markdown",
                reply_markup=inline.get_cart_keyboard(cart_items)
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число")

@router.callback_query(F.data.startswith("remove_"))
async def remove_from_cart(callback: CallbackQuery):
    """Удаление товара из корзины"""
    await callback.answer()
    
    product_id = int(callback.data.replace("remove_", ""))
    await db.remove_from_cart(callback.from_user.id, product_id)
    await callback.answer("🗑 Товар удален из корзины")
    
    await show_updated_cart(callback)

@router.callback_query(F.data == "view_cart")
async def view_cart(callback: CallbackQuery):
    """Просмотр корзины"""
    await callback.answer()
    await show_updated_cart(callback)

async def show_updated_cart(callback: CallbackQuery):
    """Вспомогательная функция для отображения обновленной корзины"""
    cart_items = await db.get_cart(callback.from_user.id)
    
    if not cart_items:
        await callback.message.edit_text(
            text="🛒 Ваша корзина пуста",
            reply_markup=None
        )
        return
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    text = "🛒 *Ваша корзина:*\n\n"
    for item in cart_items:
        text += f"• *{item['name']}*\n"
        text += f"  {item['quantity']} шт. x {item['price']}₽ = {item['price'] * item['quantity']}₽\n"
    text += f"\n*Итого: {total}₽*"
    
    await callback.message.edit_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=inline.get_cart_keyboard(cart_items)
    )

@router.callback_query(F.data == "clear_cart")
async def clear_cart(callback: CallbackQuery):
    """Очистка корзины"""
    await callback.answer()
    
    await db.clear_cart(callback.from_user.id)
    await callback.answer("🗑 Корзина очищена")
    await callback.message.edit_text(
        text="🛒 Ваша корзина пуста",
        reply_markup=None
    )

# ⚠️ ВНИМАНИЕ: Здесь должен быть ваш код оформления заказа
# ===========================================================
# @router.callback_query(F.data == "checkout")
# async def checkout_start(callback: CallbackQuery, state: FSMContext):
#     """Начало оформления заказа"""
#     # Здесь сделайте свою систему оформления заказа
#     # Например: сбор контактных данных, адреса, способа оплаты и т.д.
#     await callback.answer("Функция оформления заказа в разработке", show_alert=True)
# ===========================================================

# Обработчик для текстовых сообщений во время ожидания ввода количества
@router.message(CartStates.waiting_for_cart_quantity_input)
async def handle_invalid_quantity_input(message: Message):
    """Обработка некорректного ввода при ожидании количества"""
    await message.answer("❌ Пожалуйста, введите целое число")