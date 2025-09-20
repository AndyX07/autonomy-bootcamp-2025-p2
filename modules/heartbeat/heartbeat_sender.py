"""
Heartbeat sending logic.
"""

from pymavlink import mavutil


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatSender:
    """
    HeartbeatSender class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        logger
    ) -> "tuple[True, HeartbeatSender] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        try:
            instance = cls(cls.__private_key, connection, logger)
            return True, instance
        except Exception as e:
            logger.error(f"HeartbeatSender create failed: {e}", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        logger
    ):
        assert key is HeartbeatSender.__private_key, "Use create() method"
        self._connection = connection
        self._logger = logger

    def run(
        self
    ):
        """
        Attempt to send a heartbeat message.
        """
        try:
            self._connection.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GCS,
                mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                0,
                0,
                0,
            )
            self._logger.debug("Heartbeat sent", True)
            return True
        except Exception as e:
            self._logger.error(f"Failed to send heartbeat: {e}", True)
            return False


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================