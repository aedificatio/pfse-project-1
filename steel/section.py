"""
A module for calculating a steel beam as a crane runway beam steel stresses.
"""

import streamlit as st
import pycba as cba
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.markers as markers

from dataclasses import dataclass, field
from typing import Dict, Optional
from handcalcs.decorator import handcalc

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

    def wheel_locations(self, pos_x_selected: float) -> list[float]:
        """
        Returns a list containing the global x positions of all crane wheels 
        given a position of the crane Vehicle on the runway.
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

    def support_locations(self) -> list[int]:
        """
        returns a list with all global x positions of the supports
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
    top_flange_width: float = 0
    top_flange_height: float = 0
    web_width: float = 0
    web_height: float = 0
    bot_flange_width: float = 0
    bot_flange_height: float = 0
    section = Optional

    def height(self) -> float:
        return self.top_flange_height + self.web_height + self.bot_flange_height
    
    def area(self) -> float:
        return self.section.get_area() # mm2
    
    def mass(self) -> float:
        return self.section.get_mass() * 1000 # kg/m1
    
    def ixx(self) -> float:
        ixx, iyy, ixy = self.section.get_ic()
        return ixx
    
    def Wx_top(self) -> float:
        zxx_plus, zxx_minus, zyy_plus, zyy_minus = self.section.get_z()
        return zxx_plus
    
    def Wx_bot(self) -> float:
        zxx_plus, zxx_minus, zyy_plus, zyy_minus = self.section.get_z()
        return zxx_minus
    
    def ex_top(self) -> float:
        return self.ixx() / self.Wx_top()
    
    def ex_bot(self) -> float:
        return self.ixx() / self.Wx_bot()


@dataclass
class Material:
    """
    Datatype represents the material of a runway beam.
    """
    fy: int = 0
    E_mod: int = 0
    rho: float = 0


# Nocache
def plot_MV_results(
        results_envelope: cba.results.Envelopes, 
        pos_x_selected: float, 
        result_at_pos: cba.results.BeamResults, 
        rw_geometry: Runway_geometry, 
        rw_crane: Crane
    ) -> matplotlib.figure.Figure:
    
    """
    Returns the Figure and Axes objects of the Bendingmoments and Shearforces 
    of the envelope forces and also the forces with the crane Vehicle at a specific position.
    """
    plot_M = {
        'title': "Bending moment",
        'y_label':'kNm',
        'max': 'green',
        'min': 'blue',
        'selected_pos': 'red'
    }
    plot_V = {
        'title': "Shearforce",
        'y_label': 'kN',
        'max': 'red',
        'min': 'orange',
        'selected_pos': 'red'
    }
    fig_M, ax_M = plot_results(
        plot_M, 
        results_envelope.x, 
        -results_envelope.Mmax, 
        -results_envelope.Mmin, 
        result_at_pos.results.M, 
        rw_geometry.support_locations(),
        rw_crane.wheel_locations(pos_x_selected)
    )
    fig_M.set_size_inches(7,5)
    
    fig_V, ax_V = plot_results(
        plot_V, 
        results_envelope.x, 
        results_envelope.Vmax, 
        results_envelope.Vmin, 
        -result_at_pos.results.V, 
        rw_geometry.support_locations(),
        rw_crane.wheel_locations(pos_x_selected)
    )
    fig_V.set_size_inches(7,5)
    return (fig_M, fig_V)

@st.cache_data
def plot_results(
    plot_info: Dict[str,str], 
    pos_x_all: np.ndarray, 
    data_max_env: np.ndarray, 
    data_min_env: np.ndarray, 
    data_at_selected_pos: np.ndarray, 
    support_locations: list[int],
    wheel_locations: list[float]
) -> matplotlib.figure.Figure:
    """
    Returns a Matplotlib Axes object.
    """
    fig, ax = plt.subplots()
    ax.set_title(plot_info['title'])
    ax.set_xlabel("m")
    ax.set_ylabel(plot_info['y_label'])
    ax.plot(pos_x_all, data_max_env, plot_info['max'])
    ax.plot(pos_x_all, data_min_env, plot_info['min'])
    ax.plot(pos_x_all, -data_at_selected_pos, color=plot_info['selected_pos'])
    
    ax.fill_between(pos_x_all, data_max_env, color=plot_info['max'], alpha=0.3)
    ax.fill_between(pos_x_all, data_min_env, color=plot_info['min'], alpha=0.3)
    ax.plot([0,support_locations[-1]/1000],[0,0], color='gray', linewidth=3)
    for support in support_locations:
        ax.plot(support/1000, 0, marker=markers.CARETUP, color='gray', markersize=9)
    for wheel in wheel_locations:
        ax.plot(wheel/1000, 0, marker=markers.CARETDOWN, color='purple', markersize=9)
    return fig, ax





# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def bending_stress(M: float, ixx: float, e: float) -> float:
    """
    Calculates bendingstress given M, e and ixx.
    """
    sigma = (M * e) / ixx
    return sigma

def bending_stress_alternative(M: float, Wx: float) -> float:
    """
    Calculates bendingstress given M and Wx.
    """
    sigma = M / Wx
    return sigma

hc_renderer = handcalc(override='long')

sigma = hc_renderer(bending_stress)
sigma_alternative = hc_renderer(bending_stress_alternative)


def calc_bendingstresses(rw_section, Mmax):
    """
    Calculate the stresses by the bendingmoment.
    """
    sigma_latex, sigma_value = sigma(M = Mmax * 1e+6, ixx = rw_section.ixx(), e=rw_section.height()/2)
    sigma_alt_latex, sigma_alt_value = sigma_alternative(M = Mmax * 1e+6, Wx = rw_section.Wx_top())
    # sigma_alt_latex, sigma_alt_value = sigma_alternative(M = Mmax * 1e+6, Wx = rw_section.Wx_bot())
    


    return sigma_latex, sigma_value, sigma_alt_latex, sigma_alt_value




