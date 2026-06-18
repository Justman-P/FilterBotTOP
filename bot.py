import io
import logging
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import telebot
from telebot import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8935583003:AAEYgHp3M0ikMKsixALoGMdmZtSIVnwM_w0"

bot = telebot.TeleBot(BOT_TOKEN)

user_photos = {}


def apply_grayscale(img):
    return ImageOps.grayscale(img).convert("RGB")

def apply_sepia(img):
    grayscale = ImageOps.grayscale(img)
    sepia = Image.new("RGB", img.size)
    pixels = list(grayscale.getdata())
    sepia_pixels = []
    for p in pixels:
        r = min(int(p * 1.1), 255)
        g = min(int(p * 0.9), 255)
        b = min(int(p * 0.7), 255)
        sepia_pixels.append((r, g, b))
    sepia.putdata(sepia_pixels)
    return sepia

def apply_blur(img):
    return img.filter(ImageFilter.GaussianBlur(radius=5))

def apply_sharpen(img):
    return ImageEnhance.Sharpness(img).enhance(3.0)

def apply_brightness(img):
    return ImageEnhance.Brightness(img).enhance(1.5)

def apply_contrast(img):
    return ImageEnhance.Contrast(img).enhance(2.0)

def apply_invert(img):
    return ImageOps.invert(img.convert("RGB"))

def apply_vintage(img):
    sepia = apply_sepia(img)
    faded = ImageEnhance.Contrast(sepia).enhance(0.7)
    return ImageEnhance.Brightness(faded).enhance(1.1)

def apply_cool(img):
    r, g, b = img.split()
    r = ImageEnhance.Brightness(r).enhance(0.8)
    b = ImageEnhance.Brightness(b).enhance(1.3)
    return Image.merge("RGB", (r, g, b))

def apply_warm(img):
    r, g, b = img.split()
    r = ImageEnhance.Brightness(r).enhance(1.3)
    b = ImageEnhance.Brightness(b).enhance(0.8)
    return Image.merge("RGB", (r, g, b))

def apply_mirror(img):
    return ImageOps.mirror(img)

def apply_rotate(img):
    return img.rotate(90, expand=True)

def apply_pixelate(img):
    small = img.resize((img.width // 10, img.height // 10), Image.NEAREST)
    return small.resize(img.size, Image.NEAREST)

def apply_emboss(img):
    return img.filter(ImageFilter.EMBOSS)

def apply_edges(img):
    return ImageOps.invert(img.filter(ImageFilter.FIND_EDGES).convert("RGB"))


FILTERS = {
    "⬛ Ч/Б":      apply_grayscale,
    "🟤 Сепия":    apply_sepia,
    "💙 Холод":    apply_cool,
    "🔴 Тепло":    apply_warm,
    "📷 Винтаж":   apply_vintage,
    "🌫 Размытие": apply_blur,
    "🔪 Резкость": apply_sharpen,
    "☀️ Яркость":  apply_brightness,
    "🎨 Контраст": apply_contrast,
    "🔄 Инверсия": apply_invert,
    "🪞 Зеркало":  apply_mirror,
    "↩️ Поворот":  apply_rotate,
    "🟦 Пиксели":  apply_pixelate,
    "🗿 Рельеф":   apply_emboss,
    "✏️ Контуры":  apply_edges,
}


def make_filters_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [
        types.InlineKeyboardButton(name, callback_data=f"filter:{name}")
        for name in FILTERS.keys()
    ]
    markup.add(*buttons)
    return markup


@bot.message_handler(commands=["start", "help"])
def handle_start(message):
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я бот для обработки фотографий.\n\n"
        "📸 Отправь мне любую фотографию, и я предложу тебе выбрать фильтр!\n\n"
        "Доступно *15 фильтров*: ч/б, сепия, размытие, контраст, инверсия и многое другое.",
        parse_mode="Markdown"
    )

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    try:
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded = bot.download_file(file_info.file_path)
        user_photos[message.from_user.id] = downloaded
        bot.send_message(
            message.chat.id,
            "✅ Фото получено! Выбери фильтр:",
            reply_markup=make_filters_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при получении фото: {e}")
        bot.send_message(message.chat.id, "❌ Не удалось обработать фото. Попробуй ещё раз.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("filter:"))
def handle_filter_choice(call):
    user_id = call.from_user.id
    filter_name = call.data.split("filter:", 1)[1]

    if user_id not in user_photos:
        bot.answer_callback_query(call.id, "⚠️ Сначала отправь фотографию!")
        return

    if filter_name not in FILTERS:
        bot.answer_callback_query(call.id, "❌ Неизвестный фильтр.")
        return

    bot.answer_callback_query(call.id, f"Применяю фильтр {filter_name}...")

    try:
        img = Image.open(io.BytesIO(user_photos[user_id])).convert("RGB")
        result_img = FILTERS[filter_name](img)
        output = io.BytesIO()
        result_img.save(output, format="JPEG", quality=95)
        output.seek(0)
        bot.send_photo(
            call.message.chat.id,
            output,
            caption=f"Применён фильтр: {filter_name}",
            reply_markup=make_filters_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при применении фильтра: {e}")
        bot.send_message(call.message.chat.id, "❌ Ошибка при обработке фото. Попробуй ещё раз.")

@bot.message_handler(func=lambda m: True)
def handle_other(message):
    bot.send_message(message.chat.id, "📸 Отправь мне фотографию, и я наложу на неё фильтр!")


if __name__ == "__main__":
    logger.info("Бот запущен...")
    bot.infinity_polling()