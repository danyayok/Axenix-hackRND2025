import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom'; // Добавляем useNavigate
import NavDivMeet from './pages/components/NavDiv';
import './Auth.css';
import Vector from './pages/static/images/Vector.png';
import Vector1 from './pages/static/images/Vector-1.png';
import Vector2 from './pages/static/images/Vector-2.png';
import Vector3 from './pages/static/images/Vector-3.png';

const API_BASE_URL = 'http://localhost:8088/api';

export default function Auth() {
    const [isLogin, setIsLogin] = useState(true);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        nickname: ''
    });
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState('');
    const navigate = useNavigate(); // Добавляем навигацию

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setMessage('');

        try {
            if (isLogin) {
                await handleLogin();
            } else {
                await handleRegister();
            }
        } catch (error) {
            setMessage('Ошибка: ' + error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleGuestLogin = async () => {
        setIsLoading(true);
        setMessage('Создаем гостевой аккаунт...');

        try {
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

                // Получаем токен для гостя
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

                    // Сохраняем в localStorage
                    localStorage.setItem('authToken', tokenData.access_token);
                    localStorage.setItem('authData', JSON.stringify({
                        userId: newUser.id,
                        isGuest: true,
                        userData: newUser
                    }));

                    setMessage('Гостевой вход успешен! Перенаправление...');

                    setTimeout(() => {
                        navigate('/Profile'); // Используем navigate вместо window.location
                    }, 1000);
                }
            }
        } catch (error) {
            setMessage('Ошибка создания гостя: ' + error.message);
            setIsLoading(false);
        }
    };

    const handleLogin = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: formData.email,
                    password: formData.password
                }),
            });

            if (response.ok) {
                const tokenData = await response.json();
                console.log('✅ Данные входа:', tokenData);

                // WORKAROUND: Получаем ID пользователя из токена
                const tokenPayload = JSON.parse(atob(tokenData.access_token.split('.')[1]));
                const userId = tokenPayload.uid || tokenPayload.sub;

                localStorage.setItem('authToken', tokenData.access_token);
                localStorage.setItem('authData', JSON.stringify({
                    userId: userId,
                    isGuest: false,
                    userData: {
                        id: userId,
                        nickname: formData.nickname || 'Пользователь',
                        email: formData.email
                    }
                }));

                setMessage('Вход успешен! Перенаправление...');

                setTimeout(() => {
                    navigate('/Profile'); // Используем navigate
                }, 1000);
            } else {
                const errorData = await response.json();
                setMessage('Неверный email или пароль: ' + (errorData.detail || ''));
            }
        } catch (error) {
            setMessage('Ошибка входа: ' + error.message);
        }
    };

    const handleRegister = async () => {
        if (formData.password !== formData.confirmPassword) {
            setMessage('Пароли не совпадают');
            return;
        }

        if (formData.password.length < 6) {
            setMessage('Пароль должен содержать минимум 6 символов');
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    nickname: formData.nickname,
                    email: formData.email,
                    password: formData.password,
                    avatar_url: null,
                    public_key_pem: ""
                }),
            });

            if (response.ok) {
                const newUser = await response.json();
                setMessage('Регистрация успешна! Автоматический вход...');

                // Автоматически логинимся после регистрации
                const loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        email: formData.email,
                        password: formData.password
                    }),
                });

                if (loginResponse.ok) {
                    const tokenData = await loginResponse.json();
                    console.log('✅ Данные регистрации:', tokenData);

                    // WORKAROUND: Получаем ID пользователя из токена
                    const tokenPayload = JSON.parse(atob(tokenData.access_token.split('.')[1]));
                    const userId = tokenPayload.uid || tokenPayload.sub;

                    localStorage.setItem('authToken', tokenData.access_token);
                    localStorage.setItem('authData', JSON.stringify({
                        userId: userId,
                        isGuest: false,
                        userData: tokenData.user || newUser
                    }));

                    setMessage('Регистрация и вход успешны! Перенаправление...');

                    setTimeout(() => {
                        navigate('/Profile'); // Используем navigate
                    }, 1000);
                } else {
                    setMessage('Регистрация успешна, но вход не удался. Войдите вручную.');
                }
            } else {
                const error = await response.json();
                setMessage('Ошибка регистрации: ' + (error.detail || 'Попробуйте другой email.'));
            }
        } catch (error) {
            setMessage('Ошибка регистрации: ' + error.message);
        }
    };

    const toggleMode = () => {
        setIsLogin(!isLogin);
        setMessage('');
        setFormData({
            email: '',
            password: '',
            confirmPassword: '',
            nickname: ''
        });
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
                <section className="auth-section">
                    <div className="auth-container">
                        <h1 className="auth-title">
                            {isLogin ? 'Вход в аккаунт' : 'Регистрация'}
                        </h1>

                        {message && (
                            <div className={`auth-message ${message.includes('Ошибка') ? 'error' : 'success'}`}>
                                {message}
                            </div>
                        )}

                        <form className="auth-form" onSubmit={handleSubmit}>
                            {!isLogin && (
                                <div className="form-group">
                                    <label className="form-label">Имя пользователя</label>
                                    <input
                                        type="text"
                                        name="nickname"
                                        className="form-input"
                                        value={formData.nickname}
                                        onChange={handleInputChange}
                                        required
                                        disabled={isLoading}
                                        placeholder="Введите ваше имя"
                                    />
                                </div>
                            )}

                            <div className="form-group">
                                <label className="form-label">Email</label>
                                <input
                                    type="email"
                                    name="email"
                                    className="form-input"
                                    value={formData.email}
                                    onChange={handleInputChange}
                                    required
                                    disabled={isLoading}
                                    placeholder="example@mail.com"
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">Пароль</label>
                                <input
                                    type="password"
                                    name="password"
                                    className="form-input"
                                    value={formData.password}
                                    onChange={handleInputChange}
                                    required
                                    disabled={isLoading}
                                    placeholder="Введите пароль"
                                />
                            </div>

                            {!isLogin && (
                                <div className="form-group">
                                    <label className="form-label">Подтвердите пароль</label>
                                    <input
                                        type="password"
                                        name="confirmPassword"
                                        className="form-input"
                                        value={formData.confirmPassword}
                                        onChange={handleInputChange}
                                        required
                                        disabled={isLoading}
                                        placeholder="Повторите пароль"
                                    />
                                </div>
                            )}

                            <button
                                type="submit"
                                className="auth-submit-btn"
                                disabled={isLoading}
                            >
                                {isLoading ? 'Загрузка...' : (isLogin ? 'Войти' : 'Зарегистрироваться')}
                            </button>
                        </form>

                        {isLogin && (
                            <>
                                <div className="guest-login-section">
                                    <div className="divider">
                                        <span>или</span>
                                    </div>
                                    <button
                                        type="button"
                                        className="guest-login-btn"
                                        onClick={handleGuestLogin}
                                        disabled={isLoading}
                                    >
                                        🎮 Войти как гость
                                    </button>
                                    <p className="guest-description">
                                        Быстрый доступ без регистрации. Некоторые функции могут быть ограничены.
                                    </p>
                                </div>
                            </>
                        )}

                        <div className="auth-switch">
                            <p>
                                {isLogin ? 'Еще нет аккаунта?' : 'Уже есть аккаунт?'}
                                <button 
                                    type="button" 
                                    className="switch-btn"
                                    onClick={toggleMode}
                                    disabled={isLoading}
                                >
                                    {isLogin ? 'Зарегистрироваться' : 'Войти'}
                                </button>
                            </p>
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