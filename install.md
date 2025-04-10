# Руководство по установке проекта на сервер Ubuntu

Это подробная инструкция по установке проекта на сервер Ubuntu для людей, не знакомых с командной строкой.

## Информация о сервере

**Тарифный план:** Cloud Starter Intel| NL-2 v.2  
**Дата открытия:** 2025-04-05  
**IPv4-адрес сервера:** 95.215.206.27  
**IPv6-адрес сервера:** 2a13:4ac0:10:0:f816:3eff:fe8f:85ec  
**Пользователь:** root  
**Пароль:** 696578As!!!!  

## Шаг 1: Подключение к серверу Ubuntu

### 1.1 Установите SSH-клиент
- Для Windows: скачайте и установите [PuTTY](https://www.putty.org/)
- Для Mac: Terminal уже установлен (находится в папке Приложения -> Утилиты)
- Для Linux: Terminal уже установлен

### 1.2 Подключение к серверу

**Через PuTTY (Windows):**
1. Откройте PuTTY
2. В поле "Host Name" введите IP-адрес вашего сервера (95.215.206.27)
3. Порт оставьте 22 (стандартный порт SSH)
4. Нажмите "Open"
5. Введите имя пользователя (root)
6. Введите пароль (696578As!!!!)

**Через Terminal (Mac/Linux):**
1. Откройте Terminal
2. Введите команду: `ssh root@95.215.206.27`
   Например: `ssh root@192.168.1.100`
3. Нажмите Enter
4. При первом подключении появится предупреждение о подлинности сервера, напечатайте "yes" и нажмите Enter
5. Введите пароль (696578As!!!!)

## Шаг 2: Обновление системы

После подключения к серверу введите следующие команды (каждую строку вводите отдельно и нажимайте Enter):

```bash
sudo apt update
```
(Система может запросить пароль - введите его)

```bash
sudo apt upgrade -y
```

Эти команды обновят список доступных пакетов и установят последние версии всех программ. Процесс может занять несколько минут.

## Шаг 3: Установка необходимых программ

### 3.1 Установка Git

Git нужен для загрузки вашего проекта с репозитория. Введите:

```bash
sudo apt install git -y
```

Чтобы проверить установку, введите:

```bash
git --version
```

Вы должны увидеть версию Git, например: `git version 2.25.1`

### 3.2 Установка Node.js и NPM (если ваш проект использует JavaScript)

```bash
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs
```

Чтобы проверить установку, введите:

```bash
node -v
npm -v
```

Вы должны увидеть версии Node .js и NPM.

### 3.3 Установка MySQL (обязательно)

```bash
# Обновление репозиториев
sudo apt update

# Установка MySQL сервера
sudo apt install mysql-server -y

# Проверка статуса MySQL
sudo systemctl status mysql

# Настройка безопасности MySQL
sudo mysql_secure_installation
```

При запуске `mysql_secure_installation` вам будет предложено настроить пароль и другие параметры безопасности:
- Введите пароль для пользователя root MySQL
- Ответьте на следующие вопросы (рекомендуется ответить 'Y' на все):
  - Remove anonymous users? (Удалить анонимных пользователей?) -> Y
  - Disallow root login remotely? (Запретить удаленный вход под root?) -> Y
  - Remove test database? (Удалить тестовую базу данных?) -> Y
  - Reload privilege tables now? (Перезагрузить таблицы привилегий?) -> Y

### 3.4 Создание базы данных и пользователя для проекта

```bash
# Вход в MySQL
sudo mysql -u root -p

# В консоли MySQL выполните следующие команды:
CREATE DATABASE wolt_sale;
CREATE USER 'woltuser'@'localhost' IDENTIFIED BY '696578As';
GRANT ALL PRIVILEGES ON wolt_sales.* TO 'woltuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Замените 'надежный_пароль' на выбранный вами пароль.

### 3.5 Установка других зависимостей (если требуется)

Если ваш проект требует другие программы (например, базу данных), установите их:

**PostgreSQL:**
```bash
sudo apt install postgresql postgresql-contrib -y
```

**MongoDB:**
```bash
sudo apt install mongodb -y
```

## Шаг 4: Создание директории проекта

Создайте папку для вашего проекта:

```bash
mkdir -p /var/www/myproject
```

Перейдите в эту папку:

```bash
cd /var/www/myproject
```

## Шаг 5: Загрузка проекта на сервер

### 5.1 Загрузка через Git (если ваш проект на GitHub/GitLab/Bitbucket)

```bash
git clone https://github.com/leznin/wolt_sales.git .
```

### 5.2 Загрузка через SFTP (если у вас нет репозитория)

1. Установите FileZilla на ваш компьютер
2. Подключитесь к серверу:
   - Хост: sftp://IP-адрес_сервера
   - Имя пользователя: ваш_пользователь
   - Пароль: ваш_пароль
   - Порт: 22
3. Перетащите файлы вашего проекта в папку `/var/www/myproject` на сервере

## Шаг 6: Установка зависимостей проекта

Если у вас Node.js проект:

```bash
npm install
```

Для Python:

```bash
pip install -r requirements.txt
```

## Шаг 7: Настройка конфигурации проекта

Создайте файл с переменными окружения (если требуется):

```bash
cp .env.example .env
nano .env
```

Откроется текстовый редактор. Измените необходимые настройки.

Для сохранения и выхода из редактора nano:
1. Нажмите Ctrl+O (сохранить)
2. Нажмите Enter (подтвердить имя файла)
3. Нажмите Ctrl+X (выйти)

## Шаг 8: Сборка проекта (если требуется)

Для Node.js проектов:

```bash
npm run build
```

## Шаг 9: Настройка веб-сервера

### 9.1 Установка Nginx

```bash
sudo apt install nginx -y
```

### 9.2 Настройка Nginx

Создайте конфигурационный файл:

```bash
sudo nano /etc/nginx/sites-available/myproject
```

Вставьте в редактор следующую конфигурацию (замените домен на ваш):

```
server {
    listen 80;
    server_name ваш-домен.com www.ваш-домен.com;
    
    root /var/www/myproject;  # для статических сайтов
    
    # Для Node.js приложений:
    location / {
        proxy_pass http://localhost:3000;  # порт, на котором работает ваше приложение
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Для PHP:
    # location ~ \.php$ {
    #     include snippets/fastcgi-php.conf;
    #     fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
    # }
    
    # Для статических файлов:
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 30d;
    }
}
```

Сохраните файл (Ctrl+O, Enter, Ctrl+X).

Создайте ссылку на конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled/
```

Проверьте конфигурацию:

```bash
sudo nginx -t
```

Если все правильно, перезапустите Nginx:

```bash
sudo systemctl restart nginx
```

## Шаг 10: Запуск приложения

### Для Node.js приложений:

Установка PM2 (менеджер процессов):

```bash
sudo npm install -g pm2
```

Запуск приложения:

```bash
cd /var/www/myproject
pm2 start npm --name "myapp" -- start
```

Настройка автозапуска:

```bash
pm2 save
pm2 startup
```

Система выдаст команду, которую нужно выполнить. Скопируйте и вставьте её.

### Для PHP:

Если используете PHP, установите PHP-FPM:

```bash
sudo apt install php-fpm php-mysql -y
```

### Для статических сайтов:

Никаких дополнительных действий не требуется, Nginx уже настроен для обслуживания статических файлов.

## Шаг 11: Настройка SSL-сертификата (HTTPS)

Установка Certbot:

```bash
sudo apt install certbot python3-certbot-nginx -y
```

Получение SSL-сертификата:

```bash
sudo certbot --nginx -d ваш-домен.com -d www.ваш-домен.com
```

Certbot задаст несколько вопросов:
1. Email для уведомлений - введите ваш email
2. Согласие с условиями - введите A
3. Делиться email - введите Y или N
4. Перенаправлять HTTP на HTTPS - рекомендуется выбрать 2

## Шаг 12: Настройка файрвола

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

На вопрос "Proceed with operation? (y|n)" введите y и нажмите Enter.

## Мониторинг и обслуживание

### Проверка статуса Nginx:

```bash
sudo systemctl status nginx
```

Для выхода нажмите q.

### Просмотр логов Nginx:

```bash
sudo tail -f /var/log/nginx/error.log
```

Для остановки просмотра логов нажмите Ctrl+C.

### Просмотр логов приложения (для Node.js с PM2):

```bash
pm2 logs
```

Для остановки просмотра логов нажмите Ctrl+C.

### Перезапуск приложения (для Node.js с PM2):

```bash
pm2 restart myapp
```

### Обновление проекта:

```bash
cd /var/www/myproject
git pull  # если проект загружался через Git
npm install  # если это Node.js проект
npm run build  # если требуется сборка
pm2 restart myapp  # если это Node.js приложение, запущенное через PM2
```

## Типичные проблемы и их решения

### Проблема: "Permission denied" (Отказано в доступе)

Решение: используйте `sudo` перед командой или измените права доступа:

```bash
sudo chown -R $USER:$USER /var/www/myproject
```

### Проблема: Порт уже используется

Решение: найдите процесс, использующий порт, и завершите его:

```bash
sudo lsof -i :3000  # заменить 3000 на нужный порт
sudo kill -9 PID  # заменить PID на номер процесса из предыдущей команды
```

### Проблема: "Command not found" (Команда не найдена)

Решение: проверьте, установлена ли программа, или обновите PATH:

```bash
which имя_программы  # проверка, установлена ли программа
echo $PATH  # проверка переменной PATH
```

### Проблема: Сайт не открывается

Решение:
1. Проверьте статус Nginx: `sudo systemctl status nginx`
2. Проверьте настройки файрвола: `sudo ufw status`
3. Проверьте логи: `sudo tail -f /var/log/nginx/error.log`

## Полезные команды

### Просмотр содержимого директории:

```bash
ls -la
```

### Просмотр содержимого файла:

```bash
cat имя_файла
```

### Редактирование файла:

```bash
nano имя_файла
```

### Просмотр свободного места на диске:

```bash
df -h
```

### Просмотр использования памяти:

```bash
free -m
```

### Перезагрузка сервера:

```bash
sudo reboot
```

### Выход из SSH-сессии:

```bash
exit
```

Для дополнительной помощи обратитесь к документации или сервису поддержки вашего хостинг-провайдера.