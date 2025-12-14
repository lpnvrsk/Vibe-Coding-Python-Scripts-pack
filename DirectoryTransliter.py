import os
import re
from pathlib import Path
from collections import defaultdict

def to_translit(text):
    """Функция транслитерации русских символов в латинские"""
    translit_dict = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }
    
    # Разделяем имя и расширение для файлов
    name, ext = os.path.splitext(text)
    
    # Транслитерируем только имя (без расширения)
    translit_name = ''
    for char in name:
        if char in translit_dict:
            translit_name += translit_dict[char]
        else:
            # Оставляем латинские буквы, цифры и разрешенные символы без изменений
            translit_name += char
    
    # Заменяем пробелы и несколько подряд идущих небуквенно-цифровых символов на дефис
    translit_name = re.sub(r'[^\w\-\.]+', '-', translit_name)
    translit_name = re.sub(r'-+', '-', translit_name)
    translit_name = translit_name.strip('-')
    
    # Сохраняем расширение в нижнем регистре
    result = translit_name + ext.lower()
    
    # Если результат пустой (например, было только расширение), возвращаем исходное имя
    return result if translit_name else text

def generate_unique_name(base_name, existing_names, is_file=True):
    """Генерирует уникальное имя с добавлением индекса при конфликте"""
    name_without_ext, ext = os.path.splitext(base_name) if is_file else (base_name, '')
    
    # Проверяем, есть ли уже такое имя
    if base_name not in existing_names:
        return base_name
    
    # Генерируем уникальное имя с индексом
    counter = 1
    while True:
        new_name = f"{name_without_ext}_{counter}{ext}" if is_file else f"{name_without_ext}_{counter}"
        if new_name not in existing_names:
            return new_name
        counter += 1

