import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import NavDivMeet from './components/NavDiv';
import './static/Notification.css';

const API_BASE_URL = 'http://localhost:8088/api';

export default function Notification() {
    const [notifications, setNotifications] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [userId, setUserId] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        checkAuthAndLoadNotifications();
    }, []);

    const checkAuthAndLoadNotifications = async () => {
        try {
            const authData = localStorage.getItem('authData');
            if (!authData) {
                navigate('/Auth');
                return;
            }

            const data = JSON.parse(authData);
            setUserId(data.userId);
            await loadNotifications(data.userId);
        } catch (error) {
            console.error('Ошибка загрузки уведомлений:', error);
            navigate('/Auth');
        }
    };

    const loadNotifications = async (userId) => {
        try {
            const authToken = localStorage.getItem('authToken');
            const response = await fetch(`${API_BASE_URL}/notifications/${userId}?limit=100`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });

            if (response.ok) {
                const notificationsData = await response.json();
                setNotifications(notificationsData);
            } else {
                console.error('Ошибка загрузки уведомлений');
            }
        } catch (error) {
            console.error('Ошибка сети:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const markAsRead = async (notificationId) => {
        try {
            const authToken = localStorage.getItem('authToken');
            await fetch(`${API_BASE_URL}/notifications/${userId}/read/${notificationId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });

            // Обновляем локальное состояние
            setNotifications(prev => prev.map(notif =>
                notif.id === notificationId ? { ...notif, is_read: true } : notif
            ));
        } catch (error) {
            console.error('Ошибка отметки уведомления:', error);
        }
    };

    const markAllAsRead = async () => {
        try {
            const authToken = localStorage.getItem('authToken');
            await fetch(`${API_BASE_URL}/notifications/${userId}/read-all`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });

            // Обновляем локальное состояние
            setNotifications(prev => prev.map(notif => ({ ...notif, is_read: true })));
        } catch (error) {
            console.error('Ошибка отметки всех уведомлений:', error);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString('ru-RU');
    };

    const getNotificationIcon = (type) => {
        switch (type) {
            case 'conference_created':
                return '🎯';
            case 'invitation':
                return '📨';
            default:
                return '🔔';
        }
    };

    if (isLoading) {
        return (
            <>
                <NavDivMeet />
                <div className="loading">Загрузка уведомлений...</div>
            </>
        );
    }

    return (
        <>
            <NavDivMeet />

            <main className="main-content">
                <section className="notifications-section">
                    <div className="notifications-header">
                        <h1 className="notifications-title">Уведомления</h1>
                        {notifications.some(notif => !notif.is_read) && (
                            <button
                                className="mark-all-read-btn"
                                onClick={markAllAsRead}
                            >
                                Отметить все как прочитанные
                            </button>
                        )}
                    </div>

                    <div className="notifications-list">
                        {notifications.length === 0 ? (
                            <div className="no-notifications">
                                <p>У вас пока нет уведомлений</p>
                            </div>
                        ) : (
                            notifications.map(notification => (
                                <div
                                    key={notification.id}
                                    className={`notification-item ${notification.is_read ? 'read' : 'unread'}`}
                                    onClick={() => !notification.is_read && markAsRead(notification.id)}
                                >
                                    <div className="notification-icon">
                                        {getNotificationIcon(notification.type)}
                                    </div>
                                    <div className="notification-content">
                                        <h3 className="notification-title">{notification.title}</h3>
                                        <p className="notification-message">{notification.message}</p>
                                        <span className="notification-date">
                                            {formatDate(notification.created_at)}
                                        </span>
                                    </div>
                                    {!notification.is_read && (
                                        <div className="notification-badge">новое</div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </section>
            </main>
        </>
    );
}