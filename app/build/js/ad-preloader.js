/**
 * Рекламный пролоадер
 * Показывает видео-рекламу вместо стандартного пролоадера
 */
class AdPreloader {
    constructor(options = {}) {
        // Настройки по умолчанию
        this.options = {
            apiUrl: '/adminqsc/api/ad/random',
            clickUrl: '/adminqsc/api/ad/click',
            viewUrl: '/adminqsc/api/ad/view',
            container: document.body,
            onClose: null,
            telegramApp: false,
            ...options
        };
        
        // Создаем элементы пролоадера
        this.createElements();
        
        // Флаг, показывающий активна ли реклама
        this.isActive = false;
        
        // Текущая реклама
        this.currentAd = null;
        
        // Таймер обратного отсчета
        this.countdownTimer = null;
        
        // Флаг, показывающий запущено ли приложение в Telegram Mini App
        this.isTelegramApp = this.options.telegramApp || (window.Telegram && window.Telegram.WebApp);
        
        // Кэш для определенной страны пользователя
        this.userCountry = null;
        
        console.log('AdPreloader инициализирован. Telegram Mini App:', this.isTelegramApp);
    }
    
    /**
     * Создает HTML-элементы пролоадера
     */
    createElements() {
        // Основной контейнер
        this.container = document.createElement('div');
        this.container.className = 'ad-preloader-container';
        this.container.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        `;
        
        // Контейнер для видео
        this.videoContainer = document.createElement('div');
        this.videoContainer.className = 'video-container';
        this.videoContainer.style.cssText = `
            position: relative;
            width: 80%;
            max-width: 80vw;
            max-height: 80vh;
            overflow: hidden;
            border-radius: 8px;
            cursor: pointer;
            margin: 0 auto;
        `;
        
        // Элемент видео
        this.videoElement = document.createElement('video');
        this.videoElement.className = 'ad-video';
        this.videoElement.style.cssText = `
            width: 100%;
            height: 100%;
            object-fit: contain;
        `;
        this.videoElement.muted = true;
        this.videoElement.autoplay = true;
        this.videoElement.playsInline = true;
        
        // Метка "Реклама"
        this.adLabel = document.createElement('div');
        this.adLabel.className = 'ad-info';
        this.adLabel.textContent = 'ADS';
        this.adLabel.style.cssText = `
            position: absolute;
            top: 10px;
            left: 10px;
            color: white;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 14px;
        `;
        
        // Таймер
        this.timer = document.createElement('div');
        this.timer.className = 'timer';
        this.timer.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            color: white;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 14px;
        `;
        
        // Кнопка пропуска
        this.skipButton = document.createElement('button');
        this.skipButton.className = 'skip-button';
        this.skipButton.textContent = 'Skip';
        this.skipButton.style.cssText = `
            position: absolute;
            bottom: 10px;
            right: 10px;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            display: none;
        `;
        
        // Добавляем элементы в контейнер
        this.videoContainer.appendChild(this.videoElement);
        this.videoContainer.appendChild(this.adLabel);
        this.videoContainer.appendChild(this.timer);
        this.videoContainer.appendChild(this.skipButton);
        
        this.container.appendChild(this.videoContainer);
        
        // Добавляем контейнер в DOM
        this.options.container.appendChild(this.container);
        
        // Добавляем обработчики событий
        this.addEventListeners();
    }
    
    /**
     * Добавляет обработчики событий
     */
    addEventListeners() {
        // Функция для обработки клика/тапа по рекламе
        const handleAdClick = async () => {
            if (this.currentAd && this.currentAd.redirect_url) {
                try {
                    // Отправляем запрос на сервер для регистрации клика
                    const success = await this.registerClick(this.currentAd.id);
                    
                    // Открываем ссылку в новой вкладке
                    if (success) {
                        console.log(`Переход по ссылке: ${this.currentAd.redirect_url}`);
                        this.openUrl(this.currentAd.redirect_url);
                    } else {
                        console.error('Не удалось зарегистрировать клик, но открываем ссылку');
                        this.openUrl(this.currentAd.redirect_url);
                    }
                } catch (error) {
                    console.error('Ошибка при обработке клика:', error);
                    // Открываем ссылку даже в случае ошибки
                    this.openUrl(this.currentAd.redirect_url);
                }
            } else {
                console.warn('Нет данных о рекламе или отсутствует URL для перехода');
            }
        };
        
        // Клик по видео (переход по рекламной ссылке)
        this.videoContainer.addEventListener('click', handleAdClick);
        
        // Добавляем обработчики тач-событий для мобильных устройств
        this.videoContainer.addEventListener('touchend', (e) => {
            e.preventDefault(); // Предотвращаем стандартное поведение
            handleAdClick();
        });
        
        // Клик по кнопке пропуска
        const handleSkipClick = (e) => {
            if (e) {
                e.stopPropagation(); // Предотвращаем всплытие события
            }
            this.close();
        };
        
        this.skipButton.addEventListener('click', handleSkipClick);
        this.skipButton.addEventListener('touchend', (e) => {
            e.preventDefault();
            handleSkipClick(e);
        });
        
        // Окончание воспроизведения видео
        this.videoElement.addEventListener('ended', () => {
            // Запускаем видео снова
            this.videoElement.currentTime = 0;
            this.videoElement.play();
        });
    }
    
