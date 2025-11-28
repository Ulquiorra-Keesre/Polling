// src/components/Poll.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { DataService } from '../services/DataService';
import './Poll.css';

const Poll = ({ user }) => {
  const { pollId } = useParams();
  const navigate = useNavigate();
  const [poll, setPoll] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [loading, setLoading] = useState(true);
  const [voting, setVoting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPollData();
    checkIfVoted();
  }, [pollId]);

  const loadPollData = async () => {
    try {
      setLoading(true);
      const pollData = await DataService.getPollById(pollId);
      if (pollData) {
        setPoll(pollData);
      } else {
        setError('Опрос не найден');
      }
    } catch (error) {
      console.error('Error loading poll:', error);
      setError('Ошибка при загрузке опроса');
    } finally {
      setLoading(false);
    }
  };

  const checkIfVoted = async () => {
    try {
      const voteCheck = await DataService.checkVote(pollId);
      if (voteCheck.has_voted) {
        navigate(`/results/${pollId}`);
      }
    } catch (error) {
      console.warn('Could not check vote status:', error);
    }
  };

  const handleVote = async () => {
    if (!selectedOption) {
      alert('Пожалуйста, выберите вариант ответа');
      return;
    }

    try {
      setVoting(true);
      const result = await DataService.vote(pollId, selectedOption);
      
      if (result.success) {
        navigate(`/results/${pollId}`);
      } else {
        throw new Error('Ошибка при голосовании');
      }
    } catch (error) {
      console.error('Error voting:', error);
      alert('Ошибка при отправке голоса. Попробуйте еще раз.');
    } finally {
      setVoting(false);
    }
  };

  const formatDate = (dateString) => {
    const options = { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString('ru-RU', options);
  };

  if (loading) {
    return (
      <div className="poll-container">
        <Header user={user} />
        <div className="loading-state">
          <i className="fas fa-spinner fa-spin"></i>
          <p>Загрузка опроса...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="poll-container">
        <Header user={user} />
        <div className="error-state">
          <i className="fas fa-exclamation-triangle"></i>
          <h3>Ошибка</h3>
          <p>{error}</p>
          <Link to="/dashboard" className="back-btn">
            <i className="fas fa-arrow-left"></i>
            Назад к опросам
          </Link>
        </div>
      </div>
    );
  }

  if (!poll) {
    return (
      <div className="poll-container">
        <Header user={user} />
        <div className="error-state">
          <i className="fas fa-exclamation-triangle"></i>
          <h3>Опрос не найден</h3>
          <p>Запрошенный опрос не существует или был удален.</p>
          <Link to="/dashboard" className="back-btn">
            <i className="fas fa-arrow-left"></i>
            Назад к опросам
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="poll-container">
      <Header user={user} />
      
      {/* Poll Info Card */}
      <div className="poll-info-card">
        <div className="poll-header">
          <h1 className="poll-title">{poll.title}</h1>
          <div className="anonymity-badge">
            <i className="fas fa-user-secret"></i>
            Анонимное голосование
          </div>
        </div>
        <p className="poll-description">{poll.description}</p>
        <div className="poll-meta">
          <div className="poll-meta-item">
            <i className="fas fa-clock"></i>
            <span>Завершается: {formatDate(poll.end_date)}</span>
          </div>
          <div className="poll-meta-item">
            <i className="fas fa-users"></i>
            <span>{poll.total_votes || 0} голосов</span>
          </div>
        </div>
      </div>

      {/* Options Section */}
      <div className="options-section">
        <div className="options-header">
          <h2>Выберите вариант ответа:</h2>
          <p>Кликните на карточку с интересующим вас вариантом</p>
        </div>
        
        <div className="option-cards">
          {poll.options && poll.options.map((option, index) => (
            <div
              key={option.id}
              className={`option-card ${selectedOption === option.id ? 'selected' : ''}`}
              onClick={() => setSelectedOption(option.id)}
            >
              <div className="option-content">
                <div className="option-number">{index + 1}</div>
                <div className="option-text">{option.text}</div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="vote-button-section">
          <button 
            className={`vote-btn ${selectedOption ? 'active' : ''}`}
            onClick={handleVote}
            disabled={!selectedOption || voting}
          >
            {voting ? (
              <>
                <i className="fas fa-spinner fa-spin"></i>
                Отправка...
              </>
            ) : (
              <>
                <i className="fas fa-vote-yea"></i>
                Проголосовать
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

const Header = ({ user }) => (
  <header className="header">
    <div className="header-content">
      <Link to="/dashboard" className="back-btn">
        <i className="fas fa-arrow-left"></i>
        Назад к опросам
      </Link>
      <div className="user-info">
        <div className="avatar">
          {user?.name ? user.name.charAt(0).toUpperCase() : 'С'}
        </div>
        <div className="user-details">
          <h2>{user?.name || `Студент ${user?.id}`}</h2>
          <p>{user?.faculty || 'Факультет информатики'}</p>
        </div>
      </div>
    </div>
  </header>
);

export default Poll;