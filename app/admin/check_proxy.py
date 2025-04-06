import aiohttp
import asyncio
import aiohttp_socks
from database import WoltDatabase

def parse_proxy_string(proxy_string):
    """
    Парсит строку прокси в формате IP:порт:логин:пароль
    
    :param proxy_string: Строка с данными прокси
    :return: Словарь с разобранными данными
    """
    parts = proxy_string.split(':')
    
    if len(parts) == 2:
        return {
            'ip': parts[0],
            'port': parts[1],
            'username': None,
            'password': None
        }
    elif len(parts) == 4:
        return {
            'ip': parts[0],
            'port': parts[1],
            'username': parts[2],
            'password': parts[3]
        }
    else:
        raise ValueError(f"Неверный формат прокси: {proxy_string}")

async def check_proxy(proxy_data, url_to_check):
    """
    Асинхронно проверяет работоспособность SOCKS5-прокси.

    :param proxy_data: Словарь с данными прокси или строка в формате IP:порт:логин:пароль
    :param url_to_check: URL, который нужно проверить через прокси
    :return: True, если прокси работает и может подключиться к URL, иначе False
    """
    # Если передана строка, парсим её
    if isinstance(proxy_data, str):
        proxy = parse_proxy_string(proxy_data)
    else:
        proxy = proxy_data
    
    proxy_url = f"socks5://"
    
    # Добавляем логин и пароль, если они есть
    if proxy.get('username') and proxy.get('password'):
        proxy_url += f"{proxy['username']}:{proxy['password']}@"
    
    proxy_url += f"{proxy['ip']}:{proxy['port']}"
    
    try:
        connector = aiohttp_socks.ProxyConnector.from_url(proxy_url)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url_to_check, timeout=10) as response:
                if response.status == 200:
                    print(f"Прокси {proxy['ip']}:{proxy['port']} работает и успешно подключился к {url_to_check}")
                    return True
                else:
                    print(f"Прокси {proxy['ip']}:{proxy['port']} вернул статус {response.status}")
                    return False
    except Exception as e:
        print(f"Прокси {proxy['ip']}:{proxy['port']} не работает: {e}")
        return False

async def check_all_proxies():
    """
    Проверяет все прокси из базы данных и возвращает результаты
    :return: Список строк с результатами проверки в формате "proxy -> status"
    """
    db = WoltDatabase()
    proxies = db.get_proxies()
    if not proxies:
        return []
    
    url = "https://api.ipify.org?format=json"
    
    tasks = []
    for proxy in proxies:
        # Если прокси хранятся в БД в полном формате (IP:порт:логин:пароль)
        if 'ip' in proxy and ':' in proxy['ip']:
            # Предполагаем, что полный формат хранится в поле 'ip'
            proxy_string = proxy['ip']
            proxy_data = parse_proxy_string(proxy_string)
            tasks.append(check_proxy(proxy_data, url))
        else:
            # Иначе используем стандартную структуру
            tasks.append(check_proxy(proxy, url))
    
    results = await asyncio.gather(*tasks)
    
    output = []
    i = 0
    for proxy in proxies:
        status = results[i]
        i += 1
        
        # Определяем строку прокси для отображения
        if 'ip' in proxy and ':' in proxy['ip']:
            # Предполагаем полный формат
            parts = proxy['ip'].split(':')
            proxy_str = proxy['ip']
            actual_ip = parts[0]
            actual_port = parts[1]
        else:
            # Стандартная структура
            proxy_str = f"{proxy['ip']}:{proxy['port']}"
            actual_ip = proxy['ip']
            actual_port = proxy['port']
            
        status_str = "active" if status else "inactive"
        output.append(f"{proxy_str} -> {status_str}")
        
        # Обновляем статус в БД
        with db.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE proxies SET status = %s WHERE ip = %s AND port = %s",
                (status_str, actual_ip, actual_port)
            )
            conn.commit()
    
    return output

# Пример использования
async def main():
    # Пример для тестирования с прокси в формате IP:порт:логин:пароль
    test_proxy = "191.102.148.33:9794:dvwBZD:xXFah2"
    url = "https://api.ipify.org?format=json"
    
    result = await check_proxy(test_proxy, url)
    print(f"{test_proxy} -> {'active' if result else 'inactive'}")
    
    # Проверка всех прокси из БД
    results = await check_all_proxies()
    print("Результаты проверки всех прокси:", results)

if __name__ == "__main__":
    asyncio.run(main())