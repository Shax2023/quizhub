import json
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Avg
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from unfold.decorators import display
from .models import Category, Quiz, Question, Choice, UserProfile, QuizAttempt, UserAnswer
from .forms import JsonImportForm


class ChoiceInline(TabularInline):
    model = Choice
    extra = 4
    fields = ['text_uz', 'is_correct']


class QuestionInline(StackedInline):
    model = Question
    extra = 1
    fields = ['text_uz', 'order', 'explanation_uz']
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ['name_uz', 'icon', 'quiz_count_display', 'bg_color']
    search_fields = ['name_uz', 'name_ru', 'name_en']
    fields = ['name_uz', 'name_ru', 'name_en', 'icon', 'bg_color', 'icon_color', 'slug']

    @display(description=_("Testlar soni"), ordering='quiz_count')
    def quiz_count_display(self, obj):
        count = obj.quizzes.filter(is_active=True).count()
        return format_html('<span style="font-weight:600;">{} ta</span>', count)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(quiz_count=Count('quizzes'))


@admin.register(Quiz)
class QuizAdmin(ModelAdmin):
    list_display = ['title_uz', 'category', 'difficulty', 'question_count_display', 'attempt_count_display', 'avg_score_display', 'is_active']
    list_filter = ['category', 'difficulty', 'is_active']
    search_fields = ['title_uz']
    inlines = [QuestionInline]
    list_editable = ['is_active']
    fields = [
        'title_uz',
        'description_uz',
        'category', 'difficulty', 'time_limit', 'is_active'
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('import-json/', self.admin_site.admin_view(self.import_json_view), name='quiz_quiz_import_json'),
        ]
        return custom + urls

    def import_json_view(self, request):
        if request.method == 'POST':
            form = JsonImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    # Quiz ma'lumotlari formadan olinadi
                    title_uz = request.POST.get('title_uz', '').strip()
                    description_uz = request.POST.get('description_uz', '').strip()
                    category_id = request.POST.get('category')
                    difficulty = request.POST.get('difficulty', 'medium')
                    time_limit = request.POST.get('time_limit', 30)

                    # Validatsiya
                    if not title_uz:
                        self.message_user(request, "Test nomi majburiy!", level=messages.ERROR)
                        form = JsonImportForm()
                        context = {
                            **self.admin_site.each_context(request),
                            'form': form,
                            'title': 'JSON dan test va savollarni yuklash',
                            'opts': self.model._meta,
                        }
                        return render(request, 'admin/quiz/quiz/import_json.html', context)

                    if not category_id:
                        self.message_user(request, "Kategoriya tanlash majburiy!", level=messages.ERROR)
                        form = JsonImportForm()
                        context = {
                            **self.admin_site.each_context(request),
                            'form': form,
                            'title': 'JSON dan test va savollarni yuklash',
                            'opts': self.model._meta,
                        }
                        return render(request, 'admin/quiz/quiz/import_json.html', context)

                    try:
                        category = Category.objects.get(id=category_id)
                    except Category.DoesNotExist:
                        self.message_user(request, "Kategoriya topilmadi!", level=messages.ERROR)
                        form = JsonImportForm()
                        context = {
                            **self.admin_site.each_context(request),
                            'form': form,
                            'title': 'JSON dan test va savollarni yuklash',
                            'opts': self.model._meta,
                        }
                        return render(request, 'admin/quiz/quiz/import_json.html', context)

                    # JSON faylni o'qish (faqat savollar)
                    questions_data = json.loads(request.FILES['json_file'].read().decode('utf-8'))
                    if isinstance(questions_data, dict):
                        questions_data = [questions_data]

                    # Test yaratish
                    quiz = Quiz.objects.create(
                        title_uz=title_uz,
                        description_uz=description_uz,
                        category=category,
                        difficulty=difficulty,
                        time_limit=int(time_limit),
                        is_active=True,
                    )

                    total_questions = 0
                    for q_data in questions_data:
                        question = Question.objects.create(
                            quiz=quiz,
                            text_uz=q_data.get('text_uz', ''),
                            explanation_uz=q_data.get('explanation_uz', ''),
                            order=q_data.get('order', 0),
                        )
                        total_questions += 1

                        for c_data in q_data.get('choices', []):
                            Choice.objects.create(
                                question=question,
                                text_uz=c_data.get('text_uz', ''),
                                is_correct=c_data.get('is_correct', False),
                            )

                    self.message_user(
                        request,
                        f"Muvaffaqiyatli yuklandi: 1 test, {total_questions} ta savol",
                        level=messages.SUCCESS
                    )
                    return HttpResponseRedirect(reverse('admin:quiz_quiz_changelist'))

                except json.JSONDecodeError as e:
                    self.message_user(request, f"JSON xatosi: {e}", level=messages.ERROR)
                except Exception as e:
                    self.message_user(request, f"Xatolik: {e}", level=messages.ERROR)
        else:
            form = JsonImportForm()

        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'categories': Category.objects.all().order_by('name_uz'),
            'title': 'JSON dan test va savollarni yuklash',
            'opts': self.model._meta,
        }
        return render(request, 'admin/quiz/quiz/import_json.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_json_url'] = reverse('admin:quiz_quiz_import_json')
        return super().changelist_view(request, extra_context=extra_context)

    @display(description=_("Savollar"), ordering='question_count')
    def question_count_display(self, obj):
        return format_html('<span style="font-weight:600;">{}</span>', obj.questions.count())

    @display(description=_("Urinishlar"), ordering='attempt_count')
    def attempt_count_display(self, obj):
        return obj.attempts.filter(completed=True).count()

    @display(description=_("O'rtacha ball"))
    def avg_score_display(self, obj):
        avg = obj.average_score()
        color = '#16A34A' if avg >= 70 else '#EA580C' if avg >= 40 else '#DC2626'
        return format_html('<span style="color:{};font-weight:600;">{}%</span>', color, avg)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(question_count=Count('questions'), attempt_count=Count('attempts'))


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = ['short_text', 'quiz', 'order', 'choice_count']
    list_filter = ['quiz__category']
    search_fields = ['text_uz']
    inlines = [ChoiceInline]
    ordering = ['quiz', 'order']

    @display(description=_("Savol matni"))
    def short_text(self, obj):
        return obj.text_uz[:80] + ('...' if len(obj.text_uz) > 80 else '')

    @display(description=_("Variantlar"))
    def choice_count(self, obj):
        return obj.choices.count()


