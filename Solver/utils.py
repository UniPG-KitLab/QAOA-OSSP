import os

def create_directories(create_log=False, create_sampler=False):
    # Create directories for results
    results_root_dir = "results"
    os.makedirs(results_root_dir, exist_ok=True)
    res_file_path = os.path.join(results_root_dir, "result.csv")
    
    log_file_path = None
    sampler_dir = None
    
    # Flag create directories for logs
    if create_log:
        log_root_dir = "log"
        os.makedirs(log_root_dir, exist_ok=True)
        log_file_path = os.path.join(log_root_dir, "log_experiment.txt")
    
    # Flag create directories for samplers
    if create_sampler:
        sampler_root_dir = "sampler"
        os.makedirs(sampler_root_dir, exist_ok=True)
        sampler_dir = sampler_root_dir
    
    return res_file_path, log_file_path, sampler_dir

