import numpy as np

class AnimationEngine:
    """Generates precise camera paths for industrial CAD presentations."""
    
    def __init__(self, num_frames=150, fps=30):
        self.num_frames = num_frames
        self.fps = fps

    def get_rotation_poses(self, initial_distance, elevation_deg=25):
        """Generates a 360-degree orbital camera path around the origin."""
        poses = []
        elevation = np.radians(elevation_deg)
        
        for i in range(self.num_frames):
            # Slow cinematic rotation (360 degrees over 150 frames)
            angle = (2 * np.pi * i) / self.num_frames
            
            # Spherical to Cartesian
            # Z is UP axis
            x = initial_distance * np.cos(elevation) * np.sin(angle)
            y = initial_distance * np.cos(elevation) * np.cos(angle)
            z = initial_distance * np.sin(elevation)
            
            # Compute Look-At matrix (Source: target=origin, eye=[x,y,z])
            target = np.zeros(3)
            eye = np.array([x, y, z])
            up = np.array([0, 0, 1])
            
            # Look-at calculation
            z_axis = (eye - target)
            z_axis /= np.linalg.norm(z_axis)
            x_axis = np.cross(up, z_axis)
            x_axis /= np.linalg.norm(x_axis)
            y_axis = np.cross(z_axis, x_axis)
            
            pose = np.eye(4)
            pose[:3, 0] = x_axis
            pose[:3, 1] = y_axis
            pose[:3, 2] = z_axis
            pose[:3, 3] = eye
            
            poses.append(pose)
            
        return poses