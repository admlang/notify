# adm.notify.telegram

A Telegram Bot API client in ADM over `std.net.http`: messages, media, keyboards, and updates
by long polling or webhook.

```bash
adm get admlang:adm.notify.telegram
```

```adm
use adm.notify.telegram

let bot = new telegram.Bot(token)                 // TELEGRAM_BOT_TOKEN when left out
try bot.send(chatId, "Release 1.4 is out", parseMode = telegram.ParseMode.MarkdownV2)
let keyboard = new telegram.InlineKeyboard()
keyboard.button("Release notes", url = "https://example.com/notes/1.4")
try bot.send(chatId, "Details:", keyboard = keyboard)

for let update in try bot.updates() {             // long polling
	let message = update.message
	continue when message is none
	try bot.send(message.chat.id, "Got it")
}
```

## Tests

`adm test notify/telegram` runs against a loopback server. `ADM_TEST_TELEGRAM_TOKEN` and
`ADM_TEST_TELEGRAM_CHAT` add messages to a real chat.
