"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib
import time

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import heartbeat_receiver
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================


def heartbeat_receiver_worker(
    connection: mavutil.mavfile,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
    heartbeat_period: float = 1.0,
) -> None:
    """
    Worker process.

    - connection: pymavlink connection object (mavutil.mavlink_connection(...))
    - output_queue: multiprocessing.Queue to send data to other processes
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
    # Instantiate class object (heartbeat_receiver.HeartbeatReceiver)

    # Main loop: do work.
    result, receiver = heartbeat_receiver.HeartbeatReceiver.create(
        connection, output_queue, local_logger
    )
    if not result:
        local_logger.error("Failed to create HeartbeatReceiver", True)
        return

    local_logger.info("HeartbeatReceiver created, entering main loop", True)

    try:
        while not controller.is_exit_requested():
            controller.check_pause()
            receiver.run()
            time.sleep(heartbeat_period)

    except Exception as exc:  # pylint: disable=broad-exception-caught
        local_logger.error(f"Unhandled exception in heartbeat receiver worker: {exc}", True)
    finally:
        local_logger.info("Heartbeat receiver worker shutting down", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
