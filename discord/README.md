# adm.notify.discord

A Discord client in ADM over `std.net.http`: the REST API, webhooks, application commands with
interactions, and the Gateway for bots that stay connected.

```bash
adm get admlang:adm.notify.discord
```

```adm
use adm.notify.discord

let bot = new discord.Client(botToken)            // DISCORD_TOKEN when left out
let embed = new discord.Embed("Release 1.4", "Now available")
embed.field("Downloads", "https://example.com/1.4")
try bot.send(channelId, "Release 1.4 is out", embeds = [embed])

try discord.webhook(hookURL).send("Build passed")
```

## Tests

`adm test notify/discord` runs against a loopback server. `ADM_TEST_DISCORD_TOKEN` and
`ADM_TEST_DISCORD_CHANNEL` add posts to a real channel and a Gateway session.
