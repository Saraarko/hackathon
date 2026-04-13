import os
from blender_runner import render_video

if __name__ == "__main__":
    os.makedirs("outputs", exist_ok=True)

    render_video()