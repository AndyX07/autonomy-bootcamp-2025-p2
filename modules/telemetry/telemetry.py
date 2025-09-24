"""
Telemetry gathering logic.
"""

import time
from typing import Tuple, Union, Optional

from pymavlink import mavutil

from ..common.modules.logger import logger


class TelemetryData:  # pylint: disable=too-many-instance-attributes
    """
    Python struct to represent Telemtry Data. Contains the most recent attitude and position reading.
    """

    def __init__(
        self,
        time_since_boot: int | None = None,  # ms
        x: float | None = None,  # m
        y: float | None = None,  # m
        z: float | None = None,  # m
        x_velocity: float | None = None,  # m/s
        y_velocity: float | None = None,  # m/s
        z_velocity: float | None = None,  # m/s
        roll: float | None = None,  # rad
        pitch: float | None = None,  # rad
        yaw: float | None = None,  # rad
        roll_speed: float | None = None,  # rad/s
        pitch_speed: float | None = None,  # rad/s
        yaw_speed: float | None = None,  # rad/s
    ) -> None:
        self.time_since_boot = time_since_boot
        self.x = x
        self.y = y
        self.z = z
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.z_velocity = z_velocity
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.roll_speed = roll_speed
        self.pitch_speed = pitch_speed
        self.yaw_speed = yaw_speed

    def __str__(self) -> str:
        return f"""{{
            time_since_boot: {self.time_since_boot},
            x: {self.x},
            y: {self.y},
            z: {self.z},
            x_velocity: {self.x_velocity},
            y_velocity: {self.y_velocity},
            z_velocity: {self.z_velocity},
            roll: {self.roll},
            pitch: {self.pitch},
            yaw: {self.yaw},
            roll_speed: {self.roll_speed},
            pitch_speed: {self.pitch_speed},
            yaw_speed: {self.yaw_speed}
        }}"""


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Telemetry:
    """
    Telemetry class to read position and attitude (orientation).
    """

    __private_key = object()

    @classmethod
    def create(
        cls, connection: mavutil.mavfile, local_logger: logger.Logger
    ) -> Tuple[bool, Union["Telemetry", None]]:
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        try:
            instance = cls(cls.__private_key, connection, local_logger)
            return True, instance
        except Exception as ex:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Failed to create Telemetry object: {ex}")
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"
        self.connection = connection
        self.local_logger = local_logger
        self.position_msg = None
        self.attitude_msg = None

    def run(
        self,
    ) -> Optional[TelemetryData]:
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        # Read MAVLink message LOCAL_POSITION_NED (32)
        # Read MAVLink message ATTITUDE (30)
        # Return the most recent of both, and use the most recent message's timestamp

        start_time = time.time()
        timeout_duration = 1.0

        # Reset messages for fresh collection
        temp_position_msg = None
        temp_attitude_msg = None

        # Collect both message types within the timeout window
        while time.time() - start_time < timeout_duration:
            msg = self.connection.recv_match(
                type=["LOCAL_POSITION_NED", "ATTITUDE"], blocking=False, timeout=0.1
            )
            if not msg:
                continue

            if msg.get_type() == "LOCAL_POSITION_NED":
                temp_position_msg = msg
            elif msg.get_type() == "ATTITUDE":
                temp_attitude_msg = msg

            # If we have both messages, break early
            if temp_position_msg and temp_attitude_msg:
                break

        # Only update instance variables and return data if we got both messages
        if temp_position_msg and temp_attitude_msg:
            self.position_msg = temp_position_msg
            self.attitude_msg = temp_attitude_msg

            # Use the maximum timestamp to ensure we get the most recent time
            ts_boot = max(self.position_msg.time_boot_ms, self.attitude_msg.time_boot_ms)
            telemetry_data = TelemetryData(
                time_since_boot=ts_boot,
                x=self.position_msg.x,
                y=self.position_msg.y,
                z=self.position_msg.z,
                x_velocity=self.position_msg.vx,
                y_velocity=self.position_msg.vy,
                z_velocity=self.position_msg.vz,
                roll=self.attitude_msg.roll,
                pitch=self.attitude_msg.pitch,
                yaw=self.attitude_msg.yaw,
                roll_speed=self.attitude_msg.rollspeed,
                pitch_speed=self.attitude_msg.pitchspeed,
                yaw_speed=self.attitude_msg.yawspeed,
            )
            return telemetry_data

        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
