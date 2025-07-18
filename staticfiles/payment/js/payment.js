document.addEventListener('DOMContentLoaded', function() {
    const qrButton = document.getElementById('qr-payment');
    const counterButton = document.getElementById('counter-payment');
    const qrContainer = document.getElementById('qr-code-container');
    const qrImage = document.getElementById('qr-code-image');
    const waitingMessage = document.getElementById('waiting-message');
    
    // WebSocket connection - connect to order-specific channel
    const ws = new WebSocket(`ws://${window.location.host}/ws/payment/${orderId}/`);
    
    ws.onopen = function(e) {
        console.log('Payment WebSocket connected');
    };
    
    ws.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log('Payment WebSocket message received:', data);
        
        // Check if payment was completed by admin
        if (data.type === 'payment_complete') {
            // Redirect to success page
            window.location.href = `/payment/success/${orderId}/`;
        }
    };
    
    ws.onclose = function(e) {
        console.error('Payment WebSocket closed unexpectedly');
    };
    
    ws.onerror = function(e) {
        console.error('Payment WebSocket error:', e);
    };
    
    qrButton.addEventListener('click', async function() {
        try {
            const response = await fetch(`/payment/generate-qr/${orderId}/`);
            const data = await response.json();
            
            qrImage.src = data.qr_code;
            qrContainer.style.display = 'block';
            
            // Simulate payment success after 5 seconds (for demo)
            setTimeout(() => {
                ws.send(JSON.stringify({
                    type: 'payment_success',
                    order_id: orderId
                }));
                
                window.location.href = `/payment/success/${orderId}/`;
            }, 5000);
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to generate QR code');
        }
    });
    
    counterButton.addEventListener('click', function() {
        console.log('Counter payment button clicked');
        
        // Send notification to admin
        ws.send(JSON.stringify({
            type: 'counter_payment',
            order_id: orderId,
            table_number: tableNumber
        }));
        
        // Show waiting message
        waitingMessage.style.display = 'block';
        
        // Hide payment buttons
        document.querySelector('.payment-options').style.display = 'none';
        
        console.log('Counter payment notification sent to admin');
    });
});