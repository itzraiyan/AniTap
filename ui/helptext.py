TOOL_OVERVIEW = (
    "AniTap: AniList Mass-Liker CLI\n"
    "─────────────────────────────────────────────\n"
    "• Mass-like posts/activities on AniList with a beautiful anime-themed CLI.\n"
    "• All prompts, menus, and errors are boxed and colored.\n"
    "• Inspirational anime quotes and banners at startup and completion.\n"
    "• Supports liking: globally, from users you follow, users who follow you, or all posts on a specific profile.\n"
    "• OAuth2 authentication for secure AniList access.\n"
    "• Multi-account support: add, switch, or remove AniList accounts.\n"
    "• Persistent config: save speed, default mode, and failed actions.\n"
    "• Robust rate limit handling, progress bars, and retry logic.\n"
    "• All prompts support -help for friendly, context-sensitive guidance.\n"
    "─────────────────────────────────────────────"
)

MAIN_MENU_HELP = (
    "Choose what you'd like to do:\n"
    "1: Like posts globally (all global activities)\n"
    "2: Like posts from users you follow\n"
    "3: Like posts from users who follow you\n"
    "4: Like all posts on a specific profile\n"
    "5: Human-like random liking (imitate real user)\n"
    "6: Follow random users\n"
    "7: Follow users via chain system\n"
    "8: Retry failed like actions\n"
    "9: Account management (add/switch/remove AniList accounts)\n"
    "10: Settings\n"
    "11: Exit\n"
    "Type -help at any prompt for context-sensitive help."
)

AUTH_CLIENT_ID_HELP = (
    "To get your AniList Client ID:\n"
    "1. Go to: https://anilist.co/settings/developer\n"
    "2. Click 'Create New Client'.\n"
    "3. Name = AniTap, Redirect URL = http://localhost\n"
    "4. Copy the Client ID from the table and paste it here."
)

AUTH_CLIENT_SECRET_HELP = (
    "After creating your AniTap client, copy the Client Secret from the developer table and paste it here."
)

AUTH_REDIRECT_URL_HELP = (
    "After approving access in your browser, AniList will redirect you to a page (it may fail to connect, that's fine!).\n"
    "Copy the full URL from your browser's address bar (it will contain ?code=...), and paste it here."
)

USERNAME_HELP = (
    "Enter your AniList username (as shown on your AniList profile page).\n"
    "This is not your email—use your display name!"
)

PROFILE_URL_HELP = (
    "Enter an AniList username or full profile URL (e.g. https://anilist.co/user/YourName/).\n"
    "Tool will extract and validate the user for you."
)

SETTINGS_HELP = (
    "You can adjust AniTap's speed, default liking mode, and other options here.\n"
    "Settings are saved locally and never shared."
)