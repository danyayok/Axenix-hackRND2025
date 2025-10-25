import { useState, useRef } from 'react';
import NavDivMeet from './components/NavDiv';
import './static/Profile.css';
// Импортируем изображения
import Vector from './static/images/Vector.png';
import Vector1 from './static/images/Vector-1.png';
import Vector2 from './static/images/Vector-2.png';
import Vector3 from './static/images/Vector-3.png';
import ProfileIcon from './static/images/profile.png';

export default function Profile() {
    const [userName, setUserName] = useState('Иван Иванов');
    const [avatar, setAvatar] = useState(ProfileIcon);
    const [isLoading, setIsLoading] = useState(false);
    const [saveStatus, setSaveStatus] = useState('');
    const fileInputRef = useRef(null);

    const handleAvatarClick = () => {
        fileInputRef.current?.click();
    };

    const handleAvatarChange = (event) => {
        const file = event.target.files[0];
        
        if (!file) return;

        // Проверяем что это изображение
        if (!file.type.startsWith('image/')) {
            alert('Пожалуйста, выберите файл изображения');
            return;
        }
        
        // Проверяем размер файла (максимум 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('Файл слишком большой. Максимальный размер: 5MB');
            return;
        }

        setIsLoading(true);

        // Создаем превью изображения
        const reader = new FileReader();
        
        reader.onload = (e) => {
            setAvatar(e.target.result);
            setIsLoading(false);
            
            // Автоматически сохраняем при изменении аватара
            handleSaveChanges();
        };

        reader.onerror = () => {
            alert('Ошибка при загрузке изображения');
            setIsLoading(false);
        };

        reader.readAsDataURL(file);
    };

    const uploadAvatarToServer = async (file) => {
        // Имитация загрузки на сервер
        return new Promise((resolve) => {
            setTimeout(() => {
                console.log('Аватар загружен на сервер:', file.name);
                resolve({ success: true });
            }, 1000);
        });
    };

    const handleSaveChanges = async () => {
        setIsLoading(true);
        setSaveStatus('Сохранение...');

        try {
            // Имитация API запроса
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Если был выбран новый файл, загружаем его
            if (fileInputRef.current?.files[0]) {
                await uploadAvatarToServer(fileInputRef.current.files[0]);
            }

            // Сохраняем данные пользователя
            const userData = {
                userName,
                avatar: avatar !== ProfileIcon ? avatar : null
            };
            
            console.log('Данные сохранены:', userData);
            setSaveStatus('Изменения сохранены!');
            
            // Через 3 секунды убираем статус
            setTimeout(() => setSaveStatus(''), 3000);
            
        } catch (error) {
            console.error('Ошибка сохранения:', error);
            setSaveStatus('Ошибка сохранения');
        } finally {
            setIsLoading(false);
        }
    };

    const handleChangePassword = () => {
        // Логика смены пароля
        const newPassword = prompt('Введите новый пароль:');
        if (newPassword) {
            console.log('Пароль изменен:', newPassword);
            alert('Пароль успешно изменен!');
        }
    };

    const handleConferenceHistory = () => {
        console.log('Переход к истории конференций');
        // В реальном приложении здесь будет навигация
        alert('Переход к истории конференций');
    };

    const handleNotificationSettings = () => {
        console.log('Настройки уведомлений');
        // В реальном приложении здесь будет модальное окно или страница
        alert('Открытие настроек уведомлений');
    };

    const handleEditProfile = () => {
        console.log('Редактирование профиля');
        // Активируем редактирование полей
        const nameInput = document.querySelector('.name-input');
        if (nameInput) {
            nameInput.focus();
        }
    };

    const handleDeleteAccount = () => {
        const confirmDelete = window.confirm(
            'Вы уверены, что хотите удалить аккаунт?\nВсе ваши данные будут безвозвратно удалены.\nЭто действие нельзя отменить.'
        );
        
        if (confirmDelete) {
            setIsLoading(true);
            
            // Имитация процесса удаления
            setTimeout(() => {
                console.log('Аккаунт удален');
                alert('Аккаунт успешно удален');
                setIsLoading(false);
                
                // В реальном приложении здесь будет редирект или очистка данных
                window.location.href = '/';
            }, 2000);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleSaveChanges();
        }
    };

    return (
        <>
            <div className="background-elements">
                <img className="vector" src={Vector} alt="" />
                <img className="vector" src={Vector1} alt="" />
                <img className="vector" src={Vector2} alt="" />
                <img className="vector" src={Vector3} alt="" />
            </div>

            <NavDivMeet />

            <main className="main-content">
                <section className="profile-section">
                    <h1 className="profile-title">Профиль</h1>
                    
                    {/* Статус сохранения */}
                    {saveStatus && (
                        <div className={`save-status ${saveStatus.includes('Ошибка') ? 'error' : 'success'}`}>
                            {saveStatus}
                        </div>
                    )}
                    
                    <div className="profile-main">
                        {/* Аватар и имя */}
                        <div className="profile-header">
                            <div className="avatar-large" onClick={handleAvatarClick}>
                                {isLoading ? (
                                    <div className="avatar-loading">Загрузка...</div>
                                ) : (
                                    <img id="avatarImage" src={avatar} alt="Аватар" />
                                )}
                                <input 
                                    ref={fileInputRef}
                                    type="file" 
                                    id="avatarInput" 
                                    accept="image/*" 
                                    style={{ display: 'none' }}
                                    onChange={handleAvatarChange}
                                />
                                <div className="avatar-overlay">
                                    <span>Изменить фото</span>
                                </div>
                            </div>
                            <div className="name-section">
                                <label className="name-label">Имя</label>
                                <input 
                                    type="text" 
                                    className="name-input" 
                                    value={userName}
                                    onChange={(e) => setUserName(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    disabled={isLoading}
                                />
                            </div>
                        </div>
                
                        {/* Вертикальный список кнопок */}
                        <div className="profile-actions">
                            <button 
                                className="profile-btn save-btn" 
                                onClick={handleSaveChanges}
                                disabled={isLoading}
                            >
                                {isLoading ? 'Сохранение...' : 'Сохранить изменения'}
                            </button>
                            <button 
                                className="profile-btn secondary-btn" 
                                onClick={handleChangePassword}
                                disabled={isLoading}
                            >
                                Сменить пароль
                            </button>
                            <button 
                                className="profile-btn secondary-btn" 
                                onClick={handleConferenceHistory}
                                disabled={isLoading}
                            >
                                История конференций
                            </button>
                            <button 
                                className="profile-btn secondary-btn" 
                                onClick={handleNotificationSettings}
                                disabled={isLoading}
                            >
                                Настройки уведомлений
                            </button>
                            <button 
                                className="profile-btn secondary-btn" 
                                onClick={handleEditProfile}
                                disabled={isLoading}
                            >
                                Редактировать профиль
                            </button>
                            <button 
                                className="profile-btn delete-btn" 
                                onClick={handleDeleteAccount}
                                disabled={isLoading}
                            >
                                Удалить аккаунт
                            </button>
                        </div>
                    </div>
                </section>
            </main>

            <footer className="footer">
                <p className="copyright">
                    ООО "Бнал" ИНН: 748327738890<br />
                    Все права защищены
                </p>
            </footer>
        </>
    );
}