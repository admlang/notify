# adm.notify.telegram

A Telegram Bot API client in ADM over `std.net.http`: every method and object of Bot API 10.3,
uploads streamed from files or bytes, keyboard builders, updates by long polling or a webhook
handler, and a local Bot API server.

```bash
adm get admlang:adm.notify.telegram
```

```adm
use adm.notify.telegram

let bot = new telegram.Bot(token)                 // TELEGRAM_BOT_TOKEN when left out
try bot.send(chatId, "Release 1\\.4 is out", parseMode = telegram.ParseMode.MarkdownV2)
let keyboard = new telegram.InlineKeyboard()
keyboard.button("Release notes", url = "https://example.com/notes/1.4")
try bot.send(chatId, "Details:", keyboard = keyboard)

for let update in try bot.updates() {             // long polling
	let message = update.message
	continue when message is none
	try bot.reply(message, "Got it")
}
```

## The API

Every Bot API method is a method of `Bot` with the API's name, less a `get` prefix
(`getChatMember` is `chatMember`, `getMe` is `me`; `getUpdates` is `updates()`, below): the
required parameters in order, the optional ones by name in camel case (`reply_markup` is
`replyMarkup`). Every API
object is a struct of the same name with camel-case fields; a field named `type` is `kind`.
An object that is one of several kinds (`ChatMember`, `MessageOrigin`, `InputMedia`, ...) is one
struct holding the fields of every kind, told apart by its `kind` or `status`.

```adm
let member = try bot.chatMember(groupId, userId)
print(member.status)                             // "administrator", "member", ...
try bot.setMyCommands([telegram.BotCommand{command: "deploy", description: "Ship it"}])
try bot.pinChatMessage(groupId, sent.messageId, disableNotification = true)
let edited = try bot.editMessageText(chatId = chat, messageId = sent.messageId, text = "Done")
```

An edit of an inline message returns none where an edit of a chat's message returns it. A chat
is its id (an int) or a channel's `@username`; a keyboard is a builder or any markup struct.

`send(chat, text, parseMode, keyboard, replyTo, silent, preview)`, `reply(message, text)` and
`answer(callbackQuery, text, alert)` cover the common cases. `escapeMarkdown(text)` (with
`MarkdownPart.Code` or `Link` inside code or a link's address) and `escapeHTML(text)` make text
literal for each parse mode.

## Files

```adm
try bot.sendPhoto(chat, telegram.upload("chart.png"), caption = "This week")
try bot.sendDocument(chat, telegram.upload("report.csv", data))       // bytes
try bot.sendSticker(chat, telegram.fileId(sticker.fileId))
try bot.sendMediaGroup(chat, [
	telegram.InputMediaPhoto{kind: "photo", media: telegram.upload("a.jpg")},
	telegram.InputMediaPhoto{kind: "photo", media: telegram.fileURL("https://example.com/b.jpg")},
])
let bytes = try bot.download(fileId)
try bot.download(fileId, "/tmp/voice.ogg")       // streamed to disk
```

An upload goes as multipart/form-data, streamed from its file as the request is sent; uploads
inside media objects get their `attach://` names. `bot.local = true` for a Bot API server run
with `--local` on the same machine: files given by path are then passed by their `file://`
address, and downloads read the server's copy.

## Keyboards

`InlineKeyboard` buttons open a URL, send callback data, switch to inline mode, open a Web App,
copy text or pay; `ReplyKeyboard` buttons send their text, the user's contact, location or a
poll. `row()` starts a new row; `removeKeyboard()` and `forceReply(placeholder)` are the other
markups.

```adm
let choice = new telegram.InlineKeyboard()
choice.button("Approve", callback = "approve:42", variant = "success").button("Reject", callback = "reject:42")
try bot.send(chat, "Deploy 1.4?", keyboard = choice)
```

## Updates

`bot.updates(timeout, allowed, offset)` is a stream of updates by long polling: an update counts
as handled once the next is asked for (`confirm()` marks it at once); a dropped connection or a
failing Telegram is waited out; a refused token or a webhook holding the updates ends the stream,
with the reason in `failure`. `next()` fails on every failure instead, and `stop()` ends the
stream from another task.

`telegram.webhook(secret, handle)` is an `http.Handler` for updates Telegram posts: a request
without the secret is answered 401, and an update `handle` fails on is answered 500, which
Telegram sends again.

```adm
try bot.setWebhook("https://bot.example.com/telegram", secretToken = secret)
try server.handle("POST /telegram", telegram.webhook(secret, def (update telegram.Update) !none {
	let query = update.callbackQuery
	try bot.answer(query, "Deploying") unless query is none
	return none
}))
```

## Limits and errors

Messages to one chat go out at most one a second, to a group or channel twenty a minute, and
thirty a second in all; paid broadcasts skip the bot's own limit and `paced = false` turns
pacing off. A 429 is waited out (`rateLimitRetries` times) for the time Telegram asked.

Every failure is a `telegram.TelegramError` with a `kind`: `Auth`, `Forbidden` (blocked, removed,
no rights), `RateLimited`, `Invalid`, `NotFound`, `Migrated` (`migrateToChatId` holds the
supergroup's id), `Conflict` (a webhook or another poller), `Transport`, `Server`; `description`
is Telegram's text and `errorCode` its code.

## Tests

`adm test notify/telegram` runs against a loopback server, every method of the API included.
With a bot token and a chat the bot may write to, the live test sends, edits, uploads, downloads
and deletes in that chat:

```bash
ADM_TEST_TELEGRAM_TOKEN=123:abc ADM_TEST_TELEGRAM_CHAT=-1001234567890 adm test notify/telegram
```

## Generated code

`types.adm`, `methods.adm` and `methods_test.adm` are generated from the Bot API reference by
`tools/generate.py`:

```bash
curl -s https://core.telegram.org/bots/api -o /tmp/api.html
python3 tools/generate.py /tmp/api.html .
```
