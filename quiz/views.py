import json
import random
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Count, Q
from django.utils.translation import gettext as _
from django.core.mail import send_mail
from django.conf import settings as django_settings
from .models import (Category, Quiz, Question, Choice, UserProfile, QuizAttempt, UserAnswer,
                     UserCreatedQuiz, UserCreatedQuestion, UserCreatedChoice, UserCreatedAttempt,
                     SiteSettings, QuizUploadRequest)
from .forms import RegisterForm, UserQuizForm, QuizUploadRequestForm


def get_lang(request):
    lang = request.session.get('quiz_lang', 'uz')
    return lang


def home(request):
    lang = get_lang(request)
    categories = Category.objects.annotate(
        active_quiz_count=Count('quizzes', filter=Q(quizzes__is_active=True))
    ).order_by('name_uz')

    popular_quizzes = Quiz.objects.filter(is_active=True).annotate(
        attempt_count=Count('attempts', filter=Q(attempts__completed=True))
    ).order_by('-attempt_count')[:6]

    top_users = UserProfile.objects.select_related('user').order_by('-total_points')[:5]

    total_quizzes = Quiz.objects.filter(is_active=True).count()
    total_users = User.objects.count()
    total_attempts = QuizAttempt.objects.filter(completed=True).count()

    context = {
        'lang': lang,
        'categories': categories,
        'popular_quizzes': popular_quizzes,
        'top_users': top_users,
        'total_quizzes': total_quizzes,
        'total_users': total_users,
        'total_attempts': total_attempts,
    }
    return render(request, 'home.html', context)


def quiz_list(request):
    lang = get_lang(request)
    category_id = request.GET.get('category')
    difficulty = request.GET.get('difficulty')
    search = request.GET.get('q', '')

    quizzes = Quiz.objects.filter(is_active=True).select_related('category')

    if category_id:
        quizzes = quizzes.filter(category_id=category_id)
    if difficulty:
        quizzes = quizzes.filter(difficulty=difficulty)
    if search:
        quizzes = quizzes.filter(Q(title_uz__icontains=search))

    categories = Category.objects.all()

    context = {
        'lang': lang,
        'quizzes': quizzes,
        'categories': categories,
        'selected_category': category_id,
        'selected_difficulty': difficulty,
        'search': search,
    }
    return render(request, 'quiz/quiz_list.html', context)


def quiz_detail(request, quiz_id):
    lang = get_lang(request)
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    questions = quiz.questions.prefetch_related('choices').order_by('order', 'id')

    user_attempts = []
    if request.user.is_authenticated:
        user_attempts = QuizAttempt.objects.filter(
            user=request.user, quiz=quiz, completed=True
        ).order_by('-started_at')[:5]

    context = {
        'lang': lang,
        'quiz': quiz,
        'questions': questions,
        'user_attempts': user_attempts,
    }
    return render(request, 'quiz/quiz_detail.html', context)


