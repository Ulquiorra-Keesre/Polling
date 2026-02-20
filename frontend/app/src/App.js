import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import Poll from './components/Poll';
import Results from './components/Results';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthService, USER_ROLES } from './services/AuthService';
import { DataService } from './services/DataService';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { checkAuth(); }, []);

  const checkAuth = async () => {
    const authStatus = await AuthService.checkAuth();
    setIsAuthenticated(authStatus);
    if (authStatus) {
      const userData = AuthService.getCurrentUser();
      const role = AuthService.getUserRole();
      setUser(userData);
      setUserRole(role);
    }
    setLoading(false);
  };

  const handleLogin = async (studentId) => {
    try {
      setLoading(true);
      const result = await AuthService.login(studentId);
      if (result.success) {
        setIsAuthenticated(true);
        setUser(result.user);
        setUserRole(result.role);
        await DataService.syncPendingVotes();
      }
      return result;
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    AuthService.logout();
    setIsAuthenticated(false);
    setUser(null);
    setUserRole(null);
  };

  if (loading) return <div className="loading-screen">Загрузка...</div>;

  return (
    <Router>
      <div className="App">
        <Routes>
          <Route 
            path="/login" 
            element={!isAuthenticated ? <Login onLogin={handleLogin} /> : <Navigate to="/dashboard" replace />} 
          />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute allowedRoles={[USER_ROLES.USER, USER_ROLES.ADMIN]}>
                <Dashboard user={user} userRole={userRole} onLogout={handleLogout} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/poll/:pollId" 
            element={
              <ProtectedRoute allowedRoles={[USER_ROLES.USER, USER_ROLES.ADMIN]}>
                <Poll user={user} userRole={userRole} />
              </ProtectedRoute>
            } 
          /> 
          <Route 
            path="/results/:pollId" 
            element={
              <ProtectedRoute allowedRoles={[USER_ROLES.USER, USER_ROLES.ADMIN]}>
                <Results user={user} userRole={userRole} />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute allowedRoles={[USER_ROLES.ADMIN]}>
                <Dashboard user={user} userRole={userRole} onLogout={handleLogout} adminView={true} />
              </ProtectedRoute>
            } 
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;