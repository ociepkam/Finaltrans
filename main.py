import time
from psychopy import visual, event, core

from src.experiment_setup import part_info, init_logging
from src.monitor_setup import create_monitor
from src.load_data import load_config
from src.exit_handler import register_save_beh_results
from src.present_info import present_sequence

from procedure_code.block_generator import generate_trial_blocks
from procedure_code.procedure_loop import procedure_loop

def main():
    session_time = time.strftime("%Y_%m_%d_%H_%M", time.gmtime())
    results_beh = []
    #                "N", # trial_idx
    #                "section_type", # training or experiment
    #                "block_number",
    #                "trial_type", # memory or relation
    #                "stimulus_type", # arrow or figure
    #                "n_elements", # number of elements in stimulus
    #                "acc", # participant accuracy
    #                "rt", # participant reaction time
    #                "true_answer_order", # only for relation trials; index from trial["answer"]["correct_index"]
    #                "participant_answer_order", # only for relation trials; order index of participant_answer
    #                "true_answer_in_clue_pos", # only for relation trials; True/False if true answer is in clue position
    #                "participant_answer_in_clue_pos"  # only for relation trials; True/False if participant answer is in clue position
    #                "matrix_1_description", # full information about trial from trial["matrix_1"],
    #                "matrix_2_description",  # full information about trial from trial["matrix_2"],
    #                "matrix_3_description",  # full information about trial from trial["matrix_3"],
    #                "matrix_4_description",  # full information about trial from trial["matrix_4"],
    #                "answer_description"  # full information about trial from trial["answer"],

    info, part_id = part_info()

    init_logging(part_id=part_id, timestamp=session_time)
    register_save_beh_results(results=results_beh, part_id=part_id, timestamp=session_time)

    config = load_config()

    win = visual.Window(fullscr=True,
                        monitor=create_monitor(config),
                        units='pix',
                        screen=0,
                        color=config["screen_color"])

    fixation_point = visual.TextStim(win=win,
                                     text=config["fixation_text"],
                                     color=config["fixation_color"],
                                     height=config["fixation_size"],)

    mouse = event.Mouse(visible=False)
    clock = core.Clock()

    # --- Training ---
    present_sequence(win=win, base_name="training", config=config)
    training = generate_trial_blocks(win=win, config=config, section_type="training")
    procedure_loop(win=win,
                   config=config,
                   section_type="training",
                   trials=training,
                   results=results_beh,
                   clock=clock,
                   mouse=mouse,
                   fixation_point=fixation_point)

    # --- Experiment ---
    present_sequence(win=win, base_name="experiment", config=config)
    experiment = generate_trial_blocks(win=win, config=config, section_type="experiment")
    procedure_loop(win=win,
                   config=config,
                   section_type="experiment",
                   trials=experiment,
                   results=results_beh,
                   clock=clock,
                   mouse=mouse,
                   fixation_point=fixation_point)

    # end procedure
    present_sequence(win=win, base_name="end", config=config)


if __name__ == '__main__':
    main()