// index/index.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Login page initialized');
    
    // Проверяем, если уже авторизован - перенаправляем
    if (AuthService.isAuthenticated()) {
        console.log('User already authenticated, redirecting to dashboard');
        window.location.href = '../dashboard/dashboard.html';
        return;
    }
    
    // Обработчик кнопки "Войти"
    document.getElementById('loginBtn').addEventListener('click', function(e) {
        e.preventDefault();
        handleLogin();
    });
    
    // Обработчик нажатия Enter
    document.getElementById('studentId').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleLogin();
        }
    });
});

function handleLogin() {
    const studentId = document.getElementById('studentId').value.trim();
    
    if (!studentId) {
        alert('Пожалуйста, введите номер студенческого билета');
        return;
    }
    
    console.log('Login attempt with student ID:', studentId);
    
    try {
        // Используем простую авторизацию (без API для начала)
        const userData = {
            id: studentId,
            name: `Студент ${studentId}`,
            faculty: 'Факультет информатики'
        };
        
        // Сохраняем в localStorage
        localStorage.setItem('userData', JSON.stringify(userData));
        localStorage.setItem('isAuthenticated', 'true');
        localStorage.setItem('studentId', studentId);
        
        console.log('Login successful, user data saved');
        
        // Перенаправляем на dashboard
        window.location.href = '../dashboard/dashboard.html';
        
    } catch (error) {
        console.error('Login error:', error);
        alert('Ошибка при авторизации');
    }
}