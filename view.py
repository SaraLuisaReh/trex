# Copyright (c) 2026 Sara Luisa Reh
# Licensed under the GNU General Public License v3.0

import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import threading

from controller import control_analysis
from GLOBAL_PATHS import CURRENT_PATH

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# global variables
dropdown = True
analysis_type = "fastq"
analysis_content=True
bg_dict = {"Dark": "gray17", "Light": "gray86"}
fg_dict = {"Dark":"white", "Light": "black"}
current_bg = bg_dict["Dark"]
current_fg = fg_dict["Dark"]
default_ref_header_dict = {"european":"_european", "non_finnish_european":"_nfe", "overall":""}


class TREX(ctk.CTk):
    def __init__(self, root):
        super().__init__()
        # window configuration
        self.title("T-Rex")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")

        # top label
        self.top_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("#3B8ED0", "#1F6AA5"), height=int(screen_height/6))
        self.top_frame.grid(row=0, column=0, columnspan=5, sticky="nsew")
        self.first_label = ctk.CTkLabel(self.top_frame, width=screen_width, text="T-Rex: Trio Rare Variant Analysis of Exomes", text_color="white", font=ctk.CTkFont(size=20, weight="bold"))
        self.first_label.grid(row=0, column=0, pady=(20, 15))

        # container
        container = ctk.CTkFrame(self, width=screen_width, corner_radius=0)
        container.grid(row=1, column=0, columnspan=5, rowspan=12)

        # Create a container for the pages (frames)
        self.frames = {}
        for page in (WaitingPage, MainPage):
            page_name = page.__name__
            frame = page(parent=container, controller=self, screenwidth=screen_width, screenheight=screen_height)
            self.frames[page_name] = frame
            # Stack frames above each other, but we are giving each frame its own unique row
            frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.show_frame("MainPage")

    def show_frame(self, page_name):
        # Show the requested frame by raising it
        frame = self.frames[page_name]
        frame.tkraise()

    def update_status(self, text):
        waiting_page = self.frames["WaitingPage"]
        waiting_page.status_label.configure(text=text)


class WaitingPage(ctk.CTkFrame):
    def __init__(self, parent, controller, screenwidth, screenheight):
        super().__init__(parent)
        self.controller = controller
        # built frame
        self.waiting_frame = ctk.CTkFrame(self, width=screenwidth-40, corner_radius=0)
        self.waiting_frame.grid(row=0, column=0, rowspan=11, columnspan=5, padx=20, pady=20)
        self.waiting_frame.columnconfigure(0, weight=1)
        self.waiting_frame.rowconfigure(6, weight=1)
        # Add labels
        label_empty_top = ctk.CTkLabel(master=self.waiting_frame, text="", width=screenwidth-40)
        label_empty_top.grid(row=0, column=0, sticky="nsew", pady=10)  # to position the following labels in the middle
        label_wait1 = ctk.CTkLabel(master=self.waiting_frame, text="Please wait while the application is running.", font=ctk.CTkFont(size=22))
        label_wait1.grid(row=1, column=0, padx=10, pady=(20, 10), sticky="nsew")
        label_wait2 = ctk.CTkLabel(self.waiting_frame, text="This can take up to 17 hours per whole-exome sequencing sample.", font=ctk.CTkFont(size=18))
        label_wait2.grid(row=2, column=0, padx=10, pady=(10, 10), sticky="nsew")
        label_wait3 = ctk.CTkLabel(master=self.waiting_frame,
                                  text="You may minimize the app window but please don't close the app or shut down the computer.\nPlease make sure that your battery is sufficiently charged.",
                                  font=ctk.CTkFont(size=15))
        label_wait3.grid(row=3, column=0, padx=10, pady=(30, 30), sticky="nsew")
        # Add status label
        self.status_label = ctk.CTkLabel(master=self.waiting_frame, text="Initializing...",font=ctk.CTkFont(size=15))
        self.status_label.grid(row=4, column=0, padx=10, pady=(30, 30), sticky="nsew")
        # Add progress bar
        progress = ctk.CTkProgressBar(master=self.waiting_frame, orientation="horizontal", width=200, mode="indeterminate")
        progress.grid(row=5, column=0, pady=30, padx=20)
        progress.grid_propagate(False)
        progress.start()
        # Add abort button
        self.abort_button = ctk.CTkButton(master=self.waiting_frame, text="Stop analysis after the current step", command=lambda: self.abort(), font=ctk.CTkFont(size=14))
        self.abort_button.grid(row=6, column=0, pady=30, padx=20)
        label_empty_bottom = ctk.CTkLabel(master=self.waiting_frame, text="", width=screenwidth-40)
        label_empty_bottom.grid(row=7, column=0, sticky="nsew", pady=10)

    # Abort button
    def abort(self):
        self.abort_button.configure(state="disabled")  # prevent double clicks
        self.status_label.configure(text="Stopping analysis safely after the current step is completed...")
        self.controller.frames["MainPage"].stop_event.set()


