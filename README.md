# Demao site: testishla.uz (https://www.testishla.uz/en/)
# QuizHub — Django Quiz Ilovasi

## Kompyuterda ishga tushirish (Local Setup)

### Talablar
- Python 3.10 yoki undan yuqori
- pip

---

## Variant 1: SQLite (oddiy, tez sozlash)

### 1. Papkaga kiring
```bash
cd quiz_django
```

### 2. Virtual muhit yarating
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### 3. Kutubxonalarni o'rnating
```bash
pip install django==5.2.1 django-unfold whitenoise python-decouple dj-database-url Pillow
```

### 4. Migratsiyalarni bajaring
```bash
python manage.py migrate
```

### 5. Demo ma'lumotlarni yuklang
```bash
python manage.py seed_data
```

### 6. Admin foydalanuvchi yarating
```bash
python manage.py createsuperuser
```

### 7. Serverni ishga tushiring
```bash
python manage.py runserver
```

Brauzerda: **http://127.0.0.1:8000**
Admin panel: **http://127.0.0.1:8000/admin** — `admin / admin123`

---

## Variant 2: PostgreSQL (tavsiya etiladi)

### 1–3. Yuqoridagi qadamlarni bajaring, so'ng psycopg2 ham o'rnating:
```bash
pip install django==5.2.1 django-unfold whitenoise python-decouple dj-database-url Pillow psycopg2-binary
```

### 2. PostgreSQL ma'lumotlar bazasini yarating
```sql
CREATE DATABASE quizhub;
CREATE USER quizhub_user WITH PASSWORD 'quchPwd123';
GRANT ALL PRIVILEGES ON DATABASE quizhub TO quizhub_user;
```

### 3. `.env` fayl yarating (quiz_django/ papkasida)
```env
DATABASE_URL=postgresql://quizhub_user:quchPwd123@localhost:5432/quizhub
SECRET_KEY=your-very-secret-key-change-this
DEBUG=True
```

> ⚠️ `.env` faylingizni hech qachon GitHub ga yuklamang!

### 4. Migratsiya va ma'lumotlar
```bash
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
```

### 5. Serverni ishga tushiring
```bash
python manage.py runserver
```

---

## Demo foydalanuvchilar (seed_data orqali)

| Foydalanuvchi | Parol    |
|---------------|----------|
| aziz_j        | demo1234 |
| malika_n      | demo1234 |
| sardor_k      | demo1234 |

---

## Admin panel orqali JSON yuklash

### Admin ga kiring
**http://127.0.0.1:8000/admin** → `admin / admin123`

### JSON Import sahifasiga o'ting
Admin panelda **Testlar** bo'limini oching → **"JSON dan yuklash"** tugmasini bosing.

---

## JSON format namunasi

```json
[
  {
    "quiz": {
      "title_uz": "Python dasturlash asoslari",
      "description_uz": "Python dasturlash tilining asosiy tushunchalari",
      "category": "Texnologiya",
      "difficulty": "easy",
      "time_limit": 20
    },
    "questions": [
      {
        "text_uz": "Python qaysi yilda yaratilgan?",
        "explanation_uz": "Python 1991 yilda Guido van Rossum tomonidan yaratilgan.",
        "order": 1,
        "choices": [
          {"text_uz": "1989", "is_correct": false},
          {"text_uz": "1991", "is_correct": true},
          {"text_uz": "1995", "is_correct": false},
          {"text_uz": "2000", "is_correct": false}
        ]
      },
      {
        "text_uz": "Pythonda izoh qanday yoziladi?",
        "explanation_uz": "# belgisi bilan bir qatorli izoh yoziladi.",
        "order": 2,
        "choices": [
          {"text_uz": "// izoh", "is_correct": false},
          {"text_uz": "/* izoh */", "is_correct": false},
          {"text_uz": "# izoh", "is_correct": true},
          {"text_uz": "-- izoh", "is_correct": false}
        ]
      }
    ]
  }
]
```

### JSON qoidalari

| Maydon | Majburiy | Qiymat |
|---|---|---|
| `quiz.title_uz` | ✅ Ha | Test nomi |
| `quiz.description_uz` | ❌ Yo'q | Test tavsifi |
| `quiz.category` | ✅ Ha | Mavjud bo'lmasa avtomatik yaratiladi |
| `quiz.difficulty` | ❌ Yo'q | `easy` / `medium` / `hard` (standart: `medium`) |
| `quiz.time_limit` | ❌ Yo'q | Daqiqalarda son (standart: `30`) |
| `questions[].text_uz` | ✅ Ha | Savol matni |
| `questions[].order` | ❌ Yo'q | Tartib raqami |
| `questions[].explanation_uz` | ❌ Yo'q | To'g'ri javob izohi |
| `choices[].text_uz` | ✅ Ha | Variant matni |
| `choices[].is_correct` | ✅ Ha | `true` yoki `false` |

> ✅ Bir faylda bir necha test bo'lishi mumkin (JSON array ichida ko'p object)
> ✅ Kategoriya mavjud bo'lmasa, avtomatik yaratiladi

---

## Loyiha tuzilmasi

```
quiz_django/
├── quiz_project/        # Django konfiguratsiya
│   ├── settings.py      # Asosiy sozlamalar
│   └── urls.py          # URL marshrut
├── quiz/                # Asosiy ilova
│   ├── models.py        # Ma'lumotlar modeli
│   ├── views.py         # Ko'rinishlar
│   ├── admin.py         # Admin panel (JSON import)
│   └── templatetags/    # Maxsus template teglari
├── templates/           # HTML shablonlar
├── static/              # CSS, JS, namuna JSON
│   └── sample_questions.json  # JSON namuna fayl
└── manage.py
```

## Ilova imkoniyatlari

- 3 til: O'zbek / Rus / Ingliz
- Kun/tun (qoʻngʻiroq) rejimi
- Anonim foydalanuvchi (statistika saqlanmaydi, ogohlantirish ko'rsatiladi)
- Ro'yxatdan o'tgan foydalanuvchilar uchun to'liq statistika va tarix
- Django Unfold admin panel (statistika bilan)
- JSON orqali testlarni ommaviy yuklash
- Barcha savol raqamlari ko'rinib turadi
