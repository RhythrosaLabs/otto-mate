# Slash Commands

Otto supports slash commands for quick actions directly from the chat input.

---

## Usage

Type `/` followed by the command name and any arguments:

```
/command [arguments]
```

---

## Available Commands

### Content Generation

| Command | Description | Example |
|---------|-------------|---------|
| `/image` | Generate an image | `/image a sunset over mountains` |
| `/video` | Generate a video | `/video waves crashing on a beach` |
| `/music` | Generate music | `/music upbeat jazz piano` |
| `/3d` | Generate a 3D model | `/3d a medieval sword` |

### Information & Research

| Command | Description | Example |
|---------|-------------|---------|
| `/search` | Search the web | `/search latest AI news` |
| `/browse` | Open and extract from URL | `/browse https://example.com` |
| `/research` | Deep multi-source research | `/research quantum computing advances 2024` |

### E-Commerce (Printify)

| Command | Description | Example |
|---------|-------------|---------|
| `/products` | List products in shop | `/products` |
| `/create-product` | Create a new product | `/create-product sunset t-shirt` |
| `/shops` | List connected shops | `/shops` |

### System & Files

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show all available commands | `/help` |
| `/status` | Show system status | `/status` |
| `/clear` | Clear the conversation | `/clear` |
| `/upload` | Upload a file | `/upload` |
| `/download` | Download a generated file | `/download` |
| `/export` | Export conversation | `/export` |

### Task Management

| Command | Description | Example |
|---------|-------------|---------|
| `/task` | Create a new task | `/task Design new logo by Friday` |
| `/tasks` | View task queue | `/tasks` |
| `/schedule` | Schedule a task | `/schedule daily 9am "Generate analytics report"` |

### Agent System

| Command | Description | Example |
|---------|-------------|---------|
| `/agents` | List active agents | `/agents` |
| `/autonomous` | Toggle autonomous mode | `/autonomous on` |
| `/plan` | Create an execution plan | `/plan build a marketing campaign` |

### Skill & Plugin Management

| Command | Description | Example |
|---------|-------------|---------|
| `/skills` | List loaded skills | `/skills` |
| `/plugins` | List loaded plugins | `/plugins` |
| `/install` | Install a plugin | `/install my-plugin` |

### Projects

| Command | Description | Example |
|---------|-------------|---------|
| `/projects` | List projects | `/projects` |
| `/project` | Switch to or create a project | `/project my-website` |

---

## Custom Slash Commands

Skills and plugins can register their own slash commands. When a skill is loaded, its defined commands become available automatically.

### Registering a Command (Plugin Example)

```python
class MyPlugin:
    def get_slash_commands(self):
        return {
            "mycommand": {
                "description": "Does something cool",
                "handler": self.handle_command,
                "usage": "/mycommand <arg>"
            }
        }
    
    async def handle_command(self, args: str, context: dict):
        return f"Executed with args: {args}"
```

---

## Output Location

Slash command outputs are saved to:

```
data/slash_outputs/
├── images/
├── videos/
├── audio/
├── exports/
└── downloads/
```
