import argparse
from experiment import Experiment

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run QAOA experiments")
    parser.add_argument("--fname", type=str, required=True, help="Filename of the problem instance")
    parser.add_argument("--minp", type=int, required=True, help="Min number of circuit phase")
    parser.add_argument("--maxp", type=int, required=True, help="Max number of circuit phase")
    parser.add_argument("--nsamples", type=int, required=True, help="Number of samples for sampling")
    parser.add_argument("--penalty", type=int, required=True, help="Value of penalty for the instance")
    parser.add_argument("--optimizer", type=str, required=True, choices=["COBYLA", "SGD"], default="COBYLA", help="Optimizer to use (COBYLA or SGD)")
    parser.add_argument("--save_log", action="store_true", help="Flag to log messages to a file instead of the terminal")
    parser.add_argument("--save_samples", action="store_true", help="Flag to save sample directories")

    args = parser.parse_args()

    experiment = Experiment(args.fname, args.minp, args.maxp, args.nsamples, args.penalty, args.optimizer, args.save_log, args.save_samples)
    
    experiment.run()
