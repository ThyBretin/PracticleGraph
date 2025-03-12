import re
from particle_utils import logger

def extract_calls(content):
    """Extract API calls from content."""
    calls = []
    for line in content.splitlines():
        if "fetch(" in line.lower():
            url = re.search(r"fetch\(['\"]([^'\"]+)['\"]", line)
            if url:
                calls.append(url.group(1))
        if "supabase" in line.lower():
            if "signin" in line.lower():
                calls.append("supabase.auth.signIn")
            elif "signout" in line.lower():
                calls.append("supabase.auth.signOut")
        if "ismockenabled" in line.lower() and "ismockenabled()" not in line:
            calls.append("isMockEnabled()")
    return list(dict.fromkeys(calls))  # Dedupe