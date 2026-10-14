# adm.notify.postmark

A Postmark client in ADM over `std.net.http`: transactional mail from `std.formats.mail`
messages or templates, batches, message streams, bounces, and Postmark's webhooks.

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
message.from = "Shop <orders@example.com>"
message.to = ["ana@example.net"]
message.subject = "Your order"
message.html = "<p>Thanks, Ana.</p>"
let sent = try pm.send(message, stream = "outbound", tag = "order")
print(sent.messageId)
```

## Tests

`adm test notify/postmark` runs against a loopback server. `ADM_TEST_POSTMARK_TOKEN`, usually the
`POSTMARK_API_TEST` token, adds calls to the real API.
