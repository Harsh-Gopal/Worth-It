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

    # We need to find fetch(`${API_BASE}/...`) and fix the trailing quote.
    # The string starts with fetch(`${API_BASE}/ and ends with " or ' or `
    # It might be followed by , { or )
    
    # Let's just fix the exact replacements I did.
    # I replaced fetch("/api/ with fetch(`${API_BASE}/
    # So the original was fetch("/api/path") -> fetch(`${API_BASE}/path")
    # Let's replace ") with `) when it follows API_BASE
    content = re.sub(r'(fetch\(`\$\{API_BASE\}[^`"]*?)"\)', r'\1`)', content)
    
    # Also for , { it was fetch("/api/path", { -> fetch(`${API_BASE}/path", {
    content = re.sub(r'(fetch\(`\$\{API_BASE\}[^`"]*?)"\s*,', r'\1` ,', content)

    # I also replaced fetch(`/api/ with fetch(`${API_BASE}/
    # That one was already a backtick string, so it became fetch(`${API_BASE}/path`) which is perfectly valid!
    # Wait, what if the string had other variables?
    # e.g. fetch(`/api/history/${id}`) -> fetch(`${API_BASE}/history/${id}`) - this is valid!

    with open(path, "w") as f:
        f.write(content)

print("Done fixing quotes!")
