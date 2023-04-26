"""
A module for checking steel stresses.
"""

from dataclasses import dataclass, field
from typing import Dict
from math import pi, sqrt
from collections import defaultdict

@dataclass
class Crane:
    crane_load: float = 0
    no_cranewheels: int = 0
    dist_between_cranewheels: int = 0


@dataclass
class Runway_geometry:
    no_spans: int = 0
    spans: Dict = field(default_factory=dict)

    def support_locations(self):
        support_locations= [0]
        for idx, _ in enumerate(self.spans):
            support_to_add = sum(list(self.spans.values())[0:idx+1])
            support_locations.append(support_to_add)
        return support_locations


@dataclass
class Material:
    fy: int = 0
    E_mod: int = 0
    rho: float = 0


def bending_stress(M: float, ixx: float, e: float) -> float:
    """
    Calculates bendingstress.
    """
    sigma = (M * e) / ixx
    return sigma