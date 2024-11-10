import subprocess, time, threading, sys, re, os
if os.name == 'nt': 
    import msvcrt
    cf_path = "./catflipper-windows.exe"
else: 
    import tty, termios
    cf_path = "./catflipper-linux"

is_running = True
cmd_history = []
hist_idx = 0

def strip_ansi(text):
    return re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', text)

class KeyReader:
    def __init__(self):
        if os.name != 'nt':
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
    
    def getch(self):
        if os.name == 'nt': 
            return msvcrt.getch().decode('utf-8', errors='ignore')
        try:
            tty.setraw(sys.stdin.fileno())
            return sys.stdin.read(1)
        finally: termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

def auto_stats(proc):
    global is_running
    while proc.poll() is None and is_running:
        try: proc.stdin.write(b"/stats\n"); proc.stdin.flush()
        except: break
        time.sleep(1200)

def get_prev_cmd():
    global hist_idx
    if cmd_history and hist_idx < len(cmd_history):
        hist_idx += 1
        return cmd_history[-hist_idx]
    return ""

def get_next_cmd():
    global hist_idx
    if hist_idx > 0:
        hist_idx -= 1
        return "" if hist_idx == 0 else cmd_history[-hist_idx]
    return ""

def handle_input(proc, keys):
    global is_running, cmd_history, hist_idx
    curr_input = ""
    write = sys.stdout.write
    flush = sys.stdout.flush
    
    while proc.poll() is None and is_running:
        try:
            rows = os.get_terminal_size()[0]
            write(f"\033[{rows};0H\033[K> {curr_input}")
            flush()

            char = keys.getch()
            
            if char == '\x03': is_running = False; break
            elif char in ('\r', '\n'):
                if curr_input.strip():
                    proc.stdin.write(f"{curr_input}\n".encode())
                    proc.stdin.flush()
                    cmd_history.append(curr_input)
                    hist_idx = 0
                curr_input = ""
            elif char in ('\x7f', '\b'): curr_input = curr_input[:-1]
            elif char == '\x1b':
                n1 = keys.getch()
                if n1 == '[':
                    n2 = keys.getch()
                    if n2 == 'A': curr_input = get_prev_cmd()
                    elif n2 == 'B': curr_input = get_next_cmd()
            elif ord(char) >= 32: curr_input += char
        except: time.sleep(0.1)

def filter(line):
    decoded = line.decode('utf-8', errors='ignore')
    clean = strip_ansi(decoded)
    return "[Coflnet]: Flips in" in clean or ("[Coflnet]: Your filter blocked" in clean and "in the last minute" in clean)

def auth_error(line):
    return "at Object.authenticate (/snapshot/the thing/Catflipper/Loader/node_modules/minecraft-protocol/src/client/microsoftAuth.js:31:40)" in line.decode('utf-8', errors='ignore')

def print_line(text, row, rows):
    row = min(row, rows - 2)
    sys.stdout.write(f"\033[{row};0H\033[K{text}\n")
    sys.stdout.flush()

def monitor():
    global is_running
    is_running = True
    proc = None
    write = sys.stdout.write
    flush = sys.stdout.flush
    
    try:
        print("Starting catflipper...")
        proc = subprocess.Popen([cf_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=False)
        write("\033[2J\033[H\033[?25l")
        flush()

        stats_thread = threading.Thread(target=auto_stats, args=(proc,), daemon=True)
        stats_thread.start()
        keys = KeyReader()
        input_thread = threading.Thread(target=handle_input, args=(proc, keys), daemon=True)
        input_thread.start()

        row = 0
        while proc.poll() is None and is_running:
            line = proc.stdout.readline()
            if line:
                if auth_error(line):
                    print("\nDetected authentication error. Restarting catflipper...")
                    proc.terminate()
                    time.sleep(2)
                    return monitor()
                
                if not filter(line):
                    rows = os.get_terminal_size()[0]
                    print_line(line.decode('utf-8', errors='ignore').rstrip(), row, rows)
                    row = (row + 1) % (rows - 1)

        if not is_running: raise KeyboardInterrupt
        print("\ncatflipper-linux crashed. Restarting...")
        time.sleep(2)
        return monitor()

    except KeyboardInterrupt:
        is_running = False
        write("\033[?25h")
        print("\nProcess monitor interrupted by user.")
        if proc: proc.terminate()
    except Exception as e:
        is_running = False
        write("\033[?25h")
        print(f"Error occurred: {e}")
        time.sleep(2)
        return monitor()

if __name__ == "__main__":
    try: monitor()
    finally:
        sys.stdout.write("\033[?25h\033[2J\033[H")
        sys.stdout.flush()
