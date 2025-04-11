/**
 * Скрипт для отслеживания прогресса выполнения main.py
 * и управления запуском/остановкой процесса
 */

// Дождемся полной загрузки DOM
document.addEventListener('DOMContentLoaded', function() {
    // Основные элементы интерфейса
    const processControlsContainer = document.getElementById('processControls');
    const processButton = document.getElementById('processButton');
    const stopButton = document.getElementById('stopButton');
    const progressBar = document.getElementById('progressBar');
    const statusText = document.getElementById('statusText');
    const terminalOutput = document.getElementById('terminalOutput');
    const proxyList = document.getElementById('proxyList');
    
    // Проверяем, что все элементы найдены
    if (!processButton || !progressBar || !statusText || !proxyList) {
        console.error('Не удалось найти один или несколько элементов интерфейса');
        return;
    }
    
    // Интервал обновления прогресса (мс)
    const updateInterval = 3000;
    let updateTimer = null;
    
    // Флаг для отслеживания, запущен ли процесс
    let processRunning = false;
    
    // Создаем текстовый прогресс-бар, если есть соответствующий элемент
    let textProgressBar = null;
    if (terminalOutput) {
        textProgressBar = new TextProgressBar(terminalOutput, {
            barLength: 40,
            barChar: '#',
            emptyChar: '-'
        });
    }
    
    // Функция для обновления UI на основе данных прогресса
    function updateUI(data) {
        // Обновляем прогресс-бар
        const progress = data.progress || 0;
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${progress}%`;
        
        // Обновляем цвет прогресс-бара в зависимости от прогресса
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
        if (progress < 30) {
            progressBar.classList.add('bg-danger');
        } else if (progress < 70) {
            progressBar.classList.add('bg-warning');
        } else {
            progressBar.classList.add('bg-success');
        }
        
        // Проверяем наличие общего количества магазинов
        const total = data.total_stores || 0;
        const processed = data.processed_stores || 0;

        // Обновляем текстовый прогресс-бар
        if (textProgressBar) {
            // Убираем информацию о прокси из текстового прогресс-бара
            textProgressBar.update(processed, total, '');
        }

        // Обновляем текст статуса с учетом общего количества магазинов
        if (total > 0) {
            statusText.textContent = `Обработано ${processed} из ${total} магазинов.`;
        } else {
            statusText.textContent = 'Нет данных о количестве магазинов.';
        }
        
        // Обновляем состояние кнопок
        processRunning = data.process_running;
        updateButtonStates(processRunning);
        
        // Обновляем информацию о прокси
        updateProxyList(data.proxy_stats || {});
        
        // Если процесс завершен, но был запланирован таймер, останавливаем его
        if (!processRunning && updateTimer) {
            // Последнее обновление перед остановкой
            clearInterval(updateTimer);
            updateTimer = null;
            console.log('Остановка таймера обновления прогресса - процесс завершен');
        }
    }
    
    // Функция для изменения состояния кнопок запуска и остановки
    function updateButtonStates(isRunning) {
        if (isRunning) {
            // Процесс запущен
            processButton.disabled = true;
            processButton.classList.remove('btn-primary', 'btn-checking');
            processButton.classList.add('btn-secondary');
            processButton.innerHTML = '<i class="fas fa-sync fa-spin mr-2"></i>Выполняется...';
            
            // Включаем кнопку остановки
            if (stopButton) {
                stopButton.disabled = false;
                stopButton.classList.remove('btn-secondary');
                stopButton.classList.add('btn-danger');
            }
        } else {
            // Процесс не запущен
            processButton.disabled = false;
            processButton.classList.remove('btn-secondary', 'btn-checking');
            processButton.classList.add('btn-primary');
            processButton.innerHTML = '<i class="fas fa-play mr-2"></i>Запустить';
            
            // Отключаем кнопку остановки
            if (stopButton) {
                stopButton.disabled = true;
                stopButton.classList.remove('btn-danger');
                stopButton.classList.add('btn-secondary');
            }
        }
    }
    
    // Функция для форматирования текста статистики прокси
    function formatProxyStats(stats) {
        if (!stats || Object.keys(stats).length === 0) {
            return '';
        }
        
        // Сортируем прокси по нагрузке (от большей к меньшей)
        const sortedStats = Object.entries(stats).sort((a, b) => b[1] - a[1]);
        
        // Формируем текст статистики
        return 'Прокси: ' + sortedStats.map(([id, count]) => `${id}:${count}`).join(', ');
    }
    
    // Функция для обновления списка прокси
    function updateProxyList(stats) {
        if (!proxyList) return;
        
        if (!stats || Object.keys(stats).length === 0) {
            proxyList.innerHTML = '<div class="no-data">Нет данных о прокси</div>';
            return;
        }
        
        let proxyHtml = '';
        
        // Сортируем прокси по нагрузке (от большей к меньшей)
        const sortedProxies = Object.entries(stats).sort((a, b) => b[1] - a[1]);
        
        // Формируем HTML для каждого прокси
        sortedProxies.forEach(([proxyId, count]) => {
            // Определяем класс для цвета текста в зависимости от нагрузки
            let colorClass = 'text-success';
            if (count > 20) {
                colorClass = 'text-danger';
            } else if (count > 10) {
                colorClass = 'text-warning';
            }
            
            proxyHtml += `
            <div class="proxy-item">
                <span class="proxy-label">Прокси ${proxyId}:</span>
                <span class="proxy-value ${colorClass}">${count} запросов</span>
            </div>`;
        });
        
        proxyList.innerHTML = proxyHtml;
    }
    
    // Функция для получения текущего прогресса с сервера
    function fetchProgress() {
        // Добавляем параметр для предотвращения кэширования
        const timestamp = new Date().getTime();
        
        fetch(`/api/progress?t=${timestamp}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Обновляем UI на основе полученных данных
            updateUI(data);
            
            // Если процесс запущен, но не было запланировано обновление, запускаем таймер
            if (data.process_running && !updateTimer) {
                console.log('Запуск таймера обновления прогресса');
                updateTimer = setInterval(fetchProgress, updateInterval);
            }
        })
        .catch(error => {
            console.error('Ошибка при получении прогресса:', error);
            
            // При ошибке возвращаем кнопки в исходное состояние
            updateButtonStates(false);
            
            // Обновляем текст статуса с информацией об ошибке
            statusText.textContent = `Ошибка: ${error.message}`;
        });
    }
    
    // Функция для запуска процесса main.py
    function startProcess() {
        // Изменяем вид кнопки и отключаем её
        processButton.disabled = true;
        processButton.classList.remove('btn-primary');
        processButton.classList.add('btn-checking');
        processButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Запуск...';
        
        // Отключаем кнопку остановки
        if (stopButton) {
            stopButton.disabled = true;
        }
        
        // Обновляем текст статуса
        statusText.textContent = 'Запуск процесса...';
        
        // Если есть текстовый прогресс-бар, обнуляем его
        if (textProgressBar) {
            textProgressBar.update(0, 100, 'Инициализация...');
        }
        
        // Отправляем запрос на сервер для запуска main.py
        fetch('/start-main', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `HTTP error! Status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Процесс успешно запущен:', data);
            
            // Обновляем текст статуса
            statusText.textContent = data.message || 'Процесс запущен успешно';
            
            // Запускаем таймер для обновления прогресса
            if (!updateTimer) {
                // Запланируем первое обновление через короткий промежуток времени
                setTimeout(() => {
                    fetchProgress();
                    
                    // Затем запускаем регулярные обновления
                    updateTimer = setInterval(fetchProgress, updateInterval);
                }, 1000);
            }
        })
        .catch(error => {
            console.error('Ошибка при запуске процесса:', error);
            
            // При ошибке возвращаем кнопки в исходное состояние
            updateButtonStates(false);
            
            // Обновляем текст статуса с информацией об ошибке
            statusText.textContent = `Ошибка запуска: ${error.message}`;
        });
    }
    
    // Функция для остановки процесса main.py
    function stopProcess() {
        // Проверка, что кнопка остановки существует
        if (!stopButton) return;
        
        // Изменяем вид кнопки остановки и отключаем её
        stopButton.disabled = true;
        stopButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Остановка...';
        
        // Обновляем текст статуса
        statusText.textContent = 'Остановка процесса...';
        
        // Отправляем запрос на сервер для остановки main.py
        fetch('/stop-main', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || `HTTP error! Status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Процесс успешно остановлен:', data);
            
            // Обновляем текст статуса
            statusText.textContent = data.message || 'Процесс остановлен успешно';
            
            // Обновляем интерфейс для отражения остановки процесса
            updateButtonStates(false);
            
            // Получаем последний статус после остановки
            setTimeout(fetchProgress, 1000);
        })
        .catch(error => {
            console.error('Ошибка при остановке процесса:', error);
            
            // Возвращаем кнопки в исходное состояние (предполагаем, что процесс все еще запущен)
            updateButtonStates(true);
            
            // Обновляем текст статуса с информацией об ошибке
            statusText.textContent = `Ошибка остановки: ${error.message}`;
        });
    }
    
    // Привязываем обработчик события к кнопке запуска
    processButton.addEventListener('click', startProcess);
    
    // Привязываем обработчик события к кнопке остановки, если она существует
    if (stopButton) {
        stopButton.addEventListener('click', stopProcess);
    }
    
    // Запускаем первичную проверку прогресса при загрузке страницы
    fetchProgress();
});