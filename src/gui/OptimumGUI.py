import baseGUI
import customtkinter as ctk
from src.scripts.mm_evaluation.compute_optimal_head import build_parser, compute_optimal_head

class computeOptimumGUI(baseGUI.ModuleGUIBase):
    MODULE_KEY = "optimum"

    def run(self):
        self.write_back()
        compute_optimal_head(self.schema)

class App(ctk.CTk):
    def __init__(self, parser):
        super().__init__()
        self.title("Compute optimal Head")
        self.lift()

        self.gui_frame = computeOptimumGUI(self, parser)  # your existing class
        self.gui_frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    parser = build_parser()
    app = App(parser)
    app.mainloop()