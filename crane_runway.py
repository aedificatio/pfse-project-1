import streamlit as st
import plotly.graph_objects as go
import sample_app_module as sam
import crane_runway as cr
import sectionproperties.pre.library.primitive_sections as primitive_sections
from sectionproperties.analysis.section import Section
from sectionproperties.pre.pre import Material
import matplotlib.pyplot as plt
import matplotlib.markers as markers
import numpy as np
import pycba as cba
from typing import Union, Dict
from dataclasses import dataclass


@dataclass
class Crane:
    crane_load: float = 0
    no_cranewheels: int = 0
    dist_between_cranewheels: int = 0

# Calculate Sectionproperties
@st.cache_data
def calc_sectionproperties(
        fy, 
        E_mod, 
        rho,
        top_flange_width, 
        top_flange_height,
        web_width,
        web_height,
        bot_flange_width,
        bot_flange_height
    ):
    name='Steel'
    poissons_ratio=0.3
    color='blue'

    steel = Material(name=name, elastic_modulus=E_mod, poissons_ratio=poissons_ratio, density=rho*1e-9,
                 yield_strength=fy, color=color)

    top_flange = primitive_sections.rectangular_section(top_flange_width, top_flange_height, material=steel).shift_section(-top_flange_width / 2, web_height / 2)
    web = primitive_sections.rectangular_section(web_width, web_height, material=steel).shift_section(-web_width / 2, -web_height / 2)
    bot_flange = primitive_sections.rectangular_section(bot_flange_width, bot_flange_height, material=steel).shift_section(-bot_flange_width / 2, -web_height / 2 - bot_flange_height)
    geometry = top_flange + web + bot_flange
    geometry.create_mesh(mesh_sizes=[15])

    section = Section(geometry)
    section.calculate_geometric_properties()
    section.calculate_warping_properties()
    return section


@st.cache_data
def create_crane_runway(
        E_mod: float, 
        ixx: float, 
        spans: Dict[int, float],
        mass: float
    ) -> cba.BeamAnalysis:
    EI_spans:float = [E_mod * ixx / 1000] * len(spans) # kN/m2
    supports: list[float] = [-1, 0] * (len(spans) + 1) # [rigid vertical support, no rotation capacity]
    UDL: float = mass / 100 # kN/m1
    
    loads: list[Union[int, float]] = []
    element_types: list[Union[int, float]] = []
    for idx, span in enumerate(spans, start = 1):
        loads.append([idx, 1, UDL, 0, 0]) # [beamnr, loadtype, force, start, stop]
        element_types.append(1)

    spans_in_m = [span / 1000 for span in list(spans.values())]

    beam_model = cba.BeamAnalysis(spans_in_m, EI_spans, supports, loads, element_types)
    return beam_model


# nocache
def create_crane_vehicle(
        beam_model: cba.BeamAnalysis, crane: cba.Vehicle) -> cba.BridgeAnalysis:
    
    if crane.no_cranewheels > 1:
        axle_spacings: list[float] = [crane.dist_between_cranewheels / 1000]*(crane.no_cranewheels - 1)
    else:
        axle_spacings = []
    axle_loads: list[float] = [crane.crane_load / crane.no_cranewheels] * crane.no_cranewheels
    
    crane_vehicle: cba.Vehicle = cba.Vehicle(axle_spacings=axle_spacings,  axle_weights=axle_loads)
    return crane_vehicle


# nocache
def create_bridge_model(
        beam_model: cba.BeamAnalysis, 
        crane_vehicle: cba.BridgeAnalysis
    ) -> cba.BridgeAnalysis:
    bridge_model: cba.BridgeAnalysis = cba.BridgeAnalysis(beam_model, crane_vehicle)
    return bridge_model


@st.cache_data
def plot_results(
    plot_info, 
    pos_x_all, 
    data_max_env, 
    data_min_env, 
    data_at_selected_pos, 
    support_locations
):
    fig, ax = plt.subplots()
    ax.set_title(plot_info['title'])
    ax.set_xlabel("m")
    ax.set_ylabel(plot_info['y_label'])
    ax.plot([0,support_locations[-1]/1000],[0,0], color='gray', linewidth=3)
    for support in support_locations:
        ax.plot(support/1000, 0, marker=markers.CARETUP, color='gray', markersize=9)
    ax.plot(pos_x_all, data_max_env, plot_info['max'])
    ax.plot(pos_x_all, data_min_env, plot_info['min'])
    ax.plot(pos_x_all, -data_at_selected_pos, color=plot_info['selected_pos'])
    
    ax.fill_between(pos_x_all, data_max_env, color=plot_info['max'], alpha=0.3)
    ax.fill_between(pos_x_all, data_min_env, color=plot_info['min'], alpha=0.3)
    return fig, ax

def calculate_envelopes(E_mod, ixx, spans, mass, crane, stepsize):
    

    beam_model = create_crane_runway(E_mod=E_mod, ixx=ixx, spans=spans, mass=mass)
    crane_vehicle = create_crane_vehicle(beam_model=beam_model, crane=crane)
    bridge_model = create_bridge_model(beam_model, crane_vehicle)
    # RESULT INFLUENCELINE BRIDGEMODEL
    results_envelope = bridge_model.run_vehicle(step=stepsize)
    results_critical_values = bridge_model.critical_values(results_envelope)
    return results_envelope, results_critical_values, bridge_model

# TODO
# docstrings module, class functions
# imports
# classes
# plot markers
