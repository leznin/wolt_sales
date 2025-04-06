import React, { useEffect, useRef, useCallback, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import styled from 'styled-components';
import { useTranslation } from 'react-i18next';
import ScrollToTopButton from '../components/ScrollToTopButton';

// Components
import ProductCard from '../components/ProductCard';
import Loading from '../components/Loading';
import Error from '../components/Error';

// API
import { getStoreDiscounts, getStoreCategories, getCategoryItems } from '../utils/api';

// Styles
const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
  
  @media (max-width: 480px) {
    padding: 1rem 0.75rem;
  }
`;

const BackLink = styled(Link)`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: ${({ theme }) => theme.colors.primary};
  font-weight: 600;
  margin-bottom: 1.5rem;
  padding: 0.5rem 1rem;
  border-radius: ${({ theme }) => theme.borderRadius.md};
  transition: all 0.2s ease;
  background-color: rgba(0, 194, 232, 0.08);
  border: 1px solid rgba(0, 194, 232, 0.2);
  
  &:hover {
    background-color: rgba(0, 194, 232, 0.15);
    transform: translateX(-3px);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  }
  
  &:active {
    transform: translateX(-1px);
  }
  
  @media (max-width: 480px) {
    font-size: 0.9rem;
    margin-bottom: 1rem;
    padding: 0.4rem 0.8rem;
  }
`;

const StoreHeader = styled.div`
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  
  @media (max-width: 480px) {
    margin-bottom: 1.25rem;
  }
`;

const StoreNameRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
`;

const StoreName = styled.h1`
  font-size: ${({ theme }) => theme.fontSizes['2xl']};
  font-weight: 700;
  color: ${({ theme }) => theme.colors.text};
  margin: 0;
  
  @media (max-width: 480px) {
    font-size: 1.5rem;
  }
`;

const StoreLocation = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.md};
  color: ${({ theme }) => theme.colors.textLight};
  text-align: right;
  
  @media (max-width: 480px) {
    font-size: 0.9rem;
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
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: ${({ theme }) => theme.colors.textLight};
  pointer-events: none;
`;

const CategorySliderContainer = styled.div`
  margin: 1.5rem 0;
  display: grid;
  grid-auto-flow: column; /* Элементы в один ряд */
  gap: 0.01px;
  overflow-x: auto; /* Горизонтальный скроллинг */
  scrollbar-width: none; /* Скрыть ползунок в Firefox */
  -ms-overflow-style: none; /* Скрыть ползунок в IE/Edge */
  padding-bottom: 0.5rem;

  &::-webkit-scrollbar {
    display: none; /* Скрыть ползунок в Chrome, Safari и других Webkit-браузерах */
  }

  @media (max-width: 480px) {
    margin: 1rem 0;
  }
`;

const CategoryItem = styled.div`
  padding: 0.5rem 1rem;
  margin: 0 0.5rem;
  background-color: ${({ active, theme }) => active ? theme.colors.primary : '#4F4F4F'};
  color: ${({ active, theme }) => active ? 'white' : theme.colors.text};
  border-radius: ${({ theme }) => theme.borderRadius.md};
  cursor: pointer;
  text-align: center;
  transition: all 0.2s ease;
  white-space: nowrap;
  font-size: 0.9rem;
  
  &:hover {
    background-color: ${({ active, theme }) => active ? theme.colors.primary : '#e0e0e0'};
  }
  
  @media (max-width: 480px) {
    padding: 0.4rem 0.75rem;
    margin: 0 0.3rem;
    font-size: 0.8rem;
  }
`;

const SectionTitle = styled.h2`
  font-size: ${({ theme }) => theme.fontSizes.xl};
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: ${({ theme }) => theme.colors.text};
  
  @media (max-width: 480px) {
    font-size: 1.25rem;
    margin-bottom: 1rem;
  }
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
    font-size: 0.9rem;
  }
