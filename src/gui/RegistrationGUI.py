import baseGUI
import customtkinter as ctk
from src.processing.registration import run_registration, build_parser

class RegistrationGUI(baseGUI.ModuleGUIBase):
    MODULE_KEY = "registration"

    def run(self):
        self.write_back()
        run_registration(self.to_args())

class App(ctk.CTk):
    def __init__(self, parser):
        super().__init__()
        self.title("Registration")
        self.lift()

        self.gui_frame = RegistrationGUI(self, parser)  # your existing class
        self.gui_frame.pack(fill="both", expand=True)


if __name__ == "__main__":
    parser = build_parser()
    app = App(parser)
    app.mainloop()