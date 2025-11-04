import nflreadpy as nfl
import pandas as pd
import matplotlib.pyplot as plt

def pass_protection(plotGraph = False, export = False):
    # Loads all play by play data from nflreadpy
    pbp_2025 = nfl.load_pbp(2025).to_pandas()

    # Drops rows indicating end of play (quarter end, two minute warning, end of OT)
    pbp_2025 = pbp_2025.dropna(subset=['play_type'])

    # Only selects plays where the Giants were in possession
    offensive_giants_snaps = pbp_2025.query("posteam == 'NYG'")

    # Only selects plays where the quarterback dropped back (indicating a pass play)
    pass_block_snaps = offensive_giants_snaps.query("qb_dropback == 1")

    # Filters out extra point attempts and two point attempts, where the data is incomplete
    pass_block_snaps = pass_block_snaps.query("extra_point_attempt == 0 and two_point_attempt == 0")

    '''
    Creates a new 'yards_until_reset' column in the Pandas dataframe that bins 
    the yards until the next first down or goal (reset).
    '''
    bins = [0, 4, 7, 10, 100]
    labels = ['Short (1-3)', 'Medium (4-6)', 'Long (7-9)', 'Very Long (10+)']
    pass_block_snaps['yards_until_reset'] = pd.cut(
        pass_block_snaps['ydstogo'], 
        bins=bins, 
        labels=labels, 
        right=False,
        include_lowest=True
    )

    blocking_by_down = pass_block_snaps.groupby(["down", "yards_until_reset"], observed=False).agg(
        # Sum the 'sack' column to get the total number of sacks
        Total_Sacks=('sack', 'sum'),
        
        # Count the number of plays to get total attempts (the denominator)
        Total_Dropbacks=('play_id', 'count')
    )

    # Calculates the sack rate and inputs the data into a new column in the dataframe
    blocking_by_down['Sack_Rate'] = (
        blocking_by_down['Total_Sacks'] / blocking_by_down['Total_Dropbacks']
    ) * 100

    if plotGraph:
        # Reshapes the data for plotting
        plot_data = blocking_by_down['Sack_Rate'].unstack(fill_value=0)

        fig, ax = plt.subplots(figsize=(10, 6))

        plot_data.plot.barh(ax=ax, rot=0, color=['#0B2265', '#a71930', '#a5acaf', 'gold'])
        ax.set_title(f"NYG Pass Protection By Down", 
                fontsize=14)
        ax.set_xlabel("Sack Rate", fontsize=12)
        ax.set_ylabel("Down", fontsize=12)
        ax.legend()
        ax.margins(x=0.1)

        for container in ax.containers:
            ax.bar_label(container, label_type='edge', fmt='{:,.2f}%', padding=3)

        ax.set_yticklabels(['1', '2', '3', '4'])

        plt.tight_layout()
        plt.show()

    if export:
        # Outputs the final data as a CSV file
        blocking_by_down.to_csv('giants_blocking_analysis.csv')

if __name__ == "__main__":
    pass_protection(plotGraph=True, export=False)