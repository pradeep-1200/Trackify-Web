document.addEventListener('DOMContentLoaded', function() {
    const dataContainer = document.getElementById('analytics-data');
    if (!dataContainer) return;

    // Parse the data safely
    function parseData(data) {
        try {
            return JSON.parse(data);
        } catch (e) {
            console.error('Error parsing data:', e);
            return [];
        }
    }

    const dailyData = parseData(dataContainer.dataset.daily || '[]');
    const categoryData = parseData(dataContainer.dataset.category || '[]');
    const productivityData = parseData(dataContainer.dataset.productivity || '[]');

    // Daily Study Time Chart
    const dailyCtx = document.getElementById('dailyChart');
    if (dailyCtx) {
        new Chart(dailyCtx, {
            type: 'line',
            data: {
                labels: dailyData.map(item => item.day ? new Date(item.day).toLocaleDateString() : ''),
                datasets: [{
                    label: 'Minutes Studied',
                    data: dailyData.map(item => item.total_duration || 0),
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Minutes'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });
    }

    // Category Distribution Chart
    const categoryCtx = document.getElementById('categoryChart');
    if (categoryCtx) {
        new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: categoryData.map(item => item.task__category || 'Uncategorized'),
                datasets: [{
                    data: categoryData.map(item => item.total_duration || 0),
                    backgroundColor: [
                        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.raw} minutes`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Productivity Chart
    const productivityCtx = document.getElementById('productivityChart');
    if (productivityCtx) {
        const labels = ['Very Low', 'Low', 'Medium', 'High', 'Very High'];
        
        new Chart(productivityCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Number of Sessions',
                    data: productivityData.map(item => item.count || 0),
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                }, {
                    label: 'Avg Duration (min)',
                    data: productivityData.map(item => item.avg_duration || 0),
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 1,
                    type: 'line',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Sessions'
                        }
                    },
                    y1: {
                        position: 'right',
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Avg Duration (min)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Productivity Score'
                        }
                    }
                }
            }
        });
    }
});