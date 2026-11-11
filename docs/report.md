# Footprinting report — example.com

Target: `example.com` (IANA documentation domain, RFC 2606)
Host: Kali GNU/Linux Rolling on WSL2
Captured: 2026-11-11, raw output in `recon/raw/`
Source walkthrough: *Footprinting and Reconnaissance with Kali Linux | 6 Recon
Tools Explained* — Waqas Karim CCIE, https://www.youtube.com/watch?v=YB2qykxmCVg

Every value below is copied from the captured output, not reconstructed.

---

## 1. `whois` — registration and delegation

```
Domain Name: EXAMPLE.COM
Registry Domain ID: 2336799_DOMAIN_COM-VRSN
Creation Date: 1995-08-14T04:00:00Z
Updated Date: 2026-08-14T08:01:43Z
Registry Expiry Date: 2027-08-13T04:00:00Z
Registrar: RESERVED-Internet Assigned Numbers Authority
Name Server: ELLIOTT.NS.CLOUDFLARE.COM
Name Server: HERA.NS.CLOUDFLARE.COM
DNSSEC: signedDelegation
Domain Status: clientDeleteProhibited — clientTransferProhibited — clientUpdateProhibited
```

**Reading it.** Registrar `RESERVED` is IANA holding the name itself, which is why
no contact details appear — this is the only domain where that registrar field is
normal. Thirty-one years of registration history and a registry expiry a year out
says someone renews it deliberately. The three `client*Prohibited` statuses block
delete, transfer and update at the registry, the standard anti-hijack setting.

The useful pivot is elsewhere: the name servers are Cloudflare's, so DNS is hosted
at the edge even though the registration is IANA's. The `whois` record already
tells you the next three tools will see a CDN, before you send a single packet to
the web server.

## 2. `nslookup` — what it resolves to now

```
Server:  10.255.255.254          (local resolver)
Name:    example.com  Address: 104.20.23.154
Name:    example.com  Address: 172.66.147.243
Name:    example.com  Address: 2606:4700:10::ac42:93f3
Name:    example.com  Address: 2606:4700:10::6814:179a
```

**Reading it.** Two A and two AAAA records, and both families live in Cloudflare's
anycast ranges (`104.16.0.0/13`, `172.64.0.0/13`, `2606:4700::/32`). You are not
looking at a server; you are looking at a set of announcement points, and which
one answers depends on where you ask from. Note also the resolver:
`10.255.255.254` is the WSL2 NAT gateway, so these answers came from the host's
upstream, not from this machine talking to the authoritative servers.

## 3. `dig` — TTLs

```
example.com.  218  IN  A  104.20.23.154
example.com.  218  IN  A  172.66.147.243
```

**Reading it.** A TTL around 300s is the signature of managed DNS that expects to
fail over fast. A long TTL (hours) on a small business site usually means nobody
has touched the zone in years — a different, also useful, inference.

## 4. `curl -sS -D - -o /dev/null` — headers only

```
HTTP/2 200
content-type: text/html; charset=utf-8
server: cloudflare
last-modified: Wed, 11 Nov 2026 12:01:58 GMT
allow: GET, HEAD
accept-ranges: bytes
age: 9314
cf-cache-status: HIT
cf-ray: a58edaadfce21841-JNB
alt-svc: h3=":443"; ma=86400
```

**Reading it.** Four separate disclosures in eight headers:

- `server: cloudflare` — the edge names itself. Origin is hidden by design.
- `cf-cache-status: HIT` and `age: 9314` — this response was served from cache,
  about 2.6 hours old, so the origin never saw the request. Any content claim you
  draw from a cached page is 2.6 hours stale.
- `alt-svc: h3=":443"` — HTTP/3 is offered, useful for knowing which protocol
  paths are worth testing.
- `cf-ray: a58edaadfce21841-JNB` — the suffix is the datacentre code. `JNB` is
  Johannesburg: the edge that served me was in South Africa. That is a fact about
  *my* location leaking through *their* headers, which is why CDN headers matter
  to privacy work as much as to recon.

## 5. `whatweb -a 1` — stack fingerprint

