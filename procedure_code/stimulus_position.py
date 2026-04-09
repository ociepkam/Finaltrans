import numpy as np

from procedure_code.figures_generation import create_arrow, create_figure, create_letter, create_mask_dot


def get_stimuli_positions(config, n_elements):
    """
    Calculate coordinates for a set of stimuli arranged symmetrically on a circle.

    The function ensures vertical symmetry (left-right balance) for any number 
    of elements. For odd numbers, one element is placed at the bottom (6 o'clock).
    For even numbers, elements are rotated so they straddle the vertical axis.

    Parameters
    ----------
    config : dict
        Experiment configuration dictionary. Must contain:
            - "stimulus_center" (tuple of float): (x, y) center of the arrangement.
            - "stimulus_distance_from_center" (float): Radius of the circle (dist).
    n_elements : int
        Number of positions to calculate (e.g., 1 to 6).

    Returns
    -------
    list of tuples
        A list of (x, y) coordinates for the stimuli.
    """
    center_x, center_y = config["stimulus_center"]
    dist = config["stimulus_distance_from_center"]

    # Case 1: Single element at the center
    if n_elements == 1:
        return [(center_x, center_y)]

    # Case 2: Two elements (Horizontal layout as requested)
    if n_elements == 2:
        return [
            (center_x - dist, center_y),
            (center_x + dist, center_y)
        ]

    # Case 3+: Circular arrangement with vertical symmetry
    positions = []

    # Calculate the angular offset to ensure symmetry
    # For odd n: One point at 270 degrees (bottom)
    # For even n: Points straddle the 90/270 axis (e.g., for 4: 45, 135, 225, 315)
    if n_elements % 2 != 0:
        # Odd: Start at 270 deg (bottom)
        start_angle = 270.0
    else:
        # Even: Offset by half the step to avoid points exactly at 90/270
        step = 360.0 / n_elements
        start_angle = 270.0 - (step / 2.0)

    for i in range(n_elements):
        # Calculate angle in degrees, then convert to radians
        # We subtract to move clockwise
        angle_deg = (start_angle - i * (360.0 / n_elements)) % 360
        angle_rad = np.radians(angle_deg)

        # Standard polar to cartesian: x = r*cos, y = r*sin
        x = center_x + dist * np.cos(angle_rad)
        y = center_y + dist * np.sin(angle_rad)

        positions.append((x, y))

    return positions


def prepare_stimulus(win, config, stimulus_type, figures):
    """
    Prepare a list of stimuli of a given type, arranged symmetrically on a circle.

    Positions are calculated automatically based on the number of elements using
    get_stimuli_positions(). Each stimulus is then created at its corresponding
    position using the appropriate creation function.

    Parameters
    ----------
    win : visual.Window
        PsychoPy window object passed to stimulus creation functions.
    config : dict
        Experiment configuration dictionary. Must contain all keys required by
        get_stimuli_positions() and the relevant creation function:
            - "stimulus_center", "stimulus_distance_from_center"
            - For arrows:  "arrow_size", "stimulus_color", "stimulus_arrow_width"
            - For figures: "figure_size", "stimulus_color", "stimulus_figure_width", "dot_size"
            - For masks:   "mask_dot_size", "stimulus_color"
    stimulus_type : str
        Type of stimulus to create. Must be one of:
            - "arrow"  — keys from ARROW_LABELS (0, 45, 90, ..., 315)
            - "figure" — keys from FIGURE_LABELS (0, 2, 3, 4, 5, 6, 8, 12)
            - "letter" — keys from LETTER_LABELS (B D H K N P T Z)
            - "mask"   — values are ignored; only len(figures) matters
    figures : list
        List of stimulus identifiers. Length determines the number of stimuli
        and their positions. Interpretation depends on stimulus_type:
            - "arrow":  list of int rotation values (e.g. [0, 90, 180])
            - "figure": list of int arm counts   (e.g. [3, 4, 6])
            - "letter": list of strings (e.g. ["A", "D", "Z"])
            - "mask":   list of any values       (e.g. [0, 0, 0])

    Returns
    -------
    list of dict
        A list of stimulus descriptors, each as returned by the corresponding
        creation function (create_arrow, create_figure, or create_mask_dot).

    Raises
    ------
    ValueError
        If stimulus_type is not one of "arrow", "figure", "letter", or "mask".
    """
    positions = get_stimuli_positions(config, len(figures))

    stimuli = []
    for pos, fig in zip(positions, figures):
        if stimulus_type == "arrow":
            stim = create_arrow(win, config, pos, rotation=fig)
        elif stimulus_type == "figure":
            stim = create_figure(win, config, pos, n_arms=fig)
        elif stimulus_type == "letter":
            stim = create_letter(win, config, pos, letter=fig)
        elif stimulus_type == "mask":
            stim = create_mask_dot(win, config, pos)
        else:
            raise ValueError(
                f"Unknown stimulus_type: '{stimulus_type}'. "
                "Expected one of: 'arrow', 'figure', 'mask'."
            )
        stimuli.append(stim)

    return stimuli


