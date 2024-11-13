import os
import traceback
import cv2
import tkinter as tk
from tkinter import filedialog, font
import numpy as np
from PIL import Image, ImageTk, ImageSequence
import json
import time
import copy
import bisect
import torch
import torchvision
import customtkinter as ctk

torchvision.disable_beta_transforms_warning()
import mimetypes
import webbrowser
from random import random, randint, shuffle

import rope.GUIElements as GE
import rope.Styles as style

from skimage import transform as trans
from torchvision.transforms import v2
from tkinter import messagebox
from multiprocessing import Pool, Manager

from os import listdir
from os.path import isfile, join
import inspect #print(inspect.currentframe().f_back.f_code.co_name, 'resize_image')
import platform
from platform import system
from rope.Dicts import CAMERA_BACKENDS, DEFAULT_DATA
from rope.FaceLandmarks import FaceLandmarks
from rope.FaceEditor import FaceEditor
from rope.Hovertip import RopeHovertip
import gc

def process_video(file):
    try:
        video = cv2.VideoCapture(file)
        if video.isOpened():
            video.set(cv2.CAP_PROP_POS_FRAMES, int(video.get(cv2.CAP_PROP_FRAME_COUNT) / 2))
            success, video_frame = video.read()

            if success:
                video_frame = cv2.cvtColor(video_frame, cv2.COLOR_BGR2RGB)
                ratio = float(video_frame.shape[0]) / video_frame.shape[1]
                new_height = 100
                new_width = int(new_height / ratio)
                video_frame = cv2.resize(video_frame, (new_width, new_height))
                return video_frame
            else:
                print('Trouble reading file:', file)
        else:
            print('Trouble opening file:', file)
    except Exception as e:
        print('Error processing file:', file, e)
    finally:
        video.release()

    return None

class GUI(tk.Tk):
    def __init__(self, models):
        super().__init__()

        self.models = models
        self.title_text = 'Rope-Next-00'
        self.title(self.title_text)
        self.target_media = []
        self.target_video_file = []
        self.action_q = []
        self.video_image = []
        self.video_loaded = False
        self.image_loaded = False
        self.media_file = []
        self.media_file_name = []
        self.stop_marker = []
        self.stop_image = []
        self.stop_marker_icon = []
        self.window_last_change = []
        self.blank = tk.PhotoImage()
        self.output_folder = []
        self.output_videos_text = []
        self.target_media_buttons = []
        self.target_media_shuffle_history = set()
        self.all_target_media_thumbnails_generated = False
        self.input_videos_button = []
        self.input_videos_text = []
        self.target_media_canvas = []
        self.source_faces_buttons = []
        self.input_videos_button = []
        self.input_faces_text = []
        self.shift_i_len = 0
        self.source_faces_canvas = []
        self.video = []
        self.video_slider = []
        self.found_faces_canvas = []
        self.merged_embedding_name = []
        self.merged_embeddings_text = []
        self.me_name = []
        self.merged_faces_canvas = []
        self.parameters = {}
        self.scroll_timeout = []
        # Face Editor
        self.parameters_face_editor = {}
        self.control = {}
        self.widget = {}
        self.static_widget = {}
        self.layer = {}

        self.temp_emb = []

        self.arcface_dst = np.array([[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366], [41.5493, 92.3655], [70.7299, 92.2041]], dtype=np.float32)

        self.json_dict =    {
                            "source videos":    None,
                            "source faces":     None,
                            "saved videos":     None,
                            'dock_win_geom':    [1400, 800, self.winfo_screenwidth()/2-400, self.winfo_screenheight()/2-510],
                            }

        self.marker =  {
                        'frame':        '0',
                        'parameters':   '',
                        'icon_ref':     '',
                        }
        self.markers = []

        self.target_face = {
                            "TKButton":                 [],
                            "ButtonState":              "off",
                            "Image":                    [],
                            "Embedding":                [],
                            "SourceFaceAssignments":    [],
                            "EmbeddingNumber":          0,      #used for adding additional found faces
                            'AssignedEmbedding':        [],     #the currently assigned source embedding, including averaged ones
                            'DFLModel':                 False,
                            }
        self.target_faces = []

        self.selected_source_face = {
                            "TKButton":                 [],
                            "ButtonState":              "off",
                            "Image":                    [],
                            "Embedding":                [],   
                            "EmbeddingWeight":          [],
                            'DFLModel':                 False,
                            "ButtonText":               [],
                            }
        self.selected_source_faces = []

        self.source_face =  {
                            "TKButton":                 [],
                            "ButtonState":              "off",
                            "Image":                    [],
                            "Embedding":                [],
                            'DFLModel':                 False,
                            "ButtonText":               [],
                            "Size":                     [],
                            }
        self.source_faces = []

        #region [#111111b4]

        script_dir = os.path.dirname(__file__)
        icon_path = os.path.join(script_dir, 'media', 'rope.ico')
        if system() != 'Linux':
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)

        #endregion

        #region [#131710b4]

        # Default Parameters Visibility Configuration
        self.default_params_visibility = {}
        self.default_params_face_editor_visibility = {}

        def load_shortcuts_from_json():
            try:
                with open("shortcuts.json", "r") as json_file:
                    return json.load(json_file)
            except FileNotFoundError:
                return {
                    "Timeline Beginning": "z",
                    "Nudge Left 30 Frames": "a",
                    "Nudge Right 30 Frames": "d",
                    "Record": "r",
                    "Play": "space",
                    "Save Image": "ctrl+s",
                    "Add Marker": "f",
                    "Delete Marker": "alt+f",
                    "Previous Marker": "q",
                    "Next Marker": "w",
                    "Toggle Restorer": "1",
                    "Toggle Restorer2": "h",
                    "Toggle Orientation": "2",
                    "Toggle Strength": "3",
                    "Toggle Differencing": "4",
                    "Toggle Occluder": "5",
                    "Toggle Face Parser": "6",
                    "Toggle Text-Based Masking": "7",
                    "Toggle Color Adjustments": "8",
                    "Toggle Face Adjustments": "9",
                    "Clear VRAM": "F1",
                    "Find Faces": "ctrl+f",
                    "Swap Faces": "s",
                    "Toggle Auto Swap": "ctrl+a",
                    "Nudge Left 1 Frame": "c",
                    "Nudge Right 1 Frame": "v",
                    "Show Mask": "x",
                    "Previous Media": "left",
                    "Next Media": "right",
                    "Delete Media": "delete",
                }
        shortcuts = load_shortcuts_from_json()

        # Update text variables with loaded shortcuts
        text_vars = {}
        for shortcut_name, default_value in shortcuts.items():
            text_vars[shortcut_name] = tk.StringVar(value=default_value)

        # Update self.key_actions with loaded shortcuts
        self.key_actions = {
            shortcuts["Timeline Beginning"]: lambda: self.preview_control('q'),
            shortcuts["Nudge Left 30 Frames"]: lambda: self.preview_control('a'),
            shortcuts["Record"]: lambda: self.toggle_rec_video(),
            shortcuts["Play"]: lambda: self.toggle_play_video(),
            shortcuts["Nudge Right 30 Frames"]: lambda: self.preview_control('d'),
            shortcuts["Save Image"]: lambda: self.save_image(),
            shortcuts["Add Marker"]: lambda: self.update_marker('add'),
            shortcuts["Delete Marker"]: lambda: self.update_marker('delete'),
            shortcuts["Previous Marker"]: lambda: self.update_marker('prev'),
            shortcuts["Next Marker"]: lambda: self.update_marker('next'),
            shortcuts["Toggle Restorer"]: lambda: self.toggle_and_update('Restorer', 'Restorer'),
            shortcuts["Toggle Restorer2"]: lambda: self.toggle_and_update('Restorer2', 'Restorer2'),
            shortcuts["Toggle Orientation"]: lambda: self.toggle_and_update('Orient', 'Orientation'),
            shortcuts["Toggle Strength"]: lambda: self.toggle_and_update('Strength', 'Strength'),
            shortcuts["Toggle Differencing"]: lambda: self.toggle_and_update('Diff', 'Differencing'),
            shortcuts["Toggle Occluder"]: lambda: self.toggle_and_update('Occluder', 'Occluder'),
            shortcuts["Toggle Face Parser"]: lambda: self.toggle_and_update('FaceParser', 'Face Parser'),
            shortcuts["Toggle Text-Based Masking"]: lambda: self.toggle_and_update('CLIP', 'Text-Based Masking'),
            shortcuts["Toggle Color Adjustments"]: lambda: self.toggle_and_update('Color', 'Color Adjustments'),
            shortcuts["Toggle Face Adjustments"]: lambda: self.toggle_and_update('FaceAdj', 'Input Face Adjustments'),
            shortcuts["Clear VRAM"]: lambda: self.clear_mem(),
            shortcuts["Find Faces"]: lambda: self.on_click_find_faces_button(),
            shortcuts["Swap Faces"]: lambda: self.toggle_swapper(),
            shortcuts["Toggle Auto Swap"]: lambda: self.toggle_auto_swap(),
            shortcuts["Nudge Left 1 Frame"]: lambda:self.back_one_frame(),
            shortcuts["Nudge Right 1 Frame"]: lambda: self.forward_one_frame(),
            shortcuts["Show Mask"]: lambda: self.toggle_maskview(),
            shortcuts["Previous Media"]: lambda: self.select_previous_target_media(),
            shortcuts["Next Media"]: lambda: self.select_next_target_media(),
            shortcuts["Delete Media"]: lambda: self.on_click_delete_media_button(),
        }
        self.bind('<Key>', self.handle_key_press)
        self.bind("<Return>", lambda event: self.focus_set())


    @staticmethod
    def bind_scroll_events(widget, callback):
        widget.bind("<MouseWheel>",lambda event: callback(event, delta=-int(event.delta / 120))) # Windows
        widget.bind("<Button-4>", lambda event: callback(event, delta=-1)) # Unix
        widget.bind("<Button-5>", lambda event: callback(event, delta=1)) # Unix

    def handle_key_press(self, event):
        if isinstance(self.focus_get(), tk.Entry):
            return
        f_keys = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12']
        modifiers = [mod for mod, mask in [('shift', 0x0001), ('ctrl', 0x0004), ('alt', 0x20000)] if event.state & mask]
        key_combination = event.keysym if event.keysym in f_keys else '+'.join(filter(None, ['+'.join(modifiers), event.keysym.lower()]))
        action = self.key_actions.get(key_combination)
        action and action()

    def toggle_and_update(self, switch_name, parameter_name):
        self.widget[f"{switch_name}Switch"].set(not self.widget[f"{switch_name}Switch"].get())

    #endregion

        # self.bind("<Return>", lambda event: self.focus_set())

#####
    def create_gui(self):

        #region [#111111b4]

        # v_f_frame == self.layer['InputVideoFrame']

        self.configure(bg=style.bg)
        ctk.set_appearance_mode("dark")

        global tmp
        tmp = ctk.CTkFrame(self, border_width=0, fg_color=style.main, bg_color=style.bg)
        tmp.grid(row=1, column=0, sticky='NEWS', padx=0, pady=0)
        tmp.grid_forget()

        #endregion

        #region [#111111b4]

        def vidupdate():
            self.resize_image()

        #Hide/Unhide Inputs Panel
        def input_panel_checkbox():
            current_state = self.checkbox.get()
            if current_state:
                self.layer['InputVideoFrame'].grid(row=0, column=0, sticky='NEWS', padx=0, pady=(0,0))
                ks_frame.grid_forget()
                pv_frame_container.grid_forget()
                self.collapse_keyboardshortcuts.deselect()
                self.collapse_parametersvisibility.deselect()
            else:
                self.layer['InputVideoFrame'].grid_forget()
                v_f_frame.grid_forget()
                self.after(10, vidupdate)

        #Hide/Unhide Faces Panel
        def collapse_faces_panel():
            current_state = self.collapse_bottom.get()
            if current_state:
                ff_frame.grid(row=5, column=0, sticky='NEWS', padx=0, pady=(1,0))
                mf_frame.grid(row=6, column=0, sticky='NEWS', padx=0, pady=1)
                self.after(10, vidupdate)
            else:
                ff_frame.grid_forget()
                mf_frame.grid_forget()
                self.after(10, vidupdate)

        #Hide/Unhide Parameters Panel
        def collapse_params_panel():
            current_state = self.collapse_params.get()
            if current_state:
                self.layer['parameter_frame'].grid(row=0, column=2, sticky='NEWS', pady=0, padx=0)
                self.after(10, vidupdate)
            else:
                self.layer['parameter_frame'].grid_forget()
                self.after(10, vidupdate)

        #Keyboard Shortcuts
        def keyboard_shortcuts():
            current_state = self.collapse_keyboardshortcuts.get()
            if current_state:
                ks_frame.grid(row=0, column=0, sticky='NEWS', padx=0, pady=(0,0))
                self.after(10, vidupdate)
                self.layer['InputVideoFrame'].grid_forget()
                pv_frame_container.grid_forget()
                self.after(10, vidupdate)
                self.checkbox.deselect()
                self.collapse_parametersvisibility.deselect()
            else:
                ks_frame.grid_forget()
                pv_frame_container.grid_forget()
                v_f_frame.grid_forget()
                self.after(10, vidupdate)
                self.layer['InputVideoFrame'].grid(row=0, column=0, sticky='NEWS', padx=0, pady=(0,0))
                self.after(10, vidupdate)
                self.checkbox.select()

        #Parameters Visibility
        def parameters_visibility():
            current_state = self.collapse_parametersvisibility.get()
            if current_state:
                pv_frame_container.grid(row=0, column=0, sticky='NEWS', padx=0, pady=(0,0))
                self.after(10, vidupdate)
                self.layer['InputVideoFrame'].grid_forget()
                ks_frame.grid_forget()
                self.after(10, vidupdate)
                self.checkbox.deselect()
                self.collapse_keyboardshortcuts.deselect()
            else:
                pv_frame_container.grid_forget()
                ks_frame.grid_forget()
                v_f_frame.grid_forget()
                self.after(10, vidupdate)
                self.layer['InputVideoFrame'].grid(row=0, column=0, sticky='NEWS', padx=0, pady=(0,0))
                self.after(10, vidupdate)
                self.checkbox.select()
                self.collapse_keyboardshortcuts.deselect()

        #endregion

        # 1 x 3 Top level grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self.configure(style.frame_style_bg)

        # Top Frame
        top_frame = tk.Frame(self, style.canvas_frame_label_1)
        top_frame.grid(row=0, column=0, sticky='NEWS', padx=1, pady=1)
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=0)

        # Middle Frame
        middle_frame = tk.Frame(self, style.frame_style_bg)
        middle_frame.grid(row=1, column=0, sticky='NEWS', padx=0, pady=0)
        middle_frame.grid_rowconfigure(0, weight=1)
        # Videos and Faces
        middle_frame.grid_columnconfigure(0, weight=0)
        # Preview
        middle_frame.grid_columnconfigure(1, weight=1)
        # Parameters
        middle_frame.grid_columnconfigure(2, weight=0)
        # Scrollbar
        middle_frame.grid_columnconfigure(3, weight=0)

        #region [#131710b4]

        global v_f_frame
        v_f_frame = ctk.CTkFrame(middle_frame, height = 42, border_width=0, fg_color=style.main)
        v_f_frame.grid(row=0, column=0, sticky='NEWS', padx=0, pady=(0,0))

        y=0
        x=10
        global ks_frame
        ks_frame = ctk.CTkFrame(middle_frame, height = 42, width=250, border_width=0, fg_color=style.main, background_corner_colors=(style.main,style.main,style.main,style.main))
        ks_frame.grid(row=0, column=0, sticky='NEWS', padx=0, pady=(0,0))
        ks_frame.grid_forget()

        def load_shortcuts_from_json():
            try:
                with open("shortcuts.json", "r") as json_file:
                    return json.load(json_file)
            except FileNotFoundError:
                return {
                    "Timeline Beginning": "z",
                    "Nudge Left 30 Frames": "a",
                    "Nudge Right 30 Frames": "d",
                    "Record": "r",
                    "Play": "space",
                    "Save Image": "ctrl+s",
                    "Add Marker": "f",
                    "Delete Marker": "alt+f",
                    "Previous Marker": "q",
                    "Next Marker": "w",
                    "Toggle Restorer": "1",
                    "Toggle Restorer2": "h",
                    "Toggle Orientation": "2",
                    "Toggle Strength": "3",
                    "Toggle Differencing": "4",
                    "Toggle Occluder": "5",
                    "Toggle Face Parser": "6",
                    "Toggle Text-Based Masking": "7",
                    "Toggle Color Adjustments": "8",
                    "Toggle Face Adjustments": "9",
                    "Clear VRAM": "F1",
                    "Find Faces": "ctrl+f",
                    "Swap Faces": "s",
                    "Toggle Auto Swap": "ctrl+a",
                    "Nudge Left 1 Frame": "c",
                    "Nudge Right 1 Frame": "v",
                    "Show Mask": "x",
                    "Previous Media": "left",
                    "Next Media": "right",
                    "Delete Media": "delete",
                }
        shortcuts = load_shortcuts_from_json()

        def save_shortcuts_to_json(shortcuts):
            with open("shortcuts.json", "w") as json_file:
                json.dump(shortcuts, json_file)

        def update_key_actions():
            self.key_actions = {
                shortcuts["Timeline Beginning"]: lambda: self.preview_control('q'),
                shortcuts["Nudge Left 30 Frames"]: lambda: self.preview_control('a'),
                shortcuts["Record"]: lambda: self.toggle_rec_video(),
                shortcuts["Play"]: lambda: self.toggle_play_video(),
                shortcuts["Nudge Right 30 Frames"]: lambda: self.preview_control('d'),
                shortcuts["Save Image"]: lambda: self.save_image(),
                shortcuts["Add Marker"]: lambda: self.update_marker('add'),
                shortcuts["Delete Marker"]: lambda: self.update_marker('delete'),
                shortcuts["Previous Marker"]: lambda: self.update_marker('prev'),
                shortcuts["Next Marker"]: lambda: self.update_marker('next'),
                shortcuts["Toggle Restorer"]: lambda: self.toggle_and_update('Restorer', 'Restorer'),
                shortcuts["Toggle Orientation"]: lambda: self.toggle_and_update('Orient', 'Orientation'),
                shortcuts["Toggle Strength"]: lambda: self.toggle_and_update('Strength', 'Strength'),
                shortcuts["Toggle Differencing"]: lambda: self.toggle_and_update('Diff', 'Differencing'),
                shortcuts["Toggle Occluder"]: lambda: self.toggle_and_update('Occluder', 'Occluder'),
                shortcuts["Toggle Face Parser"]: lambda: self.toggle_and_update('FaceParser', 'Face Parser'),
                shortcuts["Toggle Text-Based Masking"]: lambda: self.toggle_and_update('CLIP', 'Text-Based Masking'),
                shortcuts["Toggle Color Adjustments"]: lambda: self.toggle_and_update('Color', 'Color Adjustments'),
                shortcuts["Toggle Face Adjustments"]: lambda: self.toggle_and_update('FaceAdj', 'Input Face Adjustments'),
                shortcuts["Clear VRAM"]: lambda: self.clear_mem(),
                shortcuts["Find Faces"]: lambda: self.on_click_find_faces_button(),
                shortcuts["Swap Faces"]: lambda: self.toggle_swapper(),
                shortcuts["Toggle Auto Swap"]: lambda: self.toggle_auto_swap(),
                shortcuts["Nudge Left 1 Frame"]: lambda:self.back_one_frame(),
                shortcuts["Nudge Right 1 Frame"]: lambda: self.forward_one_frame(),
                shortcuts["Show Mask"]: lambda: self.toggle_maskview(),
                shortcuts["Previous Media"]: lambda: self.select_previous_target_media(),
                shortcuts["Next Media"]: lambda: self.select_next_target_media(),
                shortcuts["Delete Media"]: lambda: self.on_click_delete_media_button(),
            }

        # Load shortcuts from JSON
        shortcuts = load_shortcuts_from_json()

        # Update text variables with loaded shortcuts
        text_vars = {}
        for shortcut_name, default_value in shortcuts.items():
            text_vars[shortcut_name] = tk.StringVar(value=default_value)

        # Create save_shortcuts function with parameters
        def save_shortcuts():
            # Update the text variables with the current values from the entry widgets
            for shortcut_name, text_var in text_vars.items():
                shortcuts[shortcut_name] = text_var.get()

            # Save the current shortcuts to JSON
            save_shortcuts_to_json(shortcuts)
            update_key_actions()

        # Create save button with lambda function
        save_ks_button = ctk.CTkButton(ks_frame, text="Save Shortcuts", command=save_shortcuts, width=150, height=15, corner_radius=3, fg_color=style.main2, hover_color=style.main3)
        save_ks_button.place(x=40, y=20)

        # Create labels and entry widgets for each shortcut
        y = 60
        x = 10
        for shortcut_name, default_value in shortcuts.items():
            ctk.CTkLabel(ks_frame, text=shortcut_name).place(x=x, y=y)
            ctk.CTkEntry(ks_frame, textvariable=text_vars[shortcut_name], width=50, height=15, border_width=0).place(x=180, y=y)
            y += 20

        # Parameters Visibility Frame Container
        pv_frame_container = tk.Frame(middle_frame, style.frame_style_bg)
        pv_frame_container.grid(row=0, column=0, sticky='NEWS', padx=0, pady=0)
        pv_frame_container.grid_rowconfigure(0, weight=0)
        pv_frame_container.grid_rowconfigure(1, weight=0)
        pv_frame_container.grid_rowconfigure(2, weight=1)

        # Create empty row
        empty_row = ctk.CTkLabel(pv_frame_container, text="", fg_color=style.main2, height=15)
        empty_row.grid(row=0, column=0, sticky='NS', padx=0, pady=0)

        # Creare CTkTabview all'interno di 'pv_frame_container'
        tabview_main_visibility = ctk.CTkTabview(pv_frame_container,
                                      width=350,
                                      height=100,
                                      corner_radius=6,
                                      border_width=1,
                                      fg_color=style.main,
                                      border_color=style.main3,
                                      segmented_button_selected_hover_color='#b1b1b2',
                                      segmented_button_unselected_hover_color=style.main,
                                      segmented_button_selected_color='#7562ee',
                                      segmented_button_unselected_color=style.main,
                                      text_color='#F1E5AC',
                                      text_color_disabled=style.main2)

        # Posizionamento del CTkTabview all'interno del frame con il grid
        tabview_main_visibility.grid(row=2, column=0, sticky='nsew')

        # Aggiungi Tabs al CTkTabview
        tab_face_swapper_visibility = tabview_main_visibility.add("Face Swapper")
        tab_face_editor_visibility = tabview_main_visibility.add("Face Editor")

        global pv_frame, pv_frame2
        pv_frame = GE.CTkScrollableFrame(tab_face_swapper_visibility, allow_drag_and_drop=True, allowed_widget_type=GE.ParamSwitch, border_width=0, fg_color=style.main, background_corner_colors=(style.main,style.main,style.main,style.main))
        pv_frame.grid(row=0, column=0, sticky='nsew', padx=0, pady=(0, 0))

        # Configura il layout per il CTkScrollableFrame affinché si espanda
        tab_face_swapper_visibility.grid_rowconfigure(0, weight=1)
        tab_face_swapper_visibility.grid_columnconfigure(0, weight=1)

        pv_frame2 = GE.CTkScrollableFrame(tab_face_editor_visibility, allow_drag_and_drop=True, allowed_widget_type=GE.ParamSwitch, border_width=0, fg_color=style.main, background_corner_colors=(style.main,style.main,style.main,style.main))
        pv_frame2.grid(row=0, column=0, sticky='nsew', padx=0, pady=(0, 0))

        tab_face_editor_visibility.grid_rowconfigure(0, weight=1)
        tab_face_editor_visibility.grid_columnconfigure(0, weight=1)

        def load_params_visibility_from_json(task='startup', initial_dir="."):
            try:
                if task == 'startup':
                    with open("startup_parameters_visibility.json", "r") as json_file:
                        config_data = json.load(json_file)
                        file_name = json_file.name
                else:
                    with filedialog.askopenfile(mode='r', initialdir=initial_dir, filetypes=[("JSON files", "*.json"), ("All files", "*.*")]) as json_file:
                        config_data = json.load(json_file)
                        file_name = json_file.name

                # Verifica il tipo di configurazione
                if config_data.get("config_type") != "parameters_visibility":
                    print(f"Error: {file_name} has an invalid configuration type!")
                    return None, None

                # Restituisci i parametri di configurazione
                return config_data.get("parameters", {}), config_data.get("parameters_face_editor", {})

            except FileNotFoundError:
                return {}, {}
            except json.JSONDecodeError:
                print(f"Error decoding JSON file: {file_name}")
                return None, None

        def save_params_visibility_to_json(params_visibility, params_face_editor_visibility, initial_dir=".", default_filename="startup_parameters_visibility.json"):
            # Aggiungi il tipo di configurazione e la versione
            config_data = {
                "config_type": "parameters_visibility",
                "version": "1.0",
                "parameters": params_visibility,
                "parameters_faceeditor": params_face_editor_visibility
            }

            save_file = filedialog.asksaveasfile(
                mode='w',
                initialdir=initial_dir,
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=default_filename  # Nome file predefinito
            )
            if save_file:
                with save_file:
                    json.dump(config_data, save_file, indent=4)

        # get Parameters Visibility from frame
        def get_params_visibility_from_frame(param_type='all'):
            params_visibility = {}
            params_face_editor_visibility = {}

            if param_type == "all" or param_type == "parameters":
                max_row = pv_frame.scrollable_frame.grid_size()[1]  # Ottieni il numero massimo di righe
                for row in range(max_row):
                    widgets_in_row = pv_frame.scrollable_frame.grid_slaves(row=row)
                    for widget in widgets_in_row:
                        # Controlla se il widget è un frame che contiene un ParamSwitch
                        if hasattr(widget, 'draggable_object_instance'):
                            #print(f"ParamSwitch nella riga {row}: {widget.draggable_object_instance.name}, Tipo: {type(widget.draggable_object_instance).__name__}, Valore: { widget.draggable_object_instance.get()}")
                            params_visibility[widget.draggable_object_instance.name] = widget.draggable_object_instance.get()

            if param_type == "all" or param_type == "parameters_face_editor":
                max_row = pv_frame2.scrollable_frame.grid_size()[1]  # Ottieni il numero massimo di righe
                for row in range(max_row):
                    widgets_in_row = pv_frame2.scrollable_frame.grid_slaves(row=row)
                    for widget in widgets_in_row:
                        # Controlla se il widget è un frame che contiene un ParamSwitch
                        if hasattr(widget, 'draggable_object_instance'):
                            #print(f"ParamSwitch nella riga {row}: {widget.draggable_object_instance.name}, Tipo: {type(widget.draggable_object_instance).__name__}, Valore: { widget.draggable_object_instance.get()}")
                            params_face_editor_visibility[widget.draggable_object_instance.name] = widget.draggable_object_instance.get()

            return params_visibility, params_face_editor_visibility

        # Create save parameters visibility function
        def save_params_visibility():
            params_visibility, params_face_editor_visibility = get_params_visibility_from_frame(param_type='all')
            # Save the current list to JSON
            save_params_visibility_to_json(params_visibility, params_face_editor_visibility)

        def remove_param_switch_widgets(param_type='all'):
            if param_type == "all" or param_type == "parameters":
                # Ottieni il numero massimo di righe nel frame
                max_row = pv_frame.scrollable_frame.grid_size()[1]

                for row in range(max_row):
                    # Ottieni tutti i widget nella riga corrente
                    widgets_in_row = pv_frame.scrollable_frame.grid_slaves(row=row)
                    for widget in widgets_in_row:
                        # Controlla se il widget ha l'attributo 'draggable_object_instance'
                        if hasattr(widget, 'draggable_object_instance'):
                            # Distrugge il widget se ha l'attributo 'draggable_object_instance'
                            widget.destroy()

            if param_type == "all" or param_type == "parameters_face_editor":
                # Ottieni il numero massimo di righe nel frame
                max_row = pv_frame2.scrollable_frame.grid_size()[1]

                for row in range(max_row):
                    # Ottieni tutti i widget nella riga corrente
                    widgets_in_row = pv_frame2.scrollable_frame.grid_slaves(row=row)
                    for widget in widgets_in_row:
                        # Controlla se il widget ha l'attributo 'draggable_object_instance'
                        if hasattr(widget, 'draggable_object_instance'):
                            # Distrugge il widget se ha l'attributo 'draggable_object_instance'
                            widget.destroy()

        def load_params_visibility_configuration():
            json_conf, json_conf2 = load_params_visibility_from_json(task='manual', initial_dir=".")
            if json_conf:
                remove_param_switch_widgets(param_type='parameters')

                for widget_name, widget_instance in self.default_params_visibility.items():
                    if widget_name not in json_conf:
                        json_conf[widget_name] = True

                apply_params_visibility_configuration(json_conf, None, param_type='parameters', reload=True)

            if json_conf2:
                remove_param_switch_widgets(param_type='parameters_face_editor')

                for widget_name, widget_instance in self.default_params_face_editor_visibility.items():
                    if widget_name not in json_conf2:
                        json_conf2[widget_name] = True

                apply_params_visibility_configuration(None, json_conf2, param_type='parameters_face_editor', reload=True)

        def default_params_visibility_configuration():
            remove_param_switch_widgets(param_type='all')
            apply_params_visibility_configuration(self.default_params_visibility, self.default_params_face_editor_visibility, param_type='all', reload=True)

        def apply_params_visibility_configuration(params_visibility=None, params_face_editor_visibility=None, param_type='all', reload=False):
            if param_type == 'all' or param_type == 'parameters':
                if params_visibility == None:
                    params_visibility, _ = get_params_visibility_from_frame(param_type='parameters')

                # Apply Parameters Visibility Configuration
                padx=1
                pady=0
                pv_row = 0
                row = 1
                column = 0
                for widget_name, widget_value in params_visibility.items():
                    if widget_name in self.widget:
                        pv_row += 1
                        row += 1

                        # Create a ParamSwitch in the scrollable frame
                        if reload:
                            GE.ParamSwitch(pv_frame.scrollable_frame, widget_name, self.widget[widget_name].display_text, 3, self.update_param_visibility, widget_value, 398, 20, pv_row, 0, padx, pady, allow_drag_and_drop=True)

                        # Check if the widget has a 'frame' attribute, so can be reordered
                        if hasattr(self.widget[widget_name], 'frame'):
                            self.widget[widget_name].frame.grid(row=row, column=column, padx=padx, pady=pady)

                        # Apply visibility setting
                        if not widget_value:
                            self.widget[widget_name].hide()  # Ensure hide method correctly removes or hides the widget
                        elif widget_value:
                            self.widget[widget_name].unhide()  # Ensure unhide method correctly add or unhides the widget

            if param_type == 'all' or param_type == 'parameters_face_editor':
                if params_face_editor_visibility == None:
                    _, params_face_editor_visibility = get_params_visibility_from_frame(param_type='parameters_face_editor')

                # Apply Parameters Visibility Configuration
                padx=1
                pady=0
                pv_row = 0
                row = 1
                column = 0
                for widget_name, widget_value in params_face_editor_visibility.items():
                    if widget_name in self.widget:
                        pv_row += 1
                        row += 1

                        # Create a ParamSwitch in the scrollable frame
                        if reload:
                            GE.ParamSwitch(pv_frame2.scrollable_frame, widget_name, self.widget[widget_name].display_text, 3, self.update_param_visibility, widget_value, 398, 20, pv_row, 0, padx, pady, allow_drag_and_drop=True)

                        # Check if the widget has a 'frame' attribute, so can be reordered
                        if hasattr(self.widget[widget_name], 'frame'):
                            self.widget[widget_name].frame.grid(row=row, column=column, padx=padx, pady=pady)

                        # Apply visibility setting
                        if not widget_value:
                            self.widget[widget_name].hide()  # Ensure hide method correctly removes or hides the widget
                        elif widget_value:
                            self.widget[widget_name].unhide()  # Ensure unhide method correctly add or unhides the widget

            # resize parameters scrollbar
            self.static_widget['parameters_scrollbar'].resize_scrollbar(None)

        # Crea una nuova Frame per contenere i pulsanti
        button_frame = tk.Frame(pv_frame_container, style.frame_style_bg)
        button_frame.grid(row=1, column=0, sticky='EW', padx=0, pady=0)

        # Configura le colonne del button_frame
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        button_frame.grid_columnconfigure(3, weight=1)

        # Crea e posiziona i pulsanti all'interno della button_frame
        save_pv_button = ctk.CTkButton(button_frame, text="Save", command=save_params_visibility, width=80, height=15, corner_radius=3, fg_color=style.main, hover_color=style.main3, text_color="#FFFFE0", anchor='center')
        save_pv_button.grid(row=0, column=0, padx=0, pady=0)

        apply_pv_button = ctk.CTkButton(button_frame, text="Apply", command=lambda: apply_params_visibility_configuration(params_visibility=None, params_face_editor_visibility=None, param_type='all', reload=False), width=80, height=15, corner_radius=3, fg_color=style.main, hover_color=style.main3, text_color="#FFFFE0", anchor='center')
        apply_pv_button.grid(row=0, column=1, padx=0, pady=0)

        load_pv_button = ctk.CTkButton(button_frame, text="Load", command=load_params_visibility_configuration, width=80, height=15, corner_radius=3, fg_color=style.main, hover_color=style.main3, text_color="#FFFFE0", anchor='center')
        load_pv_button.grid(row=0, column=2, padx=0, pady=0)

        default_pv_button = ctk.CTkButton(button_frame, text="Default", command=default_params_visibility_configuration, width=80, height=15, corner_radius=3, fg_color=style.main, hover_color=style.main3, text_color="#FFFFE0", anchor='center')
        default_pv_button.grid(row=0, column=3, padx=0, pady=0)

        pv_frame_container.grid_forget()
        #endregion

        # Bottom Frame
        bottom_frame = tk.Frame( self, style.canvas_frame_label_1)
        bottom_frame.grid(row=2, column=0, sticky='NEWS', padx=1, pady=1)
        bottom_frame.grid_columnconfigure(0, minsize=100)
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_columnconfigure(2, minsize=100)

