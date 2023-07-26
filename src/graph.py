import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from temur_rhinos import N_GAMES, ON_THE_PLAY

# Read the CSV file into a DataFrame
df = pd.read_csv("game_log.csv")

# Filter the DataFrame to only include rows where the turn number is 3 (or whatever turn number you're interested in)
turn_n_df = df[df["turn"] == 3]

# Calculate the percentage of simulations with each combination of number of lands and cyclers that had 3 lands in play
percentage_df = (
    turn_n_df.groupby(["n_lands_in_starting_deck", "n_cyclers_in_starting_deck"])
    .apply(lambda group: group["can_play_cascade"].mean())
    .reset_index()
)
percentage_df.columns = ["n_lands_in_starting_deck", "n_cyclers_in_starting_deck", "percentage"]

# Create a pivot table
pivot_table = percentage_df.pivot(
    index="n_lands_in_starting_deck", columns="n_cyclers_in_starting_deck", values="percentage"
)

# Create an array of formatted strings to use for annotation
annot_array = pivot_table.values
annot_array = np.vectorize("{:.3f}".format)(annot_array)

# Create the desired graph
plt.figure(figsize=(10, 8))
sns.heatmap(
    pivot_table,
    cmap="RdYlGn",
    annot=annot_array,  # pass in formatted annotation array here
    fmt="",  # prevent seaborn from applying additional formatting
)
plt.title("Percentage of simulations that have 3 untapped lands by turn 3", fontsize=16, pad=30)
plt.text(
    0.5,
    1.02,
    f"Number of Games per simulation: {N_GAMES}, On the play: {ON_THE_PLAY}",
    fontsize=12,
    ha="center",
    va="center",
    transform=plt.gca().transAxes,
)
plt.xlabel("Number of cyclers in starting deck")
plt.ylabel("Number of lands in starting deck")

# Save the figure to a file
plt.savefig("assets/heatmap.png")

plt.show()
