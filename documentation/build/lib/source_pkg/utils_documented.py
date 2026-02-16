import argparse

def get_config():
    """Dynamically converts all CLI --key value pairs into a config object.

    This function parses command-line arguments, extracts key-value pairs
    starting with '--', and converts them into a Namespace object.  It
    handles cases where `--key` is followed by a value.  Arguments that
    don't match the `--key` pattern are ignored.

    Returns:
        argparse.Namespace: A Namespace object containing the extracted
                             key-value pairs from the command line.
                             If no key-value pairs are found, it returns an
                             empty Namespace.
    """
    parser = argparse.ArgumentParser()
    args, unknown = parser.parse_known_args()
    config_dict = {}
    for i in range(0, len(unknown), 2):
        key = unknown[i].lstrip("-") # removes the '--'
        if i + 1 < len(unknown):
            config_dict[key] = unknown[i+1]
    return argparse.Namespace(**config_dict)
