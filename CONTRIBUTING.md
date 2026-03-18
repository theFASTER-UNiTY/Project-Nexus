# Contribution Guide for Project Nexus

We are excited that you are considering contributing to Project Nexus! Whether it's reporting a bug, suggesting a new feature, or submitting code, your help is invaluable.

## Code of Conduct

Please note that this project is governed by the [Code of Conduct](CODE_OF_CONDUCT). By participating, you are expected to uphold this code.

---

## How to Contribute

There are several ways to contribute, even without writing code:

### 1. Reporting a Bug 🐛

If you encounter a stability issue or an error, please:

* Check the [existing Issues](https://github.com/theFASTER-UNiTY/Project-Nexus/issues) to ensure the bug hasn't already been reported.
* Use the designated **Bug Report** template.
* Be sure to include the following information:
    * **Clear steps to reproduce** the bug.
    * The **application version** and your **operating system**.
    * The **full error message** (if any).

### 2. Suggesting a New Feature ✨

We welcome all suggestions to improve the application!

* Use the **Feature Request** template.
* Clearly explain the **current problem** and the **added value** of the proposed solution.

### 3. Submitting Code Changes (Pull Request - PR) ⚙️

If you wish to submit code (bug fix or new feature), please follow this workflow:

#### Environment Setup

1.  **Fork** the repository.
2.  **Clone** your fork locally:
    ```shell
    git clone https://github.com/theFASTER-UNiTY/Project-Nexus.git
    ```
3.  **Create a virtual environment** and install dependencies:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    ```

#### Contribution Workflow

1.  **Create a new branch** for your changes. The branch name should be descriptive:
    * For a bug fix: `fix/short-bug-description`
    * For a new feature: `feature/new-feature-name`
    ```bash
    git checkout -b feature/my-new-feature
    ```
2.  **Code your changes.**
3.  **Commit** your changes using a clear and concise message (e.g., `feat: Add dark theme option` or `fix: Resolve Errno XX launching issue`).
4.  **Push** your branch to your fork on GitHub.
5.  **Create a Pull Request (PR)**: Go to your fork's page on GitHub and click the "Compare & pull request" button to submit your PR.

---

## Style and Conventions

To ensure clean and maintainable code, please follow these rules:


* **Docstrings**: Document new functions and classes using docstrings.
* **Testing**: If you fix a bug, include a regression test if possible.
* **Versioning**: Never increment or modify the `version.json` file. We manage tags and releases.

Thank you for your interest and support! We look forward to seeing your contributions.
