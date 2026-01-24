import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import logging

from models import SolverResults, ProjectData
from config import VisualizationConfig, OutputConfig
from .data_transformer import VisualizationDataTransformer
from utils import now_stamp, safe_mkdir

logger = logging.getLogger(__name__)


class ResourceUtilizationRenderer:
    """Renders resource utilization charts."""
    
    def __init__(self, viz_config: VisualizationConfig = None, output_config: OutputConfig = None):
        self.config = viz_config or VisualizationConfig()
        self.output_config = output_config or OutputConfig()
        self.transformer = VisualizationDataTransformer()
    
    def render(
        self,
        results: SolverResults,
        data: ProjectData,
        output_dir: Path,
        timestamp: str = None
    ) -> str:
        """Render resource utilization chart."""
        timestamp = timestamp or now_stamp()
        safe_mkdir(output_dir)
        
        renewable_resources = data.get_renewable_resources()
        
        if not renewable_resources:
            logger.warning("No renewable resources to plot")
            return None
        
        makespan = max(int(results.makespan), 1)
        time_points = list(range(makespan + 1))
        
        num_resources = len(renewable_resources)
        fig, axes = plt.subplots(
            num_resources, 1,
            figsize=(14, 3 * num_resources),
            squeeze=False
        )
        
        for idx, (resource_id, resource) in enumerate(renewable_resources.items()):
            ax = axes[idx][0]
            
            utilization = self.transformer.calculate_resource_utilization(
                results, data, resource_id
            )
            
            # Plot utilization
            ax.fill_between(
                time_points, 0, utilization,
                alpha=self.config.FILL_ALPHA,
                color="steelblue",
                label="Usage"
            )
            
            # Plot capacity line
            ax.axhline(
                y=resource.capacity,
                color="red",
                linestyle="--",
                linewidth=2,
                label="Capacity"
            )
            
            # Configure axes
            ax.set_title(
                f"Resource {resource_id} Utilization (Capacity: {resource.capacity})",
                fontsize=11,
                weight="bold"
            )
            ax.set_xlabel("Time", fontsize=10)
            ax.set_ylabel("Usage", fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.legend(loc="upper right")
            ax.set_xlim(0, makespan)
            ax.set_ylim(0, max(resource.capacity * 1.1, max(utilization) * 1.1 if utilization else 1))
        
        plt.tight_layout()
        
        # Fix: Use filename from config
        filename = f"{self.output_config.RESOURCE_UTIL_PREFIX}_{timestamp}.png"
        filepath = output_dir / filename
        plt.savefig(filepath, dpi=self.config.CHART_DPI, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        
        logger.info(f"Resource utilization chart saved: {filepath}")
        print(f"✓ Resource utilization chart saved: {filepath}")
        
        return str(filepath)