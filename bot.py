"""
Бот «Всесвіт Ліхтаря» — меню вибору Повних Досьє + оплата.

Що робить:
1. Людина переходить у бота з кнопки "🏮 Світло" на сторінці конкретного досьє
   (той вампір одразу позначається обраним) — або просто заходить у бота напряму.
2. Бачить список усіх 14 вампірів із чекбоксами ✅/⬜ і може обрати скільки завгодно.
3. Бот сам рахує суму (з автоматичною знижкою за кілька штук) і показує її.
4. Натискає «Готово» → обирає спосіб оплати (картка / готівка / донейшн).
5. Бот дякує і повідомляє, що Тетяна зв'яжеться з реквізитами; тобі приходить
   сповіщення з повним переліком і сумою в окремому чаті.

ЩО ПОТРІБНО ЗРОБИТИ ПЕРЕД ЗАПУСКОМ:
1. Встав токен від @BotFather у BOT_TOKEN.
2. Встав свій числовий Telegram ID у TATIANA_CHAT_ID (дізнатися через @userinfobot).
3. pip install python-telegram-bot --upgrade
4. python bot.py
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─── НАЛАШТУВАННЯ ────────────────────────────────────────────────────────
BOT_TOKEN = "8930342730:AAGouMFeGv2SFlEcZSb_vlapBdY96TwwLJY"
TATIANA_CHAT_ID = 5218298715  # твій особистий Telegram ID

# Вампірі у порядку показу в меню: id -> назва (той самий id, що і в тесті на сайті)
VAMPIRES = {
    "obraza": "Образи",
    "sumniv": "Сумніву в собі",
    "provyna": "Провини",
    "tilo": "Відсутності контакту з тілом",
    "viyna": "Війни з собою",
    "treba": "Життя в режимі «треба»",
    "emocii": "Прихованих подавлених емоцій",
    "podobatys": "Бажання подобатись",
    "gonka": "Внутрішньої гонки",
    "kontrol": "Контролю",
    "toksychni": "Токсичних стосунків",
    "bil": "Непрожитого болю",
    "uvaga": "Викраденої уваги",
    "nezavershene": "Незавершених справ",
}


_PRICE_TABLE = {
    1: 200,
    2: 370,
    3: 530,
    4: 560,
    5: 690,
    6: 840,
    7: 990,
    8: 1120,
    9: 1250,
    10: 1400,
    11: 1550,
    12: 1680,
    13: 1810,
}


def compute_price(n: int) -> int:
    """Ціна за n обраних досьє."""
    if n <= 0:
        return 0
    if n >= len(VAMPIRES):
        return 1500  # весь комплект
    return _PRICE_TABLE[n]


# ──────────────────────────────────────────────────────────────────────────


def dossier_desc(selected: set) -> str:
    """Формує людський опис обраних досьє: 'Повне Досьє вампіра X' або список для кількох."""
    names = [VAMPIRES[v] for v in selected]
    if len(names) == 1:
        return f"Повне Досьє вампіра {names[0]}"
    return "Повні Досьє вампірів: " + ", ".join(names)


WELCOME_TEXT = (
    "🏮 Вітаю в Архіві Тетяни Леочко.\n\n"
    "Тут зберігаються Повні Досьє вампірів твоєї енергії — де вони "
    "сформувалися і як звільнитися від їхнього впливу.\n\n"
    "Обери нижче одного чи кількох вампірів, від яких хочеш звільнитися — "
    "ліхтар запалиться 🏮. Мінімальний обмін енергією відкриє доступ до "
    "обраних Повних Досьє."
)


def build_keyboard(selected: set) -> InlineKeyboardMarkup:
    buttons = []
    for i, (vid, name) in enumerate(VAMPIRES.items(), start=1):
        mark = "🏮 " if vid in selected else ""
        buttons.append([InlineKeyboardButton(f"{mark}{i}. {name}", callback_data=f"tog_{vid}")])
    buttons.append([InlineKeyboardButton("🧾 Готово — перейти до оплати", callback_data="done")])
    return InlineKeyboardMarkup(buttons)


def selection_text(selected: set) -> str:
    if not selected:
        return "🏮 Обери, які досьє тобі потрібні 👇"
    n = len(selected)
    price = compute_price(n)
    desc = dossier_desc(selected)
    return (
        f"🏮 Обрано: {n} шт.\n{desc}\n\n"
        f"💰 Разом: {price}₴\n\n"
        f"Можеш додати ще або натиснути «Готово» 👇"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start — або просто, або /start obraza (з посилання на сторінці досьє)."""
    args = context.args
    vampire_id = args[0] if args else None

    selected = context.user_data.setdefault("selected", set())
    if vampire_id in VAMPIRES:
        selected.add(vampire_id)

    await update.message.reply_text(WELCOME_TEXT)
    await update.message.reply_text(selection_text(selected), reply_markup=build_keyboard(selected))


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    selected = context.user_data.setdefault("selected", set())

    # ── перемкнути вампіра в списку ──
    if data.startswith("tog_"):
        vid = data[4:]
        if vid in selected:
            selected.discard(vid)
        else:
            selected.add(vid)
        await query.edit_message_text(selection_text(selected), reply_markup=build_keyboard(selected))
        return

    # ── перейти до вибору способу оплати ──
    if data == "done":
        if not selected:
            await query.answer("Спочатку обери хоча б одного вампіра 🙏", show_alert=True)
            return
        n = len(selected)
        price = compute_price(n)
        desc = dossier_desc(selected)
        text = f"{desc}\n\n💰 До сплати: {price}₴\n\nОбери, як тобі зручніше обмінятися енергією 👇"
        keyboard = [
            [InlineKeyboardButton("💳 Картою", callback_data="pay_card")],
            [InlineKeyboardButton("💵 Готівкою", callback_data="pay_cash")],
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # ── обрано спосіб оплати ──
    if data.startswith("pay_"):
        method = data[4:]
        method_labels = {"card": "оплату карткою", "cash": "оплату готівкою"}
        chosen = method_labels.get(method, method)

        n = len(selected)
        price = compute_price(n)
        desc = dossier_desc(selected)

        await query.edit_message_text(
            f"Дякую! 🙏 Записала: {chosen}, {n} шт. на {price}₴.\n\n"
            f"Тетяна скоро напише тобі особисто з деталями 🏮"
        )

        if TATIANA_CHAT_ID:
            user = query.from_user
            notify_text = (
                f"🔔 Новий запит на Повні Досьє!\n\n"
                f"{desc}\n"
                f"Кількість: {n} шт.\n"
                f"Сума: {price}₴\n"
                f"Спосіб оплати: {chosen}\n"
                f"Від: {user.first_name} (@{user.username or 'без username'})\n"
                f"Написати: tg://user?id={user.id}"
            )
            await context.bot.send_message(chat_id=TATIANA_CHAT_ID, text=notify_text)

        context.user_data["selected"] = set()  # очистити вибір після завершення


# ─── ЗАХИЩЕНА ПЕРЕДАЧА ФАЙЛУ КЛІЄНТУ (тільки для Тетяни) ──────────────────
# Як користуватись: у сповіщенні про замовлення є "Написати: tg://user?id=XXXX".
# Тетяна пише боту команду  /send XXXX  (той самий id), а НАСТУПНИМ повідомленням
# надсилає боту готовий файл (документ або аудіо). Бот перешле цей файл клієнту
# з увімкненим захистом від пересилання/збереження (кнопка "Переслати" зникає).


async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != TATIANA_CHAT_ID:
        return  # ця команда доступна тільки Тетяні
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text(
            "Напиши так: /send 123456789 (id клієнта з посилання tg://user?id=... "
            "у сповіщенні про замовлення)."
        )
        return
    context.user_data["send_to"] = int(args[0])
    await update.message.reply_text(
        "Готово. Тепер надішли мені файл (документ або аудіо) — "
        "перешлю його клієнту з захистом від пересилання 🏮"
    )


async def handle_admin_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != TATIANA_CHAT_ID:
        return
    target_id = context.user_data.get("send_to")
    if not target_id:
        return  # Тетяна не в режимі пересилання — ігноруємо файл
    msg = update.message
    try:
        if msg.document:
            await context.bot.send_document(
                chat_id=target_id, document=msg.document.file_id, protect_content=True
            )
        elif msg.audio:
            await context.bot.send_audio(
                chat_id=target_id, audio=msg.audio.file_id, protect_content=True
            )
        elif msg.voice:
            await context.bot.send_voice(
                chat_id=target_id, voice=msg.voice.file_id, protect_content=True
            )
        else:
            await msg.reply_text("Це не файл/аудіо — спробуй ще раз.")
            return
        await msg.reply_text("Надіслано клієнту із захистом від пересилання ✅")
    except Exception as e:
        await msg.reply_text(f"Не вдалося надіслати: {e}")
    finally:
        context.user_data["send_to"] = None


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(
        MessageHandler(filters.Document.ALL | filters.AUDIO | filters.VOICE, handle_admin_file)
    )
    print("Бот запущено. Залиш це вікно відкритим, поки хочеш отримувати заявки.")
    app.run_polling()


if __name__ == "__main__":
    main()
