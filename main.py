#!/usr/bin/env python3
import sys
import os
from ui.banners import print_banner, print_outro, print_random_quote
from ui.prompts import menu_boxed, print_info, print_success, print_error, print_warning, prompt_boxed
from ui.helptext import TOOL_OVERVIEW, MAIN_MENU_HELP, SETTINGS_HELP
from config.config import load_config, save_config
from anilist.auth import choose_account_flow
from tap.liker import (
    like_global,
    like_following,
    like_followers,
    like_profile,
    human_like_liker,
    follow_random_users,
    follow_chain_users
)
from tap.summary import retry_failed_actions

def account_management(config):
    print_info("Account Management")
    username, token = choose_account_flow()
    config["token"] = token
    config["last_used_account"] = username
    save_config(config)
    print_success(f"Authenticated as: {username}")
    return config

def settings_menu(config):
    print_info("Settings")
    while True:
        choice = menu_boxed(
            "Settings Menu:",
            [
                f"Set liking speed (currently: {config.get('liking_speed', 'medium')})",
                f"Set default mode (currently: {config.get('default_mode', 'global')})",
                "Clear failed actions list",
                "Show help",
                "Back to main menu"
            ],
            helpmsg=SETTINGS_HELP
        )
        if choice == 1:
            speed = prompt_boxed(
                "Set liking speed (fast / medium / slow):",
                default=config.get("liking_speed", "medium"),
                color="CYAN",
                helpmsg="Controls how quickly AniTap likes posts. 'fast' is quickest, but may trigger rate limits."
            ).lower()
            if speed in ("fast", "medium", "slow"):
                config["liking_speed"] = speed
                save_config(config)
                print_success(f"Liking speed set to {speed}")
            else:
                print_warning("Invalid speed. Please enter fast, medium, or slow.")
        elif choice == 2:
            mode = prompt_boxed(
                "Set default mode (global / following / profile):",
                default=config.get("default_mode", "global"),
                color="CYAN",
                helpmsg="Default mode determines which liking workflow starts by default."
            ).lower()
            if mode in ("global", "following", "profile"):
                config["default_mode"] = mode
                save_config(config)
                print_success(f"Default mode set to {mode}")
            else:
                print_warning("Invalid mode. Please enter global, following, or profile.")
        elif choice == 3:
            config["failed_actions"] = []
            save_config(config)
            print_success("Failed actions list cleared.")
        elif choice == 4:
            print_info(SETTINGS_HELP)
        elif choice == 5:
            break

def main():
    config = load_config()
    print_banner()
    print_info("Welcome to AniTap! Your anime-themed AniList mass-liker tool.")
    print_random_quote()

    while True:
        choice = menu_boxed(
            "What would you like to do?",
            [
                "Like posts globally (all global activities)",
                "Like posts from users you follow",
                "Like posts from users who follow you",
                "Like posts on a specific profile",
                "Human-like random liking (imitate real user)",
                "Follow random users",
                "Follow users via chain system",
                "Retry failed like actions",
                "Account management (add/switch/remove)",
                "Settings",
                "Exit"
            ],
            helpmsg=MAIN_MENU_HELP +
            "\n5: Human-like mode randomly likes activities from different sources with random breaks/delays." +
            "\n6: Follow random users." +
            "\n7: Follow users via chain system." +
            "\n8: Retry any failed likes from previous sessions."
        )

        try:
            if choice == 1:
                if not config.get("token"):
                    print_warning("No AniList account authenticated yet. Please add an account first!")
                    config = account_management(config)
                like_global(config)
                print_outro()
                break

            elif choice == 2:
                if not config.get("token"):
                    print_warning("No AniList account authenticated yet. Please add an account first!")
                    config = account_management(config)
                like_following(config)
                print_outro()
                break

            elif choice == 3:
                if not config.get("token"):
                    print_warning("No AniList account authenticated yet. Please add an account first!")
                    config = account_management(config)
                like_followers(config)
                print_outro()
                break

            elif choice == 4:
                if not config.get("token"):
                    print_warning("No AniList account authenticated yet. Please add an account first!")
                    config = account_management(config)
                like_profile(config)
                print_outro()
                break

            elif choice == 5:
                if not config.get("token"):
                    print_warning("No AniList account authenticated yet. Please add an account first!")
                    config = account_management(config)
                human_like_liker(config)
                print_outro()
                break

            elif choice == 6:
                if not config.get("token"):
                    print_warning("No AniList account authenticated yet. Please add an account first!")
                    config = account_management(config)
                follow_random_users(config)
                print_outro()
                break

            elif choice == 7:
                if not config.get("token"):
                    print_warning("No AniList account authenticated yet. Please add an account first!")
                    config = account_management(config)
                follow_chain_users(config)
                print_outro()
                break

            elif choice == 8:
                if not config.get("token"):
                    print_warning("No AniList account authenticated yet. Please add an account first!")
                    config = account_management(config)
                retry_failed_actions(config, config.get("token"))

            elif choice == 9:
                config = account_management(config)

            elif choice == 10:
                settings_menu(config)

            elif choice == 11:
                print_success("Thanks for using AniTap! See you next time, senpai!")
                print_outro()
                sys.exit(0)

            else:
                print_error("Invalid selection. Please choose a valid option.")
        except KeyboardInterrupt:
            print_warning("Interrupted by user. Exiting gracefully...")
            print_outro()
            sys.exit(0)
        except Exception as e:
            try:
                from rich.console import Console
                from rich.traceback import Traceback
                Console().print(Traceback())
            except ImportError:
                print_error(f"Unexpected error: {e}")
            sys.exit(1)

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