def quiz_take(request, quiz_id):
    lang = get_lang(request)
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    all_questions = list(quiz.questions.prefetch_related('choices').order_by('order', 'id'))

    if not all_questions:
        messages.error(request, _("Bu testda savollar yo'q."))
        return redirect('quiz_detail', quiz_id=quiz_id)

    if request.method == 'POST':
        if not request.session.session_key:
            request.session.create()

        question_ids = request.POST.get('question_ids', '')
        selected_ids = [int(pk) for pk in question_ids.split(',') if pk.strip().isdigit()]
        questions = list(Question.objects.filter(id__in=selected_ids).prefetch_related('choices'))
        questions.sort(key=lambda q: selected_ids.index(q.id))

        if not questions:
            messages.error(request, _("Savollarni tanlashda xatolik yuz berdi."))
            return redirect('quiz_detail', quiz_id=quiz_id)

        attempt = QuizAttempt.objects.create(
            user=request.user if request.user.is_authenticated else None,
            quiz=quiz,
            session_key=request.session.session_key or '',
            total_questions=len(questions)
        )

        score = 0
        for question in questions:
            choice_id = request.POST.get(f'question_{question.id}')
            choice = None
            is_correct = False

            if choice_id:
                try:
                    choice = Choice.objects.get(id=choice_id, question=question)
                    is_correct = choice.is_correct
                    if is_correct:
                        score += 1
                except Choice.DoesNotExist:
                    pass

            UserAnswer.objects.create(
                attempt=attempt,
                question=question,
                choice=choice,
                is_correct=is_correct
            )

        attempt.score = score
        attempt.completed = True
        attempt.completed_at = timezone.now()
        attempt.save()

        if request.user.is_authenticated:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.total_points += score * 10
            profile.quizzes_taken += 1
            profile.save()

        response = redirect('quiz_result', attempt_id=attempt.id)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return response

    max_questions = len(all_questions)
    default_question_count = min(30, max_questions)
    requested_count = request.GET.get('num_questions', '')
    show_mode = request.GET.get('show_mode', 'end')

    try:
        num_questions = int(requested_count) if requested_count else default_question_count
    except ValueError:
        num_questions = default_question_count

    num_questions = max(1, min(num_questions, max_questions))
    if num_questions < max_questions:
        questions = random.sample(all_questions, num_questions)
    else:
        questions = list(all_questions)
        random.shuffle(questions)

    # Shuffle choices for each question
    for q in questions:
        choices = list(q.choices.all())
        random.shuffle(choices)
        q.shuffled_choices = choices

    selected_question_ids = ','.join(str(question.id) for question in questions)

    context = {
        'lang': lang,
        'quiz': quiz,
        'questions': questions,
        'is_anonymous': not request.user.is_authenticated,
        'questions_count': len(questions),
        'selected_question_ids': selected_question_ids,
        'requested_question_count': num_questions,
        'max_question_count': max_questions,
        'show_mode': show_mode,
    }
    return render(request, 'quiz/quiz_take.html', context)


def quiz_result(request, attempt_id):
    lang = get_lang(request)
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)

    if attempt.user and attempt.user != request.user and not request.user.is_staff:
        return redirect('home')

    answers = attempt.answers.select_related('question', 'choice').prefetch_related(
        'question__choices'
    ).order_by('question__order', 'question__id')

    is_anonymous = attempt.user is None
    grade, grade_color = attempt.get_grade()

    response = render(request, 'quiz/quiz_result.html', {
        'lang': lang,
        'attempt': attempt,
        'answers': answers,
        'is_anonymous': is_anonymous,
        'grade': grade,
        'grade_color': grade_color,
    })
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    response['Pragma'] = 'no-cache'
    return response


def leaderboard(request):
    lang = get_lang(request)
    top_users = UserProfile.objects.select_related('user').order_by('-total_points')[:20]

    context = {
        'lang': lang,
        'top_users': top_users,
    }
    return render(request, 'quiz/leaderboard.html', context)


def categories(request):
    lang = get_lang(request)
    cats = Category.objects.annotate(
        active_quiz_count=Count('quizzes', filter=Q(quizzes__is_active=True))
    ).order_by('name_uz')

    context = {
        'lang': lang,
        'categories': cats,
    }
    return render(request, 'quiz/categories.html', context)


@login_required
def profile(request):
    lang = get_lang(request)
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    recent_attempts = QuizAttempt.objects.filter(
        user=request.user, completed=True
    ).select_related('quiz').order_by('-started_at')[:10]

    context = {
        'lang': lang,
        'user_profile': user_profile,
        'recent_attempts': recent_attempts,
    }
    return render(request, 'accounts/profile.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, _("Muvaffaqiyatli ro'yxatdan o'tdingiz!"))
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'registration/register.html', {'form': form, 'lang': get_lang(request)})


@require_POST
def set_theme(request):
    theme = request.POST.get('theme', 'dark')
    request.session['quiz_theme'] = theme
    return JsonResponse({'theme': theme})


@require_POST
def set_language(request):
    lang = request.POST.get('lang', 'uz')
    if lang in ['uz', 'ru', 'en']:
        request.session['quiz_lang'] = lang
    return JsonResponse({'lang': lang})


