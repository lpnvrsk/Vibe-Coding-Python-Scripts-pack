# pip install torch torchvision transformers easyocr pillow
import os
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
import easyocr
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageDescriber:
    def __init__(self):
        """Инициализация моделей"""
        logger.info("Загрузка моделей... Это может занять несколько минут.")
        
        # Инициализация BLIP для генерации описаний
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        
        # Инициализация EasyOCR для распознавания текста
        self.reader = easyocr.Reader(['ru', 'en'])  # Русский и английский
        
        # Проверка доступности GPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.device == "cuda":
            self.model = self.model.to(self.device)
            logger.info("Используется GPU для ускорения обработки")
        else:
            logger.info("Используется CPU, обработка может быть медленной")
        
        logger.info("Модели загружены успешно!")

    def generate_description(self, image_path):
        """Генерирует текстовое описание изображения"""
        try:
            image = Image.open(image_path).convert('RGB')
            
            # Обработка изображения
            inputs = self.processor(image, return_tensors="pt").to(self.device)
            
            # Генерация описания
            with torch.no_grad():
                out = self.model.generate(**inputs, max_length=100, num_beams=5)
            
            description = self.processor.decode(out[0], skip_special_tokens=True)
            return description
            
        except Exception as e:
            return f"Ошибка при генерации описания: {str(e)}"

    def extract_text(self, image_path):
        """Извлекает текст из изображения"""
        try:
            # Распознавание текста
            results = self.reader.readtext(image_path, detail=0)
            
            if results:
                extracted_text = "\n".join(results)
                return extracted_text
            else:
                return "Текст не обнаружен"
                
        except Exception as e:
            return f"Ошибка при распознавании текста: {str(e)}"

    def process_folder(self, input_folder, output_file="описания_картинок.txt"):
        """Обрабатывает все изображения в папке"""
        
        # Поддерживаемые форматы изображений
        supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
        
        # Получаем список файлов
        try:
            files = os.listdir(input_folder)
            image_files = [f for f in files if os.path.splitext(f)[1].lower() in supported_formats]
        except Exception as e:
            logger.error(f"Ошибка при чтении папки: {e}")
            return
        
        if not image_files:
            logger.warning("В указанной папке не найдено поддерживаемых изображений")
            return
        
        logger.info(f"Найдено {len(image_files)} изображений для обработки")
        
        # Обработка изображений
        processed_count = 0
        start_time = time.time()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ОПИСАНИЯ ИЗОБРАЖЕНИЙ\n")
            f.write("=" * 60 + "\n\n")
            
            for filename in image_files:
                image_path = os.path.join(input_folder, filename)
                logger.info(f"Обрабатывается: {filename}")
                
                # Генерация описания
                description = self.generate_description(image_path)
                
                # Извлечение текста
                extracted_text = self.extract_text(image_path)
                
                # Запись результатов в файл
                f.write(f"ФАЙЛ: {filename}\n")
                f.write(f"ОПИСАНИЕ: {description}\n")
                f.write(f"ИЗВЛЕЧЕННЫЙ ТЕКСТ:\n{extracted_text}\n")
                f.write("-" * 50 + "\n\n")
                
                processed_count += 1
                
                # Вывод прогресса
                if processed_count % 5 == 0:
                    elapsed_time = time.time() - start_time
                    logger.info(f"Обработано: {processed_count}/{len(image_files)}. Прошло времени: {elapsed_time:.1f} сек")
        
        total_time = time.time() - start_time
        logger.info(f"Обработка завершена! Обработано {processed_count} изображений за {total_time:.1f} секунд")
        logger.info(f"Результаты сохранены в файл: {output_file}")

def main():
    # Настройки
    INPUT_FOLDER = input("Введите путь к папке с изображениями: ").strip().strip('"')
    OUTPUT_FILE = "описания_картинок.txt"
    
    # Проверка существования папки
    if not os.path.exists(INPUT_FOLDER):
        print(f"Ошибка: Папка '{INPUT_FOLDER}' не существует!")
        return
    
    # Создание экземпляра класса и обработка
    describer = ImageDescriber()
    describer.process_folder(INPUT_FOLDER, OUTPUT_FILE)

if __name__ == "__main__":
    main()
