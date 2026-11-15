"""Все тексты бота: русский и узбекский (латиница)."""

QUICK_KEYS = ["block", "lights", "alarm", "window", "evac", "urgent"]

T = {
    "ru": {
        # ---- меню ----
        "btn_my": "🏷 Мои стикеры",
        "btn_activate": "➕ Активировать",
        "btn_chats": "💬 Чаты",
        "btn_buy": "🛒 Купить Mesh",
        "btn_help": "ℹ️ Как это работает",
        "btn_lang": "🌐 Til / Язык",
        "btn_cancel": "✖️ Отмена",
        "btn_back": "⬅️ Назад",

        "welcome": (
            "<b>Mesh - DYLNX</b> 🌐\n"
            "Умный QR-стикер для связи с вами в любых ситуациях.\n\n"
            "Нужно связаться с владельцем вещи, автомобиля или оставить важное сообщение? "
            "Достаточно отсканировать QR — и сообщение моментально придёт владельцу сюда, в Telegram.\n\n"
            "🔒 Никто не видит ваш номер и аккаунт — чат полностью анонимный.\n\n"
            "Купили стикер? Нажмите <b>«➕ Активировать»</b>."
        ),
        "help": (
            "<b>Как работает Mesh - DYLNX</b>\n\n"
            "1️⃣ Покупаете стикер с уникальным QR и секретным кодом.\n"
            "2️⃣ Активируете его здесь: «➕ Активировать» → ссылка/фото QR → код.\n"
            "3️⃣ Клеите стикер на видное место (автомобиль, гаджет, сумка, дверь и т.д.).\n"
            "4️⃣ Если кто-то захочет с вами связаться — сканирует QR, жмёт «Написать владельцу», "
            "и сообщение приходит вам в этот бот.\n"
            "5️⃣ Вы отвечаете прямо тут. Ни номер, ни ваш Telegram никто не увидит.\n\n"
            "Под каждым сообщением есть кнопки: ответить, «уже иду», заблокировать, завершить чат.\n"
            "Ещё можно просто ответить (reply) на сообщение — ответ уйдёт в нужный чат."
        ),
        "buy": (
            "<b>🛒 Купить Mesh - DYLNX</b>\n\n"
            "Стикер Mesh — это:\n"
            "• связь с вами 24/7 в любой ситуации\n"
            "• полная анонимность — без публикации личного номера\n"
            "• активация за 1 минуту прямо в Telegram\n\n"
            "Чтобы заказать — напишите нам 👇"
        ),
        "buy_btn": "🛒 Заказать",
        "support_btn": "💬 Поддержка",
        "lang_choose": "Выберите язык / Tilni tanlang:",
        "lang_set": "✅ Язык: русский",
        "service_down": "⚠️ Сервис временно недоступен. Попробуйте через минуту.",
        "cancelled": "Отменено.",

        # ---- гость (тот, кто сканировал) ----
        "contact_intro": (
            "<b>Mesh - DYLNX</b> · связь с владельцем \n\n"
            "Ваше сообщение мгновенно придёт владельцу.\n"
            "🔒 Ваши данные скрыты — владелец не увидит ваш аккаунт, а вы — его.\n\n"
            "Выберите причину или просто напишите сообщение 👇"
        ),
        "q_block": "🚧 Транспорт/объект перекрывает проезд",
        "q_lights": "💡 Оставлены включенные приборы/фары",
        "q_alarm": "🚨 Сработала сигнализация / тревога",
        "q_window": "🪟 Что-то открыто или забыто",
        "q_evac": "🚛 Объект собираются переместить / эвакуировать",
        "q_urgent": "⚠️ Срочно требуется ваше внимание",
        "q_custom": "✍️ Своё сообщение",
        "write_custom": "Напишите сообщение — оно сразу уйдёт владельцу. Можно отправить фото или геолокацию.",
        "first_delivered": "✅ Доставлено владельцу! Ответ придёт сюда же. Можете продолжать писать.",
        "own_sticker": "🙂 Это ваш собственный стикер. Так его увидят другие — сообщения будут приходить вам сюда.",
        "mesh_not_found": "❌ Такой стикер не найден. Проверьте QR-код.",
        "mesh_inactive": (
            "⏳ Этот стикер ещё не активирован владельцем, связаться через него пока нельзя.\n\n"
            "Если это ваш стикер — активируйте его 👇"
        ),
        "mesh_expired": "⌛️ Срок действия этого стикера истёк — связаться через него сейчас нельзя.",
        "you_blocked": "🚫 Владелец ограничил сообщения от вас.",
        "slow_down": "⏱ Не так быстро — подождите пару секунд.",

        # ---- чат ----
        "hdr_to_owner": "🔔 <b>Mesh - DYLNX</b> · Чат #{conv}\nСтикер <code>…{short}</code> · Гость",
        "hdr_to_guest": "👤 <b>Владелец</b> · Чат #{conv}",
        "hdr_admin": "📢 <b>Mesh - DYLNX</b> · сообщение от администрации\nСтикер <code>…{short}</code>",
        "b_reply": "↩️ Ответить",
        "b_omw": "🏃 Уже иду",
        "b_block": "🚫 Блок",
        "b_end": "✖️ Завершить",
        "b_unblock": "🔓 Разблокировать",
        "omw_text": "🏃 Владелец увидел сообщение и уже направляется",
        "omw_done": "Гостю отправлено: «уже иду» ✅",
        "reply_mode": "✍️ Пишите — ответ уйдёт в <b>Чат #{conv}</b>.",
        "blocked_ok": "🚫 Гость из Чата #{conv} заблокирован, чат закрыт.",
        "unblocked_ok": "🔓 Разблокировано.",
        "chat_ended_you": "✖️ Чат #{conv} завершён.",
        "chat_ended_other": "✖️ Собеседник завершил Чат #{conv}.",
        "chat_closed": "Этот чат уже закрыт.",
        "no_chat": "Сейчас у вас нет открытых чатов. Используйте меню 👇",
        "pick_chat": "У вас несколько открытых чатов. Выберите, кому отвечать, и отправьте сообщение ещё раз:",
        "chats_title": "<b>💬 Открытые чаты</b>\nНажмите, чтобы отвечать в выбранный чат.",
        "chat_row_owner": "Чат #{conv} · гость · {ago}",
        "chat_row_guest": "Чат #{conv} · владелец · {ago}",
        "chat_selected": "✅ Теперь ваши сообщения уходят в <b>Чат #{conv}</b>.",
        "ago_min": "{n} мин назад",
        "ago_h": "{n} ч назад",
        "media_photo": "[фото]", "media_video": "[видео]", "media_voice": "[голосовое]",
        "media_location": "[геолокация]", "media_sticker": "[стикер]", "media_other": "[вложение]",
        "unsupported": "Такой тип сообщения нельзя переслать.",

        # ---- активация ----
        "act_ask_qr": (
            "<b>Активация стикера Mesh - DYLNX</b>\n\n"
            "Отправьте одно из:\n"
            "• фото QR-кода со стикера\n"
            "• ссылку из QR (…/mesh/xxxx/)\n"
            "• UUID стикера"
        ),
        "act_bad_qr": "Не нашёл код стикера 🤔 Пришлите ссылку из QR или более чёткое фото.",
        "act_already_mine": "✅ Этот стикер уже активирован на вас.",
        "act_taken": "🔒 Этот стикер уже привязан к другому пользователю. Если это ошибка — напишите в поддержку.",
        "act_expired": "⌛️ Срок действия стикера истёк ({until}). Обратитесь в поддержку для продления.",
        "act_ask_pass": "🔑 Введите секретный код с карточки, которая шла вместе со стикером:",
        "act_bad_pass": "❌ Неверный код. Осталось попыток: {left}.",
        "act_locked": "⛔️ Слишком много неверных попыток. Попробуйте через 15 минут.",
        "act_ask_phone": (
            "📞 Показывать ваш номер на странице стикера для экстренного звонка?\n\n"
            "Если нажмёте «Не показывать» — с вами можно будет связаться только через анонимный чат."
        ),
        "act_share_phone": "📱 Показывать мой номер",
        "act_no_phone": "🙈 Не показывать",
        "act_bad_phone": "Нажмите одну из кнопок ниже или отправьте номер в формате +998901234567.",
        "act_done": (
            "🎉 <b>Стикер активирован!</b>\n\n"
            "Наклейте его на видное место.\n"
            "Теперь все сообщения по этому стикеру будут приходить вам сюда.\n\n"
            "Действует до: <b>{until}</b>"
        ),
        "act_error": "⚠️ Не получилось активировать: {err}",

        # ---- мои стикеры ----
        "my_empty": "У вас пока нет активированных стикеров.\nКупили? Нажмите «➕ Активировать».",
        "my_title": "<b>🏷 Ваши стикеры Mesh - DYLNX</b>",
        "my_row": " …{short} · до {until}",
        "card": (
            "<b>🏷 Стикер Mesh - DYLNX</b>\n"
            "<code>{uuid}</code>\n\n"
            "Статус: {status}\n"
            "Действует до: <b>{until}</b>\n"
            "Номер для звонка: {phone}\n"
            "Сообщений всего: {count}"
        ),
        "st_active": "🟢 активен", "st_expired": "🔴 истёк", "st_off": "⚪️ выключен",
        "phone_hidden": "скрыт 🙈",
        "b_phone_hide": "🙈 Скрыть номер",
        "b_phone_show": "📱 Показывать номер",
        "b_open_page": "🔗 Страница стикера",
        "b_qr": "🖼 QR-код",
        "b_unbind": "⛔️ Отвязать",
        "unbind_confirm": "Точно отвязать стикер? Сообщения перестанут приходить, пока его снова не активируют кодом.",
        "b_yes": "Да, отвязать",
        "unbound": "Стикер отвязан.",
        "phone_hidden_ok": "Номер скрыт 🙈",
        "phone_ask": "Нажмите кнопку ниже, чтобы поделиться номером:",
        "phone_saved": "📱 Номер сохранён и показывается на странице стикера.",
        "no_qr": "QR-картинка ещё не сгенерирована — спросите администратора.",
        "expiry_remind": "⏰ Стикер <code>…{short}</code> истекает <b>{until}</b>. Продлите, чтобы не потерять связь.",
    },

    "uz": {
        "btn_my": "🏷 Stikerlarim",
        "btn_activate": "➕ Faollashtirish",
        "btn_chats": "💬 Chatlar",
        "btn_buy": "🛒 Mesh sotib olish",
        "btn_help": "ℹ️ Qanday ishlaydi",
        "btn_lang": "🌐 Til / Язык",
        "btn_cancel": "✖️ Bekor qilish",
        "btn_back": "⬅️ Orqaga",

        "welcome": (
            "<b>Mesh - DYLNX</b> 🌐\n"
            "Har qanday vaziyatda siz bilan bog'lanish uchun aqlli QR-stiker.\n\n"
            "Buyumingiz, mashinangiz yoki boshqa narsangiz kimgadir xalaqit beryapti yoxud muhim xabar qoldirmoqchimisiz? "
            "QR kodni skanerlash kifoya — xabar shu zahoti egasiga, Telegramdagi ushbu botga kelib tushadi.\n\n"
            "🔒 Raqamingiz ham, akkauntingiz ham hech kimga ko'rinmaydi — muloqot to'liq anonim.\n\n"
            "Stiker sotib oldingizmi? <b>«➕ Faollashtirish»</b> tugmasini bosing."
        ),
        "help": (
            "<b>Mesh - DYLNX qanday ishlaydi</b>\n\n"
            "1️⃣ Noyob QR kod va maxfiy kalitga ega stikerni sotib olasiz.\n"
            "2️⃣ Uni shu yerda faollashtirasiz: «➕ Faollashtirish» → QR havolasi/surati → kod.\n"
            "3️⃣ Stikerni ko'zga ko'ringan qulay joyga (avtomobil, gadjet, sumka, eshik va hokazo) yopishtirasiz.\n"
            "4️⃣ Kimgadir siz bilan bog'lanish kerak bo'lsa — u QR kodni skanerlaydi, «Egasiga yozish» tugmasini bosadi "
            "va xabar sizning botingizga kelib tushadi.\n"
            "5️⃣ Shu yerning o'zida javob berasiz. Na raqamingiz, na Telegramingiz boshqalarga ko'rinadi.\n\n"
            "Har bir xabar ostida qulay tugmalar mavjud: javob berish, «ketyapman», bloklash, chatni yakunlash.\n"
            "Shuningdek, xabarga oddiygina reply (javob qaytarish) qilish orqali ham yozishingiz mumkin."
        ),
        "buy": (
            "<b>🛒 Mesh - DYLNX sotib olish</b>\n\n"
            "Mesh stikeri — bu:\n"
            "• istalgan vaziyatda 24/7 rejimida aloqada bo'lish\n"
            "• shaxsiy raqamsiz to'liq maxfiylik va xavfsizlik\n"
            "• Telegramda atigi 1 daqiqada oson faollashtirish\n\n"
            "Buyurtma berish uchun bizga yozing 👇"
        ),
        "buy_btn": "🛒 Buyurtma berish",
        "support_btn": "💬 Yordam",
        "lang_choose": "Выберите язык / Tilni tanlang:",
        "lang_set": "✅ Til: o'zbekcha",
        "service_down": "⚠️ Xizmat vaqtincha ishlamayapti. Iltimos, bir daqiqadan so'ng qayta urinib ko'ring.",
        "cancelled": "Bekor qilindi.",

        "contact_intro": (
            "<b>Mesh - DYLNX</b> · egasi bilan bog'lanish \n\n"
            "Xabaringiz shu zahoti egasiga yetib boradi.\n"
            "🔒 Ma'lumotlaringiz xavfsiz — egasi sizning profilingizni ko'rmaydi, siz ham unikini.\n\n"
            "Sababni tanlang yoki shunchaki o'z xabaringizni yozing 👇"
        ),
        "q_block": "🚧 Transport/obyekt yo'lni to'sib qo'ygan",
        "q_lights": "💡 Chiroqlar yoki uskunalar yoniq qolgan",
        "q_alarm": "🚨 Signalizatsiya yoki ogohlantirish ishladi",
        "q_window": "🪟 Nimadir ochiq yoki unutilgan",
        "q_evac": "🚛 Obyektni ko'chirish/evakuatsiya qilishmoqchi",
        "q_urgent": "⚠️ Zudlik bilan e'tiboringiz talab etiladi",
        "q_custom": "✍️ O'z xabarimni yozish",
        "write_custom": "Xabaringizni yozing — u darhol egasiga yetib boradi. Shuningdek, rasm yoki geolokatsiya yuborishingiz ham mumkin.",
        "first_delivered": "✅ Egasiga yetkazildi! Javob shu yerga keladi. Yozishda davom etishingiz mumkin.",
        "own_sticker": "🙂 Bu sizning o'z stikeringiz. Boshqalar uni aynan shunday ko'radi — kelgan xabarlar shu yerga kelib tushadi.",
        "mesh_not_found": "❌ Bunday stiker topilmadi. QR kodni qaytadan tekshiring.",
        "mesh_inactive": (
            "⏳ Bu stiker hali egasi tomonidan faollashtirilmagan, hozircha uning orqali bog'lanib bo'lmaydi.\n\n"
            "Agar bu o'z stikeringiz bo'lsa — uni faollashtiring 👇"
        ),
        "mesh_expired": "⌛️ Bu stikerning amal qilish muddati tugagan — hozirda u orqali bog'lanish imkonsiz.",
        "you_blocked": "🚫 Egasi sizdan keladigan xabarlarni cheklagan (bloklagan).",
        "slow_down": "⏱ Juda tez yuboryapsiz — iltimos, bir necha soniya kuting.",

        "hdr_to_owner": "🔔 <b>Mesh - DYLNX</b> · Chat #{conv}\nStiker <code>…{short}</code> · Mehmon",
        "hdr_to_guest": "👤 <b>Egasi</b> · Chat #{conv}",
        "hdr_admin": "📢 <b>Mesh - DYLNX</b> · ma'muriyatdan xabar\nStiker <code>…{short}</code>",
        "b_reply": "↩️ Javob berish",
        "b_omw": "🏃 Yo'ldapman",
        "b_block": "🚫 Bloklash",
        "b_end": "✖️ Yakunlash",
        "b_unblock": "🔓 Blokdan chiqarish",
        "omw_text": "🏃 Egasi xabarni o'qidi va yo'lga chiqdi",
        "omw_done": "Mehmonga «yo'ldapman» xabari yuborildi ✅",
        "reply_mode": "✍️ Yozing — javobingiz <b>Chat #{conv}</b> ga ketadi.",
        "blocked_ok": "🚫 Chat #{conv} mehmoni bloklandi, muloqot yopildi.",
        "unblocked_ok": "🔓 Blokdan muvaffaqiyatli chiqarildi.",
        "chat_ended_you": "✖️ Chat #{conv} yakunlandi.",
        "chat_ended_other": "✖️ Suhbatdosh Chat #{conv} ni yakunladi.",
        "chat_closed": "Bu chat allaqachon yopilgan.",
        "no_chat": "Hozirda faol chatlaringiz yo'q. Kerakli amal uchun menyudan foydalaning 👇",
        "pick_chat": "Sizda bir nechta ochiq chat mavjud. Kimga javob berishni tanlang va xabarni qaytadan yuboring:",
        "chats_title": "<b>💬 Ochiq chatlar</b>\nJavob berish uchun kerakli chatni tanlang.",
        "chat_row_owner": "Chat #{conv} · mehmon · {ago}",
        "chat_row_guest": "Chat #{conv} · egasi · {ago}",
        "chat_selected": "✅ Endi xabarlaringiz <b>Chat #{conv}</b> ga yo'naltiriladi.",
        "ago_min": "{n} daq oldin",
        "ago_h": "{n} soat oldin",
        "media_photo": "[rasm]", "media_video": "[video]", "media_voice": "[ovozli xabar]",
        "media_location": "[geolokatsiya]", "media_sticker": "[stiker]", "media_other": "[ilova]",
        "unsupported": "Bunday turdagi xabarni uzatib bo'lmaydi.",

        "act_ask_qr": (
            "<b>Mesh - DYLNX stikerini faollashtirish</b>\n\n"
            "Quyidagilardan birini yuboring:\n"
            "• stikerdagi QR kodning surati\n"
            "• QR havolasi (…/mesh/xxxx/)\n"
            "• stikerning UUID raqami"
        ),
        "act_bad_qr": "Stiker kodi topilmadi 🤔 QR havolasini yoki aniqroq surat yuboring.",
        "act_already_mine": "✅ Bu stiker allaqachon sizga faollashtirilgan.",
        "act_taken": "🔒 Bu stiker allaqachon boshqa foydalanuvchiga biriktirilgan. Agar bu xatolik bo'lsa — yordam xizmatiga yozing.",
        "act_expired": "⌛️ Stikerning amal qilish muddati tugagan ({until}). Uzaytirish uchun qo'llab-quvvatlash xizmatiga murojaat qiling.",
        "act_ask_pass": "🔑 Stiker bilan birga kelgan kartochkadagi maxfiy kodni kiriting:",
        "act_bad_pass": "❌ Kod noto'g'ri kiritildi. Qolgan urinishlar soni: {left}.",
        "act_locked": "⛔️ Juda ko'p noto'g'ri urinishlar aniqlandi. 15 daqiqadan so'ng qayta urinib ko'ring.",
        "act_ask_phone": (
            "📞 Favqulodda qo'ng'iroqlar uchun raqamingiz stiker sahifasida ko'rsatilsinmi?\n\n"
            "«Ko'rsatilmasin» ni tanlasangiz — siz bilan faqat anonim chat orqali bog'lanish mumkin bo'ladi."
        ),
        "act_share_phone": "📱 Raqamim ko'rsatilsin",
        "act_no_phone": "🙈 Ko'rsatilmasin",
        "act_bad_phone": "Iltimos, quyidagi tugmalardan birini bosing yoki raqamni +998901234567 formatida yuboring.",
        "act_done": (
            "🎉 <b>Stiker muvaffaqiyatli faollashtirildi!</b>\n\n"
            "Uni qulay va ko'rinadigan joyga yopishtiring.\n"
            "Endi ushbu stiker bo'yicha barcha xabarlar shu yerga kelib tushadi.\n\n"
            "Amal qilish muddati: <b>{until}</b> gacha"
        ),
        "act_error": "⚠️ Faollashtirib bo'lmadi: {err}",

        "my_empty": "Hozircha faollashtirilgan stikerlaringiz yo'q.\nSotib oldingizmi? «➕ Faollashtirish» tugmasini bosing.",
        "my_title": "<b>🏷 Sizning Mesh - DYLNX stikerlaringiz</b>",
        "my_row": " …{short} · {until} gacha",
        "card": (
            "<b>🏷 Mesh - DYLNX stikeri</b>\n"
            "<code>{uuid}</code>\n\n"
            "Holati: {status}\n"
            "Amal qiladi: <b>{until}</b> gacha\n"
            "Qo'ng'iroq uchun raqam: {phone}\n"
            "Jami xabarlar: {count}"
        ),
        "st_active": "🟢 faol", "st_expired": "🔴 muddati tugagan", "st_off": "⚪️ o'chirilgan",
        "phone_hidden": "yashirin 🙈",
        "b_phone_hide": "🙈 Raqamni yashirish",
        "b_phone_show": "📱 Raqamni ko'rsatish",
        "b_open_page": "🔗 Stiker sahifasi",
        "b_qr": "🖼 QR kod",
        "b_unbind": "⛔️ Biriktiruvni uzish",
        "unbind_confirm": "Stikerni haqiqatan ham uzmoqchimisiz? Kod bilan qayta faollashtirmaguningizcha xabarlar kelmaydi.",
        "b_yes": "Ha, uzish",
        "unbound": "Stiker muvaffaqiyatli uzildi.",
        "phone_hidden_ok": "Raqam muvaffaqiyatli yashirildi 🙈",
        "phone_ask": "Raqamingizni ulashish uchun quyidagi tugmani bosing:",
        "phone_saved": "📱 Raqam saqlandi va stiker sahifasida ko'rsatila boshlaydi.",
        "no_qr": "QR surat hali yaratilmagan — administratorga murojaat qiling.",
        "expiry_remind": "⏰ <code>…{short}</code> stikerining muddati <b>{until}</b> sanasida tugaydi. Aloqani uzib qo'ymaslik uchun muddatini uzaytiring.",
    },
}


def t(lang: str, key: str, **kw) -> str:
    s = T.get(lang, T["ru"]).get(key) or T["ru"].get(key, key)
    return s.format(**kw) if kw else s


def all_variants(key: str) -> set[str]:
    return {T[lang][key] for lang in T}


MENU_TEXTS = set().union(*(all_variants(k) for k in
                           ("btn_my", "btn_activate", "btn_chats", "btn_buy", "btn_help", "btn_lang", "btn_cancel")))