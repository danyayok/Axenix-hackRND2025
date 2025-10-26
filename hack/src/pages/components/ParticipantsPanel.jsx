import React from 'react';

const ParticipantsPanel = ({ participants, currentUserId, roomSlug, isAdmin, onParticipantsUpdate }) => {

    const getInitials = (name) => {
        return name ? name.charAt(0).toUpperCase() : 'U';
    };

    const getRoleBadge = (role, isCurrentUser) => {
        if (isCurrentUser) {
            return <span className="participant-role participant">Вы</span>;
        }

        switch(role) {
            case 'owner':
                return <span className="participant-role owner">Владелец</span>;
            case 'admin':
                return <span className="participant-role admin">Админ</span>;
            default:
                return <span className="participant-role participant">Участник</span>;
        }
    };

    const getStatusIndicator = (participant) => {
        if (participant.is_online) {
            if (participant.is_speaking) {
                return <div className="status-indicator speaking" title="Говорит"></div>;
            }
            return <div className="status-indicator online" title="В сети"></div>;
        }
        return <div className="status-indicator offline" title="Не в сети"></div>;
    };

    const getMediaIcons = (participant) => {
        return (
            <div className="media-status">
                <span className={`media-icon ${participant.mic_muted ? 'muted' : 'active'}`} title={participant.mic_muted ? 'Микрофон выключен' : 'Микрофон включен'}>
                    🎤
                </span>
                <span className={`media-icon ${participant.cam_off ? 'muted' : 'active'}`} title={participant.cam_off ? 'Камера выключена' : 'Камера включена'}>
                    📹
                </span>
                {participant.hand_raised && (
                    <span className="hand-raised" title="Поднял руку">
                        ✋
                    </span>
                )}
            </div>
        );
    };

    return (
        <div className="participants-section">
            <h3>
                👥 Участники ({participants.length})
            </h3>
            <div className="participants-list">
                {participants.map((participant) => {
                    const isCurrentUser = participant.user_id === currentUserId;
                    const displayName = participant.nickname || `Участник ${participant.user_id}`;

                    return (
                        <div
                            key={participant.membership_id || participant.user_id}
                            className={`participant-item ${isCurrentUser ? 'current-user' : ''}`}
                        >
                            <div className={`participant-avatar ${participant.role} ${isCurrentUser ? 'current-user' : ''}`}>
                                {getInitials(displayName)}
                            </div>

                            <div className="participant-info">
                                <div className="participant-name-row">
                                    <span className="participant-name">
                                        {displayName}
                                        {isCurrentUser && ' (Вы)'}
                                    </span>
                                    {getRoleBadge(participant.role, isCurrentUser)}
                                </div>

                                <div className="participant-status">
                                    <div className="status-info">
                                        {getStatusIndicator(participant)}
                                        <span>
                                            {participant.is_online ? 'В сети' : 'Не в сети'}
                                        </span>
                                    </div>
                                    {getMediaIcons(participant)}
                                </div>
                            </div>
                        </div>
                    );
                })}

                {participants.length === 0 && (
                    <div className="no-participants">
                        <p style={{ color: '#888', textAlign: 'center', padding: '20px' }}>
                            Участников пока нет
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ParticipantsPanel;