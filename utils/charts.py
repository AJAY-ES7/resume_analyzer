import matplotlib.pyplot as plt
import os
import numpy as np

# --------------------------------------------------
# Bar Chart: Matched vs Missing Skills
# --------------------------------------------------
def generate_bar_chart(matched, missing, filename):
    labels = ['Matched Skills', 'Missing Skills']
    values = [len(matched), len(missing)]

    plt.figure()
    plt.bar(labels, values)
    plt.title('Skill Comparison')
    plt.ylabel('Count')

    path = os.path.join('static/charts', filename)
    plt.savefig(path)
    plt.close()

    return path


# --------------------------------------------------
# Radar Chart: Skill Coverage
# --------------------------------------------------
def generate_radar_chart(matched, jd_skills, filename):
    categories = jd_skills
    total = len(categories)

    if total == 0:
        return None

    values = []
    for skill in categories:
        values.append(1 if skill in matched else 0)

    values += values[:1]  # close the loop

    angles = np.linspace(0, 2 * np.pi, total, endpoint=False).tolist()
    angles += angles[:1]

    plt.figure()
    ax = plt.subplot(111, polar=True)
    ax.plot(angles, values)
    ax.fill(angles, values, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), categories)
    ax.set_title("Skill Coverage Radar")

    path = os.path.join('static/charts', filename)
    plt.savefig(path)
    plt.close()

    return path
