# SentinelCell README Standards

To maintain consistency across our agentic ecosystem, every component of SentinelCell must follow these documentation guidelines.

## 1. Structure Requirements
Every README must contain:
- **Project Name & Badges:** Use relevant shields/badges for build status and version.
- **Problem Statement:** One paragraph explaining the "pain point" being solved.
- **Agentic Architecture:** A visual representation (Mermaid/SVG) of the agent's flow.
- **Setup & Deployment:** Clear, step-by-step instructions.
- **Skill Documentation:** Reference the corresponding `SKILL.md` file.

## 2. Style Guidelines
- **Language:** Use only English for all documentation to maintain global accessibility.
- **Conciseness:** Keep technical descriptions under 300 words.
- **Code-First:** Use code blocks for every configuration example.
- **Safety First:** Always include a "Security Disclaimer" if the agent interacts with external APIs.

## 3. Mandatory Sections
| Section | Purpose |
| :--- | :--- |
| **Philosophy** | The "Vibe" or intent behind the agent. |
| **Capability Matrix** | List of skills/tools the agent is authorized to use. |
| **Sandbox Policy** | Reference to Antigravity CLI usage. |

## 4. Maintenance Rule
If a new skill is added, the agent MUST trigger a README update via the `auto-commit` workflow.

### 5. Language & Tone
- Use a professional yet approachable tone.
- Avoid jargon unless it is defined in the documentation.
- Use active voice and imperative mood for instructions.
- Use only English for all documentation to maintain global accessibility.