class MainPage(ctk.CTkFrame):
    def __init__(self, parent, controller, screenwidth, screenheight):
        super().__init__(parent)
        self.controller = controller
        self.stop_event = threading.Event()
        # top menu
        # ("#3B8ED0", "#1F6AA5")
        self.top_menu_frame = ctk.CTkFrame(self, corner_radius=0, height=int(screenheight/6))
        self.top_menu_frame.grid(row=0, column=1, columnspan=1, sticky="nsew")
        self.analysis_button = ctk.CTkButton(self.top_menu_frame, text="New Analysis", height=40, font=ctk.CTkFont(size=17),text_color="white",corner_radius=0, command=self.analysis_button_event)
        self.analysis_button.grid(row=0, column=1, padx=5, pady=2)
        self.right_top_menu_frame = ctk.CTkFrame(self, corner_radius=0, height=int(screenheight/6))
        self.right_top_menu_frame.grid(row=0, column=3, columnspan=2, sticky="nsw")
        self.information_button = ctk.CTkButton(self.right_top_menu_frame, text="Information about \n Analysis Settings",height=40, font=ctk.CTkFont(size=14), text_color="white", corner_radius=0, command=lambda : self.information_button_event())
        self.information_button.grid(row=0, column=0, padx=4, pady=2)
        self.about_button = ctk.CTkButton(self.right_top_menu_frame, text="About this Project", height=40, font=ctk.CTkFont(size=14), text_color="white", corner_radius=0, command=self.about_button_event)
        self.about_button.grid(row=0, column=1, padx=1, pady=2)

        # start sidebar
        self.sidebar()

        # start mainbar
        self.main_bar(screenheight)

        # Create content frames once
        self.analysis_content_frame = self.create_analysis_content()
        self.analysis_content_frame.grid(row=0, column=0, sticky="nsew")

        self.info_content_frame = self.create_information_content()
        self.info_content_frame.grid(row=0, column=0, sticky="nsew")
        self.info_content_frame.grid_forget()  # hidden initially

        self.about_content_frame = self.create_about_content(screenwidth)
        self.about_content_frame.grid(row=0, column=0, sticky="nsew")
        self.about_content_frame.grid_forget()

        # Show the default content
        self.show_content("analysis")

    def show_content(self, content_name):
        # Hide all frames first
        for frame in [self.analysis_content_frame, self.info_content_frame, self.about_content_frame]:
            frame.grid_forget()

        # Show the requested frame
        if content_name == "analysis":
            self.analysis_content_frame.grid(row=0, column=0, sticky="nsew")
        elif content_name == "info":
            self.info_content_frame.grid(row=0, column=0, sticky="nsew")
        elif content_name == "about":
            self.about_content_frame.grid(row=0, column=0, sticky="nsew")

    def sidebar(self):
        # frame
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=11, sticky="nsew")

        # label
        self.top_label = ctk.CTkLabel(self.sidebar_frame, text="Select a File Type",
                                                 font=ctk.CTkFont(size=18, weight="bold"))
        self.top_label.grid(row=2, column=0, padx=50, pady=(50, 20))

        # buttons
        self.sidebar_fastq = ctk.CTkButton(self.sidebar_frame, text="FASTQ File", font=ctk.CTkFont(size=15),
                                          text_color="white", command=self.fastq_button_event)
        self.sidebar_fastq.grid(row=3, column=0, padx=20, pady=10)
        self.sidebar_BAM = ctk.CTkButton(self.sidebar_frame, text="BAM File",font=ctk.CTkFont(size=15),text_color="white", command=self.bam_button_event)
        self.sidebar_BAM.grid(row=4, column=0, padx=20, pady=10)
        self.sidebar_vcf = ctk.CTkButton(self.sidebar_frame, text="VCF File",font=ctk.CTkFont(size=15),text_color="white", command=self.vcf_button_event)
        self.sidebar_vcf.grid(row=5, column=0, padx=20, pady=10)
        self.sidebar_csv = ctk.CTkButton(self.sidebar_frame, text="CSV File",font=ctk.CTkFont(size=15),text_color="white", command=self.csv_button_event)
        self.sidebar_csv.grid(row=6, column=0, padx=20, pady=10)
        self.sidebar_tsv = ctk.CTkButton(self.sidebar_frame, text="TSV File",font=ctk.CTkFont(size=15),text_color="white", command=self.tsv_button_event)
        self.sidebar_tsv.grid(row=7, column=0, padx=20, pady=10)

        # change appearance
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark","Light"], command=self.change_appearance_event)
        self.appearance_mode_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 50))

    def main_bar(self, screenheight):
        # scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(master=self, corner_radius=0, height=int(screenheight-1/3*screenheight))
        self.scrollable_frame.grid(row=2, column=1, rowspan=11,columnspan=4, sticky="nsew", padx=20, pady=20)

        self.grid_rowconfigure(2, weight=1)  # Allow vertical expansion
        self.grid_columnconfigure(1, weight=1)  # Allow horizontal expansion

        ## create analysis content
        self.analysis_content = self.create_analysis_content()
        self.analysis_content.grid(row=0, column=0, sticky="nsew")

    def create_analysis_content(self):
        analysis_frame = ctk.CTkFrame(self.scrollable_frame)
        bg_color = analysis_frame.cget("bg_color")
        self.info_label = ctk.CTkLabel(master=analysis_frame, text="1. Step: Please choose the right file format in the sidebar on the left",font=ctk.CTkFont(size=16, weight="bold"))
        self.info_label.grid(row=1, column=1, columnspan=2, padx=(50,20), pady=(20,10), sticky="w")
        # "Upload" Label
        self.upload_label = ctk.CTkLabel(master=analysis_frame, text="2. Step: Upload FASTQ Files",font=ctk.CTkFont(size=16, weight="bold"))
        self.upload_label.grid(row=2, column=1, padx=(50,20), pady=(15,5), sticky="w")
        self.upload_pathfield = self.create_path_entry(
            analysis_frame,
            row=3,
            label_text="Please enter the path to the folder where the files \n are stored that you wish to analyze:",
            browse_command=self.browse_folder
        )
        # Create output fields
        self.output_label = ctk.CTkLabel(master=analysis_frame, text="3. Step: Define the Output Directory",
                                         font=ctk.CTkFont(size=16, weight="bold"))
        self.output_label.grid(row=4, column=1, padx=50, pady=(20,5), sticky="nw")
        self.output_pathfield = self.create_path_entry(
            analysis_frame,
            row=5,
            label_text="Please enter the folder path where the output should be stored:",
            browse_command=self.browse_output_folder
        )

        # Set cutoff for rare variants
        self.cutoff_label = ctk.CTkLabel(master=analysis_frame, text="4. Step: Choose the allele frequency cutoff",
                                         font=ctk.CTkFont(size=16, weight="bold"))
        self.cutoff_label.grid(row=6, column=1,columnspan=2, padx=50, pady=(20,5), sticky="nw")
        self.cutoff_info = ctk.CTkLabel(master=analysis_frame, text="Only return variants where the allele frequency \n of the population is less than:",
                                                     font=ctk.CTkFont(size=14, slant="italic"))
        self.cutoff_info.grid(row=7, column=1, padx=50, pady=5, sticky="nw")
        self.entry_field = ctk.CTkEntry(analysis_frame, width=60)
        self.entry_field.grid(row=7, column=2, padx=(10,0), pady=5, sticky="nw")
        # set default cutoff to 5.0
        self.entry_field.insert(0, "5.0")
        percentage_label = ctk.CTkLabel(analysis_frame, text="%", width=20)
        percentage_label.grid(row=7, column=2, padx=(70,0), pady=5,sticky="nw")
        # Add validation for cutoff entries
        vcmd = self.register(self.validate_cutoff_entry)
        self.entry_field.configure(validate="key", validatecommand=(vcmd, "%P"))
        # Choose reference population
        self.ref_pop_label = ctk.CTkLabel(master=analysis_frame,
                                        text="Please choose the reference population:",
                                        font=ctk.CTkFont(size=14, slant="italic"))
        self.ref_pop_label.grid(row=8, column=1, padx=50, pady=(5,0), sticky="nw")
        # Create Radiobutton for "European", "Non-Finnish European" and "Overall"
        self.radio_frame = ctk.CTkFrame(master=analysis_frame, fg_color=bg_color)
        self.radio_frame.grid(row=8, column=2, columnspan=3, padx=(10,0), pady=5, sticky="nw")
        self.ref_population = ctk.StringVar(value="european")
        self.radio_european = tk.Radiobutton(master=self.radio_frame, text="European", variable=self.ref_population, value="european", fg=current_fg, bg=current_bg, font=ctk.CTkFont(size=14))
        self.radio_overall = tk.Radiobutton(master=self.radio_frame, text="Overall", variable=self.ref_population, value="overall", fg=current_fg, bg=current_bg, font=ctk.CTkFont(size=14))
        self.radio_non_finnish_european = tk.Radiobutton(master=self.radio_frame, text="Non-Finnish European", variable=self.ref_population, value="non_finnish_european", fg=current_fg, bg=current_bg, font=ctk.CTkFont(size=14))
        self.radio_european.grid(row=0, column=0, padx=(10, 0), pady=5, sticky="w")
        self.radio_non_finnish_european.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="w")
        self.radio_overall.grid(row=0, column=2, padx=(10, 0), pady=5, sticky="w")

        # Additional Options
        self.options_label = ctk.CTkLabel(master=analysis_frame, text="5. Step: Specify additional options for filtering variants",
                                         font=ctk.CTkFont(size=16, weight="bold"))
        self.options_label.grid(row=9, column=1, padx=50, pady=(25, 5), sticky="nw")
        self.options_dropdown_button = ctk.CTkButton(analysis_frame, text="+", command=lambda: self.options_dropdown(), font=ctk.CTkFont(size=15), width=30, height=30)
        self.options_dropdown_button.grid(row=10, column=1, padx=90, pady=(5, 0), sticky="nw")
        # create checkbox
        self.checkbox_frame = ctk.CTkFrame(master=analysis_frame, fg_color=bg_color)
        self.checkbox_frame.grid(row=11, column=1, padx=50, pady=(0, 20), sticky="nw", columnspan=2)
        self.checkbox_1 = ctk.CTkCheckBox(master=self.checkbox_frame, text="Only homozygous variants")
        self.checkbox_1.grid(row=0, column=1, pady=(20, 0), padx=50, sticky="nw")
        self.checkbox_2 = ctk.CTkCheckBox(master=self.checkbox_frame,  text="Only de novo variants")
        self.checkbox_2.grid(row=1, column=1, pady=(20, 0), padx=50, sticky="nw")
        self.checkbox_3 = ctk.CTkCheckBox(master=self.checkbox_frame,text="Only variants in CpG islands")
        self.checkbox_3.grid(row=2, column=1, pady=(20, 0), padx=50, sticky="nw")
        self.checkbox_4 = ctk.CTkCheckBox(master=self.checkbox_frame,text="Only protein coding variants")
        self.checkbox_4.grid(row=3, column=1, pady=(20, 0), padx=50, sticky="nw")
        self.checkbox_5 = ctk.CTkCheckBox(master=self.checkbox_frame, text="Only variants that are significant in Trio Disequilibrium Test")
        self.checkbox_5.grid(row=4, column=1, columnspan=2, pady=(20, 0), padx=50, sticky="nw")
        self.checkbox_6 = ctk.CTkCheckBox(master=self.checkbox_frame, text="Only variants that are significant in Chi Square Test")
        self.checkbox_6.grid(row=5, column=1,columnspan=2, pady=(20, 0), padx=50, sticky="nw")
        # create submit button
        self.submit_button = ctk.CTkButton(analysis_frame, text="Submit", command=lambda: self.submit(), font=ctk.CTkFont(size=16, weight="bold"), height=40)
        self.submit_button.grid(row=10, column=4, padx=(0,0), pady=(0, 0), sticky="ne")
        # create warning label
        self.warning_label = ctk.CTkLabel(master=analysis_frame,
                                        text="Please enter a file or folder path",
                                        font=ctk.CTkFont(size=13, slant="italic"))

        return analysis_frame

    def create_information_content(self):
        info_frame = ctk.CTkFrame(self.scrollable_frame)
        info_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        title_font = ctk.CTkFont(size=18, weight="bold")
        header_font = ctk.CTkFont(size=15, weight="bold")
        text_font = ctk.CTkFont(size=13)

        # Title
        title_label = ctk.CTkLabel(
            master=info_frame,
            text="Information about Analysis Settings",
            font=title_font
        )
        title_label.grid(row=0, column=0, sticky="w", padx=50, pady=(10, 15))

        # Intro text
        intro_text = (
            'To start a new analysis, click the "New Analysis" button and follow '
            "the instructions in the dialog."
        )

        intro_label = ctk.CTkLabel(
            master=info_frame,
            text=intro_text,
            wraplength=850,
            justify="left",
            font=text_font
        )
        intro_label.grid(row=1, column=0, sticky="w", padx=50, pady=5)

        # Reference databases
        ref_text = (
            "Filtering by allele frequency in the reference population is based on "
            "data from gnomAD v4.0 (European reference population >582,716 individuals). "
            "Variant pathogenicity annotations are derived from ClinVar."
        )

        ref_label = ctk.CTkLabel(
            master=info_frame,
            text=ref_text,
            wraplength=850,
            justify="left",
            font=text_font
        )
        ref_label.grid(row=2, column=0, sticky="w", padx=50, pady=5)

        # Pipeline header
        pipeline_header = ctk.CTkLabel(
            master=info_frame,
            text="Integrated analysis pipeline:",
            font=header_font
        )
        pipeline_header.grid(row=3, column=0, sticky="w", padx=50, pady=(15, 5))

        pipeline_steps = [
            "• Read preprocessing: Trimmomatic",
            "• Alignment to GRCh38: BWA-MEM",
            "• Post-processing: Picard",
            "• Variant calling: GATK HaplotypeCaller and VarScan2",
            "• Variant annotation: SnpEff / SnpSift",
            "• Quality control is performed after each analysis step"
        ]

        for i, step in enumerate(pipeline_steps):
            label = ctk.CTkLabel(
                master=info_frame,
                text=step,
                anchor="w",
                justify="left",
                font=text_font
            )
            label.grid(row=4 + i, column=0, sticky="w", padx=70, pady=1)

        # Statistics section
        stats_text = (
            "If a statistical test is selected (Chi-square test or Transmission "
            "Disequilibrium Test), multiple testing correction using the "
            "Bonferroni method is automatically applied (alpha<=0.05)."
        )

        stats_label = ctk.CTkLabel(
            master=info_frame,
            text=stats_text,
            wraplength=850,
            justify="left",
            font=text_font
        )
        stats_label.grid(row=10, column=0, sticky="w", padx=50, pady=(15, 5))

        # TSV section header
        tsv_header = ctk.CTkLabel(
            master=info_frame,
            text="TSV/CSV Input Requirements:",
            font=header_font
        )
        tsv_header.grid(row=11, column=0, sticky="w", padx=50, pady=(15, 5))

        tsv_intro = (
            "If the analysis is started with a TSV or CSV file, the following headers must "
            "be present. The order does not matter, but the names must match exactly:"
        )

        tsv_intro_label = ctk.CTkLabel(
            master=info_frame,
            text=tsv_intro,
            wraplength=850,
            justify="left",
            font=text_font
        )
        tsv_intro_label.grid(row=12, column=0, sticky="w", padx=50, pady=5)

        headers = [
            "• sample",
            "• location (format: chromosome:position (e.g. 9:141950, no 'chr'))",
            "• ref (reference base)",
            "• alt (alternate/variant base)",
            "• biotype (protein coding variants must be 'protein_coding')",
            "• af_c (allele frequency of the child (decimal ≤ 1.0))",
            "• af_f (allele frequency of the father)",
            "• af_m (allele frequency of the mother)",
            "• gnomad_af (allele frequency in the reference population)",
            "• gnomad_an (allele number in the reference population)"
        ]

        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                master=info_frame,
                text=header,
                anchor="w",
                justify="left",
                font=text_font
            )
            label.grid(row=13 + i, column=0, sticky="w", padx=70, pady=1)

        # Recommendation
        recommendation_text = (
            "Because the TSV and CSV format is very strict, it is strongly recommended "
            "to start the pipeline using a BAM or VCF file whenever possible."
        )

        recommendation_label = ctk.CTkLabel(
            master=info_frame,
            text=recommendation_text,
            wraplength=850,
            justify="left",
            font=text_font
        )
        recommendation_label.grid(row=24, column=0, sticky="w", padx=50, pady=(15, 10))

        return info_frame

    def create_about_content(self, screenwidth):
        about_frame = ctk.CTkFrame(self.scrollable_frame)
        about_label = ctk.CTkLabel(master=about_frame, text="About this Project", font=ctk.CTkFont(size=18, weight="bold"))
        about_label.grid(row=0, column=0, padx=50, pady=(20, 10), sticky="w")
        about_text = (
            "T-Rex is a desktop application for standardized and local analysis of whole exome "
            "sequencing germline trio data.\n\n"
            "It allows users to process FASTQ, BAM, VCF, CSV, and TSV files with customizable "
            "filtering options for variant type, statistical significance, and population allele "
            "frequency based on the gnomAD database.\n\n"
            "This desktop application was developed at the Department of Pediatrics at the "
            "Technical University of Munich. \n"
            "Contributors: Sara-Luisa Reh, Carolin Walter, Judith Lohse, Tabita Ghete, "
            "Markus Metzler, Anne Quante, Arndt Borkhardt, Julia Hauer, Franziska Auer \n"
            "Logo design: Anne-Christine Reh \n"
        )
        about_text_label = ctk.CTkLabel(
            master=about_frame,
            text=about_text,
            wraplength=850,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=15)
        )
        about_text_label.grid(row=1, column=0, sticky="w", pady=(0, 5), padx=50)
        contact_heading = "Contact Details:"
        name_line = "Name: Sara-Luisa Reh"
        email_line = "Mail Address: sara-luisa.reh@tum.de"


        # Add content to scrollable frame using grid
        ctk.CTkLabel(about_frame, text=contact_heading, font=ctk.CTkFont(size=15, weight="bold")).grid(row=2, column=0,
                                                                                                   sticky="w",
                                                                                                   pady=(5, 5), padx=50)
        ctk.CTkLabel(about_frame, text=name_line, font=ctk.CTkFont(size=15)).grid(row=3, column=0, sticky="w", padx=50)
        ctk.CTkLabel(about_frame, text=email_line, font=ctk.CTkFont(size=15)).grid(row=4, column=0, sticky="w", padx=50)

        return about_frame

    def create_result_content(self, labeltext):
        result_frame = ctk.CTkFrame(self.scrollable_frame)
        label_result = ctk.CTkLabel(master=result_frame, text=labeltext, font=ctk.CTkFont(size=20))
        label_result.grid(row=1, column=0, padx=10, pady=(20, 10), sticky="nsew")
        return result_frame

    def create_path_entry(self, parent, row, label_text, browse_command):
        # Creates a labeled Entry + Browse button row efficiently.
        label = ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=14, slant="italic"))
        label.grid(row=row, column=1, padx=(50, 10), pady=5, sticky="nw")

        entry = ctk.CTkEntry(parent, width=400, placeholder_text="Enter Folder Path")
        entry.grid(row=row, column=2, columnspan=2, padx=10, pady=5, sticky="w")

        button = ctk.CTkButton(parent, text="Browse", command=lambda: browse_command(entry))
        button.grid(row=row, column=4, padx=10, pady=5, sticky="nw")

        return entry

    def reset_analysis_form(self):
        # Clear path entries
        self.upload_pathfield.delete(0, tk.END)
        self.output_pathfield.delete(0, tk.END)
        self.upload_pathfield.configure(placeholder_text="Enter Folder Path")
        self.output_pathfield.configure(placeholder_text="Enter Output Path")
        # Reset cutoff to default
        self.entry_field.delete(0, tk.END)
        self.entry_field.insert(0, "5.0")
        # Reset reference population
        self.ref_population.set("european")
        # Uncheck all checkboxes
        self.checkbox_1.deselect()
        self.checkbox_2.deselect()
        self.checkbox_3.deselect()
        self.checkbox_4.deselect()
        self.checkbox_5.deselect()
        self.checkbox_6.deselect()
        # Hide warning label if visible
        self.warning_label.grid_forget()
        # Reset upload label text
        self.upload_label.configure(
            text="2. Step: Upload FASTQ Files",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        # Reset global analysis type
        global analysis_type
        analysis_type = "fastq"

    def bam_button_event(self):
        self.analysis_button_event()
        global analysis_type
        analysis_type="bam"
        self.upload_label.configure(text="2. Step: Upload BAM Files", font=ctk.CTkFont(size=16, weight="bold"))

    def fastq_button_event(self):
        self.analysis_button_event()
        global analysis_type
        analysis_type="fastq"
        self.upload_label.configure(text="2. Step: Upload FASTQ Files", font=ctk.CTkFont(size=16, weight="bold"))

    def vcf_button_event(self):
        self.analysis_button_event()
        global analysis_type
        analysis_type="vcf"
        self.upload_label.configure(text="2. Step: Upload VCF Files", font=ctk.CTkFont(size=16, weight="bold"))

    def csv_button_event(self):
        self.analysis_button_event()
        global analysis_type
        analysis_type="csv"
        self.upload_label.configure(text="2. Step: Upload CSV File", font=ctk.CTkFont(size=16, weight="bold"))

    def tsv_button_event(self):
        self.analysis_button_event()
        global analysis_type
        analysis_type="tsv"
        self.upload_label.configure(text="2. Step: Upload TSV File", font=ctk.CTkFont(size=16, weight="bold"))

    def analysis_button_event(self):
        self.reset_analysis_form()
        self.show_content("analysis")

    def information_button_event(self):
        self.show_content("info")

    def about_button_event(self):
        self.show_content("about")

    def clear_scrollable_frame(self):
        # Hide all current content in the scrollable frame
        for widget in self.scrollable_frame.winfo_children():
            widget.grid_forget()

    def change_appearance_event(self, new_appearance: str):
        ctk.set_appearance_mode(new_appearance)  # change radiobuttons
        global current_bg, current_fg
        current_bg = bg_dict[new_appearance]
        current_fg = fg_dict[new_appearance]
        for button in [self.radio_overall,self.radio_european, self.radio_non_finnish_european]:
            button.config(bg=current_bg, fg=current_fg)

    def options_dropdown(self):
        # change global dropdown value
        global dropdown
        dropdown = not dropdown
        # if dropdown is now True: show the widgets in checkbox frame
        if dropdown:
            i=0
            for widget in self.checkbox_frame.winfo_children():
                widget.grid(row=i, column=1, pady=(20, 0), padx=50, sticky="nw")
                i+=1
        # if dropdown is false hide the widgets
        else:
            for widget in self.checkbox_frame.winfo_children():
                widget.grid_forget()

    # Function to open file dialog and insert folder path
    def browse_folder(self, upload_pathfield):
        #self.master.update()
        folder_path = filedialog.askdirectory(title="Select a Folder")
        if folder_path:
            upload_pathfield.delete(0, tk.END)  # Clear existing text in the entry
            upload_pathfield.insert(0, folder_path)  # Insert the selected folder path
        #self.master.update()

    def browse_output_folder(self, outputfolder):
        #self.master.update()
        folder_path = filedialog.askdirectory(title="Select a Folder")
        if folder_path:
            outputfolder.delete(0, tk.END)  # Clear existing text in the entry
            outputfolder.insert(0, folder_path)  # Insert the selected folder path
        #self.master.update()

    # validate entry of cutoff percentage
    def validate_cutoff_entry(self,input_value):
        try:
            if input_value=="":
                return True # allow empty input
            # check if the input is a valid percentage (0-100 with decimal)
            value = float(input_value)  # Try to convert to a float
            if 0 <= value <= 100:
                return True  # valid percentage
            else:
                return False
        except ValueError:
            return False  # not a valid number

    def get_checkbox_state(self):
        # store checkbox in a dictionary where the value is true or false
        checkbox_dict = {
            "homozygous": self.checkbox_1.get(),
            "denovo": self.checkbox_2.get(),
            "cpg": self.checkbox_3.get(),
            "protein_coding": self.checkbox_4.get(),
            "tdt": self.checkbox_5.get(),
            "chi_square": self.checkbox_6.get(),
        }
        return checkbox_dict

    # run the analysis
    def run_analysis(self):
        def progress_callback(message):
            self.after(0, lambda: self.controller.update_status(message))
        self.stop_event.clear()  # reset stop event before starting
        option_dict = self.get_checkbox_state()
        ref_pop_suffix = default_ref_header_dict[self.ref_population.get()]  # "_european", "_nfe" or ""
        output_labeltext = control_analysis(self.upload_pathfield.get(), analysis_type, self.output_pathfield.get(),
                                            self.entry_field.get(), ref_pop_suffix, option_dict, progress_callback, self.stop_event)
        # Switch back to main thread to update UI
        self.after(0, lambda: self.show_results(output_labeltext))

    # show analysis results
    def show_results(self, output_labeltext):
        self.controller.show_frame("MainPage")
        #self.clear_scrollable_frame()
        messagebox.showinfo("Result",output_labeltext)
        #result_content = self.create_result_content(output_labeltext)
        #result_content.grid(row=0, column=0, sticky="nsew")

    # Submit button
    def submit(self):
        # check entry
        if self.output_pathfield.get()!="" and self.upload_pathfield.get()!="":
            self.controller.show_frame("WaitingPage")
            # Start background thread
            thread = threading.Thread(target=self.run_analysis)
            thread.start()
        else:
            self.warning_label.grid(row=11, column=4, padx=(0, 0), pady=(0, 0), sticky="ne")


if __name__ == "__main__":
    app = TREX(ctk)
    # load icon
    image_path = os.path.join(CURRENT_PATH, "t_rex_logo.png")
    icon_image = Image.open(image_path)
    photo = ImageTk.PhotoImage(icon_image)
    app.iconphoto(True, photo)
    app.mainloop()