    /**
     * Загружает случайную рекламу с сервера
     */
    async loadAd() {
        try {
            // Получаем страну пользователя
            const country = await this.getUserCountry();
            
            // Формируем URL с параметром страны
            const url = `${this.options.apiUrl}${country ? `?country=${encodeURIComponent(country)}` : ''}`;
            
            console.log(`Загрузка рекламы с параметром страны: ${country || 'не определена'}`);
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success && data.ad) {
                this.currentAd = data.ad;
                return true;
            } else {
                console.error('Ошибка загрузки рекламы:', data.error || 'Неизвестная ошибка');
                return false;
            }
        } catch (error) {
            console.error('Ошибка при загрузке рекламы:', error);
            return false;
        }
    }
    
    /**
     * Получает страну пользователя на основе последней геолокации
     * из локального хранилища или API
     */
    async getUserCountry() {
        try {
            // Если страна уже определена, используем кэшированное значение
            if (this.userCountry) {
                return this.userCountry;
            }
            
            // Проверяем сохраненную геопозицию в localStorage
            const savedLocation = localStorage.getItem('userLocation');
            
            // Если приложение запущено в Telegram Mini App, пробуем получить страну по ID пользователя
            if (this.isTelegramApp && window.Telegram && window.Telegram.WebApp) {
                const userId = window.Telegram.WebApp.initDataUnsafe.user?.id;
                
                if (userId) {
                    try {
                        // Сначала пробуем получить страны, магазины которых отслеживает пользователь
                        const countriesResponse = await fetch(`/api/user-countries/${userId}`);
                        if (countriesResponse.ok) {
                            const countries = await countriesResponse.json();
                            if (countries && countries.length > 0) {
                                // Берем первую страну из списка
                                this.userCountry = countries[0];
                                console.log(`Страна определена по отслеживаемым магазинам: ${this.userCountry}`);
                                return this.userCountry;
                            }
                        }
                        
                        // Если не нашли страны по отслеживаемым магазинам, пробуем по последней локации
                        const locationResponse = await fetch(`/api/user-last-location/${userId}`);
                        const locationData = await locationResponse.json();
                        
                        if (locationData && locationData.lat && locationData.lon) {
                            const country = await this.getCountryByCoordinates(locationData.lat, locationData.lon);
                            if (country) {
                                this.userCountry = country;
                                return country;
                            }
                        }
                    } catch (e) {
                        console.warn('Ошибка при получении страны пользователя:', e);
                    }
                }
            }
            
            // Проверяем сохраненную локацию, если не удалось определить через API
            if (savedLocation) {
                try {
                    const location = JSON.parse(savedLocation);
                    if (location && location.lat && location.lon) {
                        return await this.getCountryByCoordinates(location.lat, location.lon);
                    }
                } catch (e) {
                    console.warn('Ошибка при чтении сохраненной локации:', e);
                }
            }
            
            // Если все методы не сработали, пробуем получить через IP-геолокацию
            try {
                const response = await fetch('https://ipapi.co/json/');
                const data = await response.json();
                this.userCountry = data.country_code || null;
                return this.userCountry;
            } catch (e) {
                console.warn('Ошибка при определении страны по IP:', e);
                return null;
            }
        } catch (error) {
            console.error('Ошибка при определении страны пользователя:', error);
            return null;
        }
    }
    
    /**
     * Получает код страны по координатам используя Reverse Geocoding API
     */
    async getCountryByCoordinates(lat, lon) {
        try {
            // Сначала пробуем получить страну из ближайшего магазина
            try {
                const response = await fetch(`/api/stores-by-location?lat=${lat}&lon=${lon}&radius=5`);
                const stores = await response.json();
                
                // Если есть магазины рядом, берем страну из первого
                if (stores && stores.length > 0 && stores[0].country) {
                    this.userCountry = stores[0].country;
                    console.log(`Страна определена по ближайшему магазину: ${this.userCountry}`);
                    return this.userCountry;
                }
            } catch (e) {
                console.warn('Ошибка при определении страны по магазинам:', e);
            }
            
            // Если не удалось определить по магазинам, используем внешний API
            const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
            const data = await response.json();
            
            if (data && data.address && data.address.country_code) {
                this.userCountry = data.address.country_code.toUpperCase();
                console.log(`Страна определена через Nominatim API: ${this.userCountry}`);
                return this.userCountry;
            }
            
            // Если не удалось определить страну, возвращаем null
            return null;
        } catch (error) {
            console.error('Ошибка при определении страны по координатам:', error);
            return null;
        }
    }
    
    /**
     * Регистрирует клик по рекламе
     */
    async registerClick(adId) {
        try {
            console.log(`Регистрация клика по рекламе ID: ${adId}`);
            const clickUrl = `${this.options.clickUrl}/${adId}`;
            
            const response = await fetch(clickUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ad_id: adId })
            });
            
            const data = await response.json();
            console.log('Результат регистрации клика:', data);
            
            return data.success;
        } catch (error) {
            console.error('Ошибка при регистрации клика:', error);
            return false;
        }
    }
    
    /**
     * Показывает рекламу
     */
    async show() {
        // Если реклама уже активна, ничего не делаем
        if (this.isActive) return;
        
        // Загружаем рекламу
        const success = await this.loadAd();
        if (!success) {
            // Если не удалось загрузить рекламу, вызываем callback и выходим
            if (typeof this.options.onClose === 'function') {
                this.options.onClose();
            }
            return;
        }
        
        // Устанавливаем данные рекламы
        this.videoElement.src = this.currentAd.video_url;
        
        // Показываем контейнер
        this.container.style.opacity = '1';
        this.container.style.pointerEvents = 'auto';
        
        // Обработчик события загрузки метаданных видео
        this.videoElement.onloadedmetadata = () => {
            // Запускаем видео с явным вызовом play() и обработкой ошибок
            const playPromise = this.videoElement.play();
            
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    console.log('Автовоспроизведение видео началось успешно');
                }).catch(error => {
                    console.error('Автовоспроизведение не удалось:', error);
                    // Добавляем кнопку воспроизведения, если автовоспроизведение не разрешено
                    this.showPlayButton();
                });
            }
        };
        
        // Устанавливаем таймер
        let timeLeft = this.currentAd.display_time;
        this.timer.textContent = timeLeft;
        
        // Запускаем обратный отсчет
        this.countdownTimer = setInterval(() => {
            timeLeft--;
            this.timer.textContent = timeLeft;
            
            // Показываем кнопку пропуска после указанного времени
            if (timeLeft <= (this.currentAd.display_time - this.currentAd.skip_after) && this.currentAd.skip_after > 0) {
                this.skipButton.style.display = 'block';
            }
            
            // Закрываем рекламу по истечении времени
            if (timeLeft <= 0) {
                clearInterval(this.countdownTimer);
                this.close();
            }
        }, 1000);
        
        // Устанавливаем флаг активности
        this.isActive = true;
    }
    
    /**
     * Закрывает рекламу
     */
    close() {
        // Останавливаем таймер
        if (this.countdownTimer) {
            clearInterval(this.countdownTimer);
            this.countdownTimer = null;
        }
        
        // Скрываем контейнер
        this.container.style.opacity = '0';
        this.container.style.pointerEvents = 'none';
        
        // Останавливаем видео
        this.videoElement.pause();
        this.videoElement.src = '';
        
        // Сбрасываем флаг активности
        this.isActive = false;
        
        // Скрываем кнопку пропуска
        this.skipButton.style.display = 'none';
        
        // Вызываем callback, если он задан
        if (typeof this.options.onClose === 'function') {
            this.options.onClose();
        }
    }
    
    /**
     * Показывает кнопку воспроизведения
     */
    showPlayButton() {
        // Создаем кнопку воспроизведения
        const playButton = document.createElement('button');
        playButton.textContent = 'Воспроизвести';
        playButton.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            z-index: 10;
        `;
        
        // Добавляем кнопку в контейнер
        this.videoContainer.appendChild(playButton);
        
        // Обработчик клика по кнопке воспроизведения
        const handlePlayClick = (e) => {
            if (e) {
                e.stopPropagation(); // Предотвращаем всплытие события
            }
            // Запускаем видео
            this.videoElement.play().catch(error => {
                console.error('Ошибка воспроизведения видео:', error);
            });
            
            // Удаляем кнопку воспроизведения
            playButton.remove();
        };
        
        // Добавляем обработчики событий для кнопки воспроизведения
        playButton.addEventListener('click', handlePlayClick);
        playButton.addEventListener('touchend', (e) => {
            e.preventDefault();
            handlePlayClick(e);
        });
    }
    
    /**
     * Открывает URL с учетом платформы (браузер или Telegram Mini App)
     */
    openUrl(url) {
        try {
            if (this.isTelegramApp) {
                console.log('Открытие URL в Telegram Mini App:', url);
                // Используем Telegram WebApp API для открытия URL
                if (window.Telegram && window.Telegram.WebApp) {
                    Telegram.WebApp.openLink(url);
                } else {
                    // Если API недоступен, пробуем обычный способ
                    window.open(url, '_blank');
                }
            } else {
                console.log('Открытие URL в обычном браузере:', url);
                // Обычное открытие в новой вкладке
                const newWindow = window.open(url, '_blank');
                
                // Если window.open заблокирован, пробуем другие методы
                if (!newWindow || newWindow.closed) {
                    console.log('window.open заблокирован, пробуем location.href');
                    window.location.href = url;
                }
            }
        } catch (error) {
            console.error('Ошибка при открытии URL:', error);
            // Запасной вариант
            try {
                window.location.href = url;
            } catch (e) {
                console.error('Не удалось открыть URL никаким способом:', e);
                alert('Не удалось открыть ссылку. Пожалуйста, скопируйте адрес: ' + url);
            }
        }
    }
}

// Экспортируем класс
window.AdPreloader = AdPreloader;
