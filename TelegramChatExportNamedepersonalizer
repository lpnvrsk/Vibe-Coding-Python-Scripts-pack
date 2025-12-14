from bs4 import BeautifulSoup
import os
import emoji
from glob import glob

print('message')

# Создаем словарь для отслеживания авторов
author_map = {}
next_author_id = 1

files = glob('messages*.html')
print(files)

# Открываем файл для записи сообщений один раз
with open('AllMessages.md', 'a', encoding='utf-8') as saving_to_text:
    for file in sorted(files):
        if os.path.exists(file):
            print(f'Обрабатывается файл {file}')
            with open(file, 'r', encoding='utf-8') as html_page:
                soup = BeautifulSoup(html_page.read(), 'html.parser')
                messages = soup.find_all('div', class_='message default clearfix')
                for message in messages:
                    messagetext = message.find('div', class_='text')
                    if messagetext is not None:
                        author_name = message.find('div', class_='from_name').get_text()
                        # Присваиваем обезличенное имя автору
                        if author_name not in author_map:
                            author_map[author_name] = f'author{next_author_id}'
                            next_author_id += 1
                        anonymous_author = author_map[author_name]
                        makemessage = (anonymous_author + ':' + messagetext.get_text()).replace('\n', '')
                        makemessage = ' '.join(makemessage.split())
                        makemessage = emoji.demojize(makemessage)
                        saving_to_text.write(makemessage + '\n')
                        print(makemessage)
        else:
            print(f'Файл {file} не найден!')
