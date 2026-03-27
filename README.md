### README

#### Project Overview
This project implements a PsychoPy-based behavioral experiment for studying cognitive processing using memory and relational trials. The experiment consists of a training phase followed by the main experimental phase, with stimuli presented visually and participant responses recorded.

#### Features
- Training and experimental blocks
- Two trial types: memory and relation
- Configurable stimuli and display settings via YAML
- Reaction time and accuracy recording
- Automatic behavioral data saving
- Modular structure for easy extension

#### Project Structure
- `main.py` – entry point of the experiment
- `config.yaml` – experiment configuration (stimuli, colors, timing, etc.)
- `src/` – core utilities:
  - experiment setup (participant info, logging)
  - monitor and window configuration
  - data loading
  - trigger handling
  - instructions presentation
- `procedure_code/` – experimental logic:
  - block and trial generation
  - procedure loop
  - stimulus generation and positioning
  - trial types (memory, relation)

#### Requirements
- Python 3.x
- PsychoPy

Install dependencies:
```
pip install psychopy, yaml
```

#### How to Run
Run the main script:
```
python main.py
```

You will be prompted to enter participant information before the experiment begins.

#### Output
Behavioral results include:
- accuracy (acc)
- reaction time (rt)
- trial type and condition details
- participant responses vs. correct answers
- detailed stimulus descriptions

Results are automatically saved with a timestamp and participant ID.

#### Configuration
All experiment parameters can be modified in `config.yaml`, including:
- screen settings (color, resolution, fixation)
- stimulus properties
- timing and sequence settings

#### Notes
- The experiment runs in full-screen mode by default.
- Make sure your monitor configuration is correctly set in `monitor_setup.py`.
- Data is saved automatically on exit.