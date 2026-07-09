document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: '/calendar/events/',
        eventDisplay: 'block',
        editable: true,
        selectable: true,
        dateClick: function(info) {
            window.location.href = `/tasks/add/?due_date=${info.dateStr}`;
        },
        eventClick: function(info) {
            window.location.href = `/tasks/${info.event.id}/edit/`;
        },
        eventDidMount: function(info) {
            info.el.style.borderRadius = '4px';
            info.el.style.border = 'none';
        }
    });

    calendar.render();
});