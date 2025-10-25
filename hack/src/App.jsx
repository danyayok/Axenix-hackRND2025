import { Routes, Route } from 'react-router-dom';
import Error from './pages/404';
import Conference from './pages/Conf.jsx';
import Home from './pages/Home.jsx';
import Invite from './pages/Invite.jsx';
import Notification from './pages/Notification.jsx';
import PlanConference from './pages/Plan-Conference.jsx';
import Settings from './pages/Settings.jsx';
import Profile from './pages/Profile.jsx';
import CreateConference from './pages/Create.jsx';

import './App.css'

function App() {
  return (
    <>
      <Routes>
        <Route path='/' element={<Home />} />
        <Route path='/Invite' element={<Invite/>} />
        <Route path='/Conference' element={<Conference/>} />
        <Route path='/Notification' element={<Notification />} />
        <Route path='/Settings' element={<Settings />} />
        <Route path='/Profile' element={<Profile />} />
        <Route path='/Plan-Conference' element={<PlanConference />} />
        <Route path='/Create' element={<CreateConference/>}></Route> 
        <Route path='*' element={<Error />} />
      </Routes>
    </>
  )
}

export default App