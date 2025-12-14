import os
import subprocess
import glob

def convert_videos():
    # Поддерживаемые форматы видеофайлов
    video_extensions = ['*.mp4', '*.mov', '*.avi', '*.mkv', '*.flv', '*.wmv', '*.webm', '*.m4v']
    video_files = []
    
    # Сбор всех видеофайлов в текущей директории
    for ext in video_extensions:
        video_files.extend(glob.glob(ext))
    
    if not video_files:
        print("Видеофайлы не найдены.")
        return

    # Создаем папку для результатов
    output_dir = "converted"
    os.makedirs(output_dir, exist_ok=True)

    for input_file in video_files:
        output_file = os.path.join(
            output_dir,
            f"{os.path.splitext(input_file)[0]}_converted.mp4"
        )

        # Параметры конвертации:
        # -c:v libx264    → кодек видео H.264
        # -preset medium  → баланс скорость/качество
        # -crf 23         → качество (0-51, меньше = лучше)
        # -c:a aac        → кодек аудио AAC
        # -b:a 128k       → битрейт аудио
        # -movflags +faststart → перемотка в браузерах
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            output_file
        ]

        try:
            print(f"Конвертирую: {input_file}")
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Успешно: {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка при конвертации {input_file}: {e}")
        except FileNotFoundError:
            print("Ошибка: ffmpeg не найден. Установите ffmpeg и добавьте в PATH.")
            return

if __name__ == "__main__":
    convert_videos()
