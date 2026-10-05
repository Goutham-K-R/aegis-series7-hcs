import re
import sys
import os
from typing import List

# Import scripts path safely
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts')))
from resolve_entities import normalize_name, AMBIGUOUS_NAMES
from .models import QueryAnalysis

class QueryAnalyzer:
    def analyze(self, query: str) -> QueryAnalysis:
        text_lower = query.lower()
        qa = QueryAnalysis(original_query=query, normalized_query=text_lower)
        
        # Entity extraction
        potential_entities = [
            "ps-04a", "ps-04", "ps-40", "p04a", "p04", "ps04a", "ps04",
            "iv-21", "iv21", "hpu", "hydraulic power unit",
            "plc-03", "controller", "pressure xdcr",
            "a17", "a18", "a19", "ecn-1042", "ecn-1058", "t1", "q1"
        ]
        
        found_entities = []
        for ent in potential_entities:
            # use regex word boundary, handle dashes
            pattern = r'\b' + re.escape(ent) + r'\b'
            if re.search(pattern, text_lower):
                # check if ambiguous
                if ent.upper() in AMBIGUOUS_NAMES:
                    qa.ambiguity_indicators.append(ent.upper())
                    found_entities.append(ent.upper())
                else:
                    norm = normalize_name(ent.upper())
                    found_entities.append(norm if norm else ent.upper())
                    
        qa.entities = list(set(found_entities))
        
        # Extract firmware context: "for firmware 3.2.1", "on firmware 3.1", "fw 3.2", "before firmware 3.2"
        fw_match = re.search(r'(?:firmware|fw|software revision|revision)\s*(\d+(?:\.\d+)*)', text_lower)
        if fw_match:
            fw = fw_match.group(1)
            if re.search(r'before\s+(?:firmware|fw|software revision|revision)\s*' + re.escape(fw), text_lower):
                parts = fw.split('.')
                prev = int(parts[-1]) - 1
                fw = '.'.join(parts[:-1] + [str(prev)]) if len(parts) > 1 else str(int(parts[0])-1)
            qa.firmware_context = fw
            
        # Predicates mapping
        if "maximum pressure" in text_lower or "pressure limit" in text_lower:
            qa.requested_predicate = "maximum_pressure"
        elif "temperature" in text_lower:
            qa.requested_predicate = "maximum_continuous_temperature"
        elif "mtbf" in text_lower:
            qa.requested_predicate = "mtbf"
        elif "voltage" in text_lower or "400 v" in text_lower or "480 v" in text_lower or "400v" in text_lower or "480v" in text_lower:
            if "compatibility" in text_lower or "compatible" in text_lower or "400" in text_lower:
                qa.requested_predicate = "voltage_compatibility"
            else:
                qa.requested_predicate = "voltage_rating"
        elif "alarm" in text_lower or "a17" in text_lower or "a18" in text_lower or "a19" in text_lower:
            qa.requested_predicate = "alarm_condition"
        
        if "connection" in text_lower or "connected" in text_lower:
            qa.relation_type = "ELECTRICALLY_CONNECTED_TO"
            
        return qa
