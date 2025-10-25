import { useState, useRef, useEffect } from 'react';
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
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [loginData, setLoginData] = useState({ email: '', password: '' });
    const fileInputRef = useRef(null);

    // Проверяем авторизацию при загрузке
    useEffect(() => {
        console.log('🔍 Проверка авторизации...');
        checkAuthStatus();
    }, []);

    const checkAuthStatus = async () => {
        try {
            const token = localStorage.getItem('authToken');
            const authData = localStorage.getItem('authData');

            console.log('📦 Token:', token ? 'есть' : 'нет');
            console.log('📦 AuthData:', authData ? 'есть' : 'нет');

            if (token && authData) {
                const data = JSON.parse(authData);
                console.log('👤 Данные пользователя:', data);

                setUserId(data.userId);
                setIsLoggedIn(true);
                setIsGuest(data.isGuest);

                if (data.isGuest) {
                    console.log('🎭 Загружаем данные гостя');
                    loadGuestData();
                } else {
                    console.log('👤 Загружаем данные пользователя с сервера');
                    await loadUserFromServer(data.userId);
                }
            } else {
                console.log('🚪 Показываем окно входа');
                setShowLoginModal(true);
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки авторизации:', error);
            setShowLoginModal(true);
        }
    };

    // Создание гостевого пользователя
    const createGuestUser = async () => {
        try {
            console.log('🎭 Создаем гостевого пользователя...');

            const response = await fetch(`${API_BASE_URL}/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    nickname: 'Гость',
                    avatar_url: null,
                    public_key_pem: ""
                }),
            });

            if (response.ok) {
                const newUser = await response.json();
                console.log('✅ Гость создан:', newUser);

                // Получаем гостевой токен
                const tokenResponse = await fetch(`${API_BASE_URL}/auth/token/guest`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        user_id: newUser.id
                    }),
                });

                if (tokenResponse.ok) {
                    const tokenData = await tokenResponse.json();
                    console.log('✅ Токен получен:', tokenData);

                    // Сохраняем данные
                    localStorage.setItem('authToken', tokenData.access_token);
                    localStorage.setItem('authData', JSON.stringify({
                        userId: newUser.id,
                        isGuest: true,
                        userData: newUser
                    }));

                    setUserId(newUser.id);
                    setIsLoggedIn(true);
                    setIsGuest(true);
                    setUserName(newUser.nickname || 'Гость');
                    setShowLoginModal(false);

                    return newUser;
                } else {
                    console.error('❌ Ошибка получения токена');
                }
            } else {
                console.error('❌ Ошибка создания гостя');
            }
        } catch (error) {
            console.error('❌ Ошибка создания гостя:', error);
        }
        return null;
    };

    // Загрузка пользователя с сервера
    const loadUserFromServer = async (userId) => {
        try {
            console.log(`👤 Загружаем пользователя ${userId}...`);
            const response = await fetch(`${API_BASE_URL}/users/${userId}`);
            if (response.ok) {
                const userData = await response.json();
                console.log('✅ Пользователь загружен:', userData);
                setUserName(userData.nickname || 'Пользователь');
                if (userData.avatar_url) {
                    setAvatar(userData.avatar_url);
                }
                return userData;
            } else {
                console.error('❌ Ошибка загрузки пользователя');
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки пользователя:', error);
        }
        return null;
    };

    // Данные гостя из sessionStorage
    const loadGuestData = () => {
        const guestData = sessionStorage.getItem('guestProfileData');
        if (guestData) {
            try {
                const data = JSON.parse(guestData);
                console.log('📦 Данные гостя загружены:', data);
                setUserName(data.userName || 'Гость');
                if (data.avatar) {
                    setAvatar(data.avatar);
                }
            } catch (error) {
                console.error('❌ Ошибка загрузки данных гостя:', error);
            }
        } else {
            console.log('📦 Нет сохраненных данных гостя');
        }
    };

    const saveGuestData = (name, avatarUrl) => {
        const guestData = {
            userName: name,
            avatar: avatarUrl && avatarUrl !== ProfileIcon ? avatarUrl : null,
            lastUpdate: new Date().toISOString()
        };
        sessionStorage.setItem('guestProfileData', JSON.stringify(guestData));
        console.log('💾 Данные гостя сохранены:', guestData);
    };

    // Регистрация пользователя
    const handleRegister = async () => {
        const email = prompt('Введите email для регистрации:');
        const password = prompt('Введите пароль:');
        const nickname = prompt('Введите имя пользователя:');

        if (email && password && nickname) {
            if (password.length < 6) {
                alert('Пароль должен содержать минимум 6 символов');
                return;
            }

            setIsLoading(true);
            try {
                console.log('📝 Регистрируем пользователя...');
                const response = await fetch(`${API_BASE_URL}/users`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        nickname: nickname,
                        email: email,
                        password: password,
                        avatar_url: null,
                        public_key_pem: ""
                    }),
                });

                if (response.ok) {
                    const newUser = await response.json();
                    console.log('✅ Пользователь зарегистрирован:', newUser);

                    alert('Регистрация успешна! Теперь войдите в систему.');
                    setLoginData({ email: email, password: '' });

                } else {
                    const error = await response.json();
                    console.error('❌ Ошибка регистрации:', error);
                    alert('Ошибка регистрации: ' + (error.detail || 'Unknown error'));
                }
            } catch (error) {
                console.error('❌ Ошибка регистрации:', error);
                alert('Ошибка регистрации: ' + error.message);
            } finally {
                setIsLoading(false);
            }
        }
    };

    // Вход пользователя
    const handleLogin = async (e) => {
        e.preventDefault();
        if (!loginData.email || !loginData.password) {
            alert('Пожалуйста, заполните все поля');
            return;
        }

        setIsLoading(true);
        console.log('🔐 Пытаемся войти...');

        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: loginData.email,
                    password: loginData.password
                }),
            });

            if (response.ok) {
                const tokenData = await response.json();
                console.log('✅ Вход успешен:', tokenData);

                localStorage.setItem('authToken', tokenData.access_token);
                localStorage.setItem('authData', JSON.stringify({
                    userId: tokenData.user.id,
                    isGuest: false,
                    userData: tokenData.user
                }));

                setUserId(tokenData.user.id);
                setIsLoggedIn(true);
                setIsGuest(false);
                setUserName(tokenData.user.nickname);
                if (tokenData.user.avatar_url) {
                    setAvatar(tokenData.user.avatar_url);
                }
                setShowLoginModal(false);
            } else {
                console.error('❌ Ошибка входа');
                alert('Ошибка входа: проверьте email и пароль');
            }
        } catch (error) {
            console.error('❌ Ошибка входа:', error);
            alert('Ошибка входа: ' + error.message);
        } finally {
            setIsLoading(false);
        }
    };

    // Продолжить как гость
    const handleContinueAsGuest = async () => {
        setIsLoading(true);
        console.log('🎭 Продолжаем как гость...');
        await createGuestUser();
        setIsLoading(false);
    };

    // Выход
    const handleLogout = () => {
        console.log('🚪 Выход из системы...');
        localStorage.removeItem('authToken');
        localStorage.removeItem('authData');
        sessionStorage.removeItem('guestProfileData');
        setUserName('Гость');
        setAvatar(ProfileIcon);
        setUserId(null);
        setIsLoggedIn(false);
        setIsGuest(true);
        setShowLoginModal(true);
    };

    // Обработчики аватара и сохранения (упрощенные версии)
    const handleAvatarClick = () => {
        if (!isLoggedIn) {
            setShowLoginModal(true);
            return;
        }
        fileInputRef.current?.click();
    };

    const handleAvatarChange = (event) => {
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

        reader.onload = (e) => {
            const newAvatar = e.target.result;
            setAvatar(newAvatar);

            if (isGuest) {
                saveGuestData(userName, newAvatar);
                setSaveStatus('Аватар обновлен!');
            } else {
                setSaveStatus('Аватар обновлен (только локально)!');
            }

            setTimeout(() => setSaveStatus(''), 3000);
            setIsLoading(false);
        };

        reader.onerror = () => {
            alert('Ошибка при загрузке изображения');
            setIsLoading(false);
        };

        reader.readAsDataURL(file);
    };

    const handleSaveChanges = async () => {
        if (!isLoggedIn) {
            setShowLoginModal(true);
            return;
        }

        setIsLoading(true);
        setSaveStatus('Сохранение...');

        try {
            if (isGuest) {
                saveGuestData(userName, avatar);
                setSaveStatus('Изменения сохранены!');
            } else {
                setSaveStatus('Изменения сохранены (только локально)!');
            }
        } catch (error) {
            setSaveStatus('Ошибка сохранения');
        } finally {
            setIsLoading(false);
            setTimeout(() => setSaveStatus(''), 3000);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleSaveChanges();
        }
    };

    // Функции которые нужно добавить (заглушки)
    const handleChangePassword = () => {
        if (!isLoggedIn || isGuest) {
            setShowLoginModal(true);
            return;
        }
        alert('Смена пароля будет доступна позже');
    };

    const handleConferenceHistory = () => {
        if (!isLoggedIn) {
            setShowLoginModal(true);
            return;
        }
        alert('История конференций будет доступна позже');
    };

    const handleNotificationSettings = () => {
        if (!isLoggedIn) {
            setShowLoginModal(true);
            return;
        }
        alert('Настройки уведомлений будут доступны позже');
    };

    const handleEditProfile = () => {
        if (!isLoggedIn) {
            setShowLoginModal(true);
            return;
        }
        const nameInput = document.querySelector('.name-input');
        if (nameInput) {
            nameInput.focus();
            nameInput.select();
        }
    };

    const handleDeleteAccount = () => {
        if (!isLoggedIn || isGuest) {
            setShowLoginModal(true);
            return;
        }
        alert('Удаление аккаунта будет доступно позже');
    };

    const debugData = () => {
        const authData = localStorage.getItem('authData');
        const guestData = sessionStorage.getItem('guestProfileData');
        console.log('🔍 DEBUG:');
        console.log('Auth Data:', authData);
        console.log('Guest Data:', guestData);
        console.log('State:', { userName, userId, isLoggedIn, isGuest });
        alert(`DEBUG:\nAuth: ${authData}\nGuest: ${guestData}\nState: ${JSON.stringify({ userName, userId, isLoggedIn, isGuest })}`);
    };

    console.log('🎨 Рендерим компонент...', { userName, userId, isLoggedIn, isGuest, showLoginModal });

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

                    {isLoggedIn && (
                        <button onClick={handleLogout} className="logout-btn">
                            Выйти
                        </button>
                    )}

                    <button onClick={debugData} className="debug-btn">
                        Debug Data
                    </button>

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
                        </div>
                    </div>
                </section>
            </main>

            {/* Модальное окно входа */}
            {showLoginModal && (
                <div className="modal-overlay">
                    <div className="login-modal">
                        <h2>Вход в систему</h2>
                        <form onSubmit={handleLogin}>
                            <div className="input-group">
                                <label>Email:</label>
                                <input
                                    type="email"
                                    value={loginData.email}
                                    onChange={(e) => setLoginData({...loginData, email: e.target.value})}
                                    placeholder="user@example.com"
                                />
                            </div>
                            <div className="input-group">
                                <label>Пароль:</label>
                                <input
                                    type="password"
                                    value={loginData.password}
                                    onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                                    placeholder="Минимум 6 символов"
                                />
                            </div>
                            <div className="modal-actions">
                                <button type="submit" disabled={isLoading}>
                                    {isLoading ? 'Вход...' : 'Войти'}
                                </button>
                                <button type="button" onClick={handleRegister}>
                                    Зарегистрироваться
                                </button>
                                <button type="button" onClick={handleContinueAsGuest}>
                                    Продолжить как гость
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <footer className="footer">
                <p className="copyright">
                    ООО "Бнал" ИНН: 748327738890<br />
                    Все права защищены
                </p>
            </footer>
        </>
    );
}