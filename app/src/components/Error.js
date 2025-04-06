import React from 'react';
import styled from 'styled-components';
import { useTranslation } from 'react-i18next';

const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
  min-height: 200px;
`;

const ErrorIcon = styled.div`
  font-size: 3rem;
  color: ${({ theme }) => theme.colors.error};
  margin-bottom: 1rem;
`;

const ErrorMessage = styled.h3`
  font-size: ${({ theme }) => theme.fontSizes.lg};
  color: ${({ theme }) => theme.colors.text};
  margin-bottom: 1rem;
`;

const RetryButton = styled.button`
  background-color: ${({ theme }) => theme.colors.primary};
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: ${({ theme }) => theme.borderRadius.md};
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
  
  &:hover {
    background-color: ${({ theme }) => theme.colors.primary}dd;
  }
`;

const Error = ({ onRetry }) => {
  const { t } = useTranslation();
  
  return (
    <Container>
      <ErrorIcon>⚠️</ErrorIcon>
      <ErrorMessage>{t('error')}</ErrorMessage>
      {onRetry && (
        <RetryButton onClick={onRetry}>
          {t('retry')}
        </RetryButton>
      )}
    </Container>
  );
};

export default Error;
