import React, { useState, useEffect, useRef, useContext } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { useTranslation } from 'react-i18next';
import { getUserLocations, deleteUserLocation, updateUserLocationName } from '../utils/api';
import { LocationContext } from '../contexts/LocationContext';

const HeaderContainer = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background-color: ${({ theme }) => theme.colors.background};
  box-shadow: ${({ theme }) => theme.shadows.sm};
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(8px);
  
  @media (prefers-color-scheme: dark) {
    background-color: rgba(18, 18, 18, 0.8);
  }
  
  @media (max-width: 480px) {
    padding: 0.75rem;
  }
`;

const Logo = styled(Link)`
  font-size: ${({ theme }) => theme.fontSizes.xl};
  font-weight: 700;
  color: ${({ theme }) => theme.colors.primary};
  display: flex;
  align-items: center;
  gap: 1.5rem;
  
  @media (max-width: 480px) {
    font-size: 3.25rem;
    gap: 0.3rem;
  }
`;

const Avatar = styled.img`
  width: 92px;
  height: 92px;
  border-radius: 50%;
  object-fit: cover;
`;

const UserInfo = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-left: 12px;
`;

const UserName = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.lg};
  font-weight: 600;
  color: ${({ theme }) => theme.colors.text};
`;

const UserUsername = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.textLight};
`;

const LanguageSelector = styled.div`
  position: relative;
`;

const LanguageButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: ${({ theme }) => theme.borderRadius.md};
  color: ${({ theme }) => theme.colors.text};
  font-size: 1rem;
  cursor: pointer;
  min-width: 120px;
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.05);
  }
  
  @media (max-width: 480px) {
    padding: 0.4rem 0.75rem;
    font-size: 0.9rem;
  }
`;

const LanguageDropdown = styled.div`
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background-color: ${({ theme }) => theme.colors.background};
  border-radius: ${({ theme }) => theme.borderRadius.md};
  box-shadow: ${({ theme }) => theme.shadows.md};
  overflow: hidden;
  width: 180px; 
  z-index: 20;
  
  @media (prefers-color-scheme: dark) {
    background-color: #1e1e1e;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.24);
  }
  
  @media (max-width: 480px) {
    width: 160px; 
    right: -5px;
  }
`;

const LanguageOption = styled.button`
  width: 100%;
  text-align: left;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  color: ${({ theme }) => theme.colors.text};
  font-size: 1.2rem; 
  
  &:hover {
    background-color: ${({ theme }) => theme.colors.surface};
  }
  
  @media (prefers-color-scheme: dark) {
    &:hover {
      background-color: rgba(255, 255, 255, 0.05);
    }
  }
  
  &:not(:last-child) {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }
  
  @media (max-width: 480px) {
    padding: 0.6rem 0.75rem;
    font-size: 1.2rem; 
  }
`;

const LocationSelector = styled.div`
  position: relative;
  margin-left: 10px;
`;

const LocationButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: ${({ theme }) => theme.borderRadius.md};
  color: ${({ theme }) => theme.colors.text};
  font-size: 1rem;
  cursor: pointer;
  min-width: 120px;
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.05);
  }
  
  @media (max-width: 480px) {
    padding: 0.4rem 0.75rem;
    font-size: 0.9rem;
  }
`;

const LocationDropdown = styled.div`
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background-color: ${({ theme }) => theme.colors.background};
  border-radius: ${({ theme }) => theme.borderRadius.md};
  box-shadow: ${({ theme }) => theme.shadows.md};
  overflow: hidden;
  width: 250px; 
  z-index: 20;
  max-height: 300px;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
  }
  
  &::-webkit-scrollbar-thumb {
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
  }
  
  @media (prefers-color-scheme: dark) {
    background-color: #1e1e1e;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.24);
  }
  
  @media (max-width: 480px) {
    width: 220px; 
    right: -5px;
  }
`;

const LocationOption = styled.button`
  width: 100%;
  text-align: left;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  color: ${({ theme }) => theme.colors.text};
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  font-size: 1.2rem; 
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  &:not(:last-child) {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
`;

const LocationText = styled.span`
  flex: 1;
  font-size: 1.2rem; 
`;

const DeleteButton = styled.button`
  background: none;
  border: none;
  color: ${({ theme }) => theme.colors.error};
  margin-left: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 1rem;
  
  &:hover {
    background-color: rgba(239, 68, 68, 0.1);
  }
`;

const EditButton = styled.button`
  background: none;
  border: none;
  color: ${({ theme }) => theme.colors.primary};
  margin-left: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 1rem;
  
  &:hover {
    background-color: rgba(0, 102, 255, 0.1);
  }
`;

const Modal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  z-index: 1000;
  padding-top: 180px;
