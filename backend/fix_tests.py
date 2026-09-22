import os
import re

directories = ["app/api/routers", "tests", "scripts", "."]

pattern = re.compile(r'min_discount_pct=([0-9\.]+),?\s*')
pattern2 = re.compile(r'min_discount_pct:\s*Optional\[float\]\s*=\s*Query\(None\),?\s*')
pattern3 = re.compile(r'min_discount_pct=req\.min_discount_pct,?\s*')

for d in directories:
    for root, _, files in os.walk(d):
        if 'venv' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                
                new_content = pattern.sub('', content)
                new_content = pattern2.sub('', new_content)
                new_content = pattern3.sub('', new_content)
                new_content = new_content.replace('None', 'None')
                
                if new_content != content:
                    with open(path, 'w') as f:
                        f.write(new_content)
                    print(f"Fixed {path}")

