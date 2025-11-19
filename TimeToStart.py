# GLP-1 Medical Information Fetcher using EndlessMedical API
# Instructions: Run this in Google Colab

import requests
import json
from typing import Dict, List

class EndlessMedicalAPI:
    """Client for interacting with EndlessMedical API"""
    
    def __init__(self):
        self.base_url = "https://api.endlessmedical.com/v1/dx"
        self.session_id = None
        
    def create_session(self) -> bool:
        """Initialize a new session with the API"""
        try:
            response = requests.get(f"{self.base_url}/InitSession")
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('SessionID')
                print(f"✓ Session created: {self.session_id}")
                return True
            else:
                print(f"✗ Failed to create session: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error creating session: {e}")
            return False
    
    def accept_terms(self) -> bool:
        """Accept the API terms of use"""
        if not self.session_id:
            print("✗ No active session")
            return False
            
        try:
            params = {
                'SessionID': self.session_id,
                'passphrase': 'I have read, understood and I accept and agree to comply with the Terms of Use of EndlessMedicalAPI and Endless Medical services. The Terms of Use are available on endlessmedical.com'
            }
            response = requests.post(f"{self.base_url}/AcceptTermsOfUse", params=params)
            
            if response.status_code == 200:
                print("✓ Terms accepted")
                return True
            else:
                print(f"✗ Failed to accept terms: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error accepting terms: {e}")
            return False
    
    def add_feature(self, feature_name: str, feature_value: str) -> bool:
        """Add a symptom or feature to the current session"""
        if not self.session_id:
            print("✗ No active session")
            return False
            
        try:
            params = {
                'SessionID': self.session_id,
                'name': feature_name,
                'value': feature_value
            }
            response = requests.post(f"{self.base_url}/UpdateFeature", params=params)
            
            if response.status_code == 200:
                print(f"✓ Added feature: {feature_name} = {feature_value}")
                return True
            else:
                print(f"✗ Failed to add feature: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Error adding feature: {e}")
            return False
    
    def analyze(self) -> Dict:
        """Get diagnosis analysis"""
        if not self.session_id:
            print("✗ No active session")
            return {}
            
        try:
            params = {'SessionID': self.session_id}
            response = requests.get(f"{self.base_url}/Analyze", params=params)
            
            if response.status_code == 200:
                data = response.json()
                print("✓ Analysis complete")
                return data
            else:
                print(f"✗ Failed to analyze: {response.status_code}")
                return {}
        except Exception as e:
            print(f"✗ Error during analysis: {e}")
            return {}


def fetch_glp1_information():
    """
    Fetch information about GLP-1 medications and related conditions
    using the EndlessMedical API
    """
    print("=" * 60)
    print("GLP-1 MEDICAL INFORMATION FETCHER")
    print("=" * 60)
    print()
    
    # Initialize API client
    api = EndlessMedicalAPI()
    
    # Create session
    if not api.create_session():
        return
    
    # Accept terms
    if not api.accept_terms():
        return
    
    print()
    print("-" * 60)
    print("SCENARIO 1: Patient considering GLP-1 for diabetes")
    print("-" * 60)
    
    # Add relevant symptoms/conditions for GLP-1 consideration
    api.add_feature("Diabetes", "yes")
    api.add_feature("HighBloodSugar", "yes")
    api.add_feature("Age", "45")
    api.add_feature("Gender", "male")
    
    # Get analysis
    results = api.analyze()
    
    if results:
        print("\nAnalysis Results:")
        print(json.dumps(results, indent=2))
    
    # Create new session for obesity scenario
    print()
    print("-" * 60)
    print("SCENARIO 2: Patient considering GLP-1 for weight management")
    print("-" * 60)
    
    api2 = EndlessMedicalAPI()
    api2.create_session()
    api2.accept_terms()
    
    api2.add_feature("Obesity", "yes")
    api2.add_feature("WeightGain", "yes")
    api2.add_feature("Age", "38")
    api2.add_feature("Gender", "female")
    
    results2 = api2.analyze()
    
    if results2:
        print("\nAnalysis Results:")
        print(json.dumps(results2, indent=2))
    
    print()
    print("=" * 60)
    print("IMPORTANT INFORMATION ABOUT GLP-1 MEDICATIONS")
    print("=" * 60)
    print("""
GLP-1 Receptor Agonists (Glucagon-Like Peptide-1):

Common Medications:
- Semaglutide (Ozempic, Wegovy)
- Liraglutide (Victoza, Saxenda)
- Dulaglutide (Trulicity)
- Tirzepatide (Mounjaro, Zepbound)

Primary Uses:
1. Type 2 Diabetes Management
2. Weight Loss/Obesity Treatment
3. Cardiovascular Risk Reduction

How They Work:
- Stimulate insulin secretion
- Suppress glucagon release
- Slow gastric emptying
- Reduce appetite

Common Side Effects:
- Nausea
- Vomiting
- Diarrhea
- Constipation
- Abdominal pain

Serious Considerations:
- Risk of thyroid C-cell tumors
- Pancreatitis risk
- Gallbladder problems
- Kidney function monitoring needed

**ALWAYS CONSULT A HEALTHCARE PROVIDER BEFORE STARTING GLP-1 MEDICATIONS**
This information is for educational purposes only.
    """)


# Run the application
if __name__ == "__main__":
    fetch_glp1_information()
    
    print()
    print("=" * 60)
    print("Additional Resources:")
    print("- EndlessMedical API: https://www.endlessmedical.com")
    print("- Always verify information with licensed healthcare providers")
    print("=" * 60)
