import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
import webbrowser

# Set appearance mode and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Jacobian Notes Generator")
        self.geometry("400x300")

        # Create frames
        self.frame_left = ctk.CTkFrame(self, width=100, corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nsew")
        self.frame_right = ctk.CTkFrame(self, width=100, corner_radius=0)
        self.frame_right.grid(row=0, column=1, sticky="nsew")

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Create Listbox within CTkFrame
        self.listbox_data_frame = ctk.CTkFrame(self.frame_left)
        self.listbox_data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.listbox_data = tk.Listbox(self.listbox_data_frame, bg="white", selectmode=tk.MULTIPLE)
        self.listbox_data.pack(fill=tk.BOTH, expand=True)

        self.listbox_notes_frame = ctk.CTkFrame(self.frame_right)
        self.listbox_notes_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.listbox_notes = tk.Listbox(self.listbox_notes_frame, bg="white")
        self.listbox_notes.pack(fill=tk.BOTH, expand=True)

        # Folder paths
        self.data_folder_path = "data"
        self.notes_folder_path = "notes"

        # Ensure the folders exist
        os.makedirs(self.data_folder_path, exist_ok=True)
        os.makedirs(self.notes_folder_path, exist_ok=True)

        # Buttons
        self.upload_files_button = ctk.CTkButton(self.frame_left, text="Upload Class Materials", command=self.upload_files)
        self.upload_files_button.pack(pady=10, padx=10)

        self.remove_files_button = ctk.CTkButton(self.frame_left, text="Remove", command=self.remove_files)
        self.remove_files_button.pack(pady=10, padx=10)

        self.generate_study_notes_button = ctk.CTkButton(self.frame_right, text="Generate Study Notes", command=self.generate_study_notes)
        self.generate_study_notes_button.pack(pady=10, padx=10)

        # Initialize the document lists
        self.update_document_list(self.listbox_data, self.data_folder_path)
        self.update_document_list(self.listbox_notes, self.notes_folder_path)

    # Function to update the document list
    def update_document_list(self, listbox, folder_path):
        listbox.delete(0, tk.END)
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):  # Only show PDF files
                listbox.insert(tk.END, filename)

    # Function to handle file upload
    def upload_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        for file_path in file_paths:
            if file_path:
                file_name = os.path.basename(file_path)
                destination_path = os.path.join(self.data_folder_path, file_name)
                # Copy file to Data folder
                with open(file_path, 'rb') as src_file:
                    with open(destination_path, 'wb') as dst_file:
                        dst_file.write(src_file.read())
        # Run populate_database.py
        subprocess.run(["python", "populate_database.py"], check=True)
        # Update the file list
        self.update_document_list(self.listbox_data, self.data_folder_path)

    # Function to remove files
    def remove_files(self):
        selected_items = self.listbox_data.curselection()
        files_to_remove = [self.listbox_data.get(i) for i in selected_items]

        if files_to_remove:
            try:
                # Call remove_documents.py as a subprocess with the selected files
                subprocess.run(["python", "remove_documents.py"] + files_to_remove, check=True)

                # Remove the files from the data folder
                for file_name in files_to_remove:
                    file_path = os.path.join(self.data_folder_path, file_name)
                    if os.path.exists(file_path):
                        os.remove(file_path)

                # Update the file list after removal
                self.update_document_list(self.listbox_data, self.data_folder_path)
                messagebox.showinfo("Success", "Selected files have been removed.")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
        else:
            messagebox.showwarning("Warning", "Please select files to remove.")

    # Button to generate study notes
    def generate_study_notes(self):
        try:
            subprocess.run(["python", "query_data.py"], check=True)
            # Update the notes list
            self.update_document_list(self.listbox_notes, self.notes_folder_path)
            
            # Attempt to open the generated PDF automatically
            pdf_path = os.path.join(self.notes_folder_path, "study_notes.pdf")
            if os.path.exists(pdf_path):
                webbrowser.open(pdf_path)
            
            messagebox.showinfo("Success", "Study notes generated successfully.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()