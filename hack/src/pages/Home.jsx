import { useState } from 'react'
import { Routes, Route } from 'react-router-dom';
import Error from './404';
import Conference from './Conf';
import Invite from './Invite';
import PlanConference from './Plan-Conference';
import './static/Home.css'

// Импортируем все изображения
import Vector from './static/images/Vector.png';
import Vector1 from './static/images/Vector-1.png';
import Vector2 from './static/images/Vector-2.png';
import Vector3 from './static/images/Vector-3.png';
import Logo from './static/images/Logo 1.png';
import ProfileIcon from './static/images/profile.png';
import CreateIcon from './static/images/create.png';
import EnterIcon from './static/images/enter.png';

export default function Home(){
    return (
        <>
            <div className="background-elements">
                <img className="vector" src={Vector} alt="" />
                <img className="vector" src={Vector1} alt="" />
                <img className="vector" src={Vector2} alt="" />
                <img className="vector" src={Vector3} alt="" />
            </div>

            <header className="header">
                <img className="logo" src={Logo} alt="Логотип сервиса" />
                <nav className="nav-controls">
                    <a href="#" className="nav-item">Уведомления</a>
                    <a href="#" className="nav-item">Настройки</a>
                </nav>
            </header>

            <main className="main-content">
                <section className="hero-section">
                    <h1 className="hero-title">
                        Сервис для проведения<br />
                        онлайн-конференций
                    </h1>
                    
                    <h2 className="action-title">Выберите действие</h2>
                    
                    <div className="actions-grid">
                        <div className="action-card">
                            <img className="action-icon" src={ProfileIcon} alt="Профиль" />
                            <div className="action-text profile">Профиль</div>
                        </div>

                        <div className="action-card">
                            <img className="action-icon create" src={CreateIcon} alt="Создать конференцию" />
                            <div className="action-text">Создать конференцию</div>
                        </div>

                        <div className="action-card">
                            <div className="action-icon enter">
                                <img className="exclude" src={EnterIcon} alt="Войти в конференцию" />
                            </div>
                            <div className="action-text">Войти в конференцию</div>
                        </div>
                    </div>
                </section>
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