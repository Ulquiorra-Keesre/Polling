// js/config.js
(function() {
    const Config = {
        API_BASE_URL: 'http://localhost:8000/api',
        
        ENDPOINTS: {
            AUTH: {
                LOGIN: '/auth/login'
            },
            POLLS: {
                LIST: '/polls',
                GET: '/polls',
                RESULTS: '/polls'
            },
            VOTES: {
                CREATE: '/votes',
                CHECK: '/votes/check'
            }
        },
        
        STORAGE_KEYS: {
            USER: 'user_data',
            AUTH: 'auth_status',
            AUTH_TOKEN: 'auth_token',
            POLLS_CACHE: 'polls_cache',
            SYNC_QUEUE: 'sync_queue'
        },
        
        CACHE_DURATION: 5 * 60 * 1000, // 5 минут
    };

    window.Config = Config;
})();