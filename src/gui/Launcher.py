import customtkinter as ctk

#from LandmarkingGUI import LandmarkPredictionGUI
#from src.processing.predict_3d_labels import build_parser as build_landmarking_parser

from RegistrationGUI import RegistrationGUI  # adjust import path/class name as needed
from src.processing.registration import build_parser as build_registration_parser  # adjust path

from HeadMeasurementsGUI import HeadMeasurementGUI
from src.scripts.mm_evaluation.compute_head_measurements import build_parser as build_measurement_parser

#from OptimumGUI import computeOptimumGUI  # adjust import path/class name as needed
#from src.scripts.mm_evaluation.compute_optimal_head import build_parser as build_optimum_parser


MODULES = [
    #("Landmarking", LandmarkPredictionGUI, build_landmarking_parser),
    ("Registration", RegistrationGUI, build_registration_parser),
    ("Head Measurements", HeadMeasurementGUI, build_measurement_parser),
    #("Compute optimal Head", computeOptimumGUI, build_optimum_parser),
]


class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Pipeline Launcher")
        self.geometry("300x400")

        self.open_windows = {}

        for label, gui_cls, parser_fn in MODULES:
            btn = ctk.CTkButton(
                self, text=label,
                command=lambda l=label, g=gui_cls, p=parser_fn: self.open_module(l, g, p),
            )
            btn.pack(fill="x", padx=20, pady=10)

    def open_module(self, label, gui_cls, parser_fn):
        win = self.open_windows.get(label)
        if win is not None and win.winfo_exists():
            win.lift()
            win.focus()
            return

        top = ctk.CTkToplevel(self)
        top.title(label)
        top.geometry("1000x600")

        parser = parser_fn()
        frame = gui_cls(top, parser)
        frame.pack(fill="both", expand=True)

        self.open_windows[label] = top


if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()