document.addEventListener('DOMContentLoaded', () => {
    // Уведомления
    function showNotification(type, message, duration = 3000) {
        const notificationArea = document.getElementById('notification-area');
        if (!notificationArea) {
            console.error('Элемент #notification-area не найден в DOM');
            return;
        }

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        notification.innerHTML = `
            <span>${message}</span>
            <span class="notification-close">×</span>
        `;
        
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        notificationArea.appendChild(notification);
        
        if (duration > 0) {
            setTimeout(() => {
                notification.remove();
            }, duration);
        }
        
        return notification;
    }

    window.showSuccessAlert = function(message) {
        showNotification('success', message);
    };

    window.showErrorAlert = function(message) {
        showNotification('error', message);
    };

    window.showWarningAlert = function(message) {
        showNotification('warning', message);
    };

    // Функция кастомного подтверждения
    window.showConfirm = function(message, callback) {
        const notificationArea = document.getElementById('notification-area');
        if (!notificationArea) {
            console.error('Элемент #notification-area не найден в DOM');
            return;
        }

        const confirmBox = document.createElement('div');
        confirmBox.className = 'notification confirm';
        confirmBox.innerHTML = `
            <span>${message}</span>
            <div class="confirm-buttons">
                <button class="btn confirm-yes">Да</button>
                <button class="btn confirm-no">Нет</button>
            </div>
        `;

        notificationArea.appendChild(confirmBox);

        const yesButton = confirmBox.querySelector('.confirm-yes');
        const noButton = confirmBox.querySelector('.confirm-no');

        // Добавляем отладку
        console.log('Создано окно подтверждения:', { yesButton, noButton });

        yesButton.addEventListener('click', () => {
            console.log('Нажата кнопка "Да"');
            callback(true);
            confirmBox.remove();
        });

        noButton.addEventListener('click', () => {
            console.log('Нажата кнопка "Нет"');
            callback(false);
            confirmBox.remove();
        });
    };
});