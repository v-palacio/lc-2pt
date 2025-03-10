import yaml
import numpy as np
import os
from copy import deepcopy
import subprocess
import shutil

from lc_initial.main import generate_coords, generate_lammps
from lc_initial.file_writer import read_box_dimensions

# Load base configuration
with open('scripts/base_config.yml', 'r') as f:
    base_config = yaml.safe_load(f)

# Define temperature range
final_temps = np.round(np.linspace(1.6, 0.2, 15), decimals=1)

# Create directory for different temperature runs
if not os.path.exists('temperature_sweep'):
    os.makedirs('temperature_sweep')

#_, box_dims = generate_coords(n_molecules = 4500, mol_length = 8, box_limit = 200,
#                config_path = 'scripts/base_config.yml', init_orient = 'crystal', wiggle_factor = 0.3)
box_dims = read_box_dimensions("system.data")
# Generate configurations for each temperature
for i, final_temp in enumerate(final_temps):
    config = deepcopy(base_config)
    
    # Keep isotropic temperature at 2.0
    T_iso = 2.0
    
    # Calculate intermediate temperatures for smooth cooling
    # Convert numpy floats to Python floats
    T_stage1 = float(T_iso - (T_iso - final_temp) * 0.33)
    T_stage2 = float(T_iso - (T_iso - final_temp) * 0.66)
    final_temp = float(final_temp)
    
    # Update configuration
    config['annealing']['iso']['temp'] = T_iso
    config['annealing']['stage1']['temp'] = T_stage1
    config['annealing']['stage2']['temp'] = T_stage2
    config['annealing']['final']['temp'] = final_temp
    config['production']['temp'] = final_temp

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
        generate_lammps(n_molecules = 4500, mol_length = 8, box_dims = box_dims,
                        config_path = config_path, template_dir = 'scripts/tmpl')
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
    with open('scripts/submit.sh', 'r') as f:
        submit_content = f.read()
    
    # Update job name to reflect temperature
    submit_content = submit_content.replace('#$ -N LC_P0.6', f'#$ -N LC_T{final_temp:.3f}')
    
    # Write modified submit script to run directory
    with open(f'{run_dir}/submit.sh', 'w') as f:
        f.write(submit_content)

    # Delete generated system files after moving them
    for file in ['system.init', 'system.settings', 'system.operations', 'run.in']:
        if os.path.exists(file):
            os.remove(file)

print("\nTemperature stages summary:")
for t in final_temps:
    T_stage1 = float(2.0 - (2.0 - t) * 0.33)
    T_stage2 = float(2.0 - (2.0 - t) * 0.66)
    print(f"Target T = {t:.3f}: Iso(2.0) → Stage1({T_stage1:.3f}) → Stage2({T_stage2:.3f}) → Final({t:.3f})")



