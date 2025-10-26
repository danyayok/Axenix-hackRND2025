import { useState, useEffect, useRef } from 'react';

const API_BASE_URL = 'http://localhost:8088/api';

export default function Chat({ roomSlug, userId, username, isConnected }) {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        loadChatHistory();
    }, [roomSlug]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const loadChatHistory = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/chat/${roomSlug}?limit=50`);
            if (response.ok) {
                const data = await response.json();
                setMessages(data.items || []);
            }
        } catch (error) {
            console.error('Ошибка загрузки чата:', error);
        }
    };

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!newMessage.trim() || !isConnected) return;

        setIsLoading(true);
        try {
            const authToken = localStorage.getItem('authToken');
            const response = await fetch(`${API_BASE_URL}/chat/${roomSlug}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`,
                },
                body: JSON.stringify({
                    user_id: userId,
                    text: newMessage
                }),
            });

            if (response.ok) {
                setNewMessage('');
                // Обновляем историю сообщений
                await loadChatHistory();
            }
        } catch (error) {
            console.error('Ошибка отправки сообщения:', error);
            alert('Ошибка отправки сообщения');
        } finally {
            setIsLoading(false);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const formatTime = (dateString) => {
        return new Date(dateString).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="chat-component">
            <div className="chat-header">
                <h3>💬 Чат комнаты</h3>
                <span className="message-count">{messages.length} сообщений</span>
            </div>

            <div className="chat-messages">
                {messages.length === 0 ? (
                    <div className="no-messages">
                        <p>Пока нет сообщений</p>
                        <p>Будьте первым, кто напишет!</p>
                    </div>
                ) : (
                    messages.map((message) => (
                        <div
                            key={message.id}
                            className={`message ${message.user_id === userId ? 'own-message' : 'other-message'}`}
                        >
                            <div className="message-header">
                                <span className="message-sender">
                                    {message.user_id === userId ? 'Вы' : `Участник ${message.user_id}`}
                                </span>
                                <span className="message-time">
                                    {formatTime(message.created_at)}
                                </span>
                            </div>
                            <div className="message-text">{message.text}</div>
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            <form className="chat-input-form" onSubmit={sendMessage}>
                <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder={isConnected ? "Введите сообщение..." : "Подключитесь к видео для чата"}
                    disabled={!isConnected || isLoading}
                    maxLength={500}
                />
                <button
                    type="submit"
                    disabled={!newMessage.trim() || !isConnected || isLoading}
                >
                    {isLoading ? '...' : '📤'}
                </button>
            </form>
        </div>
    );
}