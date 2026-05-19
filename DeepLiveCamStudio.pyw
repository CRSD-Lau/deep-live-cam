import sys

from modules.desktop_launcher import prepare_desktop_environment, launch


if __name__ == "__main__":
    if len(sys.argv) > 1:
        prepare_desktop_environment()
        import run
        run.core.run()
    else:
        launch()
