import streamlit as st
import sectionproperties.pre.library.primitive_sections as primitive_sections
from sectionproperties.analysis.section import Section
from sectionproperties.pre.pre import Material
import matplotlib.pyplot as plt
import matplotlib.markers as markers
import pycba as cba
from typing import Union, Dict
from dataclasses import dataclass
from handcalcs.decorator import handcalc
from steel import section


# Calculate Sectionproperties
@st.cache_data
def calc_sectionproperties(
        material,
        runway_section
    ):
    name='Steel'
    poissons_ratio=0.3
    color='blue'

    steel = Material(name=name, elastic_modulus=material.E_mod, poissons_ratio=poissons_ratio, density=material.rho*1e-9,
                 yield_strength=material.fy, color=color)

    top_flange = primitive_sections.rectangular_section(
        runway_section.top_flange_width, runway_section.top_flange_height, material=steel).shift_section(-runway_section.top_flange_width / 2, runway_section.web_height / 2)
    web = primitive_sections.rectangular_section(runway_section.web_width, runway_section.web_height, material=steel).shift_section(-runway_section.web_width / 2, -runway_section.web_height / 2)
    bot_flange = primitive_sections.rectangular_section(runway_section.bot_flange_width, runway_section.bot_flange_height, material=steel).shift_section(-runway_section.bot_flange_width / 2, -runway_section.web_height / 2 - runway_section.bot_flange_height)
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
    support_locations,
    wheel_locations
):
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

@st.cache_data
def calculate_envelopes(E_mod, spans, ixx, mass, crane, stepsize):
    

    beam_model = create_crane_runway(E_mod=E_mod, ixx=ixx, spans=spans, mass=mass)
    crane_vehicle = create_crane_vehicle(beam_model=beam_model, crane=crane)
    bridge_model = create_bridge_model(beam_model, crane_vehicle)
    # RESULT INFLUENCELINE BRIDGEMODEL
    results_envelope = bridge_model.run_vehicle(step=stepsize)
    results_critical_values = bridge_model.critical_values(results_envelope)
    return results_envelope, results_critical_values, bridge_model

# Nocache
def plot_MV_results(results_envelope, pos_x_selected, result_at_pos, rw_geometry, rw_crane):
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
    return (fig_M, ax_M, fig_V, ax_V)


hc_renderer = handcalc(override='long')

sigma1 = hc_renderer(section.bending_stress)
sigma2 = hc_renderer(section.bending_stress)

def calc_bendingstresses():
    sigma1_latex, sigma1_value = sigma1(M = 10e+6, ixx = 200e+10, e = 34.0)
    sigma2_latex, sigma2_value = sigma2(M = 20e+6, ixx = 400e+10, e = 44.0)



    return sigma1_latex, sigma2_latex, sigma1_value, sigma2_value
    # return 2,3,4,5

# calc_euler_buckling = hc_renderer(columns.eulerbucklingload)
# calc_factored_resistance = hc_renderer(columns.factored_axial_capacity)

# def calc_pr_at_given_height(area: float, Ix: float, Iy: float, kx: float, ky: float, L: float, E: float, fy: float, n: float, phi=0.9):
#     """
#     Doc strings
#     """
#     xbuckling_latex, _ = calc_euler_buckling(E, Ix, kx, L)
#     ybuckling_latex, _ = calc_euler_buckling(E, Iy, ky, L)
#     factored_latex, factored_load = calc_factored_resistance(
#         area,
#         Ix,
#         Iy,
#         kx,
#         ky,
#         L,
#         E,
#         fy,
#         n,
#         phi
#         )
#     return [xbuckling_latex, ybuckling_latex, factored_latex], factored_load

# TODO
# docstrings module, class functions
# imports
# classes
# plot markers
