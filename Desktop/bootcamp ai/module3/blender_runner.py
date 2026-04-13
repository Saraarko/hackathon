import os
import numpy as np
import matplotlib
matplotlib.use('Agg') # Pour tourner sans interface graphique
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scene_builder import create_scene
from animation import setup_animation

def render_video():
    scene = create_scene()
    anim_conf = setup_animation()
    
    print("Configuration lue:", scene)
    print("Démarrage du rendu 3D de la vanne (Patientez quelques secondes)...")

    output_file = "outputs/valve.mp4"

    fig = plt.figure(figsize=(6, 6))
    fig.patch.set_facecolor('#202020') # Fond gris foncé
    
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('#202020')
    ax.set_axis_off() # Cacher les grilles

    # Tracé d'un cylindre simple (simulant le corps de la vanne)
    z = np.linspace(0, 5, 40)
    theta = np.linspace(0, 2 * np.pi, 40)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x_grid = 2 * np.cos(theta_grid)
    y_grid = 2 * np.sin(theta_grid)

    ax.plot_surface(x_grid, y_grid, z_grid, color='cyan', alpha=0.9, edgecolor='#00CED1', lw=0.5)

    # Fonction qui met à jour l'angle de vue à chaque image
    def update(frame):
        ax.view_init(elev=30., azim=frame * 10)
        return fig,

    # Création de l'animation vidéo (36 frames = 360°)
    anim = animation.FuncAnimation(fig, update, frames=36, blit=False)

    # Sauvegarde du fichier vidéo avec FFmpeg
    anim.save(output_file, writer='ffmpeg', fps=15)
    
    print("VIDEO GENERATED:", output_file)