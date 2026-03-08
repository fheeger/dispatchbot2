# Dispatch Bot Commands

The default command prefix is `!`. Commands are grouped by role.

---

## Player Commands

### `!dispatch <message>`
Submit a dispatch. Write the entire message content after `!dispatch` in the same Discord message. The bot will add a 📨 reaction to confirm the dispatch was received.

Aliases: `!Dispatch`

**Example:**
```
!dispatch Requesting artillery support at grid 447. Signed, Alpha Company.
```

---

### `!howto`
Display instructions on how to use the bot as a player.

---

## Umpire Commands

### `!create_account <username>`
Create an account for the umpire web interface. The generated password will be sent to you by DM. You should change your password after first login.

**Example:**
```
!create_account john_umpire
```

---

### `!start_game <game_name>`
Start a new game. The game name may only contain letters, numbers, dashes (`-`), underscores (`_`), and tildes (`~`) — no spaces.

**Example:**
```
!start_game Operation_Blue_Star
```

---

### `!end_game`
End the current game associated with the category you are typing in.

---

### `!next_turn`
Advance the game to the next turn and deliver all messages that are due for this turn. The bot will:
1. Warn if there are unapproved messages still on the server
2. Advance the turn on the backend
3. Fetch and deliver approved messages to the relevant player channels

---

### `!add_category <game_name> [category_name ...]`
Register one or more Discord categories with a game. Category names are matched case-insensitively (Discord displays them in caps but they may not be stored that way).

If no category names are given, the category containing the channel you are typing in is added.

**Examples:**
```
!add_category Operation_Blue_Star Blue
!add_category Operation_Blue_Star Red Blue
```

---

### `!remove_category <game_name> [category_name ...]`
Remove one or more categories from a game. If no category names are given, the category containing the current channel is removed.

**Examples:**
```
!remove_category Operation_Blue_Star Blue
```

---

### `!list_categories <game_name>`
List all categories currently registered to a game.

**Example:**
```
!list_categories Operation_Blue_Star
```

---

### `!add_channel [channel_name ...]`
Register one or more channels as player channels in the game associated with the current category. Channels are added to whichever game their category belongs to.

If no channel names are given, the channel you are typing in is added.

**Examples:**
```
!add_channel
!add_channel alpha-company bravo-company
```

---

### `!remove_channel [channel_name ...]`
Remove one or more channels from a game. If no channel names are given, the current channel is removed.

**Examples:**
```
!remove_channel
!remove_channel alpha-company
```

---

### `!list_channels`
List all player channels registered to the game associated with the current category.

---

### `!broadcast <message>`
Send a message to all player channels in the current game.

**Example:**
```
!broadcast Umpire time has begun. No more orders until next turn.
```

---

### `!check_for_missed_messages`
Scan player channels for dispatch messages that were never processed (e.g. because the bot was offline). Checks the last 20 messages per channel and re-submits any `!dispatch` messages that are missing the 📨 reaction and are less than 3 days old.

---

### `!url`
Reply with the URL of the backend admin interface.

---

## Admin Commands

### `!message_all <filename>`
Send the contents of a file (from the bot's `data/` directory) as a DM to every member of the server. Reports how many messages were sent successfully.

**Example:**
```
!message_all announcement.txt
```

---

## Miscellaneous

### `!hello`
The bot introduces itself.
