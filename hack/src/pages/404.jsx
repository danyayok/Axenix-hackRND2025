import { useState } from 'react'
import { Routes, Route } from 'react-router-dom';
import PlanConference from './Plan-Conference.jsx';
import Conference from './Conf.jsx';
import Home from './Home.jsx';
import Invite from './Invite.jsx';

export default function Error(){

    return(
        <>
        <h1>Вы ошиблись адресом</h1>
        </>
    )
}