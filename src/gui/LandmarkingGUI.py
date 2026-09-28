import baseGUI
import customtkinter as ctk
from src.processing.predict_3d_labels import process_scans, build_parser

class LandmarkPredictionGUI(baseGUI.ModuleGUIBase):
    MODULE_KEY = "landmarking"

    def run(self):
        self.write_back()
        process_scans(self.to_args())

class App(ctk.CTk):
    def __init__(self, parser):
        super().__init__()
        self.title("Landmarking")
        self.lift()

        self.gui_frame = LandmarkPredictionGUI(self, parser)  # your existing class
        self.gui_frame.pack(fill="both", expand=True)
        self.attributes("-topmost", True)
        self.attributes("-topmost", False)
        self.focus_force()

if __name__ == "__main__":
    parser = build_parser()
    app = App(parser)
    app.mainloop()