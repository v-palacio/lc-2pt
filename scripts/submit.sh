#!/bin/bash
#$ -N LC_P0.6
#$ -cwd
#$ -o run.out
#$ -e run.err
#$ -q all.q
#$ -l hostname="compute-0-10.local"
#$ -pe mpi 4   # Request 16 cores
module load intel
module load lammps/23Jun22-intel
module load openmpi/3.1.4-intel  # If needed for your system

# Run LAMMPS in parallel
mpirun -np $NSLOTS lmp < run.in
