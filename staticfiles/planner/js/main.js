document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(el => {
        el.addEventListener('mouseover', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute z-10 bg-gray-800 text-white text-xs rounded py-1 px-2';
            tooltip.textContent = this.dataset.tooltip;
            this.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.top = `${rect.height + 5}px`;
            tooltip.style.left = '50%';
            tooltip.style.transform = 'translateX(-50%)';
            
            this.addEventListener('mouseout', function() {
                tooltip.remove();
            });
        });
    });
    
    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.transition = 'opacity 0.5s ease-out';
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        }, 5000);
    });

    // Toggle dark mode based on user settings
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', function() {
            document.documentElement.classList.toggle('dark', this.checked);
        });
    }

    // Form handling enhancements
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="animate-spin">⏳</span> Processing...';
            }
        });
    });
});