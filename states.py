from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_for_product_name = State()
    waiting_for_product_description = State()
    waiting_for_product_price = State()
    waiting_for_product_image = State()
    waiting_for_product_category = State()
    waiting_for_edit_price = State()
    waiting_for_edit_stock = State()  # Для изменения количества
    waiting_for_stock_input = State()  # Для ввода нового количества

class CartStates(StatesGroup):
    waiting_for_quantity = State()
    waiting_for_checkout_phone = State()
    waiting_for_checkout_address = State()
    waiting_for_cart_quantity_input = State()