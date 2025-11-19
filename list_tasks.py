"""Quick script to list available query tasks"""
from manage_query_tasks import TASK_TEMPLATES

print("=" * 80)
print("AVAILABLE QUERY TASK TEMPLATES")
print("=" * 80)
print()

for i, (name, info) in enumerate(TASK_TEMPLATES.items(), 1):
    print(f"{i}. {name}")
    print(f"   {info['description']}")
    print()

print("=" * 80)
print(f"Total: {len(TASK_TEMPLATES)} templates available")
print()
print("To create tasks:")
print("  python manage_query_tasks.py")
print()
print("Or create all at once:")
print("  python -c \"from manage_query_tasks import create_all_templates; create_all_templates()\"")
