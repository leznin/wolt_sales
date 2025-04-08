import React, { useState, useEffect, useContext, useCallback } from 'react';
import styled from 'styled-components';
import { useTranslation } from 'react-i18next';
import ScrollToTopButton from '../components/ScrollToTopButton';

// Components
import StoreCard from '../components/StoreCard';
import Loading from '../components/Loading';
import Error from '../components/Error';

// API
import { getVenueTypes, getStoresByLocation, searchProducts } from '../utils/api';

// Добавляем контекст для доступа к выбранной локации
import { LocationContext } from '../contexts/LocationContext';

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
  
  @media (max-width: 480px) {
    padding: 1rem 0.75rem;
  }
`;

const HeaderContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  @media (max-width: 480px) {
    align-items: center;
  }
`;

const Title = styled.h1`
  font-size: ${({ theme }) => theme.fontSizes['2xl']};
  font-weight: 700;
  color: ${({ theme }) => theme.colors.text};
  margin: 0;
  
  @media (max-width: 480px) {
    font-size: 1.5rem;
    text-align: center;
  }
`;

const SearchContainer = styled.div`
  position: relative;
  width: 300px;
  
  @media (max-width: 768px) {
    width: 100%;
  }
`;

const SearchInput = styled.input`
  width: 100%;
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.borderRadius.md};
  font-size: ${({ theme }) => theme.fontSizes.md};
  
  &:focus {
    outline: none;
    border-color: ${({ theme }) => theme.colors.primary};
    box-shadow: 0 0 0 2px ${({ theme }) => theme.colors.primary}33;
  }
  
  @media (max-width: 480px) {
    font-size: 0.9rem;
    padding: 0.4rem 2rem 0.4rem 0.75rem;
  }
`;

const SearchIcon = styled.span`
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: ${({ theme }) => theme.colors.textLight};
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  @media (max-width: 480px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem 1rem;
  color: ${({ theme }) => theme.colors.textLight};
  
  @media (max-width: 480px) {
    padding: 2rem 0.5rem;
  }
`;

const VenueTypeMenu = styled.div`
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  
  @media (max-width: 480px) {
    justify-content: center;
    gap: 0.75rem;
  }
`;

const VenueTypeButton = styled.button`
  padding: 0.5rem 1rem;
  border-radius: ${({ theme }) => theme.borderRadius.md};
  font-size: ${({ theme }) => theme.fontSizes.md};
  font-weight: ${({ active }) => (active ? '700' : '500')};
  background-color: ${({ theme, active }) => (active ? '#0066cc' : '#f0f0f0')};
  color: ${({ theme, active }) => (active ? '#ffffff' : '#333333')};
  border: 1px solid ${({ theme, active }) => (active ? '#0055bb' : '#dddddd')};
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  
  &:hover {
    background-color: ${({ theme, active }) => (active ? '#0055bb' : '#e0e0e0')};
    border-color: ${({ theme, active }) => (active ? '#004499' : '#cccccc')};
  }
  
  &:focus {
    outline: none;
    box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.3);
  }
  
  @media (max-width: 480px) {
    font-size: 0.9rem;
    padding: 0.4rem 0.8rem;
  }
`;

const NoLocationMessage = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  
  p {
    font-size: ${({ theme }) => theme.fontSizes.lg};
    color: ${({ theme }) => theme.colors.textLight};
    margin-bottom: 0;
  }
`;

// Стили для продуктовых карточек
const ProductGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  @media (max-width: 480px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
`;

const ProductCard = styled.div`
  display: flex;
  flex-direction: column;
  background-color: ${({ theme }) => theme.colors?.background || '#ffffff'};
  border-radius: 0.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  height: 100%;
  position: relative;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  @media (prefers-color-scheme: dark) {
    background-color: #1e1e1e;
  }
`;

const ImageContainer = styled.div`
  position: relative;
  padding-top: 75%; /* 4:3 aspect ratio */
  overflow: hidden;
  background-color: #f5f5f5;
  
  @media (prefers-color-scheme: dark) {
    background-color: #2a2a2a;
  }
`;

