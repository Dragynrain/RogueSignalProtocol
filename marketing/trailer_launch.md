# Trailer launch kit

Everything needed to put `marketing/trailer_final.mp4` (35s, 1080p30) out into the world: YouTube upload fields, the itch page change, an itch devlog post, short posts for other channels, and the order to do it in.

The trailer opens with about 13 seconds of AI-generated video before the gameplay. That matters for two things below: YouTube's synthetic content checkbox, and which communities to skip.

---

## 1. YouTube

### Title

```
Rogue Signal Protocol - Trailer | Free Stealth Roguelike (Windows, Linux, Steam Deck)
```

Shorter alternative if the long one gets cut off in search:

```
Rogue Signal Protocol - Official Trailer (Free Stealth Roguelike)
```

### Description

```
Rogue Signal Protocol is a turn-based stealth roguelike. You're a digital consciousness trying to get out of a corporate network, and every enemy shows you the next 3 tiles it plans to step on. Runs take 10-15 minutes. Die once and the save is deleted.

Free and open source (MIT). Windows, Linux, and Steam Deck.

Download: https://dragynrain.itch.io/rogue-signal-protocol
Source: https://github.com/Dragynrain/RogueSignalProtocol
Discord: https://discord.gg/5fykUtECqz

What's in it:
- No RNG in combat or movement. Only the level layout is random.
- 3 procedurally generated network levels, 8 enemy types, 13 exploits
- Exploits cost RAM and build heat. Get too loud and the Admin Avatar comes looking for you.
- Graphical tiles or ASCII glyphs, same game either way
- 47 achievements and a 20-level Ascension mode once you win
- Hands-on tutorial level, full gamepad support (Xbox, PlayStation, Steam Deck)

Made solo by Adam Forster (Dragynrain). The opening sequence and the game's art and music were made with AI tools, then curated and edited. All gameplay in the trailer is real footage from the game.

#roguelike #stealth #indiegame
```

### Tags

```
rogue signal protocol, roguelike, stealth roguelike, turn based, traditional roguelike, cyberpunk, hacking game, free game, open source game, linux game, steam deck, ascii, indie game, permadeath, itch.io
```

### Upload settings

- Thumbnail: `marketing/youtube_thumbnail.jpg` (1280x720, the end card). The subtitle text is small at thumbnail size. If the video doesn't get clicks, try a gameplay frame with the yellow movement arrows and just the title on top.
- Altered or synthetic content: answer **Yes**. The opening shows a realistic-looking person, which is the case YouTube asks you to label. It costs nothing and avoids a strike later.
- Made for kids: No.
- Category: Gaming. Add the game title in the game field if YouTube offers it.
- Visibility: upload as Unlisted first, check it plays, then switch to Public when the itch devlog goes up.
- Add it to a "Rogue Signal Protocol" playlist so future videos stack up under it.
- Comments: on. Answer the first few yourself.
- Music: the soundtrack is the game's own, so there's nothing to claim. If Content ID flags it anyway, dispute it.

---

## 2. itch.io game page

1. Edit the game page and paste the YouTube URL into the "Gameplay video or trailer" field. It shows up at the top of the page.
2. Check that the AI disclosure on the page is still set and matches the README credits (art and audio, now the trailer opening too).
3. No change needed to the page text. The current description in `itch_io_page_formatted.txt` still matches the game.

---

## 3. itch devlog post

Post type: Devlog (or Announcement). Paste the YouTube link on its own line so itch embeds it.

Title:

```
Rogue Signal Protocol has a trailer
```

Body:

```
It took a while, but there's finally a trailer.

[YouTube link here]

Most of it is real gameplay, recorded by a script that plays the game and captures specific moments: an enemy's queued path, a sneak attack from a blind spot, an exploit that runs the heat up, the Admin showing up, and a death screen. Then another script cuts the clips together with captions and the end card. Doing it that way meant I could re-record the whole thing after a bug fix instead of trying to replay a lucky run by hand.

The opening 13 seconds aren't gameplay. They're AI-generated video of the setup: someone in a lab getting pulled into the network and coming out the other side as a signal. The rest of the game's art and music came from AI tools too, which the credits already say.

One thing I didn't think about until it was almost too late: the trailer ends on a death, and death in this game deletes your save. The capture script now runs in its own throwaway data folder so recording a trailer doesn't wipe my actual run.

If you haven't tried it: runs are 10-15 minutes, enemies show you their next three moves, and dying deletes the save. It's free, on Windows and Linux, and runs on the Steam Deck.

Comments, Discord, and GitHub issues all reach me. If the trailer made you want to try it and the game didn't match the trailer, I'd like to hear that too.
```

---

## 4. Short posts

### Discord (your server)

```
The trailer is up: [YouTube link]

35 seconds, mostly real gameplay. If you want to help, a like or a share does more for a small game than you'd think.
```

### Bluesky / Mastodon

```
Rogue Signal Protocol finally has a trailer. Turn-based stealth roguelike, enemies show you their next three moves, death deletes your save. Free and open source on Windows, Linux, and Steam Deck.

[YouTube link]

#roguelike #indiedev #gamedev #linuxgaming
```

Mastodon also has #ScreenshotSaturday on Saturdays. A 5-10 second clip of the yellow movement arrows works better there than the full trailer.

### Reddit

Reddit prefers a native video upload over a YouTube link. Upload `trailer_final.mp4` directly and put the links in a comment.

r/roguelikes title:

```
Rogue Signal Protocol - trailer for my free stealth roguelike where enemies show their next 3 moves
```

First comment:

```
Solo dev here. It's turn-based, deterministic combat (no hit chance, fixed damage), and every enemy telegraphs the next three tiles it'll move to. The challenge is reading those queues and slipping through blind spots before you build up enough trace that the Admin shows up. Runs are 10-15 minutes, permadeath.

Free on itch: https://dragynrain.itch.io/rogue-signal-protocol
Source (MIT): https://github.com/Dragynrain/RogueSignalProtocol

Happy to answer design questions.
```

r/linux_gaming and r/SteamDeck: same video, but lead with the platform.

```
Rogue Signal Protocol - free, open source stealth roguelike that runs natively on Linux and the Deck (trailer)
```

First comment for those subs: AppImage, tarball, and AUR (`yay -S rogue-signal-protocol-bin`). Full gamepad support, and it's turn-based so it plays fine on the Deck.

---

## 5. Where to post, in order

Day 1:
1. YouTube upload (unlisted, check, then public)
2. itch page trailer field
3. itch devlog post
4. Your Discord
5. Bluesky / Mastodon

Over the next week (one or two a day, not all at once, so you can answer comments):
6. r/roguelikes
7. r/linux_gaming
8. r/SteamDeck
9. r/IndieGaming (native video upload)
10. Add the trailer link to IndieDB, IGDB, RogueBasin, and the GamingOnLinux and Lutris database entries where they have a video field
11. Update the Rogue Temple 1.0 thread with the link

Press and creators (after the press kit is live, see `docs/PRESSKIT.md`):
12. Alpha Beta Gamer and Free Game Planet (same admin, one email each)
13. GamingOnLinux editorial
14. Roguelike YouTubers from the marketing plan (Splattercat, Nookrium, Retromation, RhapsodyPlays). One short email each with the trailer link and the press kit.

Skip or think twice:
- r/roguelikedev and Sharing Saturday. The dev communities are where the AI pushback came from before, and the trailer opens with AI video. If you post there, lead with the capture script, which is the part they'd actually find interesting.
- Rogueliker. They skip AI-heavy projects in roundups.
