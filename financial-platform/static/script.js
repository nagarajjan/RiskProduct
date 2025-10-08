const API_BASE_URL = 'http://127.0.0.1:5000/api';

document.addEventListener('DOMContentLoaded', async () => {
    await fetchCustomers();
});

async function fetchCustomers() {
    const response = await fetch(`${API_BASE_URL}/customers`);
    const data = await response.json();
    const customerSelect = document.getElementById('customer_id');

    if (data.customers && data.customers.length > 0) {
        customerSelect.innerHTML = data.customers.map(customer =>
            `<option value="${customer.customer_id}">${customer.customer_id} (${customer.risk_appetite}, ${customer.country})</option>`
        ).join('');
    } else {
        customerSelect.innerHTML = '<option value="">No customers available</option>';
    }
}

document.getElementById('profile-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const customerId = document.getElementById('customer_id').value;
    const crossBorder = document.getElementById('cross_border').checked;

    const response = await fetch(`${API_BASE_URL}/filter-products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: customerId, buy_cross_border: crossBorder })
    });

    const data = await response.json();
    displayProducts(data.products, customerId);
});

function displayProducts(products, customerId) {
    const productList = document.getElementById('product-list');
    productList.innerHTML = '';

    if (products && products.length > 0) {
        products.forEach(product => {
            const card = document.createElement('div');
            card.className = 'product-card';

            let countryInfo = product.regulatory_status.replace(/Approved for /g, '').replace(/ markets/g, '');
            let riskClass = product.risk_level.replace(/\s/g, '');

            card.innerHTML = `
                <h3>${product.name}</h3>
                <p><strong>Type:</strong> ${product.type}</p>
                <p><strong class="risk-tag risk-${riskClass}">Risk Level: ${product.risk_level}</strong></p>
                <p><strong>Approved In:</strong> ${countryInfo}</p>
            `;
            card.addEventListener('click', () => showProductDetails(product.product_id, customerId));
            productList.appendChild(card);
        });
    } else {
        productList.innerHTML = '<p>No products found matching your criteria.</p>';
    }
}

async function showProductDetails(productId, customerId) {
    const detailsContainer = document.getElementById('product-details');
    const detailsContent = document.getElementById('details-content');
    detailsContent.textContent = 'Loading...';
    detailsContainer.style.display = 'block';

    const response = await fetch(`${API_BASE_URL}/product-details`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customer_id: customerId, product_id: productId })
    });

    const data = await response.json();
    detailsContent.textContent = data.details;
}
