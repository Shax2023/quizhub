import json

with open('test_questions.json', 'r', encoding='utf-8') as f:
    questions_data = json.load(f)

print('JSON parsed successfully!')
print(f'Number of questions: {len(questions_data)}')
print(f'First question text: {questions_data[0]["text_uz"]}')
print(f'Number of choices: {len(questions_data[0]["choices"])}')
print('All checks passed!')
