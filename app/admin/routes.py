"""
Admin Panel Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app, send_from_directory
import os
from functools import wraps
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import datetime
import uuid
from dotenv import load_dotenv
import time
import json
from datetime import datetime
import mysql.connector
import asyncio
import requests
import threading


# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен бота из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Загрузка переменных из .env файла
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(dotenv_path=env_path)

# Получение учетных данных из .env
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# Импортируем базу данных
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)
from database import WoltDatabase

# Создаем Blueprint
admin_bp = Blueprint('admin', __name__, 
                    template_folder='templates',
                    static_folder='static',
                    url_prefix='/adminqsc')

# Инициализация базы данных
db = WoltDatabase()

# Декоратор для проверки авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# Функция для проверки допустимых расширений файлов
def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Маршрут для логина
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            error = 'Неверное имя пользователя или пароль'
    
    # Получаем текущую тему из cookie или используем светлую по умолчанию
    theme = request.cookies.get('admin_theme', 'light')
    
    return render_template('admin/login.html', error=error, theme=theme)

# Маршрут для выхода
@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))

# Главная страница админки
@admin_bp.route('/')
@login_required
def dashboard():
    # Получаем текущую тему из cookie
    theme = request.cookies.get('admin_theme', 'light')
    
    return render_template('admin/dashboard.html', theme=theme)

# Маршрут для настроек
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    db = current_app.config['DATABASE']
    theme = request.cookies.get('admin_theme', 'light')
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'save_proxies':
            proxy_lines = request.form.get('proxyList', '').strip().split('\n')
            proxies = []
            for line in proxy_lines:
                line = line.strip()
                if line and ':' in line:  # Basic validation
                    proxies.append(line)
            
            try:
                db.save_proxies(proxies)
                return jsonify({
                    'success': True, 
                    'message': f'Успешно обработано {len(proxies)} прокси (дубликаты пропущены)'
                })
            except Exception as e:
                return jsonify({
                    'success': False, 
                    'message': f'Ошибка при сохранении прокси: {str(e)}'
                })
        
        elif action == 'save_user_agents':
            user_agents = request.form.get('userAgentList', '').strip().split('\n')
            user_agents = [ua.strip() for ua in user_agents if ua.strip()]
            try:
                db.save_user_agents(user_agents)
                return jsonify({'success': True, 'message': 'User-Agent сохранены'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)})
        
        if action == 'save_delay':
            delay = request.form.get('delayTime', '').strip()
            execution_time = request.form.get('executionTime', '').strip()
            
            try:
                # Преобразуем задержку в число
                delay_int = int(delay) if delay else 0
                db.save_setting('execution_delay', str(delay_int))
                
                # Сохраняем только время (формат HH:MM)
                if execution_time:
                    # Простая проверка формата времени
                    if ':' in execution_time and len(execution_time.split(':')) == 2:
                        db.save_setting('execution_time', execution_time)
                    else:
                        raise ValueError("Неверный формат времени. Используйте HH:MM")
                
                return jsonify({'success': True, 'message': 'Настройки сохранены'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)})
        
        elif action == 'save_all':
            proxies = request.form.get('proxyList', '').strip().split('\n')
            proxies = [p.strip() for p in proxies if p.strip()]
            user_agents = request.form.get('userAgentList', '').strip().split('\n')
            user_agents = [ua.strip() for ua in user_agents if ua.strip()]
            delay = request.form.get('delayTime', '').strip()
            execution_time = request.form.get('executionTime', '').strip()
            
            try:
                db.save_proxies(proxies)
                db.save_user_agents(user_agents)
                if delay:
                    db.save_setting('execution_delay', delay)
                return jsonify({'success': True, 'message': 'Все данные сохранены'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)})
        
        elif action == 'check_proxies':
            from app.admin.check_proxy import check_all_proxies
            import asyncio
            
            try:
                # Запускаем асинхронную функцию в синхронном контексте
                results = asyncio.run(check_all_proxies())
                return jsonify({
                    'success': True,
                    'message': 'Прокси проверены',
                    'results': results
                })
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)})

        elif action == 'delete_bad_proxies':
            try:
                db.delete_bad_proxies()
                return jsonify({'success': True, 'message': 'Неактивные прокси удалены'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)})
        
        elif action == 'delete_all_proxies':
            try:
                db.delete_all_proxies()
                return jsonify({'success': True, 'message': 'Все прокси удалены'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)})
        
        elif action == 'delete_all_user_agents':
            try:
                db.delete_all_user_agents()
                return jsonify({'success': True, 'message': 'Все User-Agent удалены'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)})
        
    # Загружаем данные из базы для отображения
    proxies = db.get_proxies()
    user_agents = db.get_user_agents()
    delay = db.get_setting('execution_delay')
    execution_time = db.get_setting('execution_time')
    
    return render_template('admin/settings.html', 
                         theme=theme,
                         proxies=proxies,
                         user_agents=user_agents,
                         delay=delay,
                         execution_time=execution_time
                         )

@admin_bp.route('/api/proxies')
@login_required
def api_proxies():
    db = current_app.config['DATABASE']
    proxies = db.get_proxies()
    return jsonify([{"proxy": p['proxy'], "status": p['status']} for p in proxies])

@admin_bp.route('/api/user_agents')
@login_required
def api_user_agents():
    db = current_app.config['DATABASE']
    uas = db.get_user_agents()
    return jsonify([{"user_agent": ua['user_agent']} for ua in uas])

@admin_bp.route('/api/delay')
@login_required
def api_delay():
    db = current_app.config['DATABASE']
    delay = db.get_setting('execution_delay')
    execution_time = db.get_setting('execution_time')
    return jsonify({"delay": delay or '', "execution_time": execution_time or ''})

@admin_bp.route('/api/server_time')
@login_required
def get_server_time():
    from datetime import datetime
    return jsonify({
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# Страница рекламы
@admin_bp.route('/ads')
@login_required
def ads():
    # Получаем текущую тему из cookie
    theme = request.cookies.get('admin_theme', 'light')
    
    db = current_app.config['DATABASE']
    ads = db.get_all_ad_preloaders()
    return render_template('admin/ads.html', ads=ads, theme=theme)

@admin_bp.route('/ads/add', methods=['GET', 'POST'])
@login_required
def add_ad():
    """Добавление нового рекламного прелоадера"""

    if request.method == 'GET':
        # Получаем список стран и городов из базы данных
        db = current_app.config['DATABASE']
        countries = db.get_all_countries()
        cities = db.get_all_cities()
        
        return render_template('admin/add_ad.html', countries=countries, cities=cities)
    

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        redirect_url = request.form.get('redirect_url')
        display_time = int(request.form.get('display_time', 5))
        skip_after = int(request.form.get('skip_after', 3))
        priority = int(request.form.get('priority', 50))
        countries = request.form.getlist('country[]')
        
        # Обработка загруженного видео
        video = request.files.get('video')
        if not video:
            flash('Необходимо загрузить видео', 'error')
            return redirect(url_for('admin.ads'))
        
        # Проверка и сохранение файла
        if video and allowed_file(video.filename, {'mp4', 'webm', 'ogg'}):
            filename = secure_filename(video.filename)
            # Генерируем уникальное имя файла
            unique_filename = f"{uuid.uuid4()}_{filename}"
            video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'videos', unique_filename)
            
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            
            video.save(video_path)
            
            # Путь для сохранения в базе данных
            db_video_path = unique_filename
            
            # Сохраняем в базе данных
            db = current_app.config['DATABASE']
            try:
                db.create_ad_preloader(title, description, db_video_path, redirect_url, display_time, skip_after, priority, countries)
                flash('Реклама успешно добавлена', 'success')
            except Exception as e:
                flash(f'Ошибка при добавлении рекламы: {str(e)}', 'error')
        else:
            flash('Недопустимый формат файла. Разрешены только: mp4, webm, ogg', 'error')
        
        return redirect(url_for('admin.ads'))
    
    return render_template('admin/add_ad.html')

@admin_bp.route('/ads/edit/<int:ad_id>', methods=['GET', 'POST'])
@login_required
def edit_ad(ad_id):
    """Редактирование рекламного прелоадера"""
    db = current_app.config['DATABASE']
    ad = db.get_ad_preloader(ad_id)
    
    if not ad:
        flash('Реклама не найдена', 'error')
        return redirect(url_for('admin.ads'))
    
    # Получаем список стран для выпадающего списка
    countries = db.get_all_countries()
    
    # Получаем текущие выбранные страны (разбиваем строку с странами на список)
    selected_countries = []
    if ad['country']:
        selected_countries = ad['country'].split(',')
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        redirect_url = request.form.get('redirect_url')
        display_time = int(request.form.get('display_time', 5))
        skip_after = int(request.form.get('skip_after', 3))
        priority = int(request.form.get('priority', 50))
        
        # Получаем список выбранных стран из формы
        countries_list = request.form.getlist('country[]')
        country_str = ','.join(countries_list) if countries_list else None
        
        # Обработка загруженного видео
        video = request.files.get('video')
        video_path = ad['video_url']  # По умолчанию используем текущий путь
        
        if video and video.filename:
            if allowed_file(video.filename, {'mp4', 'webm', 'ogg'}):
                # Удаляем старый файл, если он существует
                old_video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'videos', ad['video_url'])
                if os.path.exists(old_video_path):
                    try:
                        os.remove(old_video_path)
                    except Exception as e:
                        print(f"Ошибка при удалении старого файла: {str(e)}")
                
                # Сохраняем новый файл
                filename = secure_filename(video.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                new_video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'videos', unique_filename)
                
                # Создаем директорию, если она не существует
                os.makedirs(os.path.dirname(new_video_path), exist_ok=True)
                
                video.save(new_video_path)
                
                # Обновляем путь для сохранения в базе данных
                video_path = unique_filename
            else:
                flash('Недопустимый формат файла. Разрешены только: mp4, webm, ogg', 'error')
                return redirect(url_for('admin.edit_ad', ad_id=ad_id))
        
        # Обновляем запись в базе данных
        try:
            db.update_ad_preloader(ad_id, title, description, video_path, redirect_url, display_time, skip_after, priority, country_str)
            flash('Реклама успешно обновлена', 'success')
        except Exception as e:
            flash(f'Ошибка при обновлении рекламы: {str(e)}', 'error')
        
        return redirect(url_for('admin.ads'))
    
    # Получаем текущую тему
    theme = request.cookies.get('admin_theme', 'light')
    
    # Передаем в шаблон не только объявление, но и списки стран и выбранные страны
    return render_template('admin/edit_ad.html', ad=ad, countries=countries, selected_countries=selected_countries, theme=theme)

@admin_bp.route('/api/ad/delete/<int:ad_id>', methods=['POST'])
@login_required
def delete_ad(ad_id):
    """Удаление рекламного прелоадера"""
    db = current_app.config['DATABASE']
    ad = db.get_ad_preloader(ad_id)
    
    if not ad:
        return jsonify({'success': False, 'message': 'Реклама не найдена'})
    
    # Удаляем файл, если он существует
    video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'videos', ad['video_url'])
    if os.path.exists(video_path):
        try:
            os.remove(video_path)
        except Exception as e:
            print(f"Ошибка при удалении файла: {str(e)}")
    
    # Удаляем запись из базы данных
    try:
        db.delete_ad_preloader(ad_id)
        return jsonify({'success': True, 'message': 'Реклама успешно удалена'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка при удалении рекламы: {str(e)}'})

@admin_bp.route('/api/ad/toggle/<int:ad_id>', methods=['POST'])
@login_required
def toggle_ad(ad_id):
    """Включение/выключение рекламного прелоадера"""
    db = current_app.config['DATABASE']
    ad = db.get_ad_preloader(ad_id)
    
    if not ad:
        return jsonify({'success': False, 'message': 'Реклама не найдена'})
    
    new_status = not ad['is_active']
    
    try:
        db.update_ad_preloader_status(ad_id, new_status)
        status_text = 'активна' if new_status else 'неактивна'
        return jsonify({'success': True, 'is_active': new_status, 'message': f'Реклама теперь {status_text}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

@admin_bp.route('/ads/preview/<int:ad_id>')
@login_required
def preview_ad(ad_id):
    """Предпросмотр рекламного прелоадера"""
    db = current_app.config['DATABASE']
    ad = db.get_ad_preloader(ad_id)
    
    if not ad:
        flash('Реклама не найдена', 'error')
        return redirect(url_for('admin.ads'))
    
    return render_template('admin/ad_preview.html', ad=ad)

@admin_bp.route('/api/ad/view/<int:ad_id>', methods=['POST'])
def record_ad_view(ad_id):
    """API для записи просмотра рекламы"""
    db = current_app.config['DATABASE']
    success = db.increment_ad_views(ad_id)
    return jsonify({'success': success})

@admin_bp.route('/api/ad/click/<int:ad_id>', methods=['POST'])
def record_ad_click(ad_id):
    """API для записи клика по рекламе"""
    db = current_app.config['DATABASE']
    # Проверяем, пришли ли данные в формате JSON
    if request.is_json:
        data = request.get_json()
        ad_id = data.get('ad_id', ad_id)
    
    success = db.increment_ad_clicks(ad_id)
    return jsonify({'success': success})

@admin_bp.route('/api/ad/random')
def get_random_ad():
    """API для получения случайной активной рекламы"""
    country = request.args.get('country', None)
    db = current_app.config['DATABASE']
    
    # Передаем параметр страны в метод get_random_active_ad_preloader
    ad = db.get_random_active_ad_preloader(country)
    
    if not ad:
        return jsonify({'success': False, 'message': 'Нет доступных рекламных материалов'})
    
    # Увеличиваем счетчик просмотров
    db.increment_ad_views(ad['id'])
    
    # Формируем URL для видео
    video_url = url_for('admin.serve_ad_video', filename=os.path.basename(ad['video_url'])) if ad['video_url'] else ''
    
    return jsonify({
        'success': True,
        'ad': {
            'id': ad['id'],
            'title': ad['title'],
            'description': ad['description'],
            'video_url': video_url,
            'redirect_url': ad['redirect_url'],
            'display_time': ad['display_time'],
            'skip_after': ad['skip_after'],
            'country': ad['country']
        }
    })

@admin_bp.route('/videos/<filename>')
def serve_ad_video(filename):
    """Отдает видео файлы рекламы"""
    uploads_dir = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(os.path.join(uploads_dir, 'videos'), filename)

# Страница телеграм рассылки
@admin_bp.route('/telegramSendler', methods=['GET', 'POST'])
@login_required
def telegramSendler():
    if request.method == 'POST':
        # Получаем данные из формы
        recipient = request.form.get('recipient')
        language = request.form.get('language')
        premium = request.form.get('premium')
        activity = request.form.get('activity')
        registration_date = request.form.get('registration_date')
        message = request.form.get('message')
        title = request.form.get('title', 'Рассылка ' + datetime.now().strftime('%d.%m.%Y %H:%M'))
        disable_notification = 'disable_notification' in request.form
        protect_content = 'protect_content' in request.form
        schedule = 'schedule' in request.form
        schedule_time = request.form.get('schedule_time') if schedule else None
        
        # Создаем JSON-объект для фильтра получателей
        recipient_filter = {
            'recipient': recipient,
            'language': language,
            'premium': premium,
            'activity': activity,
            'registration_date': registration_date,
            'disable_notification': disable_notification,
            'protect_content': protect_content
        }
        
        # Получаем медиа-файл, если он был загружен
        media_url = None
        media_type = None
        if 'media' in request.files and request.files['media'].filename:
            media_file = request.files['media']
            
            # Определяем тип медиа
            filename = media_file.filename.lower()
            if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                media_type = 'photo'
            elif filename.endswith(('.mp4', '.avi', '.mov')):
                media_type = 'video'
            elif filename.endswith(('.mp3', '.wav', '.ogg')):
                media_type = 'audio'
            else:
                media_type = 'document'
            
            # Генерируем уникальное имя файла
            filename = secure_filename(media_file.filename)
            timestamp = int(time.time())
            unique_filename = f"{timestamp}_{filename}"
            
            # Определяем путь для сохранения
            save_path = os.path.join('app/static/uploads/telegram', unique_filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Сохраняем файл
            media_file.save(save_path)
            
            # Путь для хранения в базе данных
            media_url = f"static/uploads/telegram/{unique_filename}"
        
        try:
            # Создаем запись о рассылке в базе данных
            broadcast_id = db.create_telegram_broadcast(
                recipient=recipient,
                language=language,
                premium=premium,
                activity=activity,
                registration_date=registration_date,
                message=message,
                disable_notification=disable_notification,
                protect_content=protect_content,
                schedule=schedule,
                schedule_time=schedule_time,
                media_path=media_url
            )
            
            # Если рассылка не запланирована, отправляем сообщения сразу
            if not schedule:
                # Отправляем сообщения пользователям
                send_telegram_broadcast(broadcast_id)
                flash('Рассылка успешно отправлена!', 'success')
            else:
                # Обновляем статус на "запланировано"
                db.update_telegram_broadcast_status(broadcast_id, 'scheduled')
                flash('Рассылка успешно запланирована!', 'success')
            
            return redirect(url_for('admin.telegramSendler'))
        except Exception as e:
            flash(f'Ошибка при создании рассылки: {str(e)}', 'error')
    
    # Получаем список городов из БД
    cities = db.get_unique_cities()
    
    # Получаем список языков из БД
    languages = db.get_unique_languages()
    
    # Получаем историю рассылок
    broadcast_history = db.get_telegram_broadcast_history()
    
    return render_template('admin/telegramSendler.html', 
                          now=datetime.now(),
                          broadcast_history=broadcast_history,
                          cities=cities,  # Передаем список городов в шаблон
                          languages=languages)

# API для оценки охвата рассылки
@admin_bp.route('/estimate_reach', methods=['POST'])
@login_required
def estimate_reach():
    """API-эндпоинт для оценки охвата рассылки"""
    try:
        # Получаем данные из JSON-запроса
        data = request.json
        recipient = data.get('recipient')
        language = data.get('language')
        premium = data.get('premium')
        activity = data.get('activity')
        registration_date = data.get('registration_date')
        
        # Получаем количество пользователей, соответствующих фильтрам
        reach = db.estimate_telegram_reach(
            recipient, language, premium, activity, registration_date
        )
        
        return jsonify({'success': True, 'reach': reach})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API для получения деталей рассылки
@admin_bp.route('/broadcast_details/<int:broadcast_id>', methods=['GET'])
@login_required
def get_broadcast_details(broadcast_id):
    """API-эндпоинт для получения деталей рассылки"""
    try:
        # Получаем данные о рассылке из базы данных
        broadcast = db.get_telegram_broadcast(broadcast_id)
        
        if not broadcast:
            return jsonify({'success': False, 'error': 'Рассылка не найдена'})
        
        # Преобразуем datetime объекты в строки для JSON
        broadcast['created_at'] = broadcast['created_at'].isoformat() if broadcast['created_at'] else None
        broadcast['scheduled_time'] = broadcast['scheduled_time'].isoformat() if broadcast['scheduled_time'] else None
        broadcast['sent_at'] = broadcast['sent_at'].isoformat() if broadcast['sent_at'] else None
        
        # Если есть путь к медиа, формируем полный URL
        if broadcast['media_url']:
            broadcast['media_url'] = url_for('admin.static', filename=broadcast['media_url'].replace('static/', ''), _external=True)
        
        # Обрабатываем JSON-поле recipient_filter
        if broadcast['recipient_filter'] and isinstance(broadcast['recipient_filter'], str):
            try:
                broadcast['recipient_filter'] = json.loads(broadcast['recipient_filter'])
            except json.JSONDecodeError:
                # Если не удалось распарсить JSON, оставляем как есть
                pass
        
        return jsonify({'success': True, 'broadcast': broadcast})
    except Exception as e:
        print(f"Ошибка при получении деталей рассылки: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def send_telegram_broadcast(broadcast_id):
    """Отправляет сообщения пользователям и обновляет статус рассылки"""
    try:
        # Получаем данные о рассылке
        broadcast = db.get_telegram_broadcast(broadcast_id)
        
        if not broadcast:
            raise Exception("Рассылка не найдена")
        
        print(f"Получены данные о рассылке: {broadcast}")
        
        # Получаем список пользователей для рассылки
        recipient_filter = {}
        if broadcast.get('recipient_filter'):
            try:
                if isinstance(broadcast['recipient_filter'], str):
                    recipient_filter = json.loads(broadcast['recipient_filter'])
                else:
                    recipient_filter = broadcast['recipient_filter']
            except json.JSONDecodeError:
                print(f"Ошибка при парсинге JSON recipient_filter: {broadcast['recipient_filter']}")
        
        print(f"Фильтр получателей: {recipient_filter}")
        
        # Обновляем статус рассылки
        db.update_telegram_broadcast_status(broadcast_id, 'in_progress')
        
        # Запускаем отправку в отдельном потоке, чтобы не блокировать основной процесс
        threading.Thread(
            target=_send_broadcast_async,
            args=(broadcast_id, broadcast, recipient_filter),
            daemon=True
        ).start()
        
        return {"success": True, "message": "Рассылка запущена в фоновом режиме"}
    except Exception as e:
        print(f"Ошибка при запуске рассылки: {str(e)}")
        
        # Обновляем статус на "ошибка"
        try:
            db.update_telegram_broadcast_status(broadcast_id, 'error')
        except:
            pass
        
        raise

def _send_broadcast_async(broadcast_id, broadcast, recipient_filter):
    """Асинхронная функция для отправки сообщений большому количеству пользователей"""
    try:
        # Получаем список пользователей для рассылки
        users = db.get_telegram_users_for_broadcast(
            recipient_filter.get('recipient'),
            recipient_filter.get('language'),
            recipient_filter.get('premium'),
            recipient_filter.get('activity'),
            recipient_filter.get('registration_date')
        )
        
        print(f"Найдено {len(users)} пользователей для рассылки")
        
        # Если пользователей нет, завершаем рассылку
        if not users:
            db.update_telegram_broadcast_status(broadcast_id, 'completed')
            print("Рассылка завершена: нет пользователей для отправки")
            return
        
        # Создаем асинхронную функцию для отправки сообщений
        async def send_messages_async():
            # Используем requests для отправки запросов к Telegram API
            bot = requests.Session()
            sent_count = 0
            error_count = 0
            
            # Ограничение скорости отправки: не более 25 сообщений в секунду (с запасом)
            rate_limit = 25
            
            # Разбиваем пользователей на группы по rate_limit
            user_groups = [users[i:i+rate_limit] for i in range(0, len(users), rate_limit)]
            total_groups = len(user_groups)
            
            print(f"Пользователи разбиты на {total_groups} групп по {rate_limit} человек")
            
            for group_idx, user_group in enumerate(user_groups):
                group_start_time = time.time()
                group_sent = 0
                
                print(f"Обработка группы {group_idx+1}/{total_groups} ({len(user_group)} пользователей)")
                
                # Обновляем прогресс рассылки в базе данных каждые 10 групп
                if group_idx % 10 == 0:
                    progress = int((group_idx / total_groups) * 100)
                    db.update_broadcast_progress(broadcast_id, progress)
                
                # Отправляем сообщения пользователям в группе
                for user in user_group:
                    try:
                        # Получаем параметры отправки из recipient_filter
                        disable_notification = recipient_filter.get('disable_notification', False)
                        protect_content = recipient_filter.get('protect_content', False)
                        
                        # Отправляем сообщение
                        if broadcast['media_url']:
                            # Полный путь к медиа-файлу
                            media_path = os.path.join(os.getcwd(), 'app', broadcast['media_url'])
                            
                            # Проверяем существование файла
                            if not os.path.exists(media_path):
                                print(f"Ошибка: файл {media_path} не найден")
                                # Отправляем только текст, если файл не найден
                                response = bot.post(
                                    f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
                                    data={
                                        'chat_id': user['user_id'],
                                        'text': broadcast['message'],
                                        'disable_notification': disable_notification,
                                        'protect_content': protect_content
                                    }
                                )
                                if response.status_code == 200:
                                    sent_count += 1
                                    group_sent += 1
                                continue
                            
                            # Отправляем в зависимости от типа медиа
                            media_type = broadcast['media_type']
                            
                            if media_type == 'photo':
                                # Отправляем фото с текстом
                                with open(media_path, 'rb') as photo:
                                    response = bot.post(
                                        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto',
                                        data={
                                            'chat_id': user['user_id'],
                                            'caption': broadcast['message'],
                                            'disable_notification': disable_notification,
                                            'protect_content': protect_content
                                        },
                                        files={'photo': photo}
                                    )
                            elif media_type == 'video':
                                # Отправляем видео с текстом
                                with open(media_path, 'rb') as video:
                                    response = bot.post(
                                        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo',
                                        data={
                                            'chat_id': user['user_id'],
                                            'caption': broadcast['message'],
                                            'disable_notification': disable_notification,
                                            'protect_content': protect_content
                                        },
                                        files={'video': video}
                                    )
                            elif media_type == 'audio':
                                # Отправляем аудио с текстом
                                with open(media_path, 'rb') as audio:
                                    response = bot.post(
                                        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio',
                                        data={
                                            'chat_id': user['user_id'],
                                            'caption': broadcast['message'],
                                            'disable_notification': disable_notification,
                                            'protect_content': protect_content
                                        },
                                        files={'audio': audio}
                                    )
                            else:
                                # Отправляем документ с текстом
                                with open(media_path, 'rb') as document:
                                    response = bot.post(
                                        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument',
                                        data={
                                            'chat_id': user['user_id'],
                                            'caption': broadcast['message'],
                                            'disable_notification': disable_notification,
                                            'protect_content': protect_content
                                        },
                                        files={'document': document}
                                    )
                        else:
                            # Отправляем только текст
                            response = bot.post(
                                f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
                                data={
                                    'chat_id': user['user_id'],
                                    'text': broadcast['message'],
                                    'disable_notification': disable_notification,
                                    'protect_content': protect_content
                                }
                            )
                        
                        # Проверяем успешность отправки
                        if response.status_code == 200:
                            # Увеличиваем счетчик отправленных сообщений
                            sent_count += 1
                            group_sent += 1
                        elif response.status_code == 429:
                            # Если превышен лимит запросов, получаем время ожидания из ответа
                            resp_json = response.json()
                            retry_after = resp_json.get('parameters', {}).get('retry_after', 5)
                            print(f"Превышен лимит запросов. Ожидание {retry_after} секунд")
                            # Ждем указанное время и повторяем попытку
                            await asyncio.sleep(retry_after)
                            # Повторяем попытку отправки (упрощенно, только текст)
                            retry_response = bot.post(
                                f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
                                data={
                                    'chat_id': user['user_id'],
                                    'text': broadcast['message'],
                                    'disable_notification': disable_notification,
                                    'protect_content': protect_content
                                }
                            )
                            if retry_response.status_code == 200:
                                sent_count += 1
                                group_sent += 1
                        else:
                            error_count += 1
                            print(f"Ошибка при отправке сообщения пользователю {user['user_id']}: {response.text}")
                            
                            # Проверяем, заблокировал ли пользователь бота
                            try:
                                resp_json = response.json()
                                error_description = resp_json.get('description', '').lower()
                                
                                # Коды ошибок, связанные с блокировкой бота пользователем
                                blocked_errors = [
                                    'forbidden: bot was blocked by the user',
                                    'forbidden: user is deactivated',
                                    'forbidden: bot can\'t initiate conversation with a user',
                                    'bot was blocked by the user'
                                ]
                                
                                # Если пользователь заблокировал бота, обновляем статус pm_enabled
                                if any(error in error_description for error in blocked_errors):
                                    print(f"Пользователь {user['user_id']} заблокировал бота. Обновляем статус pm_enabled.")
                                    db.update_user_pm_status(user['user_id'], False)
                            except Exception as e:
                                print(f"Ошибка при обработке ответа API: {str(e)}")
                    except Exception as e:
                        error_count += 1
                        print(f"Ошибка при отправке сообщения пользователю {user['user_id']}: {str(e)}")
                        continue
                
                # Вычисляем, сколько времени заняла отправка группы
                group_time = time.time() - group_start_time
                
                # Если отправка заняла меньше 1 секунды, ждем оставшееся время
                # чтобы соблюдать ограничение API Telegram
                if group_time < 1.0:
                    wait_time = 1.0 - group_time
                    print(f"Ожидание {wait_time:.2f} секунд для соблюдения ограничений API")
                    await asyncio.sleep(wait_time)
                
                print(f"Группа {group_idx+1}: отправлено {group_sent}/{len(user_group)} сообщений за {group_time:.2f} секунд")
            
            # Обновляем статус рассылки
            db.update_telegram_broadcast_status(broadcast_id, 'completed')
            db.update_broadcast_progress(broadcast_id, 100)
            
            print(f"Рассылка завершена: отправлено {sent_count}/{len(users)} сообщений, ошибок: {error_count}")
            
            return sent_count
        
        # Запускаем асинхронную функцию в event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sent_count = loop.run_until_complete(send_messages_async())
        loop.close()
        
        return sent_count
    except Exception as e:
        print(f"Ошибка при отправке рассылки: {str(e)}")
        
        # Обновляем статус на "ошибка"
        try:
            db.update_telegram_broadcast_status(broadcast_id, 'error')
        except:
            pass

# Страница статистики
@admin_bp.route('/statistic')
@login_required
def statistic():
    # Получаем текущую тему из cookie
    theme = request.cookies.get('admin_theme', 'light')
    
    # Получаем время последнего обновления магазинов
    last_store_update = db.get_last_store_update() or "Не обновлялись"
    next_store_update = db.get_next_store_update() or "Не запланировано"

    # сверяем часы и минуты и если время меньше то добавляем 1 день для вывода на странице в формате '2025-04-06 12:30'
    if next_store_update < datetime.now().strftime('%H:%M'):
        next_store_update = datetime.now().strftime('%Y-%m-%d') + ' ' + next_store_update
        
    
    # Получаем статистику по пользователям
    user_stats = {
        'weekly': db.get_new_users_count(days=7),
        'monthly': db.get_new_users_count(days=30)
    }
    
    # Получаем данные для графика (последние 12 недель)
    weekly_data = db.get_user_growth_data(weeks=12)
    monthly_data = db.get_user_growth_data(months=6)
    
    return render_template('admin/statistic.html', 
                         theme=theme,
                         next_store_update=next_store_update,
                         last_store_update=last_store_update,
                         user_stats=user_stats,
                         weekly_data=json.dumps(weekly_data),
                         monthly_data=json.dumps(monthly_data))

# API для переключения темы
@admin_bp.route('/toggle-theme', methods=['POST'])
def toggle_theme():
    current_theme = request.json.get('current_theme', 'light')
    new_theme = 'dark' if current_theme == 'light' else 'light'
    
    # Создаем ответ
    response = jsonify({'success': True, 'theme': new_theme})
    
    # Устанавливаем cookie с темой
    response.set_cookie('admin_theme', new_theme, max_age=60*60*24*365)
    
    return response

# Вспомогательная функция для создания таблицы настроек (если потребуется в будущем)
def ensure_admin_preferences_table():
    """Создает таблицу admin_preferences, если она не существует"""
    try:
        # Используем контекстный менеджер для автоматического закрытия соединения и курсора
        connection = db.pool.get_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_preferences (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL UNIQUE,
                    theme VARCHAR(10) DEFAULT 'light',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
        db.pool.release_connection(connection)
        return True
    except Exception as e:
        print(f"Ошибка при создании таблицы admin_preferences: {e}")
        return False
