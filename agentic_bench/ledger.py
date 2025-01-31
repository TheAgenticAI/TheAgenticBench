from pydantic import BaseModel
from typing import Optional, Dict, Any, Union
import logfire
from utils.models import LedgerAnswer, LedgerModel

# Custom exceptions for ledger management
class LedgerError(Exception):
    """Base exception for ledger-related errors"""

    pass

class LedgerUpdateError(LedgerError):
    """Raised when ledger update fails"""

    pass

class LedgerNotInitializedError(LedgerError):
    """Raised when trying to access uninitialized ledger"""

    pass

class LedgerManager:
    """Manages the ledger state and operations"""

    def __init__(self, max_stalls: int = 3):
        self.ledger: Optional[LedgerModel] = None
        self.stall_counter: int = 0
        self.max_stalls: int = max_stalls
        logfire.info("LedgerManager initialized")

    def initialize_ledger(self) -> None:
        """Initialize ledger with default values"""
        try:
            self.ledger = LedgerModel(
                is_request_satisfied=LedgerAnswer(
                    answer=False, explanation="Task not completed"
                ),
                is_in_loop=LedgerAnswer(
                    answer=False, explanation="Conversation started"
                ),
                is_progress_being_made=LedgerAnswer(
                    answer=True, explanation="Initial state"
                ),
                next_speaker=LedgerAnswer(
                    answer="", explanation="No speaker selected yet"
                ),
                instruction_or_question=LedgerAnswer(
                    answer="", explanation="No instruction set"
                ),
            )
            logfire.info("Ledger initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize ledger: {str(e)}"
            logfire.error(error_msg, exc_info=True)
            raise LedgerError(error_msg)

    def update_ledger(self, new_state: Dict[str, Any]) -> None:
        """Update ledger with new state information"""
        try:
            if not isinstance(new_state, dict):
                raise ValueError("New state must be a dictionary")

            self.ledger = LedgerModel(**new_state)
            logfire.debug("Ledger updated successfully", extra={"new_state": new_state})

        except Exception as e:
            error_msg = f"Failed to update ledger: {str(e)}"
            logfire.error(error_msg, exc_info=True)
            raise LedgerUpdateError(error_msg)

    def _check_initialized(self) -> None:
        """Check if ledger is initialized"""
        if self.ledger is None:
            raise LedgerNotInitializedError("Ledger not initialized")

    def is_task_complete(self) -> bool:
        """Check if the task is complete"""
        try:
            self._check_initialized()
            if self.ledger is None:
                return False
            return bool(self.ledger.is_request_satisfied.answer)
        except LedgerNotInitializedError:
            return False

    def is_conversation_stalled(self) -> bool:
        """Check if conversation is stalled"""
        try:
            self._check_initialized()
            if self.ledger is None:
                return False
            return bool(
                self.ledger.is_in_loop.answer
                or not self.ledger.is_progress_being_made.answer
            )
        except LedgerNotInitializedError:
            return False

    def get_next_speaker(self) -> Optional[str]:
        """Get the next speaker from ledger"""
        try:
            self._check_initialized()
            if self.ledger is None:
                return None
            return str(self.ledger.next_speaker.answer)
        except LedgerNotInitializedError:
            logfire.warn("Attempted to get next speaker from uninitialized ledger")
            return None

    def get_instruction(self) -> Optional[str]:
        """Get the instruction for next speaker"""
        try:
            self._check_initialized()
            if self.ledger is None:
                return None
            return str(self.ledger.instruction_or_question.answer)
        except LedgerNotInitializedError:
            logfire.warn("Attempted to get instruction from uninitialized ledger")
            return None

    def handle_stall(self) -> bool:
        """
        Handle stalled conversation
        Returns: True if should replan, False otherwise
        """
        try:
            if self.is_conversation_stalled():
                self.stall_counter += 1
                logfire.warn(f"Conversation stalled. Stall count: {self.stall_counter}")

                if self.stall_counter >= self.max_stalls:
                    logfire.warn("Max stalls reached, replanning needed")
                    self.stall_counter = 0
                    return True
            else:
                if self.stall_counter > 0:
                    logfire.info("Conversation resumed, resetting stall counter")
                self.stall_counter = 0

            return False

        except Exception as e:
            logfire.error(f"Error handling stall: {str(e)}", exc_info=True)
            return False

    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of current ledger state"""
        try:
            self._check_initialized()
            if self.ledger is None:
                return {
                    "error": "Ledger not initialized",
                    "stall_count": self.stall_counter,
                }
            return {
                "task_complete": self.is_task_complete(),
                "is_stalled": self.is_conversation_stalled(),
                "stall_count": self.stall_counter,
                "next_speaker": self.get_next_speaker(),
                "has_instruction": bool(self.get_instruction()),
            }
        except LedgerNotInitializedError:
            return {
                "error": "Ledger not initialized",
                "stall_count": self.stall_counter,
            }

# Example usage:
if __name__ == "__main__":
    # Initialize manager
    manager = LedgerManager(max_stalls=3)

    # Initialize ledger
    manager.initialize_ledger()

    # Example update
    new_state = {
        "is_request_satisfied": {"answer": False, "explanation": "Work in progress"},
        "is_in_loop": {"answer": False},
        "is_progress_being_made": {"answer": True},
        "next_speaker": {"answer": "file_surfer"},
        "instruction_or_question": {"answer": "Please analyze example.py"},
    }

    manager.update_ledger(new_state)

    # Get state summary
    print(manager.get_state_summary())
