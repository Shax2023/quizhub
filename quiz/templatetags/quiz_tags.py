from django import template

register = template.Library()


@register.filter
def get_title(quiz, lang):
    return quiz.title


@register.filter
def get_description(quiz, lang):
    return quiz.description


@register.filter
def get_text(obj, lang):
    return obj.text


@register.filter
def get_explanation(obj, lang):
    return obj.explanation


@register.filter
def get_name(category, lang):
    return category.get_name(lang)


@register.filter
def score_pct(attempt):
    return attempt.score_percentage()


@register.simple_tag
def get_letters(label, index):
    letters = ['A', 'B', 'C', 'D', 'E', 'F']
    if index < len(letters):
        return letters[index]
    return str(index + 1)
