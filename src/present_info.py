from src.load_data import read_text_from_file
from psychopy import visual, event, logging, core
from src.exit_handler import check_exit
import os


def draw_stim(stim, flag):
    """
    Sets the autoDraw flag on a stimulus or a collection of stimuli.
    Supports a single stimulus, a flat or nested list, a dictionary,
    or any combination thereof (e.g. a dict containing lists of stimuli).

    Args:
        stim: A single PsychoPy stimulus object, a flat or nested list of stimulus objects,
            or a dictionary whose values are stimulus objects or lists of stimulus objects.
        flag (bool): If True, the stimulus will be drawn on every frame. If False, drawing stops.
    """
    if isinstance(stim, dict):
        for elem in stim.values():
            draw_stim(elem, flag)
    elif isinstance(stim, list):
        for elem in stim:
            draw_stim(elem, flag)
    else:
        stim.setAutoDraw(flag)


def present_text(win, file_name, config, keys=('return', 'space', 'f7'), replacements={}):
    """
    Displays a text instruction screen loaded from a file and waits for the participant to continue.
    Checks for the exit key after the participant responds.

    Args:
        win (visual.Window): The PsychoPy window object.
        file_name (str): Path to the text file containing the instruction content.
        config (dict): Dictionary containing:
            - instruction_text_size (int | float): Height of the displayed text in window units.
            - instruction_color (str): Color of the displayed text.
            - instruction_wrap_width (int | float): Maximum line width in pixels before text wraps.
            - instruction_font (str): Font name of the displayed text.
        keys (tuple): A tuple of keys that allow the participant to proceed. Defaults to ('return', 'space').
        replacements (dict): Optional dict to insert into the instruction text. Defaults to {}.
    """
    logging.info(f'Displaying info screen: {file_name}')

    msg = read_text_from_file(file_name, replacements=replacements)
    msg = visual.TextStim(win, color=config["instruction_color"],
                          text=msg, height=config["instruction_text_size"],
                          wrapWidth=config["instruction_wrap_width"],
                          font=config["instruction_font"])
    msg.draw()
    win.flip()

    event.waitKeys(keyList=list(keys))
    check_exit()

    logging.info(f'Info screen confirmed by participant: {file_name}')
    win.flip()


def present_image(win, file_name, size, keys=('return', 'space', 'f7')):
    """
    Displays an image screen loaded from the 'messages' directory and waits for the participant to continue.
    Checks for the exit key after the participant responds.

    Args:
        win (visual.Window): The PsychoPy window object.
        file_name (str): Name of the image file located in the 'messages' directory.
        size (tuple): Size of the displayed image as (width, height) in window units.
        keys (tuple): A tuple of keys that allow the participant to proceed. Defaults to ('return', 'space').
    """
    logging.info(f'Displaying image screen: {file_name}')

    image = visual.ImageStim(win=win, image=os.path.join('messages', file_name),
                             interpolate=True, size=size)
    image.draw()
    win.flip()

    event.waitKeys(keyList=list(keys))
    check_exit()

    logging.info(f'Image screen confirmed by participant: {file_name}')
    win.flip()


def present_sequence(win, base_name, config,
                     keys=('return', 'space'), folder='messages'):
    """
    Displays a sequence of instruction screens in order, loading files named
    '<base_name>_1.*', '<base_name>_2.*', etc. from the specified folder.
    If only a single file named '<base_name>.*' exists, it is displayed directly
    without requiring the '_1' suffix.
    Supports both text (.txt) and image files (.jpg, .jpeg, .png, .bmp).
    Stops when no file with the next index is found.

    Args:
        win (visual.Window): The PsychoPy window object.
        base_name (str): Base name of the instruction files (e.g. 'instruction').
        text_size (int | float): Height of the displayed text in window units.
        text_color (str): Color of the displayed text.
        wrap_width (int | float): Maximum line width in pixels before text wraps.
        keys (tuple): A tuple of keys that allow the participant to proceed. Defaults to ('return', 'space').
        folder (str): Directory to search for instruction files. Defaults to 'messages'.
    """
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}
    TEXT_EXTENSIONS = {'.txt'}
    ALL_EXTENSIONS = IMAGE_EXTENSIONS | TEXT_EXTENSIONS

    def find_file(name):
        matches = [
            f for f in os.listdir(folder)
            if os.path.splitext(f)[0] == name
            and os.path.splitext(f)[1].lower() in ALL_EXTENSIONS
        ]
        return matches[0] if matches else None

    def present_file(file_name):
        ext = os.path.splitext(file_name)[1].lower()
        logging.info(f'Presenting sequence screen: {file_name}')
        if ext in TEXT_EXTENSIONS:
            present_text(win, file_name=os.path.join(folder, file_name),
                         config=config, keys=keys)
        elif ext in IMAGE_EXTENSIONS:
            present_image(win, file_name=file_name, size=(config["instruction_wrap_width"], None), keys=keys)

    # Check for a single file without suffix first
    single_file = find_file(base_name)
    if single_file:
        present_file(single_file)
        logging.info(f'Single screen presented for "{base_name}".')
        return

    # Otherwise iterate through numbered sequence
    idx = 1
    while True:
        file_name = find_file(f'{base_name}_{idx}')
        if not file_name:
            break
        present_file(file_name)
        idx += 1

    logging.info(f'Sequence complete: {idx - 1} screen(s) presented for "{base_name}".')


def show_feedback(win, acc, config):
    """
    Displays a feedback message based on participant's accuracy.
    The message is looked up from a dictionary in config using acc as the key.

    Args:
        win (visual.Window): The PsychoPy window object.
        acc: Accuracy value used as a key to look up the feedback message
            (e.g. True/False, 1/0, 'correct'/'error').
        config (dict): Configuration dictionary containing:
            - 'feedback_text' (dict): Mapping of accuracy values to feedback messages
                (e.g. {True: 'Correct!', False: 'Error!'}).
            - 'feedback_color' (str): Color of the feedback text.
            - 'feedback_size' (int | float): Height of the feedback text in window units.
            - 'feedback_time' (float): Duration in seconds to display the feedback.
    """
    feedback_text = config['feedback_text'][acc]
    logging.info(f'Displaying feedback for acc={acc}: "{feedback_text}"')

    feedback = visual.TextStim(win, text=feedback_text,
                               color=config['feedback_color'],
                               height=config['feedback_size'])
    feedback.draw()
    win.flip()
    core.wait(config['feedback_time'])
    win.flip()