@admin.register(Choice)
class ChoiceAdmin(ModelAdmin):
    list_display = ['short_text', 'question', 'is_correct_display']
    list_filter = ['is_correct']
    search_fields = ['text_uz']

    @display(description=_("Variant"))
    def short_text(self, obj):
        return obj.text_uz[:80]

    @display(description=_("To'g'ri"), boolean=True)
    def is_correct_display(self, obj):
        return obj.is_correct


@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ['user', 'total_points', 'quizzes_taken', 'rank_display', 'avg_score_display']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering = ['-total_points']

    @display(description=_("Reyting o'rni"))
    def rank_display(self, obj):
        return format_html('#{}</span>', obj.rank())

    @display(description=_("O'rtacha ball"))
    def avg_score_display(self, obj):
        avg = obj.average_score()
        return f'{avg}%'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(ModelAdmin):
    list_display = ['user_display', 'quiz', 'score_display', 'total_questions', 'completed', 'started_at', 'duration_display']
    list_filter = ['completed', 'quiz__category', 'quiz']
    search_fields = ['user__username', 'quiz__title_uz']
    readonly_fields = ['user', 'quiz', 'session_key', 'started_at', 'completed_at', 'score', 'total_questions', 'completed']
    date_hierarchy = 'started_at'

    @display(description=_("Foydalanuvchi"))
    def user_display(self, obj):
        return obj.user.username if obj.user else format_html('<i style="color:#9CA3AF;">Anonim</i>')

    @display(description=_("Natija"))
    def score_display(self, obj):
        pct = obj.score_percentage()
        grade, color = obj.get_grade()
        return format_html(
            '<span style="color:{};font-weight:600;">{}/{} ({}% — {})</span>',
            color, obj.score, obj.total_questions, pct, grade
        )

    @display(description=_("Davomiyligi"))
    def duration_display(self, obj):
        mins = obj.duration_minutes()
        return f'{mins} min' if mins else '—'

    def has_add_permission(self, request):
        return False
