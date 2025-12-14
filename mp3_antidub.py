import os
import hashlib
import shutil
from collections import defaultdict
from pathlib import Path
import mimetypes

def get_file_hash(filepath, chunk_size=8192):
    """Вычисляет MD5 хеш файла для обнаружения дубликатов."""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Ошибка при чтении файла {filepath}: {e}")
        return None

def is_mp3_file(filepath):
    """Проверяет, является ли файл mp3 файлом."""
    return Path(filepath).suffix.lower() == '.mp3'

def extract_artist_from_filename(filename):
    """Извлекает имя исполнителя из имени файла."""
    # Удаляем расширение
    name = Path(filename).stem
    
    # Популярные паттерны именования
    patterns = [' - ', ' – ', ' — ', '__', '_']
    
    for pattern in patterns:
        if pattern in name:
            # Берем часть до разделителя как исполнителя
            parts = name.split(pattern, 1)
            if parts[0].strip():
                return parts[0].strip()
    
    # Если паттерн не найден, пробуем разделить по точке или пробелу
    name_parts = name.replace('.', ' ').split()
    if len(name_parts) > 1:
        # Предполагаем, что первое слово - исполнитель
        return name_parts[0]
    
    return "Unknown_Artist"

def analyze_music_folder(folder_path, dry_run=True):
    """Анализирует папку с музыкой и собирает статистику."""
    folder_path = Path(folder_path).resolve()
    
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Ошибка: Папка '{folder_path}' не существует или не является директорией")
        return None, None, None, None
    
    print("=" * 60)
    print(f"Анализирую папку: {folder_path}")
    if dry_run:
        print("РЕЖИМ DRY RUN (только анализ)")
    else:
        print("РЕЖИМ ВЫПОЛНЕНИЯ (будут внесены изменения)")
    print("=" * 60)
    
    # Словари для хранения данных
    files_by_hash = defaultdict(list)  # Хеш -> список файлов
    artist_stats = defaultdict(lambda: {'count': 0, 'size': 0, 'files': []})
    
    total_files = 0
    mp3_files = 0
    total_size = 0
    
    # Рекурсивно обходим все файлы
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            filepath = Path(root) / file
            total_files += 1
            
            # Пропускаем системные файлы
            if file.startswith('.') or file.startswith('~$'):
                continue
            
            # Проверяем, является ли файл mp3
            if not is_mp3_file(filepath):
                continue
            
            try:
                file_size = filepath.stat().st_size
                mp3_files += 1
                total_size += file_size
                
                # Извлекаем исполнителя
                artist = extract_artist_from_filename(file)
                
                # Добавляем в статистику по исполнителю
                artist_stats[artist]['count'] += 1
                artist_stats[artist]['size'] += file_size
                artist_stats[artist]['files'].append(filepath)
                
                # Вычисляем хеш для поиска дубликатов
                file_hash = get_file_hash(filepath)
                if file_hash:
                    files_by_hash[file_hash].append(filepath)
                    
            except Exception as e:
                print(f"Ошибка при обработке файла {filepath}: {e}")
    
    print(f"\nОбщая статистика:")
    print(f"  Всего файлов в папке: {total_files}")
    print(f"  MP3 файлов: {mp3_files}")
    print(f"  Общий размер MP3 файлов: {total_size / (1024**3):.2f} GB")
    
    # Анализ дубликатов
    print(f"\n{'='*60}")
    print("АНАЛИЗ ДУБЛИКАТОВ:")
    print(f"{'='*60}")
    
    duplicate_hashes = {h: files for h, files in files_by_hash.items() if len(files) > 1}
    total_duplicate_files = 0
    total_duplicate_size = 0
    files_to_delete = []
    
    if duplicate_hashes:
        print(f"Найдено {len(duplicate_hashes)} групп дубликатов:")
        for i, (file_hash, files) in enumerate(duplicate_hashes.items(), 1):
            print(f"\nГруппа {i} (хеш: {file_hash[:8]}...):")
            original_file = files[0]
            original_size = original_file.stat().st_size
            
            for j, filepath in enumerate(files, 1):
                size = filepath.stat().st_size
                rel_path = filepath.relative_to(folder_path)
                if j == 1:
                    print(f"  [ОРИГИНАЛ] {rel_path}")
                    print(f"     Размер: {size / 1024:.1f} KB")
                else:
                    print(f"  [ДУБЛИКАТ] {rel_path}")
                    print(f"     Размер: {size / 1024:.1f} KB")
                    files_to_delete.append(filepath)
            
            # Первый файл считаем оригиналом, остальные - дубликатами
            duplicate_count = len(files) - 1
            duplicate_size = duplicate_count * original_size
            
            total_duplicate_files += duplicate_count
            total_duplicate_size += duplicate_size
            
            print(f"  Будет удалено: {duplicate_count} файлов, "
                  f"освободится: {duplicate_size / (1024**2):.1f} MB")
    else:
        print("Дубликаты не найдены.")
    
    # Анализ по исполнителям
    print(f"\n{'='*60}")
    print("АНАЛИЗ ПО ИСПОЛНИТЕЛЯМ:")
    print(f"{'='*60}")
    
    # Сортируем исполнителей по количеству треков
    sorted_artists = sorted(artist_stats.items(), 
                          key=lambda x: x[1]['count'], 
                          reverse=True)
    
    artists_with_many_tracks = []
    unknown_artist_count = 0
    files_to_move = defaultdict(list)  # Исполнитель -> список файлов для перемещения
    
    print(f"\nВсего исполнителей: {len(sorted_artists)}")
    print(f"\nДетальная статистика по исполнителям:")
    print("-" * 80)
    print(f"{'Исполнитель':<30} {'Треков':<10} {'Размер':<15} {'Действие'}")
    print("-" * 80)
    
    for artist, stats in sorted_artists:
        # Unknown_Artist не трогаем, даже если больше 4 треков
        if artist == "Unknown_Artist":
            unknown_artist_count = stats['count']
            action = "Оставить в общей папке (Unknown_Artist)"
        elif stats['count'] > 4:
            action = f"→ Переместить в папку '{artist}'"
            artists_with_many_tracks.append(artist)
            # Сохраняем файлы для перемещения
            for filepath in stats['files']:
                # Не перемещаем файлы, которые будут удалены как дубликаты
                if filepath not in files_to_delete:
                    files_to_move[artist].append(filepath)
        else:
            action = "Оставить как есть"
        
        print(f"{artist:<30} {stats['count']:<10} "
              f"{stats['size'] / (1024**2):.1f} MB{'':<5} {action}")
    
    # Информация о Unknown_Artist
    if unknown_artist_count > 0:
        print(f"\n{'='*60}")
        print(f"ФАЙЛЫ С НЕОПРЕДЕЛЕННЫМ ИСПОЛНИТЕЛЕМ:")
        print(f"{'='*60}")
        print(f"Файлов с Unknown_Artist: {unknown_artist_count}")
        print("Эти файлы останутся в общей папке и не будут перемещены")
    
    # Подробная информация по исполнителям с большим количеством треков
    if artists_with_many_tracks:
        print(f"\n{'='*60}")
        print(f"ИСПОЛНИТЕЛИ ДЛЯ ПЕРЕМЕЩЕНИЯ (>4 треков, исключая Unknown_Artist):")
        print(f"{'='*60}")
        
        total_move_files = 0
        total_move_size = 0
        
        for artist in artists_with_many_tracks:
            stats = artist_stats[artist]
            move_count = len(files_to_move[artist])
            move_size = sum(f.stat().st_size for f in files_to_move[artist])
            total_move_files += move_count
            total_move_size += move_size
            
            print(f"\n{artist} ({move_count} треков для перемещения, "
                  f"{move_size / (1024**2):.1f} MB):")
            
            for i, filepath in enumerate(files_to_move[artist][:6], 1):  # Показываем первые 6
                print(f"  {i}. {filepath.name}")
            
            if move_count > 6:
                print(f"  ... и ещё {move_count - 6} треков")
            
            print(f"  Будет перемещено в: {folder_path / artist}")
    
    # Сводная статистика
    print(f"\n{'='*60}")
    if dry_run:
        print("СВОДНАЯ СТАТИСТИКА DRY RUN:")
    else:
        print("ПЛАН ДЕЙСТВИЙ:")
    print(f"{'='*60}")
    print(f"Дубликаты:")
    print(f"  - Файлов для удаления: {total_duplicate_files}")
    print(f"  - Будет освобождено: {total_duplicate_size / (1024**3):.2f} GB")
    
    print(f"\nИсполнители:")
    print(f"  - Всего исполнителей: {len(sorted_artists)}")
    print(f"  - Исполнителей для перемещения (>4 треков): {len(artists_with_many_tracks)}")
    print(f"  - Файлов с Unknown_Artist: {unknown_artist_count} (остаются в общей папке)")
    
    if artists_with_many_tracks:
        print(f"\nПапки, которые будут созданы:")
        for artist in artists_with_many_tracks[:10]:  # Показываем первые 10
            print(f"  - {folder_path / artist}")
        if len(artists_with_many_tracks) > 10:
            print(f"  ... и ещё {len(artists_with_many_tracks) - 10} папок")
        
        print(f"\nФайлов для перемещения: {total_move_files}")
        print(f"Общий размер перемещаемых файлов: {total_move_size / (1024**3):.2f} GB")
    
    if dry_run:
        print(f"\n{'='*60}")
        print("РЕЖИМ DRY RUN ЗАВЕРШЕН")
        print("Для выполнения действий запустите скрипт с аргументом --apply")
        print(f"{'='*60}")
    
    return files_to_delete, files_to_move, total_duplicate_size, total_move_size

