// StoreCard.js
import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { useTranslation } from 'react-i18next';

// Стили для изображения
const StoreImage = styled.img`
  width: 100%;
  height: 150px; /* Фиксированная высота для единообразия */
  object-fit: cover; /* Изображение заполняет контейнер, сохраняя пропорции */
  background-color: ${({ theme }) => theme.colors.background}; /* Цвет фона для пустых областей */
  
  @media (max-width: 480px) {
    height: 120px; /* Уменьшаем высоту на маленьких экранах */
  }
`;

const Card = styled(Link)`
  display: flex;
  flex-direction: column;
  background-color: ${({ theme }) => theme.colors.background};
  border-radius: ${({ theme }) => theme.borderRadius.lg};
  overflow: hidden;
  box-shadow: ${({ theme }) => theme.shadows.md};
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  height: 100%;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: ${({ theme }) => theme.shadows.lg};
  }
  
  @media (prefers-color-scheme: dark) {
    background-color: #1e1e1e;
  }
  
  @media (max-width: 480px) {
    flex-direction: column;
    margin-bottom: 0.75rem;
  }
`;

const StoreInfo = styled.div`
  padding: 1.25rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  
  @media (max-width: 480px) {
    padding: 1rem;
  }
`;

const StoreName = styled.h2`
  font-size: ${({ theme }) => theme.fontSizes.lg};
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: ${({ theme }) => theme.colors.text};
  
  @media (max-width: 480px) {
    font-size: 1.1rem;
  }
`;

const StoreLocation = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.textLight};
  margin-bottom: 1rem;
  text-align: right;
  
  @media (max-width: 480px) {
    margin-bottom: 0.75rem;
    font-size: 0.85rem;
  }
`;

const DiscountInfo = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: auto;
  
  @media (max-width: 480px) {
    flex-wrap: wrap;
  }
`;

const DiscountStat = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
  
  @media (max-width: 480px) {
    margin-right: 1rem;
    margin-bottom: 0.5rem;
  }
`;

const StatLabel = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.textLight};
  white-space: nowrap;
`;

const StatValue = styled.span`
  font-size: ${({ theme }) => `calc(${theme.fontSizes.md} * 2)`};
  font-weight: 600;
  color: ${({ theme }) => theme.colors.primary};
  
  @media (max-width: 480px) {
    font-size: 0.95rem;
  }
`;

const ViewButton = styled.div`
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: ${({ theme }) => theme.colors.primary};
  color: white;
  text-align: center;
  font-weight: 500;
  border-radius: ${({ theme }) => theme.borderRadius.md};
  transition: background-color 0.2s ease;
  
  &:hover {
    background-color: ${({ theme }) => theme.colors.primary}dd;
  }
  
  @media (max-width: 480px) {
    margin-top: 0.75rem;
    padding: 0.6rem;
    font-size: 0.9rem;
  }
`;

const StoreCard = ({ store }) => {
  const { t } = useTranslation();

  return (
    <Card to={`/store/${store.id}`}>
      {/* Добавляем изображение магазина */}
      {store.image_url ? (
        <StoreImage src={store.image_url} alt={store.name} />
      ) : (
        <StoreImage src="https://via.placeholder.com/150" alt="No image available" />
      )}
      <StoreInfo>
        <StoreName>{store.name}</StoreName>
        <StoreLocation>{store.city.charAt(0).toUpperCase() + store.city.slice(1)}</StoreLocation>
        
        <DiscountInfo>
          <DiscountStat>
            <StatLabel>{t('discountCount')}</StatLabel>
            <StatValue>{store.discount_count}</StatValue>
          </DiscountStat>
        </DiscountInfo>
        
        <ViewButton>{t('viewStore')}</ViewButton>
      </StoreInfo>
    </Card>
  );
};

export default StoreCard;