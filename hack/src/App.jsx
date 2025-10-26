import { Routes, Route } from 'react-router-dom';
import ProtectedRoute from './pages/components/ProtectedRoute';

import Conference from './pages/Conf.jsx';
import Home from './pages/Home.jsx';
import Invite from './pages/Invite.jsx';
import Notification from './pages/Notification.jsx';
import PlanConference from './pages/Plan-Conference.jsx';
import Settings from './pages/Settings.jsx';
import Profile from './pages/Profile.jsx';
import CreateConference from './pages/Create.jsx';
import Auth from './Auth.jsx';
import NotFoundPage from './pages/404';

import './App.css'

function App() {
  return (
    <>
      <Routes>
        <Route path='/' element={<Home />} />
        <Route path='/Auth' element={<Auth />} />

        {/* Защищенные маршруты */}
        <Route path='/Profile' element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        } />

        <Route path='/Conference' element={
          <ProtectedRoute>
            <Conference />
          </ProtectedRoute>
        } />

        <Route path='/Create' element={
          <ProtectedRoute>
            <CreateConference />
          </ProtectedRoute>
        } />

        <Route path='/Settings' element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        } />

        <Route path='/Plan-Conference' element={
          <ProtectedRoute>
            <CreateConference />
          </ProtectedRoute>
        } />

        {/* Остальные маршруты */}
        <Route path='/Invite' element={<Invite/>} />
        <Route path='/Notification' element={<Notification />} />
        <Route path="/room/:slug" element={<Conference />} />
        <Route path='*' element={<NotFoundPage />} />
      </Routes>
    </>
  )
}

export default App