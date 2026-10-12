import sys
import os

# Add backend directory to path so we can import app modules
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_dir)

from app.ai_client import AIClient

def run_test():
    client = AIClient()
    
    verify_data = {
        "product_id": "PRD_1234",
        "manufacturing_location": "USA",
        "origin": "Factory_A",
        "weather_conditions": "Clear",
        "temperature": 22.5,
        "humidity": 45.0,
        "micro_textures": 0.96,
        "color_printing_patterns": 0.95,
        "geometric_alignment": 0.99,
        "surface_features": 0.94,
        "printing_artifacts": 0.98,
        "frequency_features": 0.90,
        "color_space_metrics": 0.95,
        "spectral_metrics": 0.92,
        "deep_learning_latent_features": 0.90,
        "qr_code_integrity": 0.99,
        "barcode_integrity": 1.0,
        "product_network": None
    }
    
    print("Testing Authentic Scan...")
    result = client.evaluate_scan_advanced(verify_data)
    print(result)
    
    print("\nTesting Counterfeit Scan (Poor Optical Metrics + Bad Temperature)...")
    verify_data["micro_textures"] = 0.50
    verify_data["geometric_alignment"] = 0.60
    verify_data["temperature"] = 35.0
    verify_data["qr_code_integrity"] = 0.65
    result2 = client.evaluate_scan_advanced(verify_data)
    print(result2)

if __name__ == "__main__":
    run_test()
