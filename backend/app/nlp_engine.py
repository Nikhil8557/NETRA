# backend/app/nlp_engine.py
import re
import logging
from typing import Dict, Any, List, Tuple, Optional
import spacy
from rapidfuzz import distance

try:
    from metaphone import doublemetaphone
except ImportError:
    def doublemetaphone(word: str) -> Tuple[str, str]:
        cleaned = "".join([c for c in word.upper() if c.isalnum()])
        consonants = "".join([c for c in cleaned if c not in "AEIOU"])
        return (consonants[:4], consonants[1:5] if len(consonants) > 1 else "")

logger = logging.getLogger("ksp_netra.nlp_engine")

class KSPNLPEngine:
    def __init__(self, model_name: str = "en_core_web_sm"):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            logger.warning(f"spaCy package '{model_name}' missing. Initiating download pipeline...")
            spacy.cli.download(model_name)
            self.nlp = spacy.load(model_name)
            
        # Refined regex matching patterns for Indian licenses, mobile numbers, and sections of law
        self.vehicle_regex = re.compile(r'\b[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z]{1,3}[-\s]?\d{4}\b', re.IGNORECASE)
        self.contact_regex = re.compile(r'\b(?:(?:\+|0{0,2})91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b')
        self.section_regex = re.compile(
            r'\b(?:Sec(?:tion)?\.?\s*\d+(?:\s*[A-Z])?\s*(?:of)?\s*(?:IPC|BNS|CrPC|IEA|NDPS|POCSO|KPF?A))\b', 
            re.IGNORECASE
        )
        self.mo_vocab = [
            "theft", "housebreaking", "chain snatching", "cyber fraud", "phishing",
            "kidnapping", "homicide", "extortion", "dacoity", "shoplifting", "break-in"
        ]

    def extract_entities(self, text: str) -> Dict[str, Any]:
        doc = self.nlp(text)
        persons = list(set([ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]))
        vehicles = list(set([match.group().upper().replace(" ", "-") for match in self.vehicle_regex.finditer(text)]))
        contacts = list(set([re.sub(r'[\s-]', '', match.group()) for match in self.contact_regex.finditer(text)]))
        sections = list(set([match.group().strip() for match in self.section_regex.finditer(text)]))
        
        lower_text = text.lower()
        mo_detected = [word.upper() for word in self.mo_vocab if word in lower_text]
        return {
            "persons": persons,
            "vehicles": vehicles,
            "contacts": contacts,
            "sections_of_law": sections,
            "modus_operandi": list(set(mo_detected))
        }

class EntityResolver:
    def __init__(self, auto_merge_threshold: float = 0.85, manual_review_threshold: float = 0.60):
        self.auto_merge_threshold = auto_merge_threshold
        self.manual_review_threshold = manual_review_threshold

    def _decode_phoneme(self, val: Any) -> str:
        if val is None:
            return ""
        if isinstance(val, bytes):
            return val.decode("utf-8")
        return str(val)

    def calculate_phonetic_similarity(self, s1: str, s2: str) -> float:
        """
        Combines double metaphone algorithms with the JaroWinkler metric for phoneme matches.
        """
        p1_prim, p1_alt = doublemetaphone(s1)
        p2_prim, p2_alt = doublemetaphone(s2)
        
        p1_p, p1_a = self._decode_phoneme(p1_prim), self._decode_phoneme(p1_alt or p1_prim)
        p2_p, p2_a = self._decode_phoneme(p2_prim), self._decode_phoneme(p2_alt or p2_prim)
        
        sim1 = distance.JaroWinkler.normalized_similarity(p1_p, p2_p)
        sim2 = distance.JaroWinkler.normalized_similarity(p1_a, p2_a)
        return max(sim1, sim2)

    def resolve_suspect(self, target: Dict[str, Any], registry: List[Dict[str, Any]]) -> Tuple[str, float, Optional[str]]:
        target_phone = target.get("phone")
        target_name = target.get("full_name", "").strip().lower()
        
        # 1. Deterministic Pass
        for item in registry:
            if target_phone and item.get("phone") == target_phone:
                return "AUTO_MERGE", 1.0, item["ksp_guid"]
            if target_name and item.get("full_name", "").strip().lower() == target_name:
                if target.get("father_name") and item.get("father_name") == target.get("father_name"):
                    return "AUTO_MERGE", 1.0, item["ksp_guid"]
                    
        # 2. Probabilistic Pass
        best_score = 0.0
        matched_guid = None
        for item in registry:
            name_sim = self.calculate_phonetic_similarity(target.get("full_name", ""), item.get("full_name", ""))
            
            father_sim = name_sim
            if target.get("father_name") and item.get("father_name"):
                father_sim = self.calculate_phonetic_similarity(target["father_name"], item["father_name"])
                
            addr_sim = name_sim
            if target.get("address") and item.get("address"):
                addr_sim = distance.JaroWinkler.normalized_similarity(target["address"].lower(), item["address"].lower())
                
            score = (name_sim * 0.50) + (father_sim * 0.30) + (addr_sim * 0.20)
            if score > best_score:
                best_score = score
                matched_guid = item["ksp_guid"]
                
        if best_score >= self.auto_merge_threshold:
            return "AUTO_MERGE", round(best_score, 3), matched_guid
        if best_score >= self.manual_review_threshold:
            return "MANUAL_REVIEW_QUEUE", round(best_score, 3), matched_guid
        return "CREATE_NEW", round(best_score, 3), None
