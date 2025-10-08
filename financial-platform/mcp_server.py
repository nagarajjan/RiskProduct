from flask import Flask, jsonify, request
from mcp.server.fastmcp import FastMCP
import openai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
mcp_server = FastMCP(name="financial-product-server")

openai_client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

@mcp_server.tool(name="get_stock_price", description="Fetches the current price of a given stock ticker.")
def get_stock_price(ticker: str) -> str:
    if ticker.upper() == "AAPL":
        return "The current price of AAPL is $205.50."
    elif ticker.upper() == "MSFT":
        return "The current price of MSFT is $420.10."
    else:
        return "Stock price not found."

@mcp_server.tool(name="calculate_risk_score", description="Calculates the risk score for a customer based on their profile.")
def calculate_risk_score(customer_id: str) -> str:
    if customer_id == "C001":
        return "The calculated risk score for C001 is 45 (Moderate)."
    else:
        return "Risk score not available for this customer."

@mcp_server.tool(name="assess_product_risk_from_evidence", description="Assesses a product's risk based on an external document and LLM analysis.")
def assess_product_risk_from_evidence(product_id: str, article_content: str, current_risk_level: str) -> str:
    prompt = f"""
    You are a financial risk analyst. Your task is to evaluate a product's risk level based on a new article.

    Product ID: {product_id}
    Current Risk Level (Initial): {current_risk_level}
    
    Article Content (New Evidence):
    {article_content}
    
    Rules for Risk Assessment:
    - If the article suggests increased volatility, geopolitical tension, or reclassification concerns for a 'High' risk product, the new risk level should be 'Very High'.
    - If the article suggests a clear decrease in risk factors, the new risk level could be 'Medium'.
    - If the article does not provide sufficient evidence to change the risk, the new risk level is 'No Change'.
    - Your output MUST be one of the following exact strings: 'Very High', 'High', 'Medium', 'Low', or 'No Change'.
    
    Based on the article, what is the new risk level?
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        if response.choices and response.choices[0].message:
            return response.choices[0].message.content.strip()
        return "Error: Empty or malformed response from LLM."
    except Exception as e:
        return f"Error assessing risk: {str(e)}"

@app.route("/mcp", methods=["POST"])
def handle_mcp_request():
    request_data = request.json
    response_data = mcp_server.dispatch(request_data)
    return jsonify(response_data)

if __name__ == "__main__":
    app.run(port=5001)
