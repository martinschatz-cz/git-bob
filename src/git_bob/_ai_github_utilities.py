# This module contains utility functions for interacting with GitHub issues and pull requests using AI.
# It includes functions for setting up AI remarks, commenting on issues, reviewing pull requests, and solving issues.
import warnings
from ._logger import Log
import os

AGENT_NAME = os.environ.get("GIT_BOB_AGENT_NAME", "git-bob")
SYSTEM_PROMPT = os.environ.get("SYSTEM_MESSAGE", f"You are an AI-based coding assistant named {AGENT_NAME}. You are an excellent Python programmer and software engineer.")


def setup_ai_remark():
    """
    Set up the AI remark for comments.

    Returns
    -------
    str
        The AI remark string.
    """
    from git_bob import __version__
    from ._utilities import Config
    model = Config.llm_name
    run_id = Config.run_id
    repository = Config.repository
    if run_id is not None:
        link = f""", [log](https://github.com/{repository}/actions/runs/{run_id})"""
    else:
        link = ""
    if AGENT_NAME != "git-bob":
        agent_name = AGENT_NAME + " / [git-bob"
    else:
        agent_name = "[" + AGENT_NAME

    return f"<sup>This message was generated by {agent_name}](https://github.com/haesleinhuepf/git-bob) (version: {__version__}, model: {model}{link}), an experimental AI-based assistant. It can make mistakes and has [limitations](https://github.com/haesleinhuepf/git-bob?tab=readme-ov-file#limitations). Check its messages carefully.</sup>"


def comment_on_issue(repository, issue, prompt_function):
    """
    Comment on a GitHub issue using a prompt function.

    Parameters
    ----------
    repository : str
        The full name of the GitHub repository.
    issue : int
        The issue number to comment on.
    prompt_function : function
        The function to generate the comment.
    """
    Log().log(f"-> comment_on_issue({repository}, {issue})")
    from ._github_utilities import get_conversation_on_issue, add_comment_to_issue, list_repository_files, \
        get_repository_file_contents
    from ._utilities import text_to_json, modify_discussion, clean_output, redact_text

    ai_remark = setup_ai_remark()

    discussion = modify_discussion(get_conversation_on_issue(repository, issue))
    print("Discussion:", discussion)

    all_files = "* " + "\n* ".join(list_repository_files(repository))

    relevant_files = prompt_function(f"""
{SYSTEM_PROMPT}
Decide what to do to respond to a github issue. The entire issue discussion is given and a list of all files in the repository.

## Discussion of the issue #{issue}

{discussion}

## All files in the repository

{all_files}

## Your task
Which of these files are necessary to read for solving the issue #{issue} ? Keep the list short.
Returning an empty list is also a valid answer.
Respond with the filenames as JSON list.
""")
    filenames = text_to_json(relevant_files)

    file_content_dict = get_repository_file_contents(repository, "main", filenames)

    temp = []
    for k, v in file_content_dict.items():
        temp = temp + [f"### File {k} content\n\n```\n{v}\n```\n"]
    relevant_files_contents = "\n".join(temp)

    comment = prompt_function(f"""
{SYSTEM_PROMPT}
Respond to a github issue. Its entire discussion is given and additionally, content of some relevant files.

## Discussion

{discussion}

## Relevant files

{relevant_files_contents}

## Your task

Respond to the discussion above.
In case code-changes are discussed, make a proposal of how new code could look like.
Do NOT explain your response or anything else. 
Do not repeat answers that were given already.
Focus on the most recent discussion.
Just respond to the discussion.
""")
    comment = redact_text(clean_output(repository, comment))

    print("comment:", comment)

    add_comment_to_issue(repository, issue, f"""        
{ai_remark}

{comment}
""")


def review_pull_request(repository, issue, prompt_function):
    """
    Review a GitHub pull request using a prompt function.

    Parameters
    ----------
    repository : str
        The full name of the GitHub repository.
    issue : int
        The pull request number to review.
    prompt_function : function
        The function to generate the review comment.
    """
    Log().log(f"-> review_pull_request({repository}, {issue})")
    from ._github_utilities import get_conversation_on_issue, add_comment_to_issue, get_diff_of_pull_request
    from ._utilities import modify_discussion, clean_output, redact_text

    ai_remark = setup_ai_remark()

    discussion = modify_discussion(get_conversation_on_issue(repository, issue))
    print("Discussion:", discussion)

    file_changes = get_diff_of_pull_request(repository, issue)

    print("file_changes:", file_changes)

    comment = prompt_function(f"""
{SYSTEM_PROMPT}
Generate a response to a github pull-request. 
Given are the discussion on the pull-request and the changed files.
Check if the discussion reflects what was changed in the files.

## Discussion

{discussion}

## Changed files

{file_changes}

## Your task

Review this pull-request and contribute to the discussion. 

Do NOT explain your response or anything else. 
Just respond to the discussion.
""")
    comment = redact_text(clean_output(repository, comment))

    print("comment:", comment)

    add_comment_to_issue(repository, issue, f"""        
{ai_remark}

{comment}
""")


