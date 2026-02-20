// frontend/src/components/ProtectedRoute.js
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { AuthService, USER_ROLES } from '../services/AuthService';

const ProtectedRoute = ({ children, allowedRoles = [], redirectTo = '/login' }) => {
  const location = useLocation();
  
  const token = localStorage.getItem('auth_token');
  const isAuthenticated = !!token;
  
  const userRole = AuthService.getUserRole();

  if (!isAuthenticated) {
    console.log('→ No token, redirect to', redirectTo);
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  if (allowedRoles.length > 0) {
    const roles = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
    
    if (!roles.includes(userRole)) {
      console.log('→ Role mismatch. User:', userRole, 'Allowed:', roles);
      return <Navigate to="/dashboard" replace />;
    }
  }
  
  console.log('→ Access granted, rendering children');
  return children;
};

export default ProtectedRoute;