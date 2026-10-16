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

Buttons, selects and files go with a message; Discord's limits are checked before it is sent:

```adm
let chart = try discord.file("chart.png")
let buttons = discord.row(discord.button("Details", "details"), discord.link("Dashboard", dashboardURL))
try bot.send(channelId, "Weekly sales", files = [chart], components = [buttons])
let recent = try bot.messages(channelId).next()   // ?Message[]: a page, newest first
```

Slash commands are registered once and answered by a handler on your HTTP server, which checks
Discord's signature and defers an answer that takes longer than three seconds:

```adm
let roll = new discord.Command("roll", "Roll dice")
roll.option(discord.OptionType.Integer, "sides", "How many sides", required = true, min = 2.0)
try bot.registerCommands([roll])

let commands = bot.interactions(def (i discord.Interaction) !none {
	return i.reply("Rolling a d{i.integer("sides")}")
})                                                 // DISCORD_PUBLIC_KEY, else the application's
try mux.handle("POST /discord", commands)
```

A bot that stays connected reads the Gateway; it reconnects and resumes by itself:

```adm
let gw = bot.gateway(discord.Intent.GuildMessages, discord.Intent.MessageContent)
for let event in gw {
	match event {
		case discord.MessageCreate:
			try bot.send(event.message.channelId, "pong") when event.message.content == "!ping"
		case discord.InteractionCreate:
			try event.interaction.reply("Hello")
		default:
	}
}
```

`bot.shards(intents)` runs every shard a large bot needs as one stream of events.

## Tests

`adm test notify/discord` runs against a loopback server. `ADM_TEST_DISCORD_TOKEN` and
`ADM_TEST_DISCORD_CHANNEL` add posts to a real channel and a Gateway session.