def summarize_github_issue(repository, issue, prompt_function):
    """
    Summarize a GitHub issue.

    Parameters
    ----------
    repository : str
        The full name of the GitHub repository.
    issue : int
        The issue number to summarize.
    llm_model : str
        The language model to use for generating the summary.
    """
    Log().log(f"-> summarize_github_issue({repository}, {issue})")
    from ._github_utilities import get_issue_details

    issue_conversation = get_issue_details(repository, issue)

    summary = prompt_function(f"""
Summarize the most important details of this issue #{issue} in the repository {repository}. 
In case filenames, variables and code-snippetes are mentioned, keep them in the summary, they are very important.

## Issue to summarize:
{issue_conversation}
""")

    print("Issue summary:", summary)
    return summary


def create_or_modify_file(repository, issue, filename, branch_name, issue_summary, prompt_function, number_of_attempts:int=3):
    """
    Create or modify a file in a GitHub repository.

    Parameters
    ----------
    repository : str
        The full name of the GitHub repository.
    issue : int
        The issue number to solve.
    filename : str
        The name of the file to create or modify.
    branch_name : str
        The name of the branch to create or modify the file in.
    issue_summary : str
        The summary of the issue to solve.
    prompt_function : function
        The function to generate the file modification content.
    """
    Log().log(f"-> create_or_modify_file({repository}, {issue}, {filename}, {branch_name})")
    from ._github_utilities import get_repository_file_contents, write_file_in_branch, create_branch, \
        check_if_file_exists, get_file_in_repository, decode_file
    from ._utilities import remove_outer_markdown, split_content_and_summary, erase_outputs_of_code_cells, \
        restore_outputs_of_code_cells, execute_notebook, text_to_json, save_and_clear_environment, \
        restore_environment, redact_text
    import os


    for attempt in range(number_of_attempts):
        an_error_happened = False

        original_ipynb_file_content = None

        format_specific_instructions = ""
        if filename.endswith('.py'):
            format_specific_instructions = " When writing new functions, use numpy-style docstrings."
        elif filename.endswith('.ipynb'):
            format_specific_instructions = " In the notebook file, write short code snippets in code cells and avoid long code blocks. Make sure everything is done step-by-step and we can inspect intermediate results. Add explanatory markdown cells in front of every code cell. The notebook has NO cell outputs! Make sure that there is code that saves results such as plots, images or dataframes, e.g. as .png or .csv files. Numpy images have to be converted to np.uint8 before saving as .png. Plots must be saved to disk before the cell ends or it is shown. The notebook must be executable from top to bottom without errors. Return the notebook in JSON format!"

        if check_if_file_exists(repository, branch_name, filename):
            file_content = decode_file(get_file_in_repository(repository, branch_name, filename))
            print(filename, "will be overwritten")
            if filename.endswith('.ipynb'):
                print("Removing outputs from ipynb file")
                original_ipynb_file_content = file_content
                file_content = erase_outputs_of_code_cells(file_content)
            file_content_instruction = f"""
Modify the file "{filename}" to solve the issue #{issue}. {format_specific_instructions}
If the discussion is long, some stuff might be already done. In that case, focus on what was said at the very end in the discussion.
Keep your modifications absolutely minimal.

That's the file "{filename}" content you will find in the file:
```
{file_content}
```

## Your task
Modify content of the file "{filename}" to solve the issue above.
Keep your modifications absolutely minimal.
Return the entire new file content, do not shorten it.
"""
        else:
            print(filename, "will be created")
            file_content_instruction = f"""
Create the file "{filename}" to solve the issue #{issue}. {format_specific_instructions}

## Your task
Generate content for the file "{filename}" to solve the issue above.
Keep it short.
"""

        prompt = f"""
{SYSTEM_PROMPT}
Given a github issue summary (#{issue}) and optionally file content (filename {filename}), modify the file content or create the file content to solve the issue.

## Issue {issue} Summary

{issue_summary}

## File {filename} content

{file_content_instruction}


Respond ONLY the content of the file and afterwards a single line summarizing the changes you made (without mentioning the issue).
"""
        print("Prompting for new file content...")
        response = prompt_function(prompt)

        new_content, commit_message = split_content_and_summary(response)

        print("New file content", len(new_content), "\n------------\n", new_content[:200], "\n------------")

        do_execute_notebook = False
        print("Summary", commit_message)

        if original_ipynb_file_content is not None:
            try:
                new_content = restore_outputs_of_code_cells(new_content, original_ipynb_file_content)
            except ValueError as e:
                warnings.warn(f"Could not restore outputs of code cells in {filename}: {e}")
                do_execute_notebook = True

        elif filename.endswith('.ipynb'):
            print("Erasing outputs in generated ipynb file")
            new_content = erase_outputs_of_code_cells(new_content)
            do_execute_notebook = True

        created_files = []
        if do_execute_notebook:
            print("Executing the notebook", len(new_content))
            current_dir = os.getcwd()
            print("current_dir", current_dir)
            path_without_filename = os.path.dirname(filename)
            print("path_without_filename", path_without_filename)
            if len(path_without_filename) > 0:
                os.makedirs(path_without_filename, exist_ok=True)
                os.chdir(path_without_filename)

            # store environment variables
            saved_environment = save_and_clear_environment()

            not_executed_notebook = new_content

            # Execute the notebook
            try:
                new_content, error_message = execute_notebook(new_content)
                restore_environment(saved_environment)
                if error_message is None:
                    # scan for files the notebook created
                    list_of_files_text = prompt_function(f"""
Extract a list of filenames including path from the following jupyter notebook. 
The path should be relative from the repository root, not from the notebooks's postion. 
The position of the notebook is {filename}.
Return the list as a JSON list and nothing else.

Notebook:
{not_executed_notebook}
            """)
                    list_of_files = text_to_json(list_of_files_text)
                    print("------------------------")
                    for file in list_of_files:
                        print("File created by notebook:", file, os.path.exists(file))
                        if os.path.exists(file):
                            created_files.append(file)
                            with open(file, 'rb') as f:
                                file_content2 = f.read()
                                write_file_in_branch(repository, branch_name, f"{file}", file_content2, f"Adding {path_without_filename}/{file} created by notebook")
                    print("------------------------")

            except Exception as e:
                raise ValueError(f"Error during notebook execution: {e}")
            finally:
                os.chdir(current_dir)
                restore_environment(saved_environment)

            print("Executed notebook", len(new_content))

        created_files.append(filename)

        new_content = redact_text(new_content)
        if not an_error_happened:
            break
        print(f"An error happened. Retrying... {attempt+1}/{number_of_attempts}")

    write_file_in_branch(repository, branch_name, filename, new_content + "\n", redact_text(commit_message))

    return commit_message + "\n\nCreated files:\n* " + "\n* ".join(created_files)


