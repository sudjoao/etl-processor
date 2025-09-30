"""
AI-powered dimension classification service using OpenRouter
"""
import os
import json
import requests
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class DimensionClassification:
    """Result of AI dimension classification"""
    column_name: str
    dimension_type: str
    dimensional_role: str
    confidence: float
    reasoning: str

class AIDimensionClassifier:
    """AI-powered dimension classifier using OpenRouter"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.model = os.getenv('AI_MODEL', 'anthropic/claude-3.5-sonnet')
        self.enabled = os.getenv('AI_CLASSIFICATION_ENABLED', 'true').lower() == 'true'
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        logger.info(f"AI Classification Enabled: {self.enabled}")
        logger.info(f"AI Model: {self.model}")
        logger.info(f"API Key configured: {'Yes' if self.api_key else 'No'}")
        if self.api_key:
            logger.info(f"API Key (first 10 chars): {self.api_key[:10]}...")

        if not self.api_key and self.enabled:
            logger.warning("OPENROUTER_API_KEY not found. AI classification disabled.")
            logger.debug(f"Environment OPENROUTER_API_KEY value: {os.getenv('OPENROUTER_API_KEY')}")
            self.enabled = False
    
    def classify_table_dimensions(self, table_name: str, columns: List[Dict[str, Any]]) -> List[DimensionClassification]:
        """
        Classify table columns into dimensional roles using AI

        Args:
            table_name: Name of the table
            columns: List of column information

        Returns:
            List of dimension classifications
        """
        logger.info(f"🔍 [AI CLASSIFIER] Starting classification for table: {table_name}")
        logger.info(f"🔍 [AI CLASSIFIER] Number of columns to classify: {len(columns)}")
        logger.info(f"🔍 [AI CLASSIFIER] AI enabled: {self.enabled}")

        if not self.enabled:
            logger.warning("⚠️ [AI CLASSIFIER] AI disabled, using fallback classification")
            return self._fallback_classification(columns)

        try:
            logger.info("🤖 [AI CLASSIFIER] AI enabled, starting AI classification process...")

            # Prepare the prompt
            logger.info("📝 [AI CLASSIFIER] Creating classification prompt...")
            prompt = self._create_classification_prompt(table_name, columns)
            logger.info(f"📝 [AI CLASSIFIER] Prompt created, length: {len(prompt)} characters")

            # Call OpenRouter API
            logger.info("🌐 [AI CLASSIFIER] Calling OpenRouter API...")
            response = self._call_openrouter_api(prompt)
            logger.info("✅ [AI CLASSIFIER] API call successful")

            # Parse the response
            logger.info("🔄 [AI CLASSIFIER] Parsing AI response...")
            classifications = self._parse_ai_response(response, columns)
            logger.info(f"✅ [AI CLASSIFIER] Successfully classified {len(classifications)} columns using AI")

            return classifications

        except Exception as e:
            logger.error(f"❌ [AI CLASSIFIER] AI classification failed: {str(e)}. Using fallback.")
            import traceback
            logger.error(f"🔍 [AI CLASSIFIER] Full error traceback:")
            logger.error(traceback.format_exc())
            return self._fallback_classification(columns)
    
    def _create_classification_prompt(self, table_name: str, columns: List[Dict[str, Any]]) -> str:
        """Create a detailed prompt for AI classification"""
        
        columns_info = []
        for col in columns:
            columns_info.append({
                "name": col["name"],
                "data_type": col["data_type"],
                "sample_values": col.get("sample_values", [])
            })
        
        prompt = f"""
You are an expert data warehouse architect. Analyze the following table and classify each column for dimensional modeling.

Table: {table_name}
Columns: {json.dumps(columns_info, indent=2)}
For each column, determine:
1. **dimensional_role**: One of:
    - "fact_measure": Numeric values that can be aggregated (sales, quantities, amounts)
    - "dimension_key": Identifiers that reference dimension tables
    - "dimension_attribute": Descriptive attributes for dimensions
    - "time_dimension": Date/time fields for time dimensions
    - "unknown": Cannot determine role