const ProductImage = styled.img`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
  
  ${ProductCard}:hover & {
    transform: scale(1.05);
  }
`;



const DiscountTag = styled.span`
  background-color: #ff5252;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 2rem;
  font-weight: 600;
  font-size: 0.875rem;
  margin-left: 0.75rem;
  
  @media (max-width: 480px) {
    padding: 0.2rem 0.6rem;
    font-size: 0.7rem;
  }
`;

const ProductInfo = styled.div`
  padding: 1.25rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  
  @media (max-width: 480px) {
    padding: 1rem;
  }
`;

const ProductName = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #333;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  
  @media (prefers-color-scheme: dark) {
    color: #f0f0f0;
  }
  
  @media (max-width: 480px) {
    font-size: 0.95rem;
    margin-bottom: 0.3rem;
  }
`;

const ProductDescription = styled.p`
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.75rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  
  @media (prefers-color-scheme: dark) {
    color: #aaa;
  }
  
  @media (max-width: 480px) {
    font-size: 0.8rem;
    margin-bottom: 0.5rem;
  }
`;

const PriceContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
  margin-bottom: 0.5rem;
`;

const PriceWrapper = styled.div`
  display: flex;
  align-items: baseline;
`;

const CurrentPrice = styled.span`
  font-size: 1.25rem;
  font-weight: 700;
  color: #00C2E8;
  
  @media (max-width: 480px) {
    font-size: 1.1rem;
  }
  
  @media (prefers-color-scheme: dark) {
    color: #00D4FF;
  }
`;

const CurrencySymbol = styled.span`
  font-weight: 500;
  margin-left: 2px;
  display: inline-block;
  color: inherit;
  font-size: 0.85em;
  vertical-align: baseline;
  opacity: 0.9;
`;

const StoreBadge = styled.div`
  margin-top: auto;
  display: flex;
  align-items: center;
  padding: 0.75rem 1.25rem;
  border-top: 1px solid #eee;
  background-color: rgba(0, 0, 0, 0.02);
  
  @media (prefers-color-scheme: dark) {
    border-top: 1px solid #333;
    background-color: rgba(255, 255, 255, 0.03);
  }
`;

const StoreColorDot = styled.span`
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #0066cc;
  margin-right: 0.5rem;
`;

const StoreName = styled.div`
  font-weight: 600;
  color: #0066cc;
  margin-right: 0.5rem;
  font-size: 0.9rem;
`;

const StoreDistance = styled.div`
  font-size: 0.8rem;
  color: #666;
  margin-left: auto;
  
  @media (prefers-color-scheme: dark) {
    color: #aaa;
  }
`;

const ProductSearchHeading = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  margin: 1.5rem 0 1rem;
  color: #333;
  
  @media (prefers-color-scheme: dark) {
    color: #f0f0f0;
  }
