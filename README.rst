==========
git2pdf
==========

git2pdf is a simple Python script that fetches the contents of files in a GitHub repository and generates a PDF with those contents.

Installation
============

git2pdf can be installed via pip:

.. code-block:: bash

    $ pip install git2pdf

Usage
=====

To use git2pdf, simply run the command and follow the prompts:

.. code-block:: bash

    $ git2pdf [--auth <YOUR_PERSONAL_ACCESS_TOKEN>] [--shrink] [--hshrink] [--expand] [--hexpand]

Optional arguments:
- `--auth <YOUR_PERSONAL_ACCESS_TOKEN>`: GitHub Personal Access Token for authentication. Only required for private repositories.
- `--shrink`: Shrink page and character size slightly.
- `--hshrink`: Shrink page and character size more.
- `--expand`: Expand page and character size slightly.
- `--hexpand`: Expand page and character size more.

When prompted, enter 'g' to select a GitHub repository or 'l' to select a local directory. Follow the subsequent prompts to select the branches, directories, and files to include in the PDF.

The generated PDF will be saved in the `git2pdf_output` directory located in the user's home directory.

Example Usage
=============

To convert a GitHub repository to PDF with authentication:

.. code-block:: bash

    $ git2pdf --auth <YOUR_PERSONAL_ACCESS_TOKEN>

To convert a local directory to PDF:

.. code-block:: bash

    $ git2pdf

Note: The authentication token is only required for private repositories or if you have exceeded the GitHub API rate limit.

Contributing
============

Contributions are welcome! Please feel free to open a pull request or submit an issue for any improvements or feature requests.

License
=======

This project is licensed under the MIT License. See the `LICENSE` file for more details.
