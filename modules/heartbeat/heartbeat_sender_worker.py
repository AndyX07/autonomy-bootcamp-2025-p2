"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib
import time

from pymavlink import mavutil

from utilities.workers import worker_controller
from . import heartbeat_sender
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def heartbeat_sender_worker(
    connection: mavutil.mavfile,
    controller: worker_controller.WorkerController,
    heartbeat_period: float = 1.0,
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    - connection: pymavlink connection object (mavutil.mavlink_connection(...))
    - controller: worker_controller.Controller used to manage worker lifecycle
    - heartbeat_period: seconds between heartbeats
    """
    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    # Instantiate logger
    worker_name = pathlib.Path(__file__).stem
    process_id = os.getpid()
    result, local_logger = logger.Logger.create(f"{worker_name}_{process_id}", True)
    if not result:
        print("ERROR: Worker failed to create logger")
        return

    # Get Pylance to stop complaining
    assert local_logger is not None

    local_logger.info("Logger initialized", True)

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Instantiate HeartbeatSender
    result, sender = heartbeat_sender.HeartbeatSender.create(connection, local_logger)
    if not result or sender is None:
        local_logger.error("Failed to create HeartbeatSender", True)
        return

    local_logger.info("HeartbeatSender created, entering main loop", True)

    try:
        while not controller.is_exit_requested():
            time.sleep(heartbeat_period)
            controller.check_pause()
            sender.run()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        local_logger.error(f"Unhandled exception in heartbeat worker: {exc}", True)
    finally:
        local_logger.info("Heartbeat worker shutting down", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
