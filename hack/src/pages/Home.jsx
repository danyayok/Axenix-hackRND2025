import { useState } from 'react';
import { Link } from 'react-router-dom';
import './static/Home.css';
// Импортируем все изображения
import Vector from './static/images/Vector.png';
import Vector1 from './static/images/Vector-1.png';
import Vector2 from './static/images/Vector-2.png';
import Vector3 from './static/images/Vector-3.png';
import Logo from './static/images/Logo1.svg';
import ProfileIcon from './static/images/profile.png';
import CreateIcon from './static/images/create.png';
import EnterIcon from './static/images/enter.png';
import NavDivMeet from './components/NavDiv';


export default function Home() {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [conferenceLink, setConferenceLink] = useState('');

    const openModal = () => setIsModalOpen(true);
    const closeModal = () => {
        setIsModalOpen(false);
        setConferenceLink('');
    };

    const handleJoinConference = () => {
        // Логика входа в конференцию
        console.log('Joining conference:', conferenceLink);
        closeModal();
    };
    

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleJoinConference();
        }
        if (e.key === 'Escape') {
            closeModal();
        }
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
                <section className="hero-section">
                    <h1 className="hero-title">
                        Сервис для проведения<br />
                        онлайн-конференций
                    </h1>
                    
                    <h2 className="action-title">Выберите действие</h2>
                    
                    <div className="actions-grid">
                        <Link to="/Profile" className="action-card-link">
                            <div className="action-card">
                                <img className="action-icon" src={ProfileIcon} alt="Профиль" />
                                <div className="action-text profile">Профиль</div>
                            </div>
                        </Link>

                        <Link to="/Plan-Conference" className="action-card-link">
                            <div className="action-card">
                                <img className="action-icon create" src={CreateIcon} alt="Создать конференцию" />
                                <div className="action-text">Создать конференцию</div>
                            </div>
                        </Link>

                        <div className="action-card" onClick={openModal}>
                            <div className="action-icon enter">
                                <img className="exclude" src={EnterIcon} alt="Войти в конференцию" />
                            </div>
                            <div className="action-text">Войти в конференцию</div>
                        </div>
                    </div>
                </section>

                {/* Модальное окно входа в конференцию */}
                {isModalOpen && (
                    <div className="modal-overlay active" onClick={closeModal}>
                        <div className="modal" onClick={(e) => e.stopPropagation()}>
                            <div className="modal-header">
                                <h2 className="modal-title">Войдите в конференцию</h2>
                                <button className="modal-close" onClick={closeModal}>×</button>
                            </div>
                            <div className="modal-body">
                                <p className="modal-description">Вставьте ссылку-приглашение</p>
                                <input 
                                    type="text" 
                                    className="modal-input" 
                                    placeholder="https://videoconf.com/room/abc123"
                                    value={conferenceLink}
                                    onChange={(e) => setConferenceLink(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    autoFocus
                                />
                            </div>
                            <div className="modal-footer">
                                <button className="btn-secondary" onClick={closeModal}>Отмена</button>
                                <button 
                                    className="btn-primary" 
                                    onClick={handleJoinConference}
                                    disabled={!conferenceLink.trim()}
                                >
                                    Войти
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </main>

            <footer className="footer">
                <p className="copyright">
                    ООО "Бнал" ИНН: 748327738990
                    Все права защищены
                </p>
            </footer>
        </>
    );
}