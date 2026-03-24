import time
from psychopy import visual, event, core

from src.experiment_setup import part_info, init_logging
from src.monitor_setup import create_monitor
from src.load_data import load_config
from src.exit_handler import register_save_beh_results
from src.present_info import present_sequence


def main():
    session_time = time.strftime("%Y_%m_%d_%H_%M", time.gmtime())
    results_beh = []

    info, part_id = part_info()

    init_logging(part_id=part_id, timestamp=session_time)
    register_save_beh_results(results=results_beh, part_id=part_id, timestamp=session_time)

    config = load_config()
    print(config)
    win = visual.Window(fullscr=True,
                        monitor=create_monitor(config),
                        units='pix',
                        screen=0,
                        color=config["screen_color"])

    mouse = event.Mouse(visible=False)
    clock = core.Clock()

    # prepare stimulus
    training = None
    experiment = None

    # training
    present_sequence(win=win, base_name="training", config=config)


    # experiment
    present_sequence(win=win, base_name="experiment", config=config)

    # end procedure
    present_sequence(win=win, base_name="end", config=config)


if __name__ == '__main__':
    main()