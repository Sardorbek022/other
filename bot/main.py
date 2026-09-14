import os
import sys
import asyncio
from pathlib import Path
from decouple import config
from asgiref.sync import sync_to_async

# ==========================================================
# 1. Django muhitini asinxron bot ichiga yuklash
# ==========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

# Django modellarini import qilamiz
from shop.models import Category, Product, Order

# Aiogram 3.x va FSM (Finite State Machine) tizimi
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

BOT_TOKEN = config('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==========================================================
# FSM: Buyurtma berish bosqichlari (States)
# ==========================================================
class OrderState(StatesGroup):
    waiting_for_name = State()   # Ismini kutish bosqichi
    waiting_for_phone = State()  # Telefonini kutish bosqichi

# ==========================================================
# 2. Django ORM so'rovlarini bot uchun asinxron qilish
# ==========================================================
@sync_to_async
def get_all_categories():
    return list(Category.objects.all())

@sync_to_async
def get_products_by_category(category_id):
    return list(Product.objects.filter(category_id=category_id, is_available=True))

@sync_to_async
def get_product_by_id(product_id):
    return Product.objects.filter(id=product_id).first()

@sync_to_async
def create_order(customer_name, phone_number, product_id):
    # Djangodagi ideal save() mantiqi narxni o'zi avtomat muhrlaydi
    return Order.objects.create(
        customer_name=customer_name,
        phone_number=phone_number,
        product_id=product_id,
        quantity=1
    )

# ==========================================================
# 3. Bot Handlers (Kategoriyalar va Mahsulotlar zanjiri)
# ==========================================================

# Xaridor /start berganda bazadan hamma kategoriyalarni chizadi
@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    await state.clear() # Har safar start bosilganda eski holatlar tozalanadi
    categories = await get_all_categories()
    
    if not categories:
        await message.answer("Hozircha do'konda kategoriyalar mavjud emas.")
        return

    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category.name, callback_data=f"category_{category.id}")
    builder.adjust(2)

    await message.answer(
        text=f"Salom, {message.from_user.full_name}!\nSardor Store botiga xush kelibsiz.\n\nKategoriyalardan birini tanlang:",
        reply_markup=builder.as_markup()
    )

# Kategoriya tugmasi bosilganda unga tegishli mahsulotlarni chiqaradi
@dp.callback_query(F.data.startswith("category_"))
async def show_products(call: types.CallbackQuery):
    category_id = int(call.data.split("_")[1])
    products = await get_products_by_category(category_id)
    
    builder = InlineKeyboardBuilder()
    if not products:
        builder.button(text="⬅️ Orqaga", callback_data="back_to_categories")
        try:
            await call.message.edit_text("Bu kategoriyada hozircha mahsulot yo'q.", reply_markup=builder.as_markup())
        except Exception:
            await call.message.delete()
            await call.message.answer("Bu kategoriyada hozircha mahsulot yo'q.", reply_markup=builder.as_markup())
        return

    for product in products:
        builder.button(text=f"{product.name} - {product.price} so'm", callback_data=f"product_{product.id}")
    
    builder.button(text="⬅️ Bosh menyu", callback_data="back_to_categories")
    builder.adjust(1)

    try:
        await call.message.edit_text("Mahsulotni tanlang:", reply_markup=builder.as_markup())
    except Exception:
        await call.message.delete()
        await call.message.answer("Mahsulotni tanlang:", reply_markup=builder.as_markup())

