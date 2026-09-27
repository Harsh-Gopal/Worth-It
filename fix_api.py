import os
import re

frontend_dir = "frontend/src"

files_to_fix = [
    "pages/TrackHistory.tsx",
    "components/search/KeywordInput.tsx",
    "components/search/LocationSelector.tsx",
    "hooks/useAlerts.ts",
    "pages/Monitoring.tsx",
    "hooks/useWishlist.ts",
    "App.tsx"
]

for rel_path in files_to_fix:
    path = os.path.join(frontend_dir, rel_path)
    with open(path, "r") as f:
        content = f.read()

    # Determine relative path to lib/api.ts
    depth = rel_path.count("/")
    if depth == 0:
        api_path = "./lib/api"
    else:
        api_path = "../" * depth + "lib/api"

    # Only add import if not present
    if "API_BASE" not in content and "import { API_BASE" not in content:
        import_stmt = f'import {{ API_BASE }} from "{api_path}";\n'
        # Insert after the first import block, or at the top
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import '):
                lines.insert(i + 1, import_stmt.strip())
                break
        else:
            lines.insert(0, import_stmt.strip())
        content = '\n'.join(lines)

    # Replace all fetch("/api/
    content = content.replace('fetch("/api/', 'fetch(`${API_BASE}/')
    content = content.replace('fetch(`/api/', 'fetch(`${API_BASE}/')

    with open(path, "w") as f:
        f.write(content)

print("Done fixing API_BASE!")
