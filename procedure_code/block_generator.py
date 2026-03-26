import random
from psychopy import logging
from procedure_code.trial_memory import generate_memory_trial
from procedure_code.trial_relation import generate_relational_trial


def generate_trial_blocks(win, config, section_type):
    """
    Generate all trial blocks for a given experiment section.

    Reads block definitions from config and generates ready-to-display
    PsychoPy trials for each block. Trials within each block are shuffled.
    All generation steps are logged using psychopy.logging at INFO level,
    preserving the full section → block → trial structure in the log file.

    Parameters
    ----------
    win : visual.Window
        PsychoPy window object. Must be open before calling this function.
    config : dict
        Experiment configuration dictionary. Must contain either
        "training_trials" or "experiment_trials" key (depending on
        section_type), structured as a list of blocks, where each block
        is a list of trial-group dicts with keys:
            - "n_trials"      (int): Number of trials to generate.
            - "task_type"     (str): "memory" or "relational".
            - "stimulus_type" (str): "arrow" or "figure".
            - "n_elements"    (int): Number of stimuli per trial.
    section_type : str
        Which section to generate. Must be "training" or "experiment".

    Returns
    -------
    list of list of dict
        A list of blocks. Each block is a list of trial dicts (shuffled).
        Each trial dict contains:
            - "task_type"     (str):  "memory" or "relational".
            - "stimulus_type" (str):  "arrow" or "figure".
            - "n_elements"    (int):  Number of stimuli in the trial.
            - "block_idx"     (int):  0-based index of the block.
            - "trial_idx"     (int):  0-based index within the block
                                      (after shuffling).
            - "section_type"  (str):  "training" or "experiment".
            - "matrix_1"      (list): Encoding stimulus set.
            - "mask"          (list): Mask stimulus set.
            - "matrix_2"      (list): Retrieval stimulus set.
            - "answer"        (dict): Correct answer metadata.

    Raises
    ------
    ValueError
        If section_type is not "training" or "experiment".
    ValueError
        If task_type in a trial group is not "memory" or "relational".
    """
    if section_type == "training":
        block_definitions = config["training_trials"]
    elif section_type == "experiment":
        block_definitions = config["experiment_trials"]
    else:
        raise ValueError(f"Invalid section_type: '{section_type}'. "
                         f"Must be 'training' or 'experiment'.")

    n_blocks = len(block_definitions)
    logging.info(f"=== GENERATE SECTION: {section_type.upper()} "
                 f"({n_blocks} block(s)) ===")

    all_blocks = []

    for block_idx, block_def in enumerate(block_definitions):
        n_trials_in_block = sum(g["n_trials"] for g in block_def)
        logging.info(f"  --- Block {block_idx + 1}/{n_blocks} "
                     f"({n_trials_in_block} trials) ---")

        block_trials = []

        for group in block_def:
            n_trials      = group["n_trials"]
            task_type     = group["task_type"]
            stimulus_type = group["stimulus_type"]
            n_elements    = group["n_elements"]

            for _ in range(n_trials):
                if task_type == "memory":
                    trial = generate_memory_trial(
                        win, config, stimulus_type, n_elements
                    )
                elif task_type == "relational":
                    trial = generate_relational_trial(
                        win, config, stimulus_type, n_elements
                    )
                else:
                    raise ValueError(
                        f"Invalid task_type: '{task_type}' in block {block_idx + 1}. "
                        f"Must be 'memory' or 'relational'."
                    )

                trial["task_type"]     = task_type
                trial["stimulus_type"] = stimulus_type
                trial["n_elements"]    = n_elements
                trial["block_idx"]     = block_idx
                trial["section_type"]  = section_type

                block_trials.append(trial)

        random.shuffle(block_trials)

        # Log final trial order and full metadata after shuffle
        for t_idx, trial in enumerate(block_trials):
            trial["trial_idx"] = t_idx
            ans = trial["answer"]
            if trial["task_type"] == "memory":
                logging.info(
                    f"  [{section_type.upper()} | "
                    f"block={block_idx + 1}/{n_blocks} | "
                    f"trial={t_idx + 1}/{n_trials_in_block}] "
                    f"task=memory  stim={trial['stimulus_type']}  "
                    f"n={trial['n_elements']}  "
                    f"matrix_1={[s['stim_label'] for s in trial['matrix_1']]}  "
                    f"matrix_2={[s['stim_label'] for s in trial['matrix_2']]}  "
                    f"changed_idx={ans['changed_index']}  "
                    f"{ans['old_value']}→{ans['new_value']}"
                )
            else:
                logging.info(
                    f"  [{section_type.upper()} | "
                    f"block={block_idx + 1}/{n_blocks} | "
                    f"trial={t_idx + 1}/{n_trials_in_block}] "
                    f"task=relational  stim={trial['stimulus_type']}  "
                    f"n={trial['n_elements']}  "
                    f"matrix_1={[s['stim_label'] for s in trial['matrix_1']]}  "
                    f"matrix_2={[s['stim_label'] for s in trial['matrix_2']]}  "
                    f"cued_idx={ans['cued_index']}  "
                    f"cued_rank={ans['cued_rank']}  "
                    f"correct={ans['correct_value']}  "
                    f"changed_idx={ans['changed_index']}  "
                    f"{ans['old_value']}→{ans['new_value']}"
                )

        all_blocks.append(block_trials)

    logging.info(f"=== SECTION {section_type.upper()} READY ===")
    return all_blocks


