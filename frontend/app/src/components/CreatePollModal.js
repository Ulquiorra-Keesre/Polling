import React, { useState } from 'react';
import './CreatePollModal.css';

const CreatePollModal = ({ isOpen, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    end_date: '',
    options: ['', '']
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Валидация
    if (!formData.title.trim() || !formData.description.trim() || !formData.end_date) {
      alert('Заполните все обязательные поля');
      return;
    }

    const validOptions = formData.options.filter(opt => opt.trim() !== '');
    if (validOptions.length < 2) {
      alert('Добавьте как минимум 2 варианта ответа');
      return;
    }

    onCreate({
      ...formData,
      options: validOptions.map(opt => ({ text: opt }))
    });
  };

  const addOption = () => {
    setFormData(prev => ({
      ...prev,
      options: [...prev.options, '']
    }));
  };

  const removeOption = (index) => {
    if (formData.options.length > 2) {
      setFormData(prev => ({
        ...prev,
        options: prev.options.filter((_, i) => i !== index)
      }));
    }
  };

  const updateOption = (index, value) => {
    setFormData(prev => ({
      ...prev,
      options: prev.options.map((opt, i) => i === index ? value : opt)
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Создать новый опрос</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Название опроса *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              placeholder="Введите название опроса"
              required
            />
          </div>

          <div className="form-group">
            <label>Описание *</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Опишите опрос"
              rows="3"
              required
            />
          </div>

          <div className="form-group">
            <label>Дата окончания *</label>
            <input
              type="datetime-local"
              value={formData.end_date}
              onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
              required
            />
          </div>

          <div className="form-group">
            <label>Варианты ответов *</label>
            {formData.options.map((option, index) => (
              <div key={index} className="option-input-group">
                <input
                  type="text"
                  value={option}
                  onChange={(e) => updateOption(index, e.target.value)}
                  placeholder={`Вариант ${index + 1}`}
                  required
                />
                {formData.options.length > 2 && (
                  <button
                    type="button"
                    className="remove-option-btn"
                    onClick={() => removeOption(index)}
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
            <button type="button" className="add-option-btn" onClick={addOption}>
              + Добавить вариант
            </button>
          </div>

          <div className="modal-actions">
            <button type="button" className="cancel-btn" onClick={onClose}>
              Отмена
            </button>
            <button type="submit" className="create-btn">
              Создать опрос
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreatePollModal;