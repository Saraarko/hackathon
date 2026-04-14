import pyrender
import imageio
import numpy as np
import os

class IndustrialRenderer:
    """Handles offscreen 3D rendering and high-quality MP4 encoding."""
    
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        # Initialize offscreen renderer
        # Note: On some systems, this requires a running X server or OSMesa
        self.renderer = pyrender.OffscreenRenderer(width, height)

    def render_animation(self, scene, camera_node, poses, output_path, fps=30):
        """Renders a sequence of poses directly to a high-quality video stream."""
        print(f"Starting Industrial Rendering ({len(poses)} frames)...")
        
        if camera_node is None:
            raise ValueError("Invalid camera node provided.")

        print(f"Streaming video encoding to: {output_path}")
        # imageio.get_writer allows direct streaming to disk, bypassing RAM bloat
        with imageio.get_writer(output_path, fps=fps, codec='libx264', format='FFMPEG', macro_block_size=None) as writer:
            for i, pose in enumerate(poses):
                # Update camera pose
                scene.set_pose(camera_node, pose=pose)
                
                # Render frame
                color, _ = self.renderer.render(scene)
                writer.append_data(color)
                
                if (i + 1) % 25 == 0:
                    print(f"Rendered {i + 1}/{len(poses)} frames...")
        
        return output_path

    def __del__(self):
        """Cleanup GL context resources safely."""
        try:
            if hasattr(self, 'renderer') and self.renderer is not None:
                self.renderer.delete()
        except Exception:
            pass
