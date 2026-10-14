# adm.notify.twilio

A Twilio client in ADM over `std.net.http`: SMS and MMS, WhatsApp, voice with TwiML, Verify,
and the webhooks Twilio sends with their signatures checked.

```bash
adm get admlang:adm.notify.twilio
```

```adm
use adm.notify.twilio

let tw = new twilio.Client(accountSid, authToken)   // TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
let sms = try tw.messages.send("+15005550006", "+15551234567", "Your code is 482913")
print(sms.sid)

let check = try tw.verify("VA...").start("+15551234567", channel = twilio.Channel.Sms)
let ok = try tw.verify("VA...").check("+15551234567", code)
```

## Tests

`adm test notify/twilio` runs against a loopback server. `ADM_TEST_TWILIO=sid:token` with
`ADM_TEST_TWILIO_FROM` and `ADM_TEST_TWILIO_TO` adds sends through the real API; the magic test
numbers keep it free.
