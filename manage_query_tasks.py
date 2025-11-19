"""
Manage Query Tasks - View, Create, and Manage Search Tasks
"""

import sys
sys.path.insert(0, '.')

from news_search import Database


# Predefined query task templates
TASK_TEMPLATES = {
    "malaysia_solar_news": {
        "prompt": """
Find latest news articles about solar energy in Malaysia.
Focus on: solar projects, solar installations, renewable energy policies, solar companies.
Return URLs as JSON array with titles.
Example: [{"url": "https://...", "title": "..."}, ...]
Limit to 15 most relevant articles.
""",
        "description": "Malaysia solar energy news"
    },
    
    "malaysia_renewable_energy": {
        "prompt": """
Find latest news about renewable energy in Malaysia.
Focus on: solar, wind, hydroelectric, renewable energy policies, green energy projects.
Return URLs as JSON array with titles.
Limit to 15 articles.
""",
        "description": "Malaysia renewable energy (all types)"
    },
    
    "asean_solar_projects": {
        "prompt": """
Find latest news about solar energy projects in ASEAN countries.
Focus on: Malaysia, Singapore, Thailand, Indonesia, Philippines, Vietnam.
Include: large-scale solar projects, solar installations, solar policies.
Return URLs as JSON array with titles.
Limit to 20 articles.
""",
        "description": "ASEAN region solar projects"
    },
    
    "global_solar_tech": {
        "prompt": """
Find latest news about solar technology innovations and breakthroughs.
Focus on: new solar panel technology, efficiency improvements, solar storage, solar research.
Return URLs as JSON array with titles.
Limit to 15 articles.
""",
        "description": "Global solar technology innovations"
    },
    
    "ev_charging_infrastructure": {
        "prompt": """
Find latest news about electric vehicle (EV) charging infrastructure.
Focus on: charging stations, charging networks, EV infrastructure projects, charging technology.
Return URLs as JSON array with titles.
Limit to 15 articles.
""",
        "description": "EV charging infrastructure news"
    },
    
    "renewable_energy_policy": {
        "prompt": """
Find latest news about renewable energy policies and regulations.
Focus on: government policies, renewable energy targets, subsidies, regulations, international agreements.
Return URLs as JSON array with titles.
Limit to 15 articles.
""",
        "description": "Renewable energy policies and regulations"
    },
    
    "tech_news_daily": {
        "prompt": """
Find latest technology news articles from today.
Focus on: AI, machine learning, software development, tech companies, tech innovations.
Return URLs as JSON array with titles.
Limit to 20 articles.
""",
        "description": "Daily technology news"
    },
    
    "ai_news": {
        "prompt": """
Find latest artificial intelligence and machine learning news.
Focus on: AI breakthroughs, AI applications, AI companies, AI research, AI ethics.
Return URLs as JSON array with titles.
Limit to 15 articles.
""",
        "description": "AI and machine learning news"
    }
}


def list_tasks():
    """List all query tasks in database"""
    db = Database()
    
    print("=" * 80)
    print("QUERY TASKS IN DATABASE")
    print("=" * 80)
    print()
    
    tasks = db.get_active_tasks()
    
    if not tasks:
        print("No query tasks found in database.")
        print()
        print("💡 Use option 2 to create tasks from templates")
        return
    
    for i, task in enumerate(tasks, 1):
        print(f"{i}. {task['task_name']}")
        print(f"   Status: {'Active' if task['is_active'] else 'Inactive'}")
        print(f"   Total Runs: {task['total_runs']}")
        print(f"   Links Found: {task['total_links_found']}")
        if task['last_run']:
            print(f"   Last Run: {task['last_run']}")
        print(f"   Prompt: {task['prompt_template'][:100]}...")
        print()


def list_templates():
    """List available task templates"""
    print("=" * 80)
    print("AVAILABLE TASK TEMPLATES")
    print("=" * 80)
    print()
    
    for i, (task_name, info) in enumerate(TASK_TEMPLATES.items(), 1):
        print(f"{i}. {task_name}")
        print(f"   Description: {info['description']}")
        print(f"   Prompt: {info['prompt'].strip()[:100]}...")
        print()


def create_task_from_template(template_name):
    """Create a task from template"""
    if template_name not in TASK_TEMPLATES:
        print(f"❌ Template '{template_name}' not found")
        return False
    
    db = Database()
    template = TASK_TEMPLATES[template_name]
    
    try:
        # Check if task already exists
        existing = db.get_query_task(template_name)
        if existing:
            print(f"⚠️  Task '{template_name}' already exists")
            return False
        
        # Create task
        task_id = db.create_query_task(
            task_name=template_name,
            prompt_template=template['prompt'].strip()
        )
        
        print(f"✅ Created task: {template_name} (ID: {task_id})")
        print(f"   Description: {template['description']}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating task: {e}")
        return False


def create_all_templates():
    """Create all template tasks"""
    print("=" * 80)
    print("CREATING ALL TEMPLATE TASKS")
    print("=" * 80)
    print()
    
    created = 0
    skipped = 0
    
    for template_name in TASK_TEMPLATES.keys():
        if create_task_from_template(template_name):
            created += 1
        else:
            skipped += 1
    
    print()
    print(f"✅ Created: {created} tasks")
    print(f"⚠️  Skipped: {skipped} tasks (already exist)")


def create_custom_task():
    """Create a custom task interactively"""
    print("=" * 80)
    print("CREATE CUSTOM TASK")
    print("=" * 80)
    print()
    
    task_name = input("Task name (e.g., 'my_custom_task'): ").strip()
    if not task_name:
        print("❌ Task name cannot be empty")
        return
    
    print()
    print("Enter your search prompt (press Enter twice when done):")
    print("Example: Find latest news about [topic]. Return URLs as JSON array.")
    print()
    
    lines = []
    while True:
        line = input()
        if line == "" and len(lines) > 0 and lines[-1] == "":
            break
        lines.append(line)
    
    prompt = "\n".join(lines).strip()
    
    if not prompt:
        print("❌ Prompt cannot be empty")
        return
    
    db = Database()
    
    try:
        task_id = db.create_query_task(
            task_name=task_name,
            prompt_template=prompt
        )
        
        print()
        print(f"✅ Created custom task: {task_name} (ID: {task_id})")
        
    except Exception as e:
        print(f"❌ Error creating task: {e}")


def main():
    print("=" * 80)
    print("QUERY TASK MANAGER")
    print("=" * 80)
    print()
    
    while True:
        print("Options:")
        print("  1. List tasks in database")
        print("  2. List available templates")
        print("  3. Create task from template")
        print("  4. Create all template tasks")
        print("  5. Create custom task")
        print("  6. Exit")
        print()
        
        choice = input("Choose option (1-6): ").strip()
        print()
        
        if choice == "1":
            list_tasks()
        
        elif choice == "2":
            list_templates()
        
        elif choice == "3":
            list_templates()
            template_name = input("Enter template name: ").strip()
            print()
            create_task_from_template(template_name)
            print()
        
        elif choice == "4":
            create_all_templates()
            print()
        
        elif choice == "5":
            create_custom_task()
            print()
        
        elif choice == "6":
            print("Goodbye!")
            break
        
        else:
            print("❌ Invalid option")
            print()


if __name__ == "__main__":
    main()
