"""
Telemtry worker that gathers GPS data.
"""

import os
import pathlib

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import telemetry
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def telemetry_worker(
    connection: mavutil.mavfile,
    args: object,  # Place your own arguments here
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    - connection: pymavlink connection object (mavutil.mavlink_connection(...))
    - output_queue: multiprocessing.Queue to send data to other processes
    - controller: worker_controller.Controller used to manage worker lifecycle
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
    # Instantiate class object (telemetry.Telemetry)

    # Main loop: do work.
    result, telem = telemetry.Telemetry.create(connection, local_logger, args)
    if not result:
        local_logger.error("Failed to create Telemetry", True)
        return
    while not controller.is_exit_requested():
        controller.check_pause()
        data = telem.run()
        if not data:
            continue
        output_queue.queue.put(data)
        local_logger.debug(f"Telemetry data: {data}", True)
    local_logger.info("Worker stopping", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
