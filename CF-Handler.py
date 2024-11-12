import os
import re
import sys
import time
import threading
import subprocess
from dataclasses import dataclass
from typing import List, Optional

# Platform-specific imports and settings
if os.name == 'nt':
    import msvcrt
    EXECUTABLE = "./catflipper-windows.exe"
else:
    import tty
    import termios
    EXECUTABLE = "./catflipper-linux"

@dataclass
class Terminal:
    """Handles terminal-related operations"""
    running: bool = True
    command_history: List[str] = None
    history_index: int = 0
    
    def __post_init__(self):
        self.command_history = []
        if os.name != 'nt':
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
    
    def get_char(self) -> str:
        """Get a single character input based on platform"""
        if os.name == 'nt':
            return msvcrt.getch().decode('utf-8', errors='ignore')
        try:
            tty.setraw(self.fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)
    
    def get_command_from_history(self, direction: int) -> str:
        """Get previous/next command from history"""
        if not self.command_history:
            return ""
            
        if direction > 0:  # Up arrow
            self.history_index = min(self.history_index + 1, len(self.command_history))
            return self.command_history[-self.history_index] if self.history_index > 0 else ""
        else:  # Down arrow
            self.history_index = max(0, self.history_index - 1)
            return self.command_history[-self.history_index] if self.history_index > 0 else ""
    
    def cleanup(self):
        """Restore terminal state"""
        sys.stdout.write("\033[?25h\033[2J\033[H")
        sys.stdout.flush()
        if os.name != 'nt':
            try:
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)
            except:
                pass

class ProcessMonitor:
    def __init__(self):
        self.terminal = Terminal()
        self.ansi_cleaner = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    
    def should_filter_line(self, line: str) -> bool:
        """Determine if a line should be filtered out"""
        clean_line = self.ansi_cleaner.sub('', line)
        return ("[Coflnet]: Flips in" in clean_line or 
                ("[Coflinet]: Your filter blocked" in clean_line and "in the last minute" in clean_line))
    
    def is_auth_error(self, line: str) -> bool:
        """Check if line contains authentication error"""
        return "at Object.authenticate" in line and "microsoftAuth.js" in line
    
    def handle_input(self, proc: subprocess.Popen):
        """Handle user input in a separate thread"""
        current_input = ""
        
        while proc.poll() is None and self.terminal.running:
            try:
                rows = os.get_terminal_size()[0]
                sys.stdout.write(f"\033[{rows};0H\033[K> {current_input}")
                sys.stdout.flush()

                char = self.terminal.get_char()
                
                if char == '\x03':  # Ctrl+C
                    self.terminal.running = False
                    break
                elif char in ('\r', '\n'):
                    if current_input.strip():
                        proc.stdin.write(f"{current_input}\n".encode())
                        proc.stdin.flush()
                        self.terminal.command_history.append(current_input)
                        self.terminal.history_index = 0
                    current_input = ""
                elif char in ('\x7f', '\b'):  # Backspace
                    current_input = current_input[:-1]
                elif char == '\x1b':  # Arrow keys
                    next_char = self.terminal.get_char()
                    if next_char == '[':
                        direction = 1 if self.terminal.get_char() == 'A' else -1
                        current_input = self.terminal.get_command_from_history(direction)
                elif ord(char) >= 32:
                    current_input += char
            except:
                time.sleep(0.1)
    
    def run(self):
        """Main monitoring loop"""
        try:
            while self.terminal.running:
                print("Starting catflipper...")
                proc = subprocess.Popen(
                    [EXECUTABLE],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=False
                )
                
                sys.stdout.write("\033[2J\033[H\033[?25l")
                sys.stdout.flush()
                
                # Start auto-stats thread
                threading.Thread(
                    target=lambda: self.auto_stats(proc),
                    daemon=True
                ).start()
                
                # Start input handling thread
                threading.Thread(
                    target=lambda: self.handle_input(proc),
                    daemon=True
                ).start()
                
                row = 0
                while proc.poll() is None and self.terminal.running:
                    line = proc.stdout.readline().decode('utf-8', errors='ignore')
                    if not line:
                        continue
                        
                    if self.is_auth_error(line):
                        print("\nDetected authentication error. Restarting...")
                        proc.terminate()
                        time.sleep(2)
                        break
                    
                    if not self.should_filter_line(line):
                        rows = os.get_terminal_size()[0]
                        row = min(row, rows - 2)
                        sys.stdout.write(f"\033[{row};0H\033[K{line.rstrip()}\n")
                        sys.stdout.flush()
                        row = (row + 1) % (rows - 1)
                
                if not self.terminal.running:
                    break
                    
                print("\nProcess crashed. Restarting...")
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\nProcess monitor interrupted by user.")
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            if 'proc' in locals():
                proc.terminate()
            self.terminal.cleanup()

def main():
    monitor = ProcessMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
