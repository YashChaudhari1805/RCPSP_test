from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ScheduledActivity:
    """Represents a scheduled activity with timing information."""
    
    activity_id: str
    start: int
    duration: int
    finish: int
    
    @classmethod
    def from_dict(cls, activity_id: str, data: dict) -> 'ScheduledActivity':
        """Create from dictionary format."""
        return cls(
            activity_id=activity_id,
            start=data['Start'],
            duration=data['Duration'],
            finish=data['Finish']
        )

@dataclass
class SolverResults:
    """Results from RCPSP solver."""
    
    makespan: int
    schedule: Dict[str, ScheduledActivity]
    cpu_time: float
    wall_time: float
    build_time: float
    status: str
    
    def is_optimal(self) -> bool:
        """Check if solution is optimal."""
        return self.status == "Optimal"

    def is_feasible(self) -> bool:
        """Check if solution is feasible (but maybe not optimal)."""
        return self.status.startswith("Feasible")
    
    def is_success(self) -> bool:
        """Check if solver succeeded (Optimal or Feasible)."""
        return self.is_optimal() or self.is_feasible()
    
    def get_scheduled_activities(self, exclude_dummies: bool = True) -> List[ScheduledActivity]:
        """Get list of scheduled activities, optionally excluding dummies."""
        activities = list(self.schedule.values())
        if exclude_dummies:
            activities = [a for a in activities if a.activity_id not in ["0", "N"]]
        return sorted(activities, key=lambda x: (x.start, x.activity_id))

@dataclass
class ValidationResult:
    """Result of data validation."""
    
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0