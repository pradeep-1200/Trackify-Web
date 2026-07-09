document.addEventListener('DOMContentLoaded', function() {
    const timerDisplay = document.getElementById('timer-display');
    const startBtn = document.getElementById('start-btn');
    const pauseBtn = document.getElementById('pause-btn');
    const resetBtn = document.getElementById('reset-btn');
    const sessionTypeDisplay = document.getElementById('session-type');
    const sessionCounter = document.getElementById('session-counter');

    if (!timerDisplay || !startBtn) return;

    let timer;
    let timeLeft = 0;
    let isRunning = false;
    let isWorkSession = true;
    let sessionsCompleted = 0;
    let sessionType = 'work';

    const workDuration = parseInt(timerDisplay.dataset.workDuration) * 60 || 25 * 60;
    const shortBreakDuration = parseInt(timerDisplay.dataset.shortBreakDuration) * 60 || 5 * 60;
    const longBreakDuration = parseInt(timerDisplay.dataset.longBreakDuration) * 60 || 15 * 60;
    const longBreakInterval = parseInt(timerDisplay.dataset.longBreakInterval) || 4;

    function updateDisplay() {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        // Update progress circle if exists
        const progressCircle = document.getElementById('progress-circle');
        if (progressCircle) {
            const totalDuration = isWorkSession ? workDuration :
                                (sessionsCompleted % longBreakInterval === 0 ? longBreakDuration : shortBreakDuration);
            const circumference = 2 * Math.PI * 40;
            const offset = circumference - (timeLeft / totalDuration) * circumference;
            progressCircle.style.strokeDashoffset = offset;
        }
    }

    function startTimer(duration) {
        if (isRunning) return;

        timeLeft = duration;
        isRunning = true;
        updateDisplay();

        timer = setInterval(() => {
            timeLeft--;
            updateDisplay();

            if (timeLeft <= 0) {
                clearInterval(timer);
                isRunning = false;
                handleSessionEnd();
            }
        }, 1000);
    }

    function handleSessionEnd() {
        // Play sound if enabled
        const soundEnabled = timerDisplay.dataset.soundsEnabled === 'True';
        if (soundEnabled) {
            const audio = new Audio('/static/planner/sounds/alert.mp3');
            audio.play().catch(e => console.log('Audio play failed:', e));
        }

        // Save the completed session to MongoDB
        const completedSessionType = isWorkSession ? 'WORK' :
            (sessionsCompleted % longBreakInterval === 0 ? 'LONG_BREAK' : 'SHORT_BREAK');
        const completedDuration = isWorkSession ? workDuration :
            (sessionsCompleted % longBreakInterval === 0 ? longBreakDuration : shortBreakDuration);

        // Get active task ID if available
        const activeTaskId = document.getElementById('active-task-id')?.value;

        // Save session to MongoDB
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        fetch('/tasks/create-timer-session/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                session_type: completedSessionType,
                duration: completedDuration,
                task_id: activeTaskId || null
            })
        }).catch(error => {
            console.error('Error saving timer session:', error);
        });

        if (isWorkSession) {
            sessionsCompleted++;
            sessionCounter.textContent = sessionsCompleted;

            // Show notification
            if (Notification.permission === 'granted') {
                new Notification('Work session completed!', {
                    body: 'Time for a break.',
                    icon: '/static/planner/images/icon.png'
                });
            }

            // Start break session
            isWorkSession = false;
            sessionType = sessionsCompleted % longBreakInterval === 0 ? 'long break' : 'short break';
            sessionTypeDisplay.textContent = sessionType;
            startTimer(sessionsCompleted % longBreakInterval === 0 ? longBreakDuration : shortBreakDuration);
        } else {
            // Show notification
            if (Notification.permission === 'granted') {
                new Notification('Break time over!', {
                    body: 'Time to get back to work.',
                    icon: '/static/planner/images/icon.png'
                });
            }

            // Start work session
            isWorkSession = true;
            sessionType = 'work';
            sessionTypeDisplay.textContent = sessionType;
            startTimer(workDuration);
        }
    }

    function pauseTimer() {
        if (!isRunning) return;
        clearInterval(timer);
        isRunning = false;
    }

    function resetTimer() {
        clearInterval(timer);
        isRunning = false;
        isWorkSession = true;
        sessionType = 'work';
        sessionTypeDisplay.textContent = sessionType;
        timeLeft = workDuration;
        updateDisplay();
    }

    // Request notification permission
    if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
        Notification.requestPermission();
    }

    // Event listeners
    startBtn.addEventListener('click', () => startTimer(isWorkSession ? workDuration :
        (sessionsCompleted % longBreakInterval === 0 ? longBreakDuration : shortBreakDuration)));
    pauseBtn?.addEventListener('click', pauseTimer);
    resetBtn?.addEventListener('click', resetTimer);

    // Initialize
    sessionTypeDisplay.textContent = sessionType;
    updateDisplay();
});