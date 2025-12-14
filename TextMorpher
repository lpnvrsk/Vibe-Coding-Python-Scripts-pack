import random
import string

def morpher(text):
    # Определяем возможные наборы символов
    letters = string.ascii_letters
    digits = string.digits
    symbols = string.punctuation
    
    result = []
    
    for char in text:
        if char.isspace():  # Если символ пробел, оставляем его без изменений
            new_char = char
        elif char.isalpha():
            # Если символ буква, выбираем случайную букву и сохраняем регистр
            new_char = random.choice(letters)
            if char.isupper():
                new_char = new_char.upper()
        elif char.isdigit():
            # Если символ цифра, выбираем случайную цифру
            new_char = random.choice(digits)
        else:
            # Остальные символы меняют на случайный спецсимвол
            new_char = random.choice(symbols)
            
        result.append(new_char)
    
    return ''.join(result)

# Получение ввода от пользователя
input_text = input("Введите текст: ")

# Применение преобразования
morphed_text = morpher(input_text)

print(f"Измененный текст:\\n{morphed_text}")
