// Mock data for demonstration
        const mockPollData = {
            id: 1,
            title: "Выбор темы для курсовой работы по веб-разработке",
            description: "Проголосуйте за наиболее интересную тему для курсовой работы. Результаты повлияют на распределение студентов по проектным группам. Ваш выбор полностью анонимен и не будет связан с вашей личностью.",
            options: [
                { id: 1, text: "Разработка мобильного приложения для здоровья", votes: 24 },
                { id: 2, text: "Создание системы управления задачами", votes: 45 },
                { id: 3, text: "Разработка платформы для онлайн-обучения", votes: 32 },
                { id: 4, text: "Создание системы анализа социальных сетей", votes: 18 }
            ],
            totalVotes: 119,
            endDate: "15.01.2024"
        };

        // Function to render results
        function renderResults(pollData) {
            // Update poll info
            document.getElementById('resultsPollTitle').textContent = pollData.title;
            document.getElementById('resultsPollDescription').textContent = pollData.description;
            document.getElementById('resultsTotalVotes').textContent = `${pollData.totalVotes} голосов`;
            
            // Render results items
            const resultsItems = document.getElementById('resultsItems');
            resultsItems.innerHTML = '';
            
            pollData.options.forEach((option, index) => {
                const percentage = pollData.totalVotes > 0 
                    ? Math.round((option.votes / pollData.totalVotes) * 100)
                    : 0;
                
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                resultItem.innerHTML = `
                    <div class="result-header">
                        <div class="result-option">
                            <div class="result-option-number">${index + 1}</div>
                            ${option.text}
                        </div>
                        <div class="result-stats">${percentage}% (${option.votes})</div>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${percentage}%"></div>
                    </div>
                `;
                resultsItems.appendChild(resultItem);
            });
        }


        // Logout functionality
        document.querySelector('.logout-btn').addEventListener('click', function() {
            if (confirm('Вы уверены, что хотите выйти из системы?')) {
                // In real app, clear session and redirect to login
                alert('Выход выполнен. В реальном приложении вы вернетесь на страницу авторизации.');
            }
        });

        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            // In a real app, you would fetch poll data from backend
            // const pollId = getPollIdFromUrl();
            // fetch(`/api/polls/${pollId}/results`).then(renderResults);
            
            // For demo, use mock data
            renderResults(mockPollData);
        });

        // Helper function to get poll ID from URL (for real implementation)
        function getPollIdFromUrl() {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get('pollId');
        }