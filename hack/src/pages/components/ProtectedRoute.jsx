import { Navigate, useLocation } from 'react-router-dom';

export default function ProtectedRoute({ children }) {
    const location = useLocation();
    const isAuthenticated = localStorage.getItem('authToken');

    if (!isAuthenticated) {
        return <Navigate to="/Auth" state={{ from: location }} replace />;
    }

    return children;
}