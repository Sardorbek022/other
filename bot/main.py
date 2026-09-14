import os
import sys
from pathlib import Path

from decouple import config
from asgiref.sync import sync_to_async

# ==========================================================
# Django muhitini yuklash
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

# Django modellari
from shop.models import Category, Product, Order

# ==========================================================
# Aiogram
# ==========================================================

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


BOT_TOKEN = config("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ==========================================================
# FSM - Buyurtma holatlari
# ==========================================================

class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


# ==========================================================
# Django ORM
# ==========================================================

@sync_to_async
def get_all_categories():
    return list(Category.objects.all())


@sync_to_async
def get_products_by_category(category_id):
    return list(
        Product.objects.filter(
            category_id=category_id,
            is_available=True
        )
    )


@sync_to_async
def get_product_by_id(product_id):
    return Product.objects.filter(id=product_id).first()


@sync_to_async
def get_product_category_id(product):
    return product.category_id


@sync_to_async
def create_order(customer_name, phone_number, product_id):
    return Order.objects.create(
        customer_name=customer_name,
        phone_number=phone_number,
        product_id=product_id,
        quantity=1
    )


# ==========================================================
# /start
# ==========================================================

@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):

    await state.clear()

    categories = await get_all_categories()

    if not categories:
        await message.answer(
            "Hozircha do'konda kategoriyalar mavjud emas."
        )
        return

    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.button(
            text=category.name,
            callback_data=f"category_{category.id}"
        )

    builder.adjust(2)

    await message.answer(
        text=(
            f"Salom, {message.from_user.full_name}!\n"
            f"Sardor Store botiga xush kelibsiz.\n\n"
            f"Kategoriyalardan birini tanlang:"
        ),
        reply_markup=builder.as_markup()
    )


# ==========================================================
# Kategoriya
# ==========================================================

@dp.callback_query(F.data.startswith("category_"))
async def show_products(call: types.CallbackQuery):

    category_id = int(call.data.split("_")[1])

    products = await get_products_by_category(category_id)

    builder = InlineKeyboardBuilder()

    if not products:

        builder.button(
            text="⬅️ Orqaga",
            callback_data="back_to_categories"
        )

        try:
            await call.message.edit_text(
                "Bu kategoriyada hozircha mahsulot yo'q.",
                reply_markup=builder.as_markup()
            )
        except Exception:
            await call.message.answer(
                "Bu kategoriyada hozircha mahsulot yo'q.",
                reply_markup=builder.as_markup()
            )

        await call.answer()
        return

    for product in products:

        builder.button(
            text=f"{product.name} - {product.price} so'm",
            callback_data=f"product_{product.id}"
        )

    builder.button(
        text="⬅️ Bosh menyu",
        callback_data="back_to_categories"
    )

    builder.adjust(1)

    try:
        await call.message.edit_text(
            "Mahsulotni tanlang:",
            reply_markup=builder.as_markup()
        )
    except Exception:
        await call.message.answer(
            "Mahsulotni tanlang:",
            reply_markup=builder.as_markup()
        )

    await call.answer()


# ==========================================================
# Mahsulot
# ==========================================================

