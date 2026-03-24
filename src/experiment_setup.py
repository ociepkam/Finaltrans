from os.path import join
from psychopy import logging, gui


def part_info():
    """
    Displays a dialog box to collect participant information at the start of the experiment.
    Exits the program if the user closes or cancels the dialog.

    Returns:
        tuple: A tuple containing:
            - info (dict): A dictionary with participant details:
                - 'Part_id' (str): Participant's ID (empty by default).
                - 'Part_age' (str): Participant's age (empty by default).
                - 'Part_sex' (str): Participant's sex, selected from ["", "MALE", "FEMALE", "OTHER"].
            - part_id_str (str): A formatted string combining participant ID, sex, and age
                in the format '{Part_id}_{Part_sex}_{Part_age}', used for naming output files.
    """
    info = {'Part_id': '', 'Part_age': '', 'Part_sex': ["", "MALE", "FEMALE", "OTHER"]}
    dictDlg = gui.DlgFromDict(dictionary=info, title='Finaltrans')
    if not dictDlg.OK:
        exit(1)
    return info, f"{info['Part_id']}_{info['Part_sex']}_{info['Part_age']}"


def init_logging(part_id, timestamp):
    """
    Initializes the PsychoPy logging system to save logs to a file.

    Args:
        part_id (str): The participant's unique identifier, used for naming the log file.
        timestamp (str): A shared session timestamp (format: YYYY_MM_DD_HH_MM) used to ensure
            the log file name matches other output files from the same session.
    """
    log_filename = join('results', f'{part_id}_log_{timestamp}.log')
    logging.LogFile(log_filename, level=logging.INFO)

    logging.info(f'--- SESSION START: {part_id} ---')
    logging.info(f'Timestamp: {timestamp}')
