import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [userData, setUserData] = useState(null);
  const [avatarPath, setAvatarPath] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchUserData() {
      try {
        // Получение initData из Telegram WebApp
        const initData = window.Telegram?.WebApp?.initData;
        
        // Генерация простого fingerprint (в производстве использовать более надежный метод)
        const fingerprint = navigator.userAgent;
        
        if (initData) {
          // Отправка данных на сервер
          const response = await axios.post('/webhook', { 
            initData, 
            fingerprint 
          });
          
          setUserData(response.data.user);
          setAvatarPath(response.data.avatarPath);
        } else {
          // Для тестирования - запрос тестовых данных пользователя
          console.log('Telegram WebApp не определен, используются тестовые данные');
        }
      } catch (error) {
        console.error('Error fetching user data:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchUserData();
  }, []);

  return (
    <UserContext.Provider value={{ userData, avatarPath, loading }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);