@dp.callback_query(F.data.startswith("product_"))
async def show_product_detail(call: types.CallbackQuery):

    product_id = int(call.data.split("_")[1])

    product = await get_product_by_id(product_id)

    if not product:
        await call.answer("Mahsulot topilmadi.")
        return

    category_id = await get_product_category_id(product)

    caption = (
        f"🛍 <b>{product.name}</b>\n\n"
        f"📝 Tavsif: {product.description or 'Yozilmagan'}\n"
        f"💰 Narxi: {product.price} so'm\n"
        f"📦 Omborda: {product.stock} ta bor"
    )

    builder = InlineKeyboardBuilder()

    builder.button(
        text="🛒 Sotib olish",
        callback_data=f"buy_{product.id}"
    )

    builder.button(
        text="⬅️ Orqaga",
        callback_data=f"category_{category_id}"
    )

    builder.adjust(1)

    try:
        await call.message.delete()
    except Exception:
        pass

    if product.image:

        try:
            photo = types.FSInputFile(product.image.path)

            await call.message.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )

        except Exception:

            await call.message.answer(
                text=caption,
                reply_markup=builder.as_markup(),
                parse_mode="HTML"
            )

    else:

        await call.message.answer(
            text=caption,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    await call.answer()


# ==========================================================
# Bosh menyu
# ==========================================================

@dp.callback_query(F.data == "back_to_categories")
async def back_to_categories(call: types.CallbackQuery):

    categories = await get_all_categories()

    builder = InlineKeyboardBuilder()

    for category in categories:

        builder.button(
            text=category.name,
            callback_data=f"category_{category.id}"
        )

    builder.adjust(2)

    try:

        await call.message.edit_text(
            "Kategoriyalardan birini tanlang:",
            reply_markup=builder.as_markup()
        )

    except Exception:

        await call.message.answer(
            "Kategoriyalardan birini tanlang:",
            reply_markup=builder.as_markup()
        )

    await call.answer()


# ==========================================================
# Sotib olish
# ==========================================================

@dp.callback_query(F.data.startswith("buy_"))
async def start_order(
    call: types.CallbackQuery,
    state: FSMContext
):

    product_id = int(call.data.split("_")[1])

    product = await get_product_by_id(product_id)

    if not product:
        await call.answer("Mahsulot topilmadi.")
        return

    if not product.is_available:
        await call.answer("Bu mahsulot hozir mavjud emas.")
        return

    if product.stock <= 0:
        await call.answer("Bu mahsulot omborda qolmagan.")
        return

    await state.update_data(
        chosen_product_id=product_id
    )

    await state.set_state(
        OrderState.waiting_for_name
    )

    await call.message.answer(
        "Iltimos, buyurtma uchun ism familiyangizni kiriting:"
    )

    await call.answer()


# ==========================================================
# Ism
# ==========================================================

@dp.message(OrderState.waiting_for_name)
async def process_name(
    message: types.Message,
    state: FSMContext
):

    if not message.text:

        await message.answer(
            "Iltimos, ism familiyangizni matn ko'rinishida yuboring."
        )

        return

    await state.update_data(
        customer_name=message.text.strip()
    )

    await state.set_state(
        OrderState.waiting_for_phone
    )

    phone_builder = ReplyKeyboardBuilder()

    phone_builder.button(
        text="📱 Telefon raqamingizni yuborish",
        request_contact=True
    )

    await message.answer(
        "Raqamingizni kiriting yoki quyidagi tugma orqali yuboring:",
        reply_markup=phone_builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )


# ==========================================================
# Telefon
# ==========================================================

@dp.message(OrderState.waiting_for_phone)
async def process_phone(
    message: types.Message,
    state: FSMContext
):

    if message.contact:

        phone_number = message.contact.phone_number

    elif message.text:

        phone_number = message.text.strip()

    else:

        await message.answer(
            "Iltimos, telefon raqamingizni yuboring."
        )

        return

    user_data = await state.get_data()

    customer_name = user_data.get("customer_name")
    product_id = user_data.get("chosen_product_id")

    if not customer_name or not product_id:

        await state.clear()

        await message.answer(
            "Buyurtma ma'lumotlari topilmadi. Iltimos, qaytadan urinib ko'ring.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        return

    product = await get_product_by_id(product_id)

    if not product:

        await state.clear()

        await message.answer(
            "Mahsulot topilmadi.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        return

    if not product.is_available or product.stock <= 0:

        await state.clear()

        await message.answer(
            "Kechirasiz, bu mahsulot hozir mavjud emas.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        return

    new_order = await create_order(
        customer_name,
        phone_number,
        product_id
    )

    back_builder = InlineKeyboardBuilder()

    back_builder.button(
        text="🛍 Qaytadan xarid qilish",
        callback_data="back_to_categories"
    )

    await message.answer(
        text="Raqam qabul qilindi. Rahmat!",
        reply_markup=types.ReplyKeyboardRemove()
    )

    await message.answer(
        text=(
            f"🎉 Buyurtmangiz muvaffaqiyatli qabul qilindi.\n\n"
            f"🔢 Buyurtma raqami: #{new_order.id}\n"
            f"🛍 Mahsulot: {product.name}\n"
            f"💰 Narxi: {product.price} so'm\n\n"
            f"Tez orada operatorlarimiz siz bilan bog'lanishadi.\n\n"
            f"Yana boshqa mahsulotlarni ko'rishni xohlaysizmi?"
        ),
        reply_markup=back_builder.as_markup()
    )

    await state.clear()
