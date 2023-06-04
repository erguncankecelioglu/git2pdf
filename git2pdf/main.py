import requests
import pkg_resources
import os
import base64
from fpdf import FPDF
from fpdf.enums import XPos, YPos


def main():
    # Get repository URL from the user
    repo_url = input("Enter the GitHub repository URL: ")
    # Constants for text
    LINE_WIDTH = 200
    CHARS_PER_LINE = 95
    # Extract the owner and repo names from the URL
    owner, repo = repo_url.split("github.com/")[-1].split('/')

    # Specify the directory where you want to save the PDF
    output_directory = os.path.join(os.path.expanduser("~"), "git2pdf_output")

    # Ensure the directory exists (if not, create it)
    os.makedirs(output_directory, exist_ok=True)

    try:
        # Fetch the file tree
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
        tree_response = requests.get(tree_url)
        tree = tree_response.json()

        if 'message' in tree:
            raise Exception(tree['message'])

        # Initialize a PDF
        pdf = FPDF()
        font_path = pkg_resources.resource_filename(__name__, 'DejaVuSans.ttf')
        pdf.add_font("DejaVuSans", style="", fname=font_path)
        pdf.add_font('DejaVuSans', 'B', fname=font_path)
        pdf.set_font("DejaVuSans", size=12)

        # Provide file selection options to the user
        print("\nFiles in the repository:")
        for i, file in enumerate(tree['tree']):
            if file['type'] == 'blob':
                print(f"{i}: {file['path']}")
        file_indices = input(
            "\nEnter the numbers of the files you want to include (separated by spaces), or 'all' to include all files: ")

        include_all = file_indices.lower() == 'all'

        if not include_all:
            file_indices = list(map(int, file_indices.split()))

        # Loop through all files in the tree
        for i, file in enumerate(tree['tree']):
            if file['type'] == 'blob':  # We only want files, not directories
                if include_all or i in file_indices:
                    # Fetch the file contents
                    contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file['path']}"
                    contents_response = requests.get(contents_url)
                    contents = contents_response.json()

                    if 'content' not in contents:
                        print(f"Couldn't fetch the contents of file: {file['path']}")
                        continue

                    # Try to decode the file contents from base64
                    try:
                        decoded_contents = base64.b64decode(contents['content']).decode('utf-8')
                    except UnicodeDecodeError:
                        print(f"Warning: Could not process file {file['path']}. Skipping...")
                        continue

                    # Add a new page to the PDF for this file
                    pdf.add_page()

                    # Add a cell for the file path
                    pdf.set_font('DejaVuSans', 'B', 12)  # Set font to bold
                    pdf.set_text_color(0, 0, 255)  # Set text color to blue
                    pdf.cell(200, 10, txt=f"File: {file['path']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
                    pdf.set_text_color(0, 0, 0)  # Reset text color to black
                    pdf.set_font('DejaVuSans', '', 10)  # Reset font to normal

                    # Add cells for each line of the file
                    for raw_line in decoded_contents.split('\n'):
                        if not raw_line.strip():  # skip over empty lines
                            continue
                        words = raw_line.split()
                        line = words.pop(0)

                        for word in words:
                            if len(line + ' ' + word) <= CHARS_PER_LINE:
                                line += ' ' + word
                            else:
                                pdf.cell(LINE_WIDTH, 10, txt=line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                                line = word

                        pdf.cell(LINE_WIDTH, 10, txt=line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Construct the full path to the PDF file
        pdf_path = os.path.join(output_directory, f"{repo}.pdf")

        # Save the PDF
        pdf.output(pdf_path)

        print(f"\nPDF created successfully at {pdf_path}!")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()
