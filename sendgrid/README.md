# adm.notify.sendgrid

A SendGrid client in ADM over `std.net.http`: mail send v3 from `std.formats.mail` messages or
dynamic templates, suppressions, the event webhook, inbound parse.

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
message.from = "Shop <orders@example.com>"
message.to = ["ana@example.net"]
message.subject = "Your order"
message.text = "Thanks, Ana."
try sg.send(message)

try sg.send(new sendgrid.Template("d-1234", to = "ana@example.net", data = {"name": "Ana", "order": "7"}))
```

## Tests

`adm test notify/sendgrid` runs against a loopback server. `ADM_TEST_SENDGRID_KEY` adds calls
to the real API in sandbox mode, which validates and delivers nothing.
