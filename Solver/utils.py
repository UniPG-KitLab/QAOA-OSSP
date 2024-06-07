import os

def create_directories(split_name, res_filename=None, create_log=False, create_sampler=False):
    # Create directories for results
    results_root_dir = "results"
    os.makedirs(results_root_dir, exist_ok=True)
    results_dir = os.path.join(results_root_dir, f"results_{split_name}")
    os.makedirs(results_dir, exist_ok=True)
    res_file_path = os.path.join(results_dir, res_filename if res_filename else f"result_{split_name}.csv")
    
    log_file_path = None
    sampler_dir = None
    
    # Flag create directories for logs
    if create_log:
        log_root_dir = "log"
        os.makedirs(log_root_dir, exist_ok=True)
        log_dir = os.path.join(log_root_dir, f"log_{split_name}")
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"log_experiment_{split_name}.txt")
    
    # Flag create directories for samplers
    if create_sampler:
        sampler_root_dir = "sampler"
        os.makedirs(sampler_root_dir, exist_ok=True)
        sampler_dir = os.path.join(sampler_root_dir, f"sampler_{split_name}")
        os.makedirs(sampler_dir, exist_ok=True)
    
    return res_file_path, log_file_path, sampler_dir
