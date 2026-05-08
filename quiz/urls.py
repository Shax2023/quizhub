from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quizzes/<int:quiz_id>/take/', views.quiz_take, name='quiz_take'),
    path('results/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('categories/', views.categories, name='categories'),
    path('profile/', views.profile, name='profile'),
    path('set-theme/', views.set_theme, name='set_theme'),
    path('set-language/', views.set_language, name='set_language'),

    # User quiz creation
    path('my-quizzes/', views.my_quizzes, name='my_quizzes'),
    path('my-quizzes/create/', views.user_quiz_create, name='user_quiz_create'),
    path('my-quizzes/<int:quiz_id>/edit/', views.user_quiz_edit, name='user_quiz_edit'),
    path('my-quizzes/<int:quiz_id>/add-question/', views.user_quiz_add_question, name='user_quiz_add_question'),
    path('my-quizzes/<int:quiz_id>/delete-question/<int:question_id>/', views.user_quiz_delete_question, name='user_quiz_delete_question'),
    path('my-quizzes/<int:quiz_id>/delete/', views.user_quiz_delete, name='user_quiz_delete'),

    # Public user quizzes
    path('community/', views.public_quizzes, name='public_quizzes'),
    path('community/<int:quiz_id>/', views.user_quiz_detail, name='user_quiz_detail'),
    path('community/<int:quiz_id>/take/', views.user_quiz_take, name='user_quiz_take'),
]
