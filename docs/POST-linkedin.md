# LinkedIn post draft — recon lab

Paste into LinkedIn. Attach one of the PNGs from `screenshots/` (the WAF +
dnsrecon one tells the best story).

---

I ran the six classic Kali footprinting tools against one domain and wrote down
what each one actually told me.

Target: `example.com` — the domain IANA reserves for documentation, so the lab is
legal to run and identical in method to a paid engagement.

What the six tools produced:

**whois** — registered 1995, registrar RESERVED (IANA itself), three nameservers
locked with clientUpdate/Transfer/DeleteProhibited. The pivot: the nameservers are
Cloudflare's, so you know a CDN is in front before you send a single packet.

**nslookup / dig** — two A and two AAAA records, all inside Cloudflare's anycast
ranges, TTL 218s. Nothing here points at a server; it points at announcement
points.

**curl -I** — eight headers, four disclosures: `server: cloudflare`,
`cf-cache-status: HIT` with `age: 9314` (the page I read was 2.6 hours old, so the
origin never saw me), `alt-svc` advertising HTTP/3, and `cf-ray: ...-JNB` — the
Johannesburg edge, which quietly reveals where *I* was asking from.

**whatweb -a 1** — passive fingerprint: HTTP server is Cloudflare, three uncommon
headers flagged, no plugin probing.

**wafw00f** — Cloudflare WAF, in two requests. But note the honest limit: that
proves a WAF at the *edge*, not at the origin.

**dnsrecon** — the richest output. DNSSEC signed with ECDSAP256SHA256, both NS
sets enumerated, and two things I did not expect to matter: the DNS server
answered a `version.bind` query with its version string, and the SPF/DMARC posture
is `v=spf1 -all` with `p=reject; sp=reject; adkim=s; aspf=s` — strict, correct,
and clearly deliberate for a domain that only exists to be read.

The takeaway is not "Cloudflare is identifiable". It is that the most useful
findings were the smallest ones: a version string offered for free, and a mail
policy that quietly says "we will never send you mail from this domain".

Footprinting is passive first. Who the scope names is the only thing that decides
which domains get queried.

The tool sequence comes from NetworkWalks (Waqas Karim CCIE)'s walkthrough —
thank you for laying it out so cleanly:
https://www.youtube.com/watch?v=YB2qykxmCVg

Repo with the raw output, the report and the reproducible script:
https://github.com/Max007-coder/kali-recon-lab

#CyberSecurity #KaliLinux #PenetrationTesting #Reconnaissance #InfoSec

---

## Tag the author (do this in the composer)

A `@mention` cannot exist in a text file — LinkedIn only creates a real tag when
you type it in the composer and pick the profile from the dropdown.

1. Put the cursor before "NetworkWalks" in the sentence "The tool sequence comes
   from NetworkWalks (Waqas Karim CCIE)'s walkthrough", type `@`, then type
   `networkwalks` and pick the account from the dropdown. That is the account to
   tag.
2. If you also want the instructor's personal profile, tag him separately after
   the company name — but NetworkWalks is the one you asked for.
3. If the dropdown does not find the account, keep the written name and links
   instead: https://www.youtube.com/watch?v=YB2qykxmCVg and
   https://www.youtube.com/@waqasulkarim. A link credits the source; only a real
   tag sends a notification.

## Ethics line to keep in the post

Only ever run this against a domain you own or have written permission to test.
Passive records are public; `whatweb`, `wafw00f` and `curl` are requests to
someone else's server.
