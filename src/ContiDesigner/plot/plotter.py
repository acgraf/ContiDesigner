from . import time_evolution, dilution_range, feed_volume_split


class Plotter:
    def __init__(self, model, solver):
        self.model = model
        self.solver = solver

    def plot_time_evolution(self, cascade=True):
        return time_evolution.plot_time_evolution(self, cascade)
    
    def plot_D_range(self, Data=None):
        return dilution_range.plot_D_range(self, Data)

    def plot_contour(self, sweep="phi_ny", contour="delta_sty_opt", Data=None, ncontours=40):
        return feed_volume_split.plot_contour(self, sweep, contour, Data, ncontours)




    
