import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name_uz = models.CharField(max_length=100, verbose_name=_("Nomi (UZ)"))
    name_ru = models.CharField(max_length=100, verbose_name=_("Nomi (RU)"), blank=True)
    name_en = models.CharField(max_length=100, verbose_name=_("Nomi (EN)"), blank=True)
    icon = models.CharField(max_length=50, default='📚', verbose_name=_("Ikonka"))
    bg_color = models.CharField(max_length=20, default='#EEEDFE', verbose_name=_("Fon rangi"))
    icon_color = models.CharField(max_length=20, default='#534AB7', verbose_name=_("Ikonka rangi"))
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Kategoriya")
        verbose_name_plural = _("Kategoriyalar")
        ordering = ['name_uz']

    def __str__(self):
        return self.name_uz

    def get_name(self, lang='uz'):
        if lang == 'ru' and self.name_ru:
            return self.name_ru
        elif lang == 'en' and self.name_en:
            return self.name_en
        return self.name_uz

    def quiz_count(self):
        return self.quizzes.filter(is_active=True).count()


class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', _('Oson')),
        ('medium', _("O'rta")),
        ('hard', _('Qiyin')),
    ]

    title_uz = models.CharField(max_length=255, verbose_name=_("Sarlavha"))
    description_uz = models.TextField(blank=True, verbose_name=_("Tavsif"))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='quizzes', verbose_name=_("Kategoriya"))
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium', verbose_name=_("Qiyinlik"))
    time_limit = models.PositiveIntegerField(default=30, verbose_name=_("Vaqt limiti (daqiqa)"))
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Test")
        verbose_name_plural = _("Testlar")
        ordering = ['-created_at']

    def __str__(self):
        return self.title_uz

    @property
    def title(self):
        return self.title_uz

    @property
    def description(self):
        return self.description_uz

    def question_count(self):
        return self.questions.count()

    def average_score(self):
        attempts = self.attempts.filter(completed=True)
        if not attempts.exists():
            return 0
        total = sum(a.score_percentage() for a in attempts)
        return round(total / attempts.count(), 1)

    def attempt_count(self):
        return self.attempts.filter(completed=True).count()

    def rating(self):
        score = self.average_score()
        return round(score / 20, 1)


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name=_("Test"))
    text_uz = models.TextField(verbose_name=_("Savol matni"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Tartib"))
    explanation_uz = models.TextField(blank=True, verbose_name=_("Izoh"))

    class Meta:
        verbose_name = _("Savol")
        verbose_name_plural = _("Savollar")
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.quiz.title_uz} — {self.text_uz[:60]}"

    @property
    def text(self):
        return self.text_uz

    @property
    def explanation(self):
        return self.explanation_uz


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices', verbose_name=_("Savol"))
    text_uz = models.CharField(max_length=500, verbose_name=_("Variant matni"))
    is_correct = models.BooleanField(default=False, verbose_name=_("To'g'ri javob"))

    class Meta:
        verbose_name = _("Variant")
        verbose_name_plural = _("Variantlar")

    def __str__(self):
        return f"{self.text_uz} ({'✓' if self.is_correct else '✗'})"

    @property
    def text(self):
        return self.text_uz


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name=_("Foydalanuvchi"))
    total_points = models.IntegerField(default=0, verbose_name=_("Umumiy ball"))
    quizzes_taken = models.IntegerField(default=0, verbose_name=_("O'tilgan testlar"))
    avatar_color = models.CharField(max_length=20, default='#534AB7', verbose_name=_("Avatar rangi"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Foydalanuvchi profili")
        verbose_name_plural = _("Foydalanuvchi profillari")

    def __str__(self):
        return f"{self.user.username} profili"

    def rank(self):
        higher = UserProfile.objects.filter(total_points__gt=self.total_points).count()
        return higher + 1

    def average_score(self):
        attempts = self.user.attempts.filter(completed=True)
        if not attempts.exists():
            return 0
        total = sum(a.score_percentage() for a in attempts)
        return round(total / attempts.count(), 1)

    def initials(self):
        name = self.user.get_full_name() or self.user.username
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return name[:2].upper()


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts', null=True, blank=True, verbose_name=_("Foydalanuvchi"))
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts', verbose_name=_("Test"))
    session_key = models.CharField(max_length=40, blank=True, verbose_name=_("Sessiya kaliti"))
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Boshlangan vaqt"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Tugatilgan vaqt"))
    completed = models.BooleanField(default=False, verbose_name=_("Tugatilgan"))
    score = models.IntegerField(default=0, verbose_name=_("Ball"))
    total_questions = models.IntegerField(default=0, verbose_name=_("Jami savollar"))

    class Meta:
        verbose_name = _("Test urinishi")
        verbose_name_plural = _("Test urinishlari")
        ordering = ['-started_at']

    def __str__(self):
        user_str = self.user.username if self.user else "Anonim"
        return f"{user_str} — {self.quiz.title_uz}"

    def score_percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100, 1)

    def duration_minutes(self):
        if self.completed_at:
            delta = self.completed_at - self.started_at
            return round(delta.total_seconds() / 60, 1)
        return 0

    def get_grade(self):
        pct = self.score_percentage()
        if pct >= 90:
            return ('A', '#16A34A')
        elif pct >= 75:
            return ('B', '#2563EB')
        elif pct >= 60:
            return ('C', '#D97706')
        elif pct >= 40:
            return ('D', '#EA580C')
        return ('F', '#DC2626')


