"""
Интеграция админ-панели с основным приложением Flask.
Этот модуль отвечает за подключение админ-панели к основному серверу приложения.
"""
from flask import Flask
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def integrate_admin(app: Flask) -> Flask:
    """
    Интегрирует админ-панель с основным Flask-приложением.
    
    Args:
        app: Экземпляр Flask-приложения
        
    Returns:
        Flask: Модифицированное Flask-приложение с интегрированной админ-панелью
    """
    try:
        # Проверяем наличие переменных окружения для админ-панели
        required_env_vars = ['ADMIN_USERNAME', 'ADMIN_PASSWORD']
        for var in required_env_vars:
            if not os.getenv(var):
                logger.warning(f"Переменная окружения {var} не задана. "
                               f"Будет использовано значение по умолчанию.")
        
        # Импортируем и инициализируем админ-панель
        from app.admin.init_admin import init_admin
        app = init_admin(app)
        
        logger.info("Админ-панель успешно интегрирована и доступна по адресу /adminqsc")
        return app
    except Exception as e:
        logger.error(f"Ошибка при интеграции админ-панели: {e}")
        # Возвращаем исходное приложение в случае ошибки
        return app
