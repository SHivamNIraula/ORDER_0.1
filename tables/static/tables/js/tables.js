document.addEventListener('DOMContentLoaded', function() {
    const selectButtons = document.querySelectorAll('.select-table-btn');
    
    selectButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const tableId = this.dataset.tableId;
            
            try {
                const response = await fetch(`/tables/lock/${tableId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    window.location.href = '/food/select/';
                } else {
                    alert(data.message || 'Failed to select table');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            }
        });
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}