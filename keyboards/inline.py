from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Any

def get_categories_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """Клавиатура с категориями товаров (без комнатных растений)"""
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.add(InlineKeyboardButton(
            text=category,
            callback_data=f"category_{category}"
        ))
    builder.add(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_menu"
    ))
    builder.adjust(2)
    return builder.as_markup()

def get_products_keyboard(products: List[Dict[str, Any]], page: int = 0, 
                         products_per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура с товарами постранично"""
    builder = InlineKeyboardBuilder()
    
    start = page * products_per_page
    end = start + products_per_page
    current_products = products[start:end]
    
    for product in current_products:
        stock_status = "✅" if product['stock'] > 0 else "❌"
        builder.add(InlineKeyboardButton(
            text=f"{stock_status} {product['name']} - {product['price']}₽",
            callback_data=f"product_{product['id']}"
        ))
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"page_{page-1}"
        ))
    if end < len(products):
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ Вперед",
            callback_data=f"page_{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(
        text="🛒 Корзина",
        callback_data="view_cart"
    ))
    builder.row(InlineKeyboardButton(
        text="🔙 В меню",
        callback_data="back_to_menu"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_product_detail_keyboard(product_id: int, in_cart: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для детальной страницы товара"""
    builder = InlineKeyboardBuilder()
    
    builder.add(InlineKeyboardButton(
        text="🛒 Добавить в корзину",
        callback_data=f"add_to_cart_{product_id}"
    ))
    
    if in_cart:
        builder.add(InlineKeyboardButton(
            text="📝 Изменить количество",
            callback_data=f"change_quantity_{product_id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="🔙 К товарам",
        callback_data="back_to_products"
    ))
    builder.add(InlineKeyboardButton(
        text="🛍 В корзину",
        callback_data="view_cart"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_cart_keyboard(items: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Клавиатура корзины с возможностью изменения количества"""
    builder = InlineKeyboardBuilder()
    
    for item in items:
        # Для каждого товара добавляем кнопки управления количеством
        item_row = InlineKeyboardBuilder()
        item_row.add(InlineKeyboardButton(
            text=f"➖ {item['name']} ({item['quantity']} шт.) ➕",
            callback_data=f"adjust_{item['product_id']}"
        ))
        builder.row(*item_row.buttons)
        
        # Кнопки для изменения количества
        adjust_row = InlineKeyboardBuilder()
        adjust_row.add(InlineKeyboardButton(
            text="−1",
            callback_data=f"dec_{item['product_id']}"
        ))
        adjust_row.add(InlineKeyboardButton(
            text="✏️ Ввести",
            callback_data=f"input_qty_{item['product_id']}"
        ))
        adjust_row.add(InlineKeyboardButton(
            text="+1",
            callback_data=f"inc_{item['product_id']}"
        ))
        adjust_row.add(InlineKeyboardButton(
            text="❌ Удалить",
            callback_data=f"remove_{item['product_id']}"
        ))
        builder.row(*adjust_row.buttons)
    
    if items:
        builder.row(InlineKeyboardButton(
            text="✅ Оформить заказ",
            callback_data="checkout"
        ))
        builder.row(InlineKeyboardButton(
            text="🗑 Очистить корзину",
            callback_data="clear_cart"
        ))
    
    builder.row(InlineKeyboardButton(
        text="🔙 Продолжить покупки",
        callback_data="back_to_products"
    ))
    
    return builder.as_markup()

def get_quantity_edit_keyboard(product_id: int, current_quantity: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура для редактирования количества"""
    builder = InlineKeyboardBuilder()
    
    # Быстрый выбор количества
    for i in range(1, 6):
        if i == current_quantity:
            builder.add(InlineKeyboardButton(
                text=f"✅ {i}",
                callback_data=f"set_qty_{product_id}_{i}"
            ))
        else:
            builder.add(InlineKeyboardButton(
                text=str(i),
                callback_data=f"set_qty_{product_id}_{i}"
            ))
    
    builder.adjust(5)
    builder.row(InlineKeyboardButton(
        text="✏️ Ввести свое число",
        callback_data=f"input_custom_{product_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="🔙 В корзину",
        callback_data="view_cart"
    ))
    
    return builder.as_markup()

def get_admin_product_list_keyboard(products: List[Dict[str, Any]], page: int = 0, 
                                   products_per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура со списком товаров для админа"""
    builder = InlineKeyboardBuilder()
    
    start = page * products_per_page
    end = start + products_per_page
    current_products = products[start:end]
    
    for product in current_products:
        stock_emoji = "✅" if product['stock'] > 0 else "❌"
        builder.add(InlineKeyboardButton(
            text=f"{stock_emoji} {product['name']} (в наличии: {product['stock']})",
            callback_data=f"admin_product_{product['id']}"
        ))
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"admin_page_{page-1}"
        ))
    if end < len(products):
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ Вперед",
            callback_data=f"admin_page_{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    builder.row(InlineKeyboardButton(
        text="🔙 В админ панель",
        callback_data="back_to_admin"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_admin_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с товаром для админа"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📦 Изменить количество", callback_data=f"admin_edit_stock_{product_id}"),
        InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"admin_edit_price_{product_id}"),
        InlineKeyboardButton(text="🗑 Удалить товар", callback_data=f"admin_delete_{product_id}"),
        InlineKeyboardButton(text="🔙 К списку товаров", callback_data="admin_list_products")
    )
    builder.adjust(1)
    return builder.as_markup()

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админская клавиатура"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product"),
        InlineKeyboardButton(text="📦 Список товаров", callback_data="admin_list_products"),
        InlineKeyboardButton(text="📊 Заказы", callback_data="admin_orders"),
        InlineKeyboardButton(text="📈 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")
    )
    builder.adjust(2)
    return builder.as_markup()

def get_quantity_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для выбора количества при добавлении"""
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(
            text=str(i),
            callback_data=f"qty_{product_id}_{i}"
        ))
    builder.adjust(5)
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=f"product_{product_id}"
    ))
    return builder.as_markup()