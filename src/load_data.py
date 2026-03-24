from psychopy import logging
import yaml
import json


def load_config(file_name="config.yaml"):
    """
    Loads experimental configuration from a YAML file and logs its content.

    Args:
        file_name (str): Name of the configuration file. Defaults to "config.yaml".

    Returns:
        dict: A dictionary containing configuration parameters.

    Raises:
        Exception: If the file is missing, empty, or contains invalid YAML.
    """
    try:
        with open(file_name, encoding='utf-8') as yaml_file:
            doc = yaml.safe_load(yaml_file)

        if doc is None:
            msg = f"Configuration file '{file_name}' is empty."
        else:
            logging.info(f"Configuration loaded successfully from '{file_name}'.")

            # Log the entire configuration content
            # Using json.dumps for a clean, readable multi-line format
            config_str = json.dumps(doc, indent=4, sort_keys=True)
            logging.info(f"--- CONFIGURATION CONTENT ---\n{config_str}\n-----------------------------")

            return doc

    except FileNotFoundError:
        msg = f"Configuration file '{file_name}' not found."
    except yaml.YAMLError as e:
        msg = f"Error parsing YAML configuration in '{file_name}': {e}"
    except Exception as e:
        msg = f"Unexpected error loading config '{file_name}': {e}"

    logging.critical(msg)
    raise Exception(msg)


def read_text_from_file(file_name, replacements=None):
    """
    Reads a message from a text file, ignoring comment lines starting with '#'.
    Replaces placeholders in the text (e.g., '{name}') with values from a dictionary.

    Args:
        file_name (str): Path to the text file to read.
        replacements (dict, optional): A dictionary where keys are placeholder names
            (without braces) and values are the strings to insert. Defaults to None.

    Returns:
        str: The processed message content with all placeholders replaced.

    Raises:
        TypeError: If file_name is not a string.
        FileNotFoundError: If the file does not exist.
        KeyError: If a placeholder in the file is missing from the replacements dict.
    """
    if not isinstance(file_name, str):
        raise TypeError('file_name must be a string.')

    try:
        lines = []
        with open(file_name, encoding='utf-8') as data_file:
            for line in data_file:
                if line.startswith('#'):
                    continue
                lines.append(line)

        full_text = ''.join(lines)

        # If replacements are provided, use Python's string formatting
        if replacements:
            try:
                return full_text.format(**replacements)
            except KeyError as e:
                msg = f"Missing replacement value for placeholder: {e} in file '{file_name}'"
                logging.error(msg)
                # Return unformatted text or handle as needed
                return full_text

        return full_text

    except FileNotFoundError:
        msg = f"Instruction file '{file_name}' not found."
        logging.critical(msg)
        raise FileNotFoundError(msg)