def execute_changes(folder_path, files_to_delete, files_to_move):
    """Выполняет реальные изменения: удаляет дубликаты и перемещает файлы."""
    folder_path = Path(folder_path).resolve()
    
    print(f"\n{'='*60}")
    print("НАЧИНАЮ ВЫПОЛНЕНИЕ ИЗМЕНЕНИЙ...")
    print(f"{'='*60}")
    
    # 1. Удаляем дубликаты
    if files_to_delete:
        print(f"\nУдаление дубликатов ({len(files_to_delete)} файлов):")
        deleted_count = 0
        deleted_size = 0
        
        for filepath in files_to_delete:
            try:
                if filepath.exists():
                    file_size = filepath.stat().st_size
                    filepath.unlink()
                    deleted_count += 1
                    deleted_size += file_size
                    print(f"  Удалено: {filepath.relative_to(folder_path)}")
                else:
                    print(f"  Файл уже удален: {filepath.relative_to(folder_path)}")
            except Exception as e:
                print(f"  Ошибка при удалении {filepath}: {e}")
        
        print(f"\nУдалено {deleted_count} файлов, "
              f"освобождено {deleted_size / (1024**3):.2f} GB")
    else:
        print("Нет дубликатов для удаления.")
    
    # 2. Перемещаем файлы по исполнителям
    if files_to_move:
        print(f"\nПеремещение файлов по исполнителям:")
        moved_count = 0
        moved_size = 0
        
        for artist, file_list in files_to_move.items():
            if not file_list:
                continue
                
            # Создаем папку для исполнителя
            artist_folder = folder_path / artist
            try:
                artist_folder.mkdir(exist_ok=True)
                print(f"\nСоздана папка: {artist_folder.name}/")
            except Exception as e:
                print(f"Ошибка при создании папки {artist_folder}: {e}")
                continue
            
            # Перемещаем файлы
            for filepath in file_list:
                try:
                    if not filepath.exists():
                        print(f"  Файл не найден (возможно уже удален): {filepath.name}")
                        continue
                    
                    target_path = artist_folder / filepath.name
                    
                    # Если файл с таким именем уже существует в целевой папке
                    if target_path.exists():
                        # Добавляем суффикс
                        name_parts = filepath.stem, filepath.suffix
                        counter = 1
                        while target_path.exists():
                            new_name = f"{name_parts[0]}_{counter}{name_parts[1]}"
                            target_path = artist_folder / new_name
                            counter += 1
                    
                    file_size = filepath.stat().st_size
                    shutil.move(str(filepath), str(target_path))
                    moved_count += 1
                    moved_size += file_size
                    print(f"  Перемещен: {filepath.name} → {artist_folder.name}/")
                    
                except Exception as e:
                    print(f"  Ошибка при перемещении {filepath}: {e}")
        
        print(f"\nПеремещено {moved_count} файлов, "
              f"{moved_size / (1024**3):.2f} GB")
    else:
        print("Нет файлов для перемещения.")
    
    print(f"\n{'='*60}")
    print("ВЫПОЛНЕНИЕ ЗАВЕРШЕНО!")
    print(f"{'='*60}")

