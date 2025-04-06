"""
Методы для работы с рекламными прелоадерами
Добавляются в класс WoltDatabase
"""

def create_ad_preloader(self, title, description, video_url, redirect_url, display_time=5, skip_after=3, priority=50):
    """Создает новую запись о рекламном прелоадере"""
    try:
        cursor = self.connection.cursor()
        query = """
        INSERT INTO ad_preloaders 
        (title, description, video_url, redirect_url, display_time, skip_after, priority, is_active) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (title, description, video_url, redirect_url, display_time, skip_after, priority, True))
        self.connection.commit()
        ad_id = cursor.lastrowid
        cursor.close()
        return ad_id
    except Exception as e:
        print(f"Ошибка при создании рекламного прелоадера: {str(e)}")
        raise

def get_all_ad_preloaders(self):
    """Возвращает список всех рекламных прелоадеров"""
    try:
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM ad_preloaders ORDER BY priority DESC, created_at DESC"
        cursor.execute(query)
        ads = cursor.fetchall()
        cursor.close()
        return ads
    except Exception as e:
        print(f"Ошибка при получении списка рекламных прелоадеров: {str(e)}")
        return []

def get_ad_preloader(self, ad_id):
    """Возвращает информацию о конкретном рекламном прелоадере"""
    try:
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT * FROM ad_preloaders WHERE id = %s"
        cursor.execute(query, (ad_id,))
        ad = cursor.fetchone()
        cursor.close()
        return ad
    except Exception as e:
        print(f"Ошибка при получении информации о рекламном прелоадере: {str(e)}")
        return None

def update_ad_preloader(self, ad_id, title, description, video_url, redirect_url, display_time, skip_after, priority):
    """Обновляет информацию о рекламном прелоадере"""
    try:
        cursor = self.connection.cursor()
        query = """
        UPDATE ad_preloaders 
        SET title = %s, description = %s, video_url = %s, redirect_url = %s, 
            display_time = %s, skip_after = %s, priority = %s
        WHERE id = %s
        """
        cursor.execute(query, (title, description, video_url, redirect_url, display_time, skip_after, priority, ad_id))
        self.connection.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Ошибка при обновлении рекламного прелоадера: {str(e)}")
        raise

def update_ad_preloader_status(self, ad_id, is_active):
    """Обновляет статус рекламного прелоадера"""
    try:
        cursor = self.connection.cursor()
        query = "UPDATE ad_preloaders SET is_active = %s WHERE id = %s"
        cursor.execute(query, (is_active, ad_id))
        self.connection.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Ошибка при обновлении статуса рекламного прелоадера: {str(e)}")
        raise

def delete_ad_preloader(self, ad_id):
    """Удаляет рекламный прелоадер"""
    try:
        cursor = self.connection.cursor()
        query = "DELETE FROM ad_preloaders WHERE id = %s"
        cursor.execute(query, (ad_id,))
        self.connection.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Ошибка при удалении рекламного прелоадера: {str(e)}")
        raise

def get_random_active_ad_preloader(self):
    """Возвращает случайный активный рекламный прелоадер с учетом приоритета"""
    try:
        cursor = self.connection.cursor(dictionary=True)
        # Используем приоритет для взвешенного выбора
        query = """
        SELECT * FROM ad_preloaders 
        WHERE is_active = TRUE 
        ORDER BY RAND() * priority DESC 
        LIMIT 1
        """
        cursor.execute(query)
        ad = cursor.fetchone()
        cursor.close()
        return ad
    except Exception as e:
        print(f"Ошибка при получении случайного рекламного прелоадера: {str(e)}")
        return None

def increment_ad_views(self, ad_id):
    """Увеличивает счетчик просмотров рекламы"""
    try:
        cursor = self.connection.cursor()
        query = "UPDATE ad_preloaders SET views = views + 1 WHERE id = %s"
        cursor.execute(query, (ad_id,))
        self.connection.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Ошибка при увеличении счетчика просмотров: {str(e)}")
        return False

def increment_ad_clicks(self, ad_id):
    """Увеличивает счетчик кликов по рекламе"""
    try:
        cursor = self.connection.cursor()
        query = "UPDATE ad_preloaders SET clicks = clicks + 1 WHERE id = %s"
        cursor.execute(query, (ad_id,))
        self.connection.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Ошибка при увеличении счетчика кликов: {str(e)}")
        return False
