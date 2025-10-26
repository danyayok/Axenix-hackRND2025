import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import NavDivMeet from './components/NavDiv';
import './static/Create.css';
import Vector from './static/images/Vector.png';
import Vector1 from './static/images/Vector-1.png';
import Vector2 from './static/images/Vector-2.png';
import Vector3 from './static/images/Vector-3.png';

const API_BASE_URL = 'http://localhost:8088/api';

export default function CreateConference() {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        is_private: false,
        create_invite: true
    });
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [userId, setUserId] = useState(null);
    const [isCheckingAuth, setIsCheckingAuth] = useState(true);
    const navigate = useNavigate();

    // Проверяем авторизацию при загрузке
    useEffect(() => {
        const checkAuth = () => {
            const authData = localStorage.getItem('authData');
            const authToken = localStorage.getItem('authToken');

            if (!authData || !authToken) {
                alert('Для создания конференции необходимо авторизоваться');
                navigate('/Auth');
                return false;
            }

            try {
                const userData = JSON.parse(authData);
                setUserId(userData.userId);
                setIsCheckingAuth(false);
                return true;
            } catch (error) {
                console.error('Ошибка парсинга authData:', error);
                localStorage.removeItem('authData');
                localStorage.removeItem('authToken');
                navigate('/Auth');
                return false;
            }
        };

        checkAuth();
    }, [navigate]);

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Дополнительная проверка перед отправкой
        if (!userId) {
            setMessage('error:Ошибка авторизации. Пожалуйста, войдите снова.');
            navigate('/Auth');
            return;
        }

        setIsLoading(true);
        setMessage('');

        try {
            const authToken = localStorage.getItem('authToken');

            // Подготавливаем данные для отправки согласно API схеме
            const conferenceData = {
                title: formData.title,
                is_private: formData.is_private,
                create_invite: formData.create_invite,
                created_by: userId.toString()
            };

            console.log('Отправка данных на создание комнаты:', conferenceData);

            // РЕАЛЬНЫЙ ЗАПРОС К БЭКЕНДУ
            const response = await fetch(`${API_BASE_URL}/rooms`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`,
                },
                body: JSON.stringify(conferenceData)
            });

            if (response.ok) {
                const roomData = await response.json();
                console.log('Комната создана успешно:', roomData);

                setMessage('success:Конференция создана успешно!');

                // После создания комнаты автоматически присоединяем пользователя
                await joinUserToRoom(roomData.slug, userId, authToken);

                // Показываем пригласительную ссылку
                setTimeout(() => {
                    let message = `Конференция "${roomData.title}" создана!\n\n`;

                    if (roomData.invite_url) {
                        const fullInviteUrl = `http://localhost:8088${roomData.invite_url}`;
                        message += `Пригласительная ссылка: ${fullInviteUrl}\n\n`;
                    }

                    message += `Ссылка для входа: http://localhost:8088/room/${roomData.slug}\n\n`;
                    message += `Скопируйте ссылки чтобы поделиться с участниками.`;

                    alert(message);

                    // Перенаправляем в созданную комнату
                    navigate(`/room/${roomData.slug}`);
                }, 1500);

                // Сброс формы ТОЛЬКО после успешного создания
                setFormData({
                    title: '',
                    description: '',
                    is_private: false,
                    create_invite: true
                });

            } else {
                const errorData = await response.json();
                console.error('Ошибка создания комнаты:', errorData);
                setMessage(`error:Ошибка создания конференции: ${errorData.detail || 'Неизвестная ошибка'}`);

                // НЕ сбрасываем форму при ошибке
            }
        } catch (error) {
            console.error('Ошибка:', error);
            setMessage(`error:Ошибка сети: ${error.message}`);

            // НЕ сбрасываем форму при ошибке сети
        } finally {
            setIsLoading(false);
        }
    };

    // Функция для присоединения пользователя к комнате
    const joinUserToRoom = async (roomSlug, userId, authToken) => {
        try {
            const joinData = {
                room_slug: roomSlug,
                user_id: userId
            };

            console.log('Присоединение пользователя к комнате:', joinData);

            const response = await fetch(`${API_BASE_URL}/participants/join`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`,
                },
                body: JSON.stringify(joinData)
            });

            if (response.ok) {
                const joinResult = await response.json();
                console.log('Пользователь присоединен к комнате:', joinResult);
                return true;
            } else {
                console.warn('Не удалось автоматически присоединить пользователя к комнате');
                return false;
            }
        } catch (error) {
            console.error('Ошибка присоединения к комнате:', error);
            return false;
        }
    };

    // Функция для получения списка комнат (для проверки)
    const fetchRooms = async () => {
        try {
            const authToken = localStorage.getItem('authToken');
            const response = await fetch(`${API_BASE_URL}/rooms`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });

            if (response.ok) {
                const rooms = await response.json();
                console.log('Список комнат:', rooms);
                return rooms;
            }
        } catch (error) {
            console.error('Ошибка получения списка комнат:', error);
        }
    };

    // Функция для заполнения демо-данными
    const fillDemoData = () => {
        setFormData({
            title: 'Еженедельное совещание команды',
            description: 'Обсуждение текущих задач и планирование на следующую неделю',
            is_private: true,
            create_invite: true
        });
    };

    // Функция для тестирования API
    const testAPI = async () => {
        try {
            const authToken = localStorage.getItem('authToken');
            const response = await fetch(`${API_BASE_URL}/rooms`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });

            if (response.ok) {
                const rooms = await response.json();
                alert(`API работает! Найдено комнат: ${rooms.length}`);
            } else {
                alert('Ошибка подключения к API');
            }
        } catch (error) {
            alert('Ошибка подключения к серверу: ' + error.message);
        }
    };

    // Показываем загрузку пока проверяем авторизацию
    if (isCheckingAuth) {
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
                    <section className="create-conference-section">
                        <div style={{ textAlign: 'center', padding: '2rem' }}>
                            <h2>Проверка авторизации...</h2>
                        </div>
                    </section>
                </main>
            </>
        );
    }

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
                <section className="create-conference-section">
                    <h1 className="create-title">Создать конференцию</h1>

                    {/* Кнопка тестирования API */}
                    <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
                        <button
                            type="button"
                            className="demo-button"
                            onClick={testAPI}
                            style={{ margin: '0 auto' }}
                        >
                            Тест подключения к API
                        </button>
                    </div>

                    {message && (
                        <div className={`create-message ${message.split(':')[0]}`}>
                            {message.split(':')[1]}
                        </div>
                    )}

                    <form className="conference-form" onSubmit={handleSubmit}>
                        {/* Название конференции */}
                        <div className="form-group">
                            <label className="form-label">Название конференции *</label>
                            <input
                                type="text"
                                className="form-input"
                                placeholder="Введите название конференции"
                                name="title"
                                value={formData.title}
                                onChange={handleInputChange}
                                required
                                disabled={isLoading}
                            />
                        </div>

                        {/* Описание */}
                        <div className="form-group">
                            <label className="form-label">Описание</label>
                            <textarea
                                className="form-input form-textarea"
                                placeholder="Опишите тему и цели конференции"
                                name="description"
                                value={formData.description}
                                onChange={handleInputChange}
                                rows="4"
                                disabled={isLoading}
                            ></textarea>
                        </div>

                        {/* Настройки конференции */}
                        <div className="form-group">
                            <label className="form-label">Настройки конференции</label>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
                                    <input
                                        type="checkbox"
                                        name="is_private"
                                        checked={formData.is_private}
                                        onChange={handleInputChange}
                                        disabled={isLoading}
                                        style={{ width: '18px', height: '18px' }}
                                    />
                                    <span style={{ fontWeight: '500' }}>
                                        Приватная комната (только по приглашению)
                                    </span>
                                </label>

                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
                                    <input
                                        type="checkbox"
                                        name="create_invite"
                                        checked={formData.create_invite}
                                        onChange={handleInputChange}
                                        disabled={isLoading}
                                        style={{ width: '18px', height: '18px' }}
                                    />
                                    <span style={{ fontWeight: '500' }}>
                                        Создать пригласительную ссылку
                                    </span>
                                </label>
                            </div>
                        </div>

                        {/* Информация о создателе */}
                        <div className="form-group">
                            <label className="form-label">Создатель</label>
                            <input
                                type="text"
                                className="form-input"
                                value={userId ? `Пользователь ID: ${userId}` : 'Не авторизован'}
                                disabled
                                style={{ opacity: 0.7 }}
                            />
                            <span className="form-hint">
                                Вы будете администратором созданной конференции
                            </span>
                        </div>

                        {/* Кнопки действий */}
                        <div className="form-actions">
                            <button
                                type="button"
                                className="demo-button"
                                onClick={fillDemoData}
                                disabled={isLoading}
                            >
                                Заполнить демо-данные
                            </button>

                            <button
                                type="submit"
                                className="create-button"
                                disabled={isLoading || !formData.title.trim()}
                            >
                                {isLoading ? 'Создание...' : 'Создать конференцию'}
                            </button>
                        </div>
                    </form>

                    {/* Дополнительная информация */}
                    <div className="creation-info" style={{
                        marginTop: '2rem',
                        padding: '1.5rem',
                        background: '#f8fafc',
                        borderRadius: '12px',
                        borderLeft: '4px solid var(--primary-color)'
                    }}>
                        <h3 style={{ marginBottom: '1rem', color: 'var(--text-dark)' }}>Как это работает:</h3>
                        <ul style={{ listStyleType: 'none', padding: 0 }}>
                            <li style={{ marginBottom: '0.5rem', paddingLeft: '1rem', position: 'relative' }}>
                                <span style={{ position: 'absolute', left: 0, color: 'var(--primary-color)' }}>•</span>
                                Данные отправляются на бэкенд и сохраняются в базе данных
                            </li>
                            <li style={{ marginBottom: '0.5rem', paddingLeft: '1rem', position: 'relative' }}>
                                <span style={{ position: 'absolute', left: 0, color: 'var(--primary-color)' }}>•</span>
                                Создается реальная комната с уникальным slug
                            </li>
                            <li style={{ marginBottom: '0.5rem', paddingLeft: '1rem', position: 'relative' }}>
                                <span style={{ position: 'absolute', left: 0, color: 'var(--primary-color)' }}>•</span>
                                Вы автоматически присоединяетесь к созданной комнате
                            </li>
                        </ul>
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