2. **dimension_type**: **Define the name of the logical dimension grouping that the column belongs to. This name should be specific to the dataset's context** (e.g., 'Customer', 'Product', 'Location', 'Visit_Type', 'Employee'). **The list below is only an example, and you must create a fitting name for the data.**
    - Example Logical Groupings: 'customer', 'product', 'location', 'time', 'transaction', 'activity', 'vehicle', 'person', 'visit', 'other'

3. **confidence**: Float between 0.0 and 1.0 indicating confidence in classification

4. **reasoning**: Brief explanation of the classification decision

Respond with a JSON array containing one object per column:

```json
[
  {{
    "column_name": "column_name",
    "dimensional_role": "role",
    "dimension_type": "type",
    "confidence": 0.95,
    "reasoning": "explanation"
  }}
]
```
Consider the context of the table name and relationships between columns. Use domain-specific names for 'dimension_type'.

Provide only the JSON response, no additional text.
"""
        return prompt
    
    def _call_openrouter_api(self, prompt: str) -> Dict[str, Any]:
        """Call OpenRouter API"""
        logger.info(f"🌐 [API CALL] Preparing API request to: {self.base_url}")
        logger.info(f"🌐 [API CALL] Model: {self.model}")
        if self.api_key:
            logger.info(f"🌐 [API CALL] API Key (first 10 chars): {self.api_key[:10]}...")
        else:
            logger.error("🌐 [API CALL] No API Key!")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5001",
            "X-Title": "ETL Processor DW Modeling"
        }

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }

        logger.info(f"🌐 [API CALL] Request data prepared, prompt length: {len(prompt)}")
        logger.info(f"🌐 [API CALL] Making POST request...")

        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            logger.info(f"🌐 [API CALL] Response status code: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"❌ [API CALL] Error response: {response.text}")

            response.raise_for_status()

            result = response.json()
            logger.info(f"✅ [API CALL] Successfully received response")
            logger.info(f"🌐 [API CALL] Response keys: {list(result.keys())}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ [API CALL] Request exception: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ [API CALL] Unexpected error: {str(e)}")
            raise
    
    def _parse_ai_response(self, response: Dict[str, Any], columns: List[Dict[str, Any]]) -> List[DimensionClassification]:
        """Parse AI response into classification objects"""
        logger.info(f"🔄 [PARSE] Starting to parse AI response...")

        try:
            logger.info(f"🔄 [PARSE] Response structure: {list(response.keys())}")

            if "choices" not in response:
                raise ValueError("No 'choices' key in response")

            if not response["choices"]:
                raise ValueError("Empty choices array in response")

            content = response["choices"][0]["message"]["content"]
            logger.info(f"🔄 [PARSE] AI response content length: {len(content)}")
            logger.info(f"🔄 [PARSE] AI response content preview: {content[:200]}...")

            # Extract JSON from response (in case there's extra text)
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1

            logger.info(f"🔄 [PARSE] JSON start index: {start_idx}, end index: {end_idx}")

            if start_idx == -1 or end_idx == 0:
                logger.error(f"❌ [PARSE] No JSON array found in response content")
                raise ValueError("No JSON array found in response")

            json_content = content[start_idx:end_idx]
            logger.info(f"🔄 [PARSE] Extracted JSON content: {json_content}")

            classifications_data = json.loads(json_content)
            logger.info(f"🔄 [PARSE] Successfully parsed JSON, found {len(classifications_data)} classifications")

            classifications = []
            for i, item in enumerate(classifications_data):
                logger.info(f"🔄 [PARSE] Processing classification {i+1}: {item.get('column_name', 'unknown')}")
                classification = DimensionClassification(
                    column_name=item["column_name"],
                    dimension_type=item["dimension_type"],
                    dimensional_role=item["dimensional_role"],
                    confidence=float(item["confidence"]),
                    reasoning=item["reasoning"]
                )
                classifications.append(classification)

            logger.info(f"✅ [PARSE] Successfully created {len(classifications)} classification objects")
            return classifications

        except Exception as e:
            logger.error(f"❌ [PARSE] Error parsing AI response: {str(e)}")
            import traceback
            logger.error(f"🔍 [PARSE] Full error traceback:")
            logger.error(traceback.format_exc())
            logger.warning(f"⚠️ [PARSE] Falling back to rule-based classification")
            return self._fallback_classification(columns)
    
    def _fallback_classification(self, columns: List[Dict[str, Any]]) -> List[DimensionClassification]:
        """Fallback classification when AI is not available"""
        logger.info(f"🔄 [FALLBACK] Starting fallback classification for {len(columns)} columns")
        classifications = []

        for i, col in enumerate(columns):
            logger.info(f"🔄 [FALLBACK] Processing column {i+1}/{len(columns)}: {col.get('name', 'unknown')}")
            col_name = col["name"].lower()
            data_type = col.get("data_type", "").upper()

            # Enhanced rule-based classification
            if any(word in col_name for word in ['id', 'key', 'codigo', 'code']) and any(word in col_name for word in ['venda', 'sale', 'transacao', 'transaction']):
                dimension_type = "transaction"
                dimensional_role = "dimension_key"
                confidence = 0.85
            elif any(word in col_name for word in ['data', 'date', 'horario', 'time', 'entrada', 'saida']):
                dimension_type = "time"
                dimensional_role = "time_dimension"
                confidence = 0.90
            elif any(word in col_name for word in ['produto', 'product', 'item', 'servico', 'service']):
                dimension_type = "product"
                dimensional_role = "dimension_attribute"
                confidence = 0.80
            elif any(word in col_name for word in ['cliente', 'customer', 'nome', 'name', 'cpf', 'email', 'telefone', 'phone']):
                dimension_type = "customer"
                dimensional_role = "dimension_attribute"
                confidence = 0.80
            elif any(word in col_name for word in ['categoria', 'category', 'tipo', 'type', 'classe', 'class']):
                dimension_type = "product"
                dimensional_role = "dimension_attribute"
                confidence = 0.75
            elif any(word in col_name for word in ['quantidade', 'qty', 'qtd', 'volume']) and ('INT' in data_type or 'DECIMAL' in data_type):
                dimension_type = "transaction"
                dimensional_role = "fact_measure"
                confidence = 0.85
            elif any(word in col_name for word in ['valor', 'preco', 'price', 'total', 'amount', 'custo', 'cost']) and ('DECIMAL' in data_type or 'FLOAT' in data_type):
                dimension_type = "transaction"
                dimensional_role = "fact_measure"
                confidence = 0.90
            elif any(word in col_name for word in ['vendedor', 'seller', 'funcionario', 'employee', 'usuario', 'user']):
                dimension_type = "employee"
                dimensional_role = "dimension_attribute"
                confidence = 0.75
            elif any(word in col_name for word in ['regiao', 'region', 'estado', 'state', 'cidade', 'city', 'local', 'location']):
                dimension_type = "location"
                dimensional_role = "dimension_attribute"
                confidence = 0.80
            elif any(word in col_name for word in ['bloco', 'block', 'apartamento', 'apartment']):
                dimension_type = "location"
                dimensional_role = "dimension_attribute"
                confidence = 0.80
            elif any(word in col_name for word in ['veiculo', 'vehicle', 'placa', 'plate', 'carro', 'car']):
                dimension_type = "vehicle"
                dimensional_role = "dimension_attribute"
                confidence = 0.80
            elif any(word in col_name for word in ['visita', 'visit', 'acesso', 'access']):
                dimension_type = "visit"
                dimensional_role = "fact_measure"
                confidence = 0.75
            elif any(word in col_name for word in ['motivo', 'reason', 'observacao', 'observation', 'comment']):
                dimension_type = "activity"
                dimensional_role = "dimension_attribute"
                confidence = 0.70
            else:
                dimension_type = "other"
                dimensional_role = "dimension_attribute"
                confidence = 0.60

            classification = DimensionClassification(
                column_name=col["name"],
                dimension_type=dimension_type,
                dimensional_role=dimensional_role,
                confidence=confidence,
                reasoning="Fallback rule-based classification"
            )
            classifications.append(classification)

        return classifications
