import streamlit as st
import plotly.graph_objects as go
import sample_app_module as sam
import crane_runway as cr
import sectionproperties.pre.library.primitive_sections as primitive_sections
from sectionproperties.analysis.section import Section
from sectionproperties.pre.pre import Material
import matplotlib.pyplot as plt
import numpy as np
import pycba as cba



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