class UserCreatedQuiz(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quizzes', verbose_name=_("Muallif"))
    title = models.CharField(max_length=255, verbose_name=_("Sarlavha"))
    description = models.TextField(blank=True, verbose_name=_("Tavsif"))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='user_quizzes', verbose_name=_("Kategoriya"))
    difficulty = models.CharField(max_length=10, choices=[('easy', _('Oson')), ('medium', _("O'rta")), ('hard', _('Qiyin'))], default='medium')
    time_limit = models.PositiveIntegerField(default=30, verbose_name=_("Vaqt limiti (daqiqa)"))
    is_published = models.BooleanField(default=True, verbose_name=_("Ommaviy (Public)"))
    share_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name=_("Ulashish tokeni"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Foydalanuvchi testi")
        verbose_name_plural = _("Foydalanuvchi testlari")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.author.username})"

    def question_count(self):
        return self.ucq_questions.count()

    def attempt_count(self):
        return self.ucq_attempts.filter(completed=True).count()

    def get_share_url(self):
        return f"/shared/{self.share_token}/"


class UserCreatedAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ucq_attempts', null=True, blank=True)
    quiz = models.ForeignKey(UserCreatedQuiz, on_delete=models.CASCADE, related_name='ucq_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        user_str = self.user.username if self.user else "Anonim"
        return f"{user_str} — {self.quiz.title}"

    def score_percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100, 1)


class UserCreatedQuestion(models.Model):
    quiz = models.ForeignKey(UserCreatedQuiz, on_delete=models.CASCADE, related_name='ucq_questions')
    text = models.TextField(verbose_name=_("Savol matni"))
    order = models.PositiveIntegerField(default=0)
    explanation = models.TextField(blank=True, verbose_name=_("Izoh"))

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:80]


class UserCreatedChoice(models.Model):
    question = models.ForeignKey(UserCreatedQuestion, on_delete=models.CASCADE, related_name='ucq_choices')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers', verbose_name=_("Urinish"))
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name=_("Savol"))
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Tanlangan variant"))
    is_correct = models.BooleanField(default=False, verbose_name=_("To'g'ri"))

    class Meta:
        verbose_name = _("Foydalanuvchi javobi")
        verbose_name_plural = _("Foydalanuvchi javoblari")
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"{self.attempt} — {self.question.text_uz[:40]}"


class SiteSettings(models.Model):
    email_host = models.CharField(max_length=255, default='smtp.gmail.com', verbose_name=_("Email server (SMTP host)"))
    email_port = models.IntegerField(default=587, verbose_name=_("Port"))
    email_use_tls = models.BooleanField(default=True, verbose_name=_("TLS ishlatish"))
    email_use_ssl = models.BooleanField(default=False, verbose_name=_("SSL ishlatish"))
    email_host_user = models.EmailField(blank=True, verbose_name=_("Email manzili (login)"))
    email_host_password = models.CharField(max_length=255, blank=True, verbose_name=_("Email paroli (App Password)"))
    admin_email = models.EmailField(blank=True, verbose_name=_("Admin email manzili"))
    site_name = models.CharField(max_length=100, default='QuizHub', verbose_name=_("Sayt nomi"))
    site_url = models.URLField(blank=True, verbose_name=_("Sayt URL manzili"))
    gemini_api_key = models.CharField(
        max_length=255, blank=True,
        verbose_name=_("Google Gemini API kaliti"),
        help_text=_("Google AI Studio dan olingan API kalit. Fayl yuklashda AI tahlil uchun ishlatiladi.")
    )

    class Meta:
        verbose_name = _("Sayt sozlamalari")
        verbose_name_plural = _("Sayt sozlamalari")

    def __str__(self):
        return "Sayt sozlamalari"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class QuizUploadRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', _("Kutilmoqda")),
        ('processing', _("Ko'rib chiqilmoqda")),
        ('done', _("Bajarildi")),
        ('rejected', _("Rad etildi")),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Foydalanuvchi"))
    user_email = models.EmailField(blank=True, verbose_name=_("Email"))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name=_("Kategoriya"))
    quiz_title = models.CharField(max_length=255, verbose_name=_("Test nomi"))
    time_limit = models.PositiveIntegerField(default=30, verbose_name=_("Vaqt limiti (daqiqa)"))
    upload_file = models.FileField(upload_to='quiz_uploads/', verbose_name=_("Fayl"))
    note = models.TextField(blank=True, verbose_name=_("Izoh"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_("Holati"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Quiz yuklash so'rovi")
        verbose_name_plural = _("Quiz yuklash so'rovlari")
        ordering = ['-created_at']

    def __str__(self):
        user_str = self.user.username if self.user else self.user_email or "Anonim"
        return f"{user_str} — {self.quiz_title}"
