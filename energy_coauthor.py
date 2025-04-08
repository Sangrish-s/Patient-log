# app.py - Complete EnergyPlus EUI Analyzer from IDF/EPW
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from eppy import modeleditor
from io import StringIO
import subprocess
import tempfile
import matplotlib.pyplot as plt
from pathlib import Path

# ==============================================
# SETUP
# ==============================================
st.set_page_config(
    page_title="EUI Analyzer from IDF",
    layout="wide",
    page_icon="🏢"
)

import subprocess
import streamlit as st

# Initialize session state
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None
if 'eui_results' not in st.session_state:
    st.session_state.eui_results = None
if 'idf_data' not in st.session_state:
    st.session_state.idf_data = None

# ==============================================
# ENERGYPLUS SIMULATION FUNCTIONS
# ==============================================
def run_energyplus(idf_file, epw_file):
    """Run EnergyPlus simulation and return results"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy files to temp dir
        tmp_idf = os.path.join(tmpdir, "in.idf")
        tmp_epw = os.path.join(tmpdir, "weather.epw")
        
        with open(tmp_idf, 'w') as f:
            f.write(idf_file.getvalue())
        with open(tmp_epw, 'wb') as f:
            f.write(epw_file.getvalue())
        
        # Run EnergyPlus
        cmd = f"energyplus -w {tmp_epw} -d {tmpdir} {tmp_idf}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            st.error(f"EnergyPlus failed: {result.stderr}")
            return None
        
        # Find output CSV
        for file in os.listdir(tmpdir):
            if file.endswith('.csv'):
                csv_path = os.path.join(tmpdir, file)
                with open(csv_path, 'r') as f:
                    return f.read()
    return None

def extract_building_data(idf_file):
    """Extract building info from IDF"""
    idf_str = idf_file.getvalue().decode('utf-8')
    iddfile = os.path.join(os.path.dirname(__file__), 'Energy+.idd')
    if not os.path.exists(iddfile):
        iddfile = None  # Let Eppy find it automatically
    
    modeleditor.IDF.setiddname(iddfile)
    idf = modeleditor.IDF(StringIO(idf_str))
    
    # Get floor area
    total_area = 0
    for zone in idf.idfobjects['ZONE']:
        total_area += zone.Floor_Area if hasattr(zone, 'Floor_Area') else 0
    
    # Get construction details
    constructions = []
    for surf in idf.idfobjects['BUILDINGSURFACE:DETAILED']:
        constructions.append(surf.Construction_Name)
    
    return {
        'floor_area': total_area,
        'zones': len(idf.idfobjects['ZONE']),
        'constructions': list(set(constructions))
    }

def process_energyplus_results(csv_data):
    """Parse EnergyPlus output CSV"""
    df = pd.read_csv(StringIO(csv_data))
    
    # Detect all energy meters
    energy_cols = [col for col in df.columns if 'Facility [J]' in col]
    energy_data = {}
    
    for col in energy_cols:
        fuel_type = col.split(':')[0]
        energy_data[fuel_type] = df[col].sum() / 3600000  # Convert J to kWh
    
    return df, energy_data

# ==============================================
# UI COMPONENTS
# ==============================================
st.title("🏢 EnergyPlus EUI Analyzer")
st.caption("Upload your IDF model and EPW weather file to calculate EUI metrics")

# File Upload Section
with st.expander("📤 Upload Input Files", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        idf_file = st.file_uploader(
            "Building Model (IDF)",
            type=["idf"],
            help="EnergyPlus Input Data File"
        )
    
    with col2:
        epw_file = st.file_uploader(
            "Weather File (EPW)",
            type=["epw"],
            help="EnergyPlus Weather File"
        )
    
    if idf_file and epw_file:
        if st.button("Run Simulation"):
            with st.spinner("Running EnergyPlus simulation..."):
                # Extract building data
                st.session_state.idf_data = extract_building_data(idf_file)
                
                # Run simulation
                csv_output = run_energyplus(idf_file, epw_file)
                
                if csv_output:
                    df, energy_data = process_energyplus_results(csv_output)
                    st.session_state.simulation_results = {
                        'raw_data': df,
                        'energy_data': energy_data
                    }
                    st.success("Simulation completed successfully!")

# Display Building Information
if st.session_state.idf_data:
    with st.expander("🏢 Building Details"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Floor Area", f"{st.session_state.idf_data['floor_area']:.1f} m²")
        col2.metric("Zones", st.session_state.idf_data['zones'])
        col3.metric("Unique Constructions", len(st.session_state.idf_data['constructions']))
        
        st.write("**Constructions Used:**")
        st.write(", ".join(st.session_state.idf_data['constructions']))

# Calculate and Display Results
if st.session_state.simulation_results and st.session_state.idf_data:
    energy_data = st.session_state.simulation_results['energy_data']
    floor_area = st.session_state.idf_data['floor_area']
    
    # Calculate EUI
    st.session_state.eui_results = {
        fuel: energy/floor_area for fuel, energy in energy_data.items()
    }
    
    st.divider()
    st.header("📊 Energy Results")
    
    # Metrics Cards
    cols = st.columns(len(st.session_state.eui_results) + 1)
    for idx, (fuel_type, eui) in enumerate(st.session_state.eui_results.items()):
        with cols[idx]:
            st.metric(
                label=f"{fuel_type} EUI",
                value=f"{eui:.1f} kWh/m²/yr",
                help="Energy Use Intensity"
            )
    
    # Total EUI
    with cols[-1]:
        total_eui = sum(st.session_state.eui_results.values())
        st.metric(
            label="Total EUI",
            value=f"{total_eui:.1f} kWh/m²/yr",
            delta="-5% vs ASHRAE 90.1" if total_eui < 150 else "+10% vs ASHRAE 90.1"
        )
    
    # Visualization Tabs
    tab1, tab2, tab3 = st.tabs(["Energy Breakdown", "Hourly Profile", "Benchmarks"])
    
    with tab1:
        fig1 = px.pie(
            names=list(st.session_state.eui_results.keys()),
            values=list(st.session_state.eui_results.values()),
            title="Energy Distribution by Fuel Type",
            hole=0.4
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with tab2:
        df = st.session_state.simulation_results['raw_data']
        if 'Electricity:Facility [J](Hourly)' in df.columns:
            df['Electricity_kWh'] = df['Electricity:Facility [J](Hourly)'] / 3600000
            fig2 = px.line(
                df,
                y='Electricity_kWh',
                title="Hourly Electricity Consumption",
                labels={'value': 'kWh', 'index': 'Hour'}
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        benchmarks = {
            'Your Building': total_eui,
            'ASHRAE 90.1': 150,
            'Net Zero': 0,
            '2030 Challenge': 38
        }
        
        fig3 = px.bar(
            x=list(benchmarks.keys()),
            y=list(benchmarks.values()),
            title="EUI Benchmark Comparison",
            color=list(benchmarks.keys()),
            labels={'x': '', 'y': 'kWh/m²/yr'}
        )
        st.plotly_chart(fig3, use_container_width=True)

# ==============================================
# REQUIREMENTS & DEPENDENCIES
# ==============================================
"""
### Requirements:
1. EnergyPlus installed and in system PATH
2. Python packages:
streamlit>=1.22
pandas>=1.5
plotly>=5.11
eppy>=0.5.60
matplotlib>=3.6
"""
# Footer
st.divider()
st.caption("EnergyPlus EUI Analyzer v1.0 | Uses Eppy for IDF processing")