`;

const StoreDetail = () => {
  const { storeId } = useParams();
  const { t } = useTranslation();
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [data, setData] = React.useState(null);
  const [searchTerm, setSearchTerm] = React.useState('');
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categoryItems, setCategoryItems] = useState([]);
  const [loadingCategoryItems, setLoadingCategoryItems] = useState(false);
  const fetchingRef = useRef(false);
  const categoriesFetchingRef = useRef(false);
  const categoryItemsFetchingRef = useRef(false);

  const fetchData = useCallback(async () => {
    if (fetchingRef.current) return;
    
    try {
      setLoading(true);
      setError(null);
      fetchingRef.current = true;
      
      console.log(`Fetching store discounts for ID: ${storeId}`);
      const result = await getStoreDiscounts(storeId);
      console.log('Store discounts result:', result);
      
      setData(result);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching store discounts:', err);
      setError(err);
      setLoading(false);
    } finally {
      fetchingRef.current = false;
    }
  }, [storeId]);

  // Fetch categories for the store
  const fetchCategories = useCallback(async () => {
    if (categoriesFetchingRef.current || !storeId) return;
    
    try {
      categoriesFetchingRef.current = true;
      const categoriesData = await getStoreCategories(storeId);
      setCategories(categoriesData);
    } catch (err) {
      console.error('Error fetching categories:', err);
    } finally {
      categoriesFetchingRef.current = false;
    }
  }, [storeId]);

  // Fetch items for a specific category
  const fetchCategoryItems = useCallback(async (categoryId) => {
    if (categoryItemsFetchingRef.current || !categoryId) return;
    
    try {
      setLoadingCategoryItems(true);
      categoryItemsFetchingRef.current = true;
      const items = await getCategoryItems(categoryId);
      setCategoryItems(items);
    } catch (err) {
      console.error('Error fetching category items:', err);
    } finally {
      categoryItemsFetchingRef.current = false;
      setLoadingCategoryItems(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    
    // Очищаем состояние при размонтировании
    return () => {
      fetchingRef.current = false;
    };
  }, [fetchData, storeId]);

  useEffect(() => {
    if (storeId) {
      fetchCategories();
    }
    
    return () => {
      categoriesFetchingRef.current = false;
    };
  }, [fetchCategories, storeId]);

  // Загружаем товары при выборе категории
  useEffect(() => {
    if (selectedCategory && selectedCategory.id) {
      fetchCategoryItems(selectedCategory.id);
    } else {
      // Если категория не выбрана, очищаем список товаров категории
      setCategoryItems([]);
    }
    
    return () => {
      categoryItemsFetchingRef.current = false;
    };
  }, [selectedCategory, fetchCategoryItems]);

  const store = data?.store;
  const discounts = data?.discounts || [];

  // Функция для удаления дубликатов товаров по id
  const getUniqueProducts = (products) => {
    const uniqueMap = new Map();
    const duplicatesCount = {total: 0};
    
    products.forEach(product => {
      // Проверяем, что у товара есть id
      const productId = product.id || product.id_venue;
      
      if (productId && !uniqueMap.has(productId)) {
        uniqueMap.set(productId, product);
      } else if (productId) {
        // Считаем дубликаты для отладки
        duplicatesCount.total++;
      }
    });
    
    // Выводим информацию о дубликатах в консоль для отладки
    if (duplicatesCount.total > 0) {
      console.log(`Удалено ${duplicatesCount.total} дублирующихся товаров из категории "Все категории"`);
    }
    
    return Array.from(uniqueMap.values());
  };

  // Получаем уникальные товары для категории "All Categories"
  const uniqueDiscounts = !selectedCategory ? getUniqueProducts(discounts) : discounts;

  // Filter discounts based on search term and selected category
  const filteredDiscounts = selectedCategory && selectedCategory.id && categoryItems.length > 0
    ? categoryItems.filter(product => 
        searchTerm
          ? product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (product.description && product.description.toLowerCase().includes(searchTerm.toLowerCase()))
          : true
      )
    : uniqueDiscounts.filter(product => 
        searchTerm
          ? product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (product.description && product.description.toLowerCase().includes(searchTerm.toLowerCase()))
          : true
      );

  return (
    <Container>
      <BackLink to="/">
        ← {t('backToStores')}
      </BackLink>
      
      {loading ? (
        <Loading />
      ) : error ? (
        <Error onRetry={() => fetchData()} />
      ) : store ? (
        <>
          <StoreHeader>
            <StoreNameRow>
              <StoreName>{store.name}</StoreName>
              <SearchContainer>
                <SearchInput 
                  type="text" 
                  placeholder={t('searchProducts')}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <SearchIcon>🔍</SearchIcon>
              </SearchContainer>
            </StoreNameRow>
            <StoreLocation>{store.city.charAt(0).toUpperCase() + store.city.slice(1)}</StoreLocation>
          </StoreHeader>
          
          {categories.length > 0 && (
            <CategorySliderContainer>
              <CategoryItem active={!selectedCategory} onClick={() => setSelectedCategory('')}>
                {t('allCategories')}
              </CategoryItem>
              {categories.map((category, index) => (
                <CategoryItem
                  key={category.id || index}
                  active={selectedCategory && selectedCategory.id === category.id}
                  onClick={() => setSelectedCategory(category)}
                >
                  {category.name} {category.items_count ? `(${category.items_count})` : ''}
                </CategoryItem>
              ))}
            </CategorySliderContainer>
          )}
          
          <SectionTitle>
            {selectedCategory && selectedCategory.name 
              ? `${t('discountedProducts')} - ${selectedCategory.name}`
              : t('discountedProducts')
            }
          </SectionTitle>
          
          {loadingCategoryItems ? (
            <Loading />
          ) : filteredDiscounts.length > 0 ? (
            <Grid>
              {filteredDiscounts.map(product => (
                <ProductCard 
                  key={product.id} 
                  product={product} 
                  store={store}
                />
              ))}
            </Grid>
          ) : (
            <EmptyState>
              <p>{searchTerm || selectedCategory ? t('noSearchResults') : t('noDiscounts')}</p>
            </EmptyState>
          )}
        </>
      ) : (
        <EmptyState>
          <p>{t('storeNotFound')}</p>
        </EmptyState>
      )}
      <ScrollToTopButton />
    </Container>
  );
};

export default StoreDetail;