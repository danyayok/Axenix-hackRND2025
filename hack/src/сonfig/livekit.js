export const livekitConfig = {
    serverUrl: 'wss://livekit.myshore.ru',
    apiKey: 'APISVzXeGWB2JZL', // НОВЫЙ КЛЮЧ
    apiSecret: '8zsqNCiqHK7jAeDIj8VxYrIXRyyNzV7dRBFnRXoSMbC' // НОВЫЙ СЕКРЕТ
};

export const generateToken = async (username, roomName) => {
    // Генерация токена будет на бэкенде для безопасности
    const response = await fetch('http://localhost:8088/api/rtc/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            room_name: roomName
        })
    });

    if (response.ok) {
        const data = await response.json();
        return data.token;
    }
    throw new Error('Failed to generate token');
};