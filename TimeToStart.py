# GLP-1 Medical Information App - Streamlit Version (Production Ready)
# Deploy with: streamlit run app.py
# Requirements: streamlit>=1.28.0, requests>=2.31.0

import streamlit as st
import requests
import json
from typing import Dict, Optional, List, Tuple
import time
from datetime import datetime

# Configuration
API_BASE_URL = "https://api.endlessmedical.com/v1/dx"
API_TIMEOUT = 10  # seconds
MAX_RETRIES = 3

class EndlessMedicalAPI:
    """Client for interacting with EndlessMedical API with enhanced error handling"""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.session_id = None
        self.last_error = None
        
    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                      data: Dict = None, retries: int = MAX_RETRIES) -> Optional[Dict]:
        """Make HTTP request with retry logic and error handling"""
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(retries):
            try:
                if method.upper() == "GET":
                    response = requests.get(url, params=params, timeout=API_TIMEOUT)
                else:
                    response = requests.post(url, params=params, json=data, timeout=API_TIMEOUT)
                
                # Check for successful status code
                if response.status_code == 200:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        self.last_error = "Invalid JSON response from API"
                        return None
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                else:
                    self.last_error = f"API returned status code {response.status_code}"
                    if attempt == retries - 1:
                        return None
                    
            except requests.exceptions.Timeout:
                self.last_error = "Request timed out"
                if attempt == retries - 1:
                    return None
                time.sleep(1)
                
            except requests.exceptions.ConnectionError:
                self.last_error = "Connection error - check internet connection"
                if attempt == retries - 1:
                    return None
                time.sleep(1)
                
            except Exception as e:
                self.last_error = f"Unexpected error: {str(e)}"
                return None
                
        return None
    
    def create_session(self) -> bool:
        """Initialize a new session with the API"""
        data = self._make_request("GET", "InitSession")
        if data and 'SessionID' in data:
            self.session_id = data['SessionID']
            return True
        return False
    
    def accept_terms(self) -> bool:
        """Accept the API terms of use"""
        if not self.session_id:
            self.last_error = "No active session"
            return False
        
        params = {
            'SessionID': self.session_id,
            'passphrase': 'I have read, understood and I accept and agree to comply with the Terms of Use of EndlessMedicalAPI and Endless Medical services. The Terms of Use are available on endlessmedical.com'
        }
        
        data = self._make_request("POST", "AcceptTermsOfUse", params=params)
        return data is not None
    
    def add_feature(self, feature_name: str, feature_value: str) -> bool:
        """Add a symptom or feature to the current session"""
        if not self.session_id:
            self.last_error = "No active session"
            return False
        
        params = {
            'SessionID': self.session_id,
            'name': feature_name,
            'value': feature_value
        }
        
        data = self._make_request("POST", "UpdateFeature", params=params)
        return data is not None
    
    def analyze(self) -> Optional[Dict]:
        """Get diagnosis analysis"""
        if not self.session_id:
            self.last_error = "No active session"
            return None
        
        params = {'SessionID': self.session_id}
        return self._make_request("GET", "Analyze", params=params)
    
    def get_last_error(self) -> str:
        """Get the last error message"""
        return self.last_error or "Unknown error"


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    defaults = {
        'analysis_complete': False,
        'results': None,
        'api_status': 'ready',
        'last_analysis_time': None,
        'feature_count': 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def test_api_connection() -> Tuple[bool, str]:
    """Test API connectivity"""
    try:
        api = EndlessMedicalAPI()
        if api.create_session():
            return True, "✅ API connection successful"
        else:
            return False, f"❌ API connection failed: {api.get_last_error()}"
    except Exception as e:
        return False, f"❌ Connection error: {str(e)}"


def display_glp1_info_sidebar():
    """Display GLP-1 information in sidebar"""
    with st.sidebar:
        st.header("💊 About GLP-1 Medications")
        
        with st.expander("Common GLP-1 Medications", expanded=False):
            st.markdown("""
            - **Semaglutide** (Ozempic, Wegovy)
            - **Liraglutide** (Victoza, Saxenda)
            - **Dulaglutide** (Trulicity)
            - **Tirzepatide** (Mounjaro, Zepbound)
            - **Exenatide** (Byetta, Bydureon)
            """)
        
        with st.expander("Primary Uses", expanded=False):
            st.markdown("""
            - Type 2 Diabetes Management
            - Weight Loss/Obesity Treatment
            - Cardiovascular Risk Reduction
            - Metabolic Health Improvement
            """)
        
        with st.expander("How They Work", expanded=False):
            st.markdown("""
            - Stimulate insulin secretion
            - Suppress glucagon release
            - Slow gastric emptying
            - Reduce appetite
            - Improve insulin sensitivity
            """)
        
        st.warning("⚠️ **Medical Disclaimer:** This tool is for educational purposes only. Always consult a licensed healthcare provider before starting any medication.")
        
        st.markdown("---")
        
        # API Status Check
        if st.button("🔌 Test API Connection"):
            with st.spinner("Testing connection..."):
                status, message = test_api_connection()
                if status:
                    st.success(message)
                else:
                    st.error(message)
        
        st.markdown("---")
        st.caption("**Data Source:** [EndlessMedical API](https://www.endlessmedical.com)")
        st.caption(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")


def collect_patient_data() -> Dict:
    """Collect patient information from UI"""
    st.header("📋 Patient Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Age", min_value=18, max_value=120, value=45, 
                             help="Patient's age in years")
        gender = st.selectbox("Gender", ["male", "female"], 
                             help="Biological sex")
    
    with col2:
        bmi = st.number_input("BMI (optional)", min_value=10.0, max_value=70.0, 
                             value=25.0, step=0.1,
                             help="Body Mass Index")
        weight = st.number_input("Weight in kg (optional)", min_value=30.0, 
                                max_value=300.0, value=70.0, step=0.5)
    
    st.markdown("---")
    st.subheader("🏥 Medical Conditions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        has_diabetes = st.checkbox("Diabetes Type 2", value=False,
                                  help="Diagnosed Type 2 Diabetes")
        has_prediabetes = st.checkbox("Prediabetes", value=False,
                                     help="Elevated blood sugar levels")
        has_obesity = st.checkbox("Obesity", value=False,
                                 help="BMI ≥ 30")
    
    with col2:
        has_high_blood_sugar = st.checkbox("High Blood Sugar", value=False,
                                          help="Elevated glucose levels")
        has_weight_gain = st.checkbox("Recent Weight Gain", value=False,
                                     help="Significant weight increase")
        has_cardiovascular = st.checkbox("Cardiovascular Disease", value=False,
                                       help="Heart or vascular conditions")
    
    with col3:
        has_hypertension = st.checkbox("Hypertension", value=False,
                                      help="High blood pressure")
        has_high_cholesterol = st.checkbox("High Cholesterol", value=False,
                                          help="Elevated cholesterol levels")
        has_fatty_liver = st.checkbox("Fatty Liver Disease", value=False,
                                     help="NAFLD/NASH")
    
    st.markdown("---")
    st.subheader("🩺 Current Symptoms")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        has_fatigue = st.checkbox("Fatigue", value=False)
        has_increased_thirst = st.checkbox("Increased Thirst", value=False)
        has_frequent_urination = st.checkbox("Frequent Urination", value=False)
    
    with col2:
        has_blurred_vision = st.checkbox("Blurred Vision", value=False)
        has_slow_healing = st.checkbox("Slow Healing Wounds", value=False)
        has_hunger = st.checkbox("Increased Hunger", value=False)
    
    with col3:
        has_numbness = st.checkbox("Numbness/Tingling", value=False)
        has_nausea = st.checkbox("Nausea", value=False)
        has_headaches = st.checkbox("Frequent Headaches", value=False)
    
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
    """Analyze patient data using EndlessMedical API"""
    api = EndlessMedicalAPI()
    
    # Create session
    progress_bar = st.progress(0, text="Initializing session...")
    if not api.create_session():
        st.error(f"Failed to create session: {api.get_last_error()}")
        return None
    
    progress_bar.progress(20, text="Accepting terms...")
    if not api.accept_terms():
        st.error(f"Failed to accept terms: {api.get_last_error()}")
        return None
    
    # Add patient features
    progress_bar.progress(40, text="Adding patient demographics...")
    api.add_feature("Age", str(patient_data['demographics']['age']))
    api.add_feature("Gender", patient_data['demographics']['gender'])
    
    progress_bar.progress(50, text="Adding medical conditions...")
    feature_count = 0
    
    # Add conditions
    for condition, has_condition in patient_data['conditions'].items():
        if has_condition:
            api.add_feature(condition, "yes")
            feature_count += 1
            time.sleep(0.1)  # Small delay to avoid rate limiting
    
    progress_bar.progress(70, text="Adding symptoms...")
    # Add symptoms
    for symptom, has_symptom in patient_data['symptoms'].items():
        if has_symptom:
            api.add_feature(symptom, "yes")
            feature_count += 1
            time.sleep(0.1)
    
    st.session_state.feature_count = feature_count
    
    # Analyze
    progress_bar.progress(90, text="Analyzing patient data...")
    time.sleep(0.5)
    results = api.analyze()
    
    progress_bar.progress(100, text="Analysis complete!")
    time.sleep(0.3)
    progress_bar.empty()
    
    if not results:
        st.error(f"Analysis failed: {api.get_last_error()}")
        return None
    
    return results


def assess_glp1_suitability(patient_data: Dict) -> Tuple[str, str, List[str]]:
    """Assess patient suitability for GLP-1 therapy"""
    conditions = patient_data['conditions']
    demographics = patient_data['demographics']
    
    # Calculate risk factors
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
        risk_factors.append("Recent significant weight gain")
    
    # Determine suitability level
    if conditions.get('Diabetes') or (conditions.get('Obesity') and demographics['bmi'] >= 30):
        level = "high"
        message = "✅ **High Suitability** - Patient profile strongly suggests potential benefit from GLP-1 therapy"
    elif len(risk_factors) >= 2:
        level = "moderate"
        message = "⚠️ **Moderate Suitability** - Patient may benefit from GLP-1 therapy pending further evaluation"
    elif len(risk_factors) == 1:
        level = "low"
        message = "ℹ️ **Low Suitability** - GLP-1 therapy may not be indicated at this time"
    else:
        level = "not_indicated"
        message = "❌ **Not Indicated** - GLP-1 therapy typically not recommended for this profile"
    
    return level, message, risk_factors


def display_results(results: Dict, patient_data: Dict):
    """Display analysis results"""
    st.header("📊 Analysis Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Features Analyzed", st.session_state.feature_count)
    with col2:
        st.metric("Age", patient_data['demographics']['age'])
    with col3:
        st.metric("BMI", f"{patient_data['demographics']['bmi']:.1f}")
    
    st.markdown("---")
    
    # GLP-1 Suitability Assessment
    st.subheader("💊 GLP-1 Medication Suitability Assessment")
    
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
        st.markdown("**Identified Risk Factors:**")
        for factor in risk_factors:
            st.markdown(f"• {factor}")
    
    # Recommendations
    st.markdown("---")
    st.subheader("📋 Recommended Next Steps")
    
    if level in ["high", "moderate"]:
        st.markdown("""
        1. **Consult with Endocrinologist** - Schedule appointment for comprehensive evaluation
        2. **Complete Medical History Review** - Ensure no contraindications
        3. **Laboratory Tests** - A1C, fasting glucose, kidney function, thyroid panel
        4. **Insurance Verification** - Check coverage and prior authorization requirements
        5. **Discuss Benefits vs Risks** - Review potential side effects and monitoring plan
        """)
    else:
        st.markdown("""
        1. **Lifestyle Modifications** - Focus on diet and exercise first
        2. **Regular Monitoring** - Track weight, blood sugar, and blood pressure
        3. **Follow-up Appointment** - Re-evaluate in 3-6 months
        4. **Consider Alternative Therapies** - Discuss other medication options if needed
        """)
    
    # Raw API Results
    st.markdown("---")
    with st.expander("🔬 Detailed API Response", expanded=False):
        st.json(results)
    
    # Export options
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download Results (JSON)", use_container_width=True):
            results_data = {
                'timestamp': datetime.now().isoformat(),
                'patient_data': patient_data,
                'api_results': results,
                'suitability': {'level': level, 'message': message, 'risk_factors': risk_factors}
            }
            st.download_button(
                label="Download JSON",
                data=json.dumps(results_data, indent=2),
                file_name=f"glp1_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("🔄 New Analysis", use_container_width=True):
            st.session_state.analysis_complete = False
            st.session_state.results = None
            st.rerun()


def main():
    """Main Streamlit application"""
    
    st.set_page_config(
        page_title="GLP-1 Medical Information Analyzer",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
    }
    .reportview-container .main .block-container {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    initialize_session_state()
    
    # Header
    st.title("💊 GLP-1 Medical Information Analyzer")
    st.markdown("**AI-Powered Patient Assessment for GLP-1 Medication Suitability**")
    st.markdown("---")
    
    # Sidebar
    display_glp1_info_sidebar()
    
    # Main content
    if not st.session_state.analysis_complete:
        # Data collection phase
        patient_data = collect_patient_data()
        
        st.markdown("---")
        
        # Analyze button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔍 Analyze Patient Profile", type="primary", use_container_width=True):
                with st.spinner("Analyzing patient data..."):
                    results = analyze_patient(patient_data)
                    
                    if results:
                        st.session_state.results = results
                        st.session_state.patient_data = patient_data
                        st.session_state.analysis_complete = True
                        st.session_state.last_analysis_time = datetime.now()
                        st.success("✅ Analysis complete!")
                        time.sleep(0.5)
                        st.rerun()
    else:
        # Display results
        display_results(st.session_state.results, st.session_state.patient_data)
    
    # Educational Information Section
    st.markdown("---")
    st.header("📚 GLP-1 Medication Information")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "How They Work", 
        "Benefits", 
        "Side Effects", 
        "Considerations",
        "Cost & Access"
    ])
    
    with tab1:
        st.markdown("""
        ### Mechanism of Action
        
        GLP-1 (Glucagon-Like Peptide-1) receptor agonists work through multiple pathways:
        
        **Glucose Regulation:**
        - Stimulate insulin secretion when blood sugar is elevated (glucose-dependent)
        - Suppress glucagon release to prevent excess glucose production by liver
        - Reduce hepatic glucose output
        
        **Weight Management:**
        - Slow gastric emptying, promoting satiety and reducing food intake
        - Act on brain appetite centers to reduce hunger signals
        - Increase energy expenditure
        
        **Cardiovascular Effects:**
        - Improve endothelial function
        - Reduce inflammation markers
        - May lower blood pressure
        - Potential anti-atherosclerotic effects
        """)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **For Type 2 Diabetes:**
            - A1C reduction: 1.0-1.5% on average
            - Low risk of hypoglycemia (vs insulin, sulfonylureas)
            - Cardiovascular benefits demonstrated in trials
            - Kidney protective effects
            - Can be combined with other diabetes medications
            """)
        
        with col2:
            st.markdown("""
            **For Weight Management:**
            - Average weight loss: 10-15% of body weight
            - Sustained weight loss with continued use
            - Reduced appetite and food cravings
            - Improved metabolic parameters
            - Better quality of life outcomes
            """)
        
        st.markdown("""
        **Additional Benefits:**
        - Reduced risk of major cardiovascular events (some medications)
        - Potential reduction in stroke risk
        - May improve liver enzymes in fatty liver disease
        - Once-weekly dosing options available
        - Can reduce need for insulin in some patients
        """)
    
    with tab3:
        st.markdown("""
        ### Side Effect Profile
        
        **Very Common (>10% of patients):**
        - Nausea (usually improves after 4-8 weeks)
        - Diarrhea
        - Decreased appetite
        - Constipation
        
        **Common (1-10% of patients):**
        - Vomiting
        - Abdominal pain or discomfort
        - Heartburn/acid reflux
        - Injection site reactions
        - Fatigue
        - Headache
        
        **Serious but Rare:**
        - Pancreatitis (inflammation of pancreas)
        - Gallbladder problems (gallstones, cholecystitis)
        - Kidney problems (usually in dehydrated patients)
        - Severe allergic reactions
        - Changes in vision (diabetic retinopathy complications)
        
        **Black Box Warning:**
        - Risk of thyroid C-cell tumors (seen in rodent studies)
        - Not recommended if personal/family history of medullary thyroid cancer
        - Avoid in Multiple Endocrine Neoplasia syndrome type 2
        
        **Management Tips:**
        - Start with low dose and titrate slowly
        - Take with food to reduce nausea
        - Stay well hydrated
        - Report severe abdominal pain immediately
        """)
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Contraindications:**
            - Personal/family history of medullary thyroid carcinoma
            - Multiple Endocrine Neoplasia syndrome type 2
            - Pregnancy or planning pregnancy
            - Type 1 diabetes (most formulations)
            - Severe gastrointestinal disease
            - History of pancreatitis (relative)
            - Diabetic ketoacidosis
            """)
        
        with col2:
            st.markdown("""
            **Drug Interactions:**
            - May slow absorption of oral medications
            - Insulin doses may need adjustment
            - Warfarin monitoring needed
            - May affect digoxin levels
            - Caution with other weight loss medications
            """)
        
        st.markdown("""
        **Monitoring Requirements:**
        - Regular blood glucose monitoring (if diabetic)
        - Kidney function tests (baseline and periodic)
        - Watch for signs of pancreatitis
        - Monitor for dehydration
        - Regular weight checks
        - A1C every 3 months initially
        - Thyroid monitoring (if symptoms develop)
        - Eye exams (diabetic patients)
        
        **Lifestyle Factors:**
        - Most effective when combined with diet and exercise
        - Requires long-term commitment
        - Weight may return if medication stopped
        - Regular follow-up appointments essential
        - Support for behavior change recommended
        """)
    
    with tab5:
        st.markdown("""
        ### Cost & Access Information
        
        **Pricing (Without Insurance):**
        - Monthly cost: $900-$1,500
        - Annual cost: $11,000-$18,000
        - Prices vary by medication and pharmacy
        
        **Insurance Coverage:**
        - Most insurance plans cover for diabetes
        - Weight loss indication may have restrictions
        - Prior authorization often required
        - Step therapy may be needed
        - Coverage varies by plan and state
        
        **Ways to Reduce Costs:**
        
        1. **Manufacturer Savings Programs:**
           - Ozempic: savings card available
           - Wegovy: savings program for eligible patients
           - Trulicity: savings card program
           - Mounjaro: savings card for eligible patients
        
        2. **Patient Assistance Programs:**
           - Novo Nordisk PAP (Ozempic, Wegovy)
           - Lilly Cares (Trulicity, Mounjaro)
           - Income-based eligibility
        
        3. **Generic/Biosimilar Options:**
           - Not yet available in US
           - Expected in coming years
        
        4. **Compounding Pharmacies:**
           - Lower cost options available
           - Quality and safety concerns
           - Not FDA-approved formulations
        
        5. **Alternative Strategies:**
           - Ask about older GLP-1 medications
           - Check multiple pharmacies for pricing
           - Use prescription discount cards
           - Consider mail-order pharmacies
        
        **Access Resources:**
        - [NeedyMeds.org](https://www.needymeds.org) - Assistance program database
        - [RxAssist.org](https://www.rxassist.org) - Patient assistance programs
        - Manufacturer websites for savings cards
        - Healthcare provider's office for samples
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>⚠️ IMPORTANT MEDICAL DISCLAIMER ⚠️</strong></p>
        <p>This tool provides educational information only and is NOT a substitute for professional medical advice, 
        diagnosis, or treatment. The analysis provided should not be used to make medical decisions.</p>
        <p><strong>Always seek the advice of your physician or other qualified health provider</strong> with any questions 
        you may have regarding a medical condition or medication.</p>
        <p style='margin-top: 20px;'>
            Data powered by <a href='https://www.endlessmedical.com' target='_blank'>EndlessMedical API</a> | 
            Educational Use Only | Not for Clinical Decision Making
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
