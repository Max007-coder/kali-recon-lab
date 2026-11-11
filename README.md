# Kali recon lab — footprinting six ways

A worked run of the six built-in Kali recon tools from *Footprinting and
Reconnaissance with Kali Linux*, executed on **Kali GNU/Linux Rolling (WSL2)** and
written up from the tool output rather than from memory.

**Source of the walkthrough:** *Footprinting and Reconnaissance with Kali Linux
| 6 Recon Tools Explained* by **Waqas Karim CCIE** —
https://www.youtube.com/watch?v=YB2qykxmCVg (channel: https://www.youtube.com/@waqasulkarim).
The tool sequence is his; the target choice, output capture and analysis here are
mine.

| # | tool | question it answers |
|---|---|---|
| 1 | `whois` | who owns the name, when, and which name servers answer for it |
| 2 | `nslookup` | what addresses the name resolves to right now |
| 3 | `dig` | the same, plus TTLs you can read for caching/infra clues |
| 4 | `curl -I` | what the server says about itself in HTTP headers |
| 5 | `whatweb` | fingerprint of the stack behind the page |
| 6 | `wafw00f` | whether a WAF sits in front of it |
| 7 | `dnsrecon` | the full DNS profile: NS, SOA, MX-ish, TXT, DNSSEC, zone transfer |

> `dnsrecon` is the seventh command in this run; the video's six are the ones
> above it.

## Target and authorisation

Everything here was run against **`example.com`** — the domain IANA reserves for
documentation (`RFC 2606`). It is public, intended to be fetched and cited, and
running a footprinting lab against it harms nobody.

**Do not point these tools at a domain you do not own or have written permission
to test.** `whois` and DNS lookups are public records, but `whatweb`, `wafw00f`
and `curl` are active requests to someone else's server. "It was only one
request" is still unauthorised probing.

## Run it

```bash
bash tools/run_recon.sh example.com        # writes recon/raw/*.txt
.venv/bin/python tools/render_screenshots.py   # rebuilds screenshots/*.png
```

The screenshots in `screenshots/` are rendered from the captured raw output
(`recon/raw/`), not grabbed from a live terminal — the text in them is exactly
what the tools printed.

## What the run found

Full detail in [`docs/report.md`](docs/report.md). In one paragraph: `example.com`
is an IANA-registered domain from 1995 sitting behind **Cloudflare** — Cloudflare
name servers, Cloudflare anycast addresses, `server: cloudflare` on the response,
a Cloudflare WAF in front, and DNSSEC signed with ECDSAP256SHA256 on a
`p=reject` DMARC policy. The interesting parts for a defender are the things that
leak *through* that edge: the DNS server software version, the DMARC/DKIM
posture, and the `cf-ray` suffix that reveals which datacentre served the
request.

## Environment

```
Kali GNU/Linux Rolling, kernel via WSL2
whois 5.x · whatweb · dnsutils (nslookup/dig) · curl · wafw00f 2.4.2 · dnsrecon
```

## Ethical note

Footprinting is the reconnaissance phase of a penetration test, and the whole
point of the phase is that it is passive first. If a report like this is going to
be delivered to a client, the scope document comes before the first query.
