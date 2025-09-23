"""
Command worker to make decisions based on Telemetry Data.
"""

import os
import pathlib

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import command
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def command_worker(
    connection: mavutil.mavfile,
    target: command.Position,
    args: object,  # Place your own arguments here
    input_queue: queue_proxy_wrapper.QueueProxyWrapper,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    args... describe what the arguments are
    - input_queue: QueueProxyWrapper
         - Queue to receive telemetry data.
    - output_queue: QueueProxyWrapper
         - Queue to send command results.
    - controller: WorkerController
         - Controller to manage worker lifecycle.
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
    # Instantiate class object (command.Command)
    cmd = command.Command.create(
        connection=connection,
        target=target,
        args=args,
        local_logger=local_logger,
        output_queue=output_queue,
    )

    # Main loop: do work.
    while not controller.is_exit_requested():
        try:
            if input_queue is None or input_queue.queue.empty():
                continue
            # Wait for telemetry data from input queue
            message = input_queue.queue.get(timeout=1.0)
            if message is None:
                continue
            # Process the telemetry data and make decisions
            cmd.run(message)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Exception in main loop: {ex}", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
