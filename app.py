import streamlit as st
import logging
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aegis.config import settings
from aegis.qa import QuestionAnswerService

# Page Configuration
st.set_page_config(
    page_title="Aegis Series-7 HCS — Knowledge Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "history" not in st.session_state:
    st.session_state.history = []
if "question_input" not in st.session_state:
    st.session_state.question_input = ""
if "current_question" not in st.session_state:
    st.session_state.current_question = ""

# Dependency Setup
@st.cache_resource
def get_qa_service():
    engine = create_engine(settings.db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    return QuestionAnswerService(session)

try:
    service = get_qa_service()
except Exception as e:
    st.error("Failed to connect to the knowledge base.")
    st.stop()

# Layout: Title & Header
st.title("Aegis Series-7 HCS")
st.header("Knowledge Assistant")
st.markdown("Evidence-grounded technical QA with deterministic verification and provenance.")
st.markdown("---")

# Layout: Sidebar (Examples & History)
with st.sidebar:
    st.subheader("Example questions")
    
    examples = [
        "What is the current normal operating pressure for the HPU?",
        "Is PS-04 the same component as PS-04A?",
        "Is PS-04 the same as PS-40?",
        "What is the maximum continuous operating temperature of PS-04A?",
        "What is the mean time between failures for IV-21?",
        "Is the Aegis Series-7 HCS compatible with a 3-phase 400V supply?"
    ]
    
    for ex in examples:
        if st.button(ex, key=ex):
            st.session_state.question_input = ex
            st.session_state.current_question = ex

    st.markdown("---")
    st.subheader("Session History")
    
    for item in reversed(st.session_state.history):
        st.markdown(f"**Q:** {item['question']}")
        st.caption(f"{item['decision']} — {item['short_answer']}")
        st.markdown("---")


# Layout: Main Input area
def submit_question():
    st.session_state.current_question = st.session_state.question_input

st.text_input("Ask a question about the supplied technical documentation:", 
              key="question_input", 
              on_change=submit_question)

if st.button("Ask Aegis"):
    submit_question()

# Display Results
if st.session_state.current_question:
    question = st.session_state.current_question
    
    try:
        with st.spinner("Analyzing query and verifying evidence..."):
            answer, rr = service.answer_question(question)
        
        # Display Decision Box
        decision_val = rr.decision.value
        if decision_val == "VERIFIED":
            st.success("✅ **VERIFIED**: Verified from supplied documentation")
        elif decision_val == "CONFLICTED":
            st.warning("⚠️ **CONFLICTED**: Conflicting evidence found in the supplied documentation.")
        elif decision_val == "INSUFFICIENT_EVIDENCE":
            st.error("❌ **INSUFFICIENT_EVIDENCE**: Insufficient verified evidence in the supplied documentation.")
        elif decision_val == "NOT_APPLICABLE":
            st.info("ℹ️ **NOT_APPLICABLE**: The retrieved evidence does not apply to the requested context.")
        
        st.markdown("### ANSWER")
        st.write(answer.text)
        st.markdown("---")
        
        st.markdown("### EVIDENCE / PROVENANCE")
        
        if answer.claims:
            for i, claim in enumerate(answer.claims):
                with st.container():
                    st.markdown(f"**Claim:**\n{claim.text}")
                    st.markdown(f"**Claim type:**\n{claim.claim_type.value}")
                    
                    if claim.evidence_ids:
                        for idx, eid in enumerate(claim.evidence_ids):
                            # Find the exact Evidence record inside rr.verified_evidence
                            ev = next((e for e in rr.verified_evidence if e.evidence_id == eid), None)
                            if ev:
                                st.markdown(f"#### Evidence #{idx+1}")
                                st.markdown(f"**Subject:** {ev.subject}")
                                st.markdown(f"**Predicate:** {ev.predicate}")
                                val_unit = f"{ev.value}" + (f" {ev.unit}" if ev.unit else "")
                                st.markdown(f"**Value:** {val_unit}")
                                
                                # Use filename instead of ID
                                filename = getattr(ev, 'document_filename', ev.document_id)
                                st.markdown(f"**Source filename:** {filename}")
                                st.markdown(f"**Document location:** {ev.document_location}")
                                
                                val_str = "None"
                                if ev.validity_info:
                                    vmin = ev.validity_info.get('fw_version_min')
                                    vmax = ev.validity_info.get('fw_version_max')
                                    if vmin and vmax: val_str = f"FW {vmin} to {vmax}"
                                    elif vmin: val_str = f"FW >= {vmin}"
                                    elif vmax: val_str = f"FW <= {vmax}"
                                st.markdown(f"**Applicability / firmware validity:** {val_str}")
                                
                                st.markdown(f"**Authority:** {getattr(ev, 'source_authority', 'OFFICIAL')}") 
                                st.markdown(f"**Extraction method:** {ev.extraction_method}")
                                st.markdown(f"**Reliability:** {ev.extraction_reliability}")
                                
                                with st.expander("Technical provenance"):
                                    st.markdown(f"**Evidence ID:** `{eid}`")
                                    st.markdown(f"**Document ID:** `{ev.document_id}`")
                    st.divider()
        else:
            st.write("No claims generated.")
        
        # Debug Details
        with st.expander("🔍 Debug / Verification Details"):
            st.markdown("**Query Analysis**")
            st.json(rr.query_analysis.model_dump())
            
            st.markdown("**Retrieval Candidates**")
            cands = []
            for c in rr.candidates:
                c_dict = c.model_dump()
                if not c_dict.get('fact_id'): c_dict.pop('fact_id', None)
                if not c_dict.get('relation_id'): c_dict.pop('relation_id', None)
                cands.append(c_dict)
            st.json(cands)
            
            st.markdown("**Verification Decision**")
            st.write(rr.decision.value)
            
            if decision_val == "CONFLICTED":
                st.markdown("**Conflict Information**")
                # Just show the claims since conflict reasoning isn't easily accessible here without ORM
                for c in answer.claims:
                    if c.claim_type.value == "CONFLICT":
                        st.write(c.text)
            
            st.markdown("**Claim Validation Result**")
            st.write("Validation Passed" if not answer.is_fallback else "Deterministic Fallback Used")
        
        # Update History
        # Ensure we don't add duplicates consecutively or add on every re-render
        if not st.session_state.history or st.session_state.history[-1]['question'] != question:
            st.session_state.history.append({
                "question": question,
                "decision": decision_val,
                "short_answer": answer.text.split('\n')[0][:100] + "..." if len(answer.text) > 100 else answer.text
            })
            
    except Exception as e:
        logging.error(f"QA Service Error: {str(e)}\n{traceback.format_exc()}")
        st.error("An internal error occurred while processing the request. Please check the logs.")

