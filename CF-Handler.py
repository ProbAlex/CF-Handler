import subprocess
import time
import threading
import sys

def autostats(process):
    while process.poll() is None:
        try:
            process.stdin.write(b"/stats\n")
            process.stdin.flush()
        except:
            break
        time.sleep(3600)

def user_input(process):
    """Handles user input and sends it to the process"""
    while process.poll() is None:
        try:
            user_input = input("> ")
            if user_input:
                process.stdin.write(f"{user_input}\n".encode())
                process.stdin.flush()
        except EOFError:
            break
        except Exception as e:
            print(f"Input error: {e}")

def run_and_monitor():
    try:
        print("Starting catflipper-linux...")
        process = subprocess.Popen(
            ["./catflipper-linux"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=False
        )
        stats_thread = threading.Thread(
            target=autostats,
            args=(process,),
            daemon=True
        )
        stats_thread.start()
        input_thread = threading.Thread(
            target=user_input,
            args=(process,),
            daemon=True
        )
        input_thread.start()
        def output():
            while process.poll() is None:
                line = process.stdout.readline()
                if line:
                    sys.stdout.buffer.write(line)
                    sys.stdout.buffer.flush()

        output_thread = threading.Thread(
            target=output,
            daemon=True
        )
        output_thread.start()
        process.wait()
        print("\ncatflipper-linux crashed. Restarting...")
        time.sleep(2)
        run_and_monitor()

    except KeyboardInterrupt:
        print("\nProcess monitor interrupted by user.")
        if process:
            process.terminate()

    except Exception as e:
        print(f"Error occurred: {e}")
        time.sleep(2)
        run_and_monitor()

if __name__ == "__main__":
    run_and_monitor()
