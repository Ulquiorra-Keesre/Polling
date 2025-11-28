// src/components/Results.js
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { DataService } from '../services/DataService';
import './Results.css';

const Results = ({ user }) => {
  const { pollId } = useParams();
  const [poll, setPoll] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadResults();
  }, [pollId]);

  const loadResults = async () => {
    try {
      setLoading(true);
      
      // Загружаем результаты
      const resultsData = await DataService.getPollResults(pollId);
      if (resultsData) {
        setResults(resultsData);
        setPoll(resultsData.poll);
      } else {
        // Если результатов нет, загружаем базовую информацию об опросе
        const pollData = await DataService.getPollById(pollId);
        if (pollData) {
          setPoll(pollData);
          // Создаем mock результаты из данных опроса
          setResults({
            poll: pollData,
            options: pollData.options || []
          });
        } else {
          setError('Опрос не найден');
        }
      }
    } catch (error) {
      console.error('Error loading results:', error);
      setError('Ошибка при загрузке результатов');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const options = { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric'
    };
    return new Date(dateString).toLocaleDateString('ru-RU', options);
  };

  if (loading) {
    return (
      <div className="results-container">
        <Header user={user} />
        <div className="loading-state">
          <i className="fas fa-spinner fa-spin"></i>
          <p>Загрузка результатов...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="results-container">
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

  if (!poll || !results) {
    return (
      <div className="results-container">
        <Header user={user} />
        <div className="error-state">
          <i className="fas fa-exclamation-triangle"></i>
          <h3>Данные не найдены</h3>
          <p>Не удалось загрузить результаты опроса.</p>
          <Link to="/dashboard" className="back-btn">
            <i className="fas fa-arrow-left"></i>
            Назад к опросам
          </Link>
        </div>
      </div>
    );
  }

  const totalVotes = poll.total_votes || results.options.reduce((sum, option) => sum + (option.votes || 0), 0);

  return (
    <div className="results-container">
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
            <span>{totalVotes} голосов</span>
          </div>
        </div>
      </div>

      {/* Results Section */}
      <div className="results-section">
        <div className="results-header">
          <h2 className="results-title">Результаты голосования</h2>
        </div>
        
        <div className="results-items">
          {results.options && results.options.length > 0 ? (
            results.options.map((option, index) => {
              const percentage = totalVotes > 0 
                ? Math.round((option.votes / totalVotes) * 100)
                : 0;
              
              return (
                <div key={option.id} className="result-item">
                  <div className="result-header">
                    <div className="result-option">
                      <div className="result-option-number">{index + 1}</div>
                      {option.text}
                    </div>
                    <div className="result-stats">
                      {percentage}% ({option.votes || 0})
                    </div>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="no-results">
              <i className="fas fa-chart-bar"></i>
              <p>Нет данных для отображения</p>
            </div>
          )}
        </div>
        
        <div className="success-notice">
          <div className="success-icon">
            <i className="fas fa-check-circle"></i>
          </div>
          <h3 className="success-title">Ваш голос учтен!</h3>
          <p className="success-text">
            Благодарим за участие в голосовании. {totalVotes > 0 ? 'Результаты обновлены в реальном времени.' : 'Будьте первым, кто проголосует!'}
          </p>
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

export default Results;