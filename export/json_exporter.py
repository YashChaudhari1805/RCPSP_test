import json
from pathlib import Path
from datetime import datetime
import logging

from models import SolverResults, ProjectData
from utils import now_stamp, safe_mkdir
from config import OutputConfig

logger = logging.getLogger(__name__)


class JSONExporter:
    """Exports results to JSON format."""
    
    def __init__(self, config: OutputConfig = None):
        self.config = config or OutputConfig()
    
    def export(
        self,
        results: SolverResults,
        data: ProjectData,
        output_dir: Path,
        timestamp: str = None
    ) -> str:
        """Export results to JSON file."""
        timestamp = timestamp or now_stamp()
        safe_mkdir(output_dir)
        
        # Fix: Use config prefix
        filename = f"{self.config.JSON_PREFIX}_{timestamp}.json"
        filepath = output_dir / filename
        
        schedule_data = {
            activity.activity_id: {
                "start": activity.start,
                "duration": activity.duration,
                "finish": activity.finish
            }
            for activity in results.get_scheduled_activities(exclude_dummies=True)
        }
        
        payload = {
            "timestamp": datetime.now().isoformat(),
            "makespan": results.makespan,
            "cpu_time_seconds": round(results.cpu_time, 6),
            "wall_time_seconds": round(results.wall_time, 6),
            "build_time_seconds": round(results.build_time, 6),
            "num_activities": len(schedule_data),
            "num_resources": len(data.resources),
            "num_precedence_relations": len(data.precedence),
            "schedule": schedule_data
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        
        logger.info(f"JSON summary saved: {filepath}")
        print(f"✓ JSON summary saved: {filepath}")
        
        return str(filepath)