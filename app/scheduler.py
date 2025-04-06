#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Планировщик задач для автоматической отправки запланированных рассылок
"""
import os
import sys
import time
import logging
import schedule
import threading
from datetime import datetime
from dotenv import load_dotenv
from requests import get

# Добавляем родительскую директорию в путь для импорта
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Импортируем базу данных и функцию отправки рассылок
from database import WoltDatabase
from app.admin.routes import send_telegram_broadcast

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(parent_dir, 'scheduler.log'))
    ]
)
logger = logging.getLogger(__name__)

# Загрузка переменных из .env файла
env_path = os.path.join(parent_dir, '.env')
load_dotenv(dotenv_path=env_path)

# Инициализация базы данных
db = WoltDatabase()

def check_scheduled_broadcasts():
    """
    Проверяет наличие запланированных рассылок и отправляет их, если наступило время
    """
    try:
        logger.info("Проверка запланированных рассылок...")
        
        # Получаем список запланированных рассылок
        broadcasts = db.get_scheduled_broadcasts()
        
        if not broadcasts:
            logger.info("Запланированных рассылок не найдено")
            return
        
        logger.info(f"Найдено {len(broadcasts)} запланированных рассылок")
        
        # Текущее время
        now = datetime.now()
        
        for broadcast in broadcasts:
            try:
                # Проверяем, наступило ли время для отправки
                scheduled_time = broadcast['scheduled_time']
                
                if scheduled_time and scheduled_time <= now:
                    logger.info(f"Отправка запланированной рассылки ID: {broadcast['id']}")
                    
                    # Отправляем рассылку
                    send_telegram_broadcast(broadcast['id'])
                    
                    logger.info(f"Рассылка ID: {broadcast['id']} успешно отправлена")
            except Exception as e:
                logger.error(f"Ошибка при обработке рассылки ID: {broadcast['id']}: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Ошибка при проверке запланированных рассылок: {str(e)}")

def run_app():
    """Запуск приложения планировщика обновления данных от wolt"""
    logger.info("Проверка необходимости обновления данных от Wolt")

    try:
        # Получаем установленное время выполнения
        execution_time_result = db.get_setting('execution_time')
        
        # Обрабатываем формат кортежа ('18:23', None)
        if isinstance(execution_time_result, tuple) and execution_time_result:
            start_time = execution_time_result[0]
        else:
            start_time = execution_time_result
            
        # Текущее время
        now = datetime.now()
        
        # Проверка времени запуска
        should_run = False
        if isinstance(start_time, str) and ":" in start_time:
            hour, minute = map(int, start_time.split(":"))
            should_run = (now.hour == hour and now.minute == minute)
        
        # Запуск обновления данных если время подходит
        if should_run:
            logger.info("Начало обновления данных от Wolt")
            
            # Путь к main.py в родительской директории
            main_script_path = os.path.join(parent_dir, 'main.py')
            
            # Использование текущего интерпретатора Python для запуска main.py
            # и передача переменных окружения из текущего процесса
            import subprocess
            result = subprocess.run([sys.executable, main_script_path], 
                                  env=os.environ.copy())
            
            if result.returncode == 0:
                logger.info("Обновление данных от Wolt успешно выполнено")
            else:
                logger.error(f"Ошибка при обновлении данных от Wolt (код {result.returncode})")
                
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных от Wolt: {str(e)}")

        
def run_threaded(job_func):
    """Запускает функцию в отдельном потоке"""
    job_thread = threading.Thread(target=job_func)
    job_thread.start()

def main():
    """Основная функция планировщика"""
    logger.info("Запуск планировщика задач для автоматической отправки рассылок")
    
    # Планируем проверку каждую минуту
    schedule.every(1).minutes.do(run_threaded, check_scheduled_broadcasts)


    # Планируем выполнение обновления данных от Wolt
    schedule.every(1).minutes.do(run_threaded, run_app)

    # Запускаем проверку сразу при старте
    check_scheduled_broadcasts()
    
    # Запуск приложения планировщика обновления данных от wolt
    run_app()
    
    # Бесконечный цикл для выполнения запланированных задач
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