####### Top Frame
      # Left
        # Label
        self.layer['topleft'] = tk.Frame(top_frame, style.canvas_frame_label_1, height = 42)
        self.layer['topleft'].grid(row=0, column=0, sticky='NEWS', pady=0)

        # Buttons
        self.widget['StartButton'] = GE.Button(self.layer['topleft'], 'StartRope', 1, self.load_all, None, 'control', 10, 9, width=200)
        self.widget['OutputFolderButton'] = GE.Button(self.layer['topleft'], 'OutputFolder', 1, self.select_save_video_path, None, 'control', x=240, y=1, width=190)
        self.output_videos_text = GE.Text(self.layer['topleft'], '', 1, 240, 20, 190, 20)

      # Right
        self.layer['topright'] = tk.Frame(top_frame, style.canvas_frame_label_1, height=42, width=413)
        self.layer['topright'].grid(row=0, column=1, sticky='NEWS', pady=0)
        self.control['ClearVramButton'] = GE.Button(self.layer['topright'], 'ClearVramButton', 1, self.clear_mem, None, 'control', x=5, y=9, width=85, height=20)
        self.static_widget['vram_indicator'] = GE.VRAM_Indicator(self.layer['topright'], 1, 300, 20, 100, 11)

        #region [#111111b4]

        ##Button - Hide/Unhide Faces Panel
        self.checkbox = ctk.CTkCheckBox(self.layer['topleft'], text="Input Panel", text_color='#B0B0B0', command=input_panel_checkbox, onvalue=True, offvalue=False, checkbox_width=18, checkbox_height=18, border_width=0, hover_color='#303030', fg_color=style.main)
        self.checkbox.place(x=500, y=10)
        self.checkbox.select()
        #Button - Hide/Unhide Inputs Panel
        self.collapse_bottom = ctk.CTkCheckBox(self.layer['topleft'], text="Faces Panel",text_color='#B0B0B0', command=collapse_faces_panel, onvalue=True, offvalue=False, checkbox_width=18,checkbox_height=18,border_width=0,hover_color='#303030',fg_color=style.main)
        self.collapse_bottom.place(x=600, y=10)
        self.collapse_bottom.select()
        #Button - Hide/Unhide Params Panel
        self.collapse_params = ctk.CTkCheckBox(self.layer['topleft'], text="Parameters Panel",text_color='#B0B0B0', command=collapse_params_panel, onvalue=True, offvalue=False, checkbox_width=18,checkbox_height=18,border_width=0,hover_color='#303030',fg_color=style.main)
        self.collapse_params.place(x=705, y=10)
        self.collapse_params.select()
        #Button - Hide/Unhide Keyboard Shortcuts Panel
        self.collapse_keyboardshortcuts = ctk.CTkCheckBox(self.layer['topleft'], text="Keyboard Shortcuts",text_color='#B0B0B0', command=keyboard_shortcuts, onvalue=True, offvalue=False, checkbox_width=18,checkbox_height=18,border_width=0,hover_color='#303030',fg_color=style.main)
        self.collapse_keyboardshortcuts.place(x=840, y=10)
        #Button - Hide/Unhide Parameters Visibility Panel
        self.collapse_parametersvisibility = ctk.CTkCheckBox(self.layer['topleft'], text="Parameters Visibility",text_color='#B0B0B0', command=parameters_visibility, onvalue=True, offvalue=False, checkbox_width=18,checkbox_height=18,border_width=0,hover_color='#303030',fg_color=style.main)
        self.collapse_parametersvisibility.place(x=985, y=10)
        #endregion

