from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from orchestrator import container

# Tell Flask where to find the front-end files
app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """Serve the index.html page."""
    return render_template('index.html')

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Endpoint to get a list of all customers."""
    return jsonify({"customers": container.orchestrator.all_customers_data})

@app.route('/api/filter-products', methods=['POST'])
def filter_products():
    data = request.json
    customer_id = data.get('customer_id')
    buy_cross_border = data.get('buy_cross_border', False)

    if not customer_id:
        return jsonify({"error": "Missing customer_id"}), 400

    customer_profile = container.orchestrator.get_customer_profile(customer_id)
    if not customer_profile:
        return jsonify({"error": f"Customer with ID {customer_id} not found"}), 404

    filtered_list = container.orchestrator.filter_products(
        customer_profile['risk_appetite'],
        customer_profile['country'],
        buy_cross_border
    )
    return jsonify({"products": filtered_list})

@app.route('/api/product-details', methods=['POST'])
def product_details():
    data = request.json
    customer_id = data.get('customer_id')
    product_id = data.get('product_id')

    if not customer_id or not product_id:
        return jsonify({"error": "Missing customer_id or product_id"}), 400
    
    customer_profile = container.orchestrator.get_customer_profile(customer_id)
    if not customer_profile:
        return jsonify({"error": f"Customer with ID {customer_id} not found"}), 404

    product = next((p for p in container.orchestrator.all_products_data if p['product_id'] == product_id), None)
    if not product:
        return jsonify({"error": f"Product with ID {product_id} not found"}), 404

    details = container.orchestrator.get_detailed_recommendation(customer_profile, product)
    return jsonify({"details": details})


if __name__ == '__main__':
    # Flask app will run on port 5000
    app.run(port=5000, debug=True)