# ===== USER QUIZ CREATION =====

@login_required
def my_quizzes(request):
    lang = get_lang(request)
    quizzes = UserCreatedQuiz.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'quiz/my_quizzes.html', {'lang': lang, 'quizzes': quizzes})


@login_required
def user_quiz_create(request):
    lang = get_lang(request)
    if request.method == 'POST':
        form = UserQuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.author = request.user
            quiz.save()
            messages.success(request, _("Test yaratildi! Endi savollar qo'shing."))
            return redirect('user_quiz_edit', quiz_id=quiz.id)
    else:
        form = UserQuizForm()
    return render(request, 'quiz/user_quiz_form.html', {'lang': lang, 'form': form, 'mode': 'create'})


@login_required
def user_quiz_edit(request, quiz_id):
    lang = get_lang(request)
    quiz = get_object_or_404(UserCreatedQuiz, id=quiz_id, author=request.user)

    if request.method == 'POST' and 'save_info' in request.POST:
        form = UserQuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, _("Test ma'lumotlari saqlandi."))
            return redirect('user_quiz_edit', quiz_id=quiz.id)
    else:
        form = UserQuizForm(instance=quiz)

    questions = quiz.ucq_questions.prefetch_related('ucq_choices').all()
    return render(request, 'quiz/user_quiz_edit.html', {
        'lang': lang, 'quiz': quiz, 'form': form, 'questions': questions
    })


@login_required
@require_POST
def user_quiz_add_question(request, quiz_id):
    quiz = get_object_or_404(UserCreatedQuiz, id=quiz_id, author=request.user)
    text = request.POST.get('text', '').strip()
    explanation = request.POST.get('explanation', '').strip()
    choices = request.POST.getlist('choice_text')
    corrects = request.POST.getlist('choice_correct')

    if not text or len(choices) < 2:
        messages.error(request, _("Savol va kamida 2 ta variant kerak."))
        return redirect('user_quiz_edit', quiz_id=quiz.id)

    if not corrects:
        messages.error(request, _("Kamida bitta to'g'ri javob belgilang."))
        return redirect('user_quiz_edit', quiz_id=quiz.id)

    q = UserCreatedQuestion.objects.create(
        quiz=quiz, text=text, explanation=explanation,
        order=quiz.ucq_questions.count()
    )
    for i, ct in enumerate(choices):
        ct = ct.strip()
        if ct:
            UserCreatedChoice.objects.create(
                question=q, text=ct,
                is_correct=(str(i) in corrects)
            )
    messages.success(request, _("Savol qo'shildi."))
    return redirect('user_quiz_edit', quiz_id=quiz.id)


@login_required
@require_POST
def user_quiz_delete_question(request, quiz_id, question_id):
    quiz = get_object_or_404(UserCreatedQuiz, id=quiz_id, author=request.user)
    q = get_object_or_404(UserCreatedQuestion, id=question_id, quiz=quiz)
    q.delete()
    messages.success(request, _("Savol o'chirildi."))
    return redirect('user_quiz_edit', quiz_id=quiz.id)


@login_required
@require_POST
def user_quiz_delete(request, quiz_id):
    quiz = get_object_or_404(UserCreatedQuiz, id=quiz_id, author=request.user)
    quiz.delete()
    messages.success(request, _("Test o'chirildi."))
    return redirect('my_quizzes')


def public_quizzes(request):
    lang = get_lang(request)
    quizzes = UserCreatedQuiz.objects.filter(is_published=True).select_related('author', 'category').order_by('-created_at')
    q = request.GET.get('q', '')
    if q:
        quizzes = quizzes.filter(title__icontains=q)
    return render(request, 'quiz/public_quizzes.html', {'lang': lang, 'quizzes': quizzes, 'search': q})


