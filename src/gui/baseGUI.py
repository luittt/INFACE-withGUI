from logging import NullHandler

import customtkinter as ctk
import yaml
from yaml import Loader
import argparse
from pathlib import Path
from src.processing.utils import path_type
from TkToolTip import ToolTip
from tkinter import TclError



class ModuleGUIBase(ctk.CTkFrame):
    MODULE_KEY: str = None  # set by subclass, e.g. "landmarking" or "registration"

    def __init__(self, master, parser: argparse.ArgumentParser, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        assert self.MODULE_KEY is not None, "Subclass must set MODULE_KEY"
        self.parser = parser
        self.schema = generate_schema(parser)
        self.chooser_widgets = {}
        self.yaml_path: Path | None = None
        self.optional_chooser_widgets = {}
        self.tips = []

        self._build_static_widgets()
        self._render_fallback_choosers()
        self.after(0, self._maximize)

    def _maximize(self):
        win = self.winfo_toplevel()
        try:
            win.state("zoomed")  # Windows (and macOS on recent Tk)
        except TclError:
            try:
                win.attributes("-zoomed", True)  # Linux/X11
            except TclError:
                # fallback: raw screen size
                win.geometry(f"{win.winfo_screenwidth()}x{win.winfo_screenheight()}+0+0")

    def run(self):
        raise NotImplementedError  # each subclass defines what "run" means

    def _set_value(self, dest, value):
        self.schema[dest]["value"] = value

    def hide_tips(self):
        for tip in self.tips:
            tip.on_leave(None)
        self.update_idletasks()

    def _build_static_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(7, weight=1)

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.grid(row=0, column=0, sticky="nw", padx=10, pady=(10, 5))

        self.load_button = ctk.CTkButton(button_row, text="Load config", command=self.load_yaml)
        self.load_button.grid(row=1, column=0, sticky="w", padx=10, pady=(10, 5))

        tip = ToolTip(self.load_button,
                msg=f"Load .YAML config file that contains the required fields to start the {self.MODULE_KEY} module.",
                delay=0.1, follow=True,
                fg="black", bg="lightgray")
        self.tips.append(tip)

        self.run_button = ctk.CTkButton(button_row, text=f"Run {self.MODULE_KEY}", command=self.run, state="disabled")
        self.run_button.grid(row=2, column=0, sticky="e", padx=10, pady=(10, 5))

        self.status_label = ctk.CTkLabel(self, text="No config loaded yet.", justify="left")
        self.status_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))
        self.bind(
            "<Configure>",
            lambda e: self.status_label.configure(wraplength=max(e.width - 40, 50))
        )

        self.req_label = ctk.CTkLabel(self, text="Required arguments:", justify="left", font=("Helvetica", 18, "bold"))
        self.req_label.grid(row=4, column=0, sticky="w", padx=10, pady=(20, 5))

        self.fields_frame = ctk.CTkFrame(self)
        self.fields_frame.grid(row=5, column=0, columnspan=2, sticky="nswe", padx=30, pady=(10, 5))

        self.optional_label = ctk.CTkLabel(self, text="Optional arguments:", justify="left", font=("Helvetica", 18, "bold"))
        self.optional_label.grid(row=6, column=0, sticky="w", padx=10, pady=(20, 5))
        self.optional_chooser_widgets = {}

        self.optional_frame = ctk.CTkScrollableFrame(self)
        self.optional_frame.grid(row=7, column=0, columnspan=2 , sticky="nwse", padx=30, pady=(10, 5))


    def load_yaml(self):
        yaml_path = ctk.filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml *.yml")])
        if not yaml_path:
            return
        self.yaml_path = Path(yaml_path)
        with open(self.yaml_path, "r") as f:
            loaded = yaml.load(f, Loader=Loader) or {}
        section = loaded.get(self.MODULE_KEY, {})
        for dest in self.schema:
            if dest in section:
                self.schema[dest] = section[dest]
        self._render_fallback_choosers()

    def _render_optional_args(self):
        for widget in self.optional_frame.winfo_children():
            widget.destroy()
        self.optional_chooser_widgets.clear()

        optional_dests = [
            dest for dest, spec in self.schema.items()
            if not spec.get("required", False)
        ]
        self._render_choosers(
            optional_dests,
            parent=self.optional_frame,
            widget_store=self.optional_chooser_widgets,
            invalid=validate_values(self.schema),
        )

    def _render_fallback_choosers(self):
        self.hide_tips()
        self.tips.clear()
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
        self.chooser_widgets.clear()

        invalid = validate_values(self.schema)
        required_dests = [dest for dest, spec in self.schema.items() if spec.get("required", True)]

        if not invalid:
            self.status_label.configure(text="All required fields present and valid.", text_color="green")
            self.run_button.configure(state="normal")
        else:
            self.status_label.configure(text=f"Missing or invalid: {', '.join(invalid)}", text_color="red")
            self.run_button.configure(state="disabled")

        self._render_choosers(required_dests, invalid=invalid)
        self._render_optional_args()

    def int_change(self, val, d, num_widget):
        val = val.get().strip()
        try:
            int(val)
            num_widget.configure(fg_color="white", border_color="green")  # valid > normal
            self._set_value(d, val)
        except ValueError:
            num_widget.configure(fg_color="#3b3b3b", border_color="red")  # invalid > red

    def change_entry(self, d, v, str_entr):
        try:
            v = str(v)
            self._set_value(d, v)
            str_entr.configure(border_color="green")
        except ValueError:
            str_entr.configure(border_color="red")

    def _render_choosers(self, items, parent=None, widget_store=None, invalid=None):
        parent = parent or self.fields_frame
        widget_store = self.chooser_widgets if widget_store is None else widget_store
        invalid = invalid or []
        for dest in items:
            spec = self.schema[dest]

            is_valid = bool(spec.get("value")) and dest not in invalid
            row = ctk.CTkFrame(parent)
            row.pack(fill="x", pady=5, padx=10)
            row.grid_columnconfigure(1, weight=1)
            label = ctk.CTkLabel(row, text=dest, width=180, anchor="w")
            label.grid(row=0, column=0, padx=(10, 10))

            tip = ToolTip(row, msg=str(spec.get("help", "")), delay=0.1, follow=True,
                    fg="black", bg="lightgray")
            self.tips.append(tip)

            kind = spec.get("kind")
            value = spec.get("value")

            if kind == "bool":
                value = value if value else False
                check = ctk.CTkCheckBox(row, text=value or "True/False",
                                        command=lambda d=dest, v=value: self._set_value(d, v))
                check.grid(row=0, column=1, sticky="w")
                widget_store[dest] = check
            elif kind == "choice":
                choices = [str(v) for v in spec.get("choices")]
                menu_var = ctk.StringVar(value=value or "choose...")
                menu = ctk.CTkOptionMenu(row, values=choices, variable=menu_var)
                menu.grid(row=0, column=1, sticky="w")
                widget_store[dest] = menu
            elif kind == "int":
                var = ctk.StringVar(value=str(value or "1"))
                num = ctk.CTkEntry(row, textvariable=var)
                num.grid(row=0, column=1, sticky="w")
                var.trace("w", lambda *args, v=var, d=dest, n=num: self.int_change(v, d, n))
                widget_store[dest] = num
            elif kind == "str":
                var = ctk.StringVar(value=str(value or ""))
                entr = ctk.CTkEntry(row, textvariable=var)
                var.trace("w", lambda d=dest, v=var: self.change_entry(d, v.get(), entr))
                entr.grid(row=0, column=1, sticky="w")
                widget_store[dest] = entr
            elif kind in ("folder", "file"):
                self.make_button(row, kind, is_valid, dest, widget_store, value)
            elif kind == "file_or_folder":
                if value is None:
                    holder = ctk.CTkFrame(row, fg_color="transparent")
                    holder.grid(row=0, column=1, sticky="ew")
                    holder.grid_columnconfigure((0, 2), weight=1)
                    self.make_button(holder, "file", is_valid, dest, widget_store, value, column=0)
                    ctk.CTkLabel(holder, text="or").grid(row=0, column=1, padx=8)
                    self.make_button(holder, "folder", is_valid, dest, widget_store, value, column=2)
                else:
                    self.make_button(row, "file", is_valid, dest, widget_store, value)

            for child in row.winfo_children():
                child.bind("<Enter>", tip.on_enter)
                child.bind("<Leave>", tip.on_leave)

    def make_button(self, row, kind, is_valid, dest, widget_store, value, column=1):
        btn = ctk.CTkButton(row,
                            text=value or f"choose {kind}...",
                            fg_color="green" if is_valid else None,
                            hover_color="darkgreen" if is_valid else None,
                            command=lambda d=dest, k=kind: self.choose_path(d, k))
        btn.grid(row=0, column=column, sticky="ew")
        widget_store[f"{dest}:{kind}"] = btn
        return btn

    def choose_path(self, dest: str, kind: str):
        self.hide_tips()
        file_types = self.schema[dest].get("file_types") or [("All files", "*.*")]
        if kind == "folder":
            path = ctk.filedialog.askdirectory()
        elif kind == "file":
            path = ctk.filedialog.askopenfilename(filetypes=file_types)
        else:
            path = None
        if path:
            self._set_value(dest, path)
            self._render_fallback_choosers()

    def write_back(self):
        if self.yaml_path is None:
            save_path = ctk.filedialog.asksaveasfilename(defaultextension=".yaml",
                                                         filetypes=[("YAML files", "*.yaml *.yml")],
                                                         confirmoverwrite=False,)
            if not save_path:
                return
            self.yaml_path = Path(save_path)
            existing = {}
        else:
            with open(self.yaml_path, "r") as f:
                existing = yaml.safe_load(f) or {}

        existing[self.MODULE_KEY] = {key: val for key, val in self.schema.items() if val.get("value") is not None}

        with open(self.yaml_path, "w") as f:
            yaml.dump(existing, f, sort_keys=False, default_flow_style=False)

        self.status_label.configure(text=f"Saved to {self.yaml_path.name}")

    def to_args(self) -> argparse.Namespace:
        actions = {a.dest: a for a in self.parser._actions}
        argv = []
        for dest, spec in self.schema.items():
            value = spec.get("value")
            if value in (None, "") or value is False:
                continue
            flag = actions[dest].option_strings[0]
            argv.append(flag)
            if spec["kind"] != "bool":
                argv.append(str(value))
        return self.parser.parse_args(argv)

