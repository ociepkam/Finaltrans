from psychopy import visual, core
import numpy as np

ARROW_LABELS = {
    0:   '↑',
    45:  '↗',
    90:  '→',
    135: '↘',
    180: '↓',
    225: '↙',
    270: '←',
    315: '↖',
}


FIGURE_LABELS = {
    0: 'dot',
    2: 'line_horizontal',
    3: 'inverted_y',
    4: 'x_shape',
    5: '5_arms',
    6: '6_arms',
    8: '8_arms',
    12: '12_arms'
}


LETTER_LABELS = {
    'B': 'B',
    'D': 'D',
    'H': 'H',
    'K': 'K',
    'N': 'N',
    'P': 'P',
    'T': 'T',
    'Z': 'Z'
}


def create_arrow(win, config, pos, rotation):
    """
        Create an arrow stimulus using PsychoPy's ShapeStim.

        Parameters
        ----------
        config : dict
            Experiment configuration dictionary. Must contain:
                - "arrow_size" (float or tuple): Scaling factor applied to the base
                  arrow vertices. A value of 1.0 uses the original vertex coordinates.
                  Pass a tuple (sx, sy) to scale width and height independently.
        pos : tuple of float
            (x, y) position of the arrow centre in PsychoPy height units.
        rotation : int
            Clockwise rotation in degrees from the upward Y-axis.
            Must be one of the keys defined in ARROW_LABELS:
            0 (↑), 45 (↗), 90 (→), 135 (↘), 180 (↓), 225 (↙), 270 (←), 315 (↖).

        Returns
        -------
        dict
            A stimulus descriptor with the following keys:
                - "stim_type"  (str):                Always "arrow".
                - "stim_label" (str):                Unicode arrow symbol (e.g. "↗").
                - "pos"        (tuple of float):     Position passed to the function.
                - "stimulus"   (visual.ShapeStim):   The PsychoPy stimulus object.
    """
    arrow_stim = visual.ShapeStim(
        win,
        vertices=[(0, -5), (0, 5), (-2, 3), (0, 5), (2, 3)],
        closeShape=False, lineColor=config["stimulus_color"], lineWidth=config["stimulus_arrow_width"],
        ori=rotation,  # 0 = Up, 90 = Right, etc.
        pos=pos,
        size=config["arrow_size"]
    )
    stimulus = {"stim_type": "arrow",
                "stim_label": ARROW_LABELS[rotation],
                "pos": pos,
                "stimulus": arrow_stim}
    return stimulus


def create_figure(win, config, pos, n_arms):
    """
    Create a star-like figure stimulus with n arms radiating from the center.

    Parameters
    ----------
    config : dict
        Experiment configuration dictionary. Must contain:
            - "figure_size" (float): The length of each arm (radius).
            - "line_width" (int): Thickness of the lines.
            - "dot_size" (float): Diameter of the dot for n_arms=0.
    pos : tuple of float
        (x, y) position of the figure center in PsychoPy height units.
    n_arms : int
        Number of arms to generate. Supported: 0, 2, 3, 4, 5, 6, 8, 12.

    Returns
    -------
    dict
        A stimulus descriptor with the following keys:
            - "stim_type"  (str):                Always "figure".
            - "stim_label" (str):                Label from FIGURE_LABELS.
            - "pos"        (tuple of float):     Position passed to the function.
            - "stimulus"   (visual.BaseVisual):  The PsychoPy stimulus object.
            :param win:
    """

    # Case 0: A simple dot (Circle)
    if n_arms == 0:
        fig_stim = visual.Circle(
            win, radius=config["dot_size"] / 2,
            fillColor=config["stimulus_color"], lineColor=config["stimulus_color"], pos=pos,
            edges=128
        )

    else:
        # Define starting angles (in degrees) based on your requirements
        # 0 degrees is "Up" in PsychoPy
        angles = []

        if n_arms == 2:
            # Horizontal line: arms at 90 (Right) and 270 (Left)
            angles = [90, 270]

        elif n_arms == 3:
            # Inverted Y: 120 deg apart, one arm pointing straight Up (0)
            # Resulting angles: 0, 60, 300
            angles = [0, 120, 240]

        elif n_arms == 4:
            # X shape: 90 deg apart, diagonal (45, 135, 225, 315)
            angles = [45, 135, 225, 315]

        else:
            # 5, 6, 8, 12: One arm pointing Up (0), others evenly distributed
            step = 360.0 / n_arms
            angles = [i * step for i in range(n_arms)]

        # Create vertices for ShapeStim
        # Each arm is a separate line segment from (0,0) to (radius * angle)
        # We represent this as a single path that returns to center after each arm
        vertices = []
        radius = config["figure_size"]

        for deg in angles:
            rad = np.radians(deg)
            # PsychoPy 0 deg is Up (Y+), so x=sin, y=cos
            dest_x = radius * np.sin(rad)
            dest_y = radius * np.cos(rad)
            vertices.extend([(0, 0), (dest_x, dest_y)])

        fig_stim = visual.ShapeStim(
            win,
            vertices=vertices,
            closeShape=False,
            lineColor=config["stimulus_color"],
            lineWidth=config["stimulus_figure_width"],
            pos=pos
        )

    stimulus = {
        "stim_type": "figure",
        "stim_label": FIGURE_LABELS[n_arms],
        "pos": pos,
        "stimulus": fig_stim
    }

    return stimulus