`;

const getVenueTypeTranslation = (venueType) => {
  switch (venueType) {
    case 'supermarket':
      return 'Супермаркеты';
    case 'pharmacy':
      return 'Аптеки';
    default:
      return venueType;
  }
};

const StoreList = () => {
  const { t } = useTranslation();
  const [selectedVenueType, setSelectedVenueType] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [venueTypes, setVenueTypes] = useState([]);
  const [isLoadingVenueTypes, setIsLoadingVenueTypes] = useState(true);
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [products, setProducts] = useState([]); // Добавляем состояние для хранения результатов поиска товаров
  
  // Получаем выбранную локацию и состояние загрузки из контекста
  const { selectedLocation, isLoading: isLoadingLocation } = useContext(LocationContext);
  
  // Загрузка списка магазинов
  const fetchStores = useCallback(async () => {
    // Если нет выбранной геопозиции и загрузка геопозиции завершена, не загружаем магазины
    if (!selectedLocation && !isLoadingLocation) {
      setStores([]);
      setLoading(false);
      return;
    }
    
    // Если геопозиция загружается, ждем
    if (isLoadingLocation) {
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      console.log('Загрузка магазинов рядом с локацией:', selectedLocation);
      const fetchedStores = await getStoresByLocation(
        selectedLocation.lat,
        selectedLocation.lon,
        3, // радиус в километрах
        selectedVenueType
      );
      
      // Сортируем магазины по расстоянию (ближайшие сначала)
      fetchedStores.sort((a, b) => (a.distance || 0) - (b.distance || 0));
      setStores(fetchedStores);
    } catch (error) {
      console.error('Error fetching stores:', error);
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [selectedVenueType, selectedLocation, isLoadingLocation]);
  
  // Загрузка магазинов при изменении локации или типа заведения
  useEffect(() => {
    fetchStores();
  }, [fetchStores]);
  
  // Загрузка типов заведений при монтировании компонента
  useEffect(() => {
    const fetchVenueTypes = async () => {
      setIsLoadingVenueTypes(true);
      try {
        const types = await getVenueTypes();
        setVenueTypes(types);
      } catch (error) {
        console.error('Error fetching venue types:', error);
      } finally {
        setIsLoadingVenueTypes(false);
      }
    };
    
    fetchVenueTypes();
  }, []);
  
  // Фильтрация магазинов по поисковому запросу
  const filteredStores = stores?.filter(store => 
    store.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Удаление дубликатов магазинов на основе их ID
  const getUniqueStores = (storesList) => {
    if (!storesList) return [];
    const uniqueStores = [];
    const storeIds = new Set();
    
    storesList.forEach(store => {
      if (!storeIds.has(store.id)) {
        storeIds.add(store.id);
        uniqueStores.push(store);
      }
    });
    
    return uniqueStores;
  };
  
  const uniqueFilteredStores = getUniqueStores(filteredStores);
  
  // Поиск товаров при изменении поискового запроса
  useEffect(() => {
    if (searchTerm.length < 2) {
      setProducts([]);
      return;
    }
    
    // Используем debounce для предотвращения слишком частых запросов
    const timer = setTimeout(async () => {
      try {
        // Всегда используем местоположение для поиска товаров, если оно доступно
        const results = selectedLocation 
          ? await searchProducts(
              searchTerm, 
              selectedLocation.lat, 
              selectedLocation.lon, 
              3 // радиус в километрах
            )
          : await searchProducts(searchTerm);
        
        setProducts(results);
      } catch (error) {
        console.error('Ошибка при поиске товаров:', error);
        setProducts([]);
      }
    }, 300);
    
    return () => clearTimeout(timer);
  }, [searchTerm, selectedLocation]);
  
  // Обработчик изменения поискового запроса
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  
  return (
    <Container>
      <HeaderContainer>
        <Title>{t('storesWithDiscounts')}</Title>
        <SearchContainer>
          <SearchInput 
            type="text" 
            placeholder={t('searchStores')}
            value={searchTerm}
            onChange={handleSearchChange}
          />
          <SearchIcon>🔍</SearchIcon>
        </SearchContainer>
      </HeaderContainer>
      
      {!isLoadingVenueTypes && venueTypes.length > 0 && (
        <VenueTypeMenu>
          <VenueTypeButton 
            active={selectedVenueType === null} 
            onClick={() => setSelectedVenueType(null)}
          >
            {t('all')}
          </VenueTypeButton>
          {venueTypes.map(type => (
            <VenueTypeButton 
              key={type} 
              active={selectedVenueType === type} 
              onClick={() => setSelectedVenueType(type)}
            >
              {type === 'supermarket' 
                ? t('supermarkets') 
                : type === 'pharmacy' 
                  ? t('pharmacies') 
                  : type === 'cosmetics' 
                    ? t('cosmetics') 
                    : type === 'pet-supplies' 
                      ? t('pet-supplies')
                      : getVenueTypeTranslation(type)}
            </VenueTypeButton>
          ))}
        </VenueTypeMenu>
      )}
      
      {/* Отображение результатов поиска */}
      {searchTerm && (
        <>
          {/* Отображение магазинов */}
          {loading || isLoadingLocation ? (
            <Loading />
          ) : error ? (
            <Error onRetry={fetchStores} />
          ) : uniqueFilteredStores && uniqueFilteredStores.length > 0 ? (
            <Grid>
              {uniqueFilteredStores.map(store => (
                <StoreCard 
                  key={store.id} 
                  store={store} 
                  onClick={() => window.location.href = `/store/${store.id}`}
                />
              ))}
            </Grid>
          ) : selectedLocation ? (
            <EmptyState>
              {searchTerm ? (
                <p>{t('noSearchResults')}</p>
              ) : selectedVenueType ? (
                <p>Нет магазинов с акциями в категории {getVenueTypeTranslation(selectedVenueType)}</p>
              ) : (
                <p>{t('noStoresNearLocation')}</p>
              )}
            </EmptyState>
          ) : (
            <NoLocationMessage>
              <p>{t('sendLocationPrompt')}</p>
            </NoLocationMessage>
          )}
          
          {/* Отображение результатов поиска товаров */}
          {searchTerm && products.length > 0 && (
            <div style={{ marginBottom: '2rem' }}>
              <ProductSearchHeading>{t('productSearchResults')}</ProductSearchHeading>
              <ProductGrid>
                {products.map(product => (
                  <ProductCard 
                    key={`${product.id}-${product.store_id || 'unknown'}`}
                    onClick={() => {
                      console.log('Redirecting to store:', product.store_id, product.store_name);
                      if (product.store_id) {
                        window.location.href = `/store/${product.store_id}`;
                      } else {
                        console.error('Missing store_id for product:', product);
                      }
                    }}
                  >
                    <ImageContainer>
                      {product.image_url ? (
                        <ProductImage src={product.image_url} alt={product.name} />
                      ) : (
                        <ProductImage src="/images/default-product.jpg" alt={product.name} />
                      )}
                    </ImageContainer>
                    <ProductInfo>
                      <ProductName>{product.name}</ProductName>
                      <ProductDescription>{product.description}</ProductDescription>
                      <PriceContainer>
                        <PriceWrapper>
                          <CurrentPrice>
                            {product.current_price} 
                            <CurrencySymbol>{product.currency === 'GEL' ? 'GEL' : product.currency || '₾'}</CurrencySymbol>
                          </CurrentPrice>
                        </PriceWrapper>
                        {product.discount_percentage > 0 && (
                          <DiscountTag>-{Math.round(product.discount_percentage)}%</DiscountTag>
                        )}
                      </PriceContainer>
                    </ProductInfo>
                    <StoreBadge>
                      <StoreColorDot />
                      <StoreName>{product.store_name}</StoreName>
                      {product.distance && (
                        <StoreDistance>{(product.distance).toFixed(1)} км</StoreDistance>
                      )}
                    </StoreBadge>
                  </ProductCard>
                ))}
              </ProductGrid>
            </div>
          )}
        </>
      )}
      
      {/* Отображение магазинов, если нет поискового запроса */}
      {!searchTerm && (
        <>
          {loading || isLoadingLocation ? (
            <Loading />
          ) : error ? (
            <Error onRetry={fetchStores} />
          ) : uniqueFilteredStores && uniqueFilteredStores.length > 0 ? (
            <Grid>
              {uniqueFilteredStores.map(store => (
                <StoreCard 
                  key={store.id} 
                  store={store} 
                  onClick={() => window.location.href = `/store/${store.id}`}
                />
              ))}
            </Grid>
          ) : selectedLocation ? (
            <EmptyState>
              {selectedVenueType ? (
                <p>Нет магазинов с акциями в категории {getVenueTypeTranslation(selectedVenueType)}</p>
              ) : (
                <p>{t('noStoresNearLocation')}</p>
              )}
            </EmptyState>
          ) : (
            <NoLocationMessage>
              <p>{t('sendLocationPrompt')}</p>
            </NoLocationMessage>
          )}
        </>
      )}
      <ScrollToTopButton />
    </Container>
  );
};

export default StoreList;
