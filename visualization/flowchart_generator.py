import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import numpy as np
from pathlib import Path
import logging

from utils import safe_mkdir
from config import OutputConfig

logger = logging.getLogger(__name__)


class FlowchartGenerator:
    """Generates program flowchart."""
    
    def __init__(self, config: OutputConfig = None):
        self.config = config or OutputConfig()
    
    def generate(self, output_dir: Path) -> str:
        """Generate and save program flowchart."""
        safe_mkdir(output_dir)
        
        fig, ax = plt.subplots(figsize=(12, 16))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 20)
        ax.axis("off")
        
        y_pos = 19
        
        # Start
        self._draw_box(ax, 3.5, y_pos, 3, 0.8, "START", "lightgreen", "ellipse")
        self._draw_arrow(ax, 5, y_pos, 5, y_pos - 0.8)
        y_pos -= 1.3
        
        # Generate Flowchart
        self._draw_box(ax, 3.5, y_pos, 3, 0.8, "Generate Flowchart", "plum")
        self._draw_arrow(ax, 5, y_pos, 5, y_pos - 0.8)
        y_pos -= 1.3
        
        # Load Excel
        self._draw_box(ax, 3.5, y_pos, 3, 0.8, "Load Excel Input", "lightblue")
        self._draw_arrow(ax, 5, y_pos, 5, y_pos - 0.8)
        y_pos -= 1.3
        
        # Validate
        self._draw_box(ax, 3.5, y_pos, 3, 0.8, "Validate Data\n(Cycles/IDs/Capacities)", "lightcoral")
        self._draw_arrow(ax, 5, y_pos, 5, y_pos - 0.8)
        y_pos -= 1.3
        
        # Valid decision
        self._draw_box(ax, 3, y_pos, 4, 1, "Valid?", "lightyellow", "diamond")
        self._draw_arrow(ax, 3, y_pos + 0.5, 1, y_pos + 0.5, "No")
        self._draw_arrow(ax, 5, y_pos, 5, y_pos - 1, "Yes")
        self._draw_box(ax, 0.2, y_pos + 0.2, 1.5, 0.6, "Exit", "salmon")
        y_pos -= 1.5
        
        # Build model
        self._draw_box(ax, 3.5, y_pos, 3, 0.8, "Build MILP Model\n(+ Cmax)", "lightblue")
        self._draw_arrow(ax, 5, y_pos, 5, y_pos - 0.8)
        y_pos -= 1.3
        
        # Solve
        self._draw_box(ax, 3.5, y_pos, 3, 0.8, "Solve (CBC)", "lightblue")
        self._draw_arrow(ax, 5, y_pos, 5, y_pos - 0.8)
        y_pos -= 1.3
        
        # Optimal decision
        self._draw_box(ax, 3, y_pos, 4, 1, "Optimal?", "lightyellow", "diamond")
        self._draw_arrow(ax, 3, y_pos + 0.5, 1, y_pos + 0.5, "No")
        self._draw_arrow(ax, 5, y_pos, 5, y_pos - 1, "Yes")
        self._draw_box(ax, 0.2, y_pos + 0.2, 1.5, 0.6, "Report Fail", "salmon")
        y_pos -= 1.5
        
        # Extract results
        self._draw_box(ax, 3.5, y_pos, 3, 0.8, "Extract Schedule\n+ Metrics", "lightblue")
        self._draw_arrow(ax, 5, y_pos, 5, y_pos - 0.8)
        y_pos -= 1.3
        
        # Create figures
        self._draw_box(ax, 3.5, y_pos, 3, 0.8, "Create Figures\n(Gantt paged)", "plum")
        self._draw_arrow(ax, 5, y_pos, 5, y_pos - 0.8)
        y_pos -= 1.3
        
        # Export
        self._draw_box(ax, 3.5, y_pos, 3, 0.8, "Export\nExcel/TXT/JSON", "plum")
        self._draw_arrow(ax, 5, y_pos, 5, y_pos - 0.8)
        y_pos -= 1.3
        
        # End
        self._draw_box(ax, 3.5, y_pos, 3, 0.8, "END", "lightgreen", "ellipse")
        
        plt.title("RCPSP Solver Program Flowchart", fontsize=16, weight="bold", pad=20)
        
        # Fix: Use filename from config
        filepath = output_dir / self.config.FLOWCHART_NAME
        plt.savefig(filepath, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        
        logger.info(f"Flowchart saved to {filepath}")
        print(f"✓ Flowchart saved: {filepath}")
        
        return str(filepath)
    
    @staticmethod
    def _draw_box(ax, x, y, width, height, text, color="lightblue", shape="rect"):
        """Draw a box on the axes."""
        if shape == "rect":
            box = Rectangle((x, y), width, height,
                          facecolor=color, edgecolor="black", linewidth=2)
            ax.add_patch(box)
        elif shape == "diamond":
            points = np.array([
                [x + width / 2, y + height],
                [x + width, y + height / 2],
                [x + width / 2, y],
                [x, y + height / 2]
            ])
            diamond = mpatches.Polygon(points, facecolor=color,
                                      edgecolor="black", linewidth=2)
            ax.add_patch(diamond)
        elif shape == "ellipse":
            ellipse = mpatches.Ellipse((x + width / 2, y + height / 2),
                                       width, height,
                                       facecolor=color, edgecolor="black", linewidth=2)
            ax.add_patch(ellipse)
        
        ax.text(x + width / 2, y + height / 2, text,
                ha="center", va="center", fontsize=9, weight="bold", wrap=True)
    
    @staticmethod
    def _draw_arrow(ax, x1, y1, x2, y2, label=""):
        """Draw an arrow."""
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=2, color="black"))
        if label:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mid_x + 0.3, mid_y, label, fontsize=8, weight="bold")