def user_quiz_detail(request, quiz_id):
    lang = get_lang(request)
    quiz = get_object_or_404(UserCreatedQuiz, id=quiz_id)
    is_author = request.user.is_authenticated and request.user == quiz.author
    if not quiz.is_published and not is_author:
        raise Http404
    return render(request, 'quiz/user_quiz_detail.html', {
        'lang': lang, 'quiz': quiz, 'is_author': is_author
    })


def shared_quiz_detail(request, token):
    """Private quiz via share token"""
    lang = get_lang(request)
    quiz = get_object_or_404(UserCreatedQuiz, share_token=token)
    is_author = request.user.is_authenticated and request.user == quiz.author
    return render(request, 'quiz/user_quiz_detail.html', {
        'lang': lang, 'quiz': quiz, 'is_author': is_author,
        'share_token': str(token), 'via_share': True,
    })


def _take_user_quiz(request, quiz, lang, via_share=False, share_token=None):
    """Shared logic for taking a user-created quiz."""
    all_questions = list(quiz.ucq_questions.all())

    if not all_questions:
        messages.error(request, _("Bu testda savollar yo'q."))
        if via_share:
            return redirect('shared_quiz_detail', token=share_token)
        return redirect('user_quiz_detail', quiz_id=quiz.id)

    if request.method == 'POST':
        show_mode = request.POST.get('show_mode', 'end')
        question_ids = request.POST.get('question_ids', '')
        selected_ids = [int(pk) for pk in question_ids.split(',') if pk.strip().isdigit()]
        questions = list(UserCreatedQuestion.objects.filter(id__in=selected_ids).prefetch_related('ucq_choices'))
        questions.sort(key=lambda q: selected_ids.index(q.id))

        if not questions:
            if via_share:
                return redirect('shared_quiz_detail', token=share_token)
            return redirect('user_quiz_detail', quiz_id=quiz.id)

        results = []
        score = 0
        for question in questions:
            choice_id = request.POST.get(f'question_{question.id}')
            chosen = None
            is_correct = False
            if choice_id:
                try:
                    chosen = UserCreatedChoice.objects.get(id=choice_id, question=question)
                    is_correct = chosen.is_correct
                    if is_correct:
                        score += 1
                except UserCreatedChoice.DoesNotExist:
                    pass
            correct_choice = question.ucq_choices.filter(is_correct=True).first()
            results.append({
                'question': question,
                'chosen': chosen,
                'is_correct': is_correct,
                'correct_choice': correct_choice,
            })

        total = len(questions)
        pct = round((score / total) * 100, 1) if total else 0

        UserCreatedAttempt.objects.create(
            user=request.user if request.user.is_authenticated else None,
            quiz=quiz,
            completed=True,
            completed_at=timezone.now(),
            score=score,
            total_questions=total
        )

        response = render(request, 'quiz/user_quiz_result.html', {
            'lang': lang, 'quiz': quiz, 'results': results,
            'score': score, 'total': total, 'pct': pct
        })
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return response

    # GET - prepare questions with shuffled choices
    show_mode = request.GET.get('show_mode', 'end')
    max_q = len(all_questions)
    num_questions = min(30, max_q)
    try:
        num_questions = int(request.GET.get('num_questions', num_questions))
        num_questions = max(1, min(num_questions, max_q))
    except ValueError:
        pass

    if num_questions < max_q:
        questions = random.sample(all_questions, num_questions)
    else:
        questions = list(all_questions)
        random.shuffle(questions)

    # Prefetch choices and shuffle them
    for q in questions:
        choices = list(UserCreatedChoice.objects.filter(question=q))
        random.shuffle(choices)
        q.shuffled_choices = choices

    selected_ids = ','.join(str(q.id) for q in questions)
    return render(request, 'quiz/user_quiz_take.html', {
        'lang': lang, 'quiz': quiz, 'questions': questions,
        'questions_count': len(questions),
        'selected_question_ids': selected_ids,
        'show_mode': show_mode,
        'is_anonymous': not request.user.is_authenticated,
        'via_share': via_share,
        'share_token': str(share_token) if share_token else '',
    })


