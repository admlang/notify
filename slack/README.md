# adm.notify.slack

A Slack client in ADM over `std.net.http`: the Web API, Block Kit, incoming webhooks, the two
ways Slack calls an app back (HTTP with signed requests, Socket Mode over WebSocket), and OAuth
installation for distributed apps.

```bash
adm get admlang:adm.notify.slack
```

```adm
use adm.notify.slack

let bot = new slack.Client(botToken)              // SLACK_BOT_TOKEN when left out
try bot.send("#deploys", "Release 1.4 is out")
let message = new slack.Message("Release 1.4 is out")
message.section("*Release 1.4* is out")
message.button("Release notes", url = "https://example.com/notes/1.4")
try bot.send("#deploys", message)
try bot.upload("#deploys", report, "report.pdf")

// a hook that posts without a bot
try slack.webhook(hookURL).send("Build passed")
```

Lists come a page at a time, or all at once; the rate limits are kept by the client:

```adm
let channels = try bot.conversations().all()
let recent = try bot.history(channelId).next()    // ?Post[]: a page, newest first
```

Messages and modals are built from typed blocks; Slack's limits are checked before anything is
sent, and a broken message fails with `Invalid` naming the block and the limit:

```adm
let form = new slack.View("New ticket", callbackId = "ticket", submit = "Create")
form.input("Title", slack.TextInput{actionId: "title"}, blockId = "title")
form.input("Due", slack.DatePicker{actionId: "due"}, optional = true)
try bot.openView(triggerId, form)
```

An app answers events, slash commands and interactions through a handler on your HTTP server,
which checks Slack's signature and sends the three-second acknowledgement:

```adm
let app = new slack.App(bot)                     // SLACK_SIGNING_SECRET
app.onCommand(def (c slack.Command) !none {
	return try c.respond("Deploying {c.text}", inChannel = true)
})
app.onEvent(def (e slack.Event) !none {
	match e.payload {
		case slack.AppMention:
			try bot.send(e.payload.channel, "Hello <@{e.payload.user}>", slack.PostOptions{thread: e.payload.ts})
		default:
	}
	return none
})
app.onView(def (s slack.ViewSubmission) !none {
	let title = s.view.value("title")
	return try s.errors(map<string, string>{"title": "At least three characters"}) when title is none || title.value.len() < 3
	return none
})
try mux.handle("/slack", app)
```

An app without a public address takes the same callbacks over Socket Mode:

```adm
try new slack.SocketMode(app).run()              // SLACK_APP_TOKEN
```

A distributed app installs itself into workspaces with OAuth and keeps each workspace's tokens
in a store you provide (a `slack.MemoryStore` by default):

```adm
let installer = new slack.Installer(["chat:write", "commands"], "https://app.example/slack/oauth", store)
try mux.handle("/slack/install", installer.installHandler())     // SLACK_CLIENT_ID, SLACK_CLIENT_SECRET
try mux.handle("/slack/oauth", installer.callbackHandler("https://app.example/installed"))
let teamBot = try installer.clientFor(teamId)    // renews a rotating token first
```

## Tests

`adm test notify/slack` runs against a loopback server. `ADM_TEST_SLACK_TOKEN` and
`ADM_TEST_SLACK_CHANNEL` add posts to a real workspace channel.
