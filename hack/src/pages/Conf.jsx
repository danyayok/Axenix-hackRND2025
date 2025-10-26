import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    LiveKitRoom,
    VideoConference,
    RoomAudioRenderer,
    ControlBar,
} from '@livekit/components-react';
import NavDivMeet from './components/NavDiv';
import Chat from './components/Chat';
import ParticipantsPanel from './components/ParticipantsPanel';
import RoomControls from './components/RoomControls';
import './static/Conf.css';

const API_BASE_URL = 'http://localhost:8088/api';

export default function Conference() {
    const { slug } = useParams();
    const navigate = useNavigate();

    const [room, setRoom] = useState(null);
    const [participants, setParticipants] = useState([]);
    const [roomState, setRoomState] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [userId, setUserId] = useState(null);
    const [username, setUsername] = useState('');
    const [token, setToken] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [showChat, setShowChat] = useState(true);
    const [showParticipants, setShowParticipants] = useState(true);

    useEffect(() => {
        checkAuthAndLoadConference();
    }, [slug]);

    const checkAuthAndLoadConference = async () => {
        try {
            const authData = localStorage.getItem('authData');
            if (!authData) {
                navigate('/Auth');
                return;
            }

            const data = JSON.parse(authData);
            setUserId(data.userId);

            const userUsername = data.userData?.nickname ||
                               data.userData?.email ||
                               `user_${data.userId}`;
            setUsername(userUsername);

            await loadConferenceData();
        } catch (error) {
            console.error('Ошибка загрузки конференции:', error);
            setError('Ошибка загрузки данных конференции');
        }
    };

    const loadConferenceData = async () => {
        try {
            setIsLoading(true);
            setError('');

            const roomResponse = await fetch(`${API_BASE_URL}/rooms/${slug}`);
            if (!roomResponse.ok) {
                if (roomResponse.status === 404) {
                    throw new Error('Комната не найдена');
                }
                throw new Error('Ошибка загрузки комнаты');
            }
            const roomData = await roomResponse.json();
            setRoom(roomData);

            await loadParticipants(roomData.slug);
            await loadRoomState(roomData.slug);
            await generateLiveKitToken(roomData.slug);

        } catch (error) {
            console.error('Ошибка загрузки данных:', error);
            setError(error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const generateLiveKitToken = async (roomName) => {
        try {
            const safeUsername = username || `user_${Date.now()}`;

            const response = await fetch(`${API_BASE_URL}/rtc/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: safeUsername,
                    room_name: roomName
                })
            });

            if (response.ok) {
                const data = await response.json();
                setToken(data.token);
            } else {
                throw new Error('Ошибка генерации токена');
            }
        } catch (error) {
            console.error('Ошибка генерации токена LiveKit:', error);
            setError('Ошибка подключения к видео-серверу');
        }
    };

    const loadParticipants = async (roomSlug) => {
        try {
            const response = await fetch(`${API_BASE_URL}/participants/${roomSlug}`);
            if (response.ok) {
                const data = await response.json();
                setParticipants(data.participants || []);
            }
        } catch (error) {
            console.error('Ошибка загрузки участников:', error);
        }
    };

    const loadRoomState = async (roomSlug) => {
        try {
            const response = await fetch(`${API_BASE_URL}/state/${roomSlug}`);
            if (response.ok) {
                const stateData = await response.json();
                setRoomState(stateData);
            }
        } catch (error) {
            console.error('Ошибка загрузки состояния комнаты:', error);
        }
    };

    const handleJoinConference = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/participants/join`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    room_slug: slug,
                    user_id: userId,
                    invite_key: room?.is_private ? room.invite_key : null
                }),
            });

            if (response.ok) {
                await loadParticipants(slug);
                if (token) {
                    setIsConnected(true);
                }
                // Показать уведомление об успешном присоединении
                showNotification('✅ Вы успешно присоединились к конференции');
            } else {
                const errorData = await response.json();
                showNotification(`❌ Ошибка: ${errorData.detail || 'Неизвестная ошибка'}`);
            }
        } catch (error) {
            console.error('Ошибка присоединения:', error);
            showNotification('❌ Ошибка присоединения к конференции');
        }
    };

    const handleLeaveConference = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/participants/leave`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    room_slug: slug,
                    user_id: userId
                }),
            });

            if (response.ok) {
                await loadParticipants(slug);
                setIsConnected(false);
                showNotification('👋 Вы вышли из конференции');
            } else {
                showNotification('❌ Ошибка выхода из конференции');
            }
        } catch (error) {
            console.error('Ошибка выхода:', error);
            showNotification('❌ Ошибка выхода из конференции');
        }
    };

    const copyInviteLink = () => {
        if (room?.invite_url) {
            const fullUrl = `http://localhost:8088${room.invite_url}`;
            navigator.clipboard.writeText(fullUrl);
            showNotification('📋 Пригласительная ссылка скопирована!');
        }
    };

    const copyInviteKey = () => {
        if (room?.invite_key) {
            navigator.clipboard.writeText(room.invite_key);
            showNotification('🔑 Инвайт-ключ скопирован!');
        }
    };

    const copyRoomLink = () => {
        const roomUrl = `http://localhost:5173/room/${slug}`;
        navigator.clipboard.writeText(roomUrl);
        showNotification('🔗 Ссылка на комнату скопирована!');
    };

    const showNotification = (message) => {
        // Создаем временное уведомление
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 15px 20px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    };

    const isUserParticipant = () => {
        return participants.some(participant => participant.user_id === userId);
    };

    const isUserAdmin = () => {
        const userParticipant = participants.find(p => p.user_id === userId);
        return userParticipant?.role === 'admin' || userParticipant?.role === 'owner';
    };

    const handleRoomDisconnected = () => {
        setIsConnected(false);
        showNotification('📞 Соединение с видео-сервером прервано');
    };

    if (isLoading) {
        return (
            <>
                <NavDivMeet />
                <div className="conference-loading">
                    <div className="loading-spinner"></div>
                    <h2>Загрузка конференции {slug}...</h2>
                </div>
            </>
        );
    }

    if (error) {
        return (
            <>
                <NavDivMeet />
                <div className="conference-error">
                    <h2>Ошибка</h2>
                    <p>{error}</p>
                    <button
                        className="join-btn"
                        onClick={() => navigate('/')}
                    >
                        Вернуться на главную
                    </button>
                </div>
            </>
        );
    }

    if (!room) {
        return (
            <>
                <NavDivMeet />
                <div className="conference-error">
                    <h2>Конференция не найдена</h2>
                    <button
                        className="join-btn"
                        onClick={() => navigate('/')}
                    >
                        Вернуться на главную
                    </button>
                </div>
            </>
        );
    }

    return (
        <>
            <NavDivMeet />

            {/* CSS для анимаций */}
            <style>
                {`
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                .loading-spinner {
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #4299e1;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                `}
            </style>

            <main className="main-content">
                <section className="conference-section">
                    <div className="conference-header">
                        <div className="conference-info">
                            <h1 className="conference-title">{room.title}</h1>
                            <p className="conference-slug">ID: {room.slug}</p>
                            <p className="conference-privacy">
                                {room.is_private ? '🔒 Приватная комната' : '🔓 Публичная комната'}
                            </p>
                            {roomState?.topic && (
                                <p className="conference-topic">🎯 Тема: {roomState.topic}</p>
                            )}
                            <div className="user-info">
                                <span>👤 Вы: {username}</span>
                                {isUserAdmin() && <span className="admin-badge">👑 Администратор</span>}
                            </div>
                        </div>

                        <div className="conference-actions">
                            {!isUserParticipant() ? (
                                <button
                                    className="join-btn"
                                    onClick={handleJoinConference}
                                >
                                    🚀 Присоединиться
                                </button>
                            ) : (
                                <button
                                    className="leave-btn"
                                    onClick={handleLeaveConference}
                                >
                                    👋 Покинуть
                                </button>
                            )}

                            {!isConnected && isUserParticipant() && token && (
                                <button
                                    className="connect-video-btn"
                                    onClick={() => setIsConnected(true)}
                                >
                                    📹 Подключить видео
                                </button>
                            )}

                            {room.is_private && (
                                <button
                                    className="invite-btn"
                                    onClick={copyInviteKey}
                                >
                                    🔑 Ключ
                                </button>
                            )}

                            <button
                                className="invite-btn"
                                onClick={copyInviteLink}
                                disabled={!room.invite_url}
                            >
                                📋 Пригласить
                            </button>

                            <button
                                className="copy-link-btn"
                                onClick={copyRoomLink}
                            >
                                🔗 Ссылка
                            </button>

                            <button
                                className={`toggle-btn ${showChat ? 'active' : ''}`}
                                onClick={() => setShowChat(!showChat)}
                            >
                                💬 Чат {showChat ? '▴' : '▾'}
                            </button>

                            <button
                                className={`toggle-btn ${showParticipants ? 'active' : ''}`}
                                onClick={() => setShowParticipants(!showParticipants)}
                            >
                                👥 Участники {showParticipants ? '▴' : '▾'}
                            </button>
                        </div>
                    </div>

                    <div className="conference-content">
                        {showParticipants && (
                            <div className="conference-sidebar">
                                <ParticipantsPanel
                                    participants={participants}
                                    currentUserId={userId}
                                    roomSlug={slug}
                                    isAdmin={isUserAdmin()}
                                    onParticipantsUpdate={loadParticipants}
                                />

                                <div className="room-state-section">
                                    <h3>📊 Статус комнаты</h3>
                                    <div className="state-info">
                                        <div className="state-item">
                                            <span>Статус:</span>
                                            <span className={`status ${roomState?.is_locked ? 'locked' : 'open'}`}>
                                                {roomState?.is_locked ? '🔒 Закрыта' : '🔓 Открыта'}
                                            </span>
                                        </div>
                                        <div className="state-item">
                                            <span>Аудио:</span>
                                            <span className={`status ${roomState?.mute_all ? 'muted' : 'unmuted'}`}>
                                                {roomState?.mute_all ? '🔇 Выкл' : '🔊 Вкл'}
                                            </span>
                                        </div>
                                        <div className="state-item">
                                            <span>Онлайн:</span>
                                            <span className="online-count">
                                                👥 {roomState?.online_count || 0}
                                            </span>
                                        </div>
                                        {roomState?.raised_hands && roomState.raised_hands.length > 0 && (
                                            <div className="state-item">
                                                <span>Поднятые руки:</span>
                                                <span className="online-count">
                                                    ✋ {roomState.raised_hands.length}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="conference-main">
                            {isConnected && token ? (
                                <div className="video-conference-container">
                                    <LiveKitRoom
                                        serverUrl={'wss://livekit.myshore.ru'}
                                        token={token}
                                        connect={true}
                                        audio={true}
                                        video={true}
                                        onDisconnected={handleRoomDisconnected}
                                        options={{
                                            adaptiveStream: true,
                                            dynacast: true,
                                            publishDefaults: {
                                                videoCodec: 'vp8',
                                            },
                                        }}
                                    >
                                        <VideoConference />
                                        <RoomAudioRenderer />
                                        <ControlBar
                                            controls={{
                                                microphone: true,
                                                camera: true,
                                                screenShare: true,
                                                leave: false
                                            }}
                                        />
                                    </LiveKitRoom>

                                    <RoomControls
                                        roomSlug={slug}
                                        isAdmin={isUserAdmin()}
                                        onStateUpdate={loadRoomState}
                                    />
                                </div>
                            ) : (
                                <div className="video-placeholder">
                                    <div className="placeholder-content">
                                        <h3>🎥 Готовы к видеовстрече?</h3>
                                        <p>Присоединитесь к видео-конференции чтобы начать общение с участниками</p>
                                        {isUserParticipant() && token && (
                                            <button
                                                className="start-video-btn"
                                                onClick={() => setIsConnected(true)}
                                            >
                                                🚀 Начать видеовстречу
                                            </button>
                                        )}
                                        {!isUserParticipant() && (
                                            <button
                                                className="join-first-btn"
                                                onClick={handleJoinConference}
                                            >
                                                📝 Сначала присоединитесь к конференции
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )}

                            {showChat && (
                                <div className="chat-container">
                                    <Chat
                                        roomSlug={slug}
                                        userId={userId}
                                        username={username}
                                        isConnected={isConnected}
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                </section>
            </main>
        </>
    );
}