def create_mask_dot(win, config, pos):
    """
        Create a filled circular dot used as a masking stimulus.

        Mask dots are used to visually occlude or replace figure stimuli
        during masking phases of the trial (e.g., backward masking or
        placeholder displays). They share the same color as regular stimuli
        to ensure perceptual uniformity.

        Parameters
        ----------
        config : dict
            Experiment configuration dictionary. Must contain:
                - "mask_dot_size"   (float): Diameter of the dot in PsychoPy
                                             height units.
                - "stimulus_color"  (str or list): Fill and line color of the dot
                                                   (e.g., 'black' or [-1, -1, -1]).
        pos : tuple of float
            (x, y) position of the dot centre in PsychoPy height units.

        Returns
        -------
        dict
            A stimulus descriptor with the following keys:
                - "stim_type"  (str):              Always "mask_dot".
                - "stim_label" (None):             Always None (mask has no identity).
                - "pos"        (tuple of float):   Position passed to the function.
                - "stimulus"   (visual.Circle):    The PsychoPy stimulus object.
    """
    fig_stim = visual.Circle(
        win, radius=config["mask_dot_size"] / 2,
        fillColor=config["stimulus_color"],
        lineColor=config["stimulus_color"],
        pos=pos,
        edges=128
    )

    stimulus = {
        "stim_type": "mask_dot",
        "stim_label": None,
        "pos": pos,
        "stimulus": fig_stim
    }

    return stimulus


def create_letter(win, config, pos, letter):
    """
    Create a letter stimulus using PsychoPy's TextStim.

    Parameters
    ----------
    win : visual.Window
        PsychoPy window object.
    config : dict
        Experiment configuration dictionary. Must contain:
            - "letter_height" (float): Height of the letter stimulus.
            - "letter_color" (str or list): Color of the text.
    pos : tuple of float
        (x, y) position of the letter center.
    letter : str
        The letter to display. Must be one of the keys in LETTER_LABELS.

    Returns
    -------
    dict
        A stimulus descriptor with the following keys:
            - "stim_type"  (str):                Always "letter".
            - "stim_label" (str):                The letter character (e.g. "B").
            - "pos"        (tuple of float):     Position passed to the function.
            - "stimulus"   (visual.TextStim):    The PsychoPy stimulus object.
    """
    if letter not in LETTER_LABELS:
        raise ValueError(f"Letter {letter} not found in LETTER_LABELS")

    letter_stim = visual.TextStim(
        win,
        text=LETTER_LABELS[letter],
        pos=pos,
        height=config["letter_height"],
        color=config["letter_color"],
        units='pix', # lub inne jednostki zgodne z Twoim win/config
        alignHoriz='center',
        alignVert='center'
    )

    stimulus = {
        "stim_type": "letter",
        "stim_label": LETTER_LABELS[letter],
        "pos": pos,
        "stimulus": letter_stim
    }
    return stimulus


