# Grid optimization visualization program
# By: George Schwaiger & Claude Haiku 5.5

import importlib.util, subprocess, sys
if importlib.util.find_spec("ipywidgets") is None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ipywidgets"])
import math
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import ipywidgets as widgets
from IPython.display import display, clear_output

# Display settings (visual only, so they live here)
BG, FG = "black", "white"
# Node colors: 0 = seen by no PMU, 1 = seen by one PMU, 2 = seen by two or more PMUs
COLORS = {0: "#7f8c8d", 1: "#f39c12", 2: "#27ae60"}


def drawEverything(buses, lines, entries, sightings, COST_PER_PMU=100_000):
    # Draw the interactive grid map and redundancy-vs-cost chart.

    # buses     : list of bus numbers
    # lines     : list of (bus_a, bus_b) tuples
    # entries   : list of dicts with "pmus" and "percentRedundancy", one per PMU count
    # sightings : function mapping a list of PMU buses to {bus: times seen}
    
    try: #attempt to run this part
        import networkx as nx #call networkx library for visualization
        g = nx.Graph() #create new graph object
        g.add_nodes_from(buses) #add the buses to the graph
        g.add_edges_from(lines) #add the edges to the graph
        pos = nx.spring_layout(g, seed=7) #forces the spacing to look good and consistent
    except ImportError: #runs if import error happened with networkx
        n = len(buses) #counts total nodes
        #backup math in case networkx is not installed, puts the buses in a circle
        pos = {b: (math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n))
               for i, b in enumerate(buses)}
    
    #matplotlib helper function, sets custom color theme for the data plot
    def style_axes(ax):
        """Black background and white text, lines, and ticks for a plot."""
        ax.set_facecolor(BG) #background color of inner plot
        ax.tick_params(colors=FG) #color of axis tick marks
        ax.xaxis.label.set_color(FG) #sets the color for x axis
        ax.yaxis.label.set_color(FG) #sets the color for y axis
        ax.title.set_color(FG) #sets the color of the graph title
        for spine in ax.spines.values(): #sets the color of the four borders of plot
            spine.set_color(FG)
        ax.grid(alpha=0.25, color=FG) #grid across the plot color, a=opacity[%]
    
    
    #widget setup
    #plot space, plot will be built on this
    out = widgets.Output(layout=widgets.Layout(width="100%"))
    #minus sign button to decrease number of PMUes
    minus = widgets.Button(description="−", layout=widgets.Layout(width="140px", height="70px"))
    #plus sign button to increase number of PMUes
    plus = widgets.Button(description="+", layout=widgets.Layout(width="140px", height="70px"))
    idx = {"i": 0} #holds which number of PMUes is being displayed
    
    #engine of visual application, gets called at the start and when buttons are pressed
    def draw():
        """Redraw the grid map, the cost chart, and the status for the current entry."""
        i = idx["i"] #reads the current state of idx, shows which PMU state to display
        entry = entries[i] #retrieve the state of the grid at this index/number of PMUes
        placement = entry["pmus"] #retrieve which buses have PMUes
        k = len(placement) #count number of PMUes total
        pct = entry["percentRedundancy"] #retrieve redundancy percent
        seen = sightings(placement) #calculate which buses are seen
    
        with out: #draw everything in the contained widget
            clear_output(wait=True) #clears the previous plot
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6)) #create both side by side figures
            fig.patch.set_facecolor(BG) #sets the background of the entire figure window
    
            #Left panel, model grid
            for a, b in lines: #for each line
                (x1, y1), (x2, y2) = pos[a], pos[b] #define the lines position
                ax1.plot([x1, x2], [y1, y2], color="#95a5a6", lw=1.5, zorder=1) #draw a line between p1 and p2
            for b in buses: #for each bus
                x, y = pos[b] #define the position of the bus
                ax1.scatter(x, y, s=650, #size of circle
                            c=COLORS[min(seen[b], 2)], #color by how many PMUs see this bus, capped at 2
                            edgecolors=FG if b in placement else "none", #white outline marks PMU buses
                            linewidths=3, zorder=2) #sets the width and ensures the circle is on top
    
            #this part forces the grid to fit inside the gui no matter the grid size
            xs = [pos[b][0] for b in buses] #gathers the x coords of all buses
            ys = [pos[b][1] for b in buses] #gathers the y coords of all buses
            x_lo, x_hi = min(xs), max(xs) #finds the min and max of x coords
            y_lo, y_hi = min(ys), max(ys) #finds the min and max of y coords
            x_span = (x_hi - x_lo) or 1 #finds the total width of the grid, minimum 1
            y_span = (y_hi - y_lo) or 1 #finds the total height of the grid, minimum 1
            #these expand the edges of the border so the grid is not cut off
            ax1.set_xlim(x_lo - 0.12 * x_span, x_hi + 0.12 * x_span)
            ax1.set_ylim(y_lo - 0.12 * y_span, y_hi + 0.40 * y_span)
    
            ax1.set_aspect("equal", adjustable="box") #forces x and y axis to scale equally
            ax1.axis("off") #hides matplotlib axis lines and tick marks for the grid
            ax1.set_title("Model Grid", color=FG, fontsize=14) #gives the title of the grid
    
            #PMU counter label, sits dynamically right underneath the grid title, uses relative coords
            ax1.text(0.5, 1.0, f"PMUs: {k}\nredundancy {pct}%", transform=ax1.transAxes,
                     ha="center", va="top", color=FG, fontsize=12, fontweight="bold",
                     linespacing=1.6)
    
            #Legend for grid plot, sits at the top middle of the gui
            legend_items = [
                Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS[0],
                       markersize=12, label="Seen by no PMU"),
                Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS[1],
                       markersize=12, label="Seen by 1 PMU"),
                Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORS[2],
                       markersize=12, label="Seen by 2+ PMUs"),
                Line2D([0], [0], marker="o", color="none", markerfacecolor=BG,
                       markeredgecolor=FG, markeredgewidth=3, markersize=12,
                       label="PMU location"),
            ]
            leg = fig.legend(handles=legend_items, loc="upper center", #places legend across the whole gui
                             bbox_to_anchor=(0.5, 0.99), ncol=4, frameon=True,
                             facecolor=BG, edgecolor=FG, fontsize=9)
            #forces legend to use white background for visibility
            for text in leg.get_texts():
                text.set_color(FG)
    
            #Right panel, redundancy vs. cost
            counts = [len(e["pmus"]) for e in entries] #makes a list to look at each scenario for PMU counts
            costs = [c * COST_PER_PMU for c in counts] #take each PMU count and multiply it by the PMU cost
            pcts = [e["percentRedundancy"] for e in entries] #extract redundancy from each scenario
    
            ax2.plot(costs, pcts, color=FG, lw=1, marker="o", zorder=1) #draws continuous line graph connecting points
            ax2.scatter(costs[i], pcts[i], s=260, facecolors="none", #draws the glowing red ring around the current PMU count
                        edgecolors="#e74c3c", linewidths=2, zorder=4)
            for cost, count, p in zip(costs, counts, pcts): #iterates through each datapoint
                ax2.annotate(f"{count} PMUs", (cost, p), #puts the number of PMUs per datapoint and formats the point
                             textcoords="offset points", xytext=(0, 10),
                             ha="center", fontsize=9, color=FG)
    
            ax2.set_xticks(costs) #forces x axis tick mark to appear at the right spot
            #sets the min and max of the x axis
            ax2.set_xlim(min(costs) - COST_PER_PMU / 2, max(costs) + COST_PER_PMU / 2)
            #formats the x axis numbers
            ax2.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:,.0f}"))
            ax2.set_ylim(0, 100) #sets min and max of y axis
            #formats the y axis numbers
            ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
            ax2.set_xlabel("Equivalent cost ($100,000 per PMU)", color=FG) 
            ax2.set_ylabel("% redundancy (load-weighted)", color=FG)
            ax2.set_title("Redundancy vs. cost", color=FG)
            style_axes(ax2) #enforces dark background
    
            #tightens the layout to leave room for the grid map legend at the top
            plt.tight_layout(rect=[0, 0, 1, 0.88])
            plt.show() #render
            plt.close(fig) #frees memory behind scenes
    
        minus.disabled = i == 0 #disables (-) button if at minimum # PMUs
        plus.disabled = i == len(entries) - 1 #disables (+) button if at max # PMUs
    
    #helper function to control idx from button presses, makes sure it stays in bounds
    def step(delta):
        """Move forward (+1) or back (-1) through the entries, then redraw."""
        idx["i"] = max(0, min(len(entries) - 1, idx["i"] + delta))
        draw() #refreshes dashboard immediately after button is updated
    
    #connects button UI to python events by calling step function
    minus.on_click(lambda _: step(-1))
    plus.on_click(lambda _: step(+1))
    
    #wraps the buttons in a box and sets the dimensions
    buttons = widgets.HBox([minus, plus],
                           layout=widgets.Layout(width="100%", justify_content="center"))
    display(widgets.VBox([out, buttons], #displays widgets
                         layout=widgets.Layout(width="100%", align_items="center")))
    draw() #draw the scenario