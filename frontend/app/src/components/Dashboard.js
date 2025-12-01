import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DataService } from '../services/DataService';
import { AuthService } from '../services/AuthService';
import CreatePollModal from './CreatePollModal';
import './Dashboard.css';

const Dashboard = ({ user, onLogout }) => {
  const [polls, setPolls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const navigate = useNavigate();

  const isAdmin = AuthService.isAdmin();

  useEffect(() => {
    loadPolls();
  }, []);

  const loadPolls = async () => {
    try {
      setLoading(true);
      const pollsData = await DataService.getPolls();
      setPolls(pollsData);
    } catch (error) {
      console.error('Error loading polls:', error);
      setError('Не удалось загрузить опросы');
    } finally {
      setLoading(false);
    }
  };

  const handlePollClick = (pollId) => {
    const hasVoted = DataService.hasVotedLocally(pollId);
    
    if (hasVoted) {
      navigate(`/results/${pollId}`);
    } else {
      navigate(`/poll/${pollId}`);
    }
  };

  const isPollExpired = (endDate) => {
    if (!endDate) return false;
    return new Date() > new Date(endDate);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Дата не указана';
    try {
      const date = new Date(dateString);
      const now = new Date();
      
      if (date < now) {
        return 'Завершен';
      }
      
      const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      };
      return `До ${date.toLocaleDateString('ru-RU', options)}`;
    } catch (error) {
      return 'Ошибка даты';
    }
  };

  const handleCreatePoll = async (pollData) => {
    try {
      const response = await fetch('http://localhost:8000/api/polls/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify(pollData)
      });

      if (response.ok) {
        const newPoll = await response.json();
        setPolls(prev => [newPoll, ...prev]);
        setShowCreateModal(false);
        alert('Опрос успешно создан!');
      } else {
        throw new Error('Ошибка при создании опроса');
      }
    } catch (error) {
      console.error('Error creating poll:', error);
      alert('Ошибка при создании опроса');
    }
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <Header user={user} onLogout={onLogout} />
        <div className="loading-state">
          <i className="fas fa-spinner fa-spin"></i>
          <p>Загрузка опросов...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-container">
        <Header user={user} onLogout={onLogout} />
        <div className="error-state">
          <i className="fas fa-exclamation-triangle"></i>
          <h3>Ошибка загрузки</h3>
          <p>{error}</p>
          <button className="retry-btn" onClick={loadPolls}>
            <i className="fas fa-redo"></i>
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <Header user={user} onLogout={onLogout} />
      
      <main className="dashboard-main">
        <div className="dashboard-header">
          <div>
            <h1>Доступные опросы</h1>
            <p>Выберите опрос для участия или просмотра результатов. Все голоса полностью анонимны.</p>
          </div>
          
          {isAdmin && (
            <button 
              className="create-poll-btn"
              onClick={() => setShowCreateModal(true)}
            >
              <i className="fas fa-plus"></i>
              Создать опрос
            </button>
          )}
        </div>

        {polls.length === 0 ? (
          <div className="empty-state">
            <i className="fas fa-inbox"></i>
            <h3>Нет доступных опросов</h3>
            <p>В данный момент нет активных опросов для голосования.</p>
          </div>
        ) : (
          <div className="polls-grid">
            {polls.map(poll => {
              const hasVoted = DataService.hasVotedLocally(poll.id);
              const isExpired = isPollExpired(poll.end_date);
              
              return (
                <div key={poll.id} className="poll-card">
                  <div className="poll-header">
                    <h3 className="poll-title">{poll.title}</h3>
                    <div className={`poll-status ${isExpired ? 'expired' : 'active'}`}>
                      {isExpired ? 'Завершен' : 'Активен'}
                    </div>
                  </div>
                  <p className="poll-description">{poll.description}</p>
                  <div className="poll-meta">
                    <div className="poll-stats">
                      <i className="fas fa-users"></i>
                      <span>{poll.total_votes || 0} голосов</span>
                    </div>
                    <div className="poll-info">
                      <div className="poll-info-item">
                        <i className="fas fa-clock"></i>
                        <span>{formatDate(poll.end_date)}</span>
                      </div>
                      <div className="poll-info-item">
                        <i className="fas fa-user-secret"></i>
                        <span>Анонимно</span>
                      </div>
                    </div>
                  </div>
                  <div className="participate-section">
                    <button 
                      className={`participate-btn ${isExpired ? 'disabled' : ''}`}
                      onClick={() => handlePollClick(poll.id)}
                      disabled={isExpired}
                    >
                      <i className={`fas fa-${hasVoted ? 'chart-bar' : 'vote-yea'}`}></i>
                      {isExpired ? 'Опрос завершен' : 
                        hasVoted ? 'Посмотреть результаты' : 'Участвовать в опросе'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      <CreatePollModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreatePoll}
      />
    </div>
  );
};

const Header = ({ user, onLogout }) => (
  <header className="header">
    <div className="header-content">
      <div className="user-info">
        <div className="avatar">
          {user?.name ? user.name.charAt(0).toUpperCase() : 'С'}
        </div>
        <div className="user-details">
          <h2>{user?.name || `Студент ${user?.id}`}</h2>
          <p>{user?.faculty || 'Факультет информатики'}</p>
        </div>
      </div>
      <button className="logout-btn" onClick={onLogout}>
        <i className="fas fa-sign-out-alt"></i>
        Выйти
      </button>
    </div>
  </header>
);

export default Dashboard;