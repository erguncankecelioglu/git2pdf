import requests
import pkg_resources
import os
import base64
from fpdf import FPDF
from fpdf.enums import XPos, YPos

LINE_WIDTH = 200
CHARS_PER_LINE = 95
output_directory = os.path.join(os.path.expanduser("~"), "git2pdf_output")

os.makedirs(output_directory, exist_ok=True)


def get_json_from_url(url):
    response = requests.get(url)
    json_data = response.json()
    if 'message' in json_data:
        print(f"Error: {json_data['message']}")
    return json_data


def get_branches(owner, repo):
    branches_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
    branches_json = get_json_from_url(branches_url)
    branches = [branch['name'] for branch in branches_json]
    return branches


def get_tree(owner, repo, branch):
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    tree_json = get_json_from_url(tree_url)
    return tree_json


def fetch_file_content(owner, repo, file_path):
    contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    contents_json = get_json_from_url(contents_url)
    if 'content' in contents_json:
        return base64.b64decode(contents_json['content']).decode('utf-8')
    else:
        print(f"Error: Couldn't fetch the contents of file: {file_path}")
    return None


def make_pdf_from_content(file_path, file_content, pdf):
    pdf.add_page()

    pdf.set_font('DejaVuSans', 'B', 12)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(200, 10, txt=f"File: {file_path}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('DejaVuSans', '', 10)

    for raw_line in file_content.split('\n'):
        if not raw_line.strip():
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
    return pdf


def main():
    repo_url = input("Enter the GitHub repository URL: ")

    owner, repo = repo_url.split("github.com/")[-1].split('/')
    try:
        branches = get_branches(owner, repo)
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

    tree = get_tree(owner, repo, selected_branch)

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

    selection = input("\nEnter 'd' to select a directory, 'f' to select a file, or 'c' to create PDF: ")
    selected_files = set()
    while selection != 'c':
        if selection == 'd':
            dir_indices = input(
                "Enter the numbers of the directories you want to select (separated by spaces): ").split()
            for dir_index in dir_indices:
                selected_dir = directories[int(dir_index)]
                print(f"You have selected directory: {selected_dir['path']}")
                for file in files:
                    if file['path'].startswith(selected_dir['path']):
                        selected_files.add(file['path'])
        elif selection == 'f':
            file_indices = input("Enter the numbers of the files you want to select (separated by spaces): ").split()
            for file_index in file_indices:
                selected_file = files[int(file_index)]
                selected_files.add(selected_file['path'])

        selection = input("\nEnter 'd' to select a directory, 'f' to select a file, or 'c' to create PDF: ")

    pdf = FPDF()
    font_path = pkg_resources.resource_filename(__name__, 'DejaVuSans.ttf')
    pdf.add_font("DejaVuSans", style="", fname=font_path)
    pdf.add_font('DejaVuSans', 'B', fname=font_path)
    pdf.set_font("DejaVuSans", size=12)

    for file_path in selected_files:
        file_content = fetch_file_content(owner, repo, file_path)
        if file_content is not None:
            pdf = make_pdf_from_content(file_path, file_content, pdf)

    pdf_path = os.path.join(output_directory, f"{repo}_{selected_branch}.pdf")
    pdf.output(pdf_path)
    print(f"\nPDF created successfully at {pdf_path}!")
    print("Thank you for using git2pdf!")


if __name__ == '__main__':
    main()
