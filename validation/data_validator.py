import logging
from .interfaces import IDataValidator
from .cycle_detector import CycleDetector
from models import ProjectData, ValidationResult

logger = logging.getLogger(__name__)

class DataValidator(IDataValidator):
    """Validates project data for feasibility."""
    
    def __init__(self):
        self.cycle_detector = CycleDetector()
    
    def validate(self, data: ProjectData) -> ValidationResult:
        """
        Validate project data.
        
        Checks:
        - No cycles in precedence graph
        - Valid precedence references
        - Non-negative durations
        - Positive resource capacities
        
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(is_valid=True)
        
        # Check for cycles
        if self.cycle_detector.has_cycle(data.activities, data.precedence):
            result.add_error("Precedence graph contains cycles")
        
        # Validate precedence references
        activity_ids = set(data.activities.keys())
        for pred, succ in data.precedence:
            if pred not in activity_ids:
                result.add_error(f"Invalid precedence: predecessor '{pred}' not found")
            if succ not in activity_ids:
                result.add_error(f"Invalid precedence: successor '{succ}' not found")
        
        # Validate durations
        for activity in data.activities.values():
            if activity.duration < 0:
                # Fix: Use correct attribute activity_id instead of id
                result.add_error(f"Activity '{activity.activity_id}' has negative duration: {activity.duration}")
        
        # Validate resource capacities
        for resource in data.resources.values():
            if resource.capacity <= 0:
                # Fix: Use correct attribute resource_id instead of id
                result.add_error(f"Resource '{resource.resource_id}' has non-positive capacity: {resource.capacity}")
        
        # Log results
        if result.has_errors():
            for error in result.errors:
                logger.error(f"Validation error: {error}")
        if result.has_warnings():
            for warning in result.warnings:
                logger.warning(f"Validation warning: {warning}")
        
        if result.is_valid:
            logger.info("Data validation passed")
        
        return result