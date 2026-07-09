// Web Worker for Pomodoro Timer
// This worker ensures the timer continues to run even when the tab is inactive

let timerId = null;
let startTime = 0;
let duration = 0;
let isRunning = false;

self.onmessage = function(e) {
    const command = e.data.command;
    
    switch (command) {
        case 'start':
            startTimer(e.data.duration);
            break;
        case 'pause':
            pauseTimer();
            break;
        case 'reset':
            resetTimer();
            break;
        case 'status':
            sendStatus();
            break;
    }
};

function startTimer(newDuration) {
    if (isRunning) {
        return;
    }
    
    if (newDuration !== undefined) {
        duration = newDuration;
    }
    
    isRunning = true;
    startTime = Date.now();
    
    // Clear any existing timer
    if (timerId) {
        clearInterval(timerId);
    }
    
    // Start a new timer that ticks every second
    timerId = setInterval(() => {
        if (isRunning) {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const remaining = Math.max(0, duration - elapsed);
            
            // Send the current time to the main thread
            self.postMessage({
                type: 'tick',
                timeLeft: remaining
            });
            
            // If the timer has completed, notify the main thread
            if (remaining <= 0) {
                clearInterval(timerId);
                isRunning = false;
                self.postMessage({
                    type: 'complete'
                });
            }
        }
    }, 1000);
    
    // Send confirmation that the timer has started
    self.postMessage({
        type: 'started',
        duration: duration
    });
}

function pauseTimer() {
    if (!isRunning) {
        return;
    }
    
    isRunning = false;
    
    if (timerId) {
        clearInterval(timerId);
    }
    
    // Calculate the remaining time
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    duration = Math.max(0, duration - elapsed);
    
    // Send confirmation that the timer has paused
    self.postMessage({
        type: 'paused',
        timeLeft: duration
    });
}

function resetTimer() {
    isRunning = false;
    
    if (timerId) {
        clearInterval(timerId);
    }
    
    // Send confirmation that the timer has reset
    self.postMessage({
        type: 'reset'
    });
}

function sendStatus() {
    let timeLeft = duration;
    
    if (isRunning) {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        timeLeft = Math.max(0, duration - elapsed);
    }
    
    self.postMessage({
        type: 'status',
        isRunning: isRunning,
        timeLeft: timeLeft
    });
}
