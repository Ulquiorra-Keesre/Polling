// Mock data
        const mockPolls = [
            {
                id: 1,
                title: "Выбор темы для курсовой работы",
                description: "Проголосуйте за наиболее интересную тему для курсовой работы по веб-разработке",
                options: [
                    { id: 1, text: "Разработка мобильного приложения для здоровья", votes: 23 },
                    { id: 2, text: "Создание системы управления задачами", votes: 45 },
                    { id: 3, text: "Разработка платформы для онлайн-обучения", votes: 32 },
                    { id: 4, text: "Создание системы анализа социальных сетей", votes: 18 }
                ],
                totalVotes: 118,
                endDate: "2024-01-15",
                anonymous: true
            },
            {
                id: 2,
                title: "Оценка качества преподавания",
                description: "Анонимная оценка преподавателя по курсу 'Основы программирования'",
                options: [
                    { id: 1, text: "Отлично (5)", votes: 67 },
                    { id: 2, text: "Хорошо (4)", votes: 23 },
                    { id: 3, text: "Удовлетворительно (3)", votes: 8 },
                    { id: 4, text: "Неудовлетворительно (2)", votes: 2 }
                ],
                totalVotes: 100,
                endDate: "2024-01-20",
                anonymous: true
            }
        ];

        // State
        let currentUser = null;
        let currentPoll = null;
        let selectedOption = null;
        let hasVoted = false;

        // DOM Elements
        const screens = {
            login: document.getElementById('loginScreen'),
            polls: document.getElementById('pollsScreen'),
            voting: document.getElementById('votingScreen'),
            results: document.getElementById('resultsScreen'),
            confirmation: document.getElementById('confirmationScreen')
        };

        // Navigation functions
        function showScreen(screenName) {
            Object.values(screens).forEach(screen => {
                screen.style.display = 'none';
            });
            screens[screenName].style.display = 'block';
        }

        // Login functionality
        document.getElementById('loginBtn').addEventListener('click', function() {
            const studentId = document.getElementById('studentId').value || 'STU12345';
            currentUser = { id: studentId, name: `Студент ${studentId}` };
            
            // Update user info in all screens
            document.querySelectorAll('[id$="UserName"]').forEach(el => {
                el.textContent = currentUser.name;
            });
            
            showScreen('polls');
            renderPolls();
        });

        // Logout functionality
        document.getElementById('logoutBtn').addEventListener('click', logout);
        document.getElementById('votingLogoutBtn').addEventListener('click', logout);
        document.getElementById('resultsLogoutBtn').addEventListener('click', logout);
        document.getElementById('confirmationLogoutBtn').addEventListener('click', logout);

        function logout() {
            currentUser = null;
            currentPoll = null;
            selectedOption = null;
            hasVoted = false;
            showScreen('login');
            document.getElementById('studentId').value = '';
        }

        // Render polls list
        function renderPolls() {
            const pollsGrid = document.getElementById('pollsGrid');
            pollsGrid.innerHTML = '';
            
            mockPolls.forEach(poll => {
                const pollCard = document.createElement('div');
                pollCard.className = 'poll-card';
                pollCard.innerHTML = `
                    <div class="poll-header">
                        <h3 class="poll-title">${poll.title}</h3>
                        <div class="poll-stats">
                            <i class="fas fa-users"></i>
                            ${poll.totalVotes} голосов
                        </div>
                    </div>
                    <p class="poll-description">${poll.description}</p>
                    <div class="poll-meta">
                        <span><i class="fas fa-clock"></i> До ${poll.endDate}</span>
                        <span><i class="fas fa-user-secret"></i> Анонимно</span>
                    </div>
                    <button class="participate-btn" data-poll-id="${poll.id}">
                        Участвовать
                    </button>
                `;
                pollsGrid.appendChild(pollCard);
            });

            // Add event listeners to participate buttons
            document.querySelectorAll('.participate-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const pollId = parseInt(this.getAttribute('data-poll-id'));
                    currentPoll = mockPolls.find(p => p.id === pollId);
                    hasVoted = false;
                    selectedOption = null;
                    showVotingScreen();
                });
            });
        }

        // Show voting screen
        function showVotingScreen() {
            if (!currentPoll) return;
            
            // Update poll info
            document.getElementById('currentPollTitle').textContent = currentPoll.title;
            document.getElementById('currentPollDescription').textContent = currentPoll.description;
            document.getElementById('pollEndDate').textContent = currentPoll.endDate;
            document.getElementById('pollTotalVotes').textContent = currentPoll.totalVotes;
            
            // Render options
            const optionsList = document.getElementById('optionsList');
            optionsList.innerHTML = '';
            
            currentPoll.options.forEach(option => {
                const optionDiv = document.createElement('div');
                optionDiv.className = 'option-item';
                optionDiv.innerHTML = `
                    <label class="option-label">
                        <input type="radio" name="vote" value="${option.id}" class="option-input">
                        <span class="option-text">${option.text}</span>
                    </label>
                `;
                optionsList.appendChild(optionDiv);
            });
            
            // Add event listeners to radio buttons
            document.querySelectorAll('input[name="vote"]').forEach(radio => {
                radio.addEventListener('change', function() {
                    selectedOption = parseInt(this.value);
                    document.getElementById('voteBtn').disabled = false;
                    document.getElementById('voteBtn').style.cssText = 'background: #4f46e5; color: white;';
                    
                    // Update selected state
                    document.querySelectorAll('.option-label').forEach(label => {
                        label.classList.remove('selected');
                    });
                    this.closest('.option-label').classList.add('selected');
                });
            });
            
            // Reset vote button
            document.getElementById('voteBtn').disabled = true;
            document.getElementById('voteBtn').style.cssText = 'background: #d1d5db; color: #9ca3af;';
            
            showScreen('voting');
        }

        // Vote functionality
        document.getElementById('voteBtn').addEventListener('click', function() {
            if (selectedOption && currentPoll) {
                hasVoted = true;
                // In a real app, this would send the vote to the server
                showScreen('confirmation');
                
                // After 2 seconds, show results
                setTimeout(() => {
                    showResultsScreen();
                }, 2000);
            }
        });

        // Show results screen
        function showResultsScreen() {
            if (!currentPoll) return;
            
            // Update poll info
            document.getElementById('resultsPollTitle').textContent = currentPoll.title;
            document.getElementById('resultsPollDescription').textContent = currentPoll.description;
            document.getElementById('resultsPollEndDate').textContent = currentPoll.endDate;
            document.getElementById('resultsPollTotalVotes').textContent = currentPoll.totalVotes;
            
            // Render results
            const resultsList = document.getElementById('resultsList');
            resultsList.innerHTML = '';
            
            currentPoll.options.forEach(option => {
                const percentage = currentPoll.totalVotes > 0 
                    ? Math.round((option.votes / currentPoll.totalVotes) * 100)
                    : 0;
                
                const resultDiv = document.createElement('div');
                resultDiv.className = 'result-item';
                resultDiv.innerHTML = `
                    <div class="result-label">
                        <span class="result-option">${option.text}</span>
                        <span class="result-stats">${percentage}% (${option.votes})</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${percentage}%"></div>
                    </div>
                `;
                resultsList.appendChild(resultDiv);
            });
            
            showScreen('results');
        }

        // Navigation buttons
        document.getElementById('backToPollsBtn').addEventListener('click', function(e) {
            e.preventDefault();
            showScreen('polls');
        });

        document.getElementById('backToPollsFromResultsBtn').addEventListener('click', function(e) {
            e.preventDefault();
            showScreen('polls');
        });

        document.getElementById('backToPollsFromConfirmationBtn').addEventListener('click', function(e) {
            e.preventDefault();
            showScreen('polls');
        });

        // Vote again functionality
        document.getElementById('voteAgainBtn').addEventListener('click', function() {
            hasVoted = false;
            selectedOption = null;
            showVotingScreen();
        });

        // Initialize
        showScreen('login');