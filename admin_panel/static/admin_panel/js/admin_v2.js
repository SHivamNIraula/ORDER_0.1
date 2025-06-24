// admin_panel/static/admin_panel/js/admin_v2.js - FIXED EVENT DELEGATION
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
    console.log('Admin JS loaded - Event Delegation Fixed');
    
    // Check if user is authenticated
    const csrfToken = getCookie('csrftoken');
    console.log('CSRF Token found:', !!csrfToken);
    
    // Initialize WebSocket connection
    initializeWebSocket();
    
    // FIXED: Use event delegation for change status buttons
    setupEventDelegation();
    
    console.log('Event delegation set up for dynamic buttons');
});

// FIXED: Set up event delegation to handle both existing and dynamically added buttons
function setupEventDelegation() {
    // Use event delegation on the table body to catch all button clicks
    const tableBody = document.getElementById('orders-table-body');
    if (tableBody) {
        // Remove any existing listeners first (prevent duplicates)
        tableBody.removeEventListener('click', handleTableBodyClick);
        // Add the event listener
        tableBody.addEventListener('click', handleTableBodyClick);
        console.log('Event delegation attached to table body');
    } else {
        console.error('Orders table body not found for event delegation');
    }
}

// FIXED: Single event handler for all table body clicks
function handleTableBodyClick(e) {
    // Check if clicked element is a change status button
    if (e.target && e.target.classList.contains('change-status-btn')) {
        e.preventDefault();
        handleChangeStatusClick(e.target);
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
    
    // Prevent multiple clicks on the same button
    if (button.disabled) {
        console.log('Button already disabled, ignoring click');
        return;
    }
    
    if (confirm('Mark this order as paid?')) {
        try {
            // Disable button immediately to prevent double-clicks
            button.disabled = true;
            button.textContent = 'Processing...';
            
            // Get fresh CSRF token each time
            const csrfToken = getCookie('csrftoken');
            console.log('CSRF Token:', csrfToken ? 'Found' : 'NOT FOUND');
            
            if (!csrfToken) {
                alert('Security error: Please refresh the page and try again.');
                // Re-enable button
                button.disabled = false;
                button.textContent = 'Change';
                return;
            }
            
            const url = `/admin-panel/change-order-status/${orderId}/`;
            console.log('Request URL:', url);
            
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
            
            // Get response text first
            const responseText = await response.text();
            console.log('Raw response (first 200 chars):', responseText.substring(0, 200));
            
            // Check if response is HTML (error page)
            if (responseText.trim().startsWith('<!DOCTYPE') || responseText.trim().startsWith('<html')) {
                console.error('Received HTML instead of JSON');
                
                if (responseText.includes('login') || responseText.includes('Login')) {
                    alert('Session expired. Please refresh the page and login again.');
                } else if (responseText.includes('403') || responseText.includes('Forbidden')) {
                    alert('Permission denied. Please refresh the page and try again.');
                } else {
                    alert('Server error occurred. Please refresh the page and try again.');
                }
                
                // Re-enable button
                button.disabled = false;
                button.textContent = 'Change';
                return;
            }
            
            // Try to parse as JSON
            let data;
            try {
                data = JSON.parse(responseText);
                console.log('Parsed JSON:', data);
            } catch (jsonError) {
                console.error('JSON parse error:', jsonError);
                alert('Invalid response from server. Please refresh the page and try again.');
                // Re-enable button
                button.disabled = false;
                button.textContent = 'Change';
                return;
            }
            
            if (data.success) {
                console.log('Order status updated successfully');
                
                // Update button appearance permanently
                button.textContent = 'Paid';
                button.classList.remove('btn-primary');
                button.classList.add('btn-success');
                // Keep button disabled
                
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
                // Re-enable button on error
                button.disabled = false;
                button.textContent = 'Change';
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
            
            // Re-enable button on error
            button.disabled = false;
            button.textContent = 'Change';
        }
    } else {
        // User cancelled, make sure button is enabled
        button.disabled = false;
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
                        // Don't reload the page, let the UI update handle it
                        console.log('Payment successful, UI updated via WebSocket');
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
    
    // Create new row - Event delegation will automatically handle clicks
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
    
    // Update pending count
    const pendingCountElement = document.getElementById('pending-count');
    if (pendingCountElement) {
        const currentCount = parseInt(pendingCountElement.textContent) || 0;
        pendingCountElement.textContent = currentCount + 1;
    }
    
    console.log('New order row added successfully (event delegation will handle clicks automatically)');
}