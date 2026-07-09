document.addEventListener('DOMContentLoaded', function() {
    // Initialize drag and drop
    const taskItems = document.querySelectorAll('.task-item');
    const quadrants = document.querySelectorAll('[id^="quadrant-"]');
    
    // Add event listeners to all task items
    taskItems.forEach(item => {
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);
        item.addEventListener('dblclick', handleEditClick);
    });

    // Add event listeners to all quadrants
    quadrants.forEach(quadrant => {
        quadrant.addEventListener('dragover', handleDragOver);
        quadrant.addEventListener('drop', handleDrop);
        quadrant.addEventListener('dragenter', handleDragEnter);
        quadrant.addEventListener('dragleave', handleDragLeave);
    });

    // Modal functionality
    const editModal = document.getElementById('edit-modal');
    const cancelEdit = document.getElementById('cancel-edit');
    
    if (cancelEdit) {
        cancelEdit.addEventListener('click', () => {
            editModal.classList.add('hidden');
        });
    }

    if (document.getElementById('edit-task-form')) {
        document.getElementById('edit-task-form').addEventListener('submit', handleTaskUpdate);
    }

    function handleDragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.dataset.taskId);
        e.target.classList.add('opacity-50');
    }
    
    function handleDragEnd(e) {
        e.target.classList.remove('opacity-50');
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    function handleDragEnter(e) {
        e.preventDefault();
        e.currentTarget.classList.add('bg-blue-50');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('bg-blue-50');
    }

    function handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('bg-blue-50');
        
        const taskId = e.dataTransfer.getData('text/plain');
        const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
        const newQuadrant = e.currentTarget.dataset.quadrant;
        
        if (!taskElement || !newQuadrant) return;
        
        // Update UI immediately
        const tasksContainer = e.currentTarget.querySelector('.quadrant-tasks');
        tasksContainer.appendChild(taskElement);
        taskElement.classList.remove('opacity-50');
        
        // Update the empty state message if needed
        updateEmptyStateMessages();
        
        // Send update to server
        updateTaskQuadrant(taskId, newQuadrant);
    }

    function handleEditClick(e) {
        const taskId = this.dataset.taskId;
        const taskTitle = this.querySelector('h3').textContent;
        const dueDateElement = this.querySelector('.task-due-date');
        const priorityElement = this.querySelector('.task-priority');
        
        let dueDate = '';
        if (dueDateElement) {
            dueDate = dueDateElement.textContent.trim();
        }
        
        let priority = '';
        if (priorityElement) {
            priority = priorityElement.textContent.trim();
        }
        
        // Populate modal
        document.getElementById('edit-task-id').value = taskId;
        document.getElementById('edit-task-title').value = taskTitle;
        
        // Parse and format due date
        if (dueDate && dueDate !== 'No deadline') {
            try {
                const dateObj = new Date(dueDate);
                if (!isNaN(dateObj.getTime())) {
                    const formattedDate = dateObj.toISOString().split('T')[0];
                    document.getElementById('edit-task-due-date').value = formattedDate;
                }
            } catch (e) {
                console.error('Error parsing date:', e);
                document.getElementById('edit-task-due-date').value = '';
            }
        } else {
            document.getElementById('edit-task-due-date').value = '';
        }
        
        // Set priority
        const prioritySelect = document.getElementById('edit-task-priority');
        if (priority.includes('High')) {
            prioritySelect.value = 'H';
        } else if (priority.includes('Medium')) {
            prioritySelect.value = 'M';
        } else {
            prioritySelect.value = 'L';
        }
        
        // Show modal
        editModal.classList.remove('hidden');
    }

    function handleTaskUpdate(e) {
        e.preventDefault();
        const taskId = document.getElementById('edit-task-id').value;
        const formData = new FormData(e.target);
        
        fetch(`/tasks/${taskId}/edit/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                response.json().then(data => {
                    alert(data.error || 'Error updating task');
                }).catch(() => {
                    alert('Error updating task');
                });
            }
        }).catch(error => {
            console.error('Error:', error);
            alert('Error updating task');
        });
    }

    function updateTaskQuadrant(taskId, newQuadrant) {
        fetch('/tasks/update-quadrant/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                task_id: taskId,
                quadrant: newQuadrant
            })
        }).then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to update quadrant');
                });
            }
            // Update the quadrant counts without page reload
            return response.json();
        }).then(data => {
            if (data && data.quadrant_counts) {
                updateQuadrantCounts(data.quadrant_counts);
            }
        }).catch(error => {
            console.error('Error:', error);
            alert(error.message || 'Error updating task quadrant');
        });
    }
    
    function updateQuadrantCounts(counts) {
        if (!counts) return;
        
        const countElements = document.querySelectorAll('.flex.justify-center.mb-6.space-x-4 span');
        
        if (countElements.length >= 4) {
            countElements[0].textContent = `Q1: ${counts.q1 || 0}`;
            countElements[1].textContent = `Q2: ${counts.q2 || 0}`;
            countElements[2].textContent = `Q3: ${counts.q3 || 0}`;
            countElements[3].textContent = `Q4: ${counts.q4 || 0}`;
        }
    }
    
    function updateEmptyStateMessages() {
        // Check each quadrant and add/remove empty state messages as needed
        quadrants.forEach(quadrant => {
            const tasksContainer = quadrant.querySelector('.quadrant-tasks');
            const taskItems = tasksContainer.querySelectorAll('.task-item');
            let emptyMessage = tasksContainer.querySelector('p.text-gray-500');
            
            if (taskItems.length === 0 && !emptyMessage) {
                // Add empty message if there are no tasks
                emptyMessage = document.createElement('p');
                emptyMessage.className = 'text-gray-500';
                emptyMessage.textContent = 'No tasks in this quadrant';
                tasksContainer.appendChild(emptyMessage);
            } else if (taskItems.length > 0 && emptyMessage) {
                // Remove empty message if there are tasks
                emptyMessage.remove();
            }
        });
    }
});