```
https://example.com [200 OK] Allow[GET, HEAD], Country[UNITED STATES][US], HTML5,
HTTPServer[cloudflare], IP[104.20.23.154], Script, Title[Example Domain],
UncommonHeaders[cf-cache-status,cf-ray,alt-svc]
```

**Reading it.** Aggression level 1 keeps this passive — it reads what the single
response offers instead of brute-forcing plugin and version paths, which is what
would make it noisy and rude on a host you do not own. With that constraint, the
fingerprint is decided almost entirely by headers: `HTTPServer[cloudflare]` plus
the three `UncommonHeaders` it flags. `Country[UNITED STATES]` is the address
block's registration, not the server's rack.

## 6. `wafw00f` — is there a WAF

```
[*] Checking https://example.com
[+] The site https://example.com is behind Cloudflare (Cloudflare Inc.) WAF.
[~] Number of requests: 2
```

**Reading it.** Two requests: a normal one, then one crafted to look like an
attack, comparing the two. The honest caveat is where the WAF sits — this proves
a WAF at the **edge**, not at the origin. If the origin IP can be found (it
usually can, via old DNS history or certificate transparency), the WAF may be
bypassed entirely. That is exactly why the origin address is worth protecting.

## 7. `dnsrecon -d example.com -t std` — full DNS profile

```
DNSSEC is configured for example.com
NSEC KSk ECDSAP256SHA256 ...
NSEC ZSK ECDSAP256SHA256 ... (three ZSKs)
SOA  elliott.ns.cloudflare.com 108.162.195.228 / 162.159.44.228 / 172.64.35.228 (+3 v6)
NS   elliott.ns.cloudflare.com 108.162.195.228, 162.159.44.228, 172.64.35.228 (+3 v6)
NS   hera.ns.cloudflare.com    172.64.32.162, 108.162.192.162, 173.245.58.162 (+3 v6)
Bind Version for 108.162.195.228 "2026.11.2"
A    example.com 104.20.23.154, 172.66.147.243
AAAA example.com 2606:4700:10::6814:179a, 2606:4700:10::ac42:93f3
TXT  example.com "_k2n1y4vw3qtb4skdx9e7dxt97qrmmq9"
TXT  example.com "v=spf1 -all"
TXT  _dmarc.example.com "v=DMARC1;p=reject;sp=reject;adkim=s;aspf=s"
TXT  _dmarc._domainkey.example.com "v=DKIM1; p="
ERROR No SRV Records Found for example.com
```

**Reading it.** This is the richest output of the six, and three findings stand out:

1. **`Bind Version ... "2026.11.2"`** — the DNS software version answered a
   `version.bind` CHAOS query. Normally that is a free gift to an attacker sizing
   up known CVEs. Here the number looks date-coded and the host is Cloudflare's
   anycast, so treat it as "the resolver will tell you what it runs" rather than a
   specific exploitable build — the *habit* of answering is the finding.
2. **`v=spf1 -all`** with **`p=reject; sp=reject; adkim=s; aspf=s`** — the domain
   publishes that it sends **no** mail, and that any mail claiming to be from it
   must fail strict alignment. This is the textbook correct configuration for a
   domain that only exists to be read. It is also why the empty
   `v=DKIM1; p=` record is harmless: no key, but nothing is supposed to sign.
3. **No SRV records** — nothing advertises where services live, so there is no
   free service map.

The DNSSEC material (one KSK, three ZSKs, ECDSAP256SHA256) matches the
`signedDelegation` status from `whois`; the chain is real, not decoration.

---

## What a client would actually be told

| finding | severity if it were your domain | fix |
|---|---|---|
| DNS server version disclosed | low | suppress `version.bind`, or use a provider that does |
| WAF only at the edge, origin unknown | medium | keep origin IP out of DNS history and CT logs |
| short TTL / anycast | informational | nothing — it is working as intended |
| SPF `-all` + DMARC `p=reject` strict | **good** | keep it, monitor DMARC reports |
| `cf-ray` reveals viewer region | informational | unavoidable with Cloudflare |

## What this run cannot tell you

It is a passive, single-vantage-point footprint. It does **not** include port
scanning, subdomain brute force, certificate-transparency mining, or any attempt
to find the origin. Every answer here came from public records or one cached HTTP
response, which is also why it was safe to run against a domain I do not own.
