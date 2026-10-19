# ZYROX VIDEO DOWNLOADER — Termux (phone) mode

Vercel ke datacenter IP ko YouTube block karta hai (bot-check), chahe token
sahi ho. Phone ka IP residential hai — isliye bot ko phone (Termux) pe
polling mode me chalao. Vercel wala deploy sirf PO-token server ke liye
rehta hai, bot ka kaam phone karega.

## Pehli baar

Termux me:

```bash
pkg install -y git
git clone https://github.com/KMJ-TIPS/zyrox-video-downloader
cd zyrox-video-downloader
bash termux/setup.sh
```

Setup poochhega: `BOT_TOKEN` (BotFather wala) aur `ADMIN_IDS` (default
8923702128). Fir webhook khud delete hoga aur bot start ho jayega.

## Dobara chalana

```bash
cd zyrox-video-downloader
bash termux/run.sh
```

## Zaroori baatein

- Bot chalte waqt Termux khula rakho (wake-lock on hai, par Android phir
  bhi background me maar sakta hai).
- Vercel pe webhook dobara set mat karna — warna polling ko updates nahi
  milenge (webhook > polling).
- `.env` me token hai — kisi ko mat bhejo.
- Vercel deploy mat hatana — PO-token server wahi se chalta hai.
