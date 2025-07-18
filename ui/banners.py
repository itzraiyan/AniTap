import random

ASCII_BANNERS = [
    r"""
     /\_/\  
    ( o.o ) 
     > ^ <    AniTap: AniList Mass-Liker
    """,
    r"""
██████████████████████████████████████████
██▀▄─██▄─▀█▄─▄█▄─▄█▄─▄▄─█─▄▄─█▄─▄▄▀█─▄─▄─█
██─▀─███─█▄▀─███─███─▄▄▄█─██─██─▄─▄███─███
▀▄▄▀▄▄▀▄▄▄▀▀▄▄▀▄▄▄▀▄▄▄▀▀▀▄▄▄▄▀▄▄▀▄▄▀▀▄▄▄▀▀
    """,
    r"""
░█████╗░███╗░░██╗██╗██████╗░░█████╗░██████╗░████████╗
██╔══██╗████╗░██║██║██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝
███████║██╔██╗██║██║██████╔╝██║░░██║██████╔╝░░░██║░░░
██╔══██║██║╚████║██║██╔═══╝░██║░░██║██╔══██╗░░░██║░░░
██║░░██║██║░╚███║██║██║░░░░░╚█████╔╝██║░░██║░░░██║░░░
╚═╝░░╚═╝╚═╝░░╚══╝╚═╝╚═╝░░░░░░╚════╝░╚═╝░░╚═╝░░░╚═╝░░░
    """,
    r"""
─█▀▀█ █▀▀▄ ─▀─ ░█▀▀█ █▀▀█ █▀▀█ ▀▀█▀▀ 
░█▄▄█ █──█ ▀█▀ ░█▄▄█ █──█ █▄▄▀ ──█── 
░█─░█ ▀──▀ ▀▀▀ ░█─── ▀▀▀▀ ▀─▀▀ ──▀──
    """,
]

QUOTES = [
    "“The world isn’t perfect. But it’s there for us, doing the best it can.” – Roy Mustang",
    "“No one knows what the future holds. That’s why its potential is infinite.” – Rintarou Okabe",
    "“Whatever you lose, you’ll find it again. But what you throw away you’ll never get back.” – Kenshin Himura",
    "“A lesson without pain is meaningless.” – Edward Elric",
    "“If you can’t find a reason to fight, then you shouldn’t be fighting.” – Akame",
    "“No matter how deep the night, it always turns to day, eventually.” – Brook"
]

INTRO = (
    "Welcome, anime fan!\n"
    "AniTap lets you mass-like AniList activities, with friendly banners and anime quotes.\n"
    "Type -help at any prompt for extra info. Enjoy!"
)

OUTRO = (
    "Thanks for using AniTap! 🌸\n"
    "Keep spreading anime love, and see you next time!"
)

def print_banner():
    print(random.choice(ASCII_BANNERS))

def print_random_quote():
    print("\n" + random.choice(QUOTES) + "\n")

def print_intro():
    print(INTRO)

def print_outro():
    print("\n" + OUTRO + "\n")
    print_random_quote()