def theme_and_lang(request):
    theme = request.session.get('quiz_theme', 'dark')
    lang = request.session.get('quiz_lang', 'uz')
    return {
        'current_theme': theme,
        'current_lang': lang,
    }
