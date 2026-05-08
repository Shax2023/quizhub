import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Count, Q
from django.utils.translation import gettext as _
from .models import (Category, Quiz, Question, Choice, UserProfile, QuizAttempt, UserAnswer,
                     UserCreatedQuiz, UserCreatedQuestion, UserCreatedChoice, UserCreatedAttempt)
from .forms import RegisterForm, UserQuizForm


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
        quizzes = quizzes.filter(
            Q(title_uz__icontains=search)
        )

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

        # Prevent back-navigation to quiz
        response = redirect('quiz_result', attempt_id=attempt.id)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        return response

    max_questions = len(all_questions)
    default_question_count = min(30, max_questions)
    requested_count = request.GET.get('num_questions', '')
    show_mode = request.GET.get('show_mode', 'end')  # 'instant' or 'end'

    try:
        num_questions = int(requested_count) if requested_count else default_question_count
    except ValueError:
        num_questions = default_question_count

    num_questions = max(1, min(num_questions, max_questions))
    if num_questions < max_questions:
        questions = random.sample(all_questions, num_questions)
    else:
        questions = all_questions

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
    # Prevent back-navigation to quiz take page
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
    """All user-created public quizzes"""
    lang = get_lang(request)
    quizzes = UserCreatedQuiz.objects.filter(is_published=True).select_related('author', 'category').order_by('-created_at')
    q = request.GET.get('q', '')
    if q:
        quizzes = quizzes.filter(title__icontains=q)
    return render(request, 'quiz/public_quizzes.html', {'lang': lang, 'quizzes': quizzes, 'search': q})


def user_quiz_detail(request, quiz_id):
    lang = get_lang(request)
    quiz = get_object_or_404(UserCreatedQuiz, id=quiz_id, is_published=True)
    return render(request, 'quiz/user_quiz_detail.html', {'lang': lang, 'quiz': quiz})


def user_quiz_take(request, quiz_id):
    lang = get_lang(request)
    quiz = get_object_or_404(UserCreatedQuiz, id=quiz_id, is_published=True)
    all_questions = list(quiz.ucq_questions.prefetch_related('ucq_choices').all())

    if not all_questions:
        messages.error(request, _("Bu testda savollar yo'q."))
        return redirect('user_quiz_detail', quiz_id=quiz_id)

    if request.method == 'POST':
        show_mode = request.POST.get('show_mode', 'end')
        question_ids = request.POST.get('question_ids', '')
        selected_ids = [int(pk) for pk in question_ids.split(',') if pk.strip().isdigit()]
        questions = list(UserCreatedQuestion.objects.filter(id__in=selected_ids).prefetch_related('ucq_choices'))
        questions.sort(key=lambda q: selected_ids.index(q.id))

        if not questions:
            return redirect('user_quiz_detail', quiz_id=quiz_id)

        # Build results for instant mode
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

        # Urinishni saqlash
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

    # GET
    show_mode = request.GET.get('show_mode', 'end')
    num_questions = min(30, len(all_questions))
    try:
        num_questions = int(request.GET.get('num_questions', num_questions))
        num_questions = max(1, min(num_questions, len(all_questions)))
    except ValueError:
        pass

    if num_questions < len(all_questions):
        questions = random.sample(all_questions, num_questions)
    else:
        questions = all_questions

    selected_ids = ','.join(str(q.id) for q in questions)
    response = render(request, 'quiz/user_quiz_take.html', {
        'lang': lang, 'quiz': quiz, 'questions': questions,
        'questions_count': len(questions),
        'selected_question_ids': selected_ids,
        'show_mode': show_mode,
        'is_anonymous': not request.user.is_authenticated,
    })
    return response
