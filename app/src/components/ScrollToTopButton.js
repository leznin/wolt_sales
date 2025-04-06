import React, { useState, useEffect } from 'react';
import styled, { keyframes } from 'styled-components';

// Анимация пульсации
const pulse = keyframes`
  0% {
    box-shadow: 0 0 0 0 rgba(0, 102, 255, 0.4);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(0, 102, 255, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(0, 102, 255, 0);
  }
`;

// Анимация стрелки
const arrowBounce = keyframes`
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-5px);
  }
  60% {
    transform: translateY(-3px);
  }
`;

const Button = styled.button`
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: ${({ theme }) => `linear-gradient(135deg, ${theme.colors.primary}, #0044cc)`};
  color: white;
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(0, 102, 255, 0.3);
  opacity: ${({ visible }) => (visible ? 1 : 0)};
  transform: ${({ visible }) => (visible ? 'scale(1)' : 'scale(0.8)')};
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  z-index: 1000;
  backdrop-filter: blur(5px);
  animation: ${({ visible }) => (visible ? pulse : 'none')} 2s infinite;
  
  &:hover {
    background: ${({ theme }) => `linear-gradient(135deg, #0055dd, #003cb3)`};
    transform: ${({ visible }) => (visible ? 'scale(1.05)' : 'scale(0.8)')};
    box-shadow: 0 6px 20px rgba(0, 102, 255, 0.4);
  }
  
  &:active {
    transform: ${({ visible }) => (visible ? 'scale(0.95)' : 'scale(0.8)')};
  }
  
  @media (max-width: 480px) {
    width: 55px;
    height: 55px;
    bottom: 30px;
    right: 30px;
  }
`;

const ArrowContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  animation: ${arrowBounce} 2s infinite;
`;

const ScrollToTopButton = () => {
  const [isVisible, setIsVisible] = useState(false);
  
  // Функция для прокрутки вверх
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };
  
  // Отслеживание прокрутки для показа/скрытия кнопки
  useEffect(() => {
    const toggleVisibility = () => {
      if (window.pageYOffset > 300) {
        setIsVisible(true);
      } else {
        setIsVisible(false);
      }
    };
    
    window.addEventListener('scroll', toggleVisibility);
    
    // Очистка слушателя при размонтировании
    return () => window.removeEventListener('scroll', toggleVisibility);
  }, []);
  
  return (
    <Button 
      visible={isVisible} 
      onClick={scrollToTop}
      aria-label="Прокрутить вверх"
    >
      <ArrowContainer>
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          width="34" 
          height="34" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2.5" 
          strokeLinecap="round" 
          strokeLinejoin="round"
        >
          <path d="M18 15l-6-6-6 6"/>
        </svg>
      </ArrowContainer>
    </Button>
  );
};

export default ScrollToTopButton;