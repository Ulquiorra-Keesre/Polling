// src/components/Login.js
import React, { useState } from 'react';
import './Login.css';

const Login = ({ onLogin }) => {
  const [studentId, setStudentId] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!studentId.trim()) {
      alert('Пожалуйста, введите номер студенческого билета');
      return;
    }

    setLoading(true);
    
    try {
      const result = await onLogin(studentId);
      
      if (!result.success) {
        alert(result.error || 'Ошибка при авторизации');
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Ошибка при авторизации');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  return (
    <div className="login-container">
      <div className="login-screen">
        <div className="logo">
          <i className="fas fa-chart-bar"></i>
        </div>
        <h1>Система опросов и голосований</h1>
        <p>Авторизуйтесь как студент для участия в голосованиях</p>
        
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="studentId">Номер студенческого билета</label>
            <input 
              type="text" 
              id="studentId"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Введите номер студенческого" 
              disabled={loading}
            />
          </div>
          
          <button 
            type="submit" 
            className="login-btn"
            disabled={loading}
          >
            {loading ? (
              <>
                <i className="fas fa-spinner fa-spin"></i>
                Вход...
              </>
            ) : (
              <>
                <i className="fas fa-user"></i>
                Войти
              </>
            )}
          </button>
        </form>
        
        <div className="anonymity-notice">
          <h3><i className="fas fa-shield-alt"></i> Гарантия анонимности</h3>
          <p>Все голоса полностью анонимны. Ваша личность не будет связана с вашим выбором.</p>
        </div>
      </div>
    </div>
  );
};

export default Login;