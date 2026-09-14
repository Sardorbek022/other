import subprocess
import sys

def run_services():

    web_server = subprocess.Popen([sys.executable, "manage.py", "runserver"])
    
    bot_process = subprocess.Popen([sys.executable, "bot/main.py"])

    try:
        web_server.wait()
        bot_process.wait()
    except KeyboardInterrupt:
        web_server.terminate()
        bot_process.terminate()

if __name__ == "__main__":
    run_services()
