import subprocess
import time

def run_and_monitor():
    while True:
        try:
            # Start the child process
            print("Starting catflipper-linux...")
            process = subprocess.Popen(["./catflipper-linux"])

            # Wait for the process to finish
            process.wait()

            # If the process exits, log the exit code
            print(f"catflipper-linux exited with code {process.returncode}")
            
            # Restart if the process was terminated or crashed
            if process.returncode != 0:
                print("catflipper-linux crashed. Restarting...")
                time.sleep(2)  # optional: add delay before restart

        except KeyboardInterrupt:
            print("Process monitor interrupted by user.")
            process.terminate()  # ensure process cleanup on exit
            break
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(2)  # optional: delay before attempting restart

if __name__ == "__main__":
    run_and_monitor()
