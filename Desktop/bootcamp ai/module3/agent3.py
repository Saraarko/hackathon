import os
import io
import numpy as np
from scene_builder import SceneBuilder
from animation import AnimationEngine
from renderer import IndustrialRenderer

def run_agent3(state):
    """
    Industrial Video Generation Node.
    Transforms 3D CAD geometry (OBJ) into a cinematic product reveal (MP4).
    """
    obj_path = state.get("obj")
    if not obj_path:
        raise ValueError("Agent 3 cannot run without OBJ file")

    print(f"[Agent 3] Starting industrial video generation for: {obj_path}")
    
    # 1. Initialize Scene
    builder = SceneBuilder(obj_path)
    builder.load_model()
    distance = builder.setup_camera()
    builder.setup_lighting()
    
    # 2. Setup Animation
    animator = AnimationEngine(num_frames=150, fps=30)
    poses = animator.get_rotation_poses(initial_distance=distance)
    
    # 3. Render and Export
    run_id = state.get("run_id")
    if not run_id:
        raise ValueError("Agent 3 requires a valid run_id in state")
        
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs", run_id, "agent3"))
    os.makedirs(out_dir, exist_ok=True)
    
    # Dynamic filename based on OBJ name
    base_name = os.path.basename(obj_path).replace(".obj", "")
    video_path = os.path.join(out_dir, f"{base_name}_reveal.mp4")
    
    renderer = IndustrialRenderer(width=1280, height=720)
    try:
        final_video = renderer.render_animation(
            scene=builder.scene,
            camera_node=builder.camera_node,
            poses=poses,
            output_path=video_path,
            fps=30
        )
        state["video"] = final_video
        print(f"[Agent 3] Success: High-fidelity video generated at {final_video}")
    except Exception as e:
        print(f"[Agent 3] Pyrender rendering error: {str(e)}.")
        print(f"[Agent 3] Triggering Trimesh GL Fallback protocol...")
        try:
            import trimesh
            import imageio
            
            # Simple trimesh scene using our raw, normalized mesh
            fallback_scene = trimesh.Scene(builder.raw_mesh)
            
            # Generate frames using trimesh.scene.save_image
            print(f"Streaming fallback video encoding to: {video_path}")
            with imageio.get_writer(video_path, fps=30, codec='libx264', format='FFMPEG', macro_block_size=None) as writer:
                # Calculate rotation increments matching the pyrender poses
                # Simplest fallback is to rotate the scene geometry around Z axis
                rotation_matrix = trimesh.transformations.rotation_matrix(
                    angle=2 * np.pi / 150, 
                    direction=[0, 0, 1], 
                    point=builder.center
                )
                
                for i in range(150):
                    fallback_scene.apply_transform(rotation_matrix)
                    png_data = fallback_scene.save_image(resolution=(1280, 720))
                    # imageio can read PNG bytes into an array
                    img_array = imageio.v2.imread(io.BytesIO(png_data))
                    writer.append_data(img_array)
                    
                    if (i + 1) % 25 == 0:
                        print(f"Rendered fallback {i + 1}/150 frames...")
                        
            state["video"] = video_path
            print(f"[Agent 3] Success (Fallback): Video generated at {video_path}")
        except Exception as fallback_err:
            print(f"[Agent 3] Fallback Rendering Error: {str(fallback_err)}")
            state["video"] = None
    
    return state

if __name__ == "__main__":
    # Mock state for standalone testing
    test_state = {"obj": "../module2/outputs/pump.obj"}
    run_agent3(test_state)
