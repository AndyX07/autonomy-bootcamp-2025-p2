"""
Decision-making logic.
"""

import math
from typing import Tuple, Union

from pymavlink import mavutil

from ..common.modules.logger import logger
from ..telemetry import telemetry


class Position:
    """
    3D vector struct.
    """

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Command:  # pylint: disable=too-many-instance-attributes
    """
    Command class to make a decision based on recieved telemetry,
    and send out commands based upon the data.
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> Tuple[bool, Union["Command", None]]:
        """
        Falliable create (instantiation) method to create a Command object.

        Returns:
            tuple[bool, Command | None]: A tuple containing:
                - success: True if creation was successful, False otherwise
                - command: The Command object if successful, None if failed
        """
        try:
            # Validate required parameters
            if connection is None:
                local_logger.error("Failed to create Command: connection is None")
                return False, None

            if target is None:
                local_logger.error("Failed to create Command: target is None")
                return False, None

            if local_logger is None:
                # Can't log this error since logger is None
                return False, None

            # Create the Command object
            command = cls(cls.__private_key, connection, target, local_logger)
            local_logger.info("Command object created successfully")
            return True, command

        except (TypeError, ValueError, AttributeError) as e:
            if local_logger is not None:
                local_logger.error(f"Failed to create Command: {e}")
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"
        self.connection = connection
        self.target = target
        self.logger = local_logger
        self.velocity_history = []

    def run(self, telemetry_data: telemetry.TelemetryData) -> None:
        """
        Make a decision based on received telemetry data.
        """
        # ----------------- AVERAGE VELOCITY -----------------
        # Calculate average velocity first, before any command logic
        vx, vy, vz = telemetry_data.x_velocity, telemetry_data.y_velocity, telemetry_data.z_velocity
        self.velocity_history.append((vx, vy, vz))
        avg_vx = sum(v[0] for v in self.velocity_history) / len(self.velocity_history)
        avg_vy = sum(v[1] for v in self.velocity_history) / len(self.velocity_history)
        avg_vz = sum(v[2] for v in self.velocity_history) / len(self.velocity_history)
        self.logger.info(f"AVERAGE VELOCITY: ({avg_vx}, {avg_vy}, {avg_vz})")

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system

        delta_z = self.target.z - telemetry_data.z
        if abs(delta_z) > 0.5:
            # Send altitude command with required mock parameters
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                0,
                1,  # param1: ascent/descent speed (Z_SPEED = 1)
                0,
                0,
                0,
                0,
                0,  # params 2-6 unused
                self.target.z,  # param7: absolute target altitude
            )
            return f"CHANGE ALTITUDE: {delta_z}"

        dx = self.target.x - telemetry_data.x
        dy = self.target.y - telemetry_data.y
        target_yaw_rad = math.atan2(dy, dx)
        target_yaw_deg = math.degrees(target_yaw_rad)
        now_yaw_rad = telemetry_data.yaw
        now_yaw_deg = math.degrees(now_yaw_rad)
        yaw_diff_deg = target_yaw_deg - now_yaw_deg
        yaw_diff_deg = (yaw_diff_deg + 180) % 360 - 180
        if abs(yaw_diff_deg) > 5:
            direction = 1 if yaw_diff_deg > 0 else -1
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                yaw_diff_deg,
                5,
                direction,
                1,
                0,
                0,
                0,
            )
            return f"CHANGE YAW: {yaw_diff_deg}"

        # If no command was sent, return None explicitly
        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
