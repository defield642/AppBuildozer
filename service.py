from jnius import autoclass
from time import sleep

# Import Android service helpers
PythonService = autoclass('org.kivy.android.PythonService')
service = PythonService.mService

def main():
    """
    Minimal background service for TimmyAlarmPro.
    This will keep the app alive in background and can be expanded later.
    """
    while True:
        # Just keep running – extend with alarm/notification logic if needed
        sleep(30)

if __name__ == "__main__":
    main()
