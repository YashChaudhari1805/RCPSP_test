from pathlib import Path
from datetime import datetime
import logging

from models import SolverResults, ProjectData
from utils import now_stamp, safe_mkdir
from config import OutputConfig

logger = logging.getLogger(__name__)


class TextExporter:
    """Exports results to text format."""
    
    def __init__(self, config: OutputConfig = None):
        self.config = config or OutputConfig()
    
    def export(
        self,
        results: SolverResults,
        data: ProjectData,
        output_dir: Path,
        timestamp: str = None
    ) -> str:
        """Export results to text file."""
        timestamp = timestamp or now_stamp()
        safe_mkdir(output_dir)
        
        # Fix: Use config prefix
        filename = f"{self.config.TEXT_PREFIX}_{timestamp}.txt"
        filepath = output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            self._write_header(f, results)
            self._write_schedule(f, results)
        
        logger.info(f"Text report saved: {filepath}")
        print(f"✓ Text report saved: {filepath}")
        
        return str(filepath)
    
    @staticmethod
    def _write_header(f, results):
        """Write header section."""
        f.write("=" * 70 + "\n")
        f.write("RCPSP OPTIMIZATION RESULTS\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Makespan: {results.makespan}\n")
        f.write(f"CPU Time (s): {results.cpu_time:.6f}\n")
        f.write(f"Wall Time (s): {results.wall_time:.6f}\n")
        f.write(f"Build Time (s): {results.build_time:.6f}\n\n")
    
    @staticmethod
    def _write_schedule(f, results):
        """Write schedule section."""
        f.write("--- SCHEDULE ---\n")
        f.write(f"{'Activity':<15} {'Dur':<6} {'Start':<10} {'Finish':<10}\n")
        f.write("-" * 50 + "\n")
        
        for activity in results.get_scheduled_activities(exclude_dummies=True):
            f.write(
                f"{activity.activity_id:<15} "
                f"{activity.duration:<6} "
                f"{activity.start:<10} "
                f"{activity.finish:<10}\n"
            )