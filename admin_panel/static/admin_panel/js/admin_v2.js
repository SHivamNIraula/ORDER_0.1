// admin_panel/static/admin_panel/js/admin.js - Fixed Dynamic Buttons
// second time changing the code to fix dynamic buttons issue
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

// Global variables
let adminWebSocket = null;
let isWebSocketConnected = false;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin JS loaded - Dynamic Buttons Fixed');
    
    // Check if user is authenticated
    const csrfToken = getCookie('csrftoken');
    console.log('CSRF Token found:', !!csrfToken);
    
    // Initialize WebSocket connection
    initializeWebSocket();
    
    // Use event delegation for change status buttons (works for dynamic content)
    setupEventDelegation();
    
    console.log('Event delegation set up for dynamic buttons');
});

// Set up event delegation to handle both existing and dynamically added buttons
function setupEventDelegation() {
    // Use event delegation on the table body to catch all button clicks
    const tableBody = document.getElementById('orders-table-body');
    if (tableBody) {
        tableBody.addEventListener('click', function(e) {
            // Check if clicked element is a change status button
            if (e.target && e.target.classList.contains('change-status-btn')) {
                e.preventDefault();
                handleChangeStatusClick(e.target);
            }
        });
        console.log('Event delegation attached to table body');
    } else {
        console.error('Orders table body not found for event delegation');
    }
}

async function handleChangeStatusClick(button) {
    console.log('=== CHANGE STATUS CLICK (Event Delegation) ===');
    
    const orderId = button.dataset.orderId;
    console.log('Order ID:', orderId);
    
    if (!orderId) {
        console.error('No order ID found');
        alert('Error: No order ID found');
        return;
    }
    
    if (confirm('Mark this order as paid?')) {
        try {
            // Get fresh CSRF token each time
            const csrfToken = getCookie('csrftoken');
            console.log('CSRF Token:', csrfToken ? 'Found' : 'NOT FOUND');
            
            if (!csrfToken) {
                alert('Security error: Please refresh the page and try again.');
                return;
            }
            
            const url = `/admin-panel/change-order-status/${orderId}/`;
            console.log('Request URL:', url);
            console.log('Full URL:', window.location.origin + url);
            
            console.log('Sending request with headers:', {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            });
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                },
                body: JSON.stringify({})
            });
            
            console.log('Response status:', response.status);
            console.log('Response content type:', response.headers.get('content-type'));
            
            // Get response text first
            const responseText = await response.text();
            console.log('Raw response (first 200 chars):', responseText.substring(0, 200));
            
            // Check if response is HTML (error page)
            if (responseText.trim().startsWith('<!DOCTYPE') || responseText.trim().startsWith('<html')) {
                console.error('Received HTML instead of JSON');
                console.log('Full HTML response:', responseText);
                
                if (responseText.includes('login') || responseText.includes('Login')) {
                    alert('Session expired. Please refresh the page and login again.');
                } else if (responseText.includes('403') || responseText.includes('Forbidden')) {
                    alert('Permission denied. Please refresh the page and try again.');
                } else {
                    alert('Server error occurred. Please refresh the page and try again.');
                }
                return;
            }
            
            // Try to parse as JSON
            let data;
            try {
                data = JSON.parse(responseText);
                console.log('Parsed JSON:', data);
            } catch (jsonError) {
                console.error('JSON parse error:', jsonError);
                console.log('Response was not valid JSON:', responseText);
                alert('Invalid response from server. Please refresh the page and try again.');
                return;
            }
            
            if (data.success) {
                console.log('Order status updated successfully');
                
                // Update button appearance
                button.textContent = 'Updated';
                button.disabled = true;
                button.classList.remove('btn-primary');
                button.classList.add('btn-success');
                
                showNotification('Order status updated successfully', 'success');
                
                // Update the status badge
                const row = button.closest('tr');
                const statusBadge = row.querySelector('.badge');
                if (statusBadge) {
                    statusBadge.classList.remove('bg-warning');
                    statusBadge.classList.add('bg-success');
                    statusBadge.textContent = 'Paid';
                }
                
                // Update pending count
                const pendingCountElement = document.getElementById('pending-count');
                if (pendingCountElement) {
                    const currentCount = parseInt(pendingCountElement.textContent) || 0;
                    if (currentCount > 0) {
                        pendingCountElement.textContent = currentCount - 1;
                    }
                }
                
            } else {
                console.error('Server returned error:', data.error);
                alert('Failed: ' + (data.error || 'Unknown error'));
            }
            
        } catch (error) {
            console.error('=== FETCH ERROR ===');
            console.error('Error type:', error.constructor.name);
            console.error('Error message:', error.message);
            console.error('Full error:', error);
            
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                alert('Network error: Cannot connect to server. Check your network connection.');
            } else {
                alert('Error: ' + error.message);
            }
        }
    }
    
    console.log('=== END CHANGE STATUS ===');
}