`;

const ModalContent = styled.div`
  background-color: rgba(40, 40, 40, 0.95);
  padding: 24px;
  border-radius: 12px;
  width: 320px;
  max-width: 90%;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.15);
`;

const ModalTitle = styled.h3`
  margin-top: 0;
  margin-bottom: 20px;
  color: white;
  font-size: 1.6rem;
  font-weight: 600;
`;

const Input = styled.input`
  width: 100%;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background-color: rgba(60, 60, 60, 0.8);
  color: white;
  margin-bottom: 20px;
  font-size: 1.2rem;
  transition: all 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: ${({ theme }) => theme.colors.primary};
    box-shadow: 0 0 0 2px ${({ theme }) => theme.colors.primary}33;
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.6);
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 12px;
`;

const Button = styled.button`
  padding: 10px 18px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  font-size: 1.1rem;
  transition: all 0.2s ease;
  
  &:focus {
    outline: none;
  }
`;

const CancelButton = styled(Button)`
  background-color: rgba(60, 60, 60, 0.8);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.15);
  
  &:hover {
    background-color: rgba(80, 80, 80, 0.8);
  }
`;

const SaveButton = styled(Button)`
  background-color: ${({ theme }) => theme.colors.primary};
  color: white;
  
  &:hover {
    background-color: ${({ theme }) => theme.colors.primary}ee;
    transform: translateY(-1px);
  }
