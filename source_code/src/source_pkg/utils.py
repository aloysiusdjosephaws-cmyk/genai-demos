import argparse

def get_config():
    """Dynamically converts all CLI --key value pairs into a config object."""
    parser = argparse.ArgumentParser()
    args, unknown = parser.parse_known_args()
    config_dict = {}
    for i in range(0, len(unknown), 2):
        key = unknown[i].lstrip("-") # removes the '--'
        if i + 1 < len(unknown):
            config_dict[key] = unknown[i+1]
    return argparse.Namespace(**config_dict)
