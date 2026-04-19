import re

# Example JSX from your Next.js project
jsx = """
<nav className="flex items-center gap-2 text-2xl font-bold text-orange-500">
  <Dumbbell className="w-8 h-8" />
  Enchanted Athletics
</nav>
"""

# Convert className → class
jsx = jsx.replace("className=", "class=")

# Convert Lucide React icons → lucide html icons
jsx = re.sub(
    r'<([A-Z][A-Za-z0-9]+)\s+([^>]*?)\s*/>',
    lambda m: f'<i data-lucide="{to_kebab(m.group(1))}" {m.group(2).replace("className=", "class=")}></i>',
    jsx
)

# Build preview HTML
html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<script src="https://cdn.tailwindcss.com"></script>

<!-- Lucide runtime -->
<script src="https://unpkg.com/lucide@latest"></script>

</head>
<body class="p-10">

{jsx}

<script>
lucide.createIcons();
</script>

</body>
</html>
"""

with open("preview_test.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Preview created: preview_test.html")