import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from matplotlib.ticker import MaxNLocator
import logging
from typing import List

from models import SolverResults, ProjectData
from config import VisualizationConfig, OutputConfig
from .data_transformer import VisualizationDataTransformer
from utils import now_stamp, safe_mkdir

logger = logging.getLogger(__name__)


class GanttChartRenderer:
    """Renders Gantt charts with pagination."""
    
    def __init__(self, viz_config: VisualizationConfig = None, output_config: OutputConfig = None):
        # Fix: Accept both configs
        self.config = viz_config or VisualizationConfig()
        self.output_config = output_config or OutputConfig()
        self.transformer = VisualizationDataTransformer()
    
    def render(
        self,
        results: SolverResults,
        data: ProjectData,
        output_dir: Path,
        timestamp: str = None
    ) -> List[str]:
        """
        Render paginated Gantt charts.
        
        Returns:
            List of file paths to generated charts
        """
        timestamp = timestamp or now_stamp()
        safe_mkdir(output_dir)
        
        sorted_activities = self.transformer.get_sorted_activities_for_gantt(results)
        
        if not sorted_activities:
            logger.warning("No activities to plot in Gantt chart")
            return []
        
        makespan = self._calculate_display_makespan(results, sorted_activities)
        pages = self._paginate_activities(sorted_activities)
        
        file_paths = []
        for page_num, page_activities in enumerate(pages, start=1):
            filepath = self._render_page(
                page_activities,
                makespan,
                page_num,
                len(pages),
                output_dir,
                timestamp
            )
            file_paths.append(filepath)
        
        return file_paths
    
    def _calculate_display_makespan(self, results, sorted_activities) -> int:
        """Calculate makespan for display purposes."""
        makespan_from_results = int(results.makespan)
        makespan_from_schedule = max(
            (activity.finish for _, activity in sorted_activities),
            default=0
        )
        return max(makespan_from_results, makespan_from_schedule, 1)
    
    def _paginate_activities(self, activities):
        """Split activities into pages."""
        pages = []
        total = len(activities)
        tasks_per_page = self.config.TASKS_PER_PAGE
        
        for i in range(0, total, tasks_per_page):
            pages.append(activities[i:i + tasks_per_page])
        
        return pages
    
    def _render_page(
        self,
        page_activities,
        makespan: int,
        page_num: int,
        total_pages: int,
        output_dir: Path,
        timestamp: str
    ) -> str:
        """Render a single page of Gantt chart."""
        n = len(page_activities)
        
        # Calculate figure size
        fig_height = max(
            self.config.MIN_FIGURE_HEIGHT,
            min(0.35 * n + 2, self.config.MAX_FIGURE_HEIGHT)
        )
        
        fig, ax = plt.subplots(figsize=(self.config.FIGURE_WIDTH, fig_height))
        
        # Extract data
        y_positions = np.arange(n)
        starts = [activity.start for _, activity in page_activities]
        durations = [activity.duration for _, activity in page_activities]
        labels = [activity_id for activity_id, _ in page_activities]
        
        # Color mapping
        cmap = plt.cm.tab20
        colors = [cmap(i % 20) for i in range(n)]
        
        # Draw bars
        ax.barh(
            y_positions,
            durations,
            left=starts,
            height=self.config.BAR_HEIGHT,
            color=colors,
            edgecolor="black",
            linewidth=self.config.BAR_EDGE_WIDTH
        )
        
        # Add labels if not too dense
        if n <= self.config.MAX_TASKS_FOR_LABELS:
            for i, (label, start, duration) in enumerate(zip(labels, starts, durations)):
                if duration >= 1:
                    ax.text(
                        start + duration / 2, i, label,
                        ha="center", va="center",
                        fontsize=8, weight="bold", color="black"
                    )
                else:
                    ax.text(
                        start + duration + 0.2, i, label,
                        ha="left", va="center",
                        fontsize=8, color="black"
                    )
        
        # Configure axes
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
        
        ax.set_xlim(0, makespan + max(1, int(0.02 * makespan)))
        ax.set_xlabel("Time", fontsize=11, weight="bold")
        ax.set_ylabel("Activity", fontsize=11, weight="bold")
        ax.set_title(
            f"RCPSP Gantt Chart (Makespan={makespan}) — Page {page_num}/{total_pages}",
            fontsize=13,
            weight="bold",
            pad=12
        )
        
        # Configure grid and ticks
        locator = self._get_tick_locator(makespan)
        ax.xaxis.set_major_locator(locator)
        ax.grid(True, axis="x", linestyle="--", alpha=self.config.GRID_ALPHA)
        ax.set_axisbelow(True)
        
        # Adjust layout
        ax.margins(x=0.01, y=0.02)
        plt.subplots_adjust(left=0.22, right=0.98, top=0.90, bottom=0.10)
        
        # Save
        # Fix: Use filename from config
        filename = f"{self.output_config.GANTT_PREFIX}_{timestamp}_P{page_num}.png"
        filepath = output_dir / filename
        plt.savefig(filepath, dpi=self.config.GANTT_DPI, facecolor="white")
        plt.close(fig)
        
        logger.info(f"Gantt chart page {page_num} saved: {filepath}")
        print(f"✓ Gantt chart page {page_num} saved: {filepath}")
        
        return str(filepath)
    
    @staticmethod
    def _get_tick_locator(makespan: int):
        """Get appropriate tick locator based on makespan."""
        if makespan <= 50:
            return MaxNLocator(nbins=10, integer=True)
        elif makespan <= 200:
            return MaxNLocator(nbins=12, integer=True)
        elif makespan <= 1000:
            return MaxNLocator(nbins=14, integer=True)
        else:
            return MaxNLocator(nbins=16, integer=True)