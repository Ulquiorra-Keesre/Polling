// js/config.js
(function() {
    const Config = {
        // Настройки API
        API_BASE_URL: 'http://localhost:3000/api',
        APP_NAME: 'Система опросов',
        VERSION: '1.0.0',
        
        // Все эндпоинты API в одном месте
        ENDPOINTS: {
            // Авторизация
            AUTH: {
                LOGIN: '/auth/login',
                LOGOUT: '/auth/logout',
                VERIFY: '/auth/verify'
            },
            
            // Опросы
            POLLS: {
                LIST: '/polls',                    // GET - все опросы
                GET: '/polls',                     // GET /polls/{id} - конкретный опрос
                RESULTS: '/polls',                 // GET /polls/{id}/results - результаты
                CREATE: '/polls',                  // POST - создание опроса (админ)
                UPDATE: '/polls',                  // PUT /polls/{id} - обновление
                DELETE: '/polls'                   // DELETE /polls/{id} - удаление
            },
            
            // Голосование
            VOTES: {
                CREATE: '/votes',                  // POST - создание голоса
                CHECK: '/votes/check',             // POST - проверка, голосовал ли
                STATS: '/votes/stats'              // GET - статистика голосований
            },
            
            // Пользователи
            USERS: {
                PROFILE: '/users/profile',         // GET - профиль пользователя
                VOTES: '/users/votes'              // GET - голоса пользователя
            }
        },
        
        STORAGE_KEYS: {
            USER: 'user_data',
            AUTH: 'auth_status',
            POLLS_CACHE: 'polls_cache',
            SYNC_QUEUE: 'sync_queue',
            AUTH_TOKEN: 'auth_token'
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

    // Сделать глобальной переменной
    window.Config = Config;
})();