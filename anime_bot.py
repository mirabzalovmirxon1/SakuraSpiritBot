import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.enums import ParseMode
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

API_TOKEN = "7923112418:AAH67ul5Bs3bnu02rDCEmzgkMvX2Mg_WqLM"  # Tokenni qo'y

# Admin ID (faqat shu foydalanuvchi anime qo'sha yoki o'chira oladi)
ADMIN_ID = 8056195391
  # O'zingizning Telegram ID'ingizni yozing

# Kanal usernamelari
CHANNELS = ["@anime_world_uz", "@ani_news_uz"]

# Ma'lumotlar bazasi
anime_db = {}
favorites = {}

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# --- FSM holatlar (admin uchun bosqichma-bosqich kiritish) ---
class AddAnime(StatesGroup):
    name = State()
    desc = State()
    episode = State()
    video = State()


# Kanalga obuna tekshiruvi
async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception:
            return False
    return True


# /start buyrug'i
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    # if not await check_subscription(message.from_user.id):
    #     keyboard = InlineKeyboardMarkup(inline_keyboard=[
    #         [InlineKeyboardButton(text="1️⃣ Kanalga o'tish", url=f"https://t.me/an1japan")],
    #         [InlineKeyboardButton(text="2️⃣ Kanalga o'tish", url=f"https://t.me/+k0TB1tK7BWg3NmEy")],
    #         [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    #     ])
    #     await message.answer("Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling 👇", reply_markup=keyboard)
    #     return

    await message.answer("👋 Salom! Anime dunyosiga xush kelibsiz!\nAnime nomini yoki ID sini yuboring 🔍")


# @dp.callback_query(F.data == "check_sub")
# async def check_sub_callback(callback: types.CallbackQuery):
#     if await check_subscription(callback.from_user.id):
#         await callback.message.edit_text("✅ Rahmat! Endi anime qidirishingiz mumkin.\nAnime nomi yoki ID yuboring 🔍")
    # else:
    #     await callback.answer("❌ Siz hali barcha kanallarga obuna bo'lmagansiz!", show_alert=True)


# Admin /add buyrug'i
@dp.message(Command("add"))
async def add_anime_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Siz admin emassiz.")
        return

    await message.answer("🎬 Anime nomini yuboring:")
    await state.set_state(AddAnime.name)


@dp.message(AddAnime.name)
async def add_anime_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📝 Anime tavsifini yuboring:")
    await state.set_state(AddAnime.desc)


@dp.message(AddAnime.desc)
async def add_anime_desc(message: types.Message, state: FSMContext):
    await state.update_data(desc=message.text)
    await message.answer("🔢 Nechinchi qism ekanligini yozing (masalan: 1-qism):")
    await state.set_state(AddAnime.episode)


@dp.message(AddAnime.episode)
async def add_anime_episode(message: types.Message, state: FSMContext):
    await state.update_data(episode=message.text)
    await message.answer("📹 Endi anime videosini yuboring (fayl yoki video havola):")
    await state.set_state(AddAnime.video)


@dp.message(AddAnime.video)
async def add_anime_video(message: types.Message, state: FSMContext):
    data = await state.get_data()
    anime_id = str(len(anime_db) + 1)
    name = data["name"]
    desc = data["desc"]
    episode = data["episode"]

    video = None
    if message.video:
        video = message.video.file_id
    else:
        video = message.text

    anime_db[anime_id] = {
        "name": name,
        "desc": desc,
        "episode": episode,
        "video": video
    }

    await message.answer(f"✅ Anime qo'shildi!\n🆔 ID: {anime_id}\n🎬 {name} — {episode}")
    await state.clear()


# Admin anime o'chirish
@dp.message(Command("delete"))
async def delete_anime(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Siz admin emassiz.")
        return

    try:
        anime_id = message.text.split(" ")[1]
        if anime_id in anime_db:
            deleted = anime_db.pop(anime_id)
            await message.answer(f"🗑 '{deleted['name']}' o'chirildi.")
        else:
            await message.answer("❌ Bunday ID mavjud emas.")
    except:
        await message.answer("❗ Foydalanish: /delete <ID>")


# Anime qidirish
@dp.message()
async def search_anime(message: types.Message):
    text = message.text.lower()
    results = []
    for anime_id, anime_data in anime_db.items():
        if text in anime_data["name"].lower() or text == anime_id:
            results.append((anime_id, anime_data))

    if not results:
        await message.answer("❌ Bunday anime topilmadi.")
        return

    for anime_id, anime_data in results:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❤️ Sevimlilarga qo'shish", callback_data=f"fav_{anime_id}")]
        ])
        caption = (
            f"🎬 <b>{anime_data['name']}</b>\n"
            f"🆔 ID: <code>{anime_id}</code>\n"
            f"📺 {anime_data['episode']}\n"
            f"📝 {anime_data['desc']}"
        )

        # Video turi
        if anime_data["video"].startswith("BAA"):
            await message.answer_video(video=anime_data["video"], caption=caption,
                                       parse_mode=ParseMode.HTML, reply_markup=keyboard)
        else:
            await message.answer(f"{caption}\n📹 Video: {anime_data['video']}",
                                 parse_mode=ParseMode.HTML, reply_markup=keyboard)


# Sevimlilarga qo'shish
@dp.callback_query(F.data.startswith("fav_"))
async def add_to_favorites(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    anime_id = callback.data.split("_")[1]
    anime = anime_db.get(anime_id)

    if not anime:
        await callback.answer("❌ Bu anime o'chirib tashlangan.", show_alert=True)
        return

    favorites.setdefault(user_id, set()).add(anime_id)
    await callback.answer(f"❤️ '{anime['name']}' sevimlilarga qo'shildi!", show_alert=True)


# /favorites — foydalanuvchi sevimlilari
@dp.message(Command("favorites"))
async def show_favorites(message: types.Message):
    favs = favorites.get(message.from_user.id, [])
    if not favs:
        await message.answer("💔 Sizda hali sevimli anime yo'q.")
        return

    text = "❤️ Sizning sevimli animelaringiz:\n\n"
    for anime_id in favs:
        data = anime_db.get(anime_id)
        if data:
            text += f"🆔 {anime_id} — {data['name']} ({data['episode']})\n"
    await message.answer(text)


# --- Asosiy ishga tushirish ---
async def main():
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
