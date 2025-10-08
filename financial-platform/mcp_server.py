from flask import Flask, jsonify, request
from mcp.server.fastmcp import FastMCP  # Import FastMCP instead of Server

# Instantiate the FastMCP class with the required 'name' argument
mcp_server = FastMCP(name="financial-product-server")

app = Flask(__name__)

# Define a tool to get real-time stock prices
@mcp_server.tool(name="get_stock_price", description="Fetches the current price of a given stock ticker.")
def get_stock_price(ticker: str) -> str:
    """Simulates a call to a real-time market data API."""
    if ticker.upper() == "AAPL":
        return "The current price of AAPL is $205.50."
    elif ticker.upper() == "MSFT":
        return "The current price of MSFT is $420.10."
    else:
        return "Stock price not found."

# Define a tool to calculate risk score
@mcp_server.tool(name="calculate_risk_score", description="Calculates the risk score for a customer based on their profile.")
def calculate_risk_score(customer_id: str) -> str:
    """Retrieves customer-specific risk information."""
    if customer_id == "C001":
        return "The calculated risk score for C001 is 45 (Moderate)."
    else:
        return "Risk score not available for this customer."

@app.route("/mcp", methods=["POST"])
def handle_mcp_request():
    request_data = request.json
    response_data = mcp_server.dispatch(request_data)
    return jsonify(response_data)

if __name__ == "__main__":
    app.run(port=5001)

