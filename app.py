import streamlit as st
import sys
import os

# Ensure src/agent.py can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.agent import run_agent_pipeline

# Configure Streamlit page
st.set_page_config(
    page_title="Hiver AI Support Agent",
    page_icon="🤖",
    layout="centered"
)

st.title("Hiver AI Support Agent")
st.markdown("A prototype agent for analyzing and responding to AppleSupport customer queries.")

# Ensure GOOGLE_API_KEY is available (read from secrets if possible)
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except:
    pass

message = st.text_area("Enter a customer support message", height=150, placeholder="e.g. @AppleSupport My iPhone is so slow after the latest iOS update!")

if st.button("Analyze", type="primary"):
    if not message.strip():
        st.warning("Please enter a customer message.")
    else:
        with st.spinner("Analyzing message and generating response..."):
            try:
                # Call the agent pipeline
                result = run_agent_pipeline(message)
                
                # Mode Indicator
                if result.get("gemini_active"):
                    st.success("⚡ **Gemini Mode Active**")
                else:
                    st.warning("⚠️ **Local Fallback Mode Active**")

                # Display Results
                st.subheader("Agent Analysis")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Predicted Intent", result["predicted_intent"])
                with col2:
                    st.metric("Confidence", f"{result['intent_confidence']:.2%}")
                
                # Decision styling
                decision = result["decision"]
                decision_color = "green" if decision == "AUTO_HANDLE" else "red"
                st.markdown(f"**Decision:** :{decision_color}[{decision}]")
                
                # Reason logic (Intent Reason or Escalation Reason depending on what drove the decision, but we show both or just the relevant one)
                # We'll show the intent reason first, then the escalation reason
                st.markdown(f"**Intent Reason:** {result.get('intent_reason', '')}")
                st.markdown(f"**Escalation Reason:** {result.get('escalation_reason', '')}")
                
                st.subheader("Draft Reply")
                st.info(result["draft_reply"])
                
                st.subheader("Historical Evidence")
                with st.expander("View Retrieved Cases"):
                    st.text(result["evidence_text"])
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
