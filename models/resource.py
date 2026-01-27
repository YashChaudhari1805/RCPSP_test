from dataclasses import dataclass
from enum import Enum

class ResourceType(Enum):
    """Type of resource."""
    RENEWABLE = "renewable"
    NON_RENEWABLE = "non_renewable"

@dataclass
class Resource:
    """Represents a project resource."""
    
    id: str
    capacity: int
    resource_type: ResourceType = ResourceType.RENEWABLE
    
    @property
    def resource_id(self):
        """Alias for compatibility."""
        return self.id
    
    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError(f"Resource {self.id} has non-positive capacity: {self.capacity}")
    
    @property
    def is_renewable(self) -> bool:
        return self.resource_type == ResourceType.RENEWABLE
    
    @property
    def is_non_renewable(self) -> bool:
        return self.resource_type == ResourceType.NON_RENEWABLE
