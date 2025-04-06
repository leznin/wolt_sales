import React, { createContext, useState, useEffect } from 'react';
import { getUserLastLocation } from '../utils/api';

export const LocationContext = createContext();

export const LocationProvider = ({ children }) => {
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Загружаем геопозицию пользователя при запуске
  useEffect(() => {
    const loadLocation = async () => {
      setIsLoading(true);
      
      try {
        // Сначала пытаемся загрузить из localStorage
        const savedLocation = localStorage.getItem('lastLocation');
        if (savedLocation) {
          try {
            const parsedLocation = JSON.parse(savedLocation);
            setSelectedLocation(parsedLocation);
            console.log('Загружена геопозиция из localStorage:', parsedLocation);
            setIsLoading(false);
            return;
          } catch (error) {
            console.error('Ошибка при загрузке геопозиции из localStorage:', error);
            localStorage.removeItem('lastLocation');
          }
        }
        
        // Если в localStorage ничего нет, пытаемся получить из API
        const userLocation = await getUserLastLocation();
        if (userLocation && userLocation.lat && userLocation.lon) {
          const location = {
            lat: userLocation.lat,
            lon: userLocation.lon
          };
          setSelectedLocation(location);
          localStorage.setItem('lastLocation', JSON.stringify(location));
          console.log('Загружена геопозиция из Telegram:', location);
        } else {
          console.log('Геопозиция пользователя не найдена');
        }
      } catch (error) {
        console.error('Ошибка при загрузке геопозиции:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadLocation();
  }, []);

  // Функция для установки геопозиции с сохранением в localStorage
  const saveLocation = (location) => {
    setSelectedLocation(location);
    if (location) {
      localStorage.setItem('lastLocation', JSON.stringify(location));
      console.log('Сохранена новая геопозиция:', location);
    } else {
      localStorage.removeItem('lastLocation');
      console.log('Геопозиция удалена');
    }
  };

  return (
    <LocationContext.Provider value={{ 
      selectedLocation, 
      setSelectedLocation: saveLocation,
      isLoading
    }}>
      {children}
    </LocationContext.Provider>
  );
};

export default LocationProvider;
