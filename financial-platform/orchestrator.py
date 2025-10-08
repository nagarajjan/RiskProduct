import os
import openai
import json
import pandas as pd
from rag_loader import RAGKnowledgeBase
from fastmcp import Client
from fastmcp.tools import Tool
from typing import Dict, Any, List
from config import RISK_MAPPING
from dotenv import load_dotenv

load_dotenv()

class FinancialOrchestrator:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.openai_client = openai.Client(api_key=self.openai_api_key)
        self.rag_kb = RAGKnowledgeBase(api_key=self.openai_api_key)
        self.mcp_client = Client("http://localhost:5001/mcp")

        self.all_products_data = self._load_product_data_from_file("product_details.json")
        self.all_customers_data = self._load_customer_data_from_file("customer_profiles.csv")
        self.config = self._load_config_from_file("config.json")

    def _load_product_data_from_file(self, file_path):
        """Loads product data directly from the JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error: {e}. Check product details file.")
            return []

    def _load_customer_data_from_file(self, file_path):
        """Loads customer data directly from the CSV file."""
        try:
            df = pd.read_csv(file_path)
            return df.to_dict('records')
        except FileNotFoundError as e:
            print(f"Error: {e}. Check customer profiles file.")
            return []
    
    def _load_config_from_file(self, file_path):
        """Loads configuration from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load config from '{file_path}'. Using default settings.")
            return {"dynamic_risk_enabled": False}

    def get_customer_profile(self, customer_id: str) -> Dict[str, Any] or None:
        """Retrieves a customer's profile by ID."""
        for customer in self.all_customers_data:
            if customer['customer_id'] == customer_id:
                return customer
        return None

    def load_data(self, files: List[str]):
        """Ingests sample data files into the RAG knowledge base."""
        self.rag_kb.build_knowledge_base(files)

    def filter_products(self, customer_risk_appetite: str, customer_country: str, buy_cross_border: bool = False) -> List[Dict[str, Any]]:
        """
        Filters products based on customer risk and regulatory approval, with an option for cross-border.
        """
        if not self.all_products_data:
            print("Product data not loaded. Returning empty list.")
            return []

        compatible_risk_levels = RISK_MAPPING.get(customer_risk_appetite, [])
        filtered_list = []

        print(f"\n--- Starting programmatic filtering for: ---")
        print(f"Customer Risk: {customer_risk_appetite} (compatible levels: {compatible_risk_levels})")
        print(f"Customer Country: {customer_country}")
        print(f"Cross-border purchases enabled: {buy_cross_border}")

        for product in self.all_products_data:
            product_risk = product.get('risk_level')
            product_regulatory = product.get('regulatory_status')

            # Rule 1: Check risk level compatibility
            risk_level_compatible = product_risk in compatible_risk_levels
            
            # Rule 2: Check regulatory status based on buy_cross_border flag
            regulatory_status_approved = False
            
            if buy_cross_border:
                if "Approved for all markets" in product_regulatory:
                    regulatory_status_approved = True
                elif "US" in product_regulatory or "EU" in product_regulatory:
                    regulatory_status_approved = True
            else:
                if "Approved for all markets" in product_regulatory:
                    regulatory_status_approved = True
                elif customer_country in product_regulatory:
                    regulatory_status_approved = True

            if risk_level_compatible and regulatory_status_approved:
                filtered_list.append(product)
        
        print("\n--- Filtering complete. ---")
        return filtered_list

    def get_detailed_recommendation(self, customer_profile: Dict[str, Any], product: Dict[str, Any]):
        """Generates a detailed value proposition for a selected product."""
        # Use RAG to confirm product-specific and regulatory context
        product_context = self.rag_kb.retrieve_context(f"Details for product {product['product_id']}.")
        regulatory_info = self.rag_kb.retrieve_context(f"Regulatory expectations for {customer_profile['country']}.")
        
        # Check the configuration file to see if dynamic risk is enabled
        risk_assessment_info = ""
        # Create a copy of the product object to safely modify the risk level
        current_product = product.copy()

        if self.config.get("dynamic_risk_enabled", False):
            # Dynamically construct the query for the latest risk article
            latest_article_query = f"latest risk update article for product {product['product_id']}"
            latest_article_context = self.rag_kb.retrieve_context(latest_article_query)

            if latest_article_context and "Knowledge base not yet populated" not in latest_article_context:
                try:
                    mcp_response = self.mcp_client.call(
                        Tool(name="assess_product_risk_from_evidence", description="Assess product risk."),
                        product_id=current_product['product_id'],
                        article_content=latest_article_context,
                        current_risk_level=current_product['risk_level']
                    )
                    if mcp_response and mcp_response.content:
                        new_risk = mcp_response.content.strip()
                        if new_risk != 'No Change' and new_risk != current_product['risk_level']:
                            current_product['risk_level'] = new_risk # Override the risk level
                            risk_assessment_info = f"**Dynamic Risk Assessment:** The risk level has been updated to **{new_risk}** based on the latest market analysis.\n"
                        else:
                            risk_assessment_info = f"**Dynamic Risk Assessment:** No change to the product's risk level based on the latest market analysis.\n"
                except Exception as e:
                    risk_assessment_info = f"**Dynamic Risk Assessment:** Failed to perform risk assessment via MCP. Error: {str(e)}.\n"
        
        mcp_output = f"{risk_assessment_info}\nAsync client call is simplified for this example."
        
        prompt = f"""
        Generate a detailed value proposition, including customized pricing, for the customer based on their profile and the selected product.
        
        **Customer Profile:**
        - Risk Appetite: {customer_profile['risk_appetite']}
        - Country: {customer_profile['country']}
        
        **Selected Product Details (from RAG):**
        Product ID: {current_product['product_id']}
        Name: {current_product['name']}
        Type: {current_product['type']}
        Risk Level: {current_product['risk_level']}
        Target Return: {current_product['target_return_range']}
        Management Fee: {current_product['management_fee']}
        Regulatory Status: {current_product['regulatory_status']}
        Description: {current_product['description']}
        
        **Real-time Context (from MCP):**
        {mcp_output}
        
        **Regulatory Context (from RAG):**
        {regulatory_info}
        
        The value proposition should clearly explain why the product is a good fit, based on the customer's risk appetite and investment horizon.
        Ensure the output is compliant with the regulatory context.
        """
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        if response.choices and response.choices.message:
            return response.choices.message.content
        return "Failed to get a detailed recommendation."

# Main application setup within Flask
class AppContainer:
    def __init__(self):
        self.orchestrator = FinancialOrchestrator()
        self.orchestrator.load_data([
            "customer_profiles.csv", 
            "product_details.json", 
            "Regulatory_Handbook_US.pdf", 
            "Product_Risk_Assessment_P001.pdf",
            "Product_Risk_Update_P001.pdf"
        ])

container = AppContainer()
