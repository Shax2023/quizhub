// main.js — QuizHub yordamchi skript
// Muhim: bu fayl quiz_take.html scriptidan OLDIN yuklanadi

function confirmSubmit(lang, answered, total) {
  const remaining = total - answered;
  let msg = '';
  if (lang === 'uz') msg = remaining > 0 ? `${remaining} ta savol javobsiz qoldi. Baribir topshirasizmi?` : 'Testni yakunlashni tasdiqlaysizmi?';
  else if (lang === 'ru') msg = remaining > 0 ? `${remaining} вопросов без ответа. Всё равно отправить?` : 'Подтвердить завершение теста?';
  else msg = remaining > 0 ? `${remaining} questions unanswered. Submit anyway?` : 'Confirm submitting the quiz?';
  return confirm(msg);
}
