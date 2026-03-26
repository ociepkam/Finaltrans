import random
from procedure_code.figures_generation import ARROW_LABELS, FIGURE_LABELS, create_underline, create_hit_area
from procedure_code.stimulus_position import prepare_stimulus


def generate_relational_trial(win, config, stimulus_type, n_elements):
    """
    Generate all stimulus sets and metadata for a single relational trial.

    In the relational condition, participants must track the ordinal rank of a
    cued stimulus across two displays. The cued position is indicated by an
    underline during the mask phase. The correct answer in matrix_2 is the
    stimulus occupying the same rank (ascending order) as the cued stimulus
    in matrix_1.

    Ordinal order is defined by the insertion order of ARROW_LABELS (angles:
    0, 45, ..., 315) and FIGURE_LABELS (arms: 0, 2, 3, ..., 12).

    Parameters
    ----
    win : visual.Window
        PsychoPy window object.
    config : dict
        Experiment configuration dictionary. Must contain all keys required by
        prepare_stimulus(), create_underline(), and create_mask_dot().
    stimulus_type : str
        Type of stimuli. Must be "arrow" or "figure".
    n_elements : int
        Number of stimuli in the set.

    Returns
    ----
    dict
        A dictionary containing:
            - "matrix_1"  : list of stimulus dicts (original set)
            - "mask"      : list of stimulus dicts (dots + underline on cued pos)
            - "matrix_2"  : list of stimulus dicts (one stimulus changed)
            - "answer"    : dict with keys:
                - "cued_index"    (int):   Index of the cued stimulus in matrix_1.
                - "cued_value"    (int):   Value of the cued stimulus.
                - "cued_rank"     (int):   Rank (0-based) of cued stimulus in matrix_1.
                - "correct_index" (int):   Index of the correct stimulus in matrix_2.
                - "correct_value" (int):   Value of the correct stimulus in matrix_2.
                - "changed_index" (int):   Index of the element changed in matrix_2.
                - "old_value"     (int):   Original value at changed_index.
                - "new_value"     (int):   New value at changed_index.
                - "pos"           (tuple): Position of the correct stimulus in matrix_2.
    """
    # 1. Select pool and rank order
    if stimulus_type == "arrow":
        pool = list(ARROW_LABELS.keys())
    elif stimulus_type == "figure":
        pool = list(FIGURE_LABELS.keys())
    else:
        raise ValueError(f"Invalid stimulus_type: '{stimulus_type}'")

    # 2. Draw n_elements for matrix_1 (no repetitions)
    matrix_1_values = random.sample(pool, n_elements)

    # 3. Prepare matrix_1
    matrix_1 = prepare_stimulus(win, config, stimulus_type, matrix_1_values)

    # 4. Prepare mask dots using prepare_stimulus
    mask_dots = prepare_stimulus(win, config, "mask", [0] * n_elements)

    # 5. Pick a random cued index and add underline to mask
    # Rule 1: changed_idx must be cued_idx.
    # Rule 2: new_val cannot be a neighbor of old_val.
    valid_indices = []
    for idx in range(n_elements):
        old_v = matrix_1_values[idx]
        old_v_rank = pool.index(old_v)
        neighbors = []
        if old_v_rank > 0: neighbors.append(pool[old_v_rank - 1])
        if old_v_rank < len(pool) - 1: neighbors.append(pool[old_v_rank + 1])

        possible_new = [v for v in pool if v not in matrix_1_values and v not in neighbors]
        if possible_new:
            valid_indices.append((idx, possible_new))

    # Pick from valid indices to satisfy Rule 2
    cued_idx, possible_new_vals = random.choice(valid_indices)
    new_val = random.choice(possible_new_vals)
    old_val = matrix_1_values[cued_idx]
    changed_idx = cued_idx

    cued_stim = mask_dots[cued_idx]["stimulus"]
    underline = create_underline(win, config, cued_stim)

    mask_with_uderline = mask_dots + [underline]

    # 6. Determine rank of cued stimulus in matrix_1 (ascending by pool order)
    sorted_values = sorted(matrix_1_values, key=lambda v: pool.index(v))
    cued_value = matrix_1_values[cued_idx]
    cued_rank = sorted_values.index(cued_value)

    # 7. Create matrix_2 values
    matrix_2_values = list(matrix_1_values)
    matrix_2_values[changed_idx] = new_val

    # 8. Find correct answer: stimulus at cued_rank in sorted matrix_2
    sorted_matrix_2 = sorted(matrix_2_values, key=lambda v: pool.index(v))
    correct_value = sorted_matrix_2[cued_rank]
    correct_index = matrix_2_values.index(correct_value)

    # 9. Prepare matrix_2
    matrix_2 = prepare_stimulus(win, config, stimulus_type, matrix_2_values)

    # 10. Build hit-areas aligned with matrix_4 (= matrix_2) positions
    hit_areas = [create_hit_area(win, config, s["pos"]) for s in matrix_2]

    # 11. Package answer metadata
    answer = {
        "cued_index": cued_idx,
        "cued_value": cued_value,
        "cued_rank": cued_rank,
        "correct_index": correct_index,
        "correct_value": correct_value,
        "changed_index": changed_idx,
        "old_value": old_val,
        "new_value": new_val,
        "pos": matrix_2[correct_index]["pos"],
    }

    return {
        "matrix_1": mask_with_uderline,
        "matrix_2": matrix_1,
        "matrix_3": mask_dots,
        "matrix_4": matrix_2,
        "hit_areas": hit_areas,
        "answer": answer,
    }


