import argparse
import time

import requests
import pkg_resources
import os
import base64
from fpdf import FPDF
from fpdf.enums import XPos, YPos

LINE_WIDTH = 210
CHARS_PER_LINE = 110
output_directory = os.path.join(os.path.expanduser("~"), "git2pdf_output")

os.makedirs(output_directory, exist_ok=True)


def get_json_from_url(url, token=None):
    headers = {}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    response = requests.get(url, headers=headers)
    json_data = response.json()
    if 'message' in json_data:
        print(f"Error: {json_data['message']}")
    return json_data


def get_branches(owner, repo, token=None):
    branches_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
    branches_json = get_json_from_url(branches_url, token)
    branches = [branch['name'] for branch in branches_json]
    return branches


def get_tree(owner, repo, branch, token=None):
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    try:
        tree_json = get_json_from_url(tree_url, token)
        return tree_json
    except requests.exceptions.RequestException:
        print(f"Error: Couldn't fetch the tree of branch: {branch}")
        return None


def fetch_file_content(owner, repo, file_path, token=None):
    contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    contents_json = get_json_from_url(contents_url, token)
    if 'content' in contents_json:
        try:
            content = base64.b64decode(contents_json['content']).decode('utf-8')
            # Replace tabs with four spaces
            content = content.replace('\t', '    ')
            return content
        except (base64.binascii.Error, UnicodeDecodeError):
            print(f"Error: Couldn't decode the contents of file: {file_path}")
    else:
        print(f"Error: Couldn't fetch the contents of file: {file_path}")
    return None