# Mahsulot bosilganda rasm, narx, tavsif va "Sotib olish" tugmasini chiqaradi
@dp.callback_query(F.data.startswith("product_"))
async def show_product_detail(call: types.CallbackQuery):
    product_id = int(call.data.split("_")[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await call.answer("Mahsulot topilmadi.")
        return

    # Sinxronlik xatosini oldini olish uchun Foreign Keyni asinxron olamiz
    category_id = await sync_to_async(lambda: product.category.id)()

    caption = (
        f"🛍 <b>{product.name}</b>\n\n"
        f"📝 Tavsif: {product.description or 'Yozilmagan'}\n"
        f"💰 Narxi: {product.price} so'm\n"
        f"📦 Omborda: {product.stock} ta bor\n"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Sotib olish", callback_data=f"buy_{product.id}")
    builder.button(text="⬅️ Orqaga", callback_data=f"category_{category_id}")
    builder.adjust(1)

    # Matndan rasmga o'tganda Bad Request xatosi bermasligi uchun eski xabarni o'chiramiz
    await call.message.delete()

    if product.image:
        photo = types.FSInputFile(product.image.path)
        await call.message.answer_photo(photo=photo, caption=caption, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await call.message.answer(text=caption, reply_markup=builder.as_markup(), parse_mode="HTML")

# Bosh menyuga orqaga qaytish mantiqi
@dp.callback_query(F.data == "back_to_categories")
async def back_to_categories(call: types.CallbackQuery):
    categories = await get_all_categories()
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(text=category.name, callback_data=f"category_{category.id}")
    builder.adjust(2)
    
    try:
        await call.message.edit_text("Kategoriyalardan birini tanlang:", reply_markup=builder.as_markup())
    except Exception:
        await call.message.delete()
        await call.message.answer("Kategoriyalardan birini tanlang:", reply_markup=builder.as_markup())

# ==========================================================
# 4. TEZKOR BUYURTMA BERISH MANTIQI (FSM)
# ==========================================================

# Xaridor "Sotib olish" tugmasini bosganda
@dp.callback_query(F.data.startswith("buy_"))
async def start_order(call: types.CallbackQuery, state: FSMContext):
    product_id = int(call.data.split("_")[1])
    
    # Mahsulot ID-sini xotiraga saqlaymiz va holatni "Ism kutish"ga o'tkazamiz
    await state.update_data(chosen_product_id=product_id)
    await state.set_state(OrderState.waiting_for_name)
    
    await call.message.answer("Iltimos, buyurtma uchun ism familiyangizni kiriting:")
    await call.answer()

# Xaridor ismini yozganda
@dp.message(OrderState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(customer_name=message.text)
    await state.set_state(OrderState.waiting_for_phone)
    
    # Raqamni oson yuborishi uchun Telegram kontakt yuborish tugmasi
    phone_builder = ReplyKeyboardBuilder()
    phone_builder.button(text="📱 Telefon raqamingizni yuborish", request_contact=True)
    
    await message.answer(
        "Raqamingizni kiriting yoki quyidagi tugma orqali yuboring:",
        reply_markup=phone_builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )

# Xaridor telefon yuborganda (Buyurtmani yakunlash qismi)
@dp.message(OrderState.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number if message.contact else message.text

    # Xotiradagi hamma ma'lumotlarni yig'ib olamiz
    user_data = await state.get_data()
    customer_name = user_data['customer_name']
    product_id = user_data['chosen_product_id']

    # To'g'ridan-to'g'ri Django PostgreSQL bazasiga yangi order yozamiz
    new_order = await create_order(customer_name, phone_number, product_id)
    
    # Cheksiz buyurtma berish imkoniyati uchun "Qaytadan xarid qilish" tugmasi
    back_builder = InlineKeyboardBuilder()
    back_builder.button(text="🛍 Qaytadan xarid qilish", callback_data="back_to_categories")
    
    # Telefon yuborish klaviaturasini tozalaymiz
    await message.answer(
        text="Raqam qabul qilindi. Rahmat!",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Xaridorga muvaffaqiyatli xabar va cheksiz inline tugmani chiqaramiz
    await message.answer(
        text=f"🎉 Buyurtmangiz muvaffaqiyatli qabul qilindi.\n"
             f"🔢 Buyurtma raqami: #{new_order.id}\n\n"
             f"Tez orada operatorlarimiz siz bilan bog'lanishadi.\n"
             f"Yana boshqa mahsulotlarni ko'rishni xohlaysizmi?",
        reply_markup=back_builder.as_markup()
    )
    
    await state.clear() # Holatni tozalaymiz

# ==========================================================
# 5. Botni ishga tushirish
# ==========================================================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
