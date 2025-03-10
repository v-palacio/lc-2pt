import yaml
import numpy as np
import os
from copy import deepcopy
import subprocess
import shutil

from lc_initial.main import generate_lammps
from lc_initial.file_writer import read_box_dimensions

# Define temperature range
final_temps = np.linspace(1.6, 0.2, 15)

box_dims = read_box_dimensions("system.data")

# Generate restart files for each temperature
for final_temp in final_temps:
    final_temp = float(final_temp)
    run_dir = f'/home/vpalacio/scruggs/lc-2pt/temperature_sweep/T_{final_temp:.1f}'
   
    
    if not os.path.exists(run_dir):
        print(f"Directory {run_dir} does not exist, skipping...")
        continue
        
    print(f"\nGenerating restart files for T = {final_temp:.3f}")
    try:
        # Generate LAMMPS files using existing config
        if os.path.exists(f'{run_dir}/restart.in'):
            os.remove(f'{run_dir}/restart.in')
        
        config_path = f'{run_dir}/config.yml'
        generate_lammps(n_molecules = 4500, mol_length = 8, box_dims = box_dims,
                        template_dir='scripts/tmpl', config_path=config_path, files='restart')
        
        # Move only the restart.in file
        shutil.move('restart.in', run_dir)

        # Copy and customize submit script
        with open('scripts/submit.sh', 'r') as f:
            submit_content = f.read()
    
        # Update job name to reflect temperature
        submit_content = submit_content.replace('#$ -N LC_P0.6', f'#$ -N LC_T{final_temp:.1f}')
        submit_content = submit_content.replace('mpirun -np $NSLOTS lmp < run.in', f'mpirun -np $NSLOTS lmp < restart.in')
    
        # Write modified submit script to run directory
        with open(f'{run_dir}/submit.sh', 'w') as f:
            f.write(submit_content)
        
                
    except Exception as e:
        print(f"Error generating restart files for T = {final_temp:.1f}")
        print(f"Error: {e}")
        continue

print("\nRestart files generation complete!")