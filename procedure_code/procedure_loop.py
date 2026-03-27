import os

from psychopy import visual, core, event, logging
from src.present_info import present_text, show_feedback, drwa_stim_for_duration, draw_stim
from src.exit_handler import check_exit

def get_stimulus_list(matrix):
    return [stim["stimulus"] for stim in matrix]


def draw_matrix(matrix, win, clock, time):
    drwa_stim_for_duration(win=win, stim=get_stimulus_list(matrix), time=time, clock=clock, end_flip=False)


def update_hit_area_hover(hit_area_dict, mouse, config):
    """
    Update the visual appearance of a hit-area based on mouse hover state.

    Should be called once per frame during the response phase. When
    ``hit_area_show_hover`` is False in config, this function does nothing.

    Parameters
    ----
    hit_area_dict : dict
        A hit-area descriptor returned by ``create_hit_area()``.
    mouse : event.Mouse
        PsychoPy mouse object.
    config : dict
        Must contain the same hit-area keys as ``create_hit_area()``.
    """
    if not config.get("hit_area_show_hover", False):
        return

    rect = hit_area_dict["stimulus"]
    if rect.contains(mouse.getPos()):
        rect.opacity = 1
        rect.lineColor = config["hit_area_hover_color"]
        rect.fillColor = config["hit_area_hover_fill"]
        rect.lineWidth = config["hit_area_hover_width"]
    else:
        rect.opacity = 0
        rect.lineColor = None
        rect.fillColor = None


def compute_accuracy(trial, clicked_stim):
    """
    Determine whether the participant's click was correct.

    For memory trials: correct if the clicked stimulus is at the changed index.
    For relational trials: correct if the clicked stimulus is at the correct index.

    Parameters
    ----------
    trial : dict
        Full trial dict including "task_type", "matrix_4", and "answer".
    clicked_stim : dict or None
        The stimulus dict that was clicked, or None for no response.

    Returns
    -------
    acc : int or None
        1, 0, or None for no answer.
    clicked_index : int or None
        Index of the clicked stimulus in matrix_4, or None.
    """
    if clicked_stim is None:
        return None, None

    matrix_4 = trial["matrix_4"]
    answer = trial["answer"]

    # Find index of clicked stimulus in matrix_4
    clicked_index = None
    for i, s in enumerate(matrix_4):
        if s is clicked_stim:
            clicked_index = i
            break

    # if clicked_index is None:
    #     return None, None

    task_type = trial["task_type"]
    if task_type == "memory":
        correct_index = answer["changed_index"]
    else:  # relational
        correct_index = answer["correct_index"]

    acc = 1 if clicked_index == correct_index else 0
    return acc, clicked_index


def build_result_row(trial, trail_idx, acc, rt, clicked_index, section_type):
    """
    Build a single result row dict for results_beh.

    Parameters
    ----------
    trial : dict
        Full trial dict.
    acc : int or None
        1, 0, or None for no answer.
    rt : float or None
        Reaction time in seconds, or None.
    clicked_index : int or None
        Index of clicked stimulus in matrix_4.
    section_type : str
        "training" or "experiment".

    Returns
    -------
    dict
        Row matching the headers defined in main.py results_beh.
    """
    answer = trial["answer"]
    task_type = trial["task_type"]

    # Relational-only fields
    if task_type == "relational":
        true_answer_order = answer.get("correct_index")
        true_answer_in_clue_pos = (answer.get("correct_index") == answer.get("cued_index"))

        if clicked_index is not None:
            participant_answer_order = clicked_index
            participant_answer_in_clue_pos = (clicked_index == answer.get("cued_index"))
        else:
            participant_answer_order = None
            participant_answer_in_clue_pos = None
    else:
        true_answer_order = None
        true_answer_in_clue_pos = None
        participant_answer_order = None
        participant_answer_in_clue_pos = None

    def _describe(matrix):
        """Return a compact description of a stimulus list."""
        # result = []
        # for s in matrix:
        #     if "stim_label" in s:
        #         result.append({"label": s["stim_label"], "pos": s.get("pos")})
        # return result
        return [{"label": s["stim_label"], "pos": s.get("pos")} for s in matrix]

    return {
        "N":                            trail_idx,
        "section_type":                 section_type,
        "block_number":                 trial["block_idx"] + 1,
        "trial_type":                   task_type,
        "stimulus_type":                trial["stimulus_type"],
        "n_elements":                   trial["n_elements"],
        "acc":                          acc,
        "rt":                           rt,
        "true_answer_order":            true_answer_order,
        "participant_answer_order":     participant_answer_order,
        "true_answer_in_clue_pos":      true_answer_in_clue_pos,
        "participant_answer_in_clue_pos": participant_answer_in_clue_pos,
        "matrix_1_description":         _describe(trial["matrix_1"]),
        "matrix_2_description":         _describe(trial["matrix_2"]),
        "matrix_3_description":         _describe(trial["matrix_3"]),
        "matrix_4_description":         _describe(trial["matrix_4"]),
    }


