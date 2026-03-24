import random
from procedure_code.figures_generation import ARROW_LABELS, FIGURE_LABELS
from procedure_code.stimulus_position import prepare_stimulus


def generate_memory_trial(win, config, stimulus_type, n_elements):
    """
    Generate all stimulus sets and metadata for a single memory trial.

    This function creates:
    1. matrix_1: The initial set of stimuli to be encoded.
    2. mask: A set of dots at the same positions to mask the encoding.
    3. matrix_2: The retrieval set where exactly one stimulus has changed.
    4. answer: Metadata about what changed and where.

    Parameters
    ----------
    win : visual.Window
        PsychoPy window object.
    config : dict
        Experiment configuration.
    stimulus_type : str
        "arrow" or "figure".
    n_elements : int
        Number of stimuli in the set.

    Returns
    -------
    dict
        A dictionary containing:
            - "matrix_1": list of stimulus dicts (original)
            - "mask":     list of stimulus dicts (dots)
            - "matrix_2": list of stimulus dicts (one changed)
            - "answer":   dict with keys:
                - "changed_index": int (0 to n-1)
                - "old_value":     int (original rotation/arms)
                - "new_value":     int (new rotation/arms)
                - "pos":           tuple (x, y) of the change
    """
    # 1. Select the pool of possible values
    if stimulus_type == "arrow":
        pool = list(ARROW_LABELS.keys())
    elif stimulus_type == "figure":
        pool = list(FIGURE_LABELS.keys())
    else:
        raise ValueError(f"Invalid stimulus_type: {stimulus_type}")

    # 2. Draw n_elements for matrix_1 (no repetitions)
    matrix_1_values = random.sample(pool, n_elements)

    # 3. Prepare matrix_1 and mask
    matrix_1 = prepare_stimulus(win, config, stimulus_type, matrix_1_values)
    mask = prepare_stimulus(win, config, "mask", [0] * n_elements)

    # 4. Create matrix_2 values
    # Pick a random index to change
    changed_idx = random.randrange(n_elements)
    old_val = matrix_1_values[changed_idx]

    # Find a new value that is NOT in the current matrix_1
    remaining_pool = [v for v in pool if v not in matrix_1_values]
    new_val = random.choice(remaining_pool)

    matrix_2_values = list(matrix_1_values)
    matrix_2_values[changed_idx] = new_val

    # 5. Prepare matrix_2
    matrix_2 = prepare_stimulus(win, config, stimulus_type, matrix_2_values)

    # 6. Package the answer metadata
    answer = {
        "changed_index": changed_idx,
        "old_value": old_val,
        "new_value": new_val,
        "pos": matrix_1[changed_idx]["pos"]
    }

    return {
        "matrix_1": matrix_1,
        "mask": mask,
        "matrix_2": matrix_2,
        "answer": answer
    }


# For tests
if __name__ == "__main__":
    from psychopy import visual, core, event

    config = {
        "stimulus_center": (0, 0),
        "stimulus_distance_from_center": 30,
        "mask_dot_size": 20,
        "stimulus_color": "black",
        "arrow_size": 2,
        "stimulus_arrow_width": 2,
        "figure_size": 10,
        "stimulus_figure_width": 2,
        "dot_size": 3,
    }

    win = visual.Window(color="white", units="pix", fullscr=True)

    def draw_stimuli(stim_list):
        for s in stim_list:
            s["stimulus"].draw()

    def draw_phase(stim_list, label_text, duration):
        """Draw stimuli with a phase label and wait."""
        label = visual.TextStim(win, text=label_text, pos=(0, -200),
                                color="gray", height=22)
        draw_stimuli(stim_list)
        label.draw()
        win.flip()
        core.wait(duration)

    # --- Run trials for both types and a few set sizes ---
    for stimulus_type in ["arrow", "figure"]:
        for n in [2, 4, 6]:

            trial = generate_memory_trial(win, config, stimulus_type, n)
            print(trial)
            # Phase 1: Matrix 1 (encoding)
            draw_phase(
                trial["matrix_1"],
                f"{stimulus_type.upper()}  n={n}  |  ENCODING",
                duration=2.0
            )

            # Phase 2: Mask
            draw_phase(
                trial["mask"],
                f"{stimulus_type.upper()}  n={n}  |  MASK",
                duration=1.0
            )

            # Phase 3: Matrix 2 (retrieval) — highlight changed position
            ans = trial["answer"]
            highlight = visual.Circle(
                win,
                radius=20,
                lineColor="red",
                fillColor=None,
                pos=ans["pos"]
            )
            draw_stimuli(trial["matrix_2"])
            highlight.draw()
            info = visual.TextStim(
                win,
                text=(f"{stimulus_type.upper()}  n={n}  |  RETRIEVAL\n"
                      f"changed idx={ans['changed_index']}  "
                      f"{ans['old_value']} → {ans['new_value']}"),
                pos=(0, -200),
                color="gray",
                height=22
            )
            info.draw()
            win.flip()
            core.wait(3.0)

            # Inter-trial blank
            win.flip()
            core.wait(0.5)

            # Allow early exit with Escape
            if "escape" in event.getKeys():
                break

    win.close()