import yaml
import numpy as np
import os
from copy import deepcopy
import subprocess
import shutil

from lc_initial.main import generate_coords, generate_lammps
from lc_initial.file_writer import read_box_dimensions

# Load base configuration
with open('base_config.yml', 'r') as f:
    base_config = yaml.safe_load(f)

# Define temperature range
final_temps = np.round(np.linspace(1.6, 0.2, 15), decimals=1)

# Create directory for different temperature runs
if not os.path.exists('temperature_sweep'):
    os.makedirs('temperature_sweep')

# Read box dimensions once
#_, box_dims = generate_coords(n_molecules=2000, mol_length=8, box_limit=50, init_orient='crystal', wiggle_factor=0.2)

box_dims = read_box_dimensions("system.data")
print(f"Using box dimensions: {box_dims}")

# Generate configurations for each temperature
for i, final_temp in enumerate(final_temps):
    config = deepcopy(base_config)  
    
    # Update annealing protocol
    config['annealing']['step0']['temp'] = 0.1
    config['annealing']['step1']['temp'] = round(float(final_temp), 1)
    config['annealing']['step2']['temp'] = round(float(final_temp), 1)
    
    # Update production temperature
    config['production']['temp'] = round(float(final_temp), 1)
    
    # Add system parameters directly to config
    if 'system' not in config:
        config['system'] = {}
    config['system'].update({
        'n_molecules': 2000,
        'mol_length': 8,
        'box_limit_x': box_dims[0],
        'box_limit_y': box_dims[1],
        'box_limit_z': box_dims[2],
        'pressure': 1.0,
        'timestep': 0.001
    })
    
    # Create and setup directory
    run_dir = f'temperature_sweep/T_{final_temp:.1f}'
    if not os.path.exists(run_dir):
        os.makedirs(run_dir)
    
    # Save configuration
    config_path = f'{run_dir}/config.yml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    # Generate simulation files
    print(f"\nGenerating system for T = {final_temp:.1f}")
    try:
        generate_lammps(n_molecules=2000, mol_length=8, box_dims=box_dims,
                       config_path=config_path, template_dir='tmpl')
        
        # Move system files and run.in to run directory
        for file in ['system.init', 'system.settings', 'system.operations', 'run.in']:
            shutil.move(file, run_dir)
        # Copy system.data since we'll need it for other temperatures
        shutil.copy('system.data', run_dir)

    except subprocess.CalledProcessError as e:
        print(f"Error generating files for T = {final_temp:.3f}")
        print(f"Error: {e}")
        continue

    # Copy and customize submit script
    with open('submit.sh', 'r') as f:
        submit_content = f.read()
    
    # Update job name to reflect temperature
    submit_content = submit_content.replace('#$ -N LC_P0.6', f'#$ -N LC_upT{final_temp:.1}')
    
    # Write modified submit script to run directory
    with open(f'{run_dir}/submit.sh', 'w') as f:
        f.write(submit_content)

    # Delete generated system files after moving them
    for file in ['system.init', 'system.settings', 'system.operations', 'run.in']:
        if os.path.exists(file):
            os.remove(file)

print("\nTemperature stages summary:")
for t in final_temps:
    print(f"Target T = {t:.3f}: Iso(2.0) → Final({t:.3f})")



