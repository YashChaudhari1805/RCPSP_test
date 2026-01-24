import pulp
import time
import logging
from typing import Dict, List

from .interfaces import ISolver
from .model_builder import ModelBuilder
from models import ProjectData, SolverResults, ScheduledActivity
from config import ModelConfig

logger = logging.getLogger(__name__)


class RCPSPSolver(ISolver):
    """Solves RCPSP using MILP with PuLP and CBC."""
    
    def __init__(self, config: ModelConfig = None, time_limit: int = None):
        self.config = config or ModelConfig()
        self.time_limit = time_limit or self.config.DEFAULT_TIME_LIMIT
        self.model_builder = ModelBuilder(self.config)
    
    def solve(self, data: ProjectData) -> SolverResults:
        """
        Solve RCPSP problem.
        
        Args:
            data: Project data
            
        Returns:
            SolverResults with schedule and metrics
        """
        logger.info("Starting RCPSP optimization")
        
        # Build model
        build_start = time.perf_counter()
        model, x_vars, cmax_var = self.model_builder.build(data)
        build_time = time.perf_counter() - build_start
        
        logger.info(f"Model built with {len(model.constraints)} constraints in {build_time:.2f}s")
        print(f"Model built with {len(model.constraints)} constraints in {build_time:.2f}s")
        
        # Solve
        logger.info("Solving MILP model...")
        print("\n--- Starting MILP Optimization ---")
        
        cpu_start = time.process_time()
        wall_start = time.perf_counter()
        
        solver = pulp.PULP_CBC_CMD(msg=self.config.SOLVER_MSG, timeLimit=self.time_limit)
        model.solve(solver)
        
        cpu_time = time.process_time() - cpu_start
        wall_time = time.perf_counter() - wall_start
        
        status = pulp.LpStatus[model.status]
        logger.info(f"Solver status: {status} | CPU: {cpu_time:.3f}s | Wall: {wall_time:.3f}s")
        print(f"Status: {status}")
        print(f"CPU Time:  {cpu_time:.3f} seconds")
        print(f"Wall Time: {wall_time:.3f} seconds")
        
        if status != "Optimal":
            if status == "Infeasible":
                print("\n**MODEL IS INFEASIBLE.**")
            return SolverResults(
                makespan=0,
                schedule={},
                cpu_time=cpu_time,
                wall_time=wall_time,
                build_time=build_time,
                status=status
            )
        
        # Extract results
        schedule = self._extract_schedule(data, x_vars, cmax_var)
        makespan = self._calculate_makespan(schedule, cmax_var)
        
        logger.info(f"Optimal makespan: {makespan}")
        
        return SolverResults(
            makespan=makespan,
            schedule=schedule,
            cpu_time=cpu_time,
            wall_time=wall_time,
            build_time=build_time,
            status=status
        )
    
    def _extract_schedule(
        self,
        data: ProjectData,
        x_vars: Dict,
        cmax_var
    ) -> Dict[str, ScheduledActivity]:
        """Extract schedule from solved model."""
        schedule = {}
        time_horizon = data.get_time_horizon()
        
        for activity_id, activity in data.activities.items():
            for t in time_horizon:
                var_value = pulp.value(x_vars[activity_id, t])
                if var_value is not None and var_value > 0.9:
                    schedule[activity_id] = ScheduledActivity(
                        activity_id=activity_id,
                        start=int(t),
                        duration=activity.duration,
                        finish=int(t + activity.duration)
                    )
                    break
        
        return schedule
    
    def _calculate_makespan(
        self,
        schedule: Dict[str, ScheduledActivity],
        cmax_var
    ) -> int:
        """Calculate makespan from schedule and Cmax variable."""
        cmax_value = pulp.value(cmax_var)
        makespan_from_var = int(cmax_value) if cmax_value is not None else 0
        
        # Safety check: compute from schedule
        # Fix: Use configured dummy names instead of hardcoded "0", "N"
        schedule_makespan = max(
            (activity.finish for activity in schedule.values() 
             if activity.activity_id not in [self.config.DUMMY_START, self.config.DUMMY_END]),
            default=0
        )
        
        return max(makespan_from_var, schedule_makespan)