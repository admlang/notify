# ADM notification libraries

Official [ADM](https://github.com/admlang/adm) libraries that send messages to people through
the services most teams use: chat platforms, SMS and voice, transactional mail. Each is written
in ADM over `std.net.http`, published as `adm.notify.<service>` and signed by the `admlang`
publisher. They live outside the standard library because these APIs change with the product;
mail over SMTP and IMAP is in `std.net.mail`, which does not.

| Library | Service | What it covers |
|---|---|---|
| [`adm.notify.slack`](slack/) | Slack | Web API, Block Kit, incoming webhooks, Events API, slash commands, Socket Mode |
| [`adm.notify.discord`](discord/) | Discord | REST, webhooks, application commands and interactions, the Gateway for bots |
| [`adm.notify.telegram`](telegram/) | Telegram | the Bot API: messages, media, keyboards, updates by polling or webhook |
| [`adm.notify.twilio`](twilio/) | Twilio | SMS and MMS, WhatsApp, voice with TwiML, Verify, webhooks |
| [`adm.notify.sendgrid`](sendgrid/) | SendGrid | mail send v3, templates, suppressions, event webhooks, inbound parse |
| [`adm.notify.postmark`](postmark/) | Postmark | mail send, batches, templates, message streams, bounces, webhooks |

## Shared shape

Each library is a `Client` over a token, a `send` for its main message kind, typed builders for
what the service renders (blocks, embeds, keyboards, TwiML), and where the service calls back a
handler for `std.net.http` that checks the request's signature and hands out typed events. Mail
libraries send `std.formats.mail` messages, so a program writes a message once and chooses the
carrier. Every failure is one error type per library with a `kind` (`Auth`, `RateLimited`,
`Invalid`, `NotFound`, `Transport`, `Server`), the service's own code and message, and the
pause a `Retry-After` asked for.

## Tests

Each suite runs against a loopback server that answers as the service does, so `adm test`
needs no account. With credentials the suite also sends to a sandbox of the service:

```bash
ADM_TEST_SLACK_TOKEN=xoxb-... ADM_TEST_SLACK_CHANNEL=C... adm test notify/slack
ADM_TEST_DISCORD_TOKEN=... ADM_TEST_DISCORD_CHANNEL=... adm test notify/discord
ADM_TEST_TELEGRAM_TOKEN=... ADM_TEST_TELEGRAM_CHAT=... adm test notify/telegram
ADM_TEST_TWILIO=sid:token ADM_TEST_TWILIO_FROM=+1... ADM_TEST_TWILIO_TO=+1... adm test notify/twilio
ADM_TEST_SENDGRID_KEY=SG.... adm test notify/sendgrid        # the sandbox mode, nothing is delivered
ADM_TEST_POSTMARK_TOKEN=POSTMARK_API_TEST adm test notify/postmark
```