####### Middle Frame

    ### Videos and Faces
        self.layer['InputVideoFrame'] = tk.Frame(middle_frame, style.canvas_frame_label_3)
        self.layer['InputVideoFrame'].grid(row=0, column=0, sticky='NEWS', padx=1, pady=0)
        # Buttons
        self.layer['InputVideoFrame'].grid_rowconfigure(0, weight=0)
        # Input Media Canvas
        self.layer['InputVideoFrame'].grid_rowconfigure(1, weight=1)

        # Input Videos
        self.layer['InputVideoFrame'].grid_columnconfigure(0, weight=0)
        # Scrollbar
        self.layer['InputVideoFrame'].grid_columnconfigure(1, weight=0)
        # Input Faces Canvas
        self.layer['InputVideoFrame'].grid_columnconfigure(0, weight=0)
        # Scrollbar
        self.layer['InputVideoFrame'].grid_columnconfigure(1, weight=0)

      # Input Videos
        # Button Frame
        frame = tk.Frame(self.layer['InputVideoFrame'], style.canvas_frame_label_2, height = 42)
        frame.grid(row=0, column=0, columnspan = 2, sticky='NEWS', padx=0, pady=0)

        # Buttons
        self.widget['VideoFolderButton'] = GE.Button(frame, 'LoadTVideos', 2, self.select_video_path, None, 'control', 10, 1, width=195)
        self.input_videos_text = GE.Text(frame, '', 2, 10, 20, 190, 20)

        # Meta frame
        target_media_meta_frame = tk.Frame(self.layer['InputVideoFrame'], style.canvas_frame_label_3)
        target_media_meta_frame.grid(row=1, column=1, sticky='NEWS', padx=0, pady=0)
        target_media_meta_frame.grid_rowconfigure(0, weight=0) # Search
        target_media_meta_frame.grid_rowconfigure(1, weight=1) # Canvas
        target_media_meta_frame.grid_columnconfigure(0, weight=1)  # Make column 0 expand

        def on_change_target_media_search_text(mode, name, use_markers):

            new_text = self.widget['TargetMediaSearchBarTextEntry'].get()
            self.filter_target_media(new_text)

        # Search Bar
        self.widget['TargetMediaSearchBarTextEntry'] = GE.Text_Entry_Search(
            target_media_meta_frame, 'TargetMediaSearchBarTextEntry', 'Search', 3, on_change_target_media_search_text, 'control', row=0, column=0, padx=4, pady=0)

        # Input Videos Frame
        self.layer['TargetMediaFrame'] = tk.Canvas(target_media_meta_frame, style.canvas_frame_label_3)
        self.layer['TargetMediaFrame'].grid(row=1, column=0, sticky='NEWS', padx=0, pady=0)
        self.layer['TargetMediaFrame'].grid_rowconfigure(0, weight=0)
        self.layer['TargetMediaFrame'].grid_rowconfigure(1, weight=1)

        # Scroll Canvas 
        self.target_media_canvas = tk.Canvas(self.layer['TargetMediaFrame'], style.canvas_frame_label_3, width=195)
        self.target_media_canvas.grid(row=1, column=0, sticky='NEWS', padx=10, pady=0)
        
        self.bind_scroll_events(self.target_media_canvas, self.target_videos_mouse_wheel)

        self.target_media_canvas.create_text(8, 20, anchor='w', fill='grey25', font=("Arial italic", 20), text=" Input Videos")

        scroll_canvas = tk.Canvas(self.layer['TargetMediaFrame'], style.canvas_frame_label_3, bd=0)
        scroll_canvas.grid(row=1, column=1, sticky='NEWS', padx=0, pady=0)
        scroll_canvas.grid_rowconfigure(0, weight=1)
        scroll_canvas.grid_columnconfigure(0, weight=1)  
        scroll_canvas.grid_columnconfigure(1, weight=0)

        self.static_widget['input_videos_scrollbar'] = GE.Scrollbar_y(scroll_canvas, self.target_media_canvas)

        # Hijack the mouse motion binding
        scroll_canvas.bind("<B1-Motion>", self.on_input_videos_scrollbar_mouse_motion)

      # Input Faces
        # Button Frame
        frame = tk.Frame(self.layer['InputVideoFrame'], style.canvas_frame_label_2, height = 42)
        frame.grid(row=0, column=2, columnspan = 2, sticky='NEWS', padx=0, pady=0)

        # Buttons
        self.widget['FacesFolderButton'] = GE.Button(frame, 'LoadSFaces', 2, self.select_faces_path, None, 'control', 10, 1, width=195)
        self.input_faces_text = GE.Text(frame, '', 2, 10, 20, 190, 20)

        # Meta frame
        source_face_meta_frame = tk.Frame(self.layer['InputVideoFrame'], style.canvas_frame_label_3)
        source_face_meta_frame.grid(row=1, column=2, sticky='NEWS', padx=0, pady=0)
        source_face_meta_frame.grid_rowconfigure(0, weight=0) # Search
        source_face_meta_frame.grid_rowconfigure(1, weight=1) # Canvas
        source_face_meta_frame.grid_columnconfigure(0, weight=1)  # Make column 0 expand

        def on_change_source_faces_search_text(mode, name, use_markers):

            new_text = self.widget['FacesSearchBarTextEntry'].get()
            self.filter_source_faces(new_text)

        # Search Bar
        self.widget['FacesSearchBarTextEntry'] = GE.Text_Entry_Search(
            source_face_meta_frame, 'FacesSearchBarTextEntry', 'Search', 3, on_change_source_faces_search_text, 'control', row=0, column=0, padx=4, pady=0)
       
        # Source Faces Frame
        self.layer['SourceFacesFrame'] = tk.Frame(source_face_meta_frame, style.canvas_frame_label_3)
        self.layer['SourceFacesFrame'].grid(row=1, column=0, sticky='NEWS', padx=0, pady=0)
        self.layer['SourceFacesFrame'].grid_rowconfigure(0, weight=0)
        self.layer['SourceFacesFrame'].grid_rowconfigure(1, weight=1)

        # Scroll Canvas
        self.source_faces_canvas = tk.Canvas(self.layer['SourceFacesFrame'], style.canvas_frame_label_3, width=195)
        self.source_faces_canvas.grid(row=1, column=0, sticky='NEWS', padx=10, pady=0)

        self.bind_scroll_events(self.source_faces_canvas, self.source_faces_mouse_wheel)

        self.source_faces_canvas.create_text(8, 20, anchor='w', fill='grey25', font=("Arial italic", 20), text=" Input Faces")

        scroll_canvas = tk.Canvas(self.layer['SourceFacesFrame'], style.canvas_frame_label_3, bd=0)
        scroll_canvas.grid(row=1, column=1, sticky='NEWS', padx=0, pady=0)
        scroll_canvas.grid_rowconfigure(0, weight=1)
        scroll_canvas.grid_columnconfigure(0, weight=1)
        scroll_canvas.grid_columnconfigure(1, weight=0)

        self.static_widget['input_faces_scrollbar'] = GE.Scrollbar_y(scroll_canvas, self.source_faces_canvas)

        # GE.Separator_y(scroll_canvas, 14, 0)
        # GE.Separator_y(self.layer['InputVideoFrame'], 229, 0)
        GE.Separator_x(self.layer['InputVideoFrame'], 0, 41)

    ### Preview
        self.layer['preview_column'] = tk.Frame(middle_frame, style.canvas_bg)
        self.layer['preview_column'].grid(row=0, column=1, sticky='NEWS', pady=0)
        self.layer['preview_column'].grid_columnconfigure(0, weight=1)
        # Preview Data
        self.layer['preview_column'].grid_rowconfigure(0, weight=0)
        # Preview Window
        self.layer['preview_column'].grid_rowconfigure(1, weight=1)
        # Timeline
        self.layer['preview_column'].grid_rowconfigure(2, weight=0)
        # MArkers
        self.layer['preview_column'].grid_rowconfigure(3, weight=0)
        # Controls
        self.layer['preview_column'].grid_rowconfigure(4, weight=0)
        # Found Faces
        self.layer['preview_column'].grid_rowconfigure(5, weight=0)
        # Merged Faces
        self.layer['preview_column'].grid_rowconfigure(6, weight=0)

      # Preview Data
        preview_data = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_2, height = 24)
        preview_data.grid(row=0, column=0, sticky='NEWS', pady=0)
        preview_data.grid_columnconfigure(0, weight=1)
        preview_data.grid_columnconfigure(1, weight=1)
        preview_data.grid_columnconfigure(2, weight=1)
        # preview_data.grid_columnconfigure(3, weight=1)
        preview_data.grid_rowconfigure(0, weight=0)

        frame = tk.Frame(preview_data, style.canvas_frame_label_2, height = 24, width=100)
        frame.grid(row=0, column=0)
        self.widget['AudioButton'] = GE.Button(frame, 'Audio', 2, self.toggle_audio, None, 'control', x=0, y=0, width=100)

        frame = tk.Frame(preview_data, style.canvas_frame_label_2, height = 24, width=100)
        frame.grid(row=0, column=1)
        self.widget['MaskViewButton'] = GE.Button(frame, 'MaskView', 2, self.toggle_maskview, None, 'control', x=0, y=0, width=100)

        frame = tk.Frame(preview_data, style.canvas_frame_label_2, height = 24, width=100)
        frame.grid(row=0, column=2)
        self.widget['CompareViewButton'] = GE.Button(frame, 'CompareView', 2, self.toggle_compareview, None, 'control', x=0, y=0, width=100)

        frame = tk.Frame(preview_data, style.canvas_frame_label_2, height = 24, width=200)
        frame.grid(row=0, column=3)
        self.widget['PreviewModeTextSel'] = GE.TextSelection(frame, 'PreviewModeTextSel', '', 2, self.set_view, True, 'control', width=200, height=20, row=0, column=0, padx=1, pady=0, text_percent=1)

      # Preview Window
        self.video = tk.Label(self.layer['preview_column'], bg='black')
        self.video.grid(row=1, column=0, sticky='NEWS', padx=0, pady=0)
        self.bind_scroll_events(self.video, self.iterate_through_merged_embeddings)
        self.video.bind("<ButtonRelease-1>", lambda event: self.toggle_play_video())

    # Videos
      # Timeline
        # Slider
        self.layer['slider_frame'] = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_2, height=50)
        self.layer['slider_frame'].grid(row=2, column=0, sticky='NEWS', pady=0)
        self.video_slider = GE.Timeline(self.layer['slider_frame'], self.widget, self.temp_toggle_swapper, self.temp_toggle_enhancer, self.temp_toggle_faces_editor, self.add_action)

        # Markers
        self.layer['markers_canvas'] = tk.Canvas(self.layer['preview_column'], style.canvas_frame_label_2, height = 20)
        self.layer['markers_canvas'].grid(row=3, column=0, sticky='NEWS')
        self.layer['markers_canvas'].bind('<Configure>', lambda e:self.update_marker(e.width))

        # self.create_ui_button('ToggleStop', marker_frame, 140, 2, width=36, height=36)

      # Controls
        self.layer['preview_frame'] = tk.Frame(self.layer['preview_column'], style.canvas_bg, height = 40)
        self.layer['preview_frame'].grid(row=4, column=0, sticky='NEWS')
        self.layer['preview_frame'].grid_columnconfigure(0, weight=0)
        self.layer['preview_frame'].grid_columnconfigure(1, weight=1)
        self.layer['preview_frame'].grid_columnconfigure(2, weight=0)
        self.layer['preview_frame'].grid_rowconfigure(0, weight=0)
        self.layer['preview_frame'].grid_rowconfigure(1, weight=0)

        # Left Side
        self.layer['play_controls_left'] = tk.Frame(self.layer['preview_frame'], style.canvas_frame_label_2, height=30, width=200 )
        self.layer['play_controls_left'].grid(row=0, column=0, sticky='NEWS', pady=0)

        # Center
        cente_frame = tk.Frame(self.layer['preview_frame'], style.canvas_frame_label_2, height=30, )
        cente_frame.grid(row=0, column=1, sticky='NEWS', pady=0)
        cente_frame.grid_columnconfigure(0, weight=0)
        cente_frame.grid_rowconfigure(0, weight=0)

        play_control_frame = tk.Frame(cente_frame, style.canvas_frame_label_2, height=30, width=300  )
        play_control_frame.place(anchor="c", relx=.5, rely=.5)

        column = 0
        col_delta = 50
        self.widget['TLBegButton'] = GE.Button(play_control_frame, 'TLBeginning', 2, self.preview_control, 'q', 'control', x=column , y=2, width=20)
        column += col_delta
        self.widget['TLLeftButton'] = GE.Button(play_control_frame, 'TLLeft', 2, self.preview_control, 'a', 'control', x=column , y=2, width=20)
        column += col_delta
        self.widget['TLRecButton'] = GE.Button(play_control_frame, 'Record', 2, self.toggle_rec_video, None, 'control', x=column , y=2, width=20)
        column += col_delta
        self.widget['TLPlayButton'] = GE.Button(play_control_frame, 'Play', 2, self.toggle_play_video, None, 'control', x=column , y=2, width=20)
        column += col_delta
        self.widget['TLRightButton'] = GE.Button(play_control_frame, 'TLRight', 2, self.preview_control, 'd', 'control', x=column , y=2, width=20)

        # Right Side
        right_playframe = tk.Frame(self.layer['preview_frame'], style.canvas_frame_label_2, height=30, width=120)
        right_playframe.grid(row=0, column=2, sticky='NEWS', pady=0)
        self.widget['AddMarkerButton'] = GE.Button(right_playframe, 'AddMarkerButton', 2, self.update_marker, 'add', 'control', x=0, y=5, width=20)
        self.widget['DelMarkerButton'] = GE.Button(right_playframe, 'DelMarkerButton', 2, self.update_marker, 'delete', 'control', x=25, y=5, width=20)
        self.widget['PrevMarkerButton'] = GE.Button(right_playframe, 'PrevMarkerButton', 2, self.update_marker, 'prev', 'control', x=50, y=5, width=20)
        self.widget['NextMarkerButton'] = GE.Button(right_playframe, 'NextMarkerButton', 2, self.update_marker, 'next', 'control', x=75, y=5, width=20)
        # self.widget['StopMarkerButton'] = GE.Button(right_playframe, 'StopMarkerButton', 2, self.update_marker, 'stop', 'control', x=100, y=5, width=20)
        self.widget['SaveMarkerButton'] = GE.Button(right_playframe, 'SaveMarkerButton', 2, self.save_markers_json, None, 'control', x=95, y=5, width=20)

    # Image controls
        self.layer['image_controls'] = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_2, height=33)
        self.layer['image_controls'].grid(row=5, column=0, sticky='NEWS', pady=0)
        self.layer['image_controls'].grid_columnconfigure(0, weight=0) 
        self.layer['image_controls'].grid_columnconfigure(1, weight=0)
        self.layer['image_controls'].grid_columnconfigure(10, weight=1)

        # Save Image Frame (aligned left)
        self.layer['image_controls_save_image_frame'] = tk.Frame(self.layer['image_controls'], style.canvas_frame_label_2, width=130, height=33)
        self.layer['image_controls_save_image_frame'].grid(row=0, column=0, sticky='W', pady=0)
        self.widget['SaveImageButton'] = GE.Button(self.layer['image_controls_save_image_frame'], 'SaveImageButton', 2, self.save_image, None, 'control', x=0, y=0, width=100, height=33)

        # Auto Swap Frame (aligned left)
        self.layer['image_controls_auto_swap_frame'] = tk.Frame(self.layer['image_controls'], style.canvas_frame_label_2, height=33)
        self.layer['image_controls_auto_swap_frame'].grid(row=0, column=1, sticky='W', pady=0)
        self.widget['AutoSwapTextSel'] = GE.TextSelection(self.layer['image_controls_auto_swap_frame'], 'AutoSwapTextSel', 'Auto Swap', 3, self.update_data, 'control', 'control', 220, 33, 0, 0, 0, 0, 0.72)
        
        self.layer['image_controls_after_playback_frame'] = tk.Frame(self.layer['image_controls'], style.canvas_frame_label_2, height=33)
        self.layer['image_controls_after_playback_frame'].grid(row=0, column=2, sticky='W', pady=0)
        self.widget['AfterPlaybackTextSel'] = GE.TextSelection(self.layer['image_controls_after_playback_frame'], 'AfterPlaybackTextSel', 'After Playback', 3, self.update_data, 'control', 'control', 320, 33, 0, 0, 0, 0, 0.72)

        # Delete Media Frame (aligned right)
        self.layer['image_controls_delete_image_frame'] = tk.Frame(self.layer['image_controls'], style.canvas_frame_label_2, width=130, height=33)
        self.layer['image_controls_delete_image_frame'].grid(row=0, column=10, sticky='E', pady=0)
        self.widget['DeleteMediaButton'] = GE.Button(self.layer['image_controls_delete_image_frame'], 'DeleteMediaButton', 2, self.on_click_delete_media_button, None, 'control', x=0, y=0, width=100, height=33)

    # FaceLab
        self.layer['FaceLab_controls'] = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_2, height=80)
        self.layer['FaceLab_controls'].grid(row=2, column=0, rowspan=2, sticky='NEWS', pady=0)

        self.layer['FaceLab_controls'].grid_forget()

      # Found Faces
        ff_frame = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_1)
        ff_frame.grid(row=6, column=0, sticky='NEWS', pady=1)
        ff_frame.grid_columnconfigure(0, weight=0)
        ff_frame.grid_columnconfigure(1, weight=1)
        ff_frame.grid_columnconfigure(2, weight=1)
        ff_frame.grid_rowconfigure(0, weight=0)

        # Buttons
        button_frame = tk.Frame(ff_frame, style.canvas_frame_label_2, height = 99, width = 224)
        button_frame.grid( row = 0, column = 0, )

        self.widget['FindFacesButton'] = GE.Button(button_frame, 'FindFaces', 2, self.on_click_find_faces_button, None, 'control', x=112, y=0, width=112, height=33)
        self.widget['ClearFacesButton'] = GE.Button(button_frame, 'ClearFaces', 2, self.on_click_clear_target_faces_button, None, 'control', x=112, y=33, width=112, height=33)
        self.widget['SwapFacesButton'] = GE.Button(button_frame, 'SwapFaces', 2, self.toggle_swapper, None, 'control', x=0, y=0, width=112, height=33)
        self.widget['EditFacesButton'] = GE.Button(button_frame, 'EditFaces', 2, self.toggle_faces_editor, None, 'control', x=0, y=33, width=112, height=33)
        self.widget['EnhanceFrameButton'] = GE.Button(button_frame, 'EnhanceFrame', 2, self.toggle_enhancer, None, 'control', x=0, y=66, width=112, height=33)

        # Scroll Canvas
        self.found_faces_canvas = tk.Canvas(ff_frame, style.canvas_frame_label_3, height = 100 )
        self.found_faces_canvas.grid( row = 0, column = 1, sticky='NEWS')
        self.bind_scroll_events(self.found_faces_canvas, self.target_faces_mouse_wheel)
        self.found_faces_canvas.create_text(8, 45, anchor='w', fill='grey25', font=("Arial italic", 20), text=" Found Faces")

        self.selected_source_faces_canvas = tk.Canvas(ff_frame, style.canvas_frame_label_3, height = 100 )
        self.selected_source_faces_canvas.grid( row = 0, column = 2, sticky='NEWS')
        self.bind_scroll_events(self.selected_source_faces_canvas, self.selected_source_faces_mouse_wheel)
        self.selected_source_faces_canvas.create_text(8, 45, anchor='w', fill='grey25', font=("Arial italic", 20), text=" Currently Selected Source Faces")

        self.static_widget['23'] = GE.Separator_y(ff_frame, 111, 0)

      # Merged Faces
        mf_frame = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_1)
        mf_frame.grid(row=7, column=0, sticky='NEWS', pady=0)
        mf_frame.grid_columnconfigure(0, minsize=10)
        mf_frame.grid_columnconfigure(1, weight=1)
        mf_frame.grid_rowconfigure(0, weight=0)

        # Buttons
        button_frame = tk.Frame(mf_frame, style.canvas_frame_label_2, height = 100, width = 112)
        button_frame.grid( row = 0, column = 0, )

        self.widget['DelEmbedButton'] = GE.Button(button_frame, 'DelEmbed', 2, self.delete_merged_embedding, None, 'control', x=0, y=30, width=112, height=33)

        # Merged Embeddings Text
        self.merged_embedding_name = tk.StringVar()
        self.merged_embeddings_text = tk.Entry(button_frame, style.entry_2, textvariable=self.merged_embedding_name)
        self.merged_embeddings_text.place(x=8, y=8, width = 96, height=20)
        self.merged_embeddings_text.bind("<Return>", lambda event: self.save_selected_source_faces(self.merged_embedding_name))
        self.me_name = self.nametowidget(self.merged_embeddings_text)

        # Scroll Canvas
        self.merged_faces_canvas = tk.Canvas(mf_frame, style.canvas_frame_label_3, height = 100)
        self.merged_faces_canvas.grid( row = 0, column = 1, sticky='NEWS')
        self.merged_faces_canvas.grid_rowconfigure(0, weight=1)
        self.bind_scroll_events(self.merged_faces_canvas, lambda event, delta: self.merged_faces_canvas.xview_scroll(delta, "units"))
        self.merged_faces_canvas.create_text(8, 45, anchor='w', fill='grey25', font=("Arial italic", 20), text=" Merged Faces")
        self.static_widget['24'] = GE.Separator_y(mf_frame, 111, 0)

    ### Parameters
        width=398

        self.layer['parameter_frame'] = tk.Frame(middle_frame, style.canvas_frame_label_3, bd=0, width=width)
        self.layer['parameter_frame'].grid(row=0, column=2, sticky='NEWS', pady=0, padx=1)

        self.layer['parameter_frame'].grid_rowconfigure(0, weight=0)
        self.layer['parameter_frame'].grid_rowconfigure(1, weight=1)
        self.layer['parameter_frame'].grid_rowconfigure(2, weight=0)
        self.layer['parameter_frame'].grid_columnconfigure(0, weight=0)
        self.layer['parameter_frame'].grid_columnconfigure(1, weight=0)

        parameters_control_frame = tk.Frame(self.layer['parameter_frame'], style.canvas_frame_label_2, bd=0, width=width, height = 42)
        parameters_control_frame.grid(row=0, column=0, columnspan=2, sticky='NEWS', pady=0, padx=0)
        parameters_control_frame.grid_columnconfigure(0, weight=1)
        parameters_control_frame.grid_columnconfigure(1, weight=1)
        parameters_control_frame.grid_columnconfigure(2, weight=1)
        parameters_control_frame.grid_rowconfigure(0, weight=0)

        frame = tk.Frame(parameters_control_frame, style.canvas_frame_label_2, height = 42, width=100)
        frame.grid(row=0, column=0)
        self.widget['SaveParamsButton'] = GE.Button(frame, 'SaveParamsButton', 2, self.parameter_io, 'save', 'control', x=0 , y=8, width=100)

        frame = tk.Frame(parameters_control_frame, style.canvas_frame_label_2, height = 42, width=100)
        frame.grid(row=0, column=1)
        self.widget['LoadParamsButton'] = GE.Button(frame, 'LoadParamsButton', 2, self.parameter_io, 'load', 'control', x=0 , y=8, width=100)

        frame = tk.Frame(parameters_control_frame, style.canvas_frame_label_2, height = 42, width=100)
        frame.grid(row=0, column=2)
        self.widget['DefaultParamsButton'] = GE.Button(frame, 'DefaultParamsButton', 2, self.parameter_io, 'default', 'control', x=0 , y=8, width=100)

        self.layer['parameters_canvas'] = tk.Canvas(self.layer['parameter_frame'], style.canvas_frame_label_3, bd=0, width=width)
        self.parameters_canvas = self.layer['parameters_canvas']
        self.parameters_canvas.grid(row=1, column=0, sticky='NEWS', pady=0, padx=0)

        # Face Editor
        tabview_main = ctk.CTkTabview(self.parameters_canvas, width=398, height=2050, corner_radius=6, border_width=1,
                                      fg_color=style.main, border_color=style.main3,
                                      segmented_button_selected_hover_color='#b1b1b2',
                                      segmented_button_unselected_hover_color=style.main,
                                      segmented_button_selected_color='#7562ee',
                                      segmented_button_unselected_color=style.main,
                                      text_color='#F1E5AC',
                                      text_color_disabled=style.main2)

        tabview_main.pack(fill='both', expand=True)  # Utilizza pack per gestire il layout all'interno del Canvas

        # Inserisci il CTkTabview nel Canvas usando create_window
        self.parameters_canvas.create_window(0, 0, window=tabview_main, anchor='nw')

        # Aggiungi Tabs al CTkTabview
        tab_face_swapper = tabview_main.add("Face Swapper  ")
        tab_live_portrait = tabview_main.add("Face Editor  ")

        self.layer['parameters_frame'] = tk.Frame(tab_face_swapper, style.canvas_frame_label_3, bd=0, width=width, height=2050)
        self.layer['parameters_frame'].grid(row=0, column=0, sticky='NEWS', pady=0, padx=0)

        self.layer['parameters_face_editor_frame'] = tk.Frame(tab_live_portrait, style.canvas_frame_label_3, bd=0, width=width, height=2050)
        self.layer['parameters_face_editor_frame'].grid(row=0, column=0, sticky='NEWS', pady=0, padx=0)

        self.layer['parameter_scroll_canvas'] = tk.Canvas(self.layer['parameter_frame'], style.canvas_frame_label_3, bd=0, )
        parameter_scroll_canvas = self.layer['parameter_scroll_canvas']
        parameter_scroll_canvas.grid(row=1, column=1, sticky='NEWS', pady=0)
        parameter_scroll_canvas.grid_rowconfigure(0, weight=1)
        parameter_scroll_canvas.grid_columnconfigure(0, weight=1)

        self.static_widget['parameters_scrollbar'] = GE.Scrollbar_y(parameter_scroll_canvas, self.parameters_canvas)

        self.bind_scroll_events(parameter_scroll_canvas, self.parameters_mouse_wheel)

        self.static_widget['30'] = GE.Separator_x(parameters_control_frame, 0, 41)

        ### Layout ###
        row = 1
        column = 0
        padx=1
        pady=0

        # Providers Priority
        row = row + 1
        self.widget['ProvidersPriorityTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'ProvidersPriorityTextSel', 'Providers Priority', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72)
        row = row + 1
        self.widget['ThreadsSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ThreadsSlider', 'Threads', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)

        # Face Swapper Model
        row = row + 1
        self.widget['FaceSwapperModelTextSel'] = GE.TextSelectionComboBox(self.layer['parameters_frame'], 'FaceSwapperModelTextSel', 'Face Swapper Model', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72, 150)
        row = row + 1
        self.widget['SwapperTypeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'SwapperTypeTextSel', 'Swapper Resolution', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72)

        #Webcam Backend
        row = row + 1
        self.widget['WebCamBackendSel'] = GE.TextSelectionComboBox(self.layer['parameters_frame'], 'WebCamBackendSel', 'Webcam Backend', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72, 150)

        #Webcam Max Resolution
        row = row + 1
        self.widget['WebCamMaxResolSel'] = GE.TextSelectionComboBox(self.layer['parameters_frame'], 'WebCamMaxResolSel', 'Webcam Resolution', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72, 150)

        #Webcam Max FPS
        row = row + 1
        self.widget['WebCamMaxFPSSel'] = GE.TextSelection(self.layer['parameters_frame'], 'WebCamMaxFPSSel', 'Webcam FPS', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72)

        #Webcam Max Count
        row = row + 1
        self.widget['WebCamMaxNoSlider'] = GE.Slider2(self.layer['parameters_frame'], 'WebCamMaxNoSlider', 'Max Webcams', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)

        #Virtual Cam
        row = row + 1
        self.widget['VirtualCameraSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'VirtualCameraSwitch', 'Send Frames to Virtual Camera', 3, self.toggle_virtualcam, 'control', 398, 20, row, 0, padx, pady)

        # Resolution override
        row = row + 1
        self.widget['ResolutionOverrideSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'ResolutionOverrideSwitch', 'Override Resolution', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['HeightOverrideSlider'] = GE.Slider2(self.layer['parameters_frame'], 'HeightOverrideSlider', 'Height', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)

        # Frame Skip
        row = row + 1
        self.widget['FrameSkipModeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'FrameSkipModeTextSel', 'Frame Skip Mode', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72)
        row = row + 1
        self.widget['FramesToSkip'] = GE.Slider2(self.layer['parameters_frame'], 'FramesToSkip', 'Frames to skip', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)

        # Restore
        row = row + 1
        self.widget['RestorerSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'RestorerSwitch', 'Restorer', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['RestorerTypeTextSel'] = GE.TextSelectionComboBox(self.layer['parameters_frame'], 'RestorerTypeTextSel', 'Restorer Type', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72, 150)
        row = row + 1
        self.widget['RestorerDetTypeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'RestorerDetTypeTextSel', 'Detection Alignment', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72)
        row = row + 1
        self.widget['VQFRFidelitySlider'] = GE.Slider2(self.layer['parameters_frame'], 'VQFRFidelitySlider', 'Fidelity Ratio', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)
        row = row + 1
        self.widget['RestorerSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestorerSlider', 'Restorer Blend', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)

        # Restore2
        row = row + 1
        self.widget['Restorer2Switch'] = GE.Switch2(self.layer['parameters_frame'], 'Restorer2Switch', '2. Restorer', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['Restorer2TypeTextSel'] = GE.TextSelectionComboBox(self.layer['parameters_frame'], 'Restorer2TypeTextSel', '2. Restorer Type', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72, 150)
        row = row + 1
        self.widget['Restorer2DetTypeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'Restorer2DetTypeTextSel', '2. Detection Alignment', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72)
        row = row + 1
        self.widget['Restorer2Slider'] = GE.Slider2(self.layer['parameters_frame'], 'Restorer2Slider', '2. Restorer Blend', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)

        # Frame Restorer
        row = row + 1
        self.widget['FrameEnhancerTypeTextSel'] = GE.TextSelectionComboBox(self.layer['parameters_frame'], 'FrameEnhancerTypeTextSel', 'Enhancer Type', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.72, 150)
        row = row + 1
        self.widget['EnhancerSlider'] = GE.Slider2(self.layer['parameters_frame'], 'EnhancerSlider', 'Enhancer Blend', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)

        # Orientation
        row = row + 1
        self.widget['OrientSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'OrientSwitch', 'Orientation', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['OrientSlider'] = GE.Slider2(self.layer['parameters_frame'], 'OrientSlider', 'Angle', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Strength
        row = row + 1
        self.widget['StrengthSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'StrengthSwitch', 'Strength', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['StrengthSlider'] = GE.Slider2(self.layer['parameters_frame'], 'StrengthSlider', 'Amount', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Border
        row = row + 1
        self.widget['BorderTopSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BorderTopSlider', 'Top Border Distance', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['BorderLeftSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BorderLeftSlider', 'Left Border Distance', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['BorderRightSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BorderRightSlider', 'Right Border Distance', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['BorderBottomSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BorderBottomSlider', 'Bottom Border Distance', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['BorderBlurSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BorderBlurSlider', 'Border Blend', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Diff
        row = row + 1
        self.widget['DiffSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'DiffSwitch', 'Differencing', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['DiffSlider'] = GE.Slider2(self.layer['parameters_frame'], 'DiffSlider', 'Amount', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['DiffingBlurSlider'] = GE.Slider2(self.layer['parameters_frame'], 'DiffingBlurSlider', 'Diff Blend Amount', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Occluder
        row = row + 1
        self.widget['OccluderSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'OccluderSwitch', 'Occluder', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['OccluderSlider'] = GE.Slider2(self.layer['parameters_frame'], 'OccluderSlider', 'Size', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Mask XSeg
        row = row + 1
        self.widget['DFLXSegSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'DFLXSegSwitch', 'DFL XSeg', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['DFLXSegSlider'] = GE.Slider2(self.layer['parameters_frame'], 'DFLXSegSlider', 'Size', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['OccluderBlurSlider'] = GE.Slider2(self.layer['parameters_frame'], 'OccluderBlurSlider', 'Occluder/XSeg Blur', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # FinalBlurSlider
        row = row + 1
        self.widget['FinalBlurSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'FinalBlurSwitch', 'Final Blur Switch', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['FinalBlurSlider'] = GE.Slider2(self.layer['parameters_frame'], 'FinalBlurSlider', 'Final Face Blur', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Overall MaskBlendSlider
        row = row + 1
        self.widget['BlendSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BlendSlider', 'Overall Mask Blend', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # DFL RCT Color Transfer
        row = row + 1
        self.widget['DFLRCTColorSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'DFLRCTColorSwitch', 'DFL RCT Color Transfer', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady+5)

        # DFL Load only one Model
        row = row + 1
        self.widget['DFLLoadOnlyOneSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'DFLLoadOnlyOneSwitch', 'DFL Keep Only Single Model in Memory', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady+5)

        # DFL AMP Morph Factor
        row = row + 1
        self.widget['DFLAmpMorphSlider'] = GE.Slider2(self.layer['parameters_frame'], 'DFLAmpMorphSlider', 'DFL AMP Morph Factor', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady+5, 0.62)

        # CLIP
        row = row + 1
        self.widget['CLIPSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'CLIPSwitch', 'Text-Based Masking', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['CLIPTextEntry'] = GE.Text_Entry(self.layer['parameters_frame'], 'CLIPTextEntry', 'Text', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['CLIPSlider'] = GE.Slider2(self.layer['parameters_frame'], 'CLIPSlider', 'Amount', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        #Restore Eyes
        row = row + 1
        self.widget['RestoreEyesSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'RestoreEyesSwitch', 'Restore Eyes', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['RestoreEyesSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreEyesSlider', 'Eyes Blend', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['Eyes_Mouth_BlurSlider'] = GE.Slider2(self.layer['parameters_frame'], 'Eyes_Mouth_BlurSlider', 'Eyes&Mouth Mask Blur', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreEyesFeatherSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreEyesFeatherSlider', 'Eyes Feather Blend', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreEyesSizeSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreEyesSizeSlider', 'Eyes Size Factor', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreEyesRadiusFactorXSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreEyesRadiusFactorXSlider', 'Eyes Radius Factor: X', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreEyesRadiusFactorYSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreEyesRadiusFactorYSlider', 'Eyes Radius Factor: Y', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreEyesSpacingOffsetSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreEyesSpacingOffsetSlider', 'Eyes Spacing Offset', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreEyesXoffsetSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreEyesXoffsetSlider', 'Eyes Offset: X', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreEyesYoffsetSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreEyesYoffsetSlider', 'Eyes Offset: Y', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        #Restore Mouth
        row = row + 1
        self.widget['RestoreMouthSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'RestoreMouthSwitch', 'Restore Mouth', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['RestoreMouthSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreMouthSlider', 'Mouth Blend', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreMouthFeatherSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreMouthFeatherSlider', 'Mouth Feather Blend', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreMouthSizeSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreMouthSizeSlider', 'Mouth Size', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreMouthRadiusFactorXSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreMouthRadiusFactorXSlider', 'Mouth Radius Factor: X', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreMouthRadiusFactorYSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreMouthRadiusFactorYSlider', 'Mouth Radius Factor: Y', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreMouthXoffsetSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreMouthXoffsetSlider', 'Mouth Offset: X', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['RestoreMouthYoffsetSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestoreMouthYoffsetSlider', 'Mouth Offset: Y', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # FaceParser - Face
        row = row + 1
        self.widget['FaceParserSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'FaceParserSwitch', 'Face Parser', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)

        #Face Background & Blurs & Neck
        row = row + 1
        self.widget['BGParserBlurSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BGParserBlurSlider', 'Background Blur', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['ParserBlurSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ParserBlurSlider', 'FaceParser Blur', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['FaceParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceParserSlider', 'Background', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['NeckParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'NeckParserSlider', 'Neck', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)

        #Eyebrows
        row = row + 1
        self.widget['LeftEyeBrowParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'LeftEyeBrowParserSlider', 'Left Eyebrow', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['RightEyeBrowParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RightEyeBrowParserSlider', 'Right Eyebrow', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)

        #Eyes
        row = row + 1
        self.widget['LeftEyeParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'LeftEyeParserSlider', 'Left Eye', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['RightEyeParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RightEyeParserSlider', 'Right Eye', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)

        #Nose and Mouth
        row = row + 1
        self.widget['NoseParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'NoseParserSlider', 'Nose', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62,40)
        row = row + 1
        self.widget['MouthParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'MouthParserSlider', 'Mouth', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62,40)

        #Lips
        row = row + 1
        self.widget['UpperLipParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'UpperLipParserSlider', 'Upper Lip', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['LowerLipParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'LowerLipParserSlider', 'Lower Lip', 3, self.update_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)

        # Autocolor
        row = row + 1
        self.widget['AutoColorSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'AutoColorSwitch', 'AutoColor', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['AutoColorTypeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'AutoColorTypeTextSel', 'Transfer Type', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['AutoColorSlider'] = GE.Slider2(self.layer['parameters_frame'], 'AutoColorSlider', 'AutoColor Blend', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Jpeg Compression
        row = row + 1
        self.widget['JpegCompressionSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'JpegCompressionSwitch', 'Jpeg Compression', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['JpegCompressionSlider'] = GE.Slider2(self.layer['parameters_frame'], 'JpegCompressionSlider', 'Jpeg Value', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Color Adjustments
        row = row + 1
        self.widget['ColorSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'ColorSwitch', 'Color Adjustments', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['ColorRedSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorRedSlider', 'Red', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['ColorGreenSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorGreenSlider', 'Green', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['ColorBlueSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorBlueSlider', 'Blue', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['ColorBrightSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorBrightSlider', 'Brightness', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['ColorContrastSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorContrastSlider', 'Contrast', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['ColorSaturationSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorSaturationSlider', 'Saturation', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['ColorSharpnessSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorSharpnessSlider', 'Sharpness', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['ColorHueSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorHueSlider', 'Hue', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['ColorGammaSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorGammaSlider', 'Gamma', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['NoiseSlider'] = GE.Slider2(self.layer['parameters_frame'], 'NoiseSlider', 'Noise', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # KPS Adjustment and scaling
        row = row + 1
        self.widget['FaceAdjSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'FaceAdjSwitch', 'Input Face Adjustments', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['KPSXSlider'] = GE.Slider2(self.layer['parameters_frame'], 'KPSXSlider', 'KPS - X', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['KPSYSlider'] = GE.Slider2(self.layer['parameters_frame'], 'KPSYSlider', 'KPS - Y', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['KPSScaleSlider'] = GE.Slider2(self.layer['parameters_frame'], 'KPSScaleSlider', 'KPS - Scale', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['FaceScaleSlider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceScaleSlider', 'Face Scale', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Face Likeness
        row = row + 1
        self.widget['FaceLikenessSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'FaceLikenessSwitch', 'Face Likeness', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['FaceLikenessFactorSlider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceLikenessFactorSlider', 'Factor', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Threshhold
        row = row + 1
        self.widget['ThresholdSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ThresholdSlider', 'Similarity Threshhold', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Max faces
        row = row + 1
        self.widget['MaxFacesSlider'] = GE.Slider2(self.layer['parameters_frame'], 'MaxFacesSlider', 'Max Faces', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Cats and Dogs
        row = row + 1
        self.widget['DetectTypeTextSel'] = GE.TextSelectionComboBox(self.layer['parameters_frame'], 'DetectTypeTextSel', 'Detection Type', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.62, 150)
        row = row + 1
        self.widget['DetectScoreSlider'] = GE.Slider2(self.layer['parameters_frame'], 'DetectScoreSlider', 'Detect Score', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Similarity
        row = row + 1
        self.widget['SimilarityTypeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'SimilarityTypeTextSel', 'Similarity Type', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.62)

        # Auto Rotation
        row = row + 1
        self.widget['AutoRotationSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'AutoRotationSwitch', 'Auto Rotation', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)

        # Landmarks Detection
        row = row + 1
        self.widget['LandmarksDetectionAdjSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'LandmarksDetectionAdjSwitch', 'Landmarks Detection Adjustments', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['LandmarksAlignModeFromPointsSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'LandmarksAlignModeFromPointsSwitch', 'From Points', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 30, 40)
        row = row + 1
        self.widget['LandmarksDetectTypeTextSel'] = GE.TextSelectionComboBox(self.layer['parameters_frame'], 'LandmarksDetectTypeTextSel', 'Landmarks Detection Type', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.62, 150)
        row = row + 1
        self.widget['LandmarksDetectScoreSlider'] = GE.Slider2(self.layer['parameters_frame'], 'LandmarksDetectScoreSlider', 'Landmarks Detect Score', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['ShowLandmarksSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'ShowLandmarksSwitch', 'Show Landmarks', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)

        # Face Landmarks Position
        row = row + 1
        self.widget['LandmarksPositionAdjSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'LandmarksPositionAdjSwitch', '5 Landmarks Position Adjustments', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['FaceIDSlider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceIDSlider', 'Face ID: ', 3, self.update_face_landmarks_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['EyeLeftXSlider'] = GE.Slider2(self.layer['parameters_frame'], 'EyeLeftXSlider', 'Left Eye:   X', 3, self.update_face_landmarks_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['EyeLeftYSlider'] = GE.Slider2(self.layer['parameters_frame'], 'EyeLeftYSlider', 'Left Eye:   Y', 3, self.update_face_landmarks_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['EyeRightXSlider'] = GE.Slider2(self.layer['parameters_frame'], 'EyeRightXSlider', 'Right Eye:   X', 3, self.update_face_landmarks_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['EyeRightYSlider'] = GE.Slider2(self.layer['parameters_frame'], 'EyeRightYSlider', 'Right Eye:   Y', 3, self.update_face_landmarks_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['NoseXSlider'] = GE.Slider2(self.layer['parameters_frame'], 'NoseXSlider', 'Nose:   X', 3, self.update_face_landmarks_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['NoseYSlider'] = GE.Slider2(self.layer['parameters_frame'], 'NoseYSlider', 'Nose:   Y', 3, self.update_face_landmarks_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['MouthLeftXSlider'] = GE.Slider2(self.layer['parameters_frame'], 'MouthLeftXSlider', 'Left Mouth:   X', 3, self.update_face_landmarks_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['MouthLeftYSlider'] = GE.Slider2(self.layer['parameters_frame'], 'MouthLeftYSlider', 'Left Mouth:   Y', 3, self.update_face_landmarks_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['MouthRightXSlider'] = GE.Slider2(self.layer['parameters_frame'], 'MouthRightXSlider', 'Right Mouth:   X', 3, self.update_face_landmarks_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)
        row = row + 1
        self.widget['MouthRightYSlider'] = GE.Slider2(self.layer['parameters_frame'], 'MouthRightYSlider', 'Right Mouth:   Y', 3, self.update_face_landmarks_data, 'parameter', 300, 20, row, 0, padx, pady, 0.62, 40)

        row = row + 1
        self.widget['RecordTypeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'RecordTypeTextSel', 'Record Type', 3, self.update_data, 'parameter', 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['VideoQualSlider'] = GE.Slider2(self.layer['parameters_frame'], 'VideoQualSlider', 'FFMPEG Quality', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['AudioSpeedSlider'] = GE.Slider2(self.layer['parameters_frame'], 'AudioSpeedSlider', 'Audio Playback Speed', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.62)
        row = row + 1
        self.widget['MergeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'MergeTextSel', 'Merge Math', 3, self.select_input_faces, 'merge', '', 398, 20, row, 0, padx, pady, 0.62)

        # Face Weights
        row = row + 1
        self.widget['ApplyFaceWeightsSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'ApplyFaceWeightsSwitch', 'Apply Face Weights', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady)
        row = row + 1
        self.widget['FaceWeights0Slider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceWeights0Slider', 'Face0 Default', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)
        row = row + 1
        self.widget['FaceWeights1Slider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceWeights1Slider', 'Face1 Default', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)
        row = row + 1
        self.widget['FaceWeights2Slider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceWeights2Slider', 'Face2 Default', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)
        row = row + 1
        self.widget['FaceWeights3Slider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceWeights3Slider', 'Face3 Default', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)
        row = row + 1
        self.widget['FaceWeights4Slider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceWeights4Slider', 'Face4 Default', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)
        row = row + 1
        self.widget['FaceWeights5Slider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceWeights5Slider', 'Face5 Default', 3, self.update_data, 'parameter', 398, 20, row, 0, padx, pady, 0.72)
    
        ### Face Editor ###
        row = 1
        column = 0
        padx=1
        pady=0

        # Providers Priority
        row = row + 1
        self.widget['FaceEditorTypeTextSel'] = GE.TextSelection(self.layer['parameters_face_editor_frame'], 'FaceEditorTypeTextSel', 'Face Editor Type', 3, self.update_face_editor_data, 'parameter_face_editor', 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60)
        row = row + 1
        self.widget['FaceEditorIDSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'FaceEditorIDSlider', 'Face Editor ID: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60)
        row = row + 1
        self.widget['CropScaleSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'CropScaleSlider', 'Crop Scale: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['EyesOpenRatioSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'EyesOpenRatioSlider', 'Eyes Close <--> Open Ratio: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['LipsOpenRatioSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'LipsOpenRatioSlider', 'Lips Close <--> Open Ratio: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['HeadPitchSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'HeadPitchSlider', 'Head Pitch: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['HeadYawSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'HeadYawSlider', 'Head Yaw: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['HeadRollSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'HeadRollSlider', 'Head Roll: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['XAxisMovementSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'XAxisMovementSlider', 'X-Axis Movement: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['YAxisMovementSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'YAxisMovementSlider', 'Y-Axis Movement: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['ZAxisMovementSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'ZAxisMovementSlider', 'Z-Axis Movement: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['MouthPoutingSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'MouthPoutingSlider', 'Mouth Pouting: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['MouthPursingSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'MouthPursingSlider', 'Mouth Pursing: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['MouthGrinSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'MouthGrinSlider', 'Mouth Grin: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['LipsCloseOpenSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'LipsCloseOpenSlider', 'Lips Close <--> Open Value: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['MouthSmileSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'MouthSmileSlider', 'Mouth Smile: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['EyeWinkSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'EyeWinkSlider', 'Eye Wink: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['EyeBrowsDirectionSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'EyeBrowsDirectionSlider', 'EyeBrows Direction : ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['EyeGazeHorizontalSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'EyeGazeHorizontalSlider', 'EyeGaze Horizontal: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)
        row = row + 1
        self.widget['EyeGazeVerticalSlider'] = GE.Slider2(self.layer['parameters_face_editor_frame'], 'EyeGazeVerticalSlider', 'EyeGaze Vertical: ', 3, self.update_face_editor_data, 'parameter_face_editor', 398, 20, row, 0, padx, pady, 0.60, 40)

        # Load saved Parameters Visibility Configuration from Json file
        params_visibility, params_face_editor_visibility = load_params_visibility_from_json()
        if params_visibility == None:
            params_visibility = {}

        # Check for all widgets not in saved Parameters Visibility Configuration and add them if missing
        for widget_name, widget_instance in self.widget.items():
            if widget_instance.parent == self.layer['parameters_frame']:
                self.default_params_visibility[widget_name] = True
                if widget_name not in params_visibility:
                    params_visibility[widget_name] = True

        if params_face_editor_visibility == None:
            params_face_editor_visibility = {}

        # Check for all widgets not in saved Parameters Visibility Configuration and add them if missing
        for widget_name, widget_instance in self.widget.items():
            if widget_instance.parent == self.layer['parameters_face_editor_frame']:
                self.default_params_face_editor_visibility[widget_name] = True
                if widget_name not in params_face_editor_visibility:
                    params_face_editor_visibility[widget_name] = True

        # Apply Parameters Visibility Configuration
        apply_params_visibility_configuration(params_visibility, params_face_editor_visibility, param_type='all', reload=True)

    ### Other
        self.layer['tooltip_frame'] = tk.Frame(self.layer['parameter_frame'], style.canvas_frame_label_3, height=80)
        self.layer['tooltip_frame'].grid(row=2, column=0, columnspan=2, sticky='NEWS', padx=0, pady=0)
        self.layer['tooltip_label'] = tk.Label(self.layer['tooltip_frame'], style.info_label, wraplength=width-10, image=self.blank, compound='left', height=80, width=width-10)
        self.layer['tooltip_label'].place(x=5, y=5)
        self.static_widget['22'] = GE.Separator_x(self.layer['tooltip_frame'], 0, 0)

 ######### FaceLab

        self.layer['facelab_canvas'] = tk.Canvas(self.layer['parameter_frame'], style.canvas_frame_label_3, bd=0, width=width)
        self.layer['facelab_canvas'].grid(row=1, column=0, sticky='NEWS', pady=0, padx=0)
        #
        self.layer['facelab_frame'] = tk.Frame(self.layer['facelab_canvas'], style.canvas_frame_label_3, bd=0, width=width, height=11000)
        self.layer['facelab_frame'].grid(row=0, column=0, sticky='NEWS', pady=0, padx=0)
        #
        self.layer['facelab_canvas'].create_window(0, 0, window=self.layer['facelab_frame'], anchor='nw')
        #
        self.layer['facelab_scroll_canvas'] = tk.Canvas(self.layer['parameter_frame'], style.canvas_frame_label_3, bd=0, )
        self.layer['facelab_scroll_canvas'].grid(row=1, column=1, sticky='NEWS', pady=0)
        self.layer['facelab_scroll_canvas'].grid_rowconfigure(0, weight=1)
        self.layer['facelab_scroll_canvas'].grid_columnconfigure(0, weight=1)

        self.static_widget['facelab_scrollbar'] =GE.Scrollbar_y(self.layer['facelab_scroll_canvas'] , self.layer['facelab_canvas'])

 ######### Options

        self.status_left_label = tk.Label(bottom_frame, style.donate_1, cursor="hand2", text=" Questions/Help/Discussions (Discord)")
        self.status_left_label.grid( row = 0, column = 0, sticky='NEWS')
        self.status_left_label.bind("<Button-1>", lambda e: self.callback("https://discord.gg/dzvpCUet"))

        self.status_label = tk.Label(bottom_frame, style.donate_1, text="Rope Next Github")
        self.status_label.grid( row = 0, column = 1, sticky='NEWS')
        self.status_label.bind("<Button-1>", lambda e: self.callback("https://github.com/Alucard24/Rope"))

        self.donate_label = tk.Label(bottom_frame, style.donate_1, text="Enjoy Rope? Please Support! (Paypal) ", anchor='e')
        self.donate_label.grid( row = 0, column = 2, sticky='NEWS')
        self.donate_label.bind("<Button-1>", lambda e: self.callback("https://www.paypal.com/donate/?business=XJX2E5ZTMZUSQ&no_recurring=0&item_name=Support+us+with+a+donation%21+Your+contribution+helps+us+continue+improving+and+providing+quality+content.+Thank+you%21&currency_code=EUR"))

        # Face Landmarks
        self.face_landmarks = FaceLandmarks(self.widget, self.parameters, self.add_action)
        self.add_action("face_landmarks", self.face_landmarks)

        # Face Editor
        self.face_editor = FaceEditor(self.widget, self.parameters_face_editor, self.add_action)
        self.add_action("face_editor", self.face_editor)

    # Face Landmarks
    def update_face_landmarks_data(self, mode, name, use_markers=False):
        # print(inspect.currentframe().f_back.f_code.co_name,)
        if mode=='parameter':
            frame_number = self.video_slider.get()
            face_id = self.widget['FaceIDSlider'].get()
            parameter_value = self.widget[name].get()

            landmarks = self.face_landmarks.get_landmarks(frame_number, face_id)
            if landmarks is None:
                landmarks = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
                self.face_landmarks.add_landmarks(frame_number, face_id, landmarks)

            match name:
                case "EyeLeftXSlider":
                    landmarks[0] = tuple((parameter_value, landmarks[0][1]))
                case "EyeLeftYSlider":
                    landmarks[0] = tuple((landmarks[0][0], parameter_value))
                case "EyeRightXSlider":
                    landmarks[1] = tuple((parameter_value, landmarks[1][1]))
                case "EyeRightYSlider":
                    landmarks[1] = tuple((landmarks[1][0], parameter_value))
                case "NoseXSlider":
                    landmarks[2] = tuple((parameter_value, landmarks[2][1]))
                case "NoseYSlider":
                    landmarks[2] = tuple((landmarks[2][0], parameter_value))
                case "MouthLeftXSlider":
                    landmarks[3] = tuple((parameter_value, landmarks[3][1]))
                case "MouthLeftYSlider":
                    landmarks[3] = tuple((landmarks[3][0], parameter_value))
                case "MouthRightXSlider":
                    landmarks[4] = tuple((parameter_value, landmarks[4][1]))
                case "MouthRightYSlider":
                    landmarks[4] = tuple((landmarks[4][0], parameter_value))

            self.add_action("face_landmarks", self.face_landmarks)

            self.face_landmarks.apply_changes_to_widget_and_parameters(frame_number, face_id)

            if use_markers:
                self.add_action('get_requested_video_frame', frame_number)
            else:
                self.add_action('get_requested_video_frame_without_markers', frame_number)

    # Face Editor
    def update_face_editor_data(self, mode, name, use_markers=False):
        if mode == 'parameter_face_editor':
            frame_number = self.video_slider.get()
            face_id = self.widget['FaceEditorIDSlider'].get()
            parameter_value = self.widget[name].get()

            parameters = self.face_editor.get_parameters(frame_number, face_id)
            if parameters is None:
                parameters = ['Human-Face', 2.50, 0.00, 0.00, 0, 0, 0, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0, 0.00, 0.00, 0.00, 0.00, 0.00]
                self.face_editor.add_parameters(frame_number, face_id, parameters)

            if name in self.face_editor.parameter_map:
                index = self.face_editor.parameter_map[name]
                parameters[index] = parameter_value

            self.add_action("face_editor", self.face_editor)
            self.face_editor.apply_changes_to_widget_and_parameters(frame_number, face_id)

            if use_markers:
                self.add_action('get_requested_video_frame', frame_number)
            else:
                self.add_action('get_requested_video_frame_without_markers', frame_number)

    # Update the parameters or controls dicts and get a new frame
    def update_data(self, mode, name, use_markers=False):
        # print(inspect.currentframe().f_back.f_code.co_name,)
        if mode=='parameter':
            self.parameters[name] = self.widget[name].get()
            self.add_action('parameters', self.parameters)
            #Similarity Type
            if name == 'SimilarityTypeTextSel' or name == 'FaceSwapperModelTextSel':
                if self.video_loaded or self.image_loaded:
                    for face in self.target_faces:
                        if face["ButtonState"]:
                            # Clear all of the assignments
                            face["SourceFaceAssignments"] = []
                    # Clear all faces
                    self.clear_target_faces()
                    # reload input faces
                    self.load_input_faces()
            elif name == "ProvidersPriorityTextSel":
                provider_value = self.models.switch_providers_priority(self.parameters[name])
                if provider_value != self.parameters[name]:
                    self.parameters[name] = provider_value
                    self.widget[name].set(provider_value, request_frame=False)
                else:
                    self.models.delete_models()
                    torch.cuda.empty_cache()

            elif name=='WebCamMaxResolSel' or name=='WebCamMaxFPSSel':
                # self.add_action(load_target_video()
                self.add_action('change_webcam_resolution_and_fps')
            elif name=='WebCamBackendSel':
                self.add_action('change_webcam_resolution_and_fps')
                self.populate_target_videos()
            elif name=='ThreadsSlider':
                self.models.set_number_of_threads(self.parameters[name])
            elif name=='ApplyFaceWeightsSwitch':
                self.select_input_faces("same", "")
            # Face Editor
            '''
            elif mode=='parameter_face_editor':
                self.parameters_face_editor[name] = self.widget[name].get()
                self.add_action('parameters_face_editor', self.parameters_face_editor)
            '''

        elif mode=='control':
            self.control[name] =  self.widget[name].get()
            self.add_action('control', self.control)

        if use_markers:
            self.add_action('get_requested_video_frame', self.video_slider.get())
        else:
            self.add_action('get_requested_video_frame_without_markers', self.video_slider.get())

    def update_param_visibility(self, name, visible):
        if name in self.widget:
            if visible:
                self.widget[name].unhide()
            else:
                self.widget[name].hide()

        # resize parameters scrollbar
        self.static_widget['parameters_scrollbar'].resize_scrollbar(None)

    def callback(self, url):
        webbrowser.open_new_tab(url)

    def target_faces_mouse_wheel(self, event, delta = 0):
        self.found_faces_canvas.xview_scroll(delta, "units")

    def selected_source_faces_mouse_wheel(self, event, delta = 0):
        self.selected_source_faces_canvas.xview_scroll(delta, "units")

    def source_faces_mouse_wheel(self, event, delta=0):
        self.source_faces_canvas.yview_scroll(delta, "units")

        # Center of visible canvas as a percentage of the entire canvas
        center = (self.source_faces_canvas.yview()[1]-self.source_faces_canvas.yview()[0])/2
        center = center+self.source_faces_canvas.yview()[0]
        self.static_widget['input_faces_scrollbar'].set(center)

    def target_videos_mouse_wheel(self, event, delta = 0):
        self.target_media_canvas.yview_scroll(delta, "units")

        # Center of visible canvas as a percentage of the entire canvas
        center = (self.target_media_canvas.yview()[1]-self.target_media_canvas.yview()[0])/2
        center = center+self.target_media_canvas.yview()[0]
        self.static_widget['input_videos_scrollbar'].set(center)

        self.render_thumbnails_for_drawn_target_media_buttons()

    def parameters_mouse_wheel(self, event, delta = 0):
        self.parameters_canvas.yview_scroll(delta, "units")

        # Center of visible canvas as a percentage of the entire canvas
        center = (self.parameters_canvas.yview()[1]-self.parameters_canvas.yview()[0])/2
        center = center+self.parameters_canvas.yview()[0]
        self.static_widget['parameters_scrollbar'].set(center)

    # focus_get()
    # def preview_control(self, event):
    #     # print(event.char, event.keysym, event.keycode)
    #     # print(type(event))
    #     if isinstance(event, str):
    #         event = event
    #     else:
    #         event = event.char

        # if self.focus_get() !=  self.widget['CLIPTextEntry'] and self.focus_get() != self.merged_embeddings_text:

        #     #asd
        #     if self.video_loaded:
        #         frame = self.video_slider.get()
        #         video_length = self.video_slider.get_length()
        #         if event == ' ':
        #             self.toggle_play_video()
        #         elif event == 'w':
        #             frame += 1
        #             if frame > video_length:
        #                 frame = video_length
        #             self.video_slider.set(frame)
        #             self.add_action("get_requested_video_frame", frame)
        #         elif event == 's':
        #             frame -= 1
        #             if frame < 0:
        #                 frame = 0
        #             self.video_slider.set(frame)
        #             self.add_action("get_requested_video_frame", frame)
        #         elif event == 'd':
        #             frame += 30
        #             if frame > video_length:
        #                 frame = video_length
        #             self.video_slider.set(frame)
        #             self.add_action("get_requested_video_frame", frame)
        #         elif event == 'a':
        #             frame -= 30
        #             if frame < 0:
        #                 frame = 0
        #             self.video_slider.set(frame)
        #             self.add_action("get_requested_video_frame", frame)
        #         elif event == 'q':
        #             frame = 0
        #             self.video_slider.set(frame)
        #             self.add_action("get_requested_video_frame", frame)

    def forward_one_frame(self):
        frame = self.video_slider.get()
        video_length = self.video_slider.get_length()
        frame += 1
        if frame > video_length:
            frame = video_length
        self.video_slider.set(frame)
        self.add_action("get_requested_video_frame", frame)

    def back_one_frame(self):
        frame = self.video_slider.get()
        frame -= 1
        if frame < 0:
            frame = 0
        self.video_slider.set(frame)
        self.add_action("get_requested_video_frame", frame)

    def preview_control(self, event):
        # print(event.char, event.keysym, event.keycode)
        # print(type(event))
        if isinstance(event, str):
            event = event
        else:
            event = event.char

        # if self.focus_get() != self.CLIP_name and self.focus_get() != self.me_name and self.parameters['ImgVidMode'] == 0:

        if self.widget['PreviewModeTextSel'].get()=='Video' and self.video_loaded:
            frame = self.video_slider.get()
            video_length = self.video_slider.get_length()
            if event == ' ':
                self.toggle_play_video()
            elif event == 'w':
                self.add_action("play_video", "stop")
                frame += 1
                if frame > video_length:
                    frame = video_length
                self.video_slider.set(frame)
                self.add_action("get_requested_video_frame", frame)
                # self.parameter_update_from_marker(frame)
            elif event == 's':
                self.add_action("play_video", "stop")
                frame -= 1
                if frame < 0:
                    frame = 0
                self.video_slider.set(frame)
                self.add_action("get_requested_video_frame", frame)
                # self.parameter_update_from_marker(frame)
            elif event == 'd':
                self.add_action("play_video", "stop")
                frame += 30
                if frame > video_length:
                    frame = video_length
                self.video_slider.set(frame)
                self.add_action("get_requested_video_frame", frame)
                # self.parameter_update_from_marker(frame)
            elif event == 'a':
                self.add_action("play_video", "stop")
                frame -= 30
                if frame < 0:
                    frame = 0
                self.video_slider.set(frame)
                self.add_action("get_requested_video_frame", frame)
                # self.parameter_update_from_marker(frame)
            elif event == 'q':
                self.add_action("play_video", "stop")
                frame = 0
                self.video_slider.set(frame)
                self.add_action("get_requested_video_frame", frame)
                # self.parameter_update_from_marker(frame)

# refactor - make sure files are closed

    def initialize_gui( self ):
        json_object = {}
        # check if data.json exists, if not then create it, else load it
        try:
            data_json_file = open("data.json", "r")
        except:
            with open("data.json", "w") as outfile:
                json.dump(self.json_dict, outfile)
        else:
            json_object = json.load(data_json_file)
            data_json_file.close()

        # Window position and size
        try:
            self.json_dict['dock_win_geom'] = json_object['dock_win_geom']
        except:
            self.json_dict['dock_win_geom'] = self.json_dict['dock_win_geom']

        # Initialize the window sizes and positions
        self.geometry('%dx%d+%d+%d' % (self.json_dict['dock_win_geom'][0], self.json_dict['dock_win_geom'][1] , self.json_dict['dock_win_geom'][2], self.json_dict['dock_win_geom'][3]))
        self.window_last_change = self.winfo_geometry()

        # self.bind('<Key>', lambda event: self.preview_control(event))
        # self.bind('<space>', lambda event: self.preview_control(event))

        self.resizable(width=True, height=True)

        # Build UI, update ui with default data
        self.create_gui()

        self.splash_image = cv2.cvtColor(cv2.imread('./rope/media/splash_next.png'), cv2.COLOR_BGR2RGB)
        self.video_image = self.splash_image
        self.resize_image()

        # Create parameters and controls and and selctively fill with UI data
        for key, value in self.widget.items():
            self.widget[key].add_info_frame(self.layer['tooltip_label'])
            if self.widget[key].get_data_type()=='parameter':
                self.parameters[key] = self.widget[key].get()

            elif self.widget[key].get_data_type()=='control':
                self.control[key] =  self.widget[key].get()

        # Create parameters_face_editor and selctively fill with UI data
        for key, value in self.widget.items():
            if self.widget[key].get_data_type()=='parameter_face_editor':
                self.parameters_face_editor[key] = self.widget[key].get()

        try:
            self.json_dict["source videos"] = json_object["source videos"]
        except KeyError:
            self.widget['VideoFolderButton'].error_button()
        else:
            if self.json_dict["source videos"] == None:
                self.widget['VideoFolderButton'].error_button()
            else:
                path = self.create_path_string(self.json_dict["source videos"], 28)
                self.input_videos_text.configure(text=path)

        try:
            self.json_dict["source faces"] = json_object["source faces"]
        except KeyError:
            self.widget['FacesFolderButton'].error_button()
        else:
            if self.json_dict["source faces"] == None:
                self.widget['FacesFolderButton'].error_button()
            else:
                path = self.create_path_string(self.json_dict["source faces"], 28)
                self.input_faces_text.configure(text=path)

        try:
            self.json_dict["saved videos"] = json_object["saved videos"]
        except KeyError:
            self.widget['OutputFolderButton'].error_button()
        else:
            if self.json_dict["saved videos"] == None:
                self.widget['OutputFolderButton'].error_button()
            else:
                path = self.create_path_string(self.json_dict["saved videos"], 28)
                self.output_videos_text.configure(text=path)
                self.add_action("saved_video_path", self.json_dict["saved videos"])

        # Check for a user parameters file and load if present
        try:
            parameters_json_file = open("startup_parameters.json", "r")
        except:
            pass
        else:
            temp = json.load(parameters_json_file)
            parameters_json_file.close()

            # Verifica il tipo di configurazione
            if temp.get("config_type") == "parameters":
                # Carica i parametri
                temp = temp.get("parameters", {})
                for key, value in self.parameters.items():
                    try:
                        # Do not load parameter that doesn't exist in widgets
                        if key in self.parameters:
                            self.parameters[key] = temp[key]
                            if key == "ProvidersPriorityTextSel":
                                provider_value = self.models.switch_providers_priority(temp[key])
                                if provider_value != temp[key]:
                                    self.parameters[key] = provider_value
                            elif key == "ThreadsSlider":
                                self.models.set_number_of_threads(value)
                    except KeyError:
                        pass

                  # Update the UI
                for key, value in self.parameters.items():
                    self.widget[key].set(value, request_frame=False)

                # Carica i parametri face editor
                temp = temp.get("parameters_face_editor", {})
                for key, value in self.parameters_face_editor.items():
                    try:
                        # Do not load parameter that doesn't exist in widgets
                        if key in self.parameters_face_editor:
                            self.parameters_face_editor[key] = temp[key]
                    except KeyError:
                        pass

                # Update the UI face editor
                for key, value in self.parameters_face_editor.items():
                    self.widget[key].set(value, request_frame=False)
            else:
                print("Error: startup_parameters.json has an invalid configuration type!")

        self.add_action('parameters', self.parameters)
        self.add_action('control', self.control)

        self.widget['StartButton'].error_button()
        self.set_view(False, '')

    def create_path_string(self, path, text_len):
        if len(path)>text_len:
            last_folder = os.path.basename(os.path.normpath(path))
            last_folder_len = len(last_folder)
            if last_folder_len>text_len:
                path = path[:3]+'...'+path[-last_folder_len+6:]
            else:
                path = path[:text_len-last_folder_len]+'.../'+path[-last_folder_len:]

        return path

    def load_all(self):
        if not self.json_dict["source videos"] or not self.json_dict["source faces"]:
            messagebox.showinfo('Set Faces folder',f'Please set faces and videos folders first!',)
            print("Please set faces and videos folders first!")
            return

        self.populate_target_videos()
        self.load_input_faces()
        self.widget['StartButton'].enable_button()

    def select_video_path(self):
        temp = self.json_dict["source videos"]
        self.json_dict["source videos"] = filedialog.askdirectory(title="Select Target Videos Folder", initialdir=temp)

        path = self.create_path_string(self.json_dict["source videos"], 28)
        self.input_videos_text.configure(text=path)

        with open("data.json", "w") as outfile:
            json.dump(self.json_dict, outfile)
            outfile.close()
        self.widget['VideoFolderButton'].set(False, request_frame=False)
        self.populate_target_videos()

    def select_save_video_path(self):
        temp = self.json_dict["saved videos"]
        self.json_dict["saved videos"] = filedialog.askdirectory(title="Select Save Video Folder", initialdir=temp)

        path = self.create_path_string(self.json_dict["saved videos"], 28)
        self.output_videos_text.configure(text=path)

        with open("data.json", "w") as outfile:
            json.dump(self.json_dict, outfile)
            outfile.close()
        self.widget['OutputFolderButton'].set(False, request_frame=False)
        self.add_action("saved_video_path",self.json_dict["saved videos"])

    def select_faces_path(self):
        temp = self.json_dict["source faces"]
        self.json_dict["source faces"] = filedialog.askdirectory(title="Select Source Faces Folder", initialdir=temp)

        path = self.create_path_string(self.json_dict["source faces"], 28)
        self.input_faces_text.configure(text=path)

        with open("data.json", "w") as outfile:
            json.dump(self.json_dict, outfile)
            outfile.close()
        self.widget['FacesFolderButton'].set(False, request_frame=False)
        self.load_input_faces()

    def load_dfl_input_models(self):
        text_font = font.Font(family="Helvetica", size=10)
        dfl_models_dir = 'dfl_models'
        j=len(self.source_faces)
        for model_file in listdir(dfl_models_dir):
            if model_file=='.gitkeep':
                continue
            new_source_face = self.source_face.copy()
            # self.source_faces.append(new_source_face)

            new_source_face["ButtonState"] = False
            new_source_face["Embedding"] = False
            new_source_face['DFLModel'] = model_file
            new_source_face['DFLModelPath'] = f'{dfl_models_dir}/{model_file}'

            button_text = f"(DFM) {model_file.split('.')[0]}"

            # Measure the text width
            # text_width = text_font.measure(button_text)
            text_width = text_font.measure('ABCDEFGHIJKLMNO')
            new_source_face["TKButton"] = tk.Button(self.merged_faces_canvas, style.media_button_off_3, image=self.blank, text=button_text, height=14, width=text_width, compound='left', anchor='w')

            new_source_face["TKButton"].bind("<ButtonRelease-1>", lambda event, arg=j: self.select_input_faces(event, arg))
            new_source_face["TKButton"].bind("<ButtonRelease-3>", lambda event, arg=j: self.select_input_faces(event, arg))
            self.bind_scroll_events(new_source_face["TKButton"], lambda event, delta: self.merged_faces_canvas.xview_scroll(delta, "units"))
            new_source_face['TextWidth'] = text_width
            x_width = 20
            if len(self.source_faces)>0:
                x_width += self.get_adjacent_element_width(j)
            new_source_face['XCoord'] = x_width
            self.merged_faces_canvas.create_window(x_width,8+(22*(j%4)), window = new_source_face["TKButton"],anchor='nw')
            self.source_faces.append(new_source_face)
            j+=1
        pass

    def get_adjacent_element_width(self, cur_index=0):
        x_width = 0
        if len(self.source_faces)>=4 and cur_index>=4:
            adjacent_elem_index = cur_index - 4
            x_width = self.source_faces[adjacent_elem_index].get('XCoord',0) + self.source_faces[adjacent_elem_index].get('TextWidth',0)
        return x_width

    def load_input_faces(self):
        self.source_faces = []
        self.merged_faces_canvas.delete("all")
        self.source_faces_canvas.delete("all")

        text_font = font.Font(family="Helvetica", size=10)

        # First load merged embeddings
        try:
            temp0 = []
            try:
                with open("merged_embeddings.txt", "r") as embedfile:
                    temp = embedfile.read().splitlines()

                    for i in range(0, len(temp), 513):
                        to = [temp[i][6:], np.array(temp[i+1:i+513], dtype='float32')]
                        temp0.append(to)
            except:
                pass

            for j in range(len(temp0)):
                new_source_face = self.source_face.copy()

                new_source_face["IsMergedEmbedding"] = True
                new_source_face["Visible"] = True

                new_source_face["File"] = ""
                new_source_face["ButtonState"] = False
                new_source_face["LockedButtonState"] = False
                new_source_face["Embedding"] = temp0[j][1]
                new_source_face["ButtonText"] = temp0[j][0]

                text_width = text_font.measure('ABCDEFGHIJKLMNO')

                new_source_face["TKButton"] = tk.Button(self.merged_faces_canvas, style.media_button_off_3, image=self.blank, text=new_source_face["ButtonText"], height=14, width=text_width, compound='left', anchor='w')

                new_source_face["TKButton"].bind("<ButtonRelease-1>", lambda event, arg=j: self.select_input_faces(event, arg))
                new_source_face["TKButton"].bind("<ButtonRelease-3>", lambda event, arg=j: self.select_input_faces(event, arg))
                self.bind_scroll_events(new_source_face["TKButton"], lambda event, delta: self.merged_faces_canvas.xview_scroll(delta, "units"))
                new_source_face['TextWidth'] = text_width
                x_width = 20
                if len(self.source_faces)>0:
                    x_width += self.get_adjacent_element_width(j)
                new_source_face['XCoord'] = x_width
                self.merged_faces_canvas.create_window(x_width,8+(22*(j%4)), window = new_source_face["TKButton"],anchor='nw')
                self.source_faces.append(new_source_face)

            self.load_dfl_input_models()

            self.merged_faces_canvas.configure(scrollregion = self.merged_faces_canvas.bbox("all"))
            self.merged_faces_canvas.xview_moveto(0)

        except Exception as e:
            pass

        self.shift_i_len = len(self.source_faces)

        # Next Load images
        directory = self.json_dict["source faces"]
        filenames = [os.path.join(dirpath,f) for (dirpath, dirnames, filenames) in os.walk(directory, followlinks=True) for f in filenames]

        filenames = sorted(filenames, key=str.lower)

        self.selected_source_faces = []
        self.selected_source_faces_canvas.delete("all")

        # torch.cuda.memory._record_memory_history(True, trace_alloc_max_entries=100000, trace_alloc_record_context=True)
        i=0
        for file in filenames: # Does not include full path
            # Find all faces and ad to faces[]
            # Guess File type based on extension
            try:
                file_type = mimetypes.guess_type(file)[0][:5]
            except:
                print('Unrecognized file type:', file)
            else:
                # Its an image
                if file_type == 'image':
                    img = cv2.imread(file)

                    if img is not None:
                        img = torch.from_numpy(img.astype('uint8')).to(self.models.device)

                        pad_scale = 0.2
                        padded_width = int(img.size()[1]*(1.+pad_scale))
                        padded_height = int(img.size()[0]*(1.+pad_scale))

                        padding = torch.zeros((padded_height, padded_width, 3), dtype=torch.uint8, device=self.models.device)

                        width_start = int(img.size()[1]*pad_scale/2)
                        width_end = width_start+int(img.size()[1])
                        height_start = int(img.size()[0]*pad_scale/2)
                        height_end = height_start+int(img.size()[0])

                        padding[height_start:height_end, width_start:width_end,  :] = img
                        img = padding

                        img = img.permute(2,0,1)
                        try:
                            if self.parameters["AutoRotationSwitch"]:
                                rotation_angles = [0, 90, 180, 270]
                            else:
                                rotation_angles = [0]
                            bboxes, kpss_5, _ = self.models.run_detect(img, detect_mode=self.parameters["DetectTypeTextSel"], max_num=1, score=0.5, use_landmark_detection=self.parameters['LandmarksDetectionAdjSwitch'], landmark_detect_mode=self.parameters["LandmarksDetectTypeTextSel"], landmark_score=0.5, from_points=self.parameters["LandmarksAlignModeFromPointsSwitch"], rotation_angles=rotation_angles) # Just one face here
                            kpss_5 = kpss_5[0]
                        except IndexError:
                            print('Image cropped too close:', file)
                        else:
                            face_emb, cropped_image = self.models.run_recognize(img, kpss_5, self.parameters["SimilarityTypeTextSel"], self.parameters['FaceSwapperModelTextSel'])
                            crop = cv2.cvtColor(cropped_image.cpu().numpy(), cv2.COLOR_BGR2RGB)
                            crop = cv2.resize(crop, (50, 50))

                            new_source_face = self.source_face.copy()
                            self.source_faces.append(new_source_face)
                            
                            self.source_faces[-1]["IsMergedEmbedding"] = False

                            self.source_faces[-1]["Image"] = ImageTk.PhotoImage(image=Image.fromarray(crop))
                            self.source_faces[-1]["Embedding"] = face_emb
                            self.source_faces[-1]["Size"] = 55
                            self.source_faces[-1]["TKButton"] = tk.Button(self.source_faces_canvas, style.media_button_off_3, image=self.source_faces[-1]["Image"], height=self.source_faces[-1]["Size"], width=self.source_faces[-1]["Size"])
                            self.source_faces[-1]["ButtonState"] = False
                            self.source_faces[-1]["LockedButtonState"] = False
                            self.source_faces[-1]["File"] = file
                            self.source_faces[-1]["Visible"] = True

                            self.source_faces[-1]["TKButton"].bind("<ButtonRelease-1>", lambda event, arg=len(self.source_faces)-1: self.select_input_faces(event, arg))            
                            self.source_faces[-1]["TKButton"].bind("<ButtonRelease-3>", lambda event, arg=len(self.source_faces)-1: self.select_input_faces(event, arg))
                            self.bind_scroll_events(self.source_faces[-1]["TKButton"], self.source_faces_mouse_wheel)

                            self.source_faces[-1]["ItemId"] = self.source_faces_canvas.create_window((i % 3) * 65, (i // 3) * 65, window=self.source_faces[-1]["TKButton"], anchor='nw')
                            self.source_faces[-1]["CanvasIndex"] = i

                            self.static_widget['input_faces_scrollbar'].resize_scrollbar(None)
                            i = i + 1

                    else:
                        print('Bad file', file)

        torch.cuda.empty_cache()

    def on_click_find_faces_button(self):
        auto_swap_state = self.widget['AutoSwapTextSel'].get()
        if auto_swap_state != "off":
            self.clear_target_faces()
            self.auto_swap()
        else:
            self.find_faces()

    def find_faces(self):
        try:
            img = torch.from_numpy(self.video_image).to(self.models.device)

            # Discard Alpha channel if it exists
            if img.shape[2] == 4:
                img = img[:, :, :3] 

            img = img.permute(2,0,1)
            if self.parameters["AutoRotationSwitch"]:
                rotation_angles = [0, 90, 180, 270]
            else:
                rotation_angles = [0]
            bboxes, kpss_5, _ = self.models.run_detect(img, detect_mode=self.parameters["DetectTypeTextSel"], max_num=50, score=self.parameters["DetectScoreSlider"]/100.0, use_landmark_detection=self.parameters['LandmarksDetectionAdjSwitch'], landmark_detect_mode=self.parameters["LandmarksDetectTypeTextSel"], landmark_score=self.parameters["LandmarksDetectScoreSlider"]/100.0, from_points=self.parameters["LandmarksAlignModeFromPointsSwitch"], rotation_angles=rotation_angles)

            ret = []
            for face_kps in kpss_5:
                face_emb, cropped_img = self.models.run_recognize(img, face_kps, self.parameters["SimilarityTypeTextSel"], self.parameters['FaceSwapperModelTextSel'])
                ret.append([face_kps, face_emb, cropped_img])

        except Exception as e:
            messagebox.showinfo('No Media', 'No appropriate media selected for find_faces method.')
            print(f"No appropriate media selected for find_faces method: {e}")

        else:
            # Find all faces and add to target_faces[]
            if ret:
                # Apply threshold tolerence
                threshhold = self.parameters["ThresholdSlider"]

                # if self.parameters["ThresholdState"]:
                    # threshhold = 0.0

                # Loop thgouh all faces in video frame
                for face in ret:
                    found = False

                    # Check if this face has already been found
                    for emb in self.target_faces:
                        if self.findCosineDistance(emb['Embedding'], face[1]) >= threshhold:
                            found = True
                            break

                    # If we dont find any existing simularities, it means that this is a new face and should be added to our found faces
                    if not found:
                        crop = cv2.resize(face[2].cpu().numpy(), (82, 82))

                        new_target_face = self.target_face.copy()
                        self.target_faces.append(new_target_face)
                        last_index = len(self.target_faces)-1

                        self.target_faces[last_index]["TKButton"] = tk.Button(self.found_faces_canvas, style.media_button_off_3, height = 86, width = 86)
                        self.bind_scroll_events(self.target_faces[last_index]["TKButton"], self.target_faces_mouse_wheel)
                        self.target_faces[last_index]["ButtonState"] = False
                        self.target_faces[last_index]["Image"] = ImageTk.PhotoImage(image=Image.fromarray(crop))
                        self.target_faces[last_index]["Embedding"] = face[1]
                        self.target_faces[last_index]["EmbeddingNumber"] = 1

                        # Add image to button
                        self.target_faces[-1]["TKButton"].config( pady = 10, image = self.target_faces[last_index]["Image"], command=lambda k=last_index: self.toggle_found_faces_buttons_state(k))

                        # Add button to canvas
                        self.found_faces_canvas.create_window((last_index)*92, 8, window=self.target_faces[last_index]["TKButton"], anchor='nw')

                        self.found_faces_canvas.configure(scrollregion = self.found_faces_canvas.bbox("all"))

    def clear_target_faces(self):
        self.target_faces = []
        self.found_faces_canvas.delete("all")

    def clear_selected_source_faces(self):
        self.selected_source_faces = []
        self.selected_source_faces_canvas.delete("all")

    def clear_faces(self):
        self.clear_target_faces()
        self.clear_selected_source_faces()

    def on_click_clear_target_faces_button(self):

        # Clears target faces and deselects all source faces, even locked ones

        self.clear_faces()

        self.clear_face_highlights(should_clear_button_state = True, should_clear_locked_button_state = True)

        self.select_input_faces("same", "") # Clear highlights, remove previous face applications

    # toggle the target faces button and make assignments
    def toggle_found_faces_buttons_state(self, button):
        # Turn all Target faces off
        for i in range(len(self.target_faces)):
            self.target_faces[i]["ButtonState"] = False
            self.target_faces[i]["TKButton"].config(style.media_button_off_3)

        # Set only the selected target face to on
        self.target_faces[button]["ButtonState"] = True
        self.target_faces[button]["TKButton"].config(style.media_button_on_3)

        # set all source face buttons to off (unless locked)
        self.clear_selected_source_faces()
        for i in range(len(self.source_faces)):
            face_locked = "LockedButtonState" in self.source_faces[i] and self.source_faces[i]["LockedButtonState"] == True
            if not face_locked:
                self.source_faces[i]["ButtonState"] = False
                self.source_faces[i]["TKButton"].config(style.media_button_off_3)
            else:
                self.select_input_faces("none", i)

        # turn back on the ones that are assigned to the curent target face
        for i in range(len(self.target_faces[button]["SourceFaceAssignments"])):
            self.source_faces[self.target_faces[button]["SourceFaceAssignments"][i]]["ButtonState"] = True

            is_locked = "LockedButtonState" in self.source_faces[self.target_faces[button]["SourceFaceAssignments"][i]] and self.source_faces[self.target_faces[button]["SourceFaceAssignments"][i]]["LockedButtonState"] == True
            button_style = style.media_button_on_lock_3 if is_locked else style.media_button_on_3

            self.source_faces[self.target_faces[button]["SourceFaceAssignments"][i]]["TKButton"].config(button_style)

        self.select_input_faces("same","")

    def clear_face_highlights(self, should_clear_button_state = False, should_clear_locked_button_state = False):

        for face in self.source_faces:
            face["TKButton"].config(style.media_button_off_3)

            # and also clear the states if not selecting multiples
            if should_clear_button_state:
                face["ButtonState"] = False
            if should_clear_locked_button_state:
                face["LockedButtonState"] = False

    def select_input_faces(self, event, button):

        def higlight_selected_faces(button_index):
            # Highlight all of input faces buttons that have a true state
            for face in self.source_faces:
                face_locked = "LockedButtonState" in face and face["LockedButtonState"] == True
                if face["ButtonState"] or face_locked:
                    
                    if face_locked:
                        face["TKButton"].config(style.media_button_on_lock_3)
                    else:
                        face["TKButton"].config(style.media_button_on_3)
                        
                    if self.widget['PreviewModeTextSel'].get() == 'FaceLab':
                        self.add_action("load_target_image", face["File"])
                        self.image_loaded = True

                # Clear DFL models from memory
                if self.models.dfl_models and self.parameters['DFLLoadOnlyOneSwitch']:
                    for model in list(self.models.dfl_models):
                        if model!=self.source_faces[button_index]['DFLModel']:
                            del self.models.dfl_models[model]._sess
                            del self.models.dfl_models[model]
                    gc.collect()

        def get_default_face_weights():
            return [
                self.widget['FaceWeights0Slider'].get(), 
                self.widget['FaceWeights1Slider'].get(), 
                self.widget['FaceWeights2Slider'].get(),
                self.widget['FaceWeights3Slider'].get(),
                self.widget['FaceWeights4Slider'].get(),
                self.widget['FaceWeights5Slider'].get()]

        def add_selected_face_to_selected_faces_canvas(face, default_weight_list = [], weight_cache = {}):

            if len(self.selected_source_faces) > 0:
                if "File" in face or "ButtonText" in face:
                    for selected_face in self.selected_source_faces:
                        if selected_face["File"] == (face["File"] if "File" in face and face["File"] != "" else face["ButtonText"]):
                            return selected_face

            new_target_face = self.selected_source_face.copy()
            self.selected_source_faces.append(new_target_face)
            last_index = len(self.selected_source_faces) - 1

            # button size (55x55)
            size = 55

            button = tk.Button(
                self.selected_source_faces_canvas,
                style.media_button_off_3,
                height=size, 
                width=size,
                image=self.blank, 
                text="",  # Initially no text for the button
            )
            button.config(font=("Arial", 1))
            self.selected_source_faces[last_index]["TKButton"] = button

            if "File" in face and face["File"] != "":
                self.selected_source_faces[last_index]["File"] = face["File"]
            else:
                self.selected_source_faces[last_index]["File"] = face["ButtonText"]
            self.selected_source_faces[last_index]["Embedding"] = face["Embedding"]

            def get_embedding_weight():
                embedding_weight = 10
                if self.selected_source_faces[last_index]["File"] in weight_cache:
                    embedding_weight = weight_cache[self.selected_source_faces[last_index]["File"]]
                elif len(default_weight_list) > last_index:
                    embedding_weight = default_weight_list[last_index]
                self.selected_source_faces[last_index]["EmbeddingWeight"] = embedding_weight

            get_embedding_weight()

            entry = tk.Entry(
                self.selected_source_faces_canvas, 
                font=("Arial", 8),
                width=int(size / 12)
            )
            self.selected_source_faces[last_index]["Entry"] = entry
            entry.insert(0, str(self.selected_source_faces[last_index]["EmbeddingWeight"])) 
            entry.grid(row=0, column=0)
            def update_entry_text():
                entry.delete(0, tk.END)
                entry.insert(0, str(self.selected_source_faces[last_index]["EmbeddingWeight"])) 
            def on_update_entry(event):
                try:
                    new_value = int(entry.get())
                    self.selected_source_faces[last_index]["EmbeddingWeight"] = new_value
                    assign_embeddings_to_target_face(False)
                except:
                    update_entry_text()
            entry.bind("<FocusOut>", on_update_entry)
            entry.bind("<Return>", on_update_entry)

            # Bind events and set initial button state
            def on_selected_face_scroll(event, delta):
                new_weight = max(0, self.selected_source_faces[last_index]["EmbeddingWeight"] - int(delta))
                self.selected_source_faces[last_index]["EmbeddingWeight"] = new_weight
                update_entry_text()
                assign_embeddings_to_target_face(False)

            def on_selected_face_left_click(event):
                get_embedding_weight()
                update_entry_text()
                assign_embeddings_to_target_face(False)

            def on_selected_face_right_click(event):
                face["LockedButtonState"] = True # lock it to unlock it
                face_index = self.source_faces.index(face)
                if face_index > -1:
                    self.select_input_faces("alt", face_index)

            self.bind_scroll_events(button, on_selected_face_scroll)
            button.bind("<ButtonRelease-1>", on_selected_face_left_click)            
            button.bind("<ButtonRelease-3>", on_selected_face_right_click)
            self.selected_source_faces[last_index]["ButtonState"] = False

            # Add image or text to button
            face_image = face["Image"]
            if isinstance(face_image, list):
                button.config(
                    text=f"{face['ButtonText']}", 
                    compound='center', 
                    anchor='center',  # Align text in the center
                    wraplength=size,   # Limit text to fit within button size
                    padx=0, pady=0
                )
            else:
                # If using an image, ensure it's resized to fit within the button
                self.selected_source_faces[last_index]["Image"] = face_image
                button.config(image=self.selected_source_faces[last_index]["Image"])

            # Add both button and entry to canvas
            pad_x = 6
            button_x = (last_index) * (size + pad_x)
            button_window = self.selected_source_faces_canvas.create_window(
                button_x, 
                8, 
                window=button, 
                anchor='center'
            )
            
            entry_window = self.selected_source_faces_canvas.create_window(
                button_x,  # Same X position as the button
                size,  # Position entry below the button
                window=entry, 
                anchor='center'
            )

            # Update canvas scroll region
            self.selected_source_faces_canvas.configure(scrollregion=self.selected_source_faces_canvas.bbox("all"))

            return self.selected_source_faces[last_index]

        def cache_selected_face_weights():

            weight_dict = {}

            for face in self.selected_source_faces:

                if "File" in face:
                    weight_dict[face["File"]] = face["EmbeddingWeight"]

            return weight_dict

        def assign_embeddings_to_target_face(clear_selected_source_faces = True):
            default_weight_list = get_default_face_weights()
            for tface in self.target_faces:
                if tface["ButtonState"]:
                    # Clear all of the assignments
                    tface["SourceFaceAssignments"] = []
                    tface['DFLModel'] = False

                    cached_weights = cache_selected_face_weights()

                    if clear_selected_source_faces:
                        self.clear_selected_source_faces()

                    # Iterate through all Input faces
                    temp_holder = []
                    for j in range(len(self.source_faces)):

                        # If the source face is active
                        face_locked = "LockedButtonState" in self.source_faces[j] and self.source_faces[j]["LockedButtonState"] == True
                        if self.source_faces[j]["ButtonState"] or face_locked:
                            tface["SourceFaceAssignments"].append(j)
                            selected_face = add_selected_face_to_selected_faces_canvas(self.source_faces[j], default_weight_list, cached_weights)
                            # Only append embedding if it is not a DFL model
                            if not self.source_faces[j]['DFLModel']:
                                temp_holder.append(selected_face['Embedding'])

                            if self.source_faces[j]['DFLModel']:
                                # Clear DFL models from memory
                                if self.models.dfl_models and self.parameters['DFLLoadOnlyOneSwitch']:
                                    for model in list(self.models.dfl_models):
                                        del self.models.dfl_models[model]._sess
                                        del self.models.dfl_models[model]
                                    gc.collect()
                                tface['DFLModel'] = self.source_faces[j]['DFLModel']

                    # do averaging
                    if temp_holder:
                        
                        tface['AssignedEmbedding'] = self.merge_embeddings(temp_holder)

                        self.temp_emb = tface['AssignedEmbedding']
                    else:
                        tface['AssignedEmbedding'] = []

                        # for k in range(512):
                        #     self.widget['emb_vec_' + str(k)].set(tface['AssignedEmbedding'][k], False)
                    break

            self.add_action("target_faces", self.target_faces)
            self.add_action('get_requested_video_frame', self.video_slider.get())

        try:
            if event.num == 1: # left click
                if event.state & 0x4 != 0:
                    modifier = 'ctrl'
                elif event.state & 0x1 != 0:
                    modifier = 'shift'
                elif event.state & 0x8 != 0:
                    modifier = 'alt'
                else:
                    modifier = 'none'
            elif event.num == 3: # right click
                modifier = 'alt'
            else:
                modifier = 'none'
        except:
            modifier = event

        # If autoswap isnt on
        # Clear all the highlights. Clear all states, excpet if a modifier is being used
        # Start by turning off all the highlights on the input faces buttons
        if modifier != 'same' and modifier != 'random' and modifier != 'merge':
            self.clear_face_highlights(modifier == 'none')

            # Toggle the state of the selected Input Face
            face_locked = "LockedButtonState" in self.source_faces[button] and self.source_faces[button]["LockedButtonState"] == True

            if not face_locked:
                self.source_faces[button]["ButtonState"] = not self.source_faces[button]["ButtonState"]

            # if shift find any other input faces and activate the state of all faces in between
            if modifier == 'shift':
                # Check if there is any dfl models already selected.
                if self.source_faces[button]["DFLModel"]:
                    for i in range(len(self.source_faces)):
                        if i==button:
                            continue
                        if self.source_faces[i]["ButtonState"] and self.source_faces[i]['DFLModel'] :
                            self.source_faces[button]["ButtonState"] = False
                            messagebox.showinfo('You cannot combine DFL Models!','You cannot combine DFL Models!')
                            for face in self.source_faces:
                                face['ButtonState'] = False
                                face["LockedButtonState"] = False
                            break

                for i in range(button-1, self.shift_i_len-1, -1):
                    face_locked = "LockedButtonState" in self.source_faces[i] and self.source_faces[i]["LockedButtonState"] == True
                    if not face_locked and self.source_faces[i]["ButtonState"]:
                        for j in range(i, button, 1):
                            if self.source_faces[j]["Visible"]:
                                self.source_faces[j]["ButtonState"] = True
                        break
                for i in range(button+1, len(self.source_faces), 1):
                    face_locked = "LockedButtonState" in self.source_faces[i] and self.source_faces[i]["LockedButtonState"] == True
                    if not face_locked and self.source_faces[i]["ButtonState"]:
                        for j in range(button, i, 1):
                            if self.source_faces[j]["Visible"]:
                                self.source_faces[j]["ButtonState"] = True
                        break

            if modifier == "alt":
                face_locked = "LockedButtonState" in self.source_faces[button] and self.source_faces[button]["LockedButtonState"] == True
                self.source_faces[button]["LockedButtonState"] = not face_locked
                self.source_faces[button]["ButtonState"] = self.source_faces[button]["LockedButtonState"]
                
            higlight_selected_faces(button)
            
        if modifier == 'random':
            self.clear_face_highlights(True)
            face_count = len(self.source_faces)
            random_index = randint(0, face_count - 1)
            self.source_faces[random_index]["ButtonState"] = True
            higlight_selected_faces(random_index)

        assign_embeddings_to_target_face()


    def populate_target_videos(self):
        videos = []
        #Webcam setup
        camera_backend = CAMERA_BACKENDS[self.parameters['WebCamBackendSel']]
        for i in range(self.parameters['WebCamMaxNoSlider']):
            try:
                camera = cv2.VideoCapture(i, camera_backend)
                if not camera.isOpened():
                    continue
                success, webcam_frame = camera.read()
                if not success:
                    continue
                ratio = float(webcam_frame.shape[0]) / webcam_frame.shape[1]
                new_height = 50
                new_width = int(new_height / ratio)
                webcam_frame = cv2.resize(webcam_frame, (new_width, new_height))
                webcam_frame = cv2.cvtColor(webcam_frame, cv2.COLOR_BGR2RGB)
                webcam_frame[:new_height, :new_width, :] = webcam_frame
                videos.append([webcam_frame, f'Webcam {i}'])
                camera.release()
            except Exception as e:
                print(e)

        # Recursively read all media files from directory
        directory =  self.json_dict["source videos"]
        filenames = [os.path.join(dirpath,f) for (dirpath, dirnames, filenames) in os.walk(directory, followlinks=True) for f in filenames]

        filenames = sorted(filenames, key=str.lower)

        images = []
        video_files = []
        self.target_media = []
        self.target_media_buttons = []
        self.target_media_canvas.delete("all")

        for file in filenames: # Does not include full path
            # Guess File type based on extension
            try:
                file_type = mimetypes.guess_type(file)[0][:5]
            except:
                print('Unrecognized file type:', file)
            else:
                # Its an image
                if file_type == 'image':
                    is_animated = False
                    try:

                        def open_cv():
                            image = cv2.imread(file)
                            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                        def open_pil():
                            with Image.open(file) as img:

                                frames = list(ImageSequence.Iterator(img))

                                if len(frames) > 1:
                                    is_animated = True

                                # If it's an animated GIF, use the first frame
                                img = img.convert('RGB')  # Ensure it has RGB mode
                                return np.array(img), is_animated

                        try:
                            # Prioritize pil for webp and gif images
                            if file.endswith(".webp") or file.endswith(".gif"):
                                image, is_animated = open_pil()
                            else:
                                image = open_cv()
                        except:
                            if file.endswith(".webp") or file.endswith(".gif"):
                                image = open_cv()
                            else:
                                image, is_animated = open_pil()

                    except Exception as e:
                        print(f"Trouble reading file '{file}': {e}")
                    else:
                        ratio = float(image.shape[0]) / image.shape[1]

                        new_height = 100
                        new_width = int(new_height / ratio)
                        image = cv2.resize(image, (new_width, new_height))
                        image[:new_height, :new_width, :] = image

                        if is_animated:
                            videos.append([image, file])
                        else:
                            images.append([image, file])

                # If it's a mimetype of video, we will render thumbnails asynchronously
                elif file_type == 'video':
                    videos.append([None,file])

        if self.widget['PreviewModeTextSel'].get()== 'Image':#images
            for i in range(len(images)):
                button = tk.Button(self.target_media_canvas, style.media_button_off_3, height = 115, width = 180)
                button.visible = True
                self.target_media_buttons.append(button)

                rgb_video = Image.fromarray(images[i][0])
                self.target_media.append(ImageTk.PhotoImage(image=rgb_video))
                button.config( image = self.target_media[i],  command=lambda i=i: self.load_target(images[i][1], self.widget['PreviewModeTextSel'].get()))
                button.media_file = images[i][1]
                button.original_index = i
                self.bind_scroll_events(button, self.target_videos_mouse_wheel)
                button.has_thumbnail = True

        elif self.widget['PreviewModeTextSel'].get()=='Video':#videos

            ratio = float(self.splash_image.shape[0]) / self.splash_image.shape[1]

            new_height = 100
            new_width = int(new_height / ratio)
            placeholder_image = cv2.resize(self.splash_image, (new_width, new_height))
            placeholder_image[:new_height, :new_width, :] = placeholder_image
            
            placeholder_thumbnail = ImageTk.PhotoImage(image=Image.fromarray(placeholder_image))

            for i in range(len(videos)):

                image = videos[i][0]
                has_thumbnail = True if image is not None else False

                button = tk.Button(self.target_media_canvas, style.media_button_off_3, height = 115, width = 165)
                button.visible = True
                self.target_media_buttons.append(button)
                self.target_media.append(ImageTk.PhotoImage(image=Image.fromarray(image)) if has_thumbnail else placeholder_thumbnail)

                filename = os.path.basename(videos[i][1])
                hovertip = RopeHovertip(button, filename, x_offset=190)
                if len(filename)>32:
                    filename = filename[:29]+'...'

                self.bind_scroll_events(button, self.target_videos_mouse_wheel)
                button.config(image = self.target_media[i], text=filename, compound='top', anchor='n',command=lambda i=i: self.load_target(videos[i][1], self.widget['PreviewModeTextSel'].get()))
                button.media_file = videos[i][1]
                button.original_index = i
                button.has_thumbnail = has_thumbnail

        self.target_media_shuffle_history = set()
        self.all_target_media_thumbnails_generated = False
        self.redraw_target_media_canvas()

    def filter_target_media(self, filter_text):

        lowercase_filter_text = filter_text.lower()

        for button in self.target_media_buttons:
            if lowercase_filter_text in button.media_file.lower():
                button.visible = True
            else:
                button.visible = False

        self.redraw_target_media_canvas()

    def filter_source_faces(self, filter_text):

        lowercase_filter_text = filter_text.lower()

        for face in self.source_faces:
            comparison_text = face["ButtonText"].lower() if isinstance(face["File"], list) else face["File"].lower()
            if lowercase_filter_text in comparison_text:
                face["Visible"] = True
            else:
                face["Visible"] = False

        self.redraw_source_faces_canvas()

    def redraw_target_media_canvas(self,):
        # Clear all canvas items
        self.target_media_canvas.delete("all")

        delx, dely = 100, 120

        # Get a list of visible items
        visible_items = []
        for button in self.target_media_buttons:
            if button.visible == True:
                visible_items.append(button)

        # Re-add the items to the canvas, repositioning them as needed
        for i, button in enumerate(visible_items):
            if button.visible == True: 
                button.item_id = self.target_media_canvas.create_window(0, i*dely, window = visible_items[i], anchor='nw')
                button.canvas_index = i

        self.static_widget['input_videos_scrollbar'].resize_scrollbar(None)

        self.render_thumbnails_for_drawn_target_media_buttons()

    def redraw_source_faces_canvas(self):
        # Clear all canvas items
        self.source_faces_canvas.delete("all")

        delx, dely = 65, 65

        # Get a list of visible items
        visible_items = []
        for face in self.source_faces:
            # Only place "image" faces and not merged embeddings
            if face["File"] != "" and face["Visible"] == True: 
                visible_items.append(face)

        # Re-add the items to the canvas, repositioning them as needed
        for i, face in enumerate(visible_items):
            face["ItemId"] = self.source_faces_canvas.create_window((i % 3) * delx, (i // 3) * dely, window=visible_items[i]["TKButton"], anchor='nw')
            face["CanvasIndex"] = i

        self.static_widget['input_faces_scrollbar'].resize_scrollbar(None)

    def is_item_drawn_in_canvas(self, canvas, item_id):
        coords = canvas.bbox(item_id)
        if coords:
            x1, y1, x2, y2 = coords
            
            # Get the current scroll position 
            scroll_y1, scroll_y2 = canvas.yview()

            # Get the full height of the canvas and apply the scroll offset
            canvas_height = canvas.bbox("all")[3] 
            
            # Calculate the vertical range of the visible area after scrolling
            visible_y1 = scroll_y1 * canvas_height 
            visible_y2 = scroll_y2 * canvas_height

            # Check if any part of the item's bounding box overlaps with the visible area
            if x2 >= 0 and y2 >= visible_y1 and x1 <= canvas.winfo_width() and y1 <= visible_y2:
                return True

        return False

    def get_visible_media_buttons(self):

        out_buttons = []

        for button in self.target_media_buttons:
            if button.visible:
                out_buttons.append(button)

        return out_buttons

    def get_drawn_target_media_buttons(self, visible_buttons):

        out_buttons = []
        has_found_drawn = False

        _, view_y2 = self.target_media_canvas.yview()
        button_count = len(visible_buttons)

        # Multiply scroll amount by button count to get an index to start with
        # then offset it to start a bit before that point and clamp it to min 0
        start_index = max(0, int(button_count * view_y2) - 20)

        for i in range(start_index, button_count):
            button = visible_buttons[i]
            if not button.visible:
                continue
            if self.is_item_drawn_in_canvas(self.target_media_canvas, button.item_id):
                out_buttons.append(button)
                has_found_drawn = True
            elif has_found_drawn:
                # drawn target media wil be contiguous,
                # so if we've found some drawn media
                # but this iteration doesn't return drawn,
                # we're not going to find anymore drawn items
                break

        return out_buttons

    def render_thumbnail_for_target_media_button(self, button):

        if button.has_thumbnail:
            return

        frame = process_video(button.media_file)

        if frame is not None:
            thumbnail = ImageTk.PhotoImage(image=Image.fromarray(frame))
            self.target_media[button.original_index] = thumbnail
            button.config(image = thumbnail)
            button.has_thumbnail = True

    def render_thumbnails_for_drawn_target_media_buttons(self):

        filter_text = self.widget['TargetMediaSearchBarTextEntry'].get()

        visible_buttons = self.target_media_buttons if filter_text == "" else self.get_visible_media_buttons()

        for button in self.get_drawn_target_media_buttons(visible_buttons):
            self.render_thumbnail_for_target_media_button(button)

    def render_thumbnails_for_all_target_media_buttons(self):

        for button in self.target_media_buttons:
            self.render_thumbnail_for_target_media_button(button)

        self.all_target_media_thumbnails_generated = True

    def on_input_videos_scrollbar_mouse_motion(self, event):

        if event is not None:
            self.static_widget['input_videos_scrollbar'].scroll(event)

        if self.all_target_media_thumbnails_generated == True:
            return

        if self.scroll_timeout:
            self.after_cancel(self.scroll_timeout)

        def is_scrolled_to_max_y(canvas):
            # Get the bounding box of all items on the canvas (x1, y1, x2, y2)
            bbox = canvas.bbox("all")
            
            # Get the current vertical scroll position (fractional values)
            _, curr_y1, _, curr_y2 = canvas.bbox("all")
            _, view_y2 = canvas.yview()
            
            if bbox is None:
                return False

            # Get the height of the canvas viewport
            canvas_height = canvas.winfo_height()

            # Check if the current scroll position is at the bottom
            if view_y2 == 1.0:  # 1.0 means the scrollbar is at the bottom
                return True
            return False

        # Scroll to bottom and let it time out to load all thumbnails immediately
        if is_scrolled_to_max_y(self.target_media_canvas):
            self.scroll_timeout = self.after(1000, self.render_thumbnails_for_all_target_media_buttons)
        else:
            self.scroll_timeout = self.after(350, self.render_thumbnails_for_drawn_target_media_buttons)

    def toggle_auto_swap(self):
        auto_swap_state = self.widget['AutoSwapTextSel'].get()
        modes = DEFAULT_DATA["AutoSwapTextSelModes"]

        if auto_swap_state in modes:
            index = modes.index(auto_swap_state) + 1
            if index > len(modes) - 1:
                index = 0
            self.widget['AutoSwapTextSel'].set(modes[index])

    def auto_swap(self):
        # Reselect Target Image
        auto_swap_state = self.widget['AutoSwapTextSel'].get()
        try:
            self.find_faces()

            # "Cosmetically" turn off all target faces
            # Don't use toggle_found_faces_buttons_state
            # because that will affect currently selected faces
            def deselect_all_target_faces():
                for i in range(len(self.target_faces)):
                    self.target_faces[i]["ButtonState"] = False
                    self.target_faces[i]["TKButton"].config(style.media_button_off_3)

            for i in range(len(self.target_faces)):
                deselect_all_target_faces()
                self.target_faces[i]["ButtonState"] = True
                self.target_faces[i]["TKButton"].config(style.media_button_on_3)

                # Reselect Source images
                self.select_input_faces(auto_swap_state, '')
            self.toggle_swapper(True)

        except Exception as e:
            print(f"Exception in auto_swap: {e}")
            pass
              
    def load_target(self, media_file, media_type):
        # Make sure the video stops playing
        self.toggle_play_video('stop')
        self.image_loaded = False
        self.video_loaded = False
        self.clear_target_faces()

        if media_type == 'Video':
            self.add_action("load_target_video", media_file)
            self.media_file = media_file
            self.media_file_name = os.path.splitext(os.path.basename(media_file))
            self.video_slider.set(0)
            self.video_loaded = True

        elif media_type == 'Image':
            self.add_action("load_target_image", media_file)
            self.media_file_name = os.path.splitext(os.path.basename(media_file))
            self.media_file = media_file
            self.image_loaded = True

        self.title(f"{self.title_text} - {os.path.basename(media_file)}")

        # # find faces
        auto_swap_state = self.widget['AutoSwapTextSel'].get()
        if auto_swap_state != "off":
            self.add_action('function', "gui.auto_swap()")
            self.toggle_play_video("play")

        # Allow continuous playback if play next or play random
        after_playback = self.widget['AfterPlaybackTextSel'].get()
        if after_playback in ['next', 'shuffle']:
            self.toggle_play_video("play")

        for i in range(len(self.target_media_buttons)):
            if self.target_media_buttons[i].visible:
                if self.target_media_buttons[i].media_file == media_file:
                    self.target_media_buttons[i].config(style.media_button_on_3)
                else:
                    self.target_media_buttons[i].config(style.media_button_off_3)

        # delete all markers
        self.layer['markers_canvas'].delete('all')
        self.markers = []
        self.stop_marker = []

        #region [#111111b4]

        self.load_markers_json()
        self.add_action("update_markers_canvas", self.markers)

        #endregion

        self.add_action("markers", self.markers)

        self.set_delete_media_button_confirm_message_state(False)

    # @profile
    def set_image(self, image, requested):
        self.video_image = image[0]
        frame = image[1]

        if not requested:
            self.video_slider.set(frame)
            self.parameter_update_from_marker(frame)

        self.resize_image()

    # @profile
    def resize_image(self):
        image = self.video_image

        if len(image) != 0:

            x1 = float(self.video.winfo_width())
            y1 = float(self.video.winfo_height())

            x2 = float(image.shape[1])
            y2 = float(image.shape[0])

            m1 = x1/y1
            m2 = x2/y2

            if m2>m1:
                x2 = x1
                y2 = x1/m2
                image = cv2.resize(image, (int(x2), int(y2)))
                padding = int((y1-y2)/2.0)
                image = cv2.copyMakeBorder( image, padding, padding, 0, 0, cv2.BORDER_CONSTANT)
            else:
                y2=y1
                x2=y2*m2
                image = cv2.resize(image, (int(x2), int(y2)))
                padding=int((x1-x2)/2.0)
                image = cv2.copyMakeBorder( image, 0, 0, padding, padding, cv2.BORDER_CONSTANT)

            image = Image.fromarray(image)
            image = ImageTk.PhotoImage(image)
            self.video.image = image
            self.video.configure(image=self.video.image)

    def check_for_video_resize(self):

        # Read the geometry from the last time json was updated. json only updates once the window ahs stopped changing
        win_geom = '%dx%d+%d+%d' % (self.json_dict['dock_win_geom'][0], self.json_dict['dock_win_geom'][1] , self.json_dict['dock_win_geom'][2], self.json_dict['dock_win_geom'][3])

        # # window has started changing
        if self.winfo_geometry() != win_geom:
            # Resize image in video window
            self.resize_image()
            for k, v in self.widget.items():
                v.is_resizing = True
                v.hide()
                v.is_resizing = False
            for k, v in self.static_widget.items():
                v.is_resizing = True
                v.hide()
                v.is_resizing = False

            # Check if window has stopped changing
            if self.winfo_geometry() != self.window_last_change:
                self.window_last_change = self.winfo_geometry()

            # The window has stopped changing
            else:
                for k, v in self.widget.items():
                    v.is_resizing = True
                    v.unhide()
                    v.is_resizing = False
                for k, v in self.static_widget.items():
                    v.is_resizing = True
                    v.unhide()
                    v.is_resizing = False
                # Update json
                str1 = self.winfo_geometry().split('x')
                str2 = str1[1].split('+')
                win_geom = [str1[0], str2[0], str2[1], str2[2]]
                win_geom = [int(strings) for strings in win_geom]
                self.json_dict['dock_win_geom'] = win_geom
                with open("data.json", "w") as outfile:
                    json.dump(self.json_dict, outfile)

    def get_action(self):
        action = self.action_q[0]
        self.action_q.pop(0)
        return action

    def get_action_length(self):
        return len(self.action_q)

    def set_video_slider_length(self, video_length):
        self.video_slider.set_length(video_length)

    def set_video_slider_fps(self, fps):
        self.video_slider.set_fps(fps)

    def findCosineDistance(self, vector1, vector2):
        vector1 = vector1.ravel()
        vector2 = vector2.ravel()
        cos_dist = 1 - np.dot(vector1, vector2)/(np.linalg.norm(vector1)*np.linalg.norm(vector2)) # 2..0
        return 100-cos_dist*50
        '''
        vector1 = vector1.ravel()
        vector2 = vector2.ravel()

        return 1 - np.dot(vector1, vector2)/(np.linalg.norm(vector1)*np.linalg.norm(vector2))
        '''

    def toggle_play_video(self, set_value='toggle'):
        if self.video_loaded:

            # Update button
            if set_value == 'toggle':
                self.widget['TLPlayButton'].toggle_button()
            if set_value == 'stop':
                self.widget['TLPlayButton'].disable_button()
            if set_value == 'play':
                self.widget['TLPlayButton'].enable_button()

            # If play
            if self.widget['TLPlayButton'].get():
                if not self.video_loaded:
                    print("Please select video first!")
                    return
                else:
                    # and record
                    if self.widget['TLRecButton'].get():
                        if not self.json_dict["saved videos"]:
                            messagebox.showinfo('Set saved videos folder','PLease set a folder to save videos before starting to record ')
                            print("Set saved video folder first!")
                            self.add_action("play_video", "stop_from_gui")

                        else:
                            self.add_action("play_video", "record")

                    # only play
                    else:
                        self.add_action("play_video", "play")

            else:
                self.add_action("play_video", "stop_from_gui")

    def set_player_buttons_to_inactive(self):
        self.widget['TLRecButton'].disable_button()
        self.widget['TLPlayButton'].disable_button()

    def set_virtual_cam_toggle_disable(self):
        self.widget['VirtualCameraSwitch'].toggle_switch(False)

    def toggle_swapper(self, toggle_value=-1):
        # print(inspect.currentframe().f_back.f_code.co_name, 'toggle_swapper: '+'toggle_value='+str(toggle_value))

        if toggle_value == -1:
            self.widget['SwapFacesButton'].toggle_button()

        else:
            if toggle_value:
                self.widget['SwapFacesButton'].enable_button()
            else:
                self.widget['SwapFacesButton'].disable_button()

        if self.widget['PreviewModeTextSel'].get()=='Video' or self.widget['PreviewModeTextSel'].get()=='Theater':
            self.update_data('control', 'SwapFacesButton', use_markers=True)
        elif self.widget['PreviewModeTextSel'].get()=='Image':
            self.update_data('control', 'SwapFacesButton', use_markers=False)
        elif self.widget['PreviewModeTextSel'].get() == 'FaceLab':
            self.update_data('control', 'SwapFacesButton', use_markers=False)

    def temp_toggle_swapper(self, state):
        if state=='off':
            self.widget['SwapFacesButton'].temp_disable_button()
        elif state=='on':
            self.widget['SwapFacesButton'].temp_enable_button()

        self.update_data('control', 'SwapFacesButton', use_markers=True)

    def toggle_enhancer(self, toggle_value=-1):
        if toggle_value == -1:
            self.widget['EnhanceFrameButton'].toggle_button()

        else:
            if toggle_value:
                self.widget['EnhanceFrameButton'].enable_button()
            else:
                self.widget['EnhanceFrameButton'].disable_button()

        if self.widget['PreviewModeTextSel'].get()=='Video' or self.widget['PreviewModeTextSel'].get()=='Theater':
            self.update_data('control', 'EnhanceFrameButton', use_markers=True)
        elif self.widget['PreviewModeTextSel'].get()=='Image':
            self.update_data('control', 'EnhanceFrameButton', use_markers=False)
        elif self.widget['PreviewModeTextSel'].get() == 'FaceLab':
            self.update_data('control', 'EnhanceFrameButton', use_markers=False)

    def temp_toggle_enhancer(self, state):
        if state=='off':
            self.widget['EnhanceFrameButton'].temp_disable_button()
        elif state=='on':
            self.widget['EnhanceFrameButton'].temp_enable_button()

        self.update_data('control', 'EnhanceFrameButton', use_markers=True)

    def toggle_faces_editor(self, toggle_value=-1):
        if toggle_value == -1:
            self.widget['EditFacesButton'].toggle_button()

        else:
            if toggle_value:
                self.widget['EditFacesButton'].enable_button()
            else:
                self.widget['EditFacesButton'].disable_button()

        if self.widget['PreviewModeTextSel'].get()=='Video' or self.widget['PreviewModeTextSel'].get()=='Theater':
            self.update_data('control', 'EditFacesButton', use_markers=True)
        elif self.widget['PreviewModeTextSel'].get()=='Image':
            self.update_data('control', 'EditFacesButton', use_markers=False)
        elif self.widget['PreviewModeTextSel'].get() == 'FaceLab':
            self.update_data('control', 'EditFacesButton', use_markers=False)

    def temp_toggle_faces_editor(self, state):
        if state=='off':
            self.widget['EditFacesButton'].temp_disable_button()
        elif state=='on':
            self.widget['EditFacesButton'].temp_enable_button()

        self.update_data('control', 'EditFacesButton', use_markers=True)

    def toggle_rec_video(self):
        # Play button must be off to enable record button

        #region [#111111b4]

        self.save_markers_json()

        #endregion

        if not self.widget['TLPlayButton'].get():
            self.widget['TLRecButton'].toggle_button()

            if self.widget['TLRecButton'].get():
                self.widget['TLRecButton'].enable_button()

            else:
                self.widget['TLRecButton'].disable_button()

    # this makes no sense
    def add_action(self, action, parameter=None): #
        # print(inspect.currentframe().f_back.f_code.co_name, '->add_action: '+action)

        if action != 'get_requested_video_frame' and action != 'get_requested_video_frame_without_markers':
            self.action_q.append([action, parameter])

        # Only do requests when the video is not playing - (moving the timeline or changing parameters)
        elif self.video_loaded and not self.widget['TLPlayButton'].get():
            self.action_q.append([action, parameter])

        elif self.image_loaded:
            self.action_q.append([action, parameter])

    def update_vram_indicator(self):
        try:
            used, total = self.models.get_gpu_memory()
        except:
            pass
        else:
            self.static_widget['vram_indicator'].set(used, total)

    def merge_embeddings(self, embedding_array):
        if embedding_array:
            if self.widget['MergeTextSel'].get() == 'Median':
                return np.median(embedding_array, 0)
            elif self.widget['MergeTextSel'].get() == 'Mean':
                weighted_array = []
                # If multiple faces aren't selected, don't bother weighting
                if self.widget['ApplyFaceWeightsSwitch'].get() == True and len(embedding_array) > 1:

                    for i in range(len(embedding_array)):
                        weighted_array.extend([embedding_array[i]] * self.selected_source_faces[i]["EmbeddingWeight"])
                        
                else:
                    weighted_array = embedding_array
                return np.mean(weighted_array, 0)
        else:
            return []


# refactor and thread i/o
    def save_selected_source_faces(self, text):
        # get name from text field
        text = text.get()
        # get embeddings from all highlightebuttons
        # iterate through the buttons

        temp_holder = []

        for button in self.source_faces:
            if button["ButtonState"]:
                temp_holder.append(button['Embedding'])

        if temp_holder:
            
            ave_embedding = self.merge_embeddings(temp_holder)

            for tface in self.target_faces:
                if tface["ButtonState"]:
                    ave_embedding = tface['AssignedEmbedding']

            if text != "":
                with open("merged_embeddings.txt", "a") as embedfile:
                    identifier = "Name: "+text
                    embedfile.write("%s\n" % identifier)
                    for number in ave_embedding:
                        embedfile.write("%s\n" % number)
            else:
                print('No embedding name specified')
        else:
            print('No Source Images selected')

        self.focus()
        self.load_input_faces()

# refactor and thread i/o
    def delete_merged_embedding(self): #add multi select

    # get selected button
        sel = []
        for j in range(len(self.source_faces)):
            if self.source_faces[j]["ButtonState"]:
                sel = j
                break

        # check if it is a merged embedding
        # if so, read txt embedding into list
        temp0 = []
        if os.path.exists("merged_embeddings.txt"):

            with open("merged_embeddings.txt", "r") as embedfile:
                temp = embedfile.read().splitlines()

                for i in range(0, len(temp), 513):
                    to = [temp[i], np.array(temp[i+1:i+513], dtype='float32')]
                    temp0.append(to)

        if j < len(temp0):
            temp0.pop(j)

            with open("merged_embeddings.txt", "w") as embedfile:
                for line in temp0:
                    embedfile.write("%s\n" % line[0])
                    for i in range(512):
                        embedfile.write("%s\n" % line[1][i])

        self.load_input_faces()

    def iterate_through_merged_embeddings(self, event, delta):
        if delta>0:
            for i in range(len(self.source_faces)):
                if self.source_faces[i]["ButtonState"] and i<len(self.source_faces)-1:
                    self.select_input_faces('none', i+1)
                    break
        elif delta<0:
            for i in range(len(self.source_faces)):
                if self.source_faces[i]["ButtonState"]and i>0:
                    self.select_input_faces('none', i-1)
                    break

    def set_view(self, load_target_videos,b):
        # self.clear_target_faces()
        # self.video_loaded = False
        # self.image_loaded = False
        if load_target_videos and self.widget['PreviewModeTextSel'].get() != 'Theater':
            self.populate_target_videos()

        self.layer['slider_frame'].grid_forget()
        self.layer['preview_frame'].grid_forget()
        self.layer['markers_canvas'].grid_forget()
        self.layer['FaceLab_controls'].grid_forget()
        self.layer['InputVideoFrame'].grid_forget()
        self.layer['parameter_frame'].grid_forget()

        self.layer['parameters_canvas'].grid_forget()
        self.layer['parameter_scroll_canvas'].grid_forget()

        self.layer['facelab_canvas'].grid_forget()
        self.layer['facelab_scroll_canvas'].grid_forget()

        if self.widget['PreviewModeTextSel'].get()=='Video':
            self.image_loaded = False
            self.layer['slider_frame'].grid(row=2, column=0, sticky='NEWS', pady=0)
            self.layer['preview_frame'].grid(row=4, column=0, sticky='NEWS')
            self.layer['markers_canvas'].grid(row=3, column=0, sticky='NEWS')
            self.layer['parameter_frame'].grid(row=0, column=2, sticky='NEWS', pady=0, padx=1)

            self.layer['parameters_canvas'].grid(row=1, column=0, sticky='NEWS', pady=0, padx=0)
            self.layer['parameter_scroll_canvas'].grid(row=1, column=1, sticky='NEWS', pady=0)
            self.layer['InputVideoFrame'].grid(row=0, column=0, sticky='NEWS', padx=1, pady=0)

        elif self.widget['PreviewModeTextSel'].get()=='Image':
            self.video_loaded = False

            self.layer['parameters_canvas'].grid(row=1, column=0, sticky='NEWS', pady=0, padx=0)
            self.layer['parameter_scroll_canvas'].grid(row=1, column=1, sticky='NEWS', pady=0)
            self.layer['InputVideoFrame'].grid(row=0, column=0, sticky='NEWS', padx=1, pady=0)
            self.layer['parameter_frame'].grid(row=0, column=2, sticky='NEWS', pady=0, padx=1)

        elif self.widget['PreviewModeTextSel'].get() == 'FaceLab':
            self.video_loaded = False
            self.layer['FaceLab_controls'].grid(row=2, column=0, rowspan=2, sticky='NEWS', pady=0)
            self.layer['facelab_canvas'].grid(row=1, column=0, sticky='NEWS', pady=0, padx=0)
            self.layer['facelab_scroll_canvas'].grid(row=1, column=1, sticky='NEWS', pady=0)
            self.layer['InputVideoFrame'].grid(row=0, column=0, sticky='NEWS', padx=1, pady=0)
            self.layer['parameter_frame'].grid(row=0, column=2, sticky='NEWS', pady=0, padx=1)

            # # find the input image with the lowest value
            # for face in self.source_faces:
            #     if face["ButtonState"]:
            #         self.image_loaded = True
            #         self.add_action("load_target_image", face["File"])
            #         break

        elif self.widget['PreviewModeTextSel'].get() == 'Theater':
            self.image_loaded = False
            self.layer['slider_frame'].grid(row=2, column=0, sticky='NEWS', pady=0)
            self.layer['preview_frame'].grid(row=4, column=0, sticky='NEWS')
            self.layer['markers_canvas'].grid(row=3, column=0, sticky='NEWS')

    def update_marker(self, action):

        if action=='add':
             # Delete existing marker at current frame and replace with new data
            for i in range(len(self.markers)):
                if self.markers[i]['frame'] == self.video_slider.get():
                    self.layer['markers_canvas'].delete(self.markers[i]['icon_ref'])
                    self.markers.pop(i)
                    break

            width = self.layer['markers_canvas'].winfo_width()-20-40-20
            position = 20+int(width*self.video_slider.get()/self.video_slider.get_length())

            temp_param = copy.deepcopy(self.parameters)
            temp = {
                    'frame':        self.video_slider.get(),
                    'parameters':   temp_param,
                    'icon_ref':     self.layer['markers_canvas'].create_line(position,0, position, 15, fill='light goldenrod'),
                    }

            self.markers.append(temp)
            def sort(e):
                return e['frame']

            self.markers.sort(key=sort)
            self.add_action("markers", self.markers)

        # elif action=='stop':
        #     if self.stop_marker == self.video_slider.get():
        #         self.stop_marker = []
        #         self.add_action('set_stop', -1)
        #         self.video_slider_canvas.delete(self.stop_image)
        #     else:
        #         self.video_slider_canvas.delete(self.stop_image)
        #         self.stop_marker = self.video_slider.self.timeline_position
        #         self.add_action('set_stop', self.stop_marker)
        #
        #         width = self.video_slider_canvas.winfo_width() - 30
        #         position = 15 + int(width * self.video_slider.self.timeline_position / self.video_slider.configure('to')[4])
        #         self.stop_image = self.video_slider_canvas.create_image(position, 30, image=self.stop_marker_icon)

        elif action=='delete':
            for i in range(len(self.markers)):
                if self.markers[i]['frame'] == self.video_slider.get():
                    self.layer['markers_canvas'].delete(self.markers[i]['icon_ref'])
                    self.markers.pop(i)
                    break

        elif action=='prev':

            temp=[]
            for i in range(len(self.markers)):
                temp.append(self.markers[i]['frame'])
            idx = bisect.bisect_left(temp, self.video_slider.get())

            if idx > 0:
                self.video_slider.set(self.markers[idx-1]['frame'])

                self.add_action('get_requested_video_frame', self.markers[idx-1]['frame'])
                self.parameter_update_from_marker(self.markers[idx-1]['frame'])

        elif action=='next':
            temp=[]
            for i in range(len(self.markers)):
                temp.append(self.markers[i]['frame'])
            idx = bisect.bisect(temp, self.video_slider.get())

            if idx < len(self.markers):
                self.video_slider.set(self.markers[idx]['frame'])

                self.add_action('get_requested_video_frame', self.markers[idx]['frame'])
                self.parameter_update_from_marker(self.markers[idx]['frame'])

        # resize canvas
        else :

            self.layer['markers_canvas'].delete('all')
            width = self.layer['markers_canvas'].winfo_width()-20-40-20

            for marker in self.markers:
                position = 20+int(width*marker['frame']/self.video_slider.get_length())
                marker['icon_ref'] = self.layer['markers_canvas'].create_line(position,0, position, 15, fill='light goldenrod')

    #region [#111111b4]

    def save_markers_json(self):

        if len(self.markers) == 0 or len(self.media_file_name) == 0:
            return
        json_file_path = os.path.join(self.json_dict["source videos"], self.media_file_name[0] + "_markers.json")
        # Save the markers to the JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(self.markers, json_file)
            print('Markers saved')

    def load_markers_json(self):
        if len(self.media_file_name) == 0:
            return
        json_file_path = os.path.join(self.json_dict["source videos"], self.media_file_name[0] + "_markers.json")
        if os.path.exists(json_file_path):
            # Load the markers from the JSON file
            with open(json_file_path, 'r') as json_file:
                loaded_markers = json.load(json_file)

            # Define update rules for parameters using lambda functions returning a list of key(s) to update
            # By default keys that do not exist in the loaded_markers will take the value currently in "parameters"
            update_rules = {
                # Example: Force TensorRT (previously no value, if not specified would default to current parameters in UI)
                #"ProvidersPriorityTextSel": lambda value, loaded_marker: {
                #    "ProvidersPriorityTextSel": "TensorRT",
                #},
                # Fix Restorer with Alucard values
                "RestorerTypeTextSel": lambda value, loaded_marker: {
                    "RestorerTypeTextSel": {
                        "GFPGAN": "GFPGAN-v1.4",
                        "CF": "CodeFormer",
                        "GPEN256": "GPEN-256",
                        "GPEN512": "GPEN-512"
                    }.get(value, value)  # Default to the original value if no match
                },
                "Restorer2TypeTextSel": lambda value, loaded_marker: {
                    "Restorer2TypeTextSel": {
                        "GFPGAN": "GFPGAN-v1.4",
                        "CF": "CodeFormer",
                        "GPEN256": "GPEN-256",
                        "GPEN512": "GPEN-512"
                    }.get(value, value)  # Default to the original value if no match
                },

                # Fix Face Parser Mouth Slider which is more granular now.
                # Split former MouthSlider in two equal parts and assign to upper/lower lips.
                "MouthParserSlider": lambda value, loaded_marker: (
                    {
                        "MouthParserSlider": max(5, value),
                        "UpperLipParserSlider": value // 2 if value > 0 else 8,
                        "LowerLipParserSlider": value // 2 if value > 0 else 8
                    # Only update if these keys didn't exist in the in loaded parameters
                    } if not {"UpperLipParserSlider", "LowerLipParserSlider"} & loaded_marker.keys() else {
                        # Otherwise we still need to give a value to the key otherwise it will not be loaded.
                        "MouthParserSlider": value,
                    }
                ),
            }

            # Update markers with existing parameters and update rules
            updated_markers = []
            for loaded_marker in loaded_markers:
                updated_parameters = {}
                rules_updated_keys = set()  # Track parameters that have been updated
                for key in self.parameters:
                    # Get the current value from the marker or use the default
                    value = loaded_marker['parameters'].get(key, self.parameters[key])

                    # Apply update rules if available
                    if key in update_rules:
                        updates = update_rules[key](value, loaded_marker['parameters'])
                        for update_key, update_value in updates.items():
                            updated_parameters[update_key] = update_value
                            rules_updated_keys.add(update_key)
                    else:
                        if key not in rules_updated_keys:
                            updated_parameters[key] = value

                updated_marker = {
                    'frame': loaded_marker['frame'],
                    'parameters': updated_parameters,
                    'icon_ref': loaded_marker.get('icon_ref')  # Preserve icon_ref if it exists
                }
                updated_markers.append(updated_marker)

            self.markers = updated_markers
            self.add_action("update_markers_canvas", self.markers)

    def update_markers_canvas(self):
        self.layer['markers_canvas'].delete('all')
        width = self.layer['markers_canvas'].winfo_width()-20-40-20
        for marker in self.markers:
            position = 20+int(width*marker['frame']/self.video_slider.get_length())
            marker['icon_ref'] = self.layer['markers_canvas'].create_line(position,0, position, 15, fill='light goldenrod')

    #endregion

    def toggle_stop(self):
        if self.stop_marker == self.video_slider.self.timeline_position:
            self.stop_marker = []
            self.add_action('set_stop', -1)
            self.video_slider_canvas.delete(self.stop_image)
        else:
            self.video_slider_canvas.delete(self.stop_image)
            self.stop_marker = self.video_slider.self.timeline_position
            self.add_action('set_stop', self.stop_marker)

            width = self.video_slider_canvas.winfo_width()-30
            position = 15+int(width*self.video_slider.self.timeline_position/self.video_slider.configure('to')[4])
            self.stop_image = self.video_slider_canvas.create_image(position, 30, image=self.stop_marker_icon)

    def save_image(self):
        if len(self.media_file_name) > 0:
            filename =  self.media_file_name[0]+"_"+str(time.time())[:10]
            filename = os.path.join(self.json_dict["saved videos"], filename)
            cv2.imwrite(filename+'.png', cv2.cvtColor(self.video_image, cv2.COLOR_BGR2RGB))
            print('Image saved as:', filename+'.png')

    def remove_target_media_from_list(self, path):

        found_media_index = -1
        for i in range(len(self.target_media_buttons)):
            if hasattr(self.target_media_buttons[i], "media_file") and self.target_media_buttons[i].media_file == path:
                found_media_index = i
                break

        # If a matching media item is found, remove it
        if found_media_index != -1:
            self.target_media.pop(found_media_index)
            self.target_media_buttons.pop(found_media_index)

            # Redraw all remaining items (this is an alternative to repositioning)
            self.redraw_target_media_canvas()
            current_button_index = self.find_currently_selected_target_media_index()

            if current_button_index != -1:
                self.scroll_to_target_media(self.target_media_buttons[current_button_index].item_id)
        

    def delete_target_media(self, path):

        self.remove_target_media_from_list(path)

        try:
            # Try to import send2trash module
            from send2trash import send2trash

                # If import successful, use send2trash to send file to trash
            send2trash(path)
            message = f"File '{path}' sent to trash/recycle bin successfully."
            print(message)

        except:
            # If send2trash module not available, delete file permanently
            os.remove(path)
            message = f"File '{path}' deleted permanently. If you want to send to trash/recycle, consider installing send2trash (pip install send2trash)."
            print(message)

    def set_delete_media_button_confirm_message_state(self, new_state):
        
        button = self.widget['DeleteMediaButton']

        if new_state:
            button.enable_button()
            button.button.config(text="Confirm?")
        else:
            button.disable_button()
            button.button.config(text="Delete Media")

    def on_click_delete_media_button(self):

        button = self.widget['DeleteMediaButton']

        if not button:
            return

        if button.state == False:
            self.set_delete_media_button_confirm_message_state(True)

        else:
            if os.path.exists(self.media_file):

                path = self.media_file
                self.select_next_target_media()
                self.delete_target_media(path)

                self.set_delete_media_button_confirm_message_state(False)

    def clear_mem(self):
        self.widget['RestorerSwitch'].set(False)
        self.widget['Restorer2Switch'].set(False)
        self.widget['OccluderSwitch'].set(False)
        self.widget['FaceParserSwitch'].set(False)
        self.widget['CLIPSwitch'].set(False)
        self.toggle_swapper(False)
        self.toggle_enhancer(False)
        self.toggle_faces_editor(False)

        self.models.delete_models()
        torch.cuda.empty_cache()

# Refactor this, doesn't seem very efficient
    def parameter_update_from_marker(self, frame):

        # sync marker data
        temp=[]
        # create a separate list with the list of frame numbers with markers
        for i in range(len(self.markers)):
            temp.append(self.markers[i]['frame'])
        # find the marker frame to the left of the current frame
        idx = bisect.bisect(temp, frame)
        # update UI with current marker state data
        if idx>0:
            # update paramter dict with marker entry
            self.parameters = copy.deepcopy(self.markers[idx-1]['parameters'])

            # Update ui
            for key, value in self.parameters.items():
                self.widget[key].set(self.parameters[key], request_frame=False)

            # self.CLIP_text.delete(0, tk.END)
            # self.CLIP_text.insert(0, self.parameters['CLIPText'])

    def toggle_audio(self):
        self.add_action('play_video', 'stop_from_gui')

        self.widget['AudioButton'].toggle_button()
        self.control['AudioButton'] = self.widget['AudioButton'].get()
        self.add_action('control', self.control)

        if self.widget['TLPlayButton'].get():
            self.add_action('play_video', 'play')

    def toggle_maskview(self):
        self.widget['MaskViewButton'].toggle_button()
        self.control['MaskViewButton'] = self.widget['MaskViewButton'].get()
        self.add_action('control', self.control)
        self.add_action('get_requested_video_frame', self.video_slider.get())

    def toggle_compareview(self):
        self.widget['CompareViewButton'].toggle_button()
        self.control['CompareViewButton'] = self.widget['CompareViewButton'].get()
        self.add_action('control', self.control)
        self.add_action('get_requested_video_frame', self.video_slider.get())

    def scroll_to_item(self, canvas, item_id, margin_in_pixels = 10):
        # Get the bounding box of the item (x1, y1, x2, y2)
        bbox = canvas.bbox(item_id)
        
        if bbox:  # If the item exists            
            # Calculate the horizontal and vertical scrolling needed
            x1, y1, x2, y2 = bbox
            
            # Calculate how much we need to scroll to bring the item into view
            delta_x = max(0, x1 - margin_in_pixels)
            delta_y = max(0, y1 - margin_in_pixels)
            
            # Scroll the canvas to bring the item into view
            canvas.xview_scroll(int(delta_x), "units")
            canvas.yview_scroll(int(delta_y), "units")

            canvas.xview_moveto(delta_x / canvas.bbox("all")[2])  
            canvas.yview_moveto(delta_y / canvas.bbox("all")[3])

    def scroll_to_target_media(self, item_id):
        self.scroll_to_item(self.target_media_canvas, item_id)

        self.target_videos_mouse_wheel(event=0, delta=0) # Update scrollbar

    def find_currently_selected_target_media_index(self):

        new_index = -1
        target_media_buttons_length = len(self.target_media_buttons)
        for i in range(target_media_buttons_length):
            if self.target_media_buttons[i].media_file == self.media_file:
                return i

        return new_index

    def select_adjacent_target_media(self, offset : int):

        if not self.media_file:
            return

        new_index = self.find_currently_selected_target_media_index()

        if new_index == -1: # If nothing selected
            return

        target_media_buttons_length = len(self.target_media_buttons)
        new_index = (new_index + offset) % target_media_buttons_length

        if new_index < 0:
            new_index += target_media_buttons_length

        self.load_target(self.target_media_buttons[new_index].media_file, self.widget['PreviewModeTextSel'].get())
        self.scroll_to_target_media(self.target_media_buttons[new_index].item_id)

    def select_previous_target_media(self):
        self.select_adjacent_target_media(-1)

    def select_next_target_media(self):
        self.select_adjacent_target_media(1)

    def select_random_target_media(self, remove_history = False):

        visible_media_buttons = self.get_visible_media_buttons()

        if remove_history:
            self.target_media_shuffle_history = set()

        # Create a list of indices for visible media buttons
        available_indices = [i for i in range(len(visible_media_buttons)) if i not in self.target_media_shuffle_history]

        # If all indices are used, reset the history and shuffle from all available buttons
        if not available_indices:
            self.target_media_shuffle_history = set()  # Clear history if all have been selected
            available_indices = list(range(len(visible_media_buttons)))

        # Shuffle available indices to ensure randomness
        shuffle(available_indices)

        # Select the first item from the shuffled list
        random_index = available_indices[0]

        # Add the selected index to history
        self.target_media_shuffle_history.add(random_index)

        self.load_target(self.target_media_buttons[random_index].media_file, self.widget['PreviewModeTextSel'].get())
        self.scroll_to_target_media(self.target_media_buttons[random_index].item_id)

    def parameter_io(self, task, initial_dir="."):
        if task == 'save':
            save_file = filedialog.asksaveasfile(mode='w', initialdir=initial_dir, initialfile="startup_parameters.json", defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
            if save_file:
                # Aggiungi config_type e version
                config_data = {
                    "config_type": "parameters",
                    "version": "1.0",
                    "parameters": self.parameters,
                    "parameters_face_editor": self.parameters_face_editor,
                }
                json.dump(config_data, save_file, indent=4)
                save_file.close()

        elif task == 'load':
            try:
                load_file = filedialog.askopenfile(mode='r', initialdir=initial_dir, filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
                if load_file:
                    config_data = json.load(load_file)
                    file_name = load_file.name
                    load_file.close()

                    # Verifica il tipo di configurazione
                    if config_data.get("config_type") != "parameters":
                        print(f"Error: {file_name} has an invalid configuration type!")
                        return

                    # Load parameters from json file and assign them only if exist
                    temp = config_data.get("parameters", {})
                    for key, value in temp.items():
                        if key in self.parameters:
                            self.parameters[key] = value

                    # Load parameters face editor from json file and assign them only if exist
                    temp = config_data.get("parameters_face_editor", {})
                    for key, value in temp.items():
                        if key in self.parameters_face_editor:
                            self.parameters_face_editor[key] = value

                    # Update the UI
                    self.update_ui_with_parameters()

                    # Log the actions
                    self.add_action('parameters', self.parameters)
                    self.add_action('parameters_face_editor', self.parameters_face_editor)
                    self.add_action('control', self.control)
                    self.add_action('get_requested_video_frame', self.video_slider.get())

            except FileNotFoundError:
                print('No save file created yet!')
            except json.JSONDecodeError:
                print('Error decoding JSON file. Please check the file format.')

        elif task == 'default':
            # Update the UI with default values
            self.load_default_parameters()

            # Log the actions
            self.add_action('parameters', self.parameters)
            self.add_action('parameters_face_editor', self.parameters_face_editor)
            self.add_action('control', self.control)
            self.add_action('get_requested_video_frame', self.video_slider.get())

    def update_ui_with_parameters(self):
        for key, value in self.parameters.items():
            self.widget[key].set(value, request_frame=False)
            if key == "ProvidersPriorityTextSel":
                provider_value = self.models.switch_providers_priority(value)
                if provider_value != value:
                    self.widget[key].set(provider_value, request_frame=False)
                else:
                    self.models.delete_models()
                    torch.cuda.empty_cache()
            elif key == "ThreadsSlider":
                self.models.set_number_of_threads(value)

        for key, value in self.parameters_face_editor.items():
            self.widget[key].set(value, request_frame=False)

    def load_default_parameters(self):
        for key, value in self.parameters.items():
            self.widget[key].load_default()

        for key, value in self.parameters_face_editor.items():
            self.widget[key].load_default()

    def findCosineDistance2(self, vector1, vector2):
        cos_dist = 1.0 - np.dot(vector1, vector2)/(np.linalg.norm(vector1)*np.linalg.norm(vector2)) # 2..0

        print(np.dot(vector1, vector2))

        return cos_dist

    def toggle_virtualcam(self, mode, name, use_markers=False):
        self.control[name] =  self.widget[name].get()
        self.add_action('control', self.control)
        if self.control[name]:
            self.add_action('enable_virtualcam')
        else:
            self.add_action('disable_virtualcam')

    def disable_record_button(self):
        self.widget['TLRecButton'].disable_button()
