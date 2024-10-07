import itertools



def plotSingle(ax, xs, ys, title, xlabel, ylabel, log, xticks=None, ylim=None):
    marker = itertools.cycle(("o", "v", "s", "x", "^")) 

    m = next(marker)
    ax.plot(xs, ys, marker=m)
        
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if log:
        ax.set_yscale("log")
    ax.grid(True, which="both")

    if xticks is not None:
        ax.set_xticks(xticks)
    else:
        ax.set_xticks(xs)
    
    if ylim is not None:
        ax.set_ylim(ylim)



def plotMultiple(ax, xs, yss, title, xlabel, ylabel, log, xticks=None, ylim=None):
    marker = itertools.cycle(("o", "v", "s", "x", "^")) 

    for ys in yss:
        m = next(marker)
        ax.plot(xs, ys, marker=m)
        
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if log:
        ax.set_yscale("log")
    ax.grid(True, which="both")

    if xticks is not None:
        ax.set_xticks(xticks)
    else:
        ax.set_xticks(xs)
    
    if ylim is not None:
        ax.set_ylim(ylim)



def plotScatter(ax, xs, ys, title, xlabel, ylabel, log, xticks=None, ylim=None):
    marker = itertools.cycle(("o", "v", "s", "x", "^")) 

    for x, y in zip(xs, ys):
        m = next(marker)
        ax.scatter(xs, ys, marker=m)
        
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if log:
        ax.set_yscale("log")
    ax.grid(True, which="both")

    if xticks is not None:
        ax.set_xticks(xticks)
    else:
        ax.set_xticks(xs)
    
    ax.set_xlim([-1, len(xs)])
    if ylim is not None:
        ax.set_ylim(ylim)