def solve_github_issue(repository, issue, llm_model, prompt_function, base_branch=None):
    """
    Attempt to solve a GitHub issue by modifying a single file and sending a pull-request, or
    commenting on a pull-request.

    Parameters
    ----------
    repository : str
        The full name of the GitHub repository.
    issue : int
        The issue number to solve.
    llm_model : str
        The language model to use for generating the solution.
    prompt_function: function
        The function to use for generating prompts.
    base_branch : str
        The name of the base branch to create the new branch from.
    """
    # modified from: https://github.com/ScaDS/generative-ai-notebooks/blob/main/docs/64_github_interaction/solving_github_issues.ipynb

    Log().log(f"-> solve_github_issue({repository}, {issue})")

    from ._github_utilities import get_issue_details, list_repository_files, get_repository_file_contents, \
        write_file_in_branch, send_pull_request, add_comment_to_issue, create_branch, check_if_file_exists, \
        get_diff_of_branches, get_conversation_on_issue, rename_file_in_repository, delete_file_from_repository, \
        copy_file_in_repository, download_to_repository, add_comment_to_issue, \
        get_repository_handle
    from ._utilities import remove_outer_markdown, split_content_and_summary, text_to_json, modify_discussion, \
        remove_ansi_escape_sequences, clean_output, redact_text
    from github.GithubException import GithubException
    import traceback

    repo = get_repository_handle(repository)

    discussion = modify_discussion(get_conversation_on_issue(repository, issue))
    print("Discussion:", discussion)

    all_files = "* " + "\n* ".join(list_repository_files(repository))

    modifications = prompt_function(f"""
Given a list of files in the repository {repository} and a github issues description (# {issue}), determine which files need to be modified, renamed or deleted to solve the issue.

## Github Issue #{issue} Discussion

{discussion}

## All files in the repository

{all_files}

## Your task
Decide which of these files need to be modified, created, downloaded, renamed, copied or deleted to solve #{issue} ? 
Downloads are necessary, if there is a url in the discussion and the linked file is needed in the proposed code.
If the user asks for executing a notebook, consider this as modification.
Keep the list of actions minimal.
Response format:
- For modifications: {{"action": "modify", "filename": "..."}}
- For creations: {{"action": "create", "filename": "..."}}
- For downloads: {{"action": "download", "source_url": "...", "target_filename": "..."}}
- For renames: {{"action": "rename", "old_filename": "...", "new_filename": "..."}}
- For copies: {{"action": "copy", "old_filename": "...", "new_filename": "..."}}
- For executions: {{"action": "execute", "filename": "..."}}
- For deletions: {{"action": "delete", "filename": "..."}}
Respond with the actions as JSON list.
""")

    instructions = text_to_json(modifications)

    # create a new branch
    if base_branch is None or base_branch == repo.get_branch(repo.default_branch).name:
        # create a new branch
        branch_name = create_branch(repository, parent_branch=base_branch)
        print("Created branch", branch_name)
    else:
        # continue on the current branch
        branch_name = base_branch
        print("Continue working on branch", branch_name)

    # sort instructions by action: downloads first, then the rest in original order
    print("unsorted instructions", instructions)
    instructions = sorted(instructions, key=lambda x: x.get('action') != 'download')
    print("sorted instructions", instructions)

    errors = []
    commit_messages = []
    for instruction in instructions:
        action = instruction.get('action')

        for filename_key in ["filename", "new_filename", "old_filename", "target_filename"]:
            if filename_key in instruction.keys():
                filename = instruction[filename_key]
                if ".github" in filename:
                    errors.append(f"Error processing {filename}: Modifying workflow files is not allowed.")
                    continue

        try:
            if action == 'create' or action == 'modify':
                filename = instruction['filename'].strip("/")
                message = filename + ":" + create_or_modify_file(repository, issue, filename, branch_name, discussion,
                                                                 prompt_function)
                commit_messages.append(message)
            elif action == 'download':
                source_url = instruction['source_url']
                target_filename = instruction['target_filename'].strip("/")
                download_to_repository(repository, branch_name, source_url, target_filename)
                commit_messages.append(f"Downloaded {source_url}, saved as {target_filename}.")
            elif action == 'rename':
                old_filename = instruction['old_filename'].strip("/")
                new_filename = instruction['new_filename'].strip("/")
                rename_file_in_repository(repository, branch_name, old_filename, new_filename)
                commit_messages.append(f"Renamed {old_filename} to {new_filename}.")
            elif action == 'delete':
                filename = instruction['filename'].strip("/")
                delete_file_from_repository(repository, branch_name, filename)
                commit_messages.append(f"Deleted {filename}.")
            elif action == 'copy':
                old_filename = instruction['old_filename'].strip("/")
                new_filename = instruction['new_filename'].strip("/")
                copy_file_in_repository(repository, branch_name, old_filename, new_filename)
                commit_messages.append(f"Copied {old_filename} to {new_filename}.")
        except Exception as e:
            traces = "    " + remove_ansi_escape_sequences(traceback.format_exc()).replace("\n", "\n    ")
            summary = f"""<details>
    <summary>Error during {instruction}: {e}</summary>
    <pre>{traces}</pre>
</details>
            """
            errors.append(summary)

    error_messages = ""
    if len(errors) > 0:
        error_messages = "\n\nDuring solving this task, the following errors occurred:\n\n* " + "\n* ".join(
            errors) + "\n"

    print(error_messages)

    # get a diff of all changes
    diffs_prompt = get_diff_of_branches(repository, branch_name, base_branch=base_branch)

    # summarize the changes
    commit_messages_prompt = "* " + "\n* ".join(commit_messages)

    from ._ai_github_utilities import setup_ai_remark
    remark = setup_ai_remark() + "\n\n"

    link_files_task = f"""
If there are image files created, use the markdown syntax ![](url) to display them.
If there other new files created, add markdown links to them. 
For file and image urls, prefix them with the repository name and the branch name: https://github.com/{repository}/blob/{branch_name}/
For image urls, append "?raw=true" by the end of the url to display the image directly. Again, you MUST use the ![]() markdown syntax for image files.
"""

    if branch_name != base_branch:

        pull_request_summary = prompt_function(f"""
{SYSTEM_PROMPT}
Given a list of commit messages and a git diff, summarize the changes you made in the files.
You modified the repository {repository} to solve the issue #{issue}, which is also summarized below.

## Github Issue #{issue} Discussion

{discussion}

## Commit messages
You committed these changes to these files

{commit_messages_prompt}

## Git diffs
The following changes were made in the files:

{diffs_prompt}

## Your task

Summarize the changes above to a one paragraph line Github pull-request message. 
{link_files_task}

Afterwards, summarize the summary in a single line, which will become the title of the pull-request.
Do not add headline or any other formatting. Just respond with the paragraph and the title in a new line below.
""")

        pull_request_description, pull_request_title = split_content_and_summary(pull_request_summary)

        full_report = remark + clean_output(repository, pull_request_description) + error_messages

        try:
            send_pull_request(repository,
                          source_branch=branch_name,
                          target_branch=base_branch,
                          title=redact_text(pull_request_title),
                          description=redact_text(full_report) + f"\n\ncloses #{issue}")
        except GithubException as e:
            add_comment_to_issue(repository, issue, f"{remark}Error creating pull-request: {e}{error_messages}")
    else:
        modification_summary = prompt_function(f"""
{SYSTEM_PROMPT}
Given a list of commit messages, summarize the changes you made.

## Commit messages
You committed these changes to these files

{commit_messages_prompt}

## Your task
Summarize the changes above to a one paragraph.
{link_files_task}

Do not add headline or any other formatting. Just respond with the paragraphe below.
""")

        add_comment_to_issue(repository, issue, remark + redact_text(clean_output(repository, modification_summary)) + redact_text(error_messages))

