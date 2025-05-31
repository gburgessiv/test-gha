# test-gha

messing with github actions for working with security advisories

---

At present, my take is "some automation is definitely possible" - critically,
GH's API lacks the ability to post comments on advisories. This means that the
UX of a greet bot/oncall assigning bot ... is suboptimal. The bot would either
have to add a footer to each advisory, or tag oncall people as collaborators
silently.

For now, I've chosen the latter.

Another point of awkwardness: triage/draft security advisories are meant to be
confidential, but GHA bots have public logs. "Carefully-written Python" isn't
my favorite thing, though seems doable given the low complexity of the greeting
script.

Finally, GH's workflows doesn't provide an `on: new_security_advisory` trigger.
This is understandable given the notes on confidentiality above, but means that
the autoassign script has to be run regularly, which is wasteful and adds
latency to the process.
