"""
A module for calculating a steel beam as a crane runway beam steel stresses.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from math import pi, sqrt
from collections import defaultdict
import streamlit as st

@dataclass
class Crane:
    """
    Datatype represents a Crane object.
    
    'crane_load', the crane load in kN
    'no_cranewheels', the number of wheels on the runway
    'dist_between_cranewheels', the distance between the wheels in mm
    'wheel_locations', a list with the global x positions of the crane wheels given a position
    """
    crane_load: float = 0
    no_cranewheels: int = 0
    dist_between_cranewheels: int = 0

    def wheel_locations(self, pos_x_selected):
        """
        Returns a list containing the global x positions of all crane wheels 
        given a position on the runway.
        """
        wheel_locations = [-idx * self.dist_between_cranewheels + pos_x_selected * 1000 for idx in range(self.no_cranewheels)]
        return wheel_locations


@dataclass
class Runway_geometry:
    """
    Datatype represents the geometry of a runway beam.
    """
    no_spans: int = 0
    spans: Dict = field(default_factory=dict)

    def support_locations(self):
        """
        reutns a list with all global x positions of the supports
        """
        support_locations= [0]
        for idx, _ in enumerate(self.spans):
            support_to_add = sum(list(self.spans.values())[0:idx+1])
            support_locations.append(support_to_add)
        return support_locations

@dataclass
class Runway_section:
    """
    Datatype represents the sectionproperties of a runway beam.
    """
    
    top_flange_width: int = 0
    top_flange_height: int = 0
    web_width: int = 0
    web_height: int = 0
    bot_flange_width: int = 0
    bot_flange_height: int = 0
    section = Optional

    def height(self):
        return self.top_flange_height + self.web_height + self.bot_flange_height
    
    def area(self):
        return self.section.get_area() # mm2
    
    def mass(self):
        return self.section.get_mass() * 1000 # kg/m1
    
    def ixx(self):
        ixx, iyy, ixy = self.section.get_ic()
        return ixx
    


@dataclass
class Material:
    """
    Datatype represents the material of a runway beam.
    """
    fy: int = 0
    E_mod: int = 0
    rho: float = 0


def bending_stress(M: float, ixx: float, e: float) -> float:
    """
    Calculates bendingstress given M, e and ixx.
    """
    sigma = (M * e) / ixx
    return sigma