def user_quiz_take(request, quiz_id):
    lang = get_lang(request)
    quiz = get_object_or_404(UserCreatedQuiz, id=quiz_id)
    is_author = request.user.is_authenticated and request.user == quiz.author
    if not quiz.is_published and not is_author:
        raise Http404
    return _take_user_quiz(request, quiz, lang)


def shared_quiz_take(request, token):
    lang = get_lang(request)
    quiz = get_object_or_404(UserCreatedQuiz, share_token=token)
    return _take_user_quiz(request, quiz, lang, via_share=True, share_token=token)


# ===== QUIZ FILE UPLOAD =====

def quiz_upload(request):
    """Try to auto-parse uploaded file; on failure, show admin request form."""
    lang = get_lang(request)

    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name.lower()
        parsed = None
        parse_error = None

        try:
            if filename.endswith('.json'):
                parsed = _parse_json_file(uploaded_file)
            elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                parsed = _parse_excel_file(uploaded_file)
            elif filename.endswith('.docx') or filename.endswith('.doc'):
                parsed = _parse_word_file(uploaded_file)
            elif filename.endswith('.pdf'):
                parsed = _parse_pdf_file(uploaded_file)
            else:
                parse_error = _("Noto'g'ri fayl turi. JSON, Excel, Word yoki PDF yuklang.")
        except Exception as e:
            parse_error = str(e)

        if parsed and not parse_error:
            # Auto-import successful
            category_id = request.POST.get('category')
            quiz_title = request.POST.get('quiz_title', uploaded_file.name.rsplit('.', 1)[0])
            time_limit = int(request.POST.get('time_limit', 30))

            try:
                category = Category.objects.get(id=category_id)
            except (Category.DoesNotExist, TypeError, ValueError):
                category = Category.objects.first()

            from .models import UserCreatedQuiz as UCQ, UserCreatedQuestion as UCQn, UserCreatedChoice as UCQc
            quiz = UCQ.objects.create(
                author=request.user if request.user.is_authenticated else User.objects.filter(is_superuser=True).first(),
                title=quiz_title,
                category=category,
                time_limit=time_limit,
                is_published=False,
            )
            for q_data in parsed:
                q = UCQn.objects.create(
                    quiz=quiz,
                    text=q_data.get('text', ''),
                    explanation=q_data.get('explanation', ''),
                    order=q_data.get('order', 0),
                )
                for c_data in q_data.get('choices', []):
                    UCQc.objects.create(
                        question=q,
                        text=c_data.get('text', ''),
                        is_correct=c_data.get('is_correct', False),
                    )
            messages.success(request, _("Test muvaffaqiyatli yuklandi!"))
            if request.user.is_authenticated:
                return redirect('user_quiz_edit', quiz_id=quiz.id)
            return redirect('home')
        else:
            # Auto-parse failed — show the admin request form
            categories = Category.objects.all().order_by('name_uz')
            return render(request, 'quiz/quiz_upload_request.html', {
                'lang': lang,
                'parse_error': parse_error or _("Fayl avtomatik o'qilmadi."),
                'categories': categories,
            })

    categories = Category.objects.all().order_by('name_uz')
    return render(request, 'quiz/quiz_upload.html', {
        'lang': lang, 'categories': categories,
    })


