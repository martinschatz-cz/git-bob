import os
import sys

from github_utilities import comment_on_issue, get_conversation_on_issue, get_most_recent_comment_on_issue
from claude import prompt_claude

print("Hello")
# Read the environment variable "ANTHROPIC_API_KEY"
api_key = os.environ.get("ANTHROPIC_API_KEY")

# Check if the environment variable is not None
print("Hello")
if api_key is not None:
    print("world!")
if api_key[0] == '"':
    print("nej!")

# Print out all arguments passed to the script
print("Script arguments:")
for arg in sys.argv[1:]:
    print(arg)

task = sys.argv[1]
repository = sys.argv[2] if len(sys.argv) > 2 else None
issue = int(sys.argv[3]) if len(sys.argv) > 3 else None

if task == "response-pull-request":

    user, text = get_most_recent_comment_on_issue(repository, issue)

    if "@bob" in text:

        discussion = get_conversation_on_issue(repository, issue)

        print("Discussion:", discussion)

        comment = prompt_claude("""
Assume you are Bob (also known as git-bob). Generate a response to the following discussion in a github pull-request:

{discussion}

Respond to the discussion above only. Do NOT explain your response or anything else. Just respond to the discussion.
""")

        print("comment:", comment)

        comment_on_issue(repository, issue, f"""
{comment}

---
This comment was generated by git-bob, an AI assistant. Read how this is done in the [git-bob](https://github.com/haesleinhuepf/git-bob) documentation.
""")

