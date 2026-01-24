import argparse
import sys
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from input import ExcelDataLoader
from validation import DataValidator
from solver import RCPSPSolver
from orchestration import RCPSPOrchestrator
from config import ModelConfig, OutputConfig, VisualizationConfig
from utils.logging_utils import setup_logging

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="RCPSP MILP Solver - Industrial Version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m cli.main --excel data/project.xlsx
  python -m cli.main --excel data/project.xlsx --output ./results --time_limit 600
        """
    )
    
    parser.add_argument(
        "--excel",
        type=str,
        required=True,
        help="Path to input Excel file"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="./output",
        help="Base output directory (default: ./output)"
    )
    
    parser.add_argument(
        "--time_limit",
        type=int,
        default=300,
        help="Solver time limit in seconds (default: 300)"
    )
    
    parser.add_argument(
        "--tasks_per_page",
        type=int,
        default=60,
        help="Number of tasks per Gantt chart page (default: 60)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for CLI."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging()
    
    # Validate input file exists
    excel_path = Path(args.excel)
    if not excel_path.exists():
        print(f"ERROR: Excel file not found: {excel_path}")
        sys.exit(1)
    
    # Initialize configurations with CLI arguments
    # Fix: Ensure CLI args override defaults in the config objects
    model_config = ModelConfig(DEFAULT_TIME_LIMIT=args.time_limit)
    output_config = OutputConfig(BASE_DIR=Path(args.output))
    viz_config = VisualizationConfig(TASKS_PER_PAGE=args.tasks_per_page)
    
    # Initialize components
    # Fix: Pass model_config to data loader so parsing settings are consistent
    data_loader = ExcelDataLoader(config=model_config)
    validator = DataValidator()
    solver = RCPSPSolver(config=model_config, time_limit=args.time_limit)
    
    # Create orchestrator
    # Fix: Pass output and visualization configs so they propagate to sub-components
    orchestrator = RCPSPOrchestrator(
        data_loader=data_loader,
        validator=validator,
        solver=solver,
        output_config=output_config,
        visualization_config=viz_config
    )
    
    # Run optimization
    result = orchestrator.run(str(excel_path))
    
    # Exit with appropriate code
    if result.success:
        sys.exit(0)
    else:
        print(f"\n✗ Failed: {result.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()