# for tests
if __name__ == "__main__":
    from psychopy import visual, core, event, logging as plog
    from src.load_data import load_config
    from os.path import join

    # Minimal logging to console for testing
    plog.console.setLevel(plog.INFO)

    config = load_config(join("..", "config.yaml"))
    win = visual.Window(color="white", units="pix", fullscr=True)

    def draw_stimuli(stim_list):
        for s in stim_list:
            s["stimulus"].draw()

    def draw_phase(stim_list, label_text, duration):
        label = visual.TextStim(win, text=label_text, pos=(0, -200),
                                color="gray", height=22)
        draw_stimuli(stim_list)
        label.draw()
        win.flip()
        core.wait(duration)

    blocks = generate_trial_blocks(win, config, "training")

    for b_idx, block in enumerate(blocks):
        for trial in block:
            ans = trial["answer"]
            label_base = (f"Block {b_idx+1}/{len(blocks)}  "
                          f"Trial {trial['trial_idx']+1}/{len(block)}  "  
                          f"[{trial['task_type'].upper()} | "
                          f"{trial['stimulus_type']} | "
                          f"n={trial['n_elements']}]")

            draw_phase(trial["matrix_1"],
                       label_base + "  |  CUE / MASK", duration=2)

            draw_phase(trial["matrix_2"],
                       label_base + "  |  ENCODING", duration=6)

            draw_phase(trial["matrix_3"],
                       label_base + "  |  ENCODING", duration=1)


            highlight = visual.Circle(
                win, radius=20, edges=128,
                lineColor="red", fillColor=None,
                lineWidth=2, pos=ans["pos"]
            )
            draw_stimuli(trial["matrix_4"])
            highlight.draw()

            if trial["task_type"] == "memory":
                info_text = (f"{label_base}  |  RETRIEVAL\n"
                             f"changed idx={ans['changed_index']}  "
                             f"{ans['old_value']} → {ans['new_value']}")
            else:
                info_text = (f"{label_base}  |  RETRIEVAL\n"
                             f"cued={ans['cued_value']} (rank {ans['cued_rank']})  "
                             f"correct={ans['correct_value']}  "
                             f"changed: {ans['old_value']} → {ans['new_value']}")

            visual.TextStim(win, text=info_text, pos=(0, -200),
                            color="gray", height=20).draw()
            win.flip()
            core.wait(3.0)

            win.flip()
            core.wait(1.5)

            if "escape" in event.getKeys():
                win.close()
                core.quit()

    win.close()