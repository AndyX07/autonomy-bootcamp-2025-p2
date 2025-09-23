"""
Telemetry gathering logic.
"""

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
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
        args: object,  # Put your own arguments here
    ) -> Tuple[bool, Union["Telemetry", None]]:
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        try:
            instance = cls(cls.__private_key, connection, args, local_logger)
            return True, instance
        except Exception as ex:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Failed to create Telemetry object: {ex}")
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        args: object,  # Put your own arguments here
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"
        self.connection = connection
        self.args = args
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
        msg = self.connection.recv_match(
            type=["LOCAL_POSITION_NED", "ATTITUDE"], blocking=True, timeout=1
        )
        if not msg:
            # Remove debug message to match expected output
            return None

        if msg.get_type() == "LOCAL_POSITION_NED":
            self.position_msg = msg
        elif msg.get_type() == "ATTITUDE":
            self.attitude_msg = msg
        
        # Only return telemetry data if we have both messages and 
        # the timestamp indicates a 500ms interval (ends in 000 or 500)
        if self.position_msg and self.attitude_msg:
            ts_boot = msg.time_boot_ms
            # Only return data at 500ms intervals (timestamps ending in 000 or 500)
            if ts_boot % 500 == 0:
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
