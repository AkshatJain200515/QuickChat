# QuickChat — Multi-Room TCP Chat Application
### B205 Computer Networks — Group Project
**Akshat Jain & Harsimran Singh | Gisma University of Applied Sciences**

---

A real-time chat application built with Python using raw TCP socket programming. We built this for our B205 Computer Networks module. The app supports multiple users chatting across different rooms at the same time.

## How it works

The application uses a Client-Server architecture. The server manages all the rooms and users, and every message goes through it. Each client that connects gets its own thread on the server side, so multiple users can chat at the same time without blocking each other.

We wrote a custom protocol on top of TCP — messages are plain text strings in the format `COMMAND/arg1/arg2`. For example, sending a message looks like `SEND/General/Hello everyone`.

## Requirements

- Python 3.7 or higher
- No external libraries needed — only uses Python's built-in `socket`, `threading`, `logging`, and `datetime` modules

## How to run

**Start the server first (run this once in one terminal):**
```
python3 server.py
```

**Then open a new terminal for each user and run:**
```
python3 client.py
```

You need at least 3 terminals open (1 server + 2 clients minimum) to properly test the group chat.

## Commands

Once connected, set your name first, then join a room:

| Command | What it does |
|---|---|
| `/name <username>` | Set your display name — do this first |
| `/join <room>` | Join a chat room |
| `/leave` | Leave your current room without disconnecting |
| `/create <room>` | Create a new room |
| `/invite <room> <user>` | Invite another user to a room |
| `/rooms` | See all available rooms |
| `/quit` | Disconnect and exit |
| anything else | Sends a message to your current room |

## Default rooms

When the server starts, three rooms are created automatically: `General`, `Tech`, and `Random`.

## Configuration

Everything is in `config.py` — the server IP, port, buffer size, and default rooms. If you want to run this across multiple machines on the same network, change `HOST` in `config.py` to the server machine's IP address and update it in the client machines too.

## Files

```
server.py    — the server, handles all connections and rooms
client.py    — the client, connects to the server and handles user input
config.py    — all settings and protocol command definitions
```

## Notes

- Usernames must be unique — the server will reject a duplicate
- Messages are broadcast to everyone in the same room
- If you switch rooms with `/join`, the old room gets notified you left
- The server logs everything to `server.log` as well as the terminal
