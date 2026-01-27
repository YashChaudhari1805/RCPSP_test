"""
Enhanced PSPLIB Parser with proper integration
"""
import pandas as pd
from typing import Dict, List, Tuple, Set
import logging

from models import ProjectData, Activity, Resource, ResourceType
from config import ModelConfig

logger = logging.getLogger(__name__)


class PSPLibParser:
    """Parses PSPLIB Excel format."""
    
    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig()
    
    def parse(self, filepath: str, sheet_names: Set[str]) -> ProjectData:
        """Parse PSPLIB format Excel file."""
        
        logger.info("Parsing PSPLIB format Excel file")
        
        try:
            # Load sheets
            resource_df = self._load_sheet(filepath, "Resource Avail")
            requests_df = self._load_sheet(filepath, "Requests")
            precedence_df = self._load_sheet(filepath, "Precedence")
            
            logger.info(f"Loaded sheets - Resources: {resource_df.shape}, Requests: {requests_df.shape}, Precedence: {precedence_df.shape}")
            
            # Parse components
            resources = self._parse_resources(resource_df)
            activities, resource_usage = self._parse_requests(requests_df, resources)
            precedence = self._parse_precedence(precedence_df)
            
            # Remap dummies
            activities, resource_usage, precedence = self._remap_dummies(
                activities, resource_usage, precedence
            )
            
            logger.info(f"Parsed {len(activities)} activities, {len(resources)} resources, {len(precedence)} precedence relations")
            
            return ProjectData(
                activities=activities,
                resources=resources,
                precedence=precedence,
                resource_usage=resource_usage
            )
            
        except Exception as e:
            logger.error(f"Failed to parse PSPLIB file: {e}")
            raise ValueError(f"Failed to parse PSPLIB Excel file: {e}")
    
    @staticmethod
    def _load_sheet(filepath: str, sheet_name: str) -> pd.DataFrame:
        """Load and normalize sheet."""
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    
    @staticmethod
    def _parse_resources(df: pd.DataFrame) -> Dict[str, Resource]:
        """Parse resources from Resource Avail sheet."""
        resources = {}
        
        # Columns like "R1 Available", "R2 Available"
        for col in df.columns:
            if "Available" in col:
                res_id = col.replace("Available", "").strip()
                capacity = int(df.iloc[0][col])
                resources[res_id] = Resource(
                    id=res_id,
                    capacity=capacity,
                    resource_type=ResourceType.RENEWABLE
                )
        
        logger.info(f"Parsed {len(resources)} resources")
        return resources
    
    @staticmethod
    def _parse_requests(df: pd.DataFrame, resources: Dict[str, Resource]) -> Tuple[Dict, Dict]:
        """Parse activities and resource usage from Requests sheet."""
        activities = {}
        usage = {}
        
        for _, row in df.iterrows():
            job_id = str(row["Job Nr"]).strip()
            duration = int(row["Duration"])
            
            activities[job_id] = Activity(id=job_id, duration=duration)
            
            # Parse resource usage
            act_usage = {}
            for res_id in resources.keys():
                if res_id in df.columns:
                    act_usage[res_id] = int(row[res_id])
                else:
                    act_usage[res_id] = 0
            usage[job_id] = act_usage
        
        logger.info(f"Parsed {len(activities)} activities with resource usage")
        return activities, usage
    
    @staticmethod
    def _parse_precedence(df: pd.DataFrame) -> List[Tuple[str, str]]:
        """Parse precedence from Precedence sheet."""
        precedence = []
        
        for _, row in df.iterrows():
            pred_id = str(row["Job Nr"]).strip()
            succ_str = str(row["Successors"]).strip()
            
            if succ_str and succ_str.lower() != "nan":
                # Handle comma-separated successors
                succ_ids = [s.strip() for s in succ_str.replace('"', '').split(',')]
                for succ_id in succ_ids:
                    if succ_id:
                        precedence.append((pred_id, succ_id))
        
        logger.info(f"Parsed {len(precedence)} precedence relations")
        return precedence
    
    def _remap_dummies(self, activities, usage, precedence):
        """Remap file's start/end to config's dummy IDs."""
        sorted_ids = sorted(activities.keys(), key=lambda x: int(x) if x.isdigit() else x)
        
        original_start = sorted_ids[0]
        original_end = sorted_ids[-1]
        
        # Check if already correct
        if original_start == self.config.DUMMY_START and original_end == self.config.DUMMY_END:
            return activities, usage, precedence
        
        mapping = {
            original_start: self.config.DUMMY_START,
            original_end: self.config.DUMMY_END
        }
        
        logger.info(f"Remapping dummies: {original_start}->{self.config.DUMMY_START}, {original_end}->{self.config.DUMMY_END}")
        
        # Remap activities
        new_activities = {}
        for aid, act in activities.items():
            new_id = mapping.get(aid, aid)
            new_act = Activity(id=new_id, duration=act.duration)
            new_activities[new_id] = new_act
        
        # Remap usage
        new_usage = {}
        for aid, u in usage.items():
            new_id = mapping.get(aid, aid)
            new_usage[new_id] = u
        
        # Remap precedence
        new_precedence = []
        for pred, succ in precedence:
            new_pred = mapping.get(pred, pred)
            new_succ = mapping.get(succ, succ)
            new_precedence.append((new_pred, new_succ))
        
        return new_activities, new_usage, new_precedence