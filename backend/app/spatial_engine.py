# backend/app/spatial_engine.py
import asyncio
import logging
import numpy as np
from datetime import datetime
from sklearn.cluster import DBSCAN
from concurrent.futures import ThreadPoolExecutor
from ksp_netra_ingestion.schemas_api import HotspotCluster, SpikeAlert

logger = logging.getLogger("ksp_netra.spatial_engine")

class SpatiotemporalHotspotEngine:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.earth_radius_meters = 6371000.0

    def _execute_clustering(self, coordinates: np.ndarray, epsilon_meters: float, min_samples: int) -> np.ndarray:
        if coordinates.size == 0:
            return np.array([])
            
        epsilon_radians = epsilon_meters / self.earth_radius_meters
        coords_rad = np.radians(coordinates)
        
        # Deploy standard density-based spatial clustering matching radians projection
        db = DBSCAN(eps=epsilon_radians, min_samples=min_samples, metric='haversine')
        db.fit(coords_rad)
        return db.labels_

    async def run_spatial_clustering(self, coordinates: np.ndarray, epsilon_meters: float = 200.0, min_samples: int = 5):
        if coordinates.size == 0:
            return []
            
        loop = asyncio.get_running_loop()
        labels = await loop.run_in_executor(
            self.executor, 
            self._execute_clustering, 
            coordinates, 
            epsilon_meters, 
            min_samples
        )
        
        clusters = []
        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:
                continue
                
            indices = np.where(labels == label)[0]
            cluster_coords = coordinates[indices]
            
            centroid_lat = float(np.mean(cluster_coords[:, 0]))
            centroid_lon = float(np.mean(cluster_coords[:, 1]))
            
            lat_offsets = cluster_coords[:, 0] - centroid_lat
            lon_offsets = cluster_coords[:, 1] - centroid_lon
            approx_distances = np.sqrt(lat_offsets**2 + lon_offsets**2) * 111000.0
            max_radius = float(np.max(approx_distances)) if approx_distances.size > 0 else 0.0
            
            clusters.append(HotspotCluster(
                cluster_id=int(label),
                centroid_latitude=centroid_lat,
                centroid_longitude=centroid_lon,
                radius_meters=max_radius,
                incident_count=len(indices),
                incident_ids=[f"INCIDENT-REF-{idx}" for idx in indices]
            ))
        return clusters

    async def calculate_regional_z_score(
        self, 
        current_count: int, 
        historical_mean: float, 
        historical_std: float, 
        region_id: str = "REG-DEFAULT"
    ) -> SpikeAlert:
        if historical_std <= 0.0:
            z_score = 0.0
        else:
            z_score = (current_count - historical_mean) / historical_std
            
        return SpikeAlert(
            region_id=region_id,
            calculated_z_score=round(z_score, 3),
            trigger_pulse_alert=z_score >= 2.0,
            current_count=current_count,
            historical_mean=historical_mean,
            historical_std=historical_std,
            timestamp=datetime.utcnow()
        )
