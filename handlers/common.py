from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from keyboards import reply, inline
from database import Database
from config import ADMIN_IDS

router = Router()
db = Database()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    is_admin = message.from_user.id in ADMIN_IDS
    await message.answer(
        f"🌸 Добро пожаловать в цветочный магазин!\n\n"
        f"Здесь вы можете заказать свежие цветы с доставкой.\n"
        f"Используйте кнопки ниже для навигации:",
        reply_markup=reply.get_main_keyboard(is_admin)
    )

@router.message(F.text == "🌸 Каталог")
async def show_catalog(message: Message):
    """Показать каталог товаров"""
    categories = await db.get_categories()
    await message.answer(
        "Выберите категорию цветов:",
        reply_markup=inline.get_categories_keyboard(categories)
    )

@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    """Показать корзину"""
    cart_items = await db.get_cart(message.from_user.id)
    
    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста")
        return
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    text = "🛒 *Ваша корзина:*\n\n"
    for item in cart_items:
        text += f"• {item['name']} - {item['quantity']} шт. x {item['price']}₽ = {item['price'] * item['quantity']}₽\n"
    text += f"\n*Итого: {total}₽*"
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=inline.get_cart_keyboard(cart_items)
    )

@router.message(F.text == "ℹ️ О нас")
async def about_us(message: Message):
    """Информация о магазине"""
    await message.answer(
        "🌸 *О нашем магазине*\n\n"
        "Мы - семейный цветочный магазин с 10-летним опытом.\n"
        "• Только свежие цветы\n"
        "• Индивидуальный подход\n"
        "• Доставка по городу\n"
        "• Оригинальные букеты\n\n"
        "Работаем ежедневно с 9:00 до 21:00",
        parse_mode="Markdown"
    )

@router.message(F.text == "📞 Контакты")
async def contacts(message: Message):
    """Контактная информация"""
    await message.answer(
        "📞 *Наши контакты*\n\n"
        "Телефон: +7 (999) 123-45-67\n"
        "Email: flowers@shop.ru\n"
        "Адрес: ул. Цветочная, д. 1\n"
        "Instagram: @flower_shop\n"
        "Telegram: @flower_shop_bot",
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.delete()
    is_admin = callback.from_user.id in ADMIN_IDS
    await callback.message.answer(
        "Главное меню:",
        reply_markup=reply.get_main_keyboard(is_admin)
    )