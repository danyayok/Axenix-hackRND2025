import { useState } from 'react'
import { Routes, Route } from 'react-router-dom';
import Error from './pages/404';
import Conference from './pages/Conf.jsx';
import Home from './pages/Home.jsx';
import Invite from './pages/Invite.jsx';

import './App.css'

function App() {


  return (
    <>
      <Routes>
        <Route path='/' element={<Home />}>

        </Route >

        <Route path='/Invite' element={<Invite/>}>
          
        </Route>

        <Route path='/Conference' element={<Conference/>}>
          
        </Route>

        <Route>
          
        </Route>

          <Route path='*' element={<Error />}>

        </Route>
      </Routes>


    </>
  )
}

export default App
