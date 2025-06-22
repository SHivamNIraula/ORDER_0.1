// admin_panel/static/admin_panel/js/admin.js - Complete Version

// CSRF Token function
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

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin JS loaded');
    
    // WebSocket connection for payment notifications
    let ws = null;
    try {
        ws = new WebSocket('ws://' + window.location.host + '/ws/payment/');
        
        ws.onopen = function(e) {
            console.log('WebSocket connected');
        };
        
        ws.onmessage = function(e) {
            const data = JSON.parse(e.data);
            showNotification(data.message, data.status);
            
            // Reload page if payment status changed
            if (data.status === 'success') {
                setTimeout(() => {
                    location.reload();
                }, 2000);
            }
        };
        
        ws.onerror = function(e) {
            console.error('WebSocket error:', e);
        };
        
        ws.onclose = function(e) {
            console.log('WebSocket closed');
        };
    } catch (error) {
        console.error('WebSocket connection failed:', error);
    }
    
    function showNotification(message, status) {
        const notificationsContainer = document.getElementById('notifications');
        if (!notificationsContainer) {
            console.error('Notifications container not found');
            return;
        }
        
        const notification = document.createElement('div');
        notification.className = `notification ${status}`;
        notification.textContent = message;
        
        notificationsContainer.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    // Handle change status buttons
    const changeStatusButtons = document.querySelectorAll('.change-status-btn');
    console.log('Found change status buttons:', changeStatusButtons.length);
    
    changeStatusButtons.forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            console.log('Change button clicked');
            
            const orderId = this.dataset.orderId;
            console.log('Order ID:', orderId);
            
            if (confirm('Mark this order as paid?')) {
                try {
                    const response = await fetch(`/admin-panel/change-order-status/${orderId}/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({})
                    });
                    
                    console.log('Response status:', response.status);
                    
                    const data = await response.json();
                    console.log('Response data:', data);
                    
                    if (data.success) {
                        // Change button appearance immediately
                        this.textContent = 'Updated';
                        this.disabled = true;
                        this.classList.remove('btn-primary');
                        this.classList.add('btn-success');
                        
                        // Show success notification
                        showNotification('Order status updated successfully', 'success');
                        
                        // Update the status badge
                        const statusBadge = this.closest('tr').querySelector('.badge');
                        if (statusBadge) {
                            statusBadge.classList.remove('bg-warning');
                            statusBadge.classList.add('bg-success');
                            statusBadge.textContent = 'Paid';
                        }
                        
                        // Reload page after delay
                        setTimeout(() => {
                            location.reload();
                        }, 1500);
                    } else {
                        alert('Failed to update order status: ' + (data.error || 'Unknown error'));
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('An error occurred: ' + error.message);
                }
            }
        });
    });
});