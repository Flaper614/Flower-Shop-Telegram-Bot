from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from database import Database
from keyboards import inline

router = Router()
db = Database()

@router.callback_query(F.data.startswith("category_"))
async def show_products_by_category(callback: CallbackQuery):
    """Показать товары категории"""
    category = callback.data.replace("category_", "")
    products = await db.get_products_by_category(category)
    
    if not products:
        await callback.answer("В этой категории пока нет товаров", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"Товары в категории '{category}':",
        reply_markup=inline.get_products_keyboard(products)
    )

@router.callback_query(F.data.startswith("page_"))
async def paginate_products(callback: CallbackQuery):
    """Пагинация товаров"""
    page = int(callback.data.replace("page_", ""))
    # Здесь нужно сохранять текущую категорию, для упрощения пока так
    await callback.answer()

@router.callback_query(F.data.startswith("product_"))
async def show_product_detail(callback: CallbackQuery):
    """Детальная страница товара"""
    product_id = int(callback.data.replace("product_", ""))
    product = await db.get_product(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    # Проверяем, есть ли товар в корзине
    cart_items = await db.get_cart(callback.from_user.id)
    in_cart = any(item['product_id'] == product_id for item in cart_items)
    
    stock_status = "✅ В наличии" if product['stock'] > 0 else "❌ Нет в наличии"
    
    text = f"*{product['name']}*\n\n"
    text += f"{product['description']}\n\n"
    text += f"💰 Цена: {product['price']}₽\n"
    text += f"📦 {stock_status}\n"
    text += f"📁 Категория: {product['category']}"
    
    if product['image_url']:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product['image_url'],
            caption=text,
            parse_mode="Markdown",
            reply_markup=inline.get_product_detail_keyboard(product_id, in_cart)
        )
    else:
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=inline.get_product_detail_keyboard(product_id, in_cart)
        )

@router.callback_query(F.data == "back_to_products")
async def back_to_products(callback: CallbackQuery):
    """Возврат к списку товаров"""
    # Здесь нужно вернуться к последней просмотренной категории
    # Для упрощения пока просто показываем каталог
    categories = await db.get_categories()
    await callback.message.edit_text(
        "Выберите категорию цветов:",
        reply_markup=inline.get_categories_keyboard(categories)
    )