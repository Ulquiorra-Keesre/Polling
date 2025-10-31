// dataService.js
class DataService {
    static async getPolls() {
        try {
            // Пробуем получить с бэкенда
            const response = await fetch(`${Config.API_BASE_URL}${Config.ENDPOINTS.POLLS}`);
            
            if (response.ok) {
                const polls = await response.json();
                // Кэшируем в localStorage
                localStorage.setItem(Config.STORAGE_KEYS.POLLS_CACHE, JSON.stringify(polls));
                return polls;
            }
        } catch (error) {
            console.warn('Backend недоступен, используем кэш:', error);
        }
        
        // Fallback на localStorage
        return this.getCachedPolls();
    }

    static async vote(pollId, optionId) {
        const studentId = AuthService.getStudentId();
        const voteData = { pollId, optionId, studentId };
        
        try {
            const response = await fetch(`${Config.API_BASE_URL}${Config.ENDPOINTS.VOTE}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${AuthService.getToken()}`
                },
                body: JSON.stringify(voteData)
            });
            
            if (response.ok) {
                // Успешно отправили на сервер
                this.removeFromSyncQueue(pollId, studentId);
                return { success: true, fromServer: true };
            } else {
                throw new Error('Server error');
            }
        } catch (error) {
            console.warn('Backend недоступен, сохраняем локально:', error);
            // Сохраняем локально и добавляем в очередь синхронизации
            this.saveVoteLocally(pollId, optionId, studentId);
            this.addToSyncQueue(pollId, optionId, studentId);
            return { success: true, fromServer: false };
        }
    }

    static getCachedPolls() {
        const cached = localStorage.getItem(Config.STORAGE_KEYS.POLLS_CACHE);
        return cached ? JSON.parse(cached) : [];
    }

    static saveVoteLocally(pollId, optionId, studentId) {
        const voteKey = `vote_${pollId}_${studentId}`;
        localStorage.setItem(voteKey, optionId);
        localStorage.setItem(`${voteKey}_time`, new Date().toISOString());
    }

    static addToSyncQueue(pollId, optionId, studentId) {
        const queue = JSON.parse(localStorage.getItem(Config.STORAGE_KEYS.SYNC_QUEUE) || '[]');
        queue.push({
            pollId,
            optionId,
            studentId,
            timestamp: new Date().toISOString()
        });
        localStorage.setItem(Config.STORAGE_KEYS.SYNC_QUEUE, JSON.stringify(queue));
    }

    static async syncPendingVotes() {
        const queue = JSON.parse(localStorage.getItem(Config.STORAGE_KEYS.SYNC_QUEUE) || '[]');
        const successfulSyncs = [];
        
        for (const vote of queue) {
            try {
                const response = await fetch(`${Config.API_BASE_URL}${Config.ENDPOINTS.VOTE}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${AuthService.getToken()}`
                    },
                    body: JSON.stringify(vote)
                });
                
                if (response.ok) {
                    successfulSyncs.push(vote);
                }
            } catch (error) {
                console.warn('Не удалось синхронизировать голос:', vote);
            }
        }
        
        // Удаляем успешно синхронизированные голоса
        this.removeFromSyncQueue(successfulSyncs);
        return successfulSyncs.length;
    }

    static removeFromSyncQueue(votesToRemove) {
        const queue = JSON.parse(localStorage.getItem(Config.STORAGE_KEYS.SYNC_QUEUE) || '[]');
        const newQueue = queue.filter(existingVote => 
            !votesToRemove.some(voteToRemove => 
                voteToRemove.pollId === existingVote.pollId && 
                voteToRemove.studentId === existingVote.studentId
            )
        );
        localStorage.setItem(Config.STORAGE_KEYS.SYNC_QUEUE, JSON.stringify(newQueue));
    }
}