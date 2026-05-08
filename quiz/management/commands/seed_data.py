from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from quiz.models import Category, Quiz, Question, Choice, UserProfile
import random


class Command(BaseCommand):
    help = 'Seed demo data for QuizHub'

    def handle(self, *args, **options):
        if Category.objects.exists():
            self.stdout.write('Data already seeded.')
            return

        self.stdout.write('Seeding demo data...')

        categories_data = [
            {'name_uz': 'Texnologiya', 'name_ru': 'Технологии', 'name_en': 'Technology', 'icon': '💻', 'bg_color': '#EEEDFE', 'icon_color': '#534AB7', 'slug': 'technology'},
            {'name_uz': 'Fan', 'name_ru': 'Наука', 'name_en': 'Science', 'icon': '🔬', 'bg_color': '#E1F5EE', 'icon_color': '#0F6E56', 'slug': 'science'},
            {'name_uz': 'Tarix', 'name_ru': 'История', 'name_en': 'History', 'icon': '📜', 'bg_color': '#FAEEDA', 'icon_color': '#854F0B', 'slug': 'history'},
            {'name_uz': 'Til', 'name_ru': 'Языки', 'name_en': 'Languages', 'icon': '🌐', 'bg_color': '#FAECE7', 'icon_color': '#993C1D', 'slug': 'languages'},
            {'name_uz': 'Matematika', 'name_ru': 'Математика', 'name_en': 'Mathematics', 'icon': '📐', 'bg_color': '#EFF6FF', 'icon_color': '#1D4ED8', 'slug': 'mathematics'},
            {'name_uz': 'Sport', 'name_ru': 'Спорт', 'name_en': 'Sports', 'icon': '⚽', 'bg_color': '#FEF9C3', 'icon_color': '#A16207', 'slug': 'sports'},
        ]
        categories = {}
        for data in categories_data:
            cat = Category.objects.create(**data)
            categories[data['slug']] = cat
            self.stdout.write(f'  Category: {cat.name_uz}')

        quizzes_data = [
            {
                'title_uz': 'Python dasturlash asoslari',
                'description_uz': 'Python dasturlash tili asoslari bo\'yicha test',
                'category': 'technology',
                'difficulty': 'easy',
                'time_limit': 20,
                'questions': [
                    {
                        'text_uz': 'Python qaysi yilda yaratilgan?',
                        'choices': [
                            ('1985', False), ('1991', True), ('1998', False), ('2000', False)
                        ]
                    },
                    {
                        'text_uz': 'Python-da ro\'yxat (list) qanday belgilanadi?',
                        'choices': [
                            ('()', False), ('{}', False), ('[]', True), ('<>', False)
                        ]
                    },
                    {
                        'text_uz': 'Python-da qaysi kalit so\'z funksiya e\'lon qilish uchun ishlatiladi?',
                        'choices': [
                            ('function', False), ('func', False), ('def', True), ('fn', False)
                        ]
                    },
                    {
                        'text_uz': 'Python-da qaysi ma\'lumot turi o\'zgarmas (immutable)?',
                        'choices': [
                            ('list', False), ('dict', False), ('set', False), ('tuple', True)
                        ]
                    },
                    {
                        'text_uz': 'print() funksiyasi nima qiladi?',
                        'choices': [
                            ('Faylga yozadi', False), ('Ekranga chiqaradi', True), ('O\'qiydi', False), ('O\'chiradi', False)
                        ]
                    },
                ]
            },
            {
                'title_uz': 'O\'zbekiston tarixi — mustaqillik davri',
                'description_uz': 'O\'zbekiston mustaqilligiga oid bilimlarni sinab ko\'ring',
                'category': 'history',
                'difficulty': 'medium',
                'time_limit': 25,
                'questions': [
                    {
                        'text_uz': 'O\'zbekiston mustaqilligini qachon e\'lon qildi?',
                        'choices': [
                            ('1989-yil', False), ('1991-yil', True), ('1992-yil', False), ('1993-yil', False)
                        ]
                    },
                    {
                        'text_uz': 'O\'zbekistonning poytaxti qaysi shahar?',
                        'choices': [
                            ('Samarqand', False), ('Buxoro', False), ('Toshkent', True), ('Namangan', False)
                        ]
                    },
                    {
                        'text_uz': 'O\'zbekistonning birinchi Prezidenti kim edi?',
                        'choices': [
                            ('Sh. Mirziyoyev', False), ('I. Karimov', True), ('A. Aripov', False), ('R. Inomov', False)
                        ]
                    },
                    {
                        'text_uz': 'O\'zbekiston pul birligi nima?',
                        'choices': [
                            ('Rubl', False), ('Dollar', False), ('So\'m', True), ('Tenge', False)
                        ]
                    },
                    {
                        'text_uz': 'O\'zbekiston qaysi regionda joylashgan?',
                        'choices': [
                            ('Janubiy Osiyo', False), ('Sharqiy Yevropa', False), ('Markaziy Osiyo', True), ('Yaqin Sharq', False)
                        ]
                    },
                ]
            },
            {
                'title_uz': 'Ingliz tili grammatikasi: Past Tenses',
                'description_uz': 'Ingliz tilining o\'tgan zamon shakllarini sinab ko\'ring',
                'category': 'languages',
                'difficulty': 'medium',
                'time_limit': 20,
                'questions': [
                    {
                        'text_uz': '"She ___ a book yesterday." bo\'sh joy uchun to\'g\'ri variant?',
                        'choices': [
                            ('reads', False), ('read', True), ('is reading', False), ('has read', False)
                        ]
                    },
                    {
                        'text_uz': '"I ___ TV when she called." to\'g\'ri shakl?',
                        'choices': [
                            ('watched', False), ('was watching', True), ('am watching', False), ('had watched', False)
                        ]
                    },
                    {
                        'text_uz': 'Past Perfect qachon ishlatiladi?',
                        'choices': [
                            ('Hozirgi ish uchun', False), ('Boshqa o\'tgan voqeadan oldin bo\'lgan ish uchun', True), ('Kelajak uchun', False), ('Odatiy holat uchun', False)
                        ]
                    },
                ]
            },
            {
                'title_uz': 'Kimyo — Davriy jadval elementlari',
                'description_uz': 'Kimyoviy elementlar haqida bilimingizni sinab ko\'ring',
                'category': 'science',
                'difficulty': 'hard',
                'time_limit': 30,
                'questions': [
                    {
                        'text_uz': 'Davriy jadvalni kim kashf etgan?',
                        'choices': [
                            ('Newton', False), ('Einstein', False), ('Mendeleev', True), ('Darwin', False)
                        ]
                    },
                    {
                        'text_uz': 'Suvning kimyoviy formulasi nima?',
                        'choices': [
                            ('CO2', False), ('H2O', True), ('NaCl', False), ('O2', False)
                        ]
                    },
                    {
                        'text_uz': 'Oltin elementining belgisi nima?',
                        'choices': [
                            ('Ag', False), ('Gl', False), ('Au', True), ('Go', False)
                        ]
                    },
                    {
                        'text_uz': 'Eng yengil element qaysi?',
                        'choices': [
                            ('Helium', False), ('Hydrogen', True), ('Lithium', False), ('Carbon', False)
                        ]
                    },
                ]
            },
            {
                'title_uz': 'Matematika — Algebra asoslari',
                'description_uz': 'Algebra bo\'yicha asosiy bilimlaringizni sinab ko\'ring',
                'category': 'mathematics',
                'difficulty': 'easy',
                'time_limit': 15,
                'questions': [
                    {
                        'text_uz': '2x + 4 = 10 tenglamada x nechaga teng?',
                        'choices': [
                            ('2', False), ('3', True), ('4', False), ('5', False)
                        ]
                    },
                    {
                        'text_uz': '√144 = ?',
                        'choices': [
                            ('10', False), ('11', False), ('12', True), ('14', False)
                        ]
                    },
                    {
                        'text_uz': '5² = ?',
                        'choices': [
                            ('10', False), ('15', False), ('20', False), ('25', True)
                        ]
                    },
                ]
            },
        ]

        for qdata in quizzes_data:
            cat = categories[qdata.pop('category')]
            questions_data = qdata.pop('questions')
            quiz = Quiz.objects.create(category=cat, **qdata)
            for i, qinfo in enumerate(questions_data):
                choices_raw = qinfo.pop('choices')
                question = Question.objects.create(quiz=quiz, order=i + 1, **qinfo)
                for ctext, is_correct in choices_raw:
                    Choice.objects.create(question=question, text_uz=ctext, is_correct=is_correct)
            self.stdout.write(f'  Quiz: {quiz.title_uz} ({quiz.questions.count()} questions)')

        # Create demo users with profiles
        avatar_colors = ['#7C5CFC', '#16A34A', '#F59E0B', '#EF4444', '#3B82F6']
        users_data = [
            ('aziz_j', 'Aziz', 'Jurayev', 9840),
            ('malika_n', 'Malika', 'Norova', 8510),
            ('sardor_k', 'Sardor', 'Karimov', 7290),
        ]
        for i, (uname, fname, lname, pts) in enumerate(users_data):
            if not User.objects.filter(username=uname).exists():
                u = User.objects.create_user(uname, password='demo1234', first_name=fname, last_name=lname)
                UserProfile.objects.create(user=u, total_points=pts, quizzes_taken=random.randint(5, 20), avatar_color=avatar_colors[i])

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))