def split_issue_in_sub_issues(repository, issue, prompt_function):
    """
    Split a main issue into sub-issues for each sub-task.

    Parameters
    ----------
    repository : str
        The full name of the GitHub repository (e.g., "username/repo-name").
    issue : int
        The main issue number.
    """
    Log().log(f"-> split_issue_in_sub_issues({repository}, {issue},...)")
    from ._utilities import text_to_json
    from ._github_utilities import create_issue, add_comment_to_issue, get_conversation_on_issue

    discussion = get_conversation_on_issue(repository, issue)
    ai_remark = setup_ai_remark()+ "\n"

    # Implement the prompt to parse the discussion
    sub_tasks_json = prompt_function(f"""
{SYSTEM_PROMPT}
You need to extract sub-tasks from a given discussion.
Hint: Sub-tasks are never about "Create an issue for X", but "X" instead. Also sub-tasks are never about "Propose X", but "X" instead.
Return a JSON list with a short title for each sub-task.

## Discussion
{discussion}

## Your task
Extract and return sub-tasks as a JSON list of sub-task titles.
""")

    sub_tasks = text_to_json(sub_tasks_json)
    created_sub_tasks = ""

    sub_issue_numbers = []
    for title in sub_tasks:
        body = prompt_function(f"""
{SYSTEM_PROMPT}
Given description of a list of sub-tasks and extra details given in a discussion, 
extract relevant information for one of the sub-tasks.

## Discussion
{discussion}

{created_sub_tasks}

## Your task
Extract relevant information for the sub-task "{title}".
Write the information down and make a proposal of how to solve the sub-task.
Do not explain your response or anything else. Just respond the relevant information for the sub-task and a potential solution.
""")
        body = body.replace(AGENT_NAME, AGENT_NAME[:3]+ "_" + AGENT_NAME[4:]) # prevent endless loops

        issue_number = create_issue(repository, title, ai_remark + body)
        sub_issue_numbers.append(issue_number)

        if len(created_sub_tasks) == 0:
            created_sub_tasks = "## Other sub-tasks\nThe following sub-tasks have already been identified:\n"
        created_sub_tasks += f"### {title}\n{body}\n\n"

    # Create a comment on the main issue with the list of sub-issues
    sub_issue_links = "\n".join([f"- #{num}" for num in sub_issue_numbers])
    comment_text = f"Sub-issues have been created:\n{sub_issue_links}"
    add_comment_to_issue(repository, issue, ai_remark + comment_text)

    return sub_issue_numbers