def quiz_upload_request(request):
    """Admin request form for quiz uploads that couldn't be auto-parsed."""
    lang = get_lang(request)
    if request.method == 'POST':
        form = QuizUploadRequestForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            if request.user.is_authenticated:
                obj.user = request.user
                if not obj.user_email:
                    obj.user_email = request.user.email
            obj.save()

            # Send email to admin
            try:
                site_settings = SiteSettings.get_settings()
                admin_email = site_settings.admin_email
                from_email = site_settings.email_host_user or 'noreply@quizhub.uz'
                if admin_email:
                    subject = f"[QuizHub] Yangi quiz yuklash so'rovi: {obj.quiz_title}"
                    body = (
                        f"Foydalanuvchi: {obj.user.username if obj.user else obj.user_email}\n"
                        f"Email: {obj.user_email}\n"
                        f"Test nomi: {obj.quiz_title}\n"
                        f"Kategoriya: {obj.category}\n"
                        f"Vaqt limiti: {obj.time_limit} daqiqa\n"
                        f"Izoh: {obj.note}\n\n"
                        f"Admin panelda ko'rish: /admin/quiz/quizuploadrequest/{obj.id}/change/"
                    )
                    send_mail(subject, body, from_email, [admin_email], fail_silently=True)
            except Exception:
                pass

            messages.success(request, _(
                "So'rovingiz yuborildi! Admin ko'rib chiqib, siz bilan bog'lanadi."
            ))
            return redirect('home')
    else:
        initial = {}
        if request.user.is_authenticated:
            initial['user_email'] = request.user.email
        form = QuizUploadRequestForm(initial=initial)

    return render(request, 'quiz/quiz_upload_request.html', {
        'lang': lang, 'form': form,
    })


def _parse_json_file(f):
    data = json.loads(f.read().decode('utf-8'))
    if isinstance(data, dict):
        data = [data]
    result = []
    for item in data:
        choices = []
        for c in item.get('choices', []):
            choices.append({'text': c.get('text', c.get('text_uz', '')), 'is_correct': c.get('is_correct', False)})
        result.append({
            'text': item.get('text', item.get('text_uz', '')),
            'explanation': item.get('explanation', item.get('explanation_uz', '')),
            'order': item.get('order', 0),
            'choices': choices,
        })
    if not result:
        raise ValueError("JSON bo'sh yoki noto'g'ri formatda.")
    return result


def _parse_excel_file(f):
    try:
        import openpyxl
        wb = openpyxl.load_workbook(f)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise ValueError("Excel fayl bo'sh.")
        result = []
        for row in rows[1:]:  # skip header
            if not row or not row[0]:
                continue
            question_text = str(row[0]).strip()
            choices = []
            correct_idx = None
            try:
                correct_idx = int(row[-1]) - 1 if row[-1] else None
            except (TypeError, ValueError):
                pass
            for i, cell in enumerate(row[1:-1]):
                if cell:
                    choices.append({
                        'text': str(cell).strip(),
                        'is_correct': (i == correct_idx),
                    })
            if question_text and choices:
                result.append({'text': question_text, 'explanation': '', 'order': 0, 'choices': choices})
        if not result:
            raise ValueError("Excel faylda savollar topilmadi.")
        return result
    except ImportError:
        raise ValueError("Excel fayllarni o'qish uchun openpyxl kutubxonasi kerak.")


def _parse_word_file(f):
    try:
        import docx
        doc = docx.Document(f)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        if not paragraphs:
            raise ValueError("Word fayl bo'sh.")
        result = []
        i = 0
        while i < len(paragraphs):
            q_text = paragraphs[i]
            i += 1
            choices = []
            while i < len(paragraphs) and paragraphs[i] and paragraphs[i][0] in 'ABCDabcd+-*':
                line = paragraphs[i]
                is_correct = line.startswith('+') or line.startswith('*')
                text = line[1:].strip() if line[0] in '+-*' else line[2:].strip()
                choices.append({'text': text, 'is_correct': is_correct})
                i += 1
            if choices:
                result.append({'text': q_text, 'explanation': '', 'order': 0, 'choices': choices})
        if not result:
            raise ValueError("Word faylda savollar topilmadi.")
        return result
    except ImportError:
        raise ValueError("Word fayllarni o'qish uchun python-docx kutubxonasi kerak.")


def _parse_pdf_file(f):
    try:
        import pypdf
        reader = pypdf.PdfReader(f)
        text = ''
        for page in reader.pages:
            text += page.extract_text() or ''
        if not text.strip():
            raise ValueError("PDF fayldan matn o'qilmadi.")
        raise ValueError("PDF avtomatik o'qilmadi. Iltimos, qo'lda so'rov yuboring.")
    except ImportError:
        raise ValueError("PDF fayllarni o'qish uchun pypdf kutubxonasi kerak.")
