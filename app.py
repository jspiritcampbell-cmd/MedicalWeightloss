# GLP-1 Medical Information App - Streamlit (Fixed for Deployment)
# Deploy with: streamlit run app.py
# Requirements: streamlit>=1.28.0, requests>=2.31.0

import streamlit as st
import requests
import json
from typing import Dict, Optional, List, Tuple
import time
from datetime import datetime
import random

# Configuration
API_BASE_URL = "https://api.endlessmedical.com/v1/dx"
API_TIMEOUT = 15
MAX_RETRIES = 2
USE_MOCK_MODE = False  # Will auto-switch to True if API fails

class MockAPI:
    """Mock API for when EndlessMedical is unavailable"""
    
    def __init__(self):
        self.session_id = f"mock_{random.randint(10000, 99999)}"
        self.features = []
        
    def create_session(self) -> bool:
        return True
    
    def accept_terms(self) -> bool:
        return True
    
    def add_feature(self, name: str, value: str) -> bool:
        self.features.append({"name": name, "value": value})
        return True
    
    def analyze(self) -> Dict:
        """Generate mock analysis based on features"""
        has_diabetes = any(f["name"] == "Diabetes" for f in self.features)
        has_obesity = any(f["name"] == "Obesity" for f in self.features)
        has_high_sugar = any(f["name"] == "HighBloodSugar" for f in self.features)
        
        conditions = []
        if has_diabetes:
            conditions.append({
                "Name": "Type 2 Diabetes Mellitus",
                "Probability": 0.85,
                "Icd": "E11",
                "ProfName": "Type 2 Diabetes Mellitus",
                "Ranking": 1
            })
        if has_obesity:
            conditions.append({
                "Name": "Obesity",
                "Probability": 0.78,
                "Icd": "E66",
                "ProfName": "Obesity",
                "Ranking": 2
            })
        if has_high_sugar:
            conditions.append({
                "Name": "Hyperglycemia",
                "Probability": 0.72,
                "Icd": "R73.9",
                "ProfName": "Hyperglycemia",
                "Ranking": 3
            })
        
        if not conditions:
            conditions = [{
                "Name": "General Health Assessment",
                "Probability": 0.60,
                "Icd": "Z00.00",
                "ProfName": "General medical examination",
                "Ranking": 1
            }]
        
        return {
            "Status": "SUCCESS",
            "SessionID": self.session_id,
            "Conditions": conditions,
            "TriageLevel": "MEDIUM" if has_diabetes or has_obesity else "LOW",
            "Message": "Mock analysis generated - EndlessMedical API unavailable"
        }
    
    def get_last_error(self) -> str:
        return "Using mock mode - API connection unavailable"


class EndlessMedicalAPI:
    """Client for EndlessMedical API with fallback to mock mode"""
    
    def __init__(self, force_mock: bool = False):
        self.base_url = API_BASE_URL
        self.session_id = None
        self.last_error = None
        self.use_mock = force_mock
        self.mock_api = None
        
        if self.use_mock:
            self.mock_api = MockAPI()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                      data: Dict = None) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        if self.use_mock:
            return {"success": True}
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=API_TIMEOUT)
            else:
                response = requests.post(url, params=params, json=data, timeout=API_TIMEOUT)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    self.last_error = "Invalid JSON response"
                    return None
            else:
                self.last_error = f"Status code {response.status_code}"
                return None
                
        except requests.exceptions.Timeout:
            self.last_error = "Request timeout"
            return None
            
        except requests.exceptions.ConnectionError:
            self.last_error = "Connection failed"
            return None
            
        except Exception as e:
            self.last_error = f"Error: {str(e)}"
            return None
    
    def create_session(self) -> bool:
        """Initialize session"""
        if self.use_mock:
            return self.mock_api.create_session()
        
        data = self._make_request("GET", "InitSession")
        if data and 'SessionID' in data:
            self.session_id = data['SessionID']
            return True
        return False
    
    def accept_terms(self) -> bool:
        """Accept API terms"""
        if self.use_mock:
            return self.mock_api.accept_terms()
        
        if not self.session_id:
            return False
        
        params = {
            'SessionID': self.session_id,
            'passphrase': 'I have read, understood and I accept and agree to comply with the Terms of Use of EndlessMedicalAPI and Endless Medical services. The Terms of Use are available on endlessmedical.com'
        }
        
        data = self._make_request("POST", "AcceptTermsOfUse", params=params)
        return data is not None
    
    def add_feature(self, feature_name: str, feature_value: str) -> bool:
        """Add feature to session"""
        if self.use_mock:
            return self.mock_api.add_feature(feature_name, feature_value)
        
        if not self.session_id:
            return False
        
        params = {
            'SessionID': self.session_id,
            'name': feature_name,
            'value': feature_value
        }
        
        data = self._make_request("POST", "UpdateFeature", params=params)
        return data is not None
    
    def analyze(self) -> Optional[Dict]:
        """Get analysis"""
        if self.use_mock:
            return self.mock_api.analyze()
        
        if not self.session_id:
            return None
        
        params = {'SessionID': self.session_id}
        return self._make_request("GET", "Analyze", params=params)
    
    def get_last_error(self) -> str:
        """Get last error message"""
        return self.last_error or "Unknown error"


