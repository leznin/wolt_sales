# messages.py
MESSAGES = {
    'ru': {  # Русский (Россия, Казахстан, Узбекистан, Грузия, Азербайджан)
        'start': "Привет, {user}! Я бот для работы с геопозицией.\nВыбери действие:",
        'location_request': "Пожалуйста, отправь мне свою локацию, нажав на кнопку скрепки 📎 и выбрав 'Геопозиция'.",
        'location_received': "Получена геопозиция:\nШирота: {lat}\nДолгота: {lon}",
        'help': "Я бот для получения геопозиции.\n1. Нажми 'Отправить локацию'\n2. Отправь свою позицию\n3. Я покажу твои координаты",
        'choose_action': "Выбери действие:",
        'btn_send_location': "Отправить локацию",
        'btn_help': "Помощь",
        'btn_back': "Назад",
        'btn_send_again': "Отправить еще раз"
    },
    'en': {  # Английский (Мальта, Кипр, универсальный язык)
        'start': "Hello, {user}! I'm a bot for working with geolocation.\nChoose an action:",
        'location_request': "Please send me your location by clicking the paperclip 📎 and selecting 'Location'.",
        'location_received': "Location received:\nLatitude: {lat}\nLongitude: {lon}",
        'help': "I'm a geolocation bot.\n1. Press 'Send location'\n2. Send your position\n3. I'll show your coordinates",
        'choose_action': "Choose an action:",
        'btn_send_location': "Send location",
        'btn_help': "Help",
        'btn_back': "Back",
        'btn_send_again': "Send again"
    },
    'fi': {  # Финский (Финляндия)
        'start': "Hei, {user}! Olen geopaikannusrobotti.\nValitse toiminto:",
        'location_request': "Lähetä minulle sijaintisi napsauttamalla paperiliitintä 📎 ja valitsemalla 'Sijainti'.",
        'location_received': "Sijainti vastaanotettu:\nLeveysaste: {lat}\nPituusaste: {lon}",
        'help': "Olen geopaikannusrobotti.\n1. Paina 'Lähetä sijainti'\n2. Lähetä sijaintisi\n3. Näytän koordinaattisi",
        'choose_action': "Valitse toiminto:",
        'btn_send_location': "Lähetä sijainti",
        'btn_help': "Apua",
        'btn_back': "Takaisin",
        'btn_send_again': "Lähetä uudelleen"
    },
    'sv': {  # Шведский (Швеция, Финляндия)
        'start': "Hej, {user}! Jag är en bot för geolokalisering.\nVälj en åtgärd:",
        'location_request': "Skicka mig din plats genom att klicka på gemet 📎 och välja 'Plats'.",
        'location_received': "Plats mottagen:\nLatitud: {lat}\nLongitud: {lon}",
        'help': "Jag är en geolokaliseringsbot.\n1. Tryck på 'Skicka plats'\n2. Skicka din position\n3. Jag visar dina koordinater",
        'choose_action': "Välj en åtgärd:",
        'btn_send_location': "Skicka plats",
        'btn_help': "Hjälp",
        'btn_back': "Tillbaka",
        'btn_send_again': "Skicka igen"
    },
    'et': {  # Эстонский (Эстония)
        'start': "Tere, {user}! Olen geopositsioneerimise bot.\nVali tegevus:",
        'location_request': "Palun saada mulle oma asukoht, klõpsates kirjaklambril 📎 ja valides 'Asukoht'.",
        'location_received': "Asukoht saadud:\nLaiuskraad: {lat}\nPikkuskraad: {lon}",
        'help': "Olen geopositsioneerimise bot.\n1. Vajuta 'Saada asukoht'\n2. Saada oma positsioon\n3. Näitan su koordinaate",
        'choose_action': "Vali tegevus:",
        'btn_send_location': "Saada asukoht",
        'btn_help': "Abi",
        'btn_back': "Tagasi",
        'btn_send_again': "Saada uuesti"
    },
    'da': {  # Датский (Дания)
        'start': "Hej, {user}! Jeg er en geolokaliseringsbot.\nVælg en handling:",
        'location_request': "Send mig din placering ved at klikke på papirclipsen 📎 og vælge 'Placering'.",
        'location_received': "Placering modtaget:\nBreddegrad: {lat}\nLængdegrad: {lon}",
        'help': "Jeg er en geolokaliseringsbot.\n1. Tryk på 'Send placering'\n2. Send din position\n3. Jeg viser dine koordinater",
        'choose_action': "Vælg en handling:",
        'btn_send_location': "Send placering",
        'btn_help': "Hjælp",
        'btn_back': "Tilbage",
        'btn_send_again': "Send igen"
    },
    'sl': {  # Словенский (Словения)
        'start': "Zdravo, {user}! Sem bot za geolokacijo.\nIzberi dejanje:",
        'location_request': "Prosim, pošlji mi svojo lokacijo tako, da klikneš na sponko 📎 in izbereš 'Lokacija'.",
        'location_received': "Lokacija prejeta:\nZemljepisna širina: {lat}\nZemljepisna dolžina: {lon}",
        'help': "Sem bot za geolokacijo.\n1. Pritisni 'Pošlji lokacijo'\n2. Pošlji svojo pozicijo\n3. Pokazal bom tvoje koordinate",
        'choose_action': "Izberi dejanje:",
        'btn_send_location': "Pošlji lokacijo",
        'btn_help': "Pomoč",
        'btn_back': "Nazaj",
        'btn_send_again': "Pošlji znova"
    },
    'sk': {  # Словацкий (Словакия)
        'start': "Ahoj, {user}! Som bot na geolokáciu.\nVyber si akciu:",
        'location_request': "Prosím, pošli mi svoju polohu kliknutím na kancelársku sponku 📎 a výberom 'Poloha'.",
        'location_received': "Poloha prijatá:\nZemepisná šírka: {lat}\nZemepisná dĺžka: {lon}",
        'help': "Som bot na geolokáciu.\n1. Stlač 'Poslať polohu'\n2. Pošli svoju pozíciu\n3. Ukážem ti tvoje súradnice",
        'choose_action': "Vyber si akciu:",
        'btn_send_location': "Poslať polohu",
        'btn_help': "Pomoc",
        'btn_back': "Späť",
        'btn_send_again': "Poslať znova"
    },
    'sr': {  # Сербский (Сербия, Косово)
        'start': "Здраво, {user}! Ја сам бот за геолокацију.\nИзабери акцију:",
        'location_request': "Молим те, пошаљи ми своју локацију кликом на спајалицу 📎 и избором 'Локација'.",
        'location_received': "Локација примљена:\nГеографска ширина: {lat}\nГеографска дужина: {lon}",
        'help': "Ја сам бот за геолокацију.\n1. Притисни 'Пошаљи локацију'\n2. Пошаљи своју позицију\n3. Показаћу ти твоје координате",
        'choose_action': "Изабери акцију:",
        'btn_send_location': "Пошаљи локацију",
        'btn_help': "Помоћ",
        'btn_back': "Назад",
        'btn_send_again': "Пошаљи поново"
    },
    'no': {  # Норвежский (Норвегия)
        'start': "Hei, {user}! Jeg er en geolokaliseringsbot.\nVelg en handling:",
        'location_request': "Send meg posisjonen din ved å klikke på binders 📎 og velge 'Posisjon'.",
        'location_received': "Posisjon mottatt:\nBreddegrad: {lat}\nLengdegrad: {lon}",
        'help': "Jeg er en geolokaliseringsbot.\n1. Trykk 'Send posisjon'\n2. Send posisjonen din\n3. Jeg viser koordinatene dine",
        'choose_action': "Velg en handling:",
        'btn_send_location': "Send posisjon",
        'btn_help': "Hjelp",
        'btn_back': "Tilbake",
        'btn_send_again': "Send igjen"
    },
    'pl': {  # Польский (Польша)
        'start': "Cześć, {user}! Jestem botem do geolokalizacji.\nWybierz działanie:",
        'location_request': "Proszę, wyślij mi swoją lokalizację, klikając na spinacz 📎 i wybierając 'Lokalizacja'.",
        'location_received': "Lokalizacja otrzymana:\nSzerokość geograficzna: {lat}\nDługość geograficzna: {lon}",
        'help': "Jestem botem do geolokalizacji.\n1. Naciśnij 'Wyślij lokalizację'\n2. Wyślij swoją pozycję\n3. Pokażę ci twoje współrzędne",
        'choose_action': "Wybierz działanie:",
        'btn_send_location': "Wyślij lokalizację",
        'btn_help': "Pomoc",
        'btn_back': "Wstecz",
        'btn_send_again': "Wyślij ponownie"
    },
    'lt': {  # Литовский (Литва)
        'start': "Sveiki, {user}! Aš esu geolokacijos botas.\nPasirink veiksmą:",
        'location_request': "Prašau atsiųsti man savo vietą, spustelėjęs segtuką 📎 ir pasirinkęs 'Vieta'.",
        'location_received': "Vieta gauta:\nPlatuma: {lat}\nIlguma: {lon}",
        'help': "Aš esu geolokacijos botas.\n1. Spausk 'Siųsti vietą'\n2. Atsiųsk savo poziciją\n3. Parodysiu tavo koordinates",
        'choose_action': "Pasirink veiksmą:",
        'btn_send_location': "Siųsti vietą",
        'btn_help': "Pagalba",
        'btn_back': "Atgal",
        'btn_send_again': "Siųsti dar kartą"
    },
    'lv': {  # Латышский (Латвия)
        'start': "Sveiki, {user}! Es esmu ģeolokācijas bots.\nIzvēlies darbību:",
        'location_request': "Lūdzu, nosūti man savu atrašanās vietu, noklikšķinot uz saspraudes 📎 un izvēloties 'Atrašanās vieta'.",
        'location_received': "Atrašanās vieta saņemta:\nPlatums: {lat}\nGarums: {lon}",
        'help': "Es esmu ģeolokācijas bots.\n1. Nospied 'Nosūtīt atrašanās vietu'\n2. Nosūti savu pozīciju\n3. Es parādīšu tavas koordinātas",
        'choose_action': "Izvēlies darbību:",
        'btn_send_location': "Nosūtīt atrašanās vietu",
        'btn_help': "Palīdzība",
        'btn_back': "Atpakaļ",
        'btn_send_again': "Nosūtīt vēlreiz"
    },
    'kk': {  # Казахский (Казахстан)
        'start': "Сәлем, {user}! Мен геолокация боты.\nӘрекетті таңда:",
        'location_request': "Маған орналасқан жеріңді жібер, қағаз қыстырғышты 📎 басып, 'Орналасу' таңда.",
        'location_received': "Орналасу алынды:\nЕндік: {lat}\nБойлық: {lon}",
        'help': "Мен геолокация боты.\n1. 'Орналасуды жібер' бас\n2. Позицияңды жібер\n3. Координаттарыңды көрсетемін",
        'choose_action': "Әрекетті таңда:",
        'btn_send_location': "Орналасуды жібер",
        'btn_help': "Көмек",
        'btn_back': "Артқа",
        'btn_send_again': "Қайта жібер"
    },
    'ja': {  # Японский (Япония)
        'start': "こんにちは、{user}さん！私はジオロケーションボットです。\nアクションを選んでください：",
        'location_request': "クリップ📎をクリックして「位置情報」を選択し、私にあなたの位置情報を送ってください。",
        'location_received': "位置情報を受け取りました：\n緯度：{lat}\n経度：{lon}",
        'help': "私はジオロケーションボットです。\n1.「位置情報を送信」を押してください\n2.あなたの位置を送ってください\n3.座標を表示します",
        'choose_action': "アクションを選んでください：",
        'btn_send_location': "位置情報を送信",
        'btn_help': "ヘルプ",
        'btn_back': "戻る",
        'btn_send_again': "もう一度送信"
    },
    'he': {  # Иврит (Израиль)
        'start': "שלום, {user}! אני בוט לגיאולוקציה.\nבחר פעולה:",
        'location_request': "אנא שלח לי את המיקום שלך על ידי לחיצה על האטב 📎 ובחירת 'מיקום'.",
        'location_received': "מיקום התקבל:\nקו רוחב: {lat}\nקו אורך: {lon}",
        'help': "אני בוט לגיאולוקציה.\n1. לחץ על 'שלח מיקום'\n2. שלח את המיקום שלך\n3. אראה לך את הקואורדינטות שלך",
        'choose_action': "בחר פעולה:",
        'btn_send_location': "שלח מיקום",
        'btn_help': "עזרה",
        'btn_back': "חזור",
        'btn_send_again': "שלח שוב"
    },
    'is': {  # Исландский (Исландия)
        'start': "Halló, {user}! Ég er staðsetningarbotni.\nVeldu aðgerð:",
        'location_request': "Vinsamlegast sendu mér staðsetninguna þína með því að smella á bréfaklemmu 📎 og velja 'Staðsetning'.",
        'location_received': "Staðsetning móttekin:\nBreiddargráða: {lat}\nLengdargráða: {lon}",
        'help': "Ég er staðsetningarbotni.\n1. Ýttu á 'Senda staðsetningu'\n2. Sendu staðsetninguna þína\n3. Ég sýni þér hnit þín",
        'choose_action': "Veldu aðgerð:",
        'btn_send_location': "Senda staðsetningu",
        'btn_help': "Hjálp",
        'btn_back': "Til baka",
        'btn_send_again': "Senda aftur"
    },
    'hu': {  # Венгерский (Венгрия)
        'start': "Helló, {user}! Geolokációs bot vagyok.\nVálassz egy műveletet:",
        'location_request': "Kérlek, küldd el nekem a helyzetedet a gemkapocsra 📎 kattintva és a 'Helyzet' kiválasztásával.",
        'location_received': "Helyzet megérkezett:\nSzélesség: {lat}\nHosszúság: {lon}",
        'help': "Geolokációs bot vagyok.\n1. Nyomd meg a 'Helyzet küldése' gombot\n2. Küldd el a pozíciódat\n3. Megmutatom a koordinátáidat",
        'choose_action': "Válassz egy műveletet:",
        'btn_send_location': "Helyzet küldése",
        'btn_help': "Segítség",
        'btn_back': "Vissza",
        'btn_send_again': "Küldés újra"
    },
    'el': {  # Греческий (Греция, Кипр)
        'start': "Γειά σου, {user}! Είμαι bot γεωτοποθεσίας.\nΕπίλεξε μια ενέργεια:",
        'location_request': "Παρακαλώ στείλε μου την τοποθεσία σου κάνοντας κλικ στο συνδετήρα 📎 και επιλέγοντας 'Τοποθεσία'.",
        'location_received': "Η τοποθεσία ελήφθη:\nΠλάτος: {lat}\nΜήκος: {lon}",
        'help': "Είμαι bot γεωτοποθεσίας.\n1. Πάτησε 'Αποστολή τοποθεσίας'\n2. Στείλε τη θέση σου\n3. Θα σου δείξω τις συντεταγμένες σου",
        'choose_action': "Επίλεξε μια ενέργεια:",
        'btn_send_location': "Αποστολή τοποθεσίας",
        'btn_help': "Βοήθεια",
        'btn_back': "Πίσω",
        'btn_send_again': "Αποστολή ξανά"
    },
    'de': {  # Немецкий (Германия, Австрия, Люксембург)
        'start': "Hallo, {user}! Ich bin ein Geolokalisierungs-Bot.\nWähle eine Aktion:",
        'location_request': "Bitte sende mir deinen Standort, indem du auf die Büroklammer 📎 klickst und 'Standort' auswählst.",
        'location_received': "Standort erhalten:\nBreitengrad: {lat}\nLängengrad: {lon}",
        'help': "Ich bin ein Geolokalisierungs-Bot.\n1. Drücke 'Standort senden'\n2. Sende deine Position\n3. Ich zeige dir deine Koordinaten",
        'choose_action': "Wähle eine Aktion:",
        'btn_send_location': "Standort senden",
        'btn_help': "Hilfe",
        'btn_back': "Zurück",
        'btn_send_again': "Erneut senden"
    },
    'ka': {  # Грузинский (Грузия)
        'start': "გამარჯობა, {user}! მე ვარ გეოლოკაციის ბოტი.\nაირჩიე მოქმედება:",
        'location_request': "გთხოვ, გამომიგზავნე შენი მდებარეობა, დააჭირე სამაგრს 📎 და აირჩიე 'მდებარეობა'.",
        'location_received': "მდებარეობა მიღებულია:\nგანედი: {lat}\nგრძედი: {lon}",
        'help': "მე ვარ გეოლოკაციის ბოტი.\n1. დააჭირე 'მდებარეობის გაგზავნა'\n2. გამომიგზავნე შენი პოზიცია\n3. გაჩვენებ შენს კოორდინატებს",
        'choose_action': "აირჩიე მოქმედება:",
        'btn_send_location': "მდებარეობის გაგზავნა",
        'btn_help': "დახმარება",
        'btn_back': "უკან",
        'btn_send_again': "ხელახლა გაგზავნა"
    },
    'cs': {  # Чешский (Чехия)
        'start': "Ahoj, {user}! Jsem bot pro geolokaci.\nVyber akci:",
        'location_request': "Prosím, pošli mi svou polohu kliknutím na sponku 📎 a výběrem 'Poloha'.",
        'location_received': "Poloha přijata:\nZeměpisná šířka: {lat}\nZeměpisná délka: {lon}",
        'help': "Jsem bot pro geolokaci.\n1. Stiskni 'Poslat polohu'\n2. Pošli svou pozici\n3. Ukážu ti tvé souřadnice",
        'choose_action': "Vyber akci:",
        'btn_send_location': "Poslat polohu",
        'btn_help': "Nápověda",
        'btn_back': "Zpět",
        'btn_send_again': "Poslat znovu"
    },
    'hr': {  # Хорватский (Хорватия)
        'start': "Zdravo, {user}! Ja sam bot za geolokaciju.\nOdaberi akciju:",
        'location_request': "Molim te, pošalji mi svoju lokaciju klikom na spajalicu 📎 i odabirom 'Lokacija'.",
        'location_received': "Lokacija primljena:\nGeografska širina: {lat}\nGeografska dužina: {lon}",
        'help': "Ja sam bot za geolokaciju.\n1. Pritisni 'Pošalji lokaciju'\n2. Pošalji svoju poziciju\n3. Pokazat ću ti tvoje koordinate",
        'choose_action': "Odaberi akciju:",
        'btn_send_location': "Pošalji lokaciju",
        'btn_help': "Pomoć",
        'btn_back': "Natrag",
        'btn_send_again': "Pošalji ponovno"
    },
    'az': {  # Азербайджанский (Азербайджан)
        'start': "Salam, {user}! Mən geolokasiya botuyam.\nHərəkət seç:",
        'location_request': "Zəhmət olmasa, mənə yerini göndər, kağız klipə 📎 klikləyib 'Yer' seçərək.",
        'location_received': "Yer alındı:\nEnlik: {lat}\nUzunluq: {lon}",
        'help': "Mən geolokasiya botuyam.\n1. 'Yeri göndər' düyməsini bas\n2. Yerini göndər\n3. Koordinatlarını göstərəcəm",
        'choose_action': "Hərəkət seç:",
        'btn_send_location': "Yeri göndər",
        'btn_help': "Kömək",
        'btn_back': "Geri",
        'btn_send_again': "Yenidən göndər"
    },
    'uz': {  # Узбекский (Узбекистан)
        'start': "Salom, {user}! Men geolokatsiya botiman.\nHarakatni tanla:",
        'location_request': "Iltimos, menga joylashuvingni yubor, qog‘oz qisqichni 📎 bosib 'Joylashuv' ni tanla.",
        'location_received': "Joylashuv qabul qilindi:\nKenglik: {lat}\nUzunlik: {lon}",
        'help': "Men geolokatsiya botiman.\n1. 'Joylashuvni yubor' ni bos\n2. Joylashuvingni yubor\n3. Koordinatalaringni ko‘rsataman",
        'choose_action': "Harakatni tanla:",
        'btn_send_location': "Joylashuvni yubor",
        'btn_help': "Yordam",
        'btn_back': "Orqaga",
        'btn_send_again': "Qayta yubor"
    },
    'mk': {  # Македонский (Северная Македония)
        'start': "Здраво, {user}! Јас сум бот за геолокација.\nИзбери акција:",
        'location_request': "Те молам, испрати ми ја твојата локација со кликнување на спојката 📎 и избирање 'Локација'.",
        'location_received': "Локација примена:\nГеографска ширина: {lat}\nГеографска должина: {lon}",
        'help': "Јас сум бот за геолокација.\n1. Притисни 'Испрати локација'\n2. Испрати ја твојата позиција\n3. Ќе ти ги покажам твоите координати",
        'choose_action': "Избери акција:",
        'btn_send_location': "Испрати локација",
        'btn_help': "Помош",
        'btn_back': "Назад",
        'btn_send_again': "Испрати повторно"
    },
    'sq': {  # Албанский (Албания, Косово)
        'start': "Përshëndetje, {user}! Unë jam një bot për gjeolokacion.\nZgjidh një veprim:",
        'location_request': "Ju lutem, më dërgoni vendndodhjen tuaj duke klikuar në kapësen e letrës 📎 dhe duke zgjedhur 'Vendndodhje'.",
        'location_received': "Vendndodhja u mor:\nGjerësia gjeografike: {lat}\nGjatësia gjeografike: {lon}",
        'help': "Unë jam një bot për gjeolokacion.\n1. Shtyp 'Dërgo vendndodhjen'\n2. Dërgo pozicionin tënd\n3. Do të të tregoj koordinatat e tua",
        'choose_action': "Zgjidh një veprim:",
        'btn_send_location': "Dërgo vendndodhjen",
        'btn_help': "Ndihmë",
        'btn_back': "Kthehu",
        'btn_send_again': "Dërgo përsëri"
    }
}

# Функция для получения текста по ключу и языку
def get_text(key, lang='en', **kwargs):
    text = MESSAGES.get(lang, MESSAGES['ru'])[key]
    return text.format(**kwargs) if kwargs else text