function initializeWebSocket() {
    try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/payment/`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        adminWebSocket = new WebSocket(wsUrl);
        
        adminWebSocket.onopen = function(e) {
            console.log('WebSocket connected successfully');
            isWebSocketConnected = true;
            updateWebSocketStatus('Connected', 'success');
        };
        
        adminWebSocket.onmessage = function(e) {
            console.log('Received WebSocket message:', e.data);
            
            try {
                const data = JSON.parse(e.data);
                console.log('Parsed data:', data);
                
                if (data.type === 'new_order') {
                    console.log('Processing new order:', data.order_data);
                    addNewOrderToTable(data.order_data);
                    showNotification(data.message, 'info');
                } else {
                    showNotification(data.message, data.status);
                    
                    if (data.status === 'success') {
                        setTimeout(() => {
                            location.reload();
                        }, 2000);
                    }
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        adminWebSocket.onerror = function(e) {
            console.error('WebSocket error:', e);
            isWebSocketConnected = false;
            updateWebSocketStatus('Error', 'danger');
        };
        
        adminWebSocket.onclose = function(e) {
            console.log('WebSocket closed. Code:', e.code, 'Reason:', e.reason);
            isWebSocketConnected = false;
            updateWebSocketStatus('Disconnected', 'warning');
            
            if (e.code !== 1000) {
                setTimeout(() => {
                    console.log('Attempting to reconnect...');
                    initializeWebSocket();
                }, 3000);
            }
        };
        
    } catch (error) {
        console.error('WebSocket initialization failed:', error);
        updateWebSocketStatus('Failed', 'danger');
    }
}

function updateWebSocketStatus(status, type) {
    const statusElement = document.getElementById('websocket-status');
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = `badge bg-${type}`;
    }
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
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function addNewOrderToTable(orderData) {
    console.log('Adding new order to table:', orderData);
    
    const ordersTableBody = document.getElementById('orders-table-body');
    if (!ordersTableBody) {
        console.error('Orders table body not found');
        return;
    }
    
    // Create new row - NO NEED to manually attach event listeners
    // Event delegation will handle the click automatically
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
        <td>#${orderData.id}</td>
        <td>Table ${orderData.table_number}</td>
        <td>${orderData.username}</td>
        <td>$${parseFloat(orderData.total_amount).toFixed(2)}</td>
        <td>
            <span class="badge bg-warning">Pending</span>
        </td>
        <td>${orderData.created_at}</td>
        <td>
            <button class="btn btn-sm btn-primary change-status-btn" data-order-id="${orderData.id}">
                Change
            </button>
        </td>
    `;
    
    // Add to top of table
    ordersTableBody.insertBefore(newRow, ordersTableBody.firstChild);
    
    // Remove last row if table gets too long
    const allRows = ordersTableBody.querySelectorAll('tr');
    if (allRows.length > 10) {
        allRows[allRows.length - 1].remove();
    }
    
    // Highlight new row briefly
    newRow.style.backgroundColor = '#d4edda';
    setTimeout(() => {
        newRow.style.backgroundColor = '';
    }, 3000);
    
    console.log('New order row added successfully (event delegation will handle clicks)');
}