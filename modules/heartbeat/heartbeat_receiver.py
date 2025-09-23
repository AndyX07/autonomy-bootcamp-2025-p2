"""
Heartbeat receiving logic.
"""

from typing import Tuple, Union
from pymavlink import mavutil

from utilities.workers.queue_proxy_wrapper import QueueProxyWrapper
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatReceiver:
    """
    HeartbeatReceiver class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        output_queue: QueueProxyWrapper,
        local_logger: logger.Logger,
    ) -> Tuple[bool, Union["HeartbeatReceiver", None]]:
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        try:
            instance = cls(cls.__private_key, connection, output_queue, local_logger)
            return True, instance
        except Exception as e:  # pylint: disable=broad-exception-caught
            local_logger.error(f"HeartbeatReceiver create failed: {e}", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        output_queue: QueueProxyWrapper,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"
        self._connection = connection
        self._output_queue = output_queue
        self._logger = local_logger
        self.missed_count = 0
        self.state = "Disconnected"

    def run(self) -> None:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        try:
            msg = self._connection.recv_match(type="HEARTBEAT", blocking=False)
            if msg is not None:
                self.missed_count = 0
                if self.state != "Connected":
                    self.state = "Connected"
                    self._logger.info("Heartbeat connected", True)
                self._logger.debug("Heartbeat received", True)
            else:
                self.missed_count += 1
                if self.missed_count >= 5 and self.state != "Disconnected":
                    self.state = "Disconnected"
                    self._logger.warning("Heartbeat disconnected", True)
            self._output_queue.queue.put(self.state)
            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logger.error(f"HeartbeatReceiver run failed: {e}", True)
            return False


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
