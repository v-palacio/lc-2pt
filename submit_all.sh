#!/bin/bash

for dir in P*; do
    cd $dir
    qsub submit.sh
    cd ..
    sleep 1
done
