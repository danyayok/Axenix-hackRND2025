import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './static/404.css'

export default function NotFoundPage() {
    const [dots, setDots] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {

        const dotsArray = [
            { top: '20%', left: '20%', delay: 0 },
            { top: '60%', left: '80%', delay: 1 },
            { top: '80%', left: '30%', delay: 2 },
            { top: '40%', left: '70%', delay: 3 },
            { top: '10%', left: '50%', delay: 4 }
        ];
        setDots(dotsArray);
    }, []);

    const handleGoBack = () => {
        navigate(-1);
    };

    return (
        <div className="not-found-page">
            <div className="dots">
                {dots.map((dot, index) => (
                    <div 
                        key={index}
                        className="dot"
                        style={{
                            top: dot.top,
                            left: dot.left,
                            animationDelay: `${dot.delay}s`
                        }}
                    />
                ))}
            </div>

            <div className="decoration decoration-1"></div>
            <div className="decoration decoration-2"></div>
            <div className="decoration decoration-3"></div>

            <div className="container">
                <div className="error-code">404</div>
                <h1>Страница не найдена</h1>
                <p>
                    К сожалению, страница, которую вы ищете, не существует или была перемещена. 
                    Попробуйте вернуться на главную страницу или воспользуйтесь поиском.
                </p>
                <div className="buttons">
                    <Link to="/" className="btn btn-primary">
                        На главную
                    </Link>
                    <button onClick={handleGoBack} className="btn btn-secondary">
                        Назад
                    </button>
                </div>
            </div>
        </div>
    );
}