# For tests
if __name__ == "__main__":
    import random
    from psychopy import visual, core
    from procedure_code.figures_generation import ARROW_LABELS, FIGURE_LABELS

    # Minimal config for testing
    config = {
        "stimulus_center": (0, 0),
        "stimulus_distance_from_center": 30,
        "mask_dot_size": 10,
        "stimulus_color": "black",
        "arrow_size": 1.5,
        "stimulus_arrow_width": 1,
        "figure_size": 10,
        "stimulus_figure_width": 1,
        "dot_size": 3,
    }

    win = visual.Window(color="white", units="pix", fullscr=True)

    n_cols = 6
    col_spacing = 150
    row_spacing = 150
    start_x = -(n_cols - 1) * col_spacing / 2

    # Row centers: arrows top, figures middle, masks bottom
    row_centers_y = [row_spacing, 0, -row_spacing]
    row_labels   = ["arrows", "figures", "masks"]

    arrow_keys  = list(ARROW_LABELS.keys())   # [0, 45, 90, 135, 180, 225, 270, 315]
    figure_keys = list(FIGURE_LABELS.keys())  # [0, 2, 3, 4, 5, 6, 8, 12]

    for n in range(1, n_cols + 1):
        col_offset_x = start_x + (n - 1) * col_spacing

        # --- Row 0: arrows ---
        arrows_sample = random.sample(arrow_keys, n)
        col_config = {**config, "stimulus_center": (col_offset_x, row_centers_y[0])}
        stims = prepare_stimulus(win, col_config, "arrow", arrows_sample)
        for s in stims:
            s["stimulus"].draw()

        # --- Row 1: figures ---
        figures_sample = random.sample(figure_keys, n)
        col_config = {**config, "stimulus_center": (col_offset_x, row_centers_y[1])}
        stims = prepare_stimulus(win, col_config, "figure", figures_sample)
        for s in stims:
            s["stimulus"].draw()

        # --- Row 2: masks ---
        col_config = {**config, "stimulus_center": (col_offset_x, row_centers_y[2])}
        stims = prepare_stimulus(win, col_config, "mask", [0] * n)
        for s in stims:
            s["stimulus"].draw()

        # Column label (n=X) below masks row
        visual.TextStim(
            win,
            text=f"n={n}",
            pos=(col_offset_x, row_centers_y[2] - 120),
            color="black",
            height=20
        ).draw()

    # Row labels on the left
    for label_text, y in zip(row_labels, row_centers_y):
        visual.TextStim(
            win,
            text=label_text,
            pos=(start_x - 120, y),
            color="gray",
            height=20
        ).draw()

    win.flip()
    core.wait(10.0)
    win.close()