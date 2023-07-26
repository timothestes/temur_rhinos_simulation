import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from temur_rhinos import N_GAMES

# Read the CSV file into a DataFrame
df = pd.read_csv("game_log.csv")

# Filter the DataFrame to only include rows where the turn number is 3
turn_n_df = df[df["turn"] == 3]

# Split the DataFrame based on 'on_the_play'
turn_n_df_true = turn_n_df[turn_n_df["on_the_play"]]
turn_n_df_false = turn_n_df[~turn_n_df["on_the_play"]]

percentage_dfs = []

# For loop to create percentage_df for each on_the_play DataFrame
for i, turn_df in enumerate([turn_n_df_true, turn_n_df_false]):
    # Calculate the percentage
    percentage_df = (
        turn_df.groupby(["n_lands_in_starting_deck", "n_cyclers_in_starting_deck"])
        .apply(lambda group: group["can_play_cascade"].mean())
        .reset_index()
    )
    percentage_df.columns = [
        "n_lands_in_starting_deck",
        "n_cyclers_in_starting_deck",
        "percentage",
    ]

    percentage_dfs.append(percentage_df)

# Calculate the min and max of the whole data for the color mapping
vmin = min(df["percentage"].min() for df in percentage_dfs)
vmax = max(df["percentage"].max() for df in percentage_dfs)

# For loop to create heatmap for each percentage_df
for i, percentage_df in enumerate(percentage_dfs):
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
        annot=annot_array,
        fmt="",
        vmin=vmin,
        vmax=vmax,  # Use the same color mapping
    )

    # Determine on_the_play status
    on_the_play_status = "On the Play" if i == 0 else "On the Draw"
    plt.title(
        f"Percentage of simulations that have 3 untapped lands by turn 3 ({on_the_play_status})",
        fontsize=16,
        pad=30,
    )
    plt.text(
        0.5,
        1.02,
        f"Number of Games per simulation: {N_GAMES}, {on_the_play_status}",
        fontsize=12,
        ha="center",
        va="center",
        transform=plt.gca().transAxes,
    )
    plt.xlabel("Number of cyclers in starting deck")
    plt.ylabel("Number of lands in starting deck")

    # Save the figure to a file
    plt.savefig(f"assets/heatmap_{on_the_play_status.replace(' ', '_').lower()}.png")

plt.show()
