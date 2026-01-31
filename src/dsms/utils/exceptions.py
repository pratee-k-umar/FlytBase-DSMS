"""
Custom Exceptions for DSMS
Sentry pattern: Well-defined exception hierarchy.
"""


class DSMSError(Exception):
    """Base exception for all DSMS errors"""
    code = 'dsms_error'
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        if code:
            self.code = code
        super().__init__(message)


class NotFoundError(DSMSError):
    """Resource not found"""
    code = 'not_found'


class ValidationError(DSMSError):
    """Validation failed"""
    code = 'validation_error'


class MissionError(DSMSError):
    """Mission operation error"""
    code = 'mission_error'


class FleetError(DSMSError):
    """Fleet/Drone operation error"""
    code = 'fleet_error'


class SimulationError(DSMSError):
    """Simulation error"""
    code = 'simulation_error'
