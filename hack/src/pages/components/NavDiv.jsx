import { Link } from 'react-router-dom';
import Logo from '../static/images/Logo1.svg';

export default function NavDivMeet(){
    return(
        <header className="header">
            <img className="logo" src={Logo} alt="Логотип сервиса" />
            <nav className="nav-controls">
                <Link to='/Notification' className="nav-item">Уведомления</Link>
                <Link to='/Settings' className="nav-item">Настройки</Link>
            </nav>
        </header>
    )
}