import { useState } from 'react';

const API_BASE_URL = 'http://localhost:8088/api';

export default function RoomControls({ roomSlug, isAdmin, onStateUpdate }) {
    const [isLoading, setIsLoading] = useState(false);
    const [newTopic, setNewTopic] = useState('');

    const setRoomLock = async (locked) => {
        if (!isAdmin) return;

        setIsLoading(true);
        try {
            const authToken = localStorage.getItem('authToken');
            const response = await fetch(`${API_BASE_URL}/state/${roomSlug}/lock`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`,
                },
                body: JSON.stringify({
                    value: locked
                }),
            });

            if (response.ok) {
                await onStateUpdate();
            }
        } catch (error) {
            console.error('Ошибка изменения блокировки:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const setMuteAll = async (muted) => {
        if (!isAdmin) return;

        setIsLoading(true);
        try {
            const authToken = localStorage.getItem('authToken');
            const response = await fetch(`${API_BASE_URL}/state/${roomSlug}/mute_all`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`,
                },
                body: JSON.stringify({
                    value: muted
                }),
            });

            if (response.ok) {
                await onStateUpdate();
            }
        } catch (error) {
            console.error('Ошибка управления аудио:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const setRoomTopic = async (e) => {
        e.preventDefault();
        if (!isAdmin || !newTopic.trim()) return;

        setIsLoading(true);
        try {
            const authToken = localStorage.getItem('authToken');
            const response = await fetch(`${API_BASE_URL}/state/${roomSlug}/topic`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`,
                },
                body: JSON.stringify({
                    topic: newTopic
                }),
            });

            if (response.ok) {
                setNewTopic('');
                await onStateUpdate();
            }
        } catch (error) {
            console.error('Ошибка изменения темы:', error);
        } finally {
            setIsLoading(false);
        }
    };

    if (!isAdmin) return null;

    return (
        <div className="room-controls">
            <h4>⚙️ Управление комнатой</h4>

            <div className="control-group">
                <label>Тема обсуждения:</label>
                <form onSubmit={setRoomTopic} className="topic-form">
                    <input
                        type="text"
                        value={newTopic}
                        onChange={(e) => setNewTopic(e.target.value)}
                        placeholder="Введите тему обсуждения..."
                        disabled={isLoading}
                        maxLength={100}
                    />
                    <button type="submit" disabled={!newTopic.trim() || isLoading}>
                        💾
                    </button>
                </form>
            </div>

            <div className="control-group">
                <label>Блокировка комнаты:</label>
                <div className="toggle-buttons">
                    <button
                        className={`toggle-btn unlock-btn`}
                        onClick={() => setRoomLock(false)}
                        disabled={isLoading}
                    >
                        🔓 Открыть
                    </button>
                    <button
                        className={`toggle-btn lock-btn`}
                        onClick={() => setRoomLock(true)}
                        disabled={isLoading}
                    >
                        🔒 Закрыть
                    </button>
                </div>
            </div>

            <div className="control-group">
                <label>Управление аудио:</label>
                <div className="toggle-buttons">
                    <button
                        className={`toggle-btn unmute-all-btn`}
                        onClick={() => setMuteAll(false)}
                        disabled={isLoading}
                    >
                        🔊 Разрешить всем
                    </button>
                    <button
                        className={`toggle-btn mute-all-btn`}
                        onClick={() => setMuteAll(true)}
                        disabled={isLoading}
                    >
                        🔇 Заглушить всех
                    </button>
                </div>
            </div>

            <div className="admin-notice">
                <small>⚠️ Только администраторы видят эти настройки</small>
            </div>
        </div>
    );
}