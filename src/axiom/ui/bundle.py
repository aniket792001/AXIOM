"""
Axiom UI Bundler
Assembles modular React components and hooks into src/axiom/ui/app.jsx
for zero-configuration in-browser execution with Babel Standalone.
Preserves the full modular source code in components/, hooks/, and services/
for direct portability to React Native / Expo.
"""

import re
from pathlib import Path

UI_DIR = Path(__file__).resolve().parent

ORDERED_FILES = [
    # 1. API Service
    UI_DIR / "services" / "api.js",
    # 2. Hooks
    UI_DIR / "hooks" / "useAuth.js",
    UI_DIR / "hooks" / "useChat.js",
    UI_DIR / "hooks" / "useVault.js",
    UI_DIR / "hooks" / "useContradiction.js",
    UI_DIR / "hooks" / "useBenchmark.js",
    # 3. Components
    UI_DIR / "components" / "Header.jsx",
    UI_DIR / "components" / "Sidebar.jsx",
    UI_DIR / "components" / "ChatScreen.jsx",
    UI_DIR / "components" / "VaultScreen.jsx",
    UI_DIR / "components" / "DiffMatrixScreen.jsx",
    UI_DIR / "components" / "BenchmarkScreen.jsx",
    UI_DIR / "components" / "HistoryScreen.jsx",
    UI_DIR / "components" / "CitationDrawer.jsx",
    UI_DIR / "components" / "ProfileModal.jsx",
    UI_DIR / "components" / "DocumentVisualizerModal.jsx",
    UI_DIR / "components" / "AuthGateModal.jsx",
    UI_DIR / "components" / "AppShell.jsx",
]

def clean_source(content: str) -> str:
    lines = []
    for line in content.splitlines():
        trimmed = line.strip()
        # Strip import statements
        if trimmed.startswith("import ") or trimmed.startswith("import{"):
            continue
        # Strip export keywords while keeping declaration
        line = re.sub(r"^export\s+(default\s+)?", "", line)
        lines.append(line)
    return "\n".join(lines)

def build_bundle():
    bundle_parts = [
        "/* ==========================================================================\n"
        "   AXIOM SCORE ENGINE - COMPILED REACT APPLICATION BUNDLE (v3.0)\n"
        "   Linear / Stripe Clean Enterprise Aesthetic - Zero Congestion Design\n"
        "   Assembled from modular source components (100% Expo / React Native Portable)\n"
        "   ========================================================================== */\n",
        "const { useState, useEffect, useRef, useMemo, useCallback } = React;\n",
    ]

    for file_path in ORDERED_FILES:
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            continue
        content = file_path.read_text(encoding="utf-8")
        cleaned = clean_source(content)
        bundle_parts.append(f"\n/* --- SOURCE: {file_path.name} --- */\n")
        bundle_parts.append(cleaned)

    # Add root render mount
    bundle_parts.append("""
/* --- ENTRYPOINT MOUNT --- */
const rootElement = document.getElementById("root");
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<AppShell />);
}
""")

    output_path = UI_DIR / "app.jsx"
    output_path.write_text("\n".join(bundle_parts), encoding="utf-8")
    print(f"Successfully generated {output_path} ({output_path.stat().st_size} bytes)")

if __name__ == "__main__":
    build_bundle()