def main():
    """Основная функция."""
    import sys
    
    # Определяем режим работы
    dry_run = True
    if '--apply' in sys.argv:
        dry_run = False
        sys.argv.remove('--apply')
    
    # Получаем путь к папке
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = input("Введите путь к папке с музыкой: ").strip()
    
    if not folder_path:
        print("Ошибка: путь не указан")
        return
    
    # Анализируем папку
    files_to_delete, files_to_move, dup_size, move_size = analyze_music_folder(folder_path, dry_run)
    
    # Если не dry run, выполняем изменения
    if not dry_run:
        # Запрашиваем подтверждение
        print(f"\n{'='*60}")
        print("ПОДТВЕРЖДЕНИЕ ДЕЙСТВИЙ")
        print(f"{'='*60}")
        
        if files_to_delete:
            print(f"Будет удалено {len(files_to_delete)} файлов-дубликатов")
            print(f"Будет освобождено: {dup_size / (1024**3):.2f} GB")
        
        total_move_files = sum(len(files) for files in files_to_move.values())
        if total_move_files > 0:
            print(f"Будет перемещено {total_move_files} файлов")
            print(f"Будет создано {len(files_to_move)} папок")
        
        if not files_to_delete and total_move_files == 0:
            print("Нет изменений для выполнения.")
            return
        
        response = input("\nВы уверены, что хотите выполнить эти действия? (yes/no): ").strip().lower()
        
        if response == 'yes' or response == 'y' or response == 'да':
            execute_changes(folder_path, files_to_delete, files_to_move)
        else:
            print("Действия отменены.")
    else:
        # В режиме dry run предлагаем запустить с --apply
        total_changes = len(files_to_delete) + sum(len(files) for files in files_to_move.values())
        if total_changes > 0:
            print(f"\nЧтобы выполнить эти изменения, запустите скрипт с ключом --apply:")
            print(f"python {sys.argv[0]} \"{folder_path}\" --apply")

if __name__ == "__main__":
    main()
