import atexit
import csv
import time
from os.path import join
from typing import Dict, List, Optional
from psychopy import logging

try:
    import parallel
    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False


class TriggerHandler:
    """
    Handles communication with the BioSemi trigger interface.

    Configuration is loaded from config.yaml via load_config(). The following
    keys are supported under the 'trigger' section:

        trigger:
          dummy_mode: true          # If true, no signal is sent to EEG hardware
          trigger_time: 0.004       # Delay (seconds) between trigger onset and clear
          trigger_limit: 60         # Counter wraps back to 1 after this value
          trigger_params:           # Extra columns to record alongside each trigger
            - corr
            - key

    Usage example:
        config = load_config()
        TRIGGERS = TriggerHandler(
            trigger_types=TriggerTypes.vals(),
            config=config,
        )
        TRIGGERS.register_save_trigger_map(part_id=part_id, timestamp=session_time)

        TRIGGERS.set_curr_trial_start()
        TRIGGERS.send_trigger(TriggerTypes.MATRIX)
        # or: win.callOnFlip(TRIGGERS.send_trigger, TriggerTypes.MATRIX, with_delay=False)
        TRIGGERS.send_clear()
        TRIGGERS.add_info_to_last_trigger(dict(corr=corr, key=key[0]), how_many=-1)
    """

    def __init__(
        self,
        trigger_types: List[str],
        config: Optional[Dict] = None,
    ) -> None:
        """
        Args:
            trigger_types: List of allowed trigger type strings.
            config:         Full config dict as returned by load_config().
                            Reads the nested 'trigger' key if present.
        """
        cfg = (config or {}).get("trigger", {})

        self.dummy_mode: bool = cfg.get("dummy_mode", True)
        self.trigger_time: float = cfg.get("trigger_time", 0.004)
        self._trigger_limit: int = cfg.get("trigger_limit", 60)
        extra_params: List[str] = cfg.get("trigger_params") or []

        self._triggers: List[Dict] = []
        self._clear_trigger: int = 0x00
        self._trigger_counter: int = 1
        self._marker_pos: int = -1

        self.trigger_types = trigger_types
        self.trigger_params: List[str] = ["trigger_no", "trigger_type"] + list(extra_params)

        self.PORT = None
        if not self.dummy_mode:
            self._connect_parallel()

        logging.info(
            f"TriggerHandler initialised | dummy_mode={self.dummy_mode} | "
            f"trigger_time={self.trigger_time} | trigger_limit={self._trigger_limit} | "
            f"trigger_params={self.trigger_params}"
        )
        if not extra_params:
            logging.warning(
                "TriggerHandler: no extra trigger_params configured — "
                "only trigger_no and trigger_type will be recorded."
            )

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _connect_parallel(self) -> None:
        if not PARALLEL_AVAILABLE:
            logging.critical("TriggerHandler: 'parallel' library not found — falling back to dummy mode.")
            self.dummy_mode = True
            return
        self.PORT = parallel.Parallel()
        logging.info("TriggerHandler: connected to EEG via parallel port.")

    def connect_to_eeg(self) -> None:
        """
        Connect to EEG hardware post-construction (e.g. after config is loaded).
        Has no effect if already connected.
        """
        if self.PORT is not None:
            logging.warning("TriggerHandler.connect_to_eeg(): connection already established — skipping.")
            return
        self.dummy_mode = False
        self._connect_parallel()

    # ------------------------------------------------------------------
    # Trigger sending
    # ------------------------------------------------------------------

    def send_trigger(
        self,
        trigger_type: str,
        info: Optional[Dict] = None,
        with_delay: bool = True,
    ) -> None:
        """
        Send a trigger to EEG and record it internally.

        Args:
            trigger_type: Must be one of the values passed as trigger_types.
            info:         Optional dict of extra parameters to attach to this trigger.
            with_delay:   If True, sleep trigger_time then send clear automatically.
                          Set to False when called via win.callOnFlip() and follow up
                          with an explicit send_clear().
        """
        if trigger_type not in self.trigger_types:
            logging.critical(f"TriggerHandler: unknown trigger type '{trigger_type}'.")
            raise ValueError(f"Unknown trigger type: '{trigger_type}'.")

        if not self.dummy_mode:
            self.PORT.setData(self._trigger_counter)
            logging.info(f"TriggerHandler: value {self._trigger_counter} sent to EEG.")

        if with_delay:
            time.sleep(self.trigger_time)
            if not self.dummy_mode:
                self.PORT.setData(self._clear_trigger)
                logging.info("TriggerHandler: clear sent after delay.")

        curr_trigger: Dict = {
            "trigger_no": self._trigger_counter,
            "trigger_type": trigger_type,
        }

        if info is not None:
            unregistered = set(info) - set(self.trigger_params)
            if unregistered:
                logging.warning(
                    f"TriggerHandler: unregistered params {sorted(unregistered)} will not be saved."
                )
            curr_trigger.update({k: v for k, v in info.items() if k in self.trigger_params})

        self._trigger_counter += 1
        if self._trigger_counter > self._trigger_limit:
            self._trigger_counter = 1

        self._triggers.append(curr_trigger)

        if self._marker_pos >= 0:
            self._marker_pos += 1

        logging.info(
            f"TriggerHandler: trigger recorded — {curr_trigger}"
        )

    def send_clear(self) -> None:
        """Manually send a clear (0x00) signal to EEG."""
        if not self.dummy_mode:
            self.PORT.setData(self._clear_trigger)
            logging.info("TriggerHandler: manual clear sent to EEG.")

    # ------------------------------------------------------------------
    # Trial markers
    # ------------------------------------------------------------------

    def set_curr_trial_start(self) -> None:
        """Mark the beginning of a new trial for use with add_info_to_last_trigger(how_many=-1)."""
        if self._marker_pos != -1:
            logging.warning(
                "TriggerHandler.set_curr_trial_start(): previous trial marker was never consumed."
            )
        self._marker_pos = 0
        logging.info("TriggerHandler: trial start marker set.")

    def add_info_to_last_trigger(self, info: Dict, how_many: int = 1) -> None:
        """
        Attach extra info to already-recorded triggers (e.g. correctness known only after response).

        Args:
            info:     Dict of key-value pairs to add.
            how_many: Number of most-recent triggers to update.
                      Pass -1 to update all triggers since the last set_curr_trial_start().
        """
        if how_many < -1:
            raise ValueError(f"how_many must be >= -1, got {how_many}.")

        if how_many == -1:
            if self._marker_pos == -1:
                raise RuntimeError("No trial marker set — call set_curr_trial_start() first.")
            how_many = self._marker_pos
            self._marker_pos = -1

        if len(self._triggers) < how_many:
            raise RuntimeError("Not enough recorded triggers to update.")

        unregistered = set(info) - set(self.trigger_params)
        if unregistered:
            logging.warning(
                f"TriggerHandler: unregistered params {sorted(unregistered)} will not be saved."
            )

        for i in range(how_many):
            target = self._triggers[-1 - i]
            overwritten = {k: target[k] for k in info if k in target}
            if overwritten:
                logging.warning(
                    f"TriggerHandler: overwriting existing keys {list(overwritten.keys())} "
                    f"in trigger #{target.get('trigger_no')}."
                )
            target.update({k: v for k, v in info.items() if k in self.trigger_params})

        logging.info(f"TriggerHandler: info {info} added to last {how_many} trigger(s).")

    # ------------------------------------------------------------------
    # Persistence — trigger map
    # ------------------------------------------------------------------

    def register_save_trigger_map(self, part_id: str, timestamp: str) -> None:
        """
        Register an atexit hook that saves the trigger map to a CSV file on program exit.
        Follows the same convention as register_save_beh_results() in exit_handler.py.

        Args:
            part_id:   Participant identifier string.
            timestamp: Session timestamp string (format: YYYY_MM_DD_HH_MM).
        """
        filename = f"{part_id}_trigger_map_{timestamp}.csv"

        @atexit.register
        def _save_trigger_map():
            if not self._triggers:
                logging.warning("TriggerHandler: no triggers recorded — skipping trigger map CSV.")
                return

            filepath = join("results", filename)
            logging.info(f"TriggerHandler: saving trigger map to {filepath} ...")
            try:
                with open(filepath, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=self.trigger_params, extrasaction="ignore")
                    writer.writeheader()
                    writer.writerows(self._triggers)
                logging.info(
                    f"TriggerHandler: trigger map saved successfully. "
                    f"Total triggers: {len(self._triggers)}."
                )
            except Exception as e:
                logging.critical(f"TriggerHandler: failed to save trigger map: {e}")

        logging.info(
            f"TriggerHandler: trigger map will be saved to results/{filename} on exit."
        )

    # ------------------------------------------------------------------
    # Debug helpers
    # ------------------------------------------------------------------

    def print_trigger_list(self) -> None:
        """Print all recorded triggers to stdout (useful for debugging)."""
        header = ",".join(self.trigger_params)
        print(header)
        for trig in self._triggers:
            print(",".join(str(trig.get(k, "UNKNOWN")) for k in self.trigger_params))