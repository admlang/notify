# adm.notify.postmark

A Postmark client in ADM over `std.net.http`: transactional mail from `std.formats.mail`
messages or templates, batches, message streams, templates and layouts, bounces and
suppressions, message search with opens and clicks, servers and sender signatures, and a
handler for Postmark's webhooks that hands out typed events and inbound mail.

```bash
adm get admlang:adm.notify.postmark
```

```adm
use (
	adm.notify.postmark
	std.formats.mail
)

let pm = new postmark.Client(serverToken)         // POSTMARK_SERVER_TOKEN when left out
let message = new mail.Message()
	.from("orders@example.com", "Shop")
	.to("ana@example.net")
	.subject("Your order")
	.html("<p>Thanks, Ana.</p>")
let sent = try pm.send(message, stream = "outbound", tag = "order")
print(sent.messageId)
```

The server token sends and reads one server's templates, bounces and messages; the account
token (`accountToken`, else `POSTMARK_ACCOUNT_TOKEN`) manages servers and sender signatures.
`postmark.testToken` (`POSTMARK_API_TEST`) validates sends and delivers nothing.
`POSTMARK_API_URL` or `baseURL` points the client elsewhere.

## Sending

`send(message)` takes From, To, Cc, Bcc, Reply-To, Subject, the text and HTML bodies,
attachments, inline parts (`message.embed(cid, ...)`) and any other header. The settings are
arguments, or a message's own Postmark headers, which win for that message:

```adm
try pm.send(message, stream = "outbound", tag = "receipt", metadata = {"order": "7"},
	trackOpens = true, trackLinks = postmark.LinkTracking.HtmlAndText)
message.header.set("X-PM-Tag", "receipt")         // also X-PM-Message-Stream, X-PM-Metadata-<key>,
                                                  // X-PM-TrackOpens, X-PM-TrackLinks
```

A `Template` is a message made from a stored template, by alias or id, filled with a model:

```adm
let welcome = new postmark.Template("welcome", to = "ana@example.net", model = {"name": "Ana"}, from = "orders@example.com")
welcome.attach("logo.png", logo, mediaType = "image/png", contentId = "logo")
try pm.send(welcome)
```

`sendBatch(messages)` and `sendBatch(templates)` send any number in calls of up to 500 messages
and 50 MB, and return one `Sent` per message in order: one Postmark refused has its
`errorCode` and `message`. Postmark's limits are checked before anything is sent: 50
recipients, 10 MB a message, a tag of 1000 characters, ten metadata fields.

## Templates

```adm
let layouts = try pm.templates(kind = postmark.TemplateKind.Layout).all()
let welcome = try pm.template("welcome")          // by alias or id
welcome.subject = "Welcome, \{\{name}}"         // braces escaped: ADM strings interpolate {...}
try pm.updateTemplate(welcome)
let validation = try pm.validateTemplate(welcome, model = {"name": "Ana"})
print(validation.allContentIsValid, validation.htmlBody.renderedContent)
```

Also `createTemplate`, `deleteTemplate`.

## Bounces and suppressions

```adm
let stats = try pm.deliveryStats()
let hard = try pm.bounces(postmark.BounceFilter{kind: "HardBounce", inactive: true}).all()
let source = try pm.bounceDump(hard[0].id)
try pm.activate(hard[0].id)

let suppressed = try pm.suppressions("outbound", reason = "ManualSuppression")
try pm.suppress("broadcast", "ana@example.net")
try pm.unsuppress("broadcast", "ana@example.net")
```

Lists come as `Pages<T>`: `next()` a page, `all()` the rest, `total` the count.

## Messages, opens and clicks

```adm
let sent = try pm.outbound(postmark.MessageFilter{recipient: "ana@example.net", metadata: {"order": "7"}}).next()
let detail = try pm.outboundMessage(id)           // bodies and delivery events
let received = try pm.inbound(postmark.InboundFilter{status: "blocked"}).all()
try pm.bypass(received[0].messageId)
let opens = try pm.opensOf(id).all()
let clicks = try pm.clicks(postmark.EngagementFilter{tag: "receipt"}).all()
```

Searches reach the first 10000 results, as Postmark allows. Dates of the filters are
`time.DateTime` in Postmark's time zone (US Eastern).

## Servers and sender signatures

`servers()`, `server`, `createServer`, `updateServer`, `deleteServer`; `signatures()`,
`signature`, `createSignature`, `updateSignature`, `deleteSignature`, `resendConfirmation`.

## Webhooks

`webhook(handle)` is an `http.Handler` for every webhook of a server: delivery, bounce, spam
complaint, open, click, subscription change and inbound. Each event is one type of the `Event`
union; inbound mail is a `std.formats.mail` message with the posted fields beside it.

```adm
try server.handle("POST /postmark", postmark.webhook(def (event postmark.Event) !none {
	match event {
		case postmark.Bounce:
			print("{event.email}: {event.description}")
		case postmark.Inbound:
			print("{event.details.originalRecipient}: {event.message.subject()}")
		default:
	}
	return none
}, header = "X-Webhook-Secret", secret = hookSecret))
```

Set the webhook's HTTP authentication and pass `username` and `password`, or add a custom header
holding a secret and pass `header` and `secret`; a request without them is answered 401. An
event `handle` fails on is answered 500 and Postmark posts it again.

## Errors

Every call fails with `PostmarkError`: `kind` is `Auth`, `NotFound`, `Inactive` (every
recipient suppressed), `Invalid` (`errorCode` is Postmark's), `RateLimited`, `Server` or
`Transport`.

## Tests

`adm test notify/postmark` runs against a loopback server. `ADM_TEST_POSTMARK_TOKEN`, usually the
`POSTMARK_API_TEST` token, adds calls to the real API; with a real server token,
`ADM_TEST_POSTMARK_FROM` names a confirmed sender and the test also reads statistics,
templates, bounces and messages. Live sends go to Postmark's black hole address.
