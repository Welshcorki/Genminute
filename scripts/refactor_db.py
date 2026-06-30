import os

files = [
    'services/upload_service.py',
    'services/analysis_service.py',
    'routes/summary.py',
    'routes/meetings_action_items.py',
    'routes/meetings.py',
    'routes/google_auth.py',
    'routes/admin.py',
    'app.py',
    'tools/google_calendar_tool.py'
]

for f in files:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            
        content = content.replace('from database.sqlite_manager import DatabaseManager', 'from database import get_db_manager')
        content = content.replace('db = DatabaseManager(str(config.DATABASE_PATH))', 'db = get_db_manager()')
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Updated {f}")