def procedure_loop(win, config, section_type, trials, results, mouse, clock, fixation_point):
    """
        Run the full trial loop for one experiment section (training or experiment).

        For each block, iterates over all trials and presents four stimulus phases
        separated by fixation crosses. After the retrieval phase, collects a mouse
        click response, evaluates accuracy, shows feedback, and appends a result
        row to results. Between blocks (but not after the last block), displays a
        break screen loaded from messages/break.txt with <break_number> replaced
        by the current break index.

        Trial phase structure
        ---------------------
        fixation → matrix_1 → matrix_2 → matrix_3 → matrix_4 (response) → feedback

        Timing
        ------
        - fixation   : config["fixation_time"] seconds
        - matrix_1   : config["stimuli_set_1"] seconds
        - matrix_2   : config["stimuli_set_2"] seconds
        - matrix_3   : config["stimuli_set_3"] seconds
        - matrix_4   : config["stimuli_set_4"] seconds

        Parameters
        ----------
        win : visual.Window
            PsychoPy window object.
        config : dict
            Experiment configuration.
        section_type : str
            "training" or "experiment".
        trials : list of list of dict
            Output of generate_trial_blocks(). Outer list = blocks,
            inner list = trial dicts.
        results : list
            results_beh list from main.py. Result row dicts are appended in place.
        mouse : event.Mouse
            PsychoPy mouse object (visible=False).
        clock : core.Clock
            Shared experiment clock (not used for RT — RT measured locally).
        fixation_point : visual.TextStim
            PsychoPy fixation point.

        Returns
        -------
        list
            The updated results list with one dict appended per trial.
        """
    n_blocks = len(trials)
    t_idx = 0

    logging.info(f"=== PROCEDURE LOOP START: {section_type.upper()} "
                 f"({n_blocks} block(s)) ===")

    for block_idx, block in enumerate(trials):
        n_trials = len(block)
        logging.info(f"  --- Block {block_idx + 1}/{n_blocks} "
                     f"({n_trials} trial(s)) ---")

        for trial in block:
            t_idx += 1
            rt = None
            acc = None
            clicked_index = None
            clicked_stim = None

            logging.info(
                f"  [TRIAL {t_idx}/{n_trials} | "
                f"{trial['task_type'].upper()} | "
                f"{trial['stimulus_type']} | "
                f"n={trial['n_elements']}]"
            )

            # --- Phase 0: Fixation ---
            drwa_stim_for_duration(win=win, stim=fixation_point, time=config["fixation_time"],
                                   clock=clock, end_flip=False)

            # --- Phase 1: matrix_1 ---
            draw_matrix(matrix=trial["matrix_1"], win=win, clock=clock, time=config["matrix_1_time"])

            # --- Phase 2: matrix_2 ---
            draw_matrix(matrix=trial["matrix_2"], win=win, clock=clock, time=config["matrix_2_time"])

            # --- Phase 3: matrix_3 ---
            draw_matrix(matrix=trial["matrix_3"], win=win, clock=clock, time=config["matrix_3_time"])

            stimulus_list = get_stimulus_list(trial["matrix_4"])
            hit_areas = trial["hit_areas"]
            hit_area_stims = [h["stimulus"] for h in hit_areas]
            draw_stim(hit_area_stims, True)
            draw_stim(stimulus_list, True)
            win.callOnFlip(clock.reset)
            win.callOnFlip(mouse.clickReset)
            win.callOnFlip(mouse.setVisible, True)
            win.callOnFlip(mouse.setPos, (0,0))
            win.flip()

            while clock.getTime() < config["matrix_4_time"] and rt is None:
                # buttons = mouse.getPressed()
                # if buttons[0]: # left mouse button pressed
                #     pos = mouse.getPos()
                #     for s in trial["matrix_4"]:
                #         print(pos, s["pos"], s["stimulus"].contains(pos))
                #         if s["stimulus"].contains(pos):
                #             rt = clock.getTime()
                #             break
                # for s in trial["matrix_4"]:
                #     if mouse.isPressedIn(s["stimulus"]):
                #         rt = clock.getTime()
                #         break

                buttons, times = mouse.getPressed(getTime=True)
                if buttons[0]:  # left button down
                    mouse_pos = mouse.getPos()
                    for i, h in enumerate(hit_areas):
                        if h["stimulus"].contains(mouse_pos):
                            rt = times[0]
                            clicked_stim = trial["matrix_4"][i]
                            break

                # Update hover highlight for each hit-area
                for h in hit_areas:
                    update_hit_area_hover(h, mouse, config)

                check_exit()
                win.flip()

            draw_stim(stimulus_list, False)
            draw_stim(hit_area_stims, False)
            win.callOnFlip(mouse.setVisible, False)

            if rt:
                acc, clicked_index = compute_accuracy(trial, clicked_stim=clicked_stim)

            logging.info(
                f"  → acc={acc}  rt={rt:.3f}s  "
                f"clicked_index={clicked_index}"
                if rt is not None else
                f"  → acc={acc}  rt=None  clicked_index={clicked_index}"
            )

            if config[f"feedback_{section_type}"]:
                feedback_acc = -1 if acc is None else acc
                show_feedback(win=win, acc=feedback_acc, config=config, clock=clock)
            else:
                win.flip()


            row = build_result_row(trial=trial, acc=acc, rt=rt, clicked_index=clicked_index, section_type=section_type, trail_idx=t_idx)
            results.append(row)

        # --- Break between blocks (not after the last block) ---
        if block_idx < n_blocks - 1:
            break_number = block_idx + 1
            break_file = os.path.join("messages", "break.txt")
            logging.info(f"  Break {break_number} after block {block_idx + 1}")
            present_text(
                win=win,
                file_name=break_file,
                config=config,
                replacements={"break_number": str(break_number)},
            )

    logging.info(f"=== PROCEDURE LOOP END: {section_type.upper()} ===")