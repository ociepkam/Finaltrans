from psychopy import logging, monitors, visual, gui
from collections import OrderedDict


def get_screen_res():
    """
    Checks the current screen resolution using pyglet.

    Returns:
        OrderedDict: A dictionary with keys 'width' and 'height' (both int).
    """
    try:
        from pyglet.canvas import get_display
        display = get_display()
        screen = display.get_default_screen()
        width, height = screen.width, screen.height

        logging.info(f'Screen resolution detected: {width}x{height}')
        return OrderedDict(width=width, height=height)

    except Exception as e:
        logging.error(f'Failed to detect screen resolution: {e}')
        return OrderedDict(width=1920, height=1080)


def create_monitor(monitor_config):
    """
    Creates and configures a PsychoPy Monitor object based on provided parameters.
    Screen resolution is detected automatically at runtime.

    Args:
        monitor_config (dict): Dictionary containing:
            - 'monitor_name' (str): Name for the monitor profile.
            - 'monitor_width' (float): Physical width of the screen in cm.
            - 'monitor_distance' (float): Distance from the participant to the screen in cm.

    Returns:
        monitors.Monitor: A configured PsychoPy Monitor object.
    """
    screen_res = get_screen_res()
    mon = monitors.Monitor(monitor_config['monitor_name'])
    mon.setWidth(monitor_config['monitor_width'])
    mon.setDistance(monitor_config['monitor_distance'])
    mon.setSizePix(list(screen_res.values()))

    logging.info(f'Monitor Profile: {mon.name}')
    logging.info(f'Physical Width: {mon.getWidth()} cm')
    logging.info(f'Viewing Distance: {mon.getDistance()} cm')
    logging.info(f'Resolution: {mon.getSizePix()} px')
    logging.info('---------------------------------------')

    return mon


def get_frame_rate(win, legal_frame_rates=(60,)):
    """
    Detects the actual frame rate of the display window and validates it against allowed values.
    Displays a message on screen during measurement, as the process may take several seconds.
    If the detected frame rate is invalid, an error dialog is shown before raising an exception.

    Args:
        win (visual.Window): The PsychoPy window object used to measure the frame rate.
        legal_frame_rates (tuple): A tuple of accepted frame rates in Hz. Defaults to (60,).

    Returns:
        int: The detected frame rate in Hz.

    Raises:
        ValueError: If the detected frame rate is not in the list of accepted frame rates.
    """
    msg = visual.TextStim(win, text='Measuring frame rate, please wait...', color='white')
    msg.draw()
    win.flip()

    frame_rate = int(round(win.getActualFrameRate(nIdentical=30, nMaxFrames=240)))
    logging.info(f'Detected frame rate: {frame_rate} Hz.')

    if frame_rate not in legal_frame_rates:
        err = f'Illegal frame rate detected: {frame_rate} Hz. Allowed: {legal_frame_rates}.'
        logging.critical(err)

        dlg = gui.Dlg(title='Frame Rate Error', labelButtonOK='Quit')
        dlg.addText(f'ERROR: {err}')
        dlg.addText('Please check your monitor settings and restart the experiment.')
        dlg.show()

        raise ValueError(err)

    return frame_rate
