import React from 'react';
import styled from 'styled-components';
import { useTranslation } from 'react-i18next';

const Card = styled.div`
  display: flex;
  flex-direction: column;
  background-color: ${({ theme }) => theme.colors.background};
  border-radius: ${({ theme }) => theme.borderRadius.lg};
  overflow: hidden;
  box-shadow: ${({ theme }) => theme.shadows.md};
  height: 100%;
  position: relative;
  
  @media (prefers-color-scheme: dark) {
    background-color: #1e1e1e;
  }
  
  @media (max-width: 480px) {
    border-radius: ${({ theme }) => theme.borderRadius.md};
  }
`;

const ImageContainer = styled.div`
  position: relative;
  padding-top: 75%; /* 4:3 aspect ratio */
  overflow: hidden;
`;

const ProductImage = styled.img`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
  
  ${Card}:hover & {
    transform: scale(1.05);
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
  font-size: ${({ theme }) => theme.fontSizes.md};
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: ${({ theme }) => theme.colors.text};
  
  @media (max-width: 480px) {
    font-size: 0.95rem;
    margin-bottom: 0.3rem;
  }
`;

const ProductCategory = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.textLight};
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  
  @media (max-width: 480px) {
    font-size: 0.65rem;
    margin-bottom: 0.5rem;
    letter-spacing: 0.3px;
  }
`;

const PriceContainer = styled.div`
  display: flex;
  justify-content: space-between; /* Распределяет элементы по краям */
  align-items: baseline;
  margin-top: auto;
  
  @media (max-width: 480px) {
    gap: 0.3rem;
  }
`;

const PriceWrapper = styled.div`
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  
  @media (max-width: 480px) {
    gap: 0.3rem;
  }
`;

const CurrentPrice = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.lg};
  font-weight: 700;
  color: ${({ theme }) => theme.colors.primary};
  
  @media (max-width: 480px) {
    font-size: 1.1rem;
  }
`;

// eslint-disable-next-line no-unused-vars
const OriginalPrice = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.textLight};
  text-decoration: line-through;
  
  @media (max-width: 480px) {
    font-size: 0.8rem;
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

const DiscountBadge = styled.span`
  background-color: ${({ theme }) => theme.colors.discount};
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: ${({ theme }) => theme.borderRadius.full};
  font-weight: 600;
  font-size: ${({ theme }) => theme.fontSizes.sm};
  
  @media (max-width: 480px) {
    padding: 0.2rem 0.6rem;
    font-size: 0.7rem;
  }
`;

const WoltButton = styled.a`
  display: block;
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #00C2E8; /* Wolt blue */
  color: white;
  text-align: center;
  font-weight: 500;
  border-radius: ${({ theme }) => theme.borderRadius.md};
  transition: background-color 0.2s ease;
  
  &:hover {
    background-color: #00A8CC;
  }
  
  @media (max-width: 480px) {
    margin-top: 0.75rem;
    padding: 0.6rem;
    font-size: 0.9rem;
  }
`;

const ProductCard = ({ product, store }) => {
  const { t } = useTranslation();
  
  const woltUrl = `https://wolt.com/en/geo/${store.city}/venue/${store.slug}/itemid-${product.id_venue}`;
  const imageUrl = product.image_url || '/images/default-product.jpg';
  
  return (
    <Card>
      <ImageContainer>
        <ProductImage src={imageUrl} alt={product.name} />
      </ImageContainer>
      
      <ProductInfo>
        <ProductName>{product.name}</ProductName>
        {product.category && <ProductCategory>{product.category}</ProductCategory>}
        
        <PriceContainer>
          <PriceWrapper>
            <CurrentPrice>
              {product.current_price} <CurrencySymbol>{store.currency}</CurrencySymbol>
            </CurrentPrice>
          </PriceWrapper>
          {product.discount_percentage > 0 && (
            <DiscountBadge>-{Math.round(product.discount_percentage)}%</DiscountBadge>
          )}
        </PriceContainer>
        
        <WoltButton href={woltUrl} target="_blank" rel="noopener noreferrer">
          {t('openInWolt')}
        </WoltButton>
      </ProductInfo>
    </Card>
  );
};

export default ProductCard;