def create_underline(win, config, stimulus, fig_size=None):
    """
    Create an underline stimulus positioned relative to a given base stimulus.

    The underline is a horizontal line placed slightly below the bounding area
    of the provided stimulus. Size is determined either from an explicit parameter
    or inferred automatically from the stimulus type.

    Parameters
    ----------
    config : dict
        Experiment configuration dictionary. Must contain:
            - "underline_extra_x_size"   (float): Additional width added to the
              underline beyond the stimulus width.
            - "underline_extra_y_distance" (float): Vertical offset from the
              bottom of the stimulus (typically negative to place below).
            - "underline_color" (str or list): Line color of the underline.
            - "underline_width" (float or int): Line thickness.
    stimulus : visual.BaseVisual
        PsychoPy stimulus object (e.g., Circle, ShapeStim). Must have a `.pos`
        attribute.
    fig_size : float, optional
        Explicit size (width/diameter) of the stimulus in the same units as the
        window. If None, size is inferred automatically:
            - visual.Circle  → radius * 2
            - visual.ShapeStim → not reliable; prefer passing fig_size explicitly.

    Returns
    -------
    dict
        A stimulus descriptor with the following keys:
            - "stim_type"  (str):                Always "underline".
            - "stim_label" (None):               Always None.
            - "pos"        (tuple of float):     Position of the base stimulus.
            - "stimulus"   (visual.ShapeStim):   The underline stimulus object.
    """
    pos = stimulus.pos

    if fig_size is None:
        if hasattr(stimulus, 'radius'):
            fig_size = stimulus.radius * 2
        else:
            raise ValueError(
                "Cannot infer fig_size from ShapeStim. "
                "Pass fig_size explicitly to create_underline()."
            )

    # underline_pos = (
    #     pos[0] - fig_size/2 - config["underline_extra_x_size"]/2,
    #     pos[1] - fig_size/2 + config["underline_extra_y_distance"]
    # )

    fig_stim = visual.Rect(
        win,
        size=(fig_size+config["underline_extra_size"]),
        lineColor = config["underline_color"],
        lineWidth = config["underline_width"],
        pos = pos
    )

    # fig_stim = visual.ShapeStim(
    #     win,
    #     vertices=[(0, 0), (fig_size + config["underline_extra_x_size"], 0)],
    #     closeShape=False,
    #     lineColor=config["underline_color"],
    #     lineWidth=config["underline_width"],
    #     pos=underline_pos
    # )

    stimulus = {
        "stim_type": "underline",
        "stim_label": None,
        "pos": pos,
        "stimulus": fig_stim
    }

    return stimulus


def create_hit_area(win, config, pos):
    """
    Create an invisible rectangular hit-area used for mouse click detection.

    Because PsychoPy's ShapeStim.contains() operates on the convex hull of
    vertices, thin line stimuli (arrows, star figures) have a near-zero
    clickable area. This function creates a square Rect centred on the
    stimulus position that acts as a reliable click target.

    The hit-area is normally invisible (opacity 0). When the mouse hovers
    over it, it becomes visible with a configurable highlight style, provided
    that ``hit_area_show_hover`` is True in config.

    To use hover highlighting, call ``update_hit_area_hover(hit_area_dict,
    mouse)`` once per frame inside the response loop.

    Parameters
    ----
    win : visual.Window
        PsychoPy window object.
    config : dict
        Experiment configuration dictionary. Must contain:
            - "hit_area_size"        (float): Side length of the square in pixels.
            - "hit_area_show_hover"  (bool):  If True, the rect becomes visible
              on hover.
            - "hit_area_hover_color" (str):   Line color when hovered
              (e.g. "white").
            - "hit_area_hover_width" (int):   Line width in pixels when hovered.
            - "hit_area_hover_fill"  (str or None): Fill color when hovered.
              Use None for transparent fill.
    pos : tuple of float
        (x, y) centre position in pixels.

    Returns
    ----
    dict
        A stimulus descriptor with the following keys:
            - "stim_type"  (str):            Always "hit_area".
            - "stim_label" (None):           Always None.
            - "pos"        (tuple of float): Position passed to the function.
            - "stimulus"   (visual.Rect):    The PsychoPy Rect object.
    """
    rect = visual.Rect(
        win,
        width=config["hit_area_size"],
        height=config["hit_area_size"],
        pos=pos,
        lineColor=None,
        fillColor=None,
        opacity=0,
        lineWidth=config["hit_area_hover_width"],
    )
    return {
        "stim_type": "hit_area",
        "stim_label": None,
        "pos": pos,
        "stimulus": rect,
    }


# Plot all figures for testing
if __name__ == "__main__":
    from src.load_data import load_config
    from os.path import join

    config = load_config(join("..", "config.yaml"))
    win = visual.Window(color='white', units='pix', fullscr=True)

    for i, e in enumerate(ARROW_LABELS.keys()):
        a = create_arrow(win, config, (-300 + i*40, 0), e)
        a["stimulus"].draw()
    for i, e in enumerate(FIGURE_LABELS.keys()):
        a = create_figure(win, config, (-300 + i * 40, -100), e)
        a["stimulus"].draw()
    for i, l in enumerate(LETTER_LABELS.keys()):
        let = create_letter(win, config, (-300 + i * 40, -200), l)
        let["stimulus"].draw()

    a = create_underline(win, config, a["stimulus"], fig_size=config["figure_size"] * 2)
    a["stimulus"].draw()

    a = create_mask_dot(win, config, (100, 0))
    a["stimulus"].draw()

    a = create_mask_dot(win, config, (100, -100))
    a["stimulus"].draw()

    a = create_underline(win, config, a["stimulus"])
    a["stimulus"].draw()

    win.flip()
    core.wait(6.0)