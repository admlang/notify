# adm.notify.sendgrid

A SendGrid client in ADM over `std.net.http`: mail send v3 from `std.formats.mail` messages or
dynamic templates, suppressions and unsubscribe groups, templates, verified senders, domain
authentication, statistics and the activity feed, the event webhook with its ECDSA signature
checked, and inbound parse.

```bash
adm get admlang:adm.notify.sendgrid
```

```adm
use (
	adm.notify.sendgrid
	std.formats.mail
)

let sg = new sendgrid.Client(apiKey)              // SENDGRID_API_KEY when left out
let message = new mail.Message()
	.from("orders@example.com", "Shop")
	.to("ana@example.net")
	.subject("Your order")
	.text("Thanks, Ana.")
try sg.send(message)

try sg.send(new sendgrid.Template("d-1234", to = "ana@example.net", data = {"name": "Ana", "order": "7"}, from = "orders@example.com"))
```

`SENDGRID_API_URL` or `baseURL` points the client elsewhere (`sendgrid.euURL` for an account
whose data stays in the EU); `onBehalfOf` acts for a subuser.

## Mail send

`send(message, options)` takes a `std.formats.mail` message: From, Reply-To, To, Cc, Bcc,
Subject, the text and HTML bodies, attachments, inline parts (`message.embed(cid, ...)`) and
any other header. It returns the id SendGrid gave the message (`X-Message-Id`), "" in the
sandbox mode.

```adm
let id = try sg.send(message, sendgrid.Options{
	categories: ["receipt"],
	args: {"order": "7"},                       // handed back in every event
	sendAt: time.now() + 2h,
	group: 42,                                  // the unsubscribe group
	tracking: sendgrid.Tracking{clicks: false, opens: true},
	sandbox: true,                              // validated, never delivered
})
```

`Options.personalizations` sends one copy per entry instead of one to the message's
recipients, each with its own recipients, subject, headers, substitutions, custom arguments and
send time. A `Template` is a dynamic template's message: one copy per `add(to, data)`.

```adm
let welcome = new sendgrid.Template("d-1234", from = "Shop <orders@example.com>")
welcome.add("ana@example.net", {"name": "Ana"})
let ben = welcome.add("ben@example.net", {"name": "Ben"})
ben.args.set("user", "b")
welcome.attach("terms.pdf", terms, mediaType = "application/pdf")
try sg.send(welcome)
```

The limits SendGrid enforces are checked before anything is sent: up to 1000 personalizations
and recipients, ten categories of up to 255 characters, 10000 bytes of custom arguments, a
send time at most 72 hours ahead, 30 MB in all.

Scheduled messages sent with a batch id can be held back together:

```adm
let batch = try sg.newBatch()
try sg.send(message, sendgrid.Options{sendAt: tomorrowMorning, batch: batch})
try sg.pause(batch)                             // or cancel(batch); resume(batch) undoes either
```

## Suppressions and groups

```adm
let recent = try sg.suppressions(sendgrid.SuppressionList.Bounces, since = lastWeek).next()
let bounces = try sg.suppressions(sendgrid.SuppressionList.Bounces).all()
let entry = try sg.suppression(sendgrid.SuppressionList.SpamReports, "ana@example.net")
try sg.unsuppress(sendgrid.SuppressionList.Blocks, "ana@example.net", "ben@example.net")
try sg.unsuppressAll(sendgrid.SuppressionList.InvalidEmails)
try sg.unsubscribe("cleo@example.net")          // the global unsubscribes

let news = try sg.createGroup("Newsletter", "Weekly news")
try sg.suppress(news.id, "dan@example.net")
let left = try sg.groupSuppressions(news.id)
let status = try sg.subscriptions("dan@example.net")
```

Lists come as `Pages<T>`: `next()` a page, `all()` the rest.

## Templates, senders, domains

`templates()`, `template(id)`, `createTemplate`, `renameTemplate`, `duplicateTemplate`,
`deleteTemplate`; `createVersion`, `version`, `updateVersion`, `deleteVersion`, `activate` for
their versions. `senders()`, `createSender`, `updateSender`, `deleteSender`,
`resendVerification`, `verifySender(token)` for verified senders. `authenticate(domain)` starts
domain authentication and returns the DNS records to publish; `validateDomain(id)` has SendGrid
check them; `domains()`, `domain`, `updateDomain`, `deleteDomain`.

## Statistics and activity

```adm
let weeks = try sg.stats(new time.Date(2026, 10, 1), by = sendgrid.Period.Week)
let receipts = try sg.stats(start, breakdown = sendgrid.Breakdown.Categories, names = ["receipt"])
let feed = try sg.activity("to_email=\"ana@example.net\"", limit = 50)
let detail = try sg.activityOf(feed[0].id)
```

Breakdowns: global, categories, mailbox providers, browsers, devices, clients, countries. The
activity feed needs SendGrid's Email Activity add-on.

## Event webhook

`events(publicKey, handle)` is an `http.Handler` that checks each request's ECDSA signature
with the key SendGrid shows for the signed webhook (`webhookKey()`, `signWebhook(true)` turns
signing on) and hands each event of the batch to `handle`.

```adm
let key = try sg.webhookKey()
try server.handle("POST /sendgrid/events", try sendgrid.events(key, def (event sendgrid.Event) !none {
	switch event.kind {
		case sendgrid.EventKind.Bounce:
			try suppressLocally(event.email, event.reason)
		case sendgrid.EventKind.Click:
			print("{event.email} followed {event.url}")
		default:
	}
	return none
}))
```

A request without a valid signature is answered 401. A batch `handle` fails on is answered 500
and SendGrid posts it again, the events already handled included: `event.id` (`sg_event_id`)
tells repeats apart. `event.args` holds the custom arguments the message was sent with.

## Inbound parse

`inbound(handle)` is an `http.Handler` that turns each posted form into a `std.formats.mail`
message, from the raw message (the "POST the raw, full MIME message" setting) or from the parsed
fields, with the SMTP envelope, the spam score and the DKIM and SPF results beside it.

```adm
try server.handle("POST /sendgrid/inbound", sendgrid.inbound(def (received sendgrid.Inbound) !none {
	print("{received.from}: {received.message.subject()}")
	for let file in received.message.attachments() {
		try store(file.filename(), file.data())
	}
	return none
}, username = "sendgrid", password = inboundPassword))
```

With a `username`, requests must carry those Basic credentials: put them in the destination
URL SendGrid posts to (`https://sendgrid:password@example.com/sendgrid/inbound`).

## Errors

Every call fails with `SendGridError`: `kind` is `Auth` (a key refused or missing a scope),
`NotFound`, `Invalid` (a request SendGrid or the local checks refuse; `problems` holds SendGrid's
`errors` with their fields), `RateLimited` (after `rateLimitRetries` waits; `retryAfter`),
`Server` or `Transport`. The client waits out an endpoint's rate limit once its requests are
spent and every 429.

## Tests

`adm test notify/sendgrid` runs against a loopback server; the event webhook test checks a
signature OpenSSL made. `ADM_TEST_SENDGRID_KEY` with `ADM_TEST_SENDGRID_FROM` (a verified
sender) adds calls to the real API: a message sent in the sandbox mode, which validates and
delivers nothing, and reads of templates, groups, bounces and statistics.
