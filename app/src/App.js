import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { createGlobalStyle, ThemeProvider } from 'styled-components';
import { useTranslation } from 'react-i18next';
import { useUser } from './context/UserContext';
import { LocationProvider } from './contexts/LocationContext';

// Pages
import StoreList from './pages/StoreList';
import StoreDetail from './pages/StoreDetail';

// Components
import Header from './components/Header';

const theme = {
  colors: {
    primary: '#0066FF',        // Оставляем как акцентный цвет
    secondary: '#FF3366',      // Оставляем как акцентный цвет
    background: '#121212',     // Тёмный фон
    surface: '#1E1E1E',        // Тёмная поверхность для карточек/элементов
    text: '#F8F9FA',          // Светлый текст
    textLight: '#A1A1AA',     // Более мягкий светлый текст для второстепенных элементов
    success: '#10B981',
    error: '#EF4444',
    discount: '#FF3366',
  },
  fonts: {
    body: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif",
    heading: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif",
  },
  fontSizes: {
    xs: '0.75rem',
    sm: '0.875rem',
    md: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
  },
  space: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '4rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '1rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  },
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
  },
};

const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  html, body {
    font-family: ${({ theme }) => theme.fonts.body};
    background-color: ${({ theme }) => theme.colors.background};
    color: ${({ theme }) => theme.colors.text};
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-size: 16px;
    line-height: 1.5;
    overflow-x: hidden;
  }

  a {
    color: inherit;
    text-decoration: none;
  }

  button {
    cursor: pointer;
    font-family: inherit;
  }

  img {
    max-width: 100%;
    height: auto;
  }

  input {
    background-color: #FFFFFF; /* Белый фон для поля ввода */
    color: #000000; /* Чёрный текст при вводе */
    border: 1px solid #333333; /* Тёмная граница для контраста с тёмным фоном */
    border-radius: ${({ theme }) => theme.borderRadius.sm};
    padding: ${({ theme }) => theme.space.sm} ${({ theme }) => theme.space.md};
    font-size: ${({ theme }) => theme.fontSizes.md};
  }

  input::placeholder {
    color: #666666; /* Серый цвет для placeholder */
    opacity: 1; /* Убираем прозрачность, если она мешает */
  }

  input:focus {
    outline: none;
    border-color: ${({ theme }) => theme.colors.primary}; /* Подсветка при фокусе */
  }

`;

function App() {
  useTranslation();
  const { avatarPath, loading, userData } = useUser();

  return (
    <ThemeProvider theme={theme}>
      <LocationProvider>
        <GlobalStyle />
        {!loading && <Header avatarPath={avatarPath} userData={userData} />}
        <main>
          <Routes>
            <Route path="/" element={<StoreList />} />
            <Route path="/store/:storeId" element={<StoreDetail />} />
          </Routes>
        </main>
      </LocationProvider>
    </ThemeProvider>
  );
}

export default App;