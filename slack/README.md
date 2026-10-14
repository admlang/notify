# adm.notify.slack

A Slack client in ADM over `std.net.http`: the Web API, Block Kit, incoming webhooks, and the
two ways Slack calls an app back (HTTP with signed requests, Socket Mode over WebSocket).

```bash
adm get admlang:adm.notify.slack
```

```adm
use adm.notify.slack

let bot = new slack.Client(botToken)              // SLACK_BOT_TOKEN when left out
try bot.send("#deploys", "Release 1.4 is out")
let message = new slack.Message()
message.section("*Release 1.4* is out")
message.button("Release notes", url = "https://example.com/notes/1.4")
try bot.send("#deploys", message)
try bot.upload("#deploys", report, "report.pdf")

// a hook that posts without a bot
try slack.webhook(hookURL).send("Build passed")
```

## Tests

`adm test notify/slack` runs against a loopback server. `ADM_TEST_SLACK_TOKEN` and
`ADM_TEST_SLACK_CHANNEL` add posts to a real workspace channel.
