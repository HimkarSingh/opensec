import os
import logging
from dotenv import load_dotenv

try:
    from e2b import Sandbox
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False
    logging.warning("E2B SDK is not installed. Code execution will be mocked.")

load_dotenv()
logger = logging.getLogger(__name__)

E2B_API_KEY = os.getenv("E2B_API_KEY")

class ExecutionEnvironment:
    def __init__(self):
        self.api_key = E2B_API_KEY
        if E2B_AVAILABLE and not self.api_key:
            logger.warning("E2B_API_KEY not found in environment. Sandboxes will not work.")

    def execute_command(self, command: str) -> str:
        """
        Executes a shell command inside an E2B Sandbox.
        """
        if not E2B_AVAILABLE or not self.api_key:
            # Fallback mock for testing if no API key is provided
            logger.info(f"Mocking execution for command: {command}")
            return f"[Mock E2B Sandbox] Executed: {command}\nOutput: Success"
            
        try:
            logger.info("Initializing E2B Sandbox...")
            # We use the standard e2b Sandbox for general execution
            with Sandbox.create(api_key=self.api_key) as sandbox:
                logger.info(f"Running command: {command}")
                result = sandbox.commands.run(command)
                
                output = result.stdout
                if result.stderr:
                    output += "\n[STDERR]:\n" + result.stderr
                    
                return output
        except Exception as e:
            logger.error(f"E2B Sandbox error: {e}")
            return f"Error executing in sandbox: {str(e)}"

# Global instance
execution_env = ExecutionEnvironment()
