import { useState } from 'react';
import { Link } from 'react-router-dom';
import NavDivMeet from './components/NavDiv';
import './static/Create.css';
// Импортируем изображения
import Vector from './static/images/Vector.png';
import Vector1 from './static/images/Vector-1.png';
import Vector2 from './static/images/Vector-2.png';
import Vector3 from './static/images/Vector-3.png';

export default function CreateConference() {
    const [formData, setFormData] = useState({
        conferenceName: '',
        participants: '',
        description: '',
        date: '',
        time: '',
        nextWork: ''
    });

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: value
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log('Данные конференции:', formData);
        // Логика создания конференции
        alert('Конференция создана успешно!');
        
        // Сброс формы после успешного создания
        setFormData({
            conferenceName: '',
            participants: '',
            description: '',
            date: '',
            time: '',
            nextWork: ''
        });
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
                <section className="create-conference-section">
                    <h1 className="create-title">Создать конференцию</h1>
                    
                    <form className="conference-form" onSubmit={handleSubmit}>
                        {/* Название конференции */}
                        <div className="form-group">
                            <label className="form-label">Название конференции</label>
                            <input 
                                type="text" 
                                className="form-input" 
                                placeholder="Введите название конференции"
                                name="conferenceName"
                                value={formData.conferenceName}
                                onChange={handleInputChange}
                                required
                            />
                        </div>

                        {/* Участники */}
                        <div className="form-group">
                            <label className="form-label">Участники</label>
                            <input 
                                type="text" 
                                className="form-input" 
                                placeholder="Введите email участников через запятую"
                                name="participants"
                                value={formData.participants}
                                onChange={handleInputChange}
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
                            ></textarea>
                        </div>

                        {/* Дата и время */}
                        <div className="form-group">
                            <label className="form-label">Дата и время</label>
                            <div className="datetime-group">
                                <input 
                                    type="date" 
                                    className="form-input" 
                                    name="date"
                                    value={formData.date}
                                    onChange={handleInputChange}
                                    required
                                />
                                <input 
                                    type="time" 
                                    className="form-input" 
                                    name="time"
                                    value={formData.time}
                                    onChange={handleInputChange}
                                    required
                                />
                            </div>
                        </div>

                        {/* Следующая работа */}
                        <div className="form-group">
                            <label className="form-label">Следующая работа</label>
                            <input 
                                type="text" 
                                className="form-input" 
                                placeholder="Опишите следующие шаги после конференции"
                                name="nextWork"
                                value={formData.nextWork}
                                onChange={handleInputChange}
                            />
                        </div>

                        {/* Кнопка создания */}
                        <button type="submit" className="create-button">
                            Создать конференцию
                        </button>
                    </form>
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