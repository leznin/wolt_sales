import axios from 'axios';

const API_URL = process.env.NODE_ENV === 'production' 
  ? '/api' 
  : 'http://localhost:5001/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Add timeout to prevent long waiting times
  timeout: 10000,
});

// Add interceptors to handle errors globally
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.message);
    // Return a rejected promise with a more user-friendly error
    return Promise.reject({
      message: 'Failed to connect to the server. Please try again later.',
      originalError: error
    });
  }
);

export const getStoresWithDiscounts = async (venueType = null) => {
  try {
    const url = venueType ? `/stores?venue_type=${venueType}` : '/stores';
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    console.error('Error fetching stores with discounts:', error);
    throw error;
  }
};

export const getStoreDiscounts = async (storeId) => {
  try {
    // Исправляем путь API, чтобы он соответствовал маршруту на сервере
    // Убираем префикс /api, так как он уже добавлен в baseURL
    console.log(`Fetching discounts for store ${storeId}`);
    const response = await api.get(`/store/${storeId}/discounts`);
    console.log('Response received:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error fetching discounts for store ${storeId}:`, error);
    throw error;
  }
};

export const getTopDiscounts = async (limit = 50, minDiscount = 10) => {
  try {
    const response = await api.get(`/top-discounts?limit=${limit}&min_discount=${minDiscount}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching top discounts:', error);
    throw error;
  }
};

export const getVenueTypes = async () => {
  try {
    const response = await api.get('/venue-types');
    return response.data;
  } catch (error) {
    console.error('Error fetching venue types:', error);
    throw error;
  }
};

export const getUserLocations = async (userId) => {
  try {
    const response = await api.get(`/user-locations/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching user locations:', error);
    return [];
  }
};

// Удаление геопозиции пользователя
export const deleteUserLocation = async (locationId) => {
  try {
    const response = await axios.delete(`/api/user-locations/${locationId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting user location:', error);
    throw error;
  }
};

// Обновление имени геопозиции пользователя
export const updateUserLocationName = async (locationId, name) => {
  try {
    const response = await axios.put(`/api/user-locations/${locationId}`, { name });
    return response.data;
  } catch (error) {
    console.error('Error updating user location name:', error);
    throw error;
  }
};

// Получение категорий магазина
export const getStoreCategories = async (storeId) => {
  try {
    console.log(`Fetching categories for store ${storeId}`);
    const response = await api.get(`/store/${storeId}/categories`);
    console.log('Categories received:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error fetching categories for store ${storeId}:`, error);
    return [];
  }
};

// Получение товаров по категории
export const getCategoryItems = async (categoryId, limit = 100, offset = 0) => {
  try {
    console.log(`Fetching items for category ${categoryId}`);
    const response = await api.get(`/category/${categoryId}/items?limit=${limit}&offset=${offset}`);
    console.log('Category items received:', response.data);
    return response.data;
  } catch (error) {
    console.error(`Error fetching items for category ${categoryId}:`, error);
    return [];
  }
};

// Получение магазинов рядом с заданной геопозицией
export const getStoresByLocation = async (latitude, longitude, radius = 3, venueType = null) => {
  try {
    let url = `${API_URL}/stores-by-location?lat=${latitude}&lon=${longitude}&radius=${radius}`;
    if (venueType) {
      url += `&venue_type=${venueType}`;
    }
    
    console.log(`Fetching stores near location (${latitude}, ${longitude}) with URL: ${url}`);
    const response = await axios.get(url);
    console.log('Stores by location received:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching stores by location:', error);
    // Добавляем детали ошибки для лучшей отладки
    if (error.response) {
      console.error('Response error data:', error.response.data);
      console.error('Response error status:', error.response.status);
    }
    return [];
  }
};

// Получение последней геопозиции пользователя из Telegram
export const getUserLastLocation = async () => {
  try {
    // Получаем Telegram User ID из localStorage или из Telegram WebApp
    let telegramUserId = null;
    
    if (window.Telegram && window.Telegram.WebApp) {
      telegramUserId = window.Telegram.WebApp.initDataUnsafe?.user?.id;
    }
    
    // Если не удалось получить ID из Telegram WebApp, пытаемся получить из localStorage
    if (!telegramUserId) {
      telegramUserId = localStorage.getItem('telegramUserId');
    }
    
    // Если ID не найден, возвращаем null
    if (!telegramUserId) {
      console.log('Telegram User ID not found');
      return null;
    }
    
    console.log(`Fetching last location for user ${telegramUserId}`);
    const response = await api.get(`/user-last-location/${telegramUserId}`);
    console.log('User last location received:', response.data);
    
    // Если получена геопозиция, сохраняем ID пользователя в localStorage
    if (response.data) {
      localStorage.setItem('telegramUserId', telegramUserId);
    }
    
    return response.data;
  } catch (error) {
    console.error('Error fetching user last location:', error);
    return null;
  }
};

// Поиск товаров по названию (используя API-эндпоинт)
export const searchProducts = async (searchTerm, latitude = null, longitude = null, radius = 3) => {
  try {
    let url = `/api/search-products?query=${encodeURIComponent(searchTerm)}`;
    
    // Если указаны координаты, добавляем их в запрос
    if (latitude !== null && longitude !== null) {
      url += `&lat=${latitude}&lon=${longitude}&radius=${radius}`;
    }
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const products = await response.json();
    console.log(`Найдено ${products.length} товаров по запросу "${searchTerm}"`);
    
    return products;
  } catch (error) {
    console.error('Ошибка при поиске товаров:', error);
    return [];
  }
};
