# QAOA-Satellite-Scheduling

## Print logs to the terminal and do not save samples (default):

python3 Solver/main.py --fname Problem_3Sat3Gs_16qbits_0.json --minp 1 --maxp 3 --nsamples 100 --penalty 2 --optimizer COBYLA

### Save the logs in a file and do not save the samples:

python3 Solver/main.py --fname Problem_3Sat3Gs_16qbits_0.json --minp 1 --maxp 3 --nsamples 100 --penalty 2 --optimizer COBYLA --log_to_file

### Save the logs to a file and save the samples:

python3 Solver/main.py --fname Problem_3Sat3Gs_16qbits_0.json --minp 1 --maxp 3 --nsamples 100 --penalty 2 --optimizer COBYLA --log_to_file --save_samples

### For help in terminal 

python3 main.py --help

