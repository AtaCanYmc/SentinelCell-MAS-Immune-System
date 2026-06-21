# SentinelCell README Standards

To maintain consistency across our agentic ecosystem, every component of SentinelCell must follow these documentation
guidelines.

## 1. Structure Requirements

Every README must contain:

- **Project Name & Badges:** Use relevant shields/badges for build status and version.
- **Content Table:** Auto-generated table of contents for easy navigation.
- **Problem Statement:** One paragraph explaining the "pain point" being solved.
- **Agentic Architecture:** A visual representation (Mermaid/SVG) of the agent's flow.
- **Setup & Deployment:** Clear, step-by-step instructions.
- **Skill Documentation:** Reference the corresponding `SKILL.md` file.
- **Sandbox Policy:** Reference the `.antigravity/auto_changelog_policy.md` for agentic permissions.
- **Security Disclaimer:** If the agent interacts with external APIs, include a disclaimer about potential risks.
- **Changelog Reference:** Link to `CHANGELOG.md` for version history.
- **License Information:** Include a link to the LICENSE file.
- **Logo:** Include a small logo or icon in the top-left corner of the README for brand identity.
- **Contact Information:** Provide a point of contact for questions or issues.
- **Contribution Guidelines:** Include a link to `CONTRIBUTING.md` for community contributions.
- **Acknowledgments:** Credit any third-party libraries, tools, or contributors.
- **References:** Include links to relevant research papers, articles, or documentation.
- **Appendix:** Include any additional information, diagrams, or resources that may be helpful for understanding the agent's functionality.
- **Security Disclaimer:** If the agent interacts with external APIs, include a disclaimer about potential risks.
- **Example Env Variables:** If applicable, provide example environment variable configurations (without sensitive information) to guide users in setting up their own `.env` files.

## 2. Style Guidelines

- **Language:** Use only English for all documentation to maintain global accessibility.
- **Conciseness:** Keep technical descriptions under 300 words.
- **Code-First:** Use code blocks for every configuration example.
- **Safety First:** Always include a "Security Disclaimer" if the agent interacts with external APIs.

## 3. Mandatory Sections

| Section               | Purpose                                              |
|:----------------------|:-----------------------------------------------------|
| **Philosophy**        | The "Vibe" or intent behind the agent.               |
| **Capability Matrix** | List of skills/tools the agent is authorized to use. |
| **Sandbox Policy**    | Reference to Antigravity CLI usage.                  |
| **Architecture**      | Mermaid/SVG diagram of the agentic flow.             |

## 4. Maintenance Rule

If a new skill is added, the agent MUST trigger a README update via the `auto-commit` workflow.

### 5. Language & Tone

- Use a professional yet approachable tone.
- Avoid jargon unless it is defined in the documentation.
- Use active voice and imperative mood for instructions.
- Use only English for all documentation to maintain global accessibility.

### 6. Versioning

- Follow semantic versioning (MAJOR.MINOR.PATCH).

### 7. Logo

- Include a small logo or icon in the top of the README for brand identity.
- Generate a simple SVG logo using the `antigravity` CLI if none exists.

### 8. Badges

- Include build status, Python version, and Kaggle Capstone badges at the top of the README.
- Use shields.io for generating badges.

# 9. Kaggle Notes

-Your submission (when submitting via GitHub) should contain a README.md file explaining the problem, solution,
architecture, instructions for setup, and relevant diagrams or images where appropriate.
