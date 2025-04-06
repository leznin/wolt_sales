/**
 * Инициализация рекламного прелоадера
 * Этот скрипт запускает рекламный прелоадер перед загрузкой основного приложения
 */
document.addEventListener('DOMContentLoaded', async function() {
    // Проверяем, существует ли класс AdPreloader
    if (typeof AdPreloader === 'undefined') {
        console.error('AdPreloader не найден. Убедитесь, что скрипт ad-preloader.js загружен.');
        return;
    }
    
    console.log('Инициализация рекламного прелоадера...');
    
    // Проверяем, запущено ли приложение в Telegram Mini App
    const isTelegramWebApp = window.Telegram && window.Telegram.WebApp;
    
    // Создаем экземпляр рекламного прелоадера
    const adPreloader = new AdPreloader({
        // Обработчик закрытия рекламы
        onClose: () => {
            console.log('Реклама закрыта, показываем основное приложение');
            // Скрываем прелоадер
            const preloader = document.getElementById('preloader');
            if (preloader) {
                preloader.style.display = 'none';
            }
            
            // Показываем основное приложение
            const appContainer = document.getElementById('app');
            if (appContainer) {
                appContainer.style.display = 'block';
            }
        },
        // Настройки для Telegram Mini App
        telegramApp: isTelegramWebApp
    });
    
    // Показываем рекламу
    await adPreloader.show();
});
