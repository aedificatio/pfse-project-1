import streamlit as st
import pycba as cba
import sectionproperties.pre.library.primitive_sections as primitive_sections
from sectionproperties.analysis.section import Section
from sectionproperties.pre.pre import Material
from typing import Union, Dict
from steel import section


# Calculate Sectionproperties
@st.cache_data
def calc_sectionproperties(material, runway_section):
    """
    Create a sectionproperties object of a H-shaped runway section 
    based on the dimensions of the flanges and the web
    """
    steel = Material(name='Steel', elastic_modulus=1, poissons_ratio=0.3, density=material.rho*1e-9,
                 yield_strength=material.fy, color='blue')

    top_flange = primitive_sections.rectangular_section(
        runway_section.top_flange_width, 
        runway_section.top_flange_height, 
        material=steel
    )
    top_flange = top_flange.shift_section(
        -runway_section.top_flange_width / 2, 
        runway_section.web_height / 2
    )

    web = primitive_sections.rectangular_section(
        runway_section.web_width, 
        runway_section.web_height, 
        material=steel
    )
    web = web.shift_section(
        -runway_section.web_width / 2, 
        -runway_section.web_height / 2
    )

    bot_flange = primitive_sections.rectangular_section(
        runway_section.bot_flange_width, 
        runway_section.bot_flange_height,
        material=steel
    )
    bot_flange = bot_flange.shift_section(
        -runway_section.bot_flange_width / 2, 
        -runway_section.web_height / 2 - runway_section.bot_flange_height
    )
    
    top_flange = top_flange - web # create common nodes between sections
    bot_flange = bot_flange - web

    geometry = top_flange + web + bot_flange
    geometry.create_mesh(mesh_sizes=[15])

    section = Section(geometry)
    section.calculate_geometric_properties()
    return section


@st.cache_data
def create_crane_runway(
        E_mod: float, 
        ixx: float, 
        spans: Dict[int, float],
        mass: float
    ) -> cba.BeamAnalysis:
    """
    Returns a PyCBA BeamAnalysis object.
    """
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
        beam_model: cba.BeamAnalysis, crane: section.Crane
    ) -> cba.Vehicle:
    """
    Returns a PyCBA Vehicle object.
    """
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
        crane_vehicle: cba.Vehicle
    ) -> cba.BridgeAnalysis:
    """
    Returns a PyCBA BridgeAnalysis object.
    """
    bridge_model: cba.BridgeAnalysis = cba.BridgeAnalysis(beam_model, crane_vehicle)
    return bridge_model


@st.cache_data
def calculate_envelopes(E_mod, spans, ixx, mass, crane, stepsize):
    """
    Calculates the envelope forces on a crane runway.
    """

    beam_model = create_crane_runway(E_mod=E_mod, ixx=ixx, spans=spans, mass=mass)
    crane_vehicle = create_crane_vehicle(beam_model=beam_model, crane=crane)
    bridge_model = create_bridge_model(beam_model, crane_vehicle)
    
    results_envelope = bridge_model.run_vehicle(step=stepsize)
    results_critical_values = bridge_model.critical_values(results_envelope)
    return results_envelope, results_critical_values, bridge_model
