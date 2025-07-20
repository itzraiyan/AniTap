# AniTap: The Ultimate AniList Mass-Liker CLI 🌸

![AniTap Banner](https://files.catbox.moe/jx8op2.png)

> **Note:** This project contains AI-generated content, but the vision and direction are crafted by the project owner.

---

AniTap is a beginner-friendly, interactive Python tool for **mass-liking AniList activities**—with maximum anime vibes, beautiful boxed layouts, and clever anti-bot features. Whether you want to spread positivity on AniList, support friends, or just automate your likes in a human-like way, AniTap is your companion.

---

## ✨ Features

* 🖼️ **Anime-themed terminal interface**  
  Random ASCII art banners and motivational anime quotes at every session!
* 🎯 **Mass-like AniList activities:**  
  - Like all global activities  
  - Like posts from people you follow  
  - Like all posts on a specific profile  
  - Like posts from your followers  
  - **Human-Like Random Liker:** AniTap imitates true human behavior—random sources, random breaks, random selection, unpredictable timing.
  - **Chain & Random Follow:** Follow random users via chain system or global extraction.
* 🔒 **Secure OAuth2 authentication:**  
  Guided, step-by-step login using AniList API credentials.  
  No password ever requested; tokens are stored locally.
* 👤 **Multi-account support:**  
  Add, switch, and remove AniList accounts at any time.
* 🛡️ **Rate limit protection:**  
  Spinner/countdown and automatic retry for safe API use.  
  **Progress bar** for all mass actions (liking, following, etc.).
* ⏱️ **Progress bars & session summaries:**  
  See stats for processed, liked, skipped, and failed posts.
* 🔁 **Failed actions saved for easy retry:**  
  AniTap always lets you retry failed likes!
* ⚙️ **Settings:**  
  Liking speed, default mode, theme, and more—saved to local config.
* 🧑‍🎓 **Beginner-friendly:**  
  All prompts support `-help` for context-sensitive guidance.
* 🐍 **Pure Python:**  
  Works on Android (Termux), Linux, Windows, and more.
* 🛡️ **Privacy:**  
  All data/tokens are stored locally only. Nothing leaves your device except for AniList API calls.

---

## 📦 Installation & Quickstart

### 🟩 Android (Termux)

1. **Install Termux:**  
   Get [Termux from F-Droid](https://f-droid.org/packages/com.termux/) or Google Play.

2. **Set up Termux:**
   ```sh
   pkg update -y
   pkg upgrade -y
   pkg install -y python git
   ```

3. **Get AniTap:**
   ```sh
   git clone https://github.com/YOUR_USERNAME/AniTap.git
   cd AniTap
   ```

4. **Install requirements:**
   ```sh
   pip install -r requirements.txt
   ```

5. **Run AniTap:**
   ```sh
   python main.py
   ```

---

### 🟦 Linux / 🟨 Windows

1. **Install Python 3 and Git**
2. **Clone the repo:**
   ```sh
   git clone https://github.com/YOUR_USERNAME/AniTap.git
   cd AniTap
   ```
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Run AniTap:**
   ```sh
   python main.py
   ```

---

## ▶️ Usage Guide

Start AniTap with:

```sh
python main.py
```

You'll be greeted by anime ASCII banners, a random quote, and a boxed main menu.

### 🏠 Main Menu

1. **Like posts globally**
2. **Like posts from users you follow**
3. **Like posts from users who follow you**
4. **Like all posts on a specific profile**
5. **Human-like random liking (imitate real user)**
6. **Follow random users**
7. **Follow users via chain system**
8. **Retry failed like actions**
9. **Account management**
10. **Settings**
11. **Exit**

**Type the number or `-help` at any prompt for friendly, detailed guidance!**

---

### 🔑 Authentication

- AniTap uses AniList OAuth2 for login.
- You'll be guided to create an AniList API Client (Client ID/Secret) at [AniList Developer Settings](https://anilist.co/settings/developer).
- Copy the Client ID and Secret as prompted.
- AniTap generates the login URL, guides you through the flow, and securely saves your token locally.
- Multi-account support: You can add, switch, or remove accounts anytime.

---

### 🎯 Liking Modes

#### **Global Mode**
- Like every visible public activity on AniList.
- Uses robust, paginated GraphQL queries for all activity types (from gaf.py, gaf2.py, sal.py).

#### **Following Mode**
- Like posts only from users you follow.
- Uses paginated, reliable queries for fetching your following list (from sal.py/tree.py).

#### **Followers Mode**
- Like posts only from users who follow you.
- Uses paginated, reliable queries for fetching your followers (from sal.py/tree.py).

#### **Profile Mode**
- Like all posts on a specific user's profile (give username or profile URL).

#### **Chain System**
- Follow users via BFS expansion (your following → their following → ...).
- Uses exact chain logic from tree.py for robust, non-repeating user discovery.

#### **Random Follow**
- Extracts user IDs from global activities using gaf2.py logic for following random AniList users.

#### **Human-Like Random Liker Mode**
**NEW!** AniTap can now **imitate true human behavior**:
- Randomly selects source: global, following, followers, or profiles you provide.
- Randomly picks only a few activities per batch.
- Randomly skips some activities (not every post is liked).
- Delays between likes are unpredictable—sometimes just seconds, often minutes, sometimes even a long break (15–60 minutes or more!).
- Occasionally takes a "human break" for up to an hour.
- The API can't tell you're a bot—your liking pattern looks just like that of a real person!
- **Perfect for stealth, fun, or long-running positivity!**

#### **Session Summaries**
- Boxed, colored stats after each run: total processed, liked, skipped, failed.
- Failed actions saved for retry.

---

### ⚙️ Settings

- Set liking speed: fast, medium, slow (affects delay between likes)
- Set default mode (which workflow starts first)
- Change color theme
- Clear failed actions list
- All settings saved in `~/.anitap_config.json`

---

### 🔁 Error Handling & Retry

- Any failed like actions are recorded.
- AniTap always lets you retry failed actions—instantly, or later.

---

### ⏳ Progress Bars & Rate Limit Handling

- **Progress bars** (via TQDM) for all mass actions—liking, following, chain, etc.
- **Rate limit spinner** and boxed prompts for “rate limit hit”, “rate limit over”, etc. These are preserved for clarity and user-friendliness, just like the original code.

---

## 🌸 Example Session

```sh
$ python main.py

░█████╗░███╗░░██╗██╗██████╗░░█████╗░██████╗░████████╗
██╔══██╗████╗░██║██║██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝

“The world isn’t perfect. But it’s there for us, doing the best it can.” – Roy Mustang

What would you like to do?
  1. Like posts globally (all global activities)
  2. Like posts from users you follow
  3. Like posts from users who follow you
  4. Like all posts on a specific profile
  5. Human-like random liking (imitate real user)
  6. Follow random users
  7. Follow users via chain system
  8. Retry failed like actions
  9. Account management
  10. Settings
  11. Exit
(Type the number or -help for info)
> 4

[Human-Like Mode begins: AniTap randomly likes a handful of activities from global/following/followers/profiles, waits random intervals (sometimes several minutes!), skips some likes, and occasionally "takes a break" for 15-60 minutes. The session runs for a realistic number of likes before ending automatically.]

Thanks for using AniTap! Keep spreading anime love!
“No matter how deep the night, it always turns to day, eventually.” – Brook
```

---

## 💡 Tips & Best Practices

- **Type `-help` at any prompt for context-sensitive help.**
- Tokens are saved only on your device. Safe, secure, and private.
- Multi-account management is easy—switch anytime.
- AniTap never overwrites, deletes, or shares your data without your confirmation.
- The tool is designed to be friendly, beautiful, and easy for all users—no coding knowledge needed!

---

## 📂 Project Structure

```
AniTap/
│
├── anilist/                 # AniList API logic and authentication
│   ├── api.py               # GraphQL queries: fetch activities, like posts, user info
│   ├── auth.py              # OAuth authentication, account/token storage
│   ├── ratelimit.py         # Rate limit detection and spinner
│
├── tap/                     # Main liking logic & workflows
│   ├── liker.py             # Implements global, following, followers, profile, chain, and human-like modes
│   ├── summary.py           # Session summary, failed/retry logic
│
├── config/                  # Configuration management
│   ├── config.py            # Loads/saves user settings
│
├── ui/                      # User interface components
│   ├── banners.py           # ASCII banners, anime quotes, intro/outro
│   ├── colors.py            # Boxed, colored output
│   ├── helptext.py          # Help messages for prompts/menus
│   ├── prompts.py           # Boxed prompts, menus, confirmations, progress bars
│
├── main.py                  # CLI entrypoint and main menu
├── requirements.txt         # Dependencies
├── LICENSE                  # License
└── README.md                # This doc
```

---

## 💡 Frequently Asked Questions

**Q: Do I need an AniList account?**  
A: Yes—sign up at [anilist.co](https://anilist.co/).

**Q: How do I add my AniList API credentials?**  
A: AniTap will guide you step-by-step. You'll create a client at [AniList Developer Settings](https://anilist.co/settings/developer) and copy the Client ID and Secret.

**Q: Is my data safe?**  
A: Yes. All tokens and config are stored locally—nothing leaves your device except requests to AniList.

**Q: Will this like private posts?**  
A: AniTap likes all visible activities for your account, including your own private posts if you authenticate.

**Q: How does Human-Like Mode work?**  
A: See [Human-Like Random Liker Mode](#-human-like-random-liker-mode)—it randomizes everything, mimics breaks, skips some activities, and is designed to make your pattern indistinguishable from a bot.

**Q: What if I get rate limited?**  
A: AniTap automatically detects rate limits, shows a spinner, waits, and resumes safely.

**Q: Where are failed actions saved?**  
A: In your config file, for easy retry.

**Q: Can I use this on Termux/mobile?**  
A: Yes! Output is wrapped for mobile screens and uses boxed layouts.

---

## 🛡️ Privacy & Security

- All tokens are saved ONLY on your device (`~/.anitap_config.json`).
- No data is sent anywhere except AniList API.
- You can delete tokens and config at any time.
- AniTap never asks for your AniList password.

---

## 🤝 Contributing

- Issues and pull requests are welcome!
- New ideas, features, anime quotes, banners, or improvements are always appreciated.

---

## 📜 License

MIT License. See LICENSE for details.

---

## 🌸 Credits & Acknowledgments

- UI inspiration: [AniPort](https://github.com/itzraiyan/AniPort)
- Liking logic: [anilist-auto-liker](https://github.com/DanielWTE/anilist-auto-liker), [AniLikerV2](https://github.com/anas1412/AniLikerV2)
- Chain/following/follower logic: [tree.py], [sal.py], [gaf.py], [gaf2.py] (used as inspiration for reliable mass operations)
- ASCII banners, anime quotes, and terminal magic!

---

## 🛑 Disclaimer

> **This project contains AI-generated content. Use at your own risk, and always review code before running.**

---

**Enjoy AniTap—and may your anime positivity reach every corner of AniList!**  
*“No matter how deep the night, it always turns to day, eventually.”* – Brook

---