import os
import re
import shutil
from pathlib import Path
from datetime import datetime

def extract_date_from_name(name):
    """
    Извлекает дату из имени файла или папки
    Возвращает datetime объект или None если дата не найдена
    """
    # Паттерн для папок типа EZSInfo_Name_2025.04.19
    folder_pattern1 = r'(\d{4}\.\d{2}\.\d{2})'
    match = re.search(folder_pattern1, name)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y.%m.%d')
        except ValueError:
            pass
    
    # Паттерн для файлов типа 2025.10.29_1456
    file_pattern1 = r'(\d{4}\.\d{2}\.\d{2})_\d{4}'
    match = re.search(file_pattern1, name)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y.%m.%d')
        except ValueError:
            pass
    
    # Паттерн для файлов типа ezbase_final_251109_0903 или tech_base_251118_2052
    file_pattern2 = r'(\d{2})(\d{2})(\d{2})_\d{4}'
    match = re.search(file_pattern2, name)
    if match:
        try:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            # Предполагаем, что год 25 это 2025 год
            full_year = 2000 + year if year < 100 else year
            return datetime(full_year, month, day)
        except ValueError:
            pass
    
    return None

def is_non_empty_folder(folder_path):
    """Проверяет, что папка не пуста"""
    try:
        return any(folder_path.iterdir())
    except (PermissionError, OSError):
        return False

def main():
    # Текущая директория, можно изменить на нужный путь
    root_path = Path('.')
    
    # Словарь для группировки по датам
    date_groups = {}
    
    print("Сканирую файлы и папки...")
    
    # Обрабатываем папки
    for item in root_path.iterdir():
        if item.is_dir():
            # Пропускаем уже созданные папки с датами (формат YYYY.MM.DD)
            if re.match(r'\d{4}\.\d{2}\.\d{2}', item.name):
                continue
                
            date = extract_date_from_name(item.name)
            if date:
                date_str = date.strftime('%Y.%m.%d')
                if date_str not in date_groups:
                    date_groups[date_str] = {'folders': [], 'files': []}
                
                if is_non_empty_folder(item):
                    date_groups[date_str]['folders'].append(item)
                    print(f"Найдена папка: {item.name} -> дата: {date_str}")
    
    # Обрабатываем файлы
    for item in root_path.iterdir():
        if item.is_file():
            date = extract_date_from_name(item.name)
            if date:
                date_str = date.strftime('%Y.%m.%d')
                if date_str not in date_groups:
                    date_groups[date_str] = {'folders': [], 'files': []}
                
                date_groups[date_str]['files'].append(item)
                print(f"Найден файл: {item.name} -> дата: {date_str}")
    
    print(f"\nНайдено групп по датам: {len(date_groups)}")
    
    # Создаем папки по датам и перемещаем элементы
    moved_count = 0
    
    for date_str, items in date_groups.items():
        target_dir = root_path / date_str
        if not target_dir.exists():
            target_dir.mkdir(parents=True)
            print(f"Создана папка: {date_str}")
        
        # Перемещаем папки
        for folder in items['folders']:
            dest_path = target_dir / folder.name
            if not dest_path.exists():
                try:
                    shutil.move(str(folder), str(dest_path))
                    print(f"Перемещена папка: {folder.name} -> {date_str}/")
                    moved_count += 1
                except Exception as e:
                    print(f"Ошибка при перемещении папки {folder.name}: {e}")
        
        # Перемещаем файлы
        for file in items['files']:
            dest_path = target_dir / file.name
            if not dest_path.exists():
                try:
                    shutil.move(str(file), str(dest_path))
                    print(f"Перемещен файл: {file.name} -> {date_str}/")
                    moved_count += 1
                except Exception as e:
                    print(f"Ошибка при перемещении файла {file.name}: {e}")
    
    print(f"\nГотово! Перемещено элементов: {moved_count}")

if __name__ == "__main__":
    main()
