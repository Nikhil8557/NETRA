# backend/app/mo_matcher.py
import asyncio
import logging
from typing import Set, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from ksp_netra_ingestion.schemas_api import MOSimilarityResult

logger = logging.getLogger("ksp_netra.mo_matcher")

class ModusOperandiMatcher:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def compute_jaccard_similarity(self, set_a: Set[str], set_b: Set[str]) -> float:
        norm_a = {tag.strip().lower() for tag in set_a}
        norm_b = {tag.strip().lower() for tag in set_b}
        
        intersection = norm_a.intersection(norm_b)
        union = norm_a.union(norm_b)
        return float(len(intersection)) / len(union) if union else 0.0

    def _rank_offenders_sync(self, active_case_mo: Set[str], known_offenders: List[Dict[str, Any]], similarity_threshold: float) -> List[MOSimilarityResult]:
        results = []
        for profile in known_offenders:
            offender_mo = set(profile.get("modus_operandi_tags", []))
            score = self.compute_jaccard_similarity(active_case_mo, offender_mo)
            
            if score >= similarity_threshold:
                norm_active = {t.strip().lower() for t in active_case_mo}
                norm_offender = {t.strip().lower() for t in offender_mo}
                
                results.append(MOSimilarityResult(
                    offender_id=profile.get("offender_id", "UNKNOWN"),
                    full_name=profile.get("full_name", "Unknown Suspect"),
                    jaccard_score=round(score, 3),
                    matching_tags=list(norm_active.intersection(norm_offender)),
                    non_matching_tags=list(norm_offender.difference(norm_active))
                ))
                
        results.sort(key=lambda x: x.jaccard_score, reverse=True)
        return results

    async def find_top_matches(self, active_case_mo: Set[str], known_offenders: List[Dict[str, Any]], similarity_threshold: float = 0.5):
        if not active_case_mo:
            return []
            
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._rank_offenders_sync, 
            active_case_mo, 
            known_offenders, 
            similarity_threshold
        )
