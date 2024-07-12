import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import re
import alphashape
import os

# ----------
# Functions
# ----------

def load_data_maestro(data):
    # 0 is a space separated list in the form of '[x, y, z], the number of spaces is not fixed'
    data['0'] = data['0'].str.replace('[', '').str.replace(']', '')
    data['0'] = data['0'].str.strip()
    data['0'] = data['0'].apply(lambda x: re.sub(r'\s+', ',', x))
    data[['x', 'y', 'z']] = data['0'].str.split(',', expand=True)
    data['x'] = data['x'].astype(float)
    data['y'] = data['y'].astype(float)
    data['z'] = data['z'].astype(float)
    data = data.drop(columns=['0'])
    return data

def load_data_vmd(file_path):
    # single line txt file in the form of '{x y z} {x y z} {x y z} ...'
    with open(file_path, 'r') as file:
        data = file.readlines()[0]
        data = data.split("} {")
        data[0] = data[0].replace("{", "")
        data[-1] = data[-1].replace("}", "").replace("\n", "")
    for i in range(len(data)):
        data[i] = data[i].split(" ")
        data[i] = [float(x) for x in data[i]]
    data = pd.DataFrame(data, columns=['x', 'y', 'z'])
    
    return data

def update_loading_plot(fraction_inside):
    # Plot the loading curve
    ax_laoding_curve.clear()
    ax_laoding_curve.plot(np.arange(0, 1.01, 0.01), loading, color='cornflowerblue')
    ax_laoding_curve.axhline(loading[1], color='crimson', linestyle='--')
    ax_laoding_curve.axhline(loading[-1], color='crimson', linestyle='--')
    ax_laoding_curve.axvline(fraction_inside, color='goldenrod', linestyle='--')
    ax_laoding_curve.set_xlabel('Fraction Inside')
    ax_laoding_curve.set_ylabel('Encapsulation Efficiency (%)')

    # Plot the data in 3D
    ax_3d_view.clear()
    # ax_3d_view.scatter(polymer_data['x'], polymer_data['y'], polymer_data['z'], s=0.1)
    ax_3d_view.plot_trisurf(*zip(*alpha_shape.vertices), triangles=alpha_shape.faces, color='cornflowerblue', alpha=0.1)
    for i, drug in enumerate(drug_data):
        try:
            ax_3d_view.scatter(drug['x'], drug['y'], drug['z'], s=0.1, c='forestgreen' if np.sum(is_inside[i]) / len(is_inside[i]) >= fraction_inside else 'crimson')
        except:
            pass
    
    # rotate the view through 90 degrees based on the fraction_inside value (0.0 -> 0 degrees, 1.0 -> 90 degrees)
    # ax_3d_view.view_init(30, 90 * fraction_inside)
    
    plt.draw()

# ----------
# Setup
# ----------

sample_name = "10gcpq_142propofol_pH7_nonwrap"
data_path = f"data\{sample_name}"
polymer_file_name = "GCPQ.txt"

# https://en.wikipedia.org/wiki/Alpha_shape
# https://github.com/bellockk/alphashape
alpha_param = 0.1

# Save a gif of the fraction_inside changing (slow)
save_gif = False

# ----------
# Main
# ----------

# Load the data
polymer_data_path = os.path.join(data_path, polymer_file_name)
drug_data_paths = [os.path.join(data_path, file) for file in os.listdir(data_path) if file.endswith(".txt") and file != polymer_file_name]
polymer_data = load_data_vmd(polymer_data_path)
drug_data = []
for drug_data_path in drug_data_paths:
    drug_data.append(load_data_vmd(drug_data_path))

# Calculate the alpha shape
points_3d = list(polymer_data[['x', 'y', 'z']].itertuples(index=False, name=None))
alpha_shape = alphashape.alphashape(points_3d, alpha=alpha_param)

# For each drug, determine if each atom is inside the alpha shape
is_inside = []
for drug in drug_data:
    point = list(drug[['x', 'y', 'z']].itertuples(index=False, name=None))
    inside = alpha_shape.contains(point)
    is_inside.append(inside)

# Calculate the loading curve (encapsulation efficiency vs fraction inside)
loading = []
for fraction_inside in np.arange(0, 1.01, 0.01):
    is_encapsulated = np.sum([np.sum(inside) / len(inside) >= fraction_inside for inside in is_inside])
    is_inside_fraction = is_encapsulated / len(is_inside) * 100
    loading.append(is_inside_fraction)

# ----------
# Output
# ----------

# Save the loading curve as a csv
loading_df = pd.DataFrame({'Fraction Inside': np.arange(0, 1.01, 0.01), 'Encapsulation Efficiency (%)': loading})
loading_df = loading_df.round(2)
loading_df.to_csv(f'data\{sample_name}_loading.csv', index=False)


# Plot the data
fig = plt.figure(figsize=(12, 6))
ax_laoding_curve = fig.add_subplot(121)
ax_3d_view = fig.add_subplot(122, projection='3d')

# 0.00 corresponds to 0% of the drug being inside the polymer
# 0.01 corresponds to 1% of the drug being inside the polymer (essentially any overlap counts as encapsulation)
# 1.00 corresponds to 100% of the drug being inside the polymer
fraction_inside = 0.01
update_loading_plot(fraction_inside)

# Create a data folder if it doesn't exist
if not os.path.exists('data'):
    os.makedirs('data')

# Save the loading curve
plt.savefig(f'data\{sample_name}_loading.png')

# Save a gif of the fraction_inside changing
if save_gif:
    ani = animation.FuncAnimation(fig, update_loading_plot, np.arange(0.01, 1.01, 0.01), interval=100)
    ani.save(f'data\{sample_name}_loading.gif', writer='imagemagick', fps=20)
