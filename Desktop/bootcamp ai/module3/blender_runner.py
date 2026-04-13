import os
import numpy as np
import matplotlib
matplotlib.use('Agg') # Pour tourner sans interface graphique
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scene_builder import create_scene
from animation import setup_animation

def render_video(diameter_mm: float = 100.0, material: str = "316L", equipment_type: str = "valve"):
    scene = create_scene(material=material)
    anim_conf = setup_animation()

    print("Configuration lue:", scene)
    print("Démarrage du rendu 3D de la vanne (Patientez quelques secondes)...")

    os.makedirs("outputs", exist_ok=True)

    # Use ffmpeg if available, otherwise fall back to GIF via Pillow
    import shutil
    if shutil.which("ffmpeg"):
        output_file = "outputs/valve.mp4"
        writer = animation.FFMpegWriter(fps=15)
    else:
        output_file = "outputs/valve.gif"
        writer = animation.PillowWriter(fps=15)

    # Rayon proportionnel au DN extrait du PDF (DN100 → rayon 2, DN65 → ~1.3, etc.)
    radius = max(0.5, (diameter_mm / 100.0) * 2.0)
    height = radius * 2.5

    # Couleur selon matériau
    _color_map = {
        "316L": "cyan", "316": "cyan", "1.4408": "#4fc3f7", "1.4462": "#81d4fa",
        "304": "#b2ebf2", "carbon_steel": "#90a4ae", "cast_iron": "#78909c",
    }
    color = _color_map.get(material, "cyan")

    fig = plt.figure(figsize=(6, 6))
    fig.patch.set_facecolor('#202020')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#202020')
    ax.set_axis_off()

    # Corps principal — cylindre aux dimensions réelles du PDF
    z      = np.linspace(0, height, 40)
    theta  = np.linspace(0, 2 * np.pi, 40)
    tg, zg = np.meshgrid(theta, z)
    ax.plot_surface(radius * np.cos(tg), radius * np.sin(tg), zg,
                    color=color, alpha=0.9, edgecolor='#00CED1', lw=0.3)

    # Brides (flanges) en haut et en bas
    for z_pos in [0, height]:
        flange_r = radius * 1.35
        zf = np.full_like(tg, z_pos)
        rf = np.linspace(radius, flange_r, 10)
        tf = np.linspace(0, 2 * np.pi, 40)
        rf_g, tf_g = np.meshgrid(rf, tf)
        ax.plot_surface(rf_g * np.cos(tf_g), rf_g * np.sin(tf_g),
                        np.full_like(rf_g, z_pos),
                        color='#37474f', alpha=0.95, edgecolor='none')

    # Label DN
    ax.text(0, 0, height + 0.3,
            f"DN{int(diameter_mm)} · {material}",
            color='white', fontsize=8, ha='center')

    ax.set_xlim(-flange_r - 0.5, flange_r + 0.5)
    ax.set_ylim(-flange_r - 0.5, flange_r + 0.5)
    ax.set_zlim(-0.5, height + 0.8)

    def update(frame):
        ax.view_init(elev=30., azim=frame * 10)
        return fig,

    anim = animation.FuncAnimation(fig, update, frames=36, blit=False)
    anim.save(output_file, writer=writer)

    print("VIDEO GENERATED:", output_file)