def make_pdf_from_content(file_path, file_content, pdf, shrink=False, hshrink=False, expand=False, hexpand=False):
    pdf.add_page()

    pdf.set_font('DejaVuSans', 'B', 12)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(200, 10, txt=f"File: {file_path}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('DejaVuSans', '', 10)

    if shrink:
        line_width = LINE_WIDTH * 0.9
        chars_per_line = CHARS_PER_LINE * 0.9
    elif hshrink:
        line_width = LINE_WIDTH * 0.8
        chars_per_line = CHARS_PER_LINE * 0.8
    elif expand:
        line_width = LINE_WIDTH * 1.1
        chars_per_line = CHARS_PER_LINE * 1.1
    elif hexpand:
        line_width = LINE_WIDTH * 1.2
        chars_per_line = CHARS_PER_LINE * 1.2
    else:
        line_width = LINE_WIDTH
        chars_per_line = CHARS_PER_LINE

    empty_lines_count = 0  # count of consecutive empty lines
    for raw_line in file_content.split('\n'):
        stripped_line = raw_line.strip()
        if not stripped_line:
            empty_lines_count += 1
            if empty_lines_count > 2:
                continue
            else:
                # This will effectively print an empty line in the PDF
                pdf.cell(line_width, 6, txt=" ", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            empty_lines_count = 0

        # Determine the starting indentation of the line
        indentation = len(raw_line) - len(stripped_line)

        # Process the line word by word
        line = " " * (indentation * 2)  # Add indentation spaces to the line
        words = stripped_line.split()
        for word in words:
            if len(line + " " + word) > chars_per_line:
                pdf.cell(line_width, 6, txt=line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                line = " " * (indentation * 2) + word  # Start a new line with the word
            else:
                line += " " + word

        if line:
            pdf.cell(line_width, 6, txt=line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    return pdf


def main():
    parser = argparse.ArgumentParser(prog='git2pdf', description='Convert a GitHub repository or local directory to PDF')
    parser.add_argument('--auth', metavar='<YOUR_PERSONAL_ACCESS_TOKEN>', help='GitHub Personal Access Token for authentication. Add your token after --auth param.')
    parser.add_argument('--shrink', action='store_true', help='Shrink page and character size slightly')
    parser.add_argument('--hshrink', action='store_true', help='Shrink page and character size more')
    parser.add_argument('--expand', action='store_true', help='Expand page and character size slightly')
    parser.add_argument('--hexpand', action='store_true', help='Expand page and character size more')
    args = parser.parse_args()

    source_type = input("Enter 'g' for GitHub repository, 'l' for local directory: ")

    if args.auth and source_type != 'g':
        print("\nWarning: The authentication token will be ignored since the source type is not a GitHub repository.\n")
        time.sleep(2)

    if source_type == 'g':
        repo_url = input("Enter the GitHub repository URL: ")

        owner, repo = repo_url.split("github.com/")[-1].split('/')
        try:
            token = args.auth if args.auth else None
            branches = get_branches(owner, repo, token)
        except:
            print("Error: Couldn't fetch the branches of the repository.")
            return

        if len(branches) > 1:
            print("\nBranches in the repository:")
            for i, branch in enumerate(branches):
                print(f"{i}: {branch}")
            branch_index = int(input("\nEnter the number of the branch you want to use: "))
            selected_branch = branches[branch_index]
        else:
            selected_branch = branches[0]

        tree = get_tree(owner, repo, selected_branch, token)

        print("\nDirectories and Files in the repository:")

        directories = []
        files = []
        directories_with_files = set()

        for i, item in enumerate(tree['tree']):
            if item['type'] == 'blob':
                files.append(item)
                file_directory = os.path.dirname(item['path'])
                directories_with_files.add(file_directory)
            else:
                directories.append(item)

        for i, directory in enumerate(directories):
            if directory['path'] in directories_with_files:
                print(f"Directory {i}: {directory['path']}")
        print('-------------------------------------------------------')
        print('-------------------------------------------------------')
        for i, file in enumerate(files):
            print(f"File {i}: {file['path']}")

        selection = input("\nEnter 'd' to select a directory, 'f' to select a file, 'a' to select all files or 'c' to create PDF: ")
        selected_files = set()
        while selection != 'c':
            if selection == 'a':
                confirmation = input("Are you sure you want to select all files in all directories? (y/n): ")
                if confirmation == 'y':
                    selected_files = set([file['path'] for file in files])
                    break
            if selection == 'd':
                dir_indices = input(
                    "Enter the numbers of the directories you want to select (separated by spaces): ").split()
                for dir_index in dir_indices:
                    try:
                        selected_dir = directories[int(dir_index)]
                        print(f"You have selected directory: {selected_dir['path']}")
                        for file in files:
                            if file['path'].startswith(selected_dir['path']):
                                selected_files.add(file['path'])
                    except IndexError:
                        print(f"Invalid directory number: {dir_index}. Please enter a valid number.")
            elif selection == 'f':
                file_indices = input(
                    "Enter the numbers of the files you want to select (separated by spaces): ").split()
                for file_index in file_indices:
                    try:
                        selected_file = files[int(file_index)]
                        print(f"You have selected file: {selected_file['path']}")
                        selected_files.add(selected_file['path'])
                    except IndexError:
                        print(f"Invalid file number: {file_index}. Please enter a valid number.")

            selection = input("\nEnter 'd' to select a directory, 'f' to select a file, 'a' to select all files or 'c' to create PDF: ")

        pdf_path = os.path.join(output_directory, f"{repo}_{selected_branch}.pdf")

    elif source_type == 'l':
        current_dir = os.getcwd()
        print(f"Current directory is: {current_dir}")
        files_and_dirs = os.listdir(current_dir)

        files = [f for f in files_and_dirs if os.path.isfile(os.path.join(current_dir, f))]

        print("\nFiles in the current directory:")
        for i, file in enumerate(files):
            print(f"File {i}: {file}")

        file_indices = input("Enter 'a' for select all files or enter the numbers of the files you want to select (separated by spaces): ").split()
        if file_indices == ['a']:
            confirmation = input("Are you sure you want to select all files in the current directory? (y/n): ")
            if confirmation == 'y':
                selected_files = set([os.path.join(current_dir, file) for file in files])
        else:
            selected_files = set()
            for file_index in file_indices:
                try:
                    selected_file = files[int(file_index)]
                    print(f"You have selected file: {selected_file}")
                    selected_files.add(os.path.join(current_dir, selected_file))
                except IndexError:
                    print(f"Invalid file number: {file_index}. Please enter a valid number.")

        pdf_path = os.path.join(output_directory, f"{current_dir.split('/')[-1]}.pdf")

    print("\nProcessing... Please wait.")
    pdf = FPDF()
    font_path = pkg_resources.resource_filename(__name__, 'DejaVuSans.ttf')
    pdf.add_font("DejaVuSans", style="", fname=font_path)
    pdf.add_font('DejaVuSans', 'B', fname=font_path)
    pdf.set_font("DejaVuSans", size=12)

    shrink = args.shrink
    hshrink = args.hshrink
    expand = args.expand
    hexpand = args.hexpand

    for file_path in selected_files:
        if source_type == 'g' or args.auth:
            token = args.auth if args.auth else None
            file_content = fetch_file_content(owner, repo, file_path, token)
            if file_content is not None:
                pdf = make_pdf_from_content(file_path, file_content, pdf, shrink, hshrink, expand, hexpand)
        elif source_type == 'l':
            with open(file_path, 'r') as f:
                try:
                    file_content = f.read()
                    if file_content is not None:
                        pdf = make_pdf_from_content(file_path, file_content, pdf, shrink, hshrink, expand, hexpand)
                except UnicodeDecodeError:
                    print(f"Error: Couldn't read the file {file_path}.")

    pdf.output(pdf_path)
    print(f"\nPDF created successfully!")
    print(f"You can find the PDF at: {pdf_path}")
    print("\nThank you for using git2pdf!")


if __name__ == '__main__':
    main()
