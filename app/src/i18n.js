import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
  en: {
    translation: {
      // General
      'appTitle': 'Promo Sniffer',
      'loading': 'Loading...',
      'error': 'Error loading data',
      'retry': 'Retry',
      'noDiscounts': 'No discounts available',
      'storeNotFound': 'Store not found',
      'searchStores': 'Search stores...',
      'searchProducts': 'Search products...',
      'noSearchResults': 'No results found matching your search',
      'allCategories': 'All Categories',
      
      // Stores
      'stores': 'Stores',
      'storesWithDiscounts': 'Stores with Discounts',
      'discountCount': 'Discount count',
      'avgDiscount': 'Avg. discount',
      'viewStore': 'View Store',
      'all': 'All',
      'supermarkets': 'Supermarkets',
      'pharmacies': 'Pharmacies',
      
      // Products
      'products': 'Products',
      'discountedProducts': 'Discounted Products',
      'productSearchResults': 'Product search results',
      'currentPrice': 'Current price',
      'originalPrice': 'Original price',
      'discount': 'Discount',
      'category': 'Category',
      'openInWolt': 'Open in Wolt',
      'backToStores': 'Back to Stores',
      
      // Language
      'language': 'Language',
      'english': 'English',
      'russian': 'Russian',
      
      // Location
      'location': 'Location',
      'deleteLocation': 'Delete location',
      'locationDeleted': 'Location deleted successfully',
      'errorDeletingLocation': 'Error deleting location',
      'editLocationName': 'Edit location name',
      'enterLocationName': 'Enter location name',
      'locationNameUpdated': 'Location name updated successfully',
      'errorUpdatingLocationName': 'Error updating location name',
      'save': 'Save',
      'cancel': 'Cancel',
      'selectedLocation': 'Selected location',
      'guest': 'Guest',
      'showingStoresWithin3km': 'showing stores within 3 km',
      'noStoresNearLocation': 'No stores with discounts found near this location',
      'sendLocationPrompt': 'Please send your location in Telegram to see stores with discounts near you',
    }
  },
  ru: {
    translation: {
      // General
      'appTitle': 'Скидочница',
      'loading': 'Загрузка...',
      'error': 'Ошибка загрузки данных',
      'retry': 'Повторить',
      'noDiscounts': 'Нет доступных скидок',
      'storeNotFound': 'Магазин не найден',
      'searchStores': 'Поиск магазинов...',
      'searchProducts': 'Поиск товаров...',
      'noSearchResults': 'Не найдено результатов по вашему запросу',
      'allCategories': 'Все категории',
      
      // Stores
      'stores': 'Магазины',
      'storesWithDiscounts': 'Магазины со скидками',
      'discountCount': 'Количество скидок',
      'avgDiscount': 'Средняя скидка',
      'viewStore': 'Просмотр магазина',
      'all': 'Все',
      'supermarkets': 'Супермаркеты',
      'pharmacies': 'Аптеки',
      
      // Products
      'products': 'Товары',
      'discountedProducts': 'Товары со скидкой',
      'productSearchResults': 'Результаты поиска товаров',
      'currentPrice': 'Текущая цена',
      'originalPrice': 'Исходная цена',
      'discount': 'Скидка',
      'category': 'Категория',
      'openInWolt': 'Открыть в Wolt',
      'backToStores': 'Назад к магазинам',
      
      // Language
      'language': 'Язык',
      'english': 'Английский',
      'russian': 'Русский',
      
      // Location
      'location': 'Геопозиция',
      'deleteLocation': 'Удалить геопозицию',
      'locationDeleted': 'Геопозиция успешно удалена',
      'errorDeletingLocation': 'Ошибка при удалении геопозиции',
      'editLocationName': 'Изменить название геопозиции',
      'enterLocationName': 'Введите название геопозиции',
      'locationNameUpdated': 'Название геопозиции успешно обновлено',
      'errorUpdatingLocationName': 'Ошибка при обновлении названия геопозиции',
      'save': 'Сохранить',
      'cancel': 'Отмена',
      'selectedLocation': 'Выбранная геопозиция',
      'guest': 'Гость',
      'showingStoresWithin3km': 'показаны магазины в радиусе 3 км',
      'noStoresNearLocation': 'Рядом с этой геопозицией не найдено магазинов со скидками',
      'sendLocationPrompt': 'Пожалуйста, отправьте свою геопозицию в Telegram, чтобы увидеть магазины со скидками рядом с вами',
    }
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    }
  });

export default i18n;
