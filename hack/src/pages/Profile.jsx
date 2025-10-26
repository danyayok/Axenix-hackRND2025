import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import NavDivMeet from './components/NavDiv';
import './static/Profile.css';
import Vector from './static/images/Vector.png';
import Vector1 from './static/images/Vector-1.png';
import Vector2 from './static/images/Vector-2.png';
import Vector3 from './static/images/Vector-3.png';
import ProfileIcon from './static/images/profile.png';

const API_BASE_URL = 'http://localhost:8088/api';

export default function Profile() {
    const [userName, setUserName] = useState('Гость');
    const [avatar, setAvatar] = useState(ProfileIcon);
    const [isLoading, setIsLoading] = useState(false);
    const [saveStatus, setSaveStatus] = useState('');
    const [userId, setUserId] = useState(null);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [isGuest, setIsGuest] = useState(true);
    const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);
    const [passwordData, setPasswordData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });
    const fileInputRef = useRef(null);
    const navigate = useNavigate();

    // Проверяем авторизацию при загрузке
    useEffect(() => {
        checkAuthStatus();
    }, []);

    const checkAuthStatus = async () => {
        try {
            const authData = localStorage.getItem('authData');
            if (authData) {
                const data = JSON.parse(authData);
                setUserId(data.userId);
                setIsLoggedIn(true);
                setIsGuest(data.isGuest);

                if (data.isGuest) {
                    loadGuestData();
                } else {
                    await loadUserFromServer(data.userId);
                }
            } else {
                // Если не авторизован - редирект на страницу авторизации
                navigate('/Auth');
            }
        } catch (error) {
            console.log('Ошибка загрузки авторизации:', error);
            navigate('/Auth');
        }
    };

    // Загрузка пользователя с сервера
    const loadUserFromServer = async (userId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/users/${userId}`);
            if (response.ok) {
                const userData = await response.json();
                setUserName(userData.nickname || 'Пользователь');
                if (userData.avatar_url) {
                    setAvatar(userData.avatar_url);
                }
            }
        } catch (error) {
            console.log('Ошибка загрузки пользователя:', error);
        }
    };

    // Обновление пользователя на сервере
    const updateUserOnServer = async (userId, nickname, avatarUrl = null) => {
        try {
            const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    nickname: nickname,
                    avatar_url: avatarUrl
                }),
            });

            if (response.ok) {
                const updatedUser = await response.json();
                return updatedUser;
            } else {
                throw new Error('Ошибка обновления');
            }
        } catch (error) {
            console.log('Ошибка обновления пользователя:', error);
            throw error;
        }
    };

    // Загрузка аватара на сервер
    const uploadAvatarToServer = async (userId, file) => {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/users/${userId}/avatar`, {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const userData = await response.json();
            console.log('✅ Аватар загружен на сервер:', userData);

            // Сервер возвращает относительный путь типа "/static/avatars/user_1.jpg"
            // Нужно преобразовать его в полный URL
            const relativeAvatarUrl = userData.avatar_url;
            const fullAvatarUrl = `http://localhost:8088${relativeAvatarUrl}`;

            console.log('🔄 Преобразованный URL:', fullAvatarUrl);
            return fullAvatarUrl;
        } else {
            throw new Error('Ошибка загрузки аватара');
        }
    } catch (error) {
        console.log('Ошибка загрузки аватара:', error);
        throw error;
    }
};

    // Данные гостя из sessionStorage
    const loadGuestData = () => {
        const guestData = sessionStorage.getItem('guestProfileData');
        if (guestData) {
            try {
                const data = JSON.parse(guestData);
                setUserName(data.userName || 'Гость');
                if (data.avatar) {
                    setAvatar(data.avatar);
                }
            } catch (error) {
                console.error('Ошибка загрузки данных гостя:', error);
            }
        }
    };

    const saveGuestData = (name, avatarUrl) => {
        const guestData = {
            userName: name,
            avatar: avatarUrl && avatarUrl !== ProfileIcon ? avatarUrl : null,
            lastUpdate: new Date().toISOString()
        };
        sessionStorage.setItem('guestProfileData', JSON.stringify(guestData));
    };

    const handleLogout = () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('authData');
        sessionStorage.removeItem('guestProfileData');
        // Редирект на страницу авторизации
        navigate('/Auth');
    };

    const handleAvatarClick = () => {
        if (!isLoggedIn) {
            navigate('/Auth');
            return;
        }
        fileInputRef.current?.click();
    };

    const handleAvatarChange = async (event) => {
        const file = event.target.files[0];

        if (!file) return;

        if (!file.type.startsWith('image/')) {
            alert('Пожалуйста, выберите файл изображения');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            alert('Файл слишком большой. Максимальный размер: 5MB');
            return;
        }

        setIsLoading(true);

        const reader = new FileReader();

        reader.onload = async (e) => {
            const newAvatar = e.target.result;

            try {
                if (isGuest) {
                    // Для гостя сохраняем только локально
                    saveGuestData(userName, newAvatar);
                    setAvatar(newAvatar);
                    setSaveStatus('Аватар обновлен!');
                } else {
                    // Для пользователя сохраняем на сервер
                    console.log('🔄 Загружаем аватар на сервер...');

                    // Сначала загружаем файл через отдельный эндпоинт
                    const avatarUrl = await uploadAvatarToServer(userId, file);
                    console.log('✅ URL аватара с сервера:', avatarUrl);

                    // Затем обновляем пользователя с новым avatar_url
                    const updatedUser = await updateUserOnServer(userId, userName, avatarUrl);
                    console.log('✅ Пользователь обновлен:', updatedUser);

                    // Обновляем UI
                    setAvatar(avatarUrl);

                    // Обновляем данные в localStorage
                    const authData = JSON.parse(localStorage.getItem('authData') || '{}');
                    authData.userData = { ...authData.userData, avatar_url: avatarUrl };
                    localStorage.setItem('authData', JSON.stringify(authData));

                    setSaveStatus('Аватар обновлен!');
                }
            } catch (error) {
                console.error('❌ Ошибка сохранения аватара:', error);
                setSaveStatus('Ошибка обновления аватара');
            } finally {
                setIsLoading(false);
                setTimeout(() => setSaveStatus(''), 3000);
            }
        };

        reader.onerror = () => {
            alert('Ошибка при загрузке изображения');
            setIsLoading(false);
        };

        reader.readAsDataURL(file);
        };

        const handleSaveChanges = async () => {
            if (!isLoggedIn) {
                navigate('/Auth');
                return;
            }

            setIsLoading(true);
            setSaveStatus('Сохранение...');

            try {
                if (isGuest) {
                    saveGuestData(userName, avatar);
                    setSaveStatus('Изменения сохранены!');
                } else {
                    const result = await updateUserOnServer(userId, userName, avatar);
                    if (result) {
                        const authData = JSON.parse(localStorage.getItem('authData') || '{}');
                        authData.userData = result;
                        localStorage.setItem('authData', JSON.stringify(authData));
                    }
                    setSaveStatus('Изменения сохранены!');
                }
            } catch (error) {
                setSaveStatus('Ошибка сохранения');
            } finally {
                setIsLoading(false);
                setTimeout(() => setSaveStatus(''), 3000);
            }
    };

    const handleChangePassword = () => {
        if (!isLoggedIn || isGuest) {
            navigate('/Auth');
            return;
        }
        setShowChangePasswordModal(true);
    };

    const handlePasswordSubmit = async (e) => {
        e.preventDefault();

        if (passwordData.newPassword !== passwordData.confirmPassword) {
            alert('Новые пароли не совпадают');
            return;
        }

        if (passwordData.newPassword.length < 6) {
            alert('Пароль должен содержать минимум 6 символов');
            return;
        }

        setIsLoading(true);

        try {
            const authToken = localStorage.getItem('authToken');
            const response = await fetch(`${API_BASE_URL}/users/${userId}/change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`,
                },
                body: JSON.stringify({
                    current_password: passwordData.currentPassword,
                    new_password: passwordData.newPassword
                }),
            });

            if (response.ok) {
                alert('Пароль успешно изменен!');
                setShowChangePasswordModal(false);
                setPasswordData({
                    currentPassword: '',
                    newPassword: '',
                    confirmPassword: ''
                });
            } else {
                const errorData = await response.json();
                alert('Ошибка изменения пароля: ' + (errorData.detail || 'Неверный текущий пароль'));
            }
        } catch (error) {
            console.error('Ошибка при изменении пароля:', error);
            alert('Ошибка при изменении пароля: ' + error.message);
        } finally {
            setIsLoading(false);
        }
    };

    // Функция закрытия модального окна
    const handleClosePasswordModal = () => {
        setShowChangePasswordModal(false);
        setPasswordData({
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
        });
    };

    const handleConferenceHistory = () => {
        if (!isLoggedIn) {
            navigate('/Auth');
            return;
        }
        alert('История конференций загружена');
    };

    const handleNotificationSettings = () => {
        if (!isLoggedIn) {
            navigate('/Auth');
            return;
        }
        alert('Настройки уведомлений открыты');
    };

    const handleEditProfile = () => {
        if (!isLoggedIn) {
            navigate('/Auth');
            return;
        }
        const nameInput = document.querySelector('.name-input');
        if (nameInput) {
            nameInput.focus();
            nameInput.select();
        }
    };

    const handleDeleteAccount = async () => {
        if (!isLoggedIn || isGuest) {
            navigate('/Auth');
            return;
        }

        const confirmDelete = window.confirm(
            'Вы уверены, что хотите удалить аккаунт?\nВсе ваши данные будут безвозвратно удалены.\nЭто действие нельзя отменить.'
        );

        if (confirmDelete) {
            setIsLoading(true);

            try {
                // Получаем токен для авторизации
                const authToken = localStorage.getItem('authToken');

                // Отправляем запрос на удаление пользователя
                const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${authToken}`,
                        'Content-Type': 'application/json',
                    },
                });

                if (response.ok) {
                    // Успешно удалили из базы - очищаем локальные данные
                    localStorage.removeItem('authToken');
                    localStorage.removeItem('authData');
                    sessionStorage.removeItem('guestProfileData');

                    // Перенаправляем на страницу авторизации
                    navigate('/Auth');
                } else {
                    const error = await response.json();
                    alert('Ошибка удаления аккаунта: ' + (error.detail || 'Unknown error'));
                }
            } catch (error) {
                console.error('Ошибка при удалении аккаунта:', error);
                alert('Ошибка при удалении аккаунта: ' + error.message);
            } finally {
                setIsLoading(false);
            }
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
                    <h1 className="profile-title">
                        Профиль {isGuest ? '(Гость)' : '(Пользователь)'}
                        {userId && !isGuest && ` (ID: ${userId})`}
                    </h1>

                    {saveStatus && (
                        <div className={`save-status ${saveStatus.includes('Ошибка') ? 'error' : 'success'}`}>
                            {saveStatus}
                        </div>
                    )}

                    <div className="profile-main">
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
                                    disabled={isLoading || !isLoggedIn}
                                />
                            </div>
                        </div>

                        <div className="profile-actions">
                            <button
                                className="profile-btn save-btn"
                                onClick={handleSaveChanges}
                                disabled={isLoading || !isLoggedIn}
                            >
                                {isLoading ? 'Сохранение...' : 'Сохранить изменения'}
                            </button>
                            <button
                                className="profile-btn secondary-btn"
                                onClick={handleChangePassword}
                                disabled={isLoading || !isLoggedIn || isGuest}
                            >
                                Сменить пароль
                            </button>
                            <button
                                className="profile-btn secondary-btn"
                                onClick={handleConferenceHistory}
                                disabled={isLoading || !isLoggedIn}
                            >
                                История конференций
                            </button>
                            <button
                                className="profile-btn secondary-btn"
                                onClick={handleNotificationSettings}
                                disabled={isLoading || !isLoggedIn}
                            >
                                Настройки уведомлений
                            </button>
                            <button
                                className="profile-btn secondary-btn"
                                onClick={handleEditProfile}
                                disabled={isLoading || !isLoggedIn}
                            >
                                Редактировать профиль
                            </button>
                            <button
                                className="profile-btn delete-btn"
                                onClick={handleDeleteAccount}
                                disabled={isLoading || !isLoggedIn || isGuest}
                            >
                                Удалить аккаунт
                            </button>
                            {isLoggedIn && (
                                <button
                                    className="profile-btn delete-btn"
                                    onClick={handleLogout}
                                >
                                    Выйти
                                </button>
                            )}
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

            {/* Модальное окно смены пароля */}
            {showChangePasswordModal && (
                <div className="modal-overlay">
                    <div className="password-modal">
                        <div className="modal-header">
                            <h2 className="modal-title">Смена пароля</h2>
                            <button className="modal-close" onClick={handleClosePasswordModal}>×</button>
                        </div>

                        <form className="password-form" onSubmit={handlePasswordSubmit}>
                            <div className="form-group">
                                <label className="form-label">Текущий пароль</label>
                                <input
                                    type="password"
                                    className="form-input"
                                    value={passwordData.currentPassword}
                                    onChange={(e) => setPasswordData({...passwordData, currentPassword: e.target.value})}
                                    placeholder="Введите текущий пароль"
                                    required
                                    disabled={isLoading}
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">Новый пароль</label>
                                <input
                                    type="password"
                                    className="form-input"
                                    value={passwordData.newPassword}
                                    onChange={(e) => setPasswordData({...passwordData, newPassword: e.target.value})}
                                    placeholder="Минимум 6 символов"
                                    required
                                    disabled={isLoading}
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">Подтвердите пароль</label>
                                <input
                                    type="password"
                                    className="form-input"
                                    value={passwordData.confirmPassword}
                                    onChange={(e) => setPasswordData({...passwordData, confirmPassword: e.target.value})}
                                    placeholder="Повторите новый пароль"
                                    required
                                    disabled={isLoading}
                                />
                            </div>

                            <div className="form-actions">
                                <button
                                    type="button"
                                    className="cancel-btn"
                                    onClick={handleClosePasswordModal}
                                    disabled={isLoading}
                                >
                                    Отмена
                                </button>
                                <button
                                    type="submit"
                                    className="submit-btn"
                                    disabled={isLoading}
                                >
                                    {isLoading ? 'Смена...' : 'Сменить пароль'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    );
}