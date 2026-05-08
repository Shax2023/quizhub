from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0004_remove_choice_text_en_remove_choice_text_ru_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCreatedQuiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Sarlavha')),
                ('description', models.TextField(blank=True, verbose_name='Tavsif')),
                ('difficulty', models.CharField(choices=[('easy', 'Oson'), ('medium', "O'rta"), ('hard', 'Qiyin')], default='medium', max_length=10)),
                ('time_limit', models.PositiveIntegerField(default=30, verbose_name='Vaqt limiti (daqiqa)')),
                ('is_published', models.BooleanField(default=True, verbose_name='Nashr etilgan')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_quizzes', to=settings.AUTH_USER_MODEL, verbose_name='Muallif')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_quizzes', to='quiz.category', verbose_name='Kategoriya')),
            ],
            options={
                'verbose_name': 'Foydalanuvchi testi',
                'verbose_name_plural': 'Foydalanuvchi testlari',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserCreatedQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Savol matni')),
                ('order', models.PositiveIntegerField(default=0)),
                ('explanation', models.TextField(blank=True, verbose_name='Izoh')),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ucq_questions', to='quiz.usercreatedquiz')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='UserCreatedChoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=500)),
                ('is_correct', models.BooleanField(default=False)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ucq_choices', to='quiz.usercreatedquestion')),
            ],
        ),
    ]