def initialize_session_state():
    """Initialize session state"""
    defaults = {
        'analysis_complete': False,
        'results': None,
        'last_analysis_time': None,
        'feature_count': 0,
        'using_mock': USE_MOCK_MODE,
        'api_tested': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def test_api_connection() -> Tuple[bool, str]:
    """Test API connectivity"""
    try:
        response = requests.get(f"{API_BASE_URL}/InitSession", timeout=5)
        if response.status_code == 200:
            return True, "✅ API connection successful"
        else:
            return False, f"⚠️ API returned status {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "⚠️ Connection timeout - using mock mode"
    except requests.exceptions.ConnectionError:
        return False, "⚠️ Connection error - using mock mode"
    except Exception as e:
        return False, f"⚠️ Error: {str(e)} - using mock mode"


def display_sidebar():
    """Display sidebar content"""
    with st.sidebar:
        st.header("💊 About GLP-1 Medications")
        
        # API Status
        st.subheader("🔌 API Status")
        if st.session_state.using_mock:
            st.warning("⚠️ Using Demo Mode\n\nAPI unavailable - showing sample analysis")
        else:
            st.success("✅ Live API Connected")
        
        if st.button("Test API Connection", use_container_width=True):
            with st.spinner("Testing..."):
                status, message = test_api_connection()
                st.info(message)
                if not status:
                    st.session_state.using_mock = True
        
        st.markdown("---")
        
        with st.expander("Common GLP-1 Medications"):
            st.markdown("""
            - **Semaglutide** (Ozempic, Wegovy)
            - **Liraglutide** (Victoza, Saxenda)
            - **Dulaglutide** (Trulicity)
            - **Tirzepatide** (Mounjaro, Zepbound)
            - **Exenatide** (Byetta)
            """)
        
        with st.expander("Primary Uses"):
            st.markdown("""
            - Type 2 Diabetes Management
            - Weight Loss/Obesity Treatment
            - Cardiovascular Risk Reduction
            - Metabolic Health Improvement
            """)
        
        st.markdown("---")
        st.warning("⚠️ **Disclaimer:** Educational purposes only. Consult healthcare providers for medical advice.")
        st.caption("**Data Source:** [EndlessMedical API](https://www.endlessmedical.com)")


def collect_patient_data() -> Dict:
    """Collect patient information"""
    st.header("📋 Patient Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Age", min_value=18, max_value=120, value=45)
        gender = st.selectbox("Gender", ["male", "female"])
    
    with col2:
        bmi = st.number_input("BMI", min_value=10.0, max_value=70.0, value=25.0, step=0.1)
        weight = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, value=70.0)
    
    st.markdown("---")
    st.subheader("🏥 Medical Conditions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        has_diabetes = st.checkbox("Type 2 Diabetes")
        has_prediabetes = st.checkbox("Prediabetes")
        has_obesity = st.checkbox("Obesity")
    
    with col2:
        has_high_blood_sugar = st.checkbox("High Blood Sugar")
        has_weight_gain = st.checkbox("Recent Weight Gain")
        has_cardiovascular = st.checkbox("Cardiovascular Disease")
    
    with col3:
        has_hypertension = st.checkbox("Hypertension")
        has_high_cholesterol = st.checkbox("High Cholesterol")
        has_fatty_liver = st.checkbox("Fatty Liver")
    
    st.markdown("---")
    st.subheader("🩺 Current Symptoms")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        has_fatigue = st.checkbox("Fatigue")
        has_increased_thirst = st.checkbox("Increased Thirst")
        has_frequent_urination = st.checkbox("Frequent Urination")
    
    with col2:
        has_blurred_vision = st.checkbox("Blurred Vision")
        has_slow_healing = st.checkbox("Slow Healing")
        has_hunger = st.checkbox("Increased Hunger")
    
    with col3:
        has_numbness = st.checkbox("Numbness/Tingling")
        has_nausea = st.checkbox("Nausea")
        has_headaches = st.checkbox("Headaches")
    
    return {
        'demographics': {
            'age': age,
            'gender': gender,
            'bmi': bmi,
            'weight': weight
        },
        'conditions': {
            'Diabetes': has_diabetes,
            'Prediabetes': has_prediabetes,
            'Obesity': has_obesity,
            'HighBloodSugar': has_high_blood_sugar,
            'WeightGain': has_weight_gain,
            'CardiovascularDisease': has_cardiovascular,
            'Hypertension': has_hypertension,
            'HighCholesterol': has_high_cholesterol,
            'FattyLiver': has_fatty_liver
        },
        'symptoms': {
            'Fatigue': has_fatigue,
            'IncreasedThirst': has_increased_thirst,
            'FrequentUrination': has_frequent_urination,
            'BlurredVision': has_blurred_vision,
            'SlowHealing': has_slow_healing,
            'IncreasedHunger': has_hunger,
            'Numbness': has_numbness,
            'Nausea': has_nausea,
            'Headaches': has_headaches
        }
    }


def analyze_patient(patient_data: Dict) -> Optional[Dict]:
    """Analyze patient data"""
    api = EndlessMedicalAPI(force_mock=st.session_state.using_mock)
    
    progress_bar = st.progress(0, text="Initializing...")
    
    if not api.create_session():
        if not st.session_state.using_mock:
            st.warning("⚠️ API unavailable - switching to demo mode")
            st.session_state.using_mock = True
            api = EndlessMedicalAPI(force_mock=True)
            api.create_session()
    
    progress_bar.progress(20, text="Accepting terms...")
    api.accept_terms()
    
    progress_bar.progress(40, text="Adding demographics...")
    api.add_feature("Age", str(patient_data['demographics']['age']))
    api.add_feature("Gender", patient_data['demographics']['gender'])
    
    progress_bar.progress(50, text="Adding conditions...")
    feature_count = 0
    
    for condition, has_condition in patient_data['conditions'].items():
        if has_condition:
            api.add_feature(condition, "yes")
            feature_count += 1
    
    progress_bar.progress(70, text="Adding symptoms...")
    for symptom, has_symptom in patient_data['symptoms'].items():
        if has_symptom:
            api.add_feature(symptom, "yes")
            feature_count += 1
    
    st.session_state.feature_count = feature_count
    
    progress_bar.progress(90, text="Analyzing...")
    time.sleep(0.5)
    results = api.analyze()
    
    progress_bar.progress(100, text="Complete!")
    time.sleep(0.3)
    progress_bar.empty()
    
    return results


def assess_glp1_suitability(patient_data: Dict) -> Tuple[str, str, List[str]]:
    """Assess GLP-1 suitability"""
    conditions = patient_data['conditions']
    demographics = patient_data['demographics']
    
    risk_factors = []
    if conditions.get('Diabetes'):
        risk_factors.append("Type 2 Diabetes diagnosis")
    if conditions.get('Obesity') or demographics['bmi'] >= 30:
        risk_factors.append("Obesity (BMI ≥ 30)")
    if conditions.get('Prediabetes'):
        risk_factors.append("Prediabetes")
    if conditions.get('CardiovascularDisease'):
        risk_factors.append("Cardiovascular disease")
    if conditions.get('HighBloodSugar'):
        risk_factors.append("Elevated blood sugar")
    if conditions.get('WeightGain'):
        risk_factors.append("Significant weight gain")
    
    if conditions.get('Diabetes') or (conditions.get('Obesity') and demographics['bmi'] >= 30):
        level = "high"
        message = "✅ **High Suitability** - Strong indication for GLP-1 therapy"
    elif len(risk_factors) >= 2:
        level = "moderate"
        message = "⚠️ **Moderate Suitability** - May benefit from evaluation"
    elif len(risk_factors) == 1:
        level = "low"
        message = "ℹ️ **Low Suitability** - May not be indicated"
    else:
        level = "not_indicated"
        message = "❌ **Not Indicated** - Typically not recommended"
    
    return level, message, risk_factors


def display_results(results: Dict, patient_data: Dict):
    """Display analysis results"""
    st.header("📊 Analysis Results")
    
    # Display mode indicator
    if st.session_state.using_mock:
        st.info("ℹ️ **Demo Mode** - Showing sample analysis (API unavailable)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Features Analyzed", st.session_state.feature_count)
    with col2:
        st.metric("Age", patient_data['demographics']['age'])
    with col3:
        st.metric("BMI", f"{patient_data['demographics']['bmi']:.1f}")
    
    st.markdown("---")
    
    # GLP-1 Assessment
    st.subheader("💊 GLP-1 Medication Suitability")
    
    level, message, risk_factors = assess_glp1_suitability(patient_data)
    
    if level == "high":
        st.success(message)
    elif level == "moderate":
        st.warning(message)
    elif level == "low":
        st.info(message)
    else:
        st.error(message)
    
    if risk_factors:
        st.markdown("**Risk Factors Identified:**")
        for
