document.addEventListener('DOMContentLoaded', function() {
    // Получаем элементы интерфейса (с правильными ID)
    const processButton = document.getElementById('processButton');
    const progressBar = document.getElementById('progressBar');
    const processStatus = document.getElementById('processStatus');
    const proxyList = document.getElementById('proxyList');
    
    if (!processButton || !progressBar || !processStatus || !proxyList) {
        console.error("Не удалось найти один или несколько элементов интерфейса");
        return; // Прерываем выполнение при отсутствии элементов
    }

    // Функция для обновления состояния процесса
    function updateProcessState() {
        // Отображаем начальное состояние кнопки и статуса
        processButton.disabled = true;
        processButton.textContent = 'Проверка...';
        processStatus.textContent = 'Проверка статуса процесса...';
        
        fetch('/adminqsc/api/process/status', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Не удалось получить статус процесса');
            return response.json();
        })
        .then(data => {
            // Обновляем прогресс-бар
            const progress = data.progress || 0;
            progressBar.style.width = `${progress}%`;
            progressBar.textContent = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
            // Меняем цвет прогресс-бара в зависимости от прогресса
            progressBar.className = 'progress-bar';
            progressBar.classList.remove('bg-danger', 'bg-warning', 'bg-success', 'progress-bar-success');
            if (progress < 30) {
                progressBar.classList.add('bg-danger');
            } else if (progress < 70) {
                progressBar.classList.add('bg-warning');
            } else {
                progressBar.classList.add('progress-bar-success');
            }
            
            // Обновляем статус процесса
            processStatus.textContent = data.status || 'Нет данных';
            
            // Обновляем состояние кнопки в зависимости от статуса процесса
            if (data.running) {
                processButton.textContent = 'Выполняется...';
                processButton.disabled = true;
                processButton.classList.remove('btn-primary');
                processButton.classList.add('btn-secondary');
            } else {
                processButton.textContent = 'Запустить';
                processButton.disabled = false;
                processButton.classList.add('btn-primary');
                processButton.classList.remove('btn-secondary');
            }
            
            // Обновляем информацию о прокси
            if (data.proxyStats && Object.keys(data.proxyStats).length > 0) {
                let proxyHtml = '';
                
                // Сортируем прокси по нагрузке (от большей к меньшей)
                const sortedProxies = Object.entries(data.proxyStats).sort((a, b) => b[1] - a[1]);
                
                sortedProxies.forEach(([proxyId, count]) => {
                    // Определяем класс цвета в зависимости от нагрузки
                    let colorClass = 'text-success';
                    if (count > 20) colorClass = 'text-danger';
                    else if (count > 10) colorClass = 'text-warning';
                    
                    proxyHtml += `<div class="proxy-item">
                        <span class="proxy-label">Прокси ${proxyId}:</span>
                        <span class="proxy-value ${colorClass}">${count} запросов</span>
                    </div>`;
                });
                
                proxyList.innerHTML = proxyHtml;
            } else {
                proxyList.innerHTML = '<div class="no-data">Нет данных о прокси</div>';
            }
            
            // Если процесс запущен, продолжаем обновление
            if (data.running) {
                setTimeout(updateProcessState, 2000);
            }
        })
        .catch(error => {
            console.error('Ошибка при обновлении статуса:', error);
            processStatus.textContent = 'Ошибка получения данных';
            
            // При ошибке восстанавливаем активность кнопки
            processButton.disabled = false;
            processButton.textContent = 'Запустить';
            processButton.classList.add('btn-primary');
            processButton.classList.remove('btn-secondary');
            
            // При ошибке пробуем еще раз через 5 секунд
            setTimeout(updateProcessState, 5000);
        });
    }
    
    // Функция для запуска процесса
    function startProcess() {
        processButton.disabled = true;
        processButton.textContent = 'Запуск...';
        processButton.classList.remove('btn-primary');
        processButton.classList.add('btn-secondary');
        
        fetch('/adminqsc/api/process/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Не удалось запустить процесс');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                processStatus.textContent = 'Процесс успешно запущен';
                // Запускаем обновление статуса
                setTimeout(updateProcessState, 1000);
            } else {
                processButton.disabled = false;
                processButton.textContent = 'Запустить';
                processButton.classList.add('btn-primary');
                processButton.classList.remove('btn-secondary');
                processStatus.textContent = `Ошибка: ${data.error || 'Неизвестная ошибка'}`;
            }
        })
        .catch(error => {
            console.error('Ошибка при запуске процесса:', error);
            processButton.disabled = false;
            processButton.textContent = 'Запустить';
            processButton.classList.add('btn-primary');
            processButton.classList.remove('btn-secondary');
            processStatus.textContent = 'Ошибка запуска процесса';
        });
    }
    
    // Инициализация карты
    const map = L.map('map').setView([55.7558, 37.6173], 2);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Загружаем локации пользователей
    let userLocations = [];
    try {
        userLocations = JSON.parse('{{ user_locations|safe }}');
        console.log("Загружены локации пользователей:", userLocations);
    } catch(e) {
        console.error("Ошибка при загрузке локаций:", e);
    }
    
    // Добавляем маркеры на карту
    if (userLocations && userLocations.length > 0) {
        const bounds = [];
        
        userLocations.forEach(location => {
            if (location && location.lat && location.lon) {
                const lat = parseFloat(location.lat);
                const lon = parseFloat(location.lon);
                
                if (!isNaN(lat) && !isNaN(lon)) {
                    bounds.push([lat, lon]);
                    
                    L.circle([lat, lon], {
                        color: '#4e73df',
                        fillColor: '#4e73df',
                        fillOpacity: 0.5,
                        radius: Math.sqrt(location.users_count || 1) * 5000
                    }).bindPopup(`
                        <div class="text-center">
                            <strong>${location.users_count || 0}</strong> пользователей<br>
                            <small>Обновлено: ${location.last_update ? new Date(location.last_update).toLocaleDateString() : 'Не указано'}</small>
                        </div>
                    `).addTo(map);
                }
            }
        });
        
        // Масштабируем карту, если есть точки
        if (bounds.length > 0) {
            try {
                map.fitBounds(bounds);
            } catch (e) {
                console.error("Ошибка при масштабировании карты:", e);
            }
        }
    }
    
    // Обновляем карту при полной загрузке
    setTimeout(() => map.invalidateSize(), 100);
    setTimeout(() => map.invalidateSize(), 500);
    
    // Получаем данные для графиков
    let weeklyData = {labels: [], data: []};
    let monthlyData = {labels: [], data: []};
    
    try {
        weeklyData = JSON.parse('{{ weekly_data|safe }}');
        monthlyData = JSON.parse('{{ monthly_data|safe }}');
    } catch(e) {
        console.error("Ошибка при загрузке данных графика:", e);
    }
    
    // Инициализация графика
    const ctx = document.getElementById('userGrowthChart');
    if (ctx) {
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: weeklyData.labels || [],
                datasets: [{
                    label: 'Новые пользователи',
                    backgroundColor: 'rgba(78, 115, 223, 0.05)',
                    borderColor: 'rgba(78, 115, 223, 1)',
                    data: weeklyData.data || [],
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                maintainAspectRatio: false,
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            maxTicksLimit: 5
                        }
                    },
                    x: {
                        ticks: {
                            maxTicksLimit: 7
                        }
                    }
                }
            }
        });
        
        // Обработчики переключения периодов
        document.querySelectorAll('[data-period]').forEach(button => {
            button.addEventListener('click', function() {
                const period = this.dataset.period;
                const data = period === 'weekly' ? weeklyData : monthlyData;
                
                // Отмечаем активную кнопку
                document.querySelectorAll('[data-period]').forEach(btn => {
                    btn.classList.remove('active');
                });
                this.classList.add('active');
                
                // Обновляем данные графика
                chart.data.labels = data.labels || [];
                chart.data.datasets[0].data = data.data || [];
                chart.update();
            });
        });
    }
    
    // Привязываем обработчик к кнопке запуска
    processButton.addEventListener('click', startProcess);
    
    // Запускаем первичное получение статуса
    updateProcessState();
});