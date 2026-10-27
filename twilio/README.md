# adm.notify.twilio

A Twilio client in ADM over `std.net.http`: SMS, MMS and WhatsApp, number lookups, voice with
TwiML builders, call control, recordings and transcriptions, Verify, API keys, subaccounts and
usage, and the webhooks Twilio sends with their signatures checked.

```bash
adm get admlang:adm.notify.twilio
```

```adm
use adm.notify.twilio

let tw = new twilio.Client(accountSid, authToken)   // TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
let sms = try tw.messages.send("+15005550006", "+15551234567", "Your code is 482913")
print(sms.sid)

let started = try tw.verify("VA...").start("+15551234567", channel = twilio.Channel.Sms)
let ok = try tw.verify("VA...").confirm("+15551234567", code)
```

An API key signs in instead of the auth token with `apiKey` and `apiSecret` (`TWILIO_API_KEY`,
`TWILIO_API_SECRET`); `region` and `edge` (`TWILIO_REGION`, `TWILIO_EDGE`) pick Twilio's
regional hosts; `tw.forAccount(subaccountSid)` acts for a subaccount. Timeouts, retries and the
transport are on `tw.connection`.

## Messages

```adm
try tw.messages.send(from, to, "Your table is ready", statusCallback = "https://example.com/status")
try tw.messages.send(from, to, media = ["https://example.com/menu.png"])               // MMS
try tw.messages.send(twilio.whatsapp(sender), twilio.whatsapp(to), content = "HX...", variables = {"1": "Ana"})
try tw.messages.send("", to, "Reminder", messagingService = "MG...", sendAt = tomorrowNine)
let sent = try tw.messages.list(twilio.MessageFilter{to: to, sentAfter: new time.Date(2026, 10, 1)}).all()
try tw.messages.cancel(scheduledSid)
for let media in try tw.messages.media(sid) {
	let bytes = try tw.messages.download(media)
}
let line = try tw.lookup("+15551234567")      // line_type_intelligence: carrier and kind of line
print(line.lineType.kind, line.lineType.carrier)
```

Also `get`, `redact`, `delete`, `deleteMedia`. WhatsApp outside the 24-hour session needs a
content template (`content`, `variables`); inside it any body goes. Before sending, the client
checks for a sender, a body (or media or template), at most ten media, 1600 characters, and a
schedule 15 minutes to 35 days ahead through a messaging service.

## Voice

```adm
let answer = new twilio.VoiceResponse()
answer.say("Thanks for calling.", voice = "Polly.Joanna")
let menu = answer.gather(input = [twilio.Input.Dtmf, twilio.Input.Speech], numDigits = 1, action = "/menu")
menu.say("Press 1 for sales, 2 for support.")
answer.dial(callerId = from).number("+15557654321").conference("Room 7", startOnEnter = true)
answer.record(maxLength = 2m, transcribe = true, transcribeCallback = "/text")

let call = try tw.calls.place(from, to, twiml = answer, progress = [twilio.CallProgress.Completed], statusCallback = "https://example.com/calls")
try tw.calls.redirect(call.sid, url = "https://example.com/hold")
try tw.calls.hangUp(call.sid)
let recording = try tw.calls.record(call.sid)
let audio = try tw.recordings.download(recording.sid)
let text = try tw.recordings.transcriptions(recording.sid)
```

`VoiceResponse` has `say`, `play`, `pause`, `gather`, `dial` (with `number`, `client`, `sip`,
`conference`, `queue`), `record`, `enqueue`, `redirect`, `reject`, `leave`, `hangup`;
`MessagingResponse` has `message` and `redirect`. `str()` is the TwiML document.

## Verify

```adm
let verify = tw.verify("VA...")
try verify.start("+15551234567")                                // SMS, the default
try verify.start("ana@example.net", channel = twilio.Channel.Email, template = "d-...", substitutions = {"name": "Ana"})
if try verify.confirm("+15551234567", code) { ... }
let limit = try verify.createRateLimit("end_user_ip")
try verify.addBucket(limit.sid, 5, 1h)
try verify.start("+15551234567", rateLimits = {"end_user_ip": clientAddress})
```

`confirm` is true once the code matches; it fails with NotFound when no verification is pending
(expired, used, or too many tries). Also `approve`, `cancel`, `get`, `rateLimits`, `buckets`,
`deleteRateLimit`, `deleteBucket`, and on the client `verifyServices`, `createVerifyService`,
`deleteVerifyService`.

## Webhooks

`webhook(authToken, handle)` is an `http.Handler` for every webhook of the account: incoming
messages and calls, message and call status callbacks, Gather and Record actions, recordings,
transcriptions, conference events. It checks `X-Twilio-Signature` (form or JSON bodies, with or
without the default port, as Twilio signs) and answers with the TwiML `handle` returns.

```adm
try server.handle("/twilio", twilio.webhook(authToken, def (event twilio.Event) !?twilio.TwiML {
	match event {
		case twilio.IncomingMessage:
			return new twilio.MessagingResponse().message("Got it, {event.profileName}.")
		case twilio.CallEvent:
			return new twilio.VoiceResponse().say("Hello").hangup()
		case twilio.MessageStatus:
			print("{event.messageSid}: {event.status}")
		default:
	}
	return none
}, baseURL = "https://example.com"))
```

The signature covers the address Twilio called: behind a proxy pass `baseURL` (the public scheme,
host and path prefix), or `trustProxy = true` to read `X-Forwarded-Proto` and
`X-Forwarded-Host`. A request whose signature does not match is answered 403.

## Accounts

```adm
let key = try tw.keys.create("ci")                    // key.secret is in this reply only
let eu = try tw.accounts.create("eu")
try tw.forAccount(eu.sid).messages.send(from, to, "Hi")
try tw.accounts.suspend(eu.sid)
let sms = try tw.usage.records(category = "sms", period = twilio.UsagePeriod.Monthly).all()
try tw.usage.createTrigger("totalprice", "100", "https://example.com/usage", triggerBy = "price")
```

## Errors

Every call fails with `TwilioError`: `kind` is `Auth`, `NotFound`, `Invalid`, `RateLimited` (after
`connection.rateLimitRetries` waits), `Server` or `Transport`, with Twilio's `errorCode` and
`moreInfo`.

## Tests

`adm test notify/twilio` runs against a loopback server; the webhook test checks Twilio's
documented signature example. `ADM_TEST_TWILIO=sid:token` with `ADM_TEST_TWILIO_FROM` and
`ADM_TEST_TWILIO_TO` adds a message and a call through the real API; with the test credentials and
the magic numbers (`+15005550006` sends) it costs nothing.
