import React from 'react';
import styled, { keyframes } from 'styled-components';
import { useTranslation } from 'react-i18next';

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  min-height: 200px;
  
  @media (max-width: 480px) {
    padding: 1.5rem;
    min-height: 150px;
  }
`;

const Spinner = styled.div`
  width: 40px;
  height: 40px;
  border: 3px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: ${({ theme }) => theme.colors.primary};
  animation: ${spin} 1s ease-in-out infinite;
  margin-bottom: 1rem;
  
  @media (prefers-color-scheme: dark) {
    border-color: rgba(255, 255, 255, 0.1);
    border-top-color: ${({ theme }) => theme.colors.primary};
  }
  
  @media (max-width: 480px) {
    width: 30px;
    height: 30px;
    border-width: 2px;
    margin-bottom: 0.75rem;
  }
`;

const Text = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.md};
  color: ${({ theme }) => theme.colors.textLight};
  
  @media (max-width: 480px) {
    font-size: 0.9rem;
  }
`;

const Loading = () => {
  const { t } = useTranslation();
  
  return (
    <Container>
      <Spinner />
      <Text>{t('loading')}</Text>
    </Container>
  );
};

export default Loading;
