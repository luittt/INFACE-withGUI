import baseGUI
import customtkinter as ctk
from src.scripts.mm_evaluation.compute_head_measurements import compute_head, build_parser

class HeadMeasurementGUI(baseGUI.ModuleGUIBase):
    MODULE_KEY = "headmeasurements"

    def run(self):
        self.write_back()
        compute_head(self.schema)

class App(ctk.CTk):
    def __init__(self, parser):
        super().__init__()
        self.title("Compute Head Measurements")
        self.lift()

        self.gui_frame = HeadMeasurementGUI(self, parser)  # your existing class
        self.gui_frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    parser = build_parser()
    app = App(parser)
    app.mainloop()