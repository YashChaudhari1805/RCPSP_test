import pandas as pd
from pathlib import Path
import numpy as np
import logging

from models import SolverResults, ProjectData
from utils import now_stamp, safe_mkdir
from config import OutputConfig

logger = logging.getLogger(__name__)


class ExcelExporter:
    """Exports results to Excel format."""
    
    def __init__(self, config: OutputConfig = None):
        # Fix: Accept config
        self.config = config or OutputConfig()
    
    def export(
        self,
        results: SolverResults,
        data: ProjectData,
        output_dir: Path,
        timestamp: str = None
    ) -> str:
        """Export results to Excel file."""
        timestamp = timestamp or now_stamp()
        safe_mkdir(output_dir)
        
        # Fix: Use prefix from config
        filename = f"{self.config.EXCEL_PREFIX}_{timestamp}.xlsx"
        filepath = output_dir / filename
        
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            self._write_schedule_sheet(results, data, writer)
            self._write_utilization_sheet(results, data, writer)
            self._write_metadata_sheet(results, data, writer)
        
        logger.info(f"Excel report saved: {filepath}")
        print(f"✓ Excel report saved: {filepath}")
        
        return str(filepath)
    
    def _write_schedule_sheet(self, results, data, writer):
        """Write schedule to Excel sheet."""
        rows = []
        
        for activity in results.get_scheduled_activities(exclude_dummies=True):
            # Get resources used
            resources_used = []
            for resource_id, usage in data.resource_usage.get(activity.activity_id, {}).items():
                if usage > 0:
                    resources_used.append(f"{resource_id}:{usage}")
            
            rows.append({
                "Activity": activity.activity_id,
                "Duration": activity.duration,
                "Start": activity.start,
                "Finish": activity.finish,
                "Resources": ", ".join(resources_used)
            })
        
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name="Schedule", index=False)
    
    def _write_utilization_sheet(self, results, data, writer):
        """Write resource utilization to Excel sheet."""
        rows = []
        renewable_resources = data.get_renewable_resources()
        
        makespan = max(int(results.makespan), 1)
        time_points = list(range(makespan + 1))
        
        for resource_id, resource in renewable_resources.items():
            utilization = []
            
            for t in time_points:
                usage = 0
                for activity in results.schedule.values():
                    if activity.activity_id in ["0", "N"]:
                        continue
                    if activity.start <= t < activity.finish:
                        usage += data.resource_usage.get(activity.activity_id, {}).get(resource_id, 0)
                utilization.append(usage)
            
            rows.append({
                "Resource": resource_id,
                "Capacity": resource.capacity,
                "Peak_Utilization": max(utilization) if utilization else 0,
                "Avg_Utilization": float(np.mean(utilization)) if utilization else 0.0
            })
        
        df = pd.DataFrame(rows)
        df.to_excel(writer, sheet_name="Resource_Utilization", index=False)
    
    def _write_metadata_sheet(self, results, data, writer):
        """Write metadata to Excel sheet."""
        activities = [a for aid, a in data.activities.items() if aid not in ["0", "N"]]
        
        metadata = [
            {"Metric": "Makespan", "Value": results.makespan},
            {"Metric": "CPU Time (s)", "Value": f"{results.cpu_time:.6f}"},
            {"Metric": "Wall Time (s)", "Value": f"{results.wall_time:.6f}"},
            {"Metric": "Build Time (s)", "Value": f"{results.build_time:.6f}"},
            {"Metric": "Activities (excl. 0,N)", "Value": len(activities)},
            {"Metric": "Renewable Resources", "Value": len(data.get_renewable_resources())},
            {"Metric": "NonRenewable Resources", "Value": len(data.get_non_renewable_resources())},
            {"Metric": "Precedence Relations", "Value": len(data.precedence)},
        ]
        
        df = pd.DataFrame(metadata)
        df.to_excel(writer, sheet_name="Metadata", index=False)