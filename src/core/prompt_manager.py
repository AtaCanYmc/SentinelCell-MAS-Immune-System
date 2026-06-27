import os
import jinja2


class PromptManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
            cls._instance._init_loader()
        return cls._instance

    def _init_loader(self):
        prompts_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "prompts"
        )
        # Use FileSystemLoader, which caches by default. We can also enable strict undefined if desired.
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(prompts_dir),
            autoescape=False,  # Safe because these are LLM prompts, not HTML
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @classmethod
    def render(cls, template_name: str, context: dict = None) -> str:
        """
        Renders a Jinja2 prompt template from the src/prompts directory.
        """
        if context is None:
            context = {}
        manager = cls()
        template = manager.env.get_template(template_name)
        return template.render(**context)
