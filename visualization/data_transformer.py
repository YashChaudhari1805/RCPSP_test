from typing import List, Tuple
from models import SolverResults, ProjectData, ScheduledActivity


class VisualizationDataTransformer:
    """Transforms solver results for visualization."""
    
    @staticmethod
    def get_sorted_activities_for_gantt(
        results: SolverResults
    ) -> List[Tuple[str, ScheduledActivity]]:
        """Get activities sorted by start time for Gantt chart."""
        activities = results.get_scheduled_activities(exclude_dummies=True)
        return [(a.activity_id, a) for a in activities]
    
    @staticmethod
    def calculate_resource_utilization(
        results: SolverResults,
        data: ProjectData,
        resource_id: str
    ) -> List[float]:
        """Calculate resource utilization over time."""
        makespan = max(int(results.makespan), 1)
        time_points = range(makespan + 1)
        utilization = []
        
        for t in time_points:
            usage = 0
            for activity in results.schedule.values():
                # Note: Assumes standard dummy names "0" and "N" here.
                # If customized in config, this filtering might need adjustment.
                if activity.activity_id in ["0", "N"]:
                    continue
                if activity.start <= t < activity.finish:
                    usage += data.resource_usage.get(activity.activity_id, {}).get(resource_id, 0)
            utilization.append(usage)
            
        # Fix: Added missing return statement
        return utilization