def collect_and_rename(root_path):
    """Собирает все пути и переименовывает файлы/папки в транслит"""
    
    # Собираем все файлы и папки рекурсивно
    all_items = []
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        # Сначала файлы, потом папки (важно для обработки вложенных элементов)
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root_path)
            all_items.append(('file', full_path, rel_path, filename))
        
        for dirname in dirnames:
            full_path = os.path.join(dirpath, dirname)
            rel_path = os.path.relpath(full_path, root_path)
            all_items.append(('dir', full_path, rel_path, dirname))
    
    # Сортируем по убыванию длины пути (чтобы вложенные элементы обрабатывались первыми)
    all_items.sort(key=lambda x: len(x[1]), reverse=True)
    
    # Словарь для отслеживания занятых имен в каждой директории
    dir_names = defaultdict(set)
    
    # Списки для записи в файлы
    original_entries = []
    conflict_entries = []
    non_conflict_files = []
    
    # Сначала проходим и собираем информацию о будущих именах
    rename_plan = []
    
    for item_type, full_path, rel_path, original_name in all_items:
        parent_dir = os.path.dirname(full_path)
        
        # Генерируем транслитерированное имя
        translit_name = to_translit(original_name)
        
        # Получаем список уже занятых имен в этой директории
        existing_names = dir_names[parent_dir]
        
        # Проверяем, является ли это файлом
        is_file = (item_type == 'file')
        
        # Генерируем уникальное имя (с индексом если нужно)
        final_name = generate_unique_name(translit_name, existing_names, is_file)
        
        # Добавляем имя в список занятых для этой директории
        dir_names[parent_dir].add(final_name)
        
        # Формируем новый путь
        new_full_path = os.path.join(parent_dir, final_name)
        
        # Запоминаем операцию переименования
        rename_plan.append((item_type, full_path, new_full_path, original_name, final_name, rel_path))
        
        # Формируем запись для оригинальных имен
        original_entry = f"{rel_path} -> {os.path.relpath(new_full_path, root_path)}"
        original_entries.append(original_entry)
        
        # Проверяем, был ли конфликт
        if translit_name != final_name:
            # Конфликт был - добавляем индекс
            conflict_entry = f"{rel_path} -> {os.path.relpath(new_full_path, root_path)}"
            conflict_entries.append(conflict_entry)
        elif is_file:
            # Файл без конфликта
            non_conflict_files.append(rel_path)
    
    # Теперь выполняем переименование
    for item_type, old_path, new_path, original_name, final_name, rel_path in rename_plan:
        try:
            # Переименовываем файл или папку
            os.rename(old_path, new_path)
            print(f"Переименован: {original_name} -> {final_name}")
            
        except Exception as e:
            print(f"Ошибка при переименовании {old_path}: {e}")
            # Обновляем запись в списке ошибкой
            for i, entry in enumerate(original_entries):
                if entry.startswith(rel_path):
                    original_entries[i] = f"ОШИБКА: {entry} - {e}"
                    break
    
    # Записываем результаты в файлы
    original_names_file = os.path.join(root_path, 'original_names.txt')
    conflicts_file = os.path.join(root_path, 'conflicts.txt')
    
    # Записываем все переименования
    with open(original_names_file, 'w', encoding='utf-8') as f:
        f.write("ПОЛНЫЙ СПИСОК ПЕРЕИМЕНОВАНИЙ:\n")
        f.write("=" * 80 + "\n\n")
        
        for entry in original_entries:
            f.write(f"{entry}\n")
    
    # Записываем конфликты отдельно
    if conflict_entries:
        with open(conflicts_file, 'w', encoding='utf-8') as f:
            f.write("КОНФЛИКТЫ ИМЕН (добавлены индексы):\n")
            f.write("=" * 80 + "\n\n")
            
            for entry in conflict_entries:
                f.write(f"{entry}\n")
        
        print(f"\nОбнаружено конфликтов: {len(conflict_entries)}")
        print(f"Список конфликтов сохранен в: {conflicts_file}")
    else:
        # Если файл конфликтов существует от предыдущего запуска, удаляем его
        if os.path.exists(conflicts_file):
            os.remove(conflicts_file)
    
    # Записываем файлы без конфликтов
    non_conflict_file = os.path.join(root_path, 'non_conflict_files.txt')
    with open(non_conflict_file, 'w', encoding='utf-8') as f:
        f.write("ФАЙЛЫ БЕЗ КОНФЛИКТОВ:\n")
        f.write("=" * 80 + "\n\n")
        
        for file_path in sorted(non_conflict_files):
            f.write(f"{file_path}\n")
    
    return len(conflict_entries), len(rename_plan)

def main():
    """Основная функция"""
    print("=== Транслитерация имен файлов и папок ===")
    print("Введите путь к папке для обработки:")
    
    while True:
        folder_path = input("Путь: ").strip()
        
        if not folder_path:
            print("Путь не может быть пустым. Попробуйте снова.")
            continue
            
        # Обрабатываем пути с кавычками
        folder_path = folder_path.strip('"\'')
        
        # Преобразуем в абсолютный путь
        folder_path = os.path.abspath(folder_path)
        
        if not os.path.exists(folder_path):
            print(f"Ошибка: Папка '{folder_path}' не существует.")
            print("Введите корректный путь:")
            continue
            
        if not os.path.isdir(folder_path):
            print(f"Ошибка: '{folder_path}' не является папкой.")
            print("Введите путь к папке:")
            continue
            
        break
    
    print(f"\nОбрабатываемая папка: {folder_path}")
    print("Собираю информацию о файлах и папках...")
    
    try:
        conflict_count, total_count = collect_and_rename(folder_path)
        
        print("\n" + "=" * 80)
        print("Обработка завершена!")
        print(f"Всего обработано элементов: {total_count}")
        print(f"Конфликтов имен: {conflict_count}")
        print(f"Оригинальные имена сохранены в: {os.path.join(folder_path, 'original_names.txt')}")
        print(f"Файлы без конфликтов в: {os.path.join(folder_path, 'non_conflict_files.txt')}")
        
        if conflict_count > 0:
            print(f"Конфликты сохранены в: {os.path.join(folder_path, 'conflicts.txt')}")
        
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")

if __name__ == "__main__":
    main()
