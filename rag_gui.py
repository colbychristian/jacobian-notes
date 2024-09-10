import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import os
import subprocess
import shlex
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io

# Create the main window
root = tk.Tk()
root.title("RAG Document Query System")

# Create frames for layout
frame_left = tk.Frame(root, width=200, bg='lightgrey')
frame_left.pack(side=tk.LEFT, fill=tk.Y)

frame_center = tk.Frame(root)
frame_center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

frame_right = tk.Frame(root, width=300, bg='lightblue')
frame_right.pack(side=tk.RIGHT, fill=tk.Y)

# Listbox for folders and documents
listbox_folders = tk.Listbox(frame_left, bg='white')
listbox_folders.pack(fill=tk.BOTH, expand=True)

# Text widget to display document content
text_document = scrolledtext.ScrolledText(frame_center, wrap=tk.WORD)
text_document.pack(fill=tk.BOTH, expand=True)

# Create a frame for the query input and button
frame_query = tk.Frame(frame_right, bg='lightblue')
frame_query.grid(row=1, column=0, padx=10, pady=(5, 10), sticky='ew')

# Text widget for querying the RAG system
text_query = tk.Entry(frame_query, width=60)  # Adjust the width as needed
text_query.grid(row=0, column=0, sticky='ew', padx=5, pady=5)

# Button for submitting queries
def query_rag():
    query = text_query.get()
    if query:
        try:
            # Safely quote the query string
            quoted_query = shlex.quote(query)
            # Run query_data.py with the user input as a command line argument
            result = subprocess.run(
                ["python", "query_data.py", quoted_query],
                text=True,  # Capture output as a string
                capture_output=True,  # Capture stdout and stderr
                check=True
            )
            # Display results
            text_results.delete(1.0, tk.END)
            text_results.insert(tk.END, result.stdout)
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"An error occurred: {e.stderr}")
    else:
        messagebox.showwarning("Input Error", "Please enter a query.")

# Button for submitting queries
query_button = tk.Button(frame_query, text="Submit Query", command=query_rag)
query_button.grid(row=0, column=1, padx=5, pady=5)

# Text widget for displaying query results
text_results = scrolledtext.ScrolledText(frame_right, wrap=tk.WORD)
text_results.grid(row=0, column=0, padx=10, pady=(10, 5), sticky='nsew')

# Configure grid weights to make the text_results and frame_query expand properly
frame_right.grid_rowconfigure(0, weight=1)  # Ensure text_results expands
frame_right.grid_rowconfigure(1, weight=0)  # Ensure frame_query is below
frame_right.grid_columnconfigure(0, weight=1)  # Ensure the text_query expands with the window
frame_right.grid_columnconfigure(1, weight=0)  # Button column does not expand

# Folder path
data_folder_path = "Data"

# Ensure the "Data" folder exists
if not os.path.exists(data_folder_path):
    os.makedirs(data_folder_path)

# Function to update the document list
def update_document_list():
    listbox_folders.delete(0, tk.END)
    for filename in os.listdir(data_folder_path):
        if filename.endswith(".pdf"):  # Only show PDF files
            listbox_folders.insert(tk.END, filename)

# Function to handle file upload
def upload_files():
    file_paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
    for file_path in file_paths:
        if file_path:
            file_name = os.path.basename(file_path)
            destination_path = os.path.join(data_folder_path, file_name)
            # Copy file to Data folder
            with open(file_path, 'rb') as src_file:
                with open(destination_path, 'wb') as dst_file:
                    dst_file.write(src_file.read())
            # Run populate_database.py
            subprocess.run(["python", "populate_database.py"], check=True)
    # Update the file list
    update_document_list()

upload_files_button = tk.Button(frame_left, text="Upload Files", command=upload_files)
upload_files_button.pack(pady=10)

# Initialize an empty list to store images
page_images = []

# Function to display selected document as images
def on_select_document(event):
    global page_images  # Ensure the list is accessible in this function
    # Use `after` to ensure the function runs after the event processing
    root.after(100, load_document)

def load_document():
    global page_images
    selected_file = listbox_folders.get(tk.ACTIVE)

    if selected_file:
        file_path = os.path.join(data_folder_path, selected_file)
        
        # Debugging: Print the file path
        print(f"Processing file: {file_path}")

        try:
            # Open the PDF with PyMuPDF (fitz)
            pdf_document = fitz.open(file_path)
            text_document.delete(1.0, tk.END)  # Clear the current text widget

            # Clear the list to prevent storing references to old images
            page_images.clear()

            # Check if the document has pages
            if pdf_document.page_count == 0:
                messagebox.showwarning("Warning", "The selected PDF has no pages.")
                return

            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)  # Load a single page
                pix = page.get_pixmap()  # Render the page to an image
                
                # Convert the pixmap to PNG format
                img_data = pix.tobytes("png")
                
                # Open image from bytes for display with PIL
                img = Image.open(io.BytesIO(img_data))

                # Resize image to fit the Tkinter window (optional)
                img = img.resize((612, 792), Image.Resampling.LANCZOS)  # Adjust size as needed

                # Convert the image to a Tkinter-compatible format
                img_tk = ImageTk.PhotoImage(img)

                # Store the image reference in the list to prevent garbage collection
                page_images.append(img_tk)

                # Display the image in the text widget
                text_document.image_create(tk.END, image=img_tk)

                # Optionally, insert page breaks between pages
                text_document.insert(tk.END, f"\n--- Page {page_num + 1} ---\n\n")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF: {str(e)}")

# Ensure the function is correctly bound to the listbox selection event
listbox_folders.bind('<<ListboxSelect>>', on_select_document)

# Run the application
update_document_list()
root.mainloop()