def generate_schema(parser: argparse.ArgumentParser) -> dict:
    schema = {}
    for action in parser._actions:
        if isinstance(action, argparse._HelpAction) or getattr(action, "gui_hidden", False):
            continue
        dest = action.dest

        if isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
            arg_type = "bool"
            kind = "bool"
        elif action.choices is not None:
            arg_type = "str"
            kind = "choice"
        elif action.type is path_type:
            arg_type = "path"
            kind = getattr(action, "chooser_kind", "file")  # fallback if someone forgets to set it
        elif action.type is not None:
            arg_type = getattr(action.type, "__name__", str(action.type))
            kind = arg_type if arg_type in ("int", "str") else "str"
        else:
            arg_type = "str"
            kind = "str"

        schema[dest] = {
            "value": action.default if action.default else None,
            "required": action.required or bool(getattr(action, "waivable_by", None)),
            "waivable_by": getattr(action, "waivable_by", None),
            "type": arg_type,
            "kind": kind,
            "nargs": action.nargs,
            "choices": list(action.choices) if action.choices is not None else None,
            "help": action.help if action.help else "No info available :(",
            "file_types": getattr(action, "file_types", None),
        }
    return schema

def validate_values(schema: dict, force_required: frozenset = frozenset()) -> list[str]:
    invalid = []
    for dest, spec in schema.items():
        required = spec["required"] or dest in force_required
        waiver = spec.get("waivable_by")
        if required and waiver and schema.get(waiver, {}).get("value"):
            required = False
        value = spec.get("value")
        if required and not value:
            invalid.append(dest)
            continue
        if spec["type"] == "path" and value and not Path(value).exists():
            invalid.append(dest)
    return invalid