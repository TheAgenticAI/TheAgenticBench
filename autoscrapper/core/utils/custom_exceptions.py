
class CustomException(Exception):
    """Base exception class for orchestrator-specific errors"""
    def __init__(self, message, original_error=None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

class PlannerError(CustomException):
    """Raised when planner execution fails"""
    pass

class BrowserNavigationError(CustomException):
    """Raised when browser navigation fails"""
    pass

class SSAnalysisError(CustomException):
    """Raised when SS analysis fails"""
    pass

class CritiqueError(CustomException):
    """Raised when critique agent fails"""
    pass