import subprocess
import time

def run_and_monitor():
    try:
        # Start the child process
        print("Starting catflipper-linux...")
        process = subprocess.Popen(["./catflipper-linux"])
        process.wait()

        print("catflipper-linux crashed. Restarting...")
        time.sleep(2)
        run_and_monitor()

    except KeyboardInterrupt:
        print("Process monitor interrupted by user.")
        process.terminate()  # ensure process cleanup on exit
    except Exception as e:
        print(f"Error occurred: {e}")
        time.sleep(2)
        run_and_monitor()

if __name__ == "__main__":
    run_and_monitor()
