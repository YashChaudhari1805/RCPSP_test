import pulp
import logging
from typing import Tuple, Dict, List

from models import ProjectData
from config import ModelConfig

logger = logging.getLogger(__name__)


class ModelBuilder:
    """Builds MILP model for RCPSP."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
    
    def build(self, data: ProjectData) -> Tuple[pulp.LpProblem, Dict, pulp.LpVariable]:
        """
        Build complete MILP model.
        
        Returns:
            (model, x_variables, cmax_variable)
        """
        model = pulp.LpProblem("RCPSP", pulp.LpMinimize)
        
        # Decision variables
        time_horizon = data.get_time_horizon()
        x_vars = self._create_start_variables(data, time_horizon)
        cmax_var = pulp.LpVariable("Cmax", lowBound=0, cat=pulp.LpInteger)
        
        # Objective
        model += cmax_var, "Minimize_Makespan"
        
        # Constraints
        self._add_start_once_constraints(model, data, x_vars, time_horizon)
        self._add_precedence_constraints(model, data, x_vars, time_horizon)
        self._add_makespan_constraints(model, data, x_vars, cmax_var, time_horizon)
        self._add_renewable_capacity_constraints(model, data, x_vars, time_horizon)
        self._add_nonrenewable_stock_constraints(model, data)
        
        return model, x_vars, cmax_var
    
    @staticmethod
    def _create_start_variables(data: ProjectData, time_horizon: List[int]) -> Dict:
        """Create binary start time variables."""
        return pulp.LpVariable.dicts(
            "Start",
            ((aid, t) for aid in data.activities.keys() for t in time_horizon),
            cat=pulp.LpBinary
        )
    
    def _add_start_once_constraints(
        self,
        model: pulp.LpProblem,
        data: ProjectData,
        x_vars: Dict,
        time_horizon: List[int]
    ):
        """Each activity starts exactly once."""
        for activity_id in data.activities.keys():
            model += (
                pulp.lpSum(x_vars[activity_id, t] for t in time_horizon) == 1,
                f"StartOnce_{activity_id}"
            )
    
    def _add_precedence_constraints(
        self,
        model: pulp.LpProblem,
        data: ProjectData,
        x_vars: Dict,
        time_horizon: List[int]
    ):
        """Precedence: successor starts after predecessor finishes."""
        for pred_id, succ_id in data.precedence:
            pred_duration = data.activities[pred_id].duration
            
            start_succ = pulp.lpSum(t * x_vars[succ_id, t] for t in time_horizon)
            finish_pred = pulp.lpSum(
                (t + pred_duration) * x_vars[pred_id, t] for t in time_horizon
            )
            
            model += (
                start_succ >= finish_pred,
                f"Prec_{pred_id}_before_{succ_id}"
            )
    
    def _add_makespan_constraints(
        self,
        model: pulp.LpProblem,
        data: ProjectData,
        x_vars: Dict,
        cmax_var: pulp.LpVariable,
        time_horizon: List[int]
    ):
        """Makespan must be >= finish time of all activities."""
        for activity_id, activity in data.activities.items():
            if activity_id in [self.config.DUMMY_START, self.config.DUMMY_END]:
                continue
            
            finish_time = pulp.lpSum(
                (t + activity.duration) * x_vars[activity_id, t]
                for t in time_horizon
            )
            
            model += (
                cmax_var >= finish_time,
                f"Cmax_ge_finish_{activity_id}"
            )
    
    def _add_renewable_capacity_constraints(
        self,
        model: pulp.LpProblem,
        data: ProjectData,
        x_vars: Dict,
        time_horizon: List[int]
    ):
        """Renewable resource capacity constraints."""
        renewable_resources = data.get_renewable_resources()
        
        for resource_id, resource in renewable_resources.items():
            for t in time_horizon:
                usage_terms = []
                
                for activity_id, activity in data.activities.items():
                    usage_amount = data.resource_usage.get(activity_id, {}).get(resource_id, 0)
                    if usage_amount <= 0:
                        continue
                    
                    duration = activity.duration
                    t_min = max(0, t - duration + 1)
                    
                    for q in range(t_min, t + 1):
                        if q in time_horizon:
                            usage_terms.append(usage_amount * x_vars[activity_id, q])
                
                if usage_terms:
                    model += (
                        pulp.lpSum(usage_terms) <= resource.capacity,
                        f"Cap_{resource_id}_t{t}"
                    )
    
    def _add_nonrenewable_stock_constraints(
        self,
        model: pulp.LpProblem,
        data: ProjectData
    ):
        """Non-renewable resource stock constraints."""
        nonrenewable_resources = data.get_non_renewable_resources()
        
        for resource_id, resource in nonrenewable_resources.items():
            total_usage = pulp.lpSum(
                data.resource_usage.get(activity_id, {}).get(resource_id, 0)
                for activity_id in data.activities.keys()
            )
            
            model += (
                total_usage <= resource.capacity,
                f"Stock_{resource_id}"
            )