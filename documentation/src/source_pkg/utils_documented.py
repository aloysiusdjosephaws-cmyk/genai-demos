import argparse

def get_config():
    """Dynamically converts all CLI --key value pairs into a config object.

    This function parses command-line arguments and converts key-value pairs
    starting with '--' into a dictionary, which is then converted into an
    argparse.Namespace object.  Unknown arguments (those not handled by
    argparse's standard parsing) are treated as key-value pairs.

    Returns:
        argparse.Namespace: An argparse.Namespace object containing the
                             key-value pairs found in the command line.
    """
    parser = argparse.ArgumentParser()
    args, unknown = parser.parse_known_args()
    config_dict = {}
    for i in range(0, len(unknown), 2):
        key = unknown[i].lstrip("-") # removes the '--'
        if i + 1 < len(unknown):
            config_dict[key] = unknown[i+1]
    return argparse.Namespace(**config_dict)