# For tests
if __name__ == "__main__":
    from psychopy import visual, core, event
    from src.load_data import load_config
    from os.path import join

    config = load_config(join("..", "config.yaml"))
    win = visual.Window(color="white", units="pix", fullscr=True)


    def draw_stimuli(stim_list):
        for s in stim_list:
            s["stimulus"].draw()


    def draw_phase(stim_list, label_text, duration):
        label = visual.TextStim(win, text=label_text, pos=(0, -350),
                                color="gray", height=22)
        draw_stimuli(stim_list)
        label.draw()
        win.flip()
        core.wait(duration)


    for stimulus_type in ["arrow", "figure"]:
        for n in [2, 4, 6]:

            trial = generate_relational_trial(win, config, stimulus_type, n)
            ans = trial["answer"]

            # Phase 1: Mask with underline (cued position)
            draw_phase(
                trial["matrix_1"],
                f"{stimulus_type.upper()}  n={n}  |  CUE  "
                f"(cued_idx={ans['cued_index']}  rank={ans['cued_rank']})",
                duration=2.0
            )

            # Phase 2: Matrix 1 (encoding)
            draw_phase(
                trial["matrix_2"],
                f"{stimulus_type.upper()}  n={n}  |  ENCODING",
                duration=3.0
            )

            draw_phase(
                trial["matrix_3"],
                f"{stimulus_type.upper()}  n={n}  |  ENCODING",
                duration=1.0
            )

            # Phase 3: Matrix 2 (retrieval) — highlight correct answer
            highlight = visual.Circle(
                win,
                radius=40,
                edges=128,
                lineColor="red",
                fillColor=None,
                lineWidth=2,
                pos=ans["pos"]
            )
            draw_stimuli(trial["matrix_4"])
            highlight.draw()
            info = visual.TextStim(
                win,
                text=(f"{stimulus_type.upper()}  n={n}  |  RETRIEVAL\n"
                      f"cued={ans['cued_value']} (rank {ans['cued_rank']})  "
                      f"correct={ans['correct_value']}  "
                      f"changed: {ans['old_value']} → {ans['new_value']}"),
                pos=(0, -350),
                color="gray",
                height=22
            )
            info.draw()
            win.flip()
            core.wait(3.0)

            # Inter-trial blank
            win.flip()
            core.wait(0.5)

            if "escape" in event.getKeys():
                break

    win.close()