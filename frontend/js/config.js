const Config = {
    // Настройки API
    API_BASE_URL: 'http://localhost:3000/api',
    APP_NAME: 'Система опросов',
    VERSION: '1.0.0',
    
    STORAGE_KEYS: {
        USER: 'user_data',
        AUTH: 'auth_status',
        POLLS_CACHE: 'polls_cache',
        SYNC_QUEUE: 'sync_queue'
    },
    
    CACHE_DURATION: 5 * 60 * 1000, // 5 минут
};

// Автоматическое определение окружения
Config.isDevelopment = window.location.hostname === 'localhost' || 
                      window.location.hostname === '127.0.0.1';

if (Config.isDevelopment) {
    Config.API_BASE_URL = 'http://localhost:3000/api';
} else {
    Config.API_BASE_URL = 'https://your-production-domain.com/api';
}

export default Config;