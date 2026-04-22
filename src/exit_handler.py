from psychopy import event, logging
import atexit
import csv
from os.path import join

# Module-level reference to the save function, set by register_save_beh_results
_save_beh_results = None


def abort_with_error(err):
    """
    Logs a critical error message and raises an exception to terminate the experiment.

    Args:
        err (str): The error message to be logged and raised.
    """
    logging.critical(err)
    raise Exception(err)


def check_exit(key='f7'):
    """
    Checks if a specific exit key has been pressed and terminates the program if so.

    Args:
        key (str): The keyboard key that triggers the exit. Defaults to 'f7'.
    """
    stop = event.getKeys(keyList=[key])
    if len(stop) > 0:
        logging.critical('Experiment finished by user! {} pressed.'.format(key))
        if _save_beh_results is not None:
            _save_beh_results()
        exit(1)


def register_save_beh_results(results, part_id, timestamp):
    """
    Registers a cleanup function to be executed upon program exit,
    which saves behavioral results to a CSV file.

    Args:
        results (list): A list of dictionaries containing the experimental data.
        part_id (str): The participant's unique identifier used for naming the output files.
        timestamp (str): The timestamp when the experiment was started.
    """
    global _save_beh_results

    @atexit.register
    def save_beh_results():
        if not results:
            logging.warning('No results to save - skipping CSV creation.')
            return

        filename = f'{part_id}_beh_{timestamp}.csv'
        logging.info(f'Saving behavioral results to {filename}...')

        try:
            with open(join('results', filename), 'w', newline='', encoding='utf-8') as beh_file:
                dict_writer = csv.DictWriter(beh_file, results[0].keys())
                dict_writer.writeheader()
                dict_writer.writerows(results)
            logging.info(f'Behavioral results saved successfully. Total rows: {len(results)}.')
        except Exception as e:
            logging.critical(f'Failed to save behavioral results: {e}')

        _save_beh_results = save_beh_results
        atexit.register(save_beh_results)