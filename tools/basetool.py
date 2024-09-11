import os
import logging
from typing import Annotated
import subprocess
from langchain_core.tools import tool
from logger import setup_logger
from load_cfg import WORKING_DIRECTORY,CONDA_PATH,CONDA_ENV
# Initialize logger
logger = setup_logger()
# Ensure the storage directory exists
if not os.path.exists(WORKING_DIRECTORY):
    os.makedirs(WORKING_DIRECTORY)
    logger.info(f"Created storage directory: {WORKING_DIRECTORY}")
@tool
def execute_code(
    input_code: Annotated[str, "The Python code to execute."],
    codefile_name: Annotated[str, "The Python code file name or full path."]
):
    """
    Execute Python code and return the result.

    This function takes Python code as input, writes it to a file, executes it,
    and returns the output or any errors encountered during execution.

    Args:
    input_code (str): The Python code to be executed.
    codefile_name (str): The name of the file to save the code in, or the full path.

    Returns:
    dict: A dictionary containing the execution result, output, and file path.
    """
    try:
        # Check if codefile_name is already an absolute path
        if os.path.isabs(codefile_name):
            code_file_path = codefile_name
        else:
            # Ensure we're not adding WORKING_DIRECTORY multiple times
            if codefile_name.startswith(WORKING_DIRECTORY):
                code_file_path = os.path.join(WORKING_DIRECTORY, codefile_name)
            else:
                code_file_path = codefile_name

        # Normalize the path
        code_file_path = os.path.normpath(code_file_path)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(code_file_path), exist_ok=True)
        
        # Write the input code to the file
        with open(code_file_path, 'w') as code_file:
            code_file.write(input_code)
        
        logger.info(f"Code written to file: {code_file_path}")
        
        # Construct the command to activate the virtual environment and run the script
        conda_path = os.getenv('CONDA_PATH', '/home/user/anaconda3')
        conda_env = os.getenv('CONDA_ENV', 'base')

        # Construct the command to activate the Conda environment and execute the given command
        source = f"source {conda_path}/etc/profile.d/conda.sh"
        conda_activate = f"conda activate {conda_env}"
        python_cmd = f"python {code_file_path}"
        full_command = f"{source} && {conda_activate} && {python_cmd}"
        
        # Execute the code using subprocess for security
        result = subprocess.run(
            ['/bin/bash', '-c', full_command],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(code_file_path),  # Set the working directory to the file's directory
        )
        
        # Capture standard output and error output
        output = result.stdout
        error_output = result.stderr
        
        if result.returncode == 0:
            logger.info("Code executed successfully")
            print(output)
            return {
                "result": "Code executed successfully",
                "output": output + "\n\nIf you have completed all tasks, respond with FINAL ANSWER.",
                "file_path": code_file_path
            }
        else:
            logger.error(f"Code execution failed: {error_output}")
            print(error_output)
            return {
                "result": "Failed to execute",
                "error": error_output,
                "file_path": code_file_path
            }
    except Exception as e:
        logger.exception("An error occurred while executing code")
        return {
            "result": "Error occurred",
            "error": str(e),
            "file_path": code_file_path if 'code_file_path' in locals() else "Unknown"
        }

@tool
def execute_command(
    command: Annotated[str, "Command to be executed."]
) -> Annotated[str, "Output of the command."]:
    """
    Execute a command in a specified Conda environment and return its output.

    This function activates a Conda environment , executes the given command,
    and returns the output or any errors encountered during execution.
    Please use pip to install the package.
    Args:
    command (str): The command to be executed in the Conda environment.

    Returns:
    str: The output of the command or an error message.
    """
    try:
        # Construct the command to activate the Conda environment and execute the given command
        source = f"source {CONDA_PATH}/etc/profile.d/conda.sh"
        conda_activate = f"conda activate {CONDA_ENV}"
        cd_command = f"cd WORKING_DIRECTORY"
        full_command = f"{source} && {conda_activate} && {cd_command} && {command}"
        
        logger.info(f"Executing command: {command}")
        
        # Execute the command and capture the output
        result = subprocess.run(
            full_command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            executable="/bin/bash"
        )
        logger.info("Command executed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command: {e.stderr}")
        return f"Error: {e.stderr}"

logger.info("Module initialized successfully")