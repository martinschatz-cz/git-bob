# git-bob
[![PyPI](https://img.shields.io/pypi/v/git-bob.svg?color=green)](https://pypi.org/project/git-bob)
[![DOI](https://zenodo.org/badge/831841421.svg)](https://doi.org/10.5281/zenodo.13970719)
[![License](https://img.shields.io/pypi/l/git-bob.svg?color=green)](https://github.com/haesleinhuepf/git-bob/raw/main/LICENSE)
<!--[![PyPI - Downloads](https://img.shields.io/pypi/dm/git-bob)](https://pypistats.org/packages/git-bob)-->

git-bob uses AI to solve GitHub issues and review pull requests. It runs inside the GitHub CI, no need to install anything on your computer.
Read more in the [preprint](https://doi.org/10.5281/zenodo.13928832). 

![banner](https://github.com/haesleinhuepf/git-bob/raw/main/docs/images/banner2.png)

Under the hood it uses [Anthropic's Claude](https://www.anthropic.com/api) or [OpenAI's chatGPT](https://openai.com/blog/openai-api) or [Google's Gemini](https://blog.google/technology/ai/google-gemini-ai/) to understand the text and 
[pygithub](https://github.com/PyGithub/PyGithub) to interact with the issues and pull requests. As its discussions are conserved, you can document how things were done using AI and 
others can learn how to prompt for the things you did. For example, the pair-plot discussion above is [available online](https://github.com/haesleinhuepf/git-bob-playground/issues/48).

## Disclaimer

`git-bob` is a research project aiming at streamlining GitHub interaction in software development projects. Under the hood it uses
artificial intelligence / large language models to generate text and code fulfilling the user's requests. 
Users are responsible to verify the generated code according to good scientific practice.

When using `git-bob` you configure it to use an API key to access the AI models. 
You have to pay for the usage and must be careful in using the software.
Do not use this technology if you are not aware of the costs and consequences.

> [!CAUTION]
> When using the Anthropic, OpenAI, Google Gemini or any other endpoint via git-bob, you are bound to the terms of service 
> of the respective companies or organizations.
> The GitHub issues, pull requests and messages you enter are transferred to their servers and may be processed and stored there. 
> Make sure to not submit any sensitive, confidential or personal data. Also using these services may cost money.

## Installation as GitHub action

There is a detailed [tutorial](https://github.com/haesleinhuepf/git-bob/blob/main/docs/installation-tutorial.md) on how to install git-bob as GitHub action to your repository. In very short, to use git-bob in your GitHub repository, you need to 
* Copy the [git-bob](https://github.com/haesleinhuepf/git-bob/blob/main/.github/workflows/git-bob.yml) GitHub workflow in folder `.github/workflows/` to your repository.
  * Make sure to replace `pip install -e .` with a specific git-bob version such as `pip install git-bob==0.11.0`.
  * Configure the LLM you want to use in the workflow files by specifying the `GIT_BOB_LLM_NAME` environment variable. These were tested:
    * `claude-3-5-sonnet-20240620`
    * `gpt-4o-2024-08-06` (recommended if you work with large files, < 16k tokens)
    * `github_models:gpt-4o`
    * `github_models:meta-llama-3.1-405b-instruct`
    * `gemini-1.5-pro-002`
  * configure a GitHub secret called `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` or `GH_MODELS_API_KEY` or `GOOGLE_API_KEY` or `KISSKI_API_KEY` or `BLABBLADOR_API_KEY` with the corresponding key from the LLM provider depending on the above configured LLM. You can get these keys here:
  * [OpenAI (gpt)](https://openai.com/blog/openai-api)
  * [Anthropic (claude)](https://www.anthropic.com/api)
  * [GitHub Models Marketplace](https://github.com/marketplace/models)
  * [Google AI](https://ai.google.dev/gemini-api/docs/api-key)
  * [KISSKI](https://services.kisski.de/services/en/service/?service=2-02-llm-service.json)
  * [BLABLADOR](https://login.helmholtz.de/oauth2-as/oauth2-authz-web-entry)
  * configure GitHub actions to run the workflow on issues and pull requests. Also give write-access to the Workflow using the `GITHUB_TOKEN`.

When using it in your repository, you can also set a custom system message, for example for:
* [General Data Science / Python Programming](https://github.com/haesleinhuepf/git-bob-playground/blob/bf08b3526980e011f632c13f29ae65372aafa5c7/.github/workflows/git-bob.yml#L75)
* [Bio-Image Analysis](https://github.com/haesleinhuepf/git-bob-bioimage-analysis-example/blob/main/.github/workflows/git-bob.yml#L75)
* [Giving advice on a specific repository / library](https://github.com/haesleinhuepf/stackview/blob/afc662a71a39f298af9f183c06c3d37c95cc2015/.github/workflows/git-bob.yml#L58)
* [Manuscript writing](https://github.com/haesleinhuepf/git-bob-manuscript/blob/49659f8a41854d4da696259e7c1316af2fc7c171/.github/workflows/comment-on-issue.yml#L49)

Furthermore, to guide discussions, you may want to setup issue templates, e.g.
* [General Python Programming Questions](https://github.com/haesleinhuepf/git-bob-playground/blob/main/.github/ISSUE_TEMPLATE/programming.md)
* [Bio-Image Analysis](https://github.com/haesleinhuepf/git-bob-playground/blob/main/.github/ISSUE_TEMPLATE/bioimage_analysis.md)
* [Statistics and Plotting](https://github.com/haesleinhuepf/git-bob-playground/blob/main/.github/ISSUE_TEMPLATE/statistics_plotting.md)

## Installation as gitlab pipeline

Since version 0.10.1 git-bob has experimental support for [gitlab](https://gitlab.com). You find detailed instructions how to install it [here](https://github.com/haesleinhuepf/git-bob/blob/main/docs/installation-tutorial-gitlab.md).

## Usage: Trigger words

To trigger git-bob, you need to comment on an issue or pull request with the `comment` trigger word (or aliases `think about`, `review`, `respond`):

```
git-bob comment
```

After some back-and-forth discussion, you can also use the `solve` trigger word (or aliases `implement`, `apply`) make git-bob solve an issue and send a pull-request. 
This trigger can also be used to modify code in pull requests.

```
git-bob solve
```

You can ask git-bob to implement a solution for testing, without sending a pull-request, using the `try` trigger:
```
git-bob try
```

If you have multiple API-Key for different LLMs configured, you can specify the LLM in the command using the `ask <LLM-Name> to` trigger command:

```
git-bob ask claude-3-5-sonnet-20240620 to solve this issue.
```

If the issue is complex and should be split into sub-issues, you can use the following command:

```
git-bob split
```

If you have two GitHub secrets `TWINE_USERNAME` and `TWINE_PASSWORD` configured, you can also use the following command to publish a new version of your library to PyPI:

```
git-bob deploy
```

All trigger words can be combined with `please` and/or `,`, which will make no difference to calling git-bob without these words:

```
git-bob, please ask gemini-1.5-pro-002 to solve this issue.
```

## Recommended Workflow

Here's the recommended workflow for using git-bob:

1. Create an issue describing the problem or task.
2. Comment on the issue with `git-bob comment`, or `git-bob think about this` (an alias for `comment`) to trigger git-bob making a plan.
3. Respond to git-bob with any clarifications or additional information it requests.
4. Comment on the issue with `git-bob solve` or `git-bob implement this` (an alias for `solve`) to trigger git-bob.
5. Wait for git-bob to create a pull request (PR) addressing the issue.
6. Review the PR and comment on the PR or on the original issue if changes are needed.
7. Wait for git-bob to create new PR or modifying the existing PR with the requested changes.
8. Repeat steps 3-5 as necessary until the issue is resolved satisfactorily.

## Use-case examples

A huge variety of use-cases for git-bob are thinkable. Here are some examples. Many serve purely demonstrative purposes. 
Some were parts of real scientific data analysis projects.

* Question answering 
  * [About specific Python libraries](https://github.com/haesleinhuepf/stackview/issues/79)
  * [Visualizing how Fourier-Transform works](https://github.com/haesleinhuepf/git-bob-playground/issues/22)
  * [The capital of France](https://github.com/haesleinhuepf/git-bob-playground/issues/24)
* Bio-image Analysis
  * [Nuclei segmentation](https://github.com/haesleinhuepf/git-bob-playground/issues/13)
  * [Cell segmentation](https://github.com/haesleinhuepf/git-bob-playground/issues/42)
* Data & Code Management
  * [Research Data Management & Folder Structures](https://github.com/haesleinhuepf/git-bob-playground/issues/45)
  * [Documenting source code](https://github.com/haesleinhuepf/git-bob/pull/29)
  * [Assisting scientific manuscript writing](https://github.com/haesleinhuepf/git-bob-manuscript/pull/9)
* Statistics
  * [Filtering data and counting records](https://github.com/NFDI4BIOIMAGE/training/issues/299)
  * [Selecting ranges of columns](https://github.com/haesleinhuepf/git-bob-playground/issues/47)
  * [Summarizing data and plotting](https://github.com/NFDI4BIOIMAGE/training/issues/250)
* Plotting
  * [Violing plots with simulated data](https://github.com/haesleinhuepf/git-bob-playground/issues/44)
  * [UMAPs with simulated data](https://github.com/haesleinhuepf/git-bob-playground/issues/41)
  * [Plotting a circle of triangles (in gitlab)](https://gitlab.com/haesleinhuepf/git-bob-gitlab-playground/-/issues/8)
  * [Pairplots with simulated data](https://github.com/haesleinhuepf/git-bob-playground/issues/48)

## Installation for development

```
git clone https://github.com/haselinhuepf/git-bob.git
cd git-bob
```

### Usage as command-line tool (for development)

You can also install git-bob locally and run it from the terminal. 
In this case, create a [GitHub token](https://github.com/settings/tokens) and store it in an environment variable named `GITHUB_API_KEY`. 
Also create an environment variable `GIT_BOB_LLM_NAME` with the name of the LLM you want to use, e.g. "gpt-4o-2024-05-13" or "claude-3-5-sonnet-20240620" or "github_models:gpt-4o".
Then you can install git-bob using pip:

```bash
pip install git-bob
```

### Usage as command-line tool (for development)

You can then use git-bob from the terminal on repositories you have read/write access to. 
It is recommended to call it from the root folder of the repository you want to interact with.

```bash
git clone https://github.com/<organization>/<repository>
cd <repository>
git-bob <action> <organization>/<repository> <issue-number>
```

Available actions:
* `review-pull-request`
* `comment-on-issue`
* `solve-issue`
* `split-issue`

## Limitations
`git-bob` is a research project and has limitations. It serves as basis for discussion and further development. Once LLMs become better, `git-bob` will become better as well.

At the moment, these limitations can be observed:
* `git-bob` was tested for Python projects mostly. It seems to be able to process Java and C++ as well.
* It can only execute code in Jupyter Notebooks. 
* It sometimes hallucinates, especially in code reviews. E.g. it [claimed](https://github.com/haesleinhuepf/git-bob/pull/70) to have tested code, which was certainly not true.
* It cannot solve issues where changing long files is required, as the output of the LLMs is limited by a maximum number of tokens (e.g. 16k for `gpt-4o-2024-08-06`). When using OpenAI's models it combines output of multiple requests to a maximum file length about 64k tokens. It may then miss some spaces or a line break where responses were stitched. 
  When using GitHub models, the maximum file length is 4k tokens. When using Anthropic's Claude, the maximum file length is 8k tokens.
* When changing multiple files, it may introduce conflicts between the files, as it does not know about the changed contents of the other files.
* It has only limited logic to control who is allowed to trigger it. 
  If you are a repository member, you can trigger it. 
  If others send a pull request, a repository member must allow the action to run manually.
* `git-bob` is incompatible with locally running open-source/-weight LLMs. 
  This might make sense when being executed locally only. In the GitHub-CI this might be impossible.
* Recently tested `claude-3-5-sonnet-20240620`, `gpt-4o-2024-08-06`, `github_models:gpt-4o`, `github_models:meta-llama-3.1-405b-instruct` and `gemini-1.5-pro-002` produced useful results.
* `git-bob` is not allowed to modify workflow files, because it also uses GitHub workflows.

## Similar projects

There are similar projects out there
* [Claude Engineer](https://github.com/Doriandarko/claude-engineer)
* [BioChatter](https://github.com/biocypher/biochatter)
* [aider](https://github.com/paul-gauthier/aider)
* [OpenDevin](https://github.com/OpenDevin/OpenDevin)
* [Devika](https://github.com/stitionai/devika)
* [GPT-Codemaster](https://github.com/dex3r/GPT-Codemaster)
* [GitHub Copilot Workspace](https://githubnext.com/projects/copilot-workspace)
* [agentless](https://github.com/OpenAutoCoder/Agentless)
* [git-aid](https://github.com/Torantulino/git-aid)
* [SWE-agent](https://github.com/princeton-nlp/SWE-agent)

## Contributing

Feedback and contributions are welcome! Just open an issue and let's discuss before you send a pull request. 
A [human](https://haesleinhuepf.github.io) will respond and comment on your ideas!

## Citation

If you use git-bob, please cite it:
```
@misc{haase_2024_13928832,
  author       = {Haase, Robert},
  title        = {{Towards Transparency and Knowledge Exchange in AI- 
                   assisted Data Analysis Code Generation}},
  month        = oct,
  year         = 2024,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.13928832},
  url          = {https://doi.org/10.5281/zenodo.13928832}
}
```

## Acknowledgements

We acknowledge the financial support by the Federal Ministry of Education and Research of Germany and by Sächsische Staatsministerium für Wissenschaft, Kultur und Tourismus in the programme Center of Excellence for AI-research „Center for Scalable Data Analytics and Artificial Intelligence Dresden/Leipzig", project identification number: ScaDS.AI
