#!/usr/bin/env python3
"""
AniList Backup Tool - Main CLI Entrypoint

Handles session start, banner and intro, main menu, and routes to export/import/info flows.
All UX is decorated and anime-themed, as per the project style guide.
"""

import sys
import os

# ===== Import UI/Helpers =====
from ui.banners import print_banner, print_outro, print_random_quote
from ui.prompts import menu_boxed, print_info, print_success, print_error, prompt_boxed
from ui.helptext import TOOL_OVERVIEW, MAIN_MENU_HELP
from ui.motd import show_motd_if_needed   # <-- ADDED

# ===== Import Workflow Modules =====
from backup.exporter import export_workflow
from backup.importer import import_workflow

# ===== Import Liker Functions =====
from tap.liker import (
    like_global,
    like_following,
    like_followers,
    like_profile,
    human_like_liker,
)

# ===== Ensure output dir exists =====
from backup.output import ensure_output_dir

def main():
    ensure_output_dir()
    print_banner()
    show_motd_if_needed()
    print_info("Welcome to your AniList Backup & Restore Tool!\n")
    print_random_quote()

    while True:
        # Main menu
        choice = menu_boxed(
            "What would you like to do?",
            [
                "Like posts globally (all global activities)",
                "Like posts from users you follow",
                "Like posts from users who follow you",
                "Like posts on a specific profile",
                "Human-like random liking (imitate real user)",
                "Export your AniList (create a backup)",
                "Import from a backup (restore your list)",
                "Learn more about this tool",
                "Settings",
                "Exit"
            ],
            helpmsg=MAIN_MENU_HELP +
                "\n1: Like activities from the global feed.\n"
                "2: Like activities from users you follow.\n"
                "3: Like activities from users who follow you.\n"
                "4: Like activities on one or more specified profiles.\n"
                "5: Human-like mode, randomly likes activities with random breaks.\n"
                "6: Export anime/manga backup.\n"
                "7: Restore from backup.\n"
                "8: Learn more about features.\n"
                "9: Settings menu.\n"
                "10: Exit."
        )

        if choice == 1:
            like_global({})
            print_outro()
            break

        elif choice == 2:
            like_following({})
            print_outro()
            break

        elif choice == 3:
            like_followers({})
            print_outro()
            break

        elif choice == 4:
            like_profile({})
            print_outro()
            break

        elif choice == 5:
            human_like_liker({})
            print_outro()
            break

        elif choice == 6:  # Export
            print_info("You have chosen to EXPORT (backup) your AniList!")
            export_workflow()
            print_outro()
            break

        elif choice == 7:  # Import/Restore
            print_info("You have chosen to IMPORT (restore) a backup!")
            import_workflow()
            print_outro()
            break

        elif choice == 8:  # Learn more
            print_info(TOOL_OVERVIEW)
            input("\nPress Enter to return to the main menu...")

        elif choice == 9:  # Settings
            print_info("Settings menu coming soon!")
            input("\nPress Enter to return to the main menu...")

        elif choice == 10:  # Exit
            print_success("Thanks for using AniList Backup Tool! See you next time, senpai!")
            print_outro()
            sys.exit(0)

        else:
            print_error("Invalid selection. Please choose a valid option.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        from ui.colors import boxed_text
        msg = boxed_text("Interrupted by user. Goodbye!", "RED", 60)
        print(msg)
        sys.exit(0)
    except Exception as e:
        try:
            from rich.console import Console
            from rich.traceback import Traceback
            Console().print(Traceback())
        except ImportError:
            print_error(f"Unexpected error: {e}")
        sys.exit(1)