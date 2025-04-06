"""
Инициализация и интеграция админ-панели с основным приложением
"""
from flask import Flask
import os
from datetime import timedelta
from database import WoltDatabase

def init_admin(app: Flask):
    """
    Инициализация админ-панели и её регистрация в основном приложении
    
    Args:
        app: Flask-приложение
    """
    # Настраиваем секретный ключ для сессий из .env или используем значение по умолчанию
    app.secret_key = os.getenv('SECRET_KEY', 'qsc_admin_secret_key_2025')
    
    # Настраиваем срок действия сессии (1 день)
    app.permanent_session_lifetime = timedelta(days=1)
    
    # Создаем экземпляр базы данных и добавляем его в конфигурацию приложения
    if 'DATABASE' not in app.config:
        app.config['DATABASE'] = WoltDatabase()
    
    # Настраиваем папку для загрузки файлов
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'uploads')
    
    # Создаем папку для загрузки, если она не существует
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Максимальный размер файла (16 МБ)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    # Разрешенные расширения файлов
    app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'webm', 'ogg'}
    
    # Импортируем Blueprint админ-панели
    from .routes import admin_bp
    
    # Регистрируем Blueprint в приложении
    app.register_blueprint(admin_bp)
    
    return app