`;

const Header = ({ avatarPath, userData }) => {
  const { t, i18n } = useTranslation();
  const [isLanguageDropdownOpen, setIsLanguageDropdownOpen] = useState(false);
  const [isLocationDropdownOpen, setIsLocationDropdownOpen] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [userLocations, setUserLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingLocation, setEditingLocation] = useState(null);
  const [locationName, setLocationName] = useState('');
  const inputRef = useRef(null);
  const languageDropdownRef = useRef(null);
  const locationDropdownRef = useRef(null);
  
  // Получаем доступ к контексту локации
  const locationContext = useContext(LocationContext);
  
  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    setIsLanguageDropdownOpen(false);
  };

  const selectLocation = (location) => {
    setIsLocationDropdownOpen(false);
    
    // Сохраняем выбранную локацию в контексте
    locationContext.setSelectedLocation(location);
    
    if (window.Telegram && window.Telegram.WebApp) {
      const locationText = location.name 
        ? location.name 
        : `${location.lat.toFixed(6)}, ${location.lon.toFixed(6)}`;
      window.Telegram.WebApp.showAlert(`${t('selectedLocation')}: ${locationText}`);
    }
  };

  const handleDeleteLocation = async (e, locationId) => {
    e.stopPropagation(); 
    
    try {
      await deleteUserLocation(locationId);
      if (userData && userData.id) {
        const updatedLocations = await getUserLocations(userData.id);
        setUserLocations(updatedLocations);
        
        if (selectedLocation && selectedLocation.id === locationId) {
          setSelectedLocation(updatedLocations.length > 0 ? updatedLocations[0] : null);
        }
      }
      
      if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.showAlert(t('locationDeleted'));
      }
    } catch (error) {
      console.error('Failed to delete location:', error);
      if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.showAlert(t('errorDeletingLocation'));
      }
    }
  };

  const openEditModal = (e, location) => {
    e.stopPropagation(); 
    setEditingLocation(location);
    setLocationName(location.name || '');
    setIsEditModalOpen(true);
  };

  const closeEditModal = () => {
    setIsEditModalOpen(false);
    setEditingLocation(null);
    setLocationName('');
  };

  const handleSaveLocationName = async () => {
    if (!editingLocation) return;
    
    try {
      await updateUserLocationName(editingLocation.id, locationName);
      
      if (userData && userData.id) {
        const updatedLocations = await getUserLocations(userData.id);
        setUserLocations(updatedLocations);
        
        if (selectedLocation && selectedLocation.id === editingLocation.id) {
          const updatedLocation = updatedLocations.find(loc => loc.id === editingLocation.id);
          if (updatedLocation) {
            setSelectedLocation(updatedLocation);
          }
        }
      }
      
      closeEditModal();
      
      if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.showAlert(t('locationNameUpdated'));
      }
    } catch (error) {
      console.error('Failed to update location name:', error);
      if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.showAlert(t('errorUpdatingLocationName'));
      }
    }
  };

  useEffect(() => {
    if (isEditModalOpen && inputRef.current) {
      setTimeout(() => {
        inputRef.current.focus();
      }, 100);
    }
  }, [isEditModalOpen]);

  useEffect(() => {
    const fetchUserLocations = async () => {
      if (userData && userData.id) {
        try {
          const locations = await getUserLocations(userData.id);
          setUserLocations(locations);
          
          if (locations.length > 0) {
            setSelectedLocation(locations[0]);
          }
        } catch (error) {
          console.error('Failed to fetch user locations:', error);
        }
      }
    };
    
    fetchUserLocations();
  }, [userData]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      // Закрываем языковой выпадающий список при клике вне его области
      if (
        languageDropdownRef.current && 
        !languageDropdownRef.current.contains(event.target) &&
        isLanguageDropdownOpen
      ) {
        setIsLanguageDropdownOpen(false);
      }
      
      // Закрываем выпадающий список локаций при клике вне его области
      if (
        locationDropdownRef.current && 
        !locationDropdownRef.current.contains(event.target) &&
        isLocationDropdownOpen
      ) {
        setIsLocationDropdownOpen(false);
      }
    };
    
    // Добавляем обработчик события
    document.addEventListener('mousedown', handleClickOutside);
    
    // Удаляем обработчик при размонтировании компонента
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isLanguageDropdownOpen, isLocationDropdownOpen]);

  const hasAvatar = Boolean(avatarPath) && avatarPath !== '';
  const logoUrl = '/images/logo.jpg'; 
  const avatarUrl = hasAvatar 
    ? (avatarPath.startsWith('photos/') ? `/telegram/${avatarPath}` : `/telegram/photos/${avatarPath}`)
    : logoUrl;

  const userName = userData?.first_name ? 
    (userData.last_name ? `${userData.first_name} ${userData.last_name}` : userData.first_name) : 
    t('guest');
  const userUsername = userData?.username ? `@${userData.username}` : '';

  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      setImageLoaded(true);
    };
    img.src = avatarUrl;
  }, [avatarUrl]);

  if (!imageLoaded) return null;

  return (
    <HeaderContainer>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        {hasAvatar ? (
          <Avatar src={avatarUrl} alt="User Avatar" />
        ) : (
          <Logo to="/">
            <Avatar src={logoUrl} alt="Logo" />
          </Logo>
        )}
        <UserInfo>
          <UserName>{userName}</UserName>
          {userUsername && <UserUsername>{userUsername}</UserUsername>}
        </UserInfo>
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '10px' }}>
        <LanguageSelector ref={languageDropdownRef}>
          <LanguageButton onClick={() => setIsLanguageDropdownOpen(!isLanguageDropdownOpen)}>
            {t('language')}
            <span>{isLanguageDropdownOpen ? '▲' : '▼'}</span>
          </LanguageButton>
          
          {isLanguageDropdownOpen && (
            <LanguageDropdown>
              <LanguageOption onClick={() => changeLanguage('en')}>
                🇬🇧 {t('english')}
              </LanguageOption>
              <LanguageOption onClick={() => changeLanguage('ru')}>
                🇷🇺 {t('russian')}
              </LanguageOption>
            </LanguageDropdown>
          )}
        </LanguageSelector>
        
        {userLocations.length > 0 && (
          <LocationSelector ref={locationDropdownRef}>
            <LocationButton onClick={() => setIsLocationDropdownOpen(!isLocationDropdownOpen)}>
              {t('location')}
              <span>{isLocationDropdownOpen ? '▲' : '▼'}</span>
            </LocationButton>
            
            {isLocationDropdownOpen && (
              <LocationDropdown>
                {userLocations.map((location) => (
                  <LocationOption 
                    key={location.id} 
                    onClick={() => selectLocation(location)}
                  >
                    <LocationText>
                      📍 {location.name || `${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}`}
                    </LocationText>
                    <div>
                      <EditButton 
                        onClick={(e) => openEditModal(e, location)}
                        title={t('editLocationName')}
                      >
                        ✏️
                      </EditButton>
                      <DeleteButton 
                        onClick={(e) => handleDeleteLocation(e, location.id)}
                        title={t('deleteLocation')}
                      >
                        🗑️
                      </DeleteButton>
                    </div>
                  </LocationOption>
                ))}
              </LocationDropdown>
            )}
          </LocationSelector>
        )}
      </div>

      {isEditModalOpen && (
        <Modal onClick={closeEditModal}>
          <ModalContent onClick={(e) => e.stopPropagation()}>
            <ModalTitle>{t('editLocationName')}</ModalTitle>
            <Input 
              ref={inputRef}
              type="text" 
              value={locationName} 
              onChange={(e) => setLocationName(e.target.value)}
              placeholder={t('enterLocationName')}
            />
            <ButtonGroup>
              <CancelButton onClick={closeEditModal}>{t('cancel')}</CancelButton>
              <SaveButton onClick={handleSaveLocationName}>{t('save')}</SaveButton>
            </ButtonGroup>
          </ModalContent>
        </Modal>
      )}
    </HeaderContainer>
  );
};

export default Header;