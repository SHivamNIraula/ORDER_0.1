document.addEventListener('DOMContentLoaded', function() {
    let cartCount = 0;
    
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    const cartCountElement = document.getElementById('cart-count');
    
    addToCartButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const foodId = this.dataset.foodId;
            const foodName = this.dataset.foodName;
            
            try {
                const response = await fetch('/food/add-to-cart/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        food_id: foodId,
                        quantity: 1
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    cartCountElement.textContent = data.cart_count;
                    
                    // Show success message
                    this.textContent = 'Added!';
                    this.classList.add('btn-success');
                    setTimeout(() => {
                        this.textContent = 'Add to Cart';
                        this.classList.remove('btn-success');
                    